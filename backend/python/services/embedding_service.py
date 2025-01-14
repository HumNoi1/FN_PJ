# services/embedding_service.py
from typing import List, Dict, Any, Optional

class EmbeddingService:
    def __init__(self, embeddings, collection):
        self.embeddings = embeddings
        self.collection = collection
        
    async def query_documents(self,
                            question: str = "",
                            file_types: Optional[List[str]] = None,
                            n_results: int = 3,
                            metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        ค้นหาข้อมูลจาก ChromaDB โดยสามารถค้นหาได้ทั้งจากคำถามและ metadata
        
        การทำงานจะแตกต่างกันขึ้นอยู่กับว่ามีการระบุคำถามหรือไม่:
        - ถ้ามีคำถาม: จะค้นหาโดยใช้ semantic search
        - ถ้าไม่มีคำถาม: จะดึงข้อมูลตาม metadata เท่านั้น
        """
        try:
            # สร้างเงื่อนไขในการค้นหา
            where_condition = {}
            
            # เพิ่มเงื่อนไข file_type
            if file_types:
                where_condition["file_type"] = {"$in": file_types}
                
            # เพิ่มเงื่อนไขจาก metadata_filter
            if metadata_filter:
                where_condition.update(metadata_filter)

            if question.strip():
                # ถ้ามีคำถาม ใช้ semantic search
                results = self.collection.query(
                    query_texts=[question],
                    n_results=n_results,
                    where=where_condition if where_condition else None
                )
            else:
                # ถ้าไม่มีคำถาม ใช้ get เพื่อดึงข้อมูลตาม metadata
                results = self.collection.get(
                    where=where_condition if where_condition else None,
                    limit=n_results
                )
                # ปรับรูปแบบผลลัพธ์ให้เหมือนกับ query
                results = {
                    'documents': [results['documents']],
                    'metadatas': [results['metadatas']],
                    'distances': [[0.0] * len(results['documents'])]  # ใส่ค่า distance เป็น 0
                }

            return {
                "success": True,
                "documents": results['documents'][0],
                "metadatas": results['metadatas'][0],
                "distances": results['distances'][0]
            }
            
        except Exception as e:
            print(f"Error in query_documents: {str(e)}")  # เพิ่ม logging
            return {
                "success": False,
                "error": str(e)
            }

    async def get_document_by_id(self, file_id: str) -> Dict[str, Any]:
        """
        ดึงเอกสารโดยตรงจาก file_id
        
        เมธอดนี้เหมาะสำหรับการดึงเอกสารที่เรารู้ ID แน่นอนแล้ว
        """
        try:
            results = self.collection.get(
                where={"file_id": file_id},
                limit=1
            )
            
            if not results['documents']:
                return {
                    "success": False,
                    "error": f"ไม่พบเอกสารที่มี ID: {file_id}"
                }

            return {
                "success": True,
                "document": results['documents'][0],
                "metadata": results['metadatas'][0]
            }
            
        except Exception as e:
            print(f"Error in get_document_by_id: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }