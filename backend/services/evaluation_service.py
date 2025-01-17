# services/evaluation_service.py
from typing import Dict, List, Optional
from services.milvus_service import MilvusService
from services.pdf_service import PDFProcessingService
from services.llm_service import LLMService

class EvaluationService:
    def __init__(
        self,
        milvus_service: MilvusService,
        pdf_service: PDFProcessingService,
        llm_service: LLMService
    ):
        """
        เริ่มต้น EvaluationService พร้อม dependencies ที่จำเป็น
        """
        self.milvus_service = milvus_service
        self.pdf_service = pdf_service
        self.llm_service = llm_service

    async def evaluate_answer(
        self,
        question: str,
        student_file_id: str,
        teacher_file_ids: List[str],
        evaluation_criteria: Dict[str, float]
    ) -> Dict:
        """
        ประเมินคำตอบของนักเรียนโดยใช้ RAG ร่วมกับ Llama 2
        """
        # ดึงข้อมูลที่เกี่ยวข้องจาก vector store
        reference_content = await self._retrieve_relevant_content(
            question, teacher_file_ids
        )
        
        # ดึงคำตอบของนักเรียน
        student_answer = await self._get_student_answer(
            student_file_id, question
        )

        # ใช้ LLM ประเมินคำตอบ
        evaluation_result = await self.llm_service.generate_evaluation(
            question=question,
            student_answer=student_answer,
            reference_content=reference_content,
            evaluation_criteria=evaluation_criteria
        )

        return evaluation_result

    async def _retrieve_relevant_content(
        self,
        question: str,
        teacher_file_ids: List[str]
    ) -> str:
        """
        ดึงเนื้อหาที่เกี่ยวข้องจากเอกสารอ้างอิงโดยใช้ semantic search
        """
        query_embedding = await self.pdf_service.create_embeddings([question])
        
        results = await self.milvus_service.search_vectors(
            collection_name="teacher_documents",
            query_vectors=query_embedding[0],
            limit=3,  # จำกัดจำนวนผลลัพธ์เพื่อให้พอดีกับ context window
            filter_expr=f"file_id in {teacher_file_ids}",
            output_fields=["content"]
        )
        
        return "\n\n".join([r["content"] for r in results])

    async def _get_student_answer(
        self,
        student_file_id: str,
        question: str
    ) -> str:
        """
        ดึงคำตอบของนักเรียนที่เกี่ยวข้องกับคำถาม
        """
        query_embedding = await self.pdf_service.create_embeddings([question])
        
        results = await self.milvus_service.search_vectors(
            collection_name="student_documents",
            query_vectors=query_embedding[0],
            limit=1,
            filter_expr=f"file_id == '{student_file_id}'",
            output_fields=["content"]
        )
        
        return results[0]["content"] if results else ""