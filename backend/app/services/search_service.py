# services/search_service.py
from typing import List, Dict
import numpy as np
from services.milvus_service import MilvusService
from services.pdf_service import PDFProcessingService

class SearchService:
    def __init__(self, milvus_service: MilvusService, pdf_service: PDFProcessingService):
        self.milvus_service = milvus_service
        self.pdf_service = pdf_service

    async def semantic_search(
        self,
        query: str,
        collection_name: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        ค้นหาเอกสารที่เกี่ยวข้องกับ query โดยใช้ semantic search
        
        Args:
            query: ข้อความที่ต้องการค้นหา
            collection_name: ชื่อ collection ที่ต้องการค้นหา
            limit: จำนวนผลลัพธ์สูงสุด
            threshold: คะแนนความเหมือนขั้นต่ำ (0-1)
        """
        # สร้าง embedding สำหรับ query
        query_embedding = await self.pdf_service.create_embeddings([query])
        
        # ค้นหาใน Milvus
        results = await self.milvus_service.search_vectors(
            collection_name=collection_name,
            query_vectors=query_embedding,
            limit=limit,
            output_fields=["file_id", "content"]
        )

        # กรองผลลัพธ์ตาม threshold
        filtered_results = [
            result for result in results 
            if result["score"] >= threshold
        ]

        return filtered_results