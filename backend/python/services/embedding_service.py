# services/embedding_service.py
import os
from typing import List, Dict, Any
import requests
from pathlib import Path
import pypdf
from io import BytesIO

class EmbeddingService:
    def __init__(self, embeddings, collection):
        self.embeddings = embeddings
        self.collection = collection
        
    async def process_file_from_url(self, file_url: str, file_id: str, file_type: str) -> Dict[str, Any]:
        """
        ดาวน์โหลดไฟล์จาก URL และทำ embedding
        """
        try:
            # ดาวน์โหลดไฟล์
            response = requests.get(file_url)
            response.raise_for_status()
            
            # อ่านไฟล์ PDF
            pdf_reader = pypdf.PdfReader(BytesIO(response.content))
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            
            # แบ่งข้อความเป็นชิ้นๆ
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(text_content)
            
            # สร้าง embeddings
            embeddings_list = self.embeddings.embed_documents(chunks)
            
            # เก็บใน ChromaDB
            self.collection.add(
                embeddings=embeddings_list,
                documents=chunks,
                ids=[f"{file_id}_{i}" for i in range(len(chunks))],
                metadatas=[{
                    "file_id": file_id,
                    "file_type": file_type,
                    "chunk_index": i
                } for i in range(len(chunks))]
            )
            
            return {
                "success": True,
                "chunks_processed": len(chunks),
                "file_id": file_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_id": file_id
            }

    async def query_documents(self, 
                            question: str, 
                            file_types: List[str] = None,
                            n_results: int = 3) -> Dict[str, Any]:
        """
        ค้นหาข้อมูลที่เกี่ยวข้องจาก ChromaDB
        """
        try:
            # สร้าง metadata filter ถ้ามีการระบุ file_types
            where = {"file_type": {"$in": file_types}} if file_types else None
            
            # ค้นหาข้อมูล
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results,
                where=where
            )
            
            return {
                "success": True,
                "documents": results['documents'][0],
                "metadatas": results['metadatas'][0],
                "distances": results['distances'][0]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }