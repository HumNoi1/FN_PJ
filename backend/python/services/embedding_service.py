# services/embedding_service.py
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        สร้าง EmbeddingService สำหรับการจัดการ embeddings ใน Milvus
        
        Args:
            model_name: ชื่อโมเดลที่ใช้สร้าง embeddings (default ใช้โมเดลที่รองรับภาษาไทย)
        """
        # ตั้งค่าโมเดลสำหรับสร้าง embeddings
        self.model_name = model_name
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # เชื่อมต่อกับ Milvus
        self._initialize_milvus()
        
    def _initialize_milvus(self):
        """
        เชื่อมต่อกับ Milvus และสร้าง collection ถ้ายังไม่มี
        """
        try:
            # เชื่อมต่อกับ Milvus server
            connections.connect("default", host="localhost", port="19530")
            logger.info("Connected to Milvus successfully")
            
            # สร้าง collection ถ้ายังไม่มี
            if "document_store" not in Collection.list_collections():
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)  # ขนาดตาม model
                ]
                
                schema = CollectionSchema(fields, "Document collection for RAG system")
                self.collection = Collection("document_store", schema)
                
                # สร้าง index สำหรับการค้นหา
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                self.collection.create_index("embedding", index_params)
                logger.info("Created new Milvus collection: document_store")
            else:
                self.collection = Collection("document_store")
                logger.info("Using existing Milvus collection: document_store")
                
            self.collection.load()
            
        except Exception as e:
            logger.error(f"Error initializing Milvus: {str(e)}")
            raise

    async def store_document(self, content: str, file_id: str, file_type: str) -> Dict[str, Any]:
        """
        จัดเก็บเอกสารและ embedding ใน Milvus
        
        Args:
            content: เนื้อหาเอกสาร
            file_id: ID ของไฟล์
            file_type: ประเภทของไฟล์ (teacher/student)
            
        Returns:
            Dictionary containing success status and document ID
        """
        try:
            # สร้าง embedding
            embedding = self._generate_embedding(content)
            
            # เตรียมข้อมูลสำหรับเพิ่มใน Milvus
            data = {
                "file_id": [file_id],
                "file_type": [file_type],
                "content": [content],
                "embedding": [embedding.tolist()]
            }
            
            # เพิ่มข้อมูลใน Milvus
            insert_result = self.collection.insert(data)
            self.collection.flush() # ทำให้แน่ใจว่าข้อมูลถูกบันทึก
            
            return {
                "success": True,
                "id": insert_result.primary_keys[0]
            }
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def query_documents(self, 
                            question: str = "",
                            file_types: Optional[List[str]] = None,
                            n_results: int = 3) -> Dict[str, Any]:
        """
        ค้นหาเอกสารที่เกี่ยวข้องโดยใช้ semantic search
        
        Args:
            question: คำถามที่ใช้ค้นหา
            file_types: รายการประเภทไฟล์ที่ต้องการค้นหา
            n_results: จำนวนผลลัพธ์ที่ต้องการ
            
        Returns:
            Dictionary containing search results
        """
        try:
            # สร้าง query embedding
            query_embedding = self._generate_embedding(question)
            
            # เตรียม search parameters
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            # สร้าง expression สำหรับกรองประเภทไฟล์
            expr = f"file_type in {file_types}" if file_types else None
            
            # ค้นหาใน Milvus
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=n_results,
                expr=expr,
                output_fields=["file_id", "file_type", "content"]
            )
            
            # จัดรูปแบบผลลัพธ์
            documents = []
            for hits in results:
                for hit in hits:
                    documents.append({
                        "file_id": hit.entity.get("file_id"),
                        "file_type": hit.entity.get("file_type"),
                        "content": hit.entity.get("content"),
                        "distance": hit.distance
                    })
            
            return {
                "success": True,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        สร้าง embedding จากข้อความโดยใช้โมเดลที่กำหนด
        
        Args:
            text: ข้อความที่ต้องการสร้าง embedding
            
        Returns:
            numpy array containing the embedding
        """
        # แปลงข้อความเป็น tokens
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        # สร้าง embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
            # ใช้ mean pooling เพื่อได้ embedding เดียวสำหรับทั้งประโยค
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
        return embeddings.numpy().flatten()

    def __del__(self):
        """
        Cleanup เมื่อ object ถูกทำลาย
        """
        try:
            connections.disconnect("default")
        except:
            pass