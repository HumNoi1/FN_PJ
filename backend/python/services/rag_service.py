# services/rag_service.py
from typing import Dict, List, Any
from .milvus_service import MilvusEmbeddingService

class RAGService:
    def __init__(self, embedding_service: MilvusEmbeddingService, llm):
        self.embedding_service = embedding_service
        self.llm = llm

    async def evaluate_student_answer(self, 
                                    question: str,
                                    student_file_id: str,
                                    teacher_file_ids: List[str],
                                    evaluation_criteria: Dict[str, int] = None) -> Dict[str, Any]:
        try:
            # ตั้งค่าเกณฑ์การประเมินมาตรฐาน
            if not evaluation_criteria:
                evaluation_criteria = {
                    "ความถูกต้องของเนื้อหา": 40,
                    "ความครบถ้วนของคำตอบ": 30,
                    "การอ้างอิงแนวคิดสำคัญ": 20,
                    "การเรียบเรียงเนื้อหา": 10
                }

            # ค้นหาข้อมูลคำตอบของนักเรียนจาก Milvus
            student_result = await self.embedding_service.query_documents(
                question="",  # Empty query to get exact match
                file_types=["student"],
                n_results=1
            )
            
            if not student_result['success']:
                raise Exception(f"ไม่สามารถดึงคำตอบของนักเรียนได้: {student_result['error']}")

            student_answer = student_result['documents'][0]['content']

            # ดึงเอกสารอ้างอิงของอาจารย์
            reference_docs = []
            for teacher_file_id in teacher_file_ids:
                teacher_result = await self.embedding_service.query_documents(
                    question="",
                    file_types=["teacher"],
                    n_results=1
                )
                if teacher_result['success']:
                    reference_docs.append(teacher_result['documents'][0]['content'])

            if not reference_docs:
                raise Exception("ไม่สามารถดึงเอกสารอ้างอิงได้")

            # สร้างบริบทการประเมิน
            reference_context = "\n\n".join(reference_docs)

            # ประเมินคำตอบ
            evaluation_result = await self._evaluate_with_llm(
                question=question,
                student_answer=student_answer,
                reference_context=reference_context,
                evaluation_criteria=evaluation_criteria
            )

            return {
                "success": True,
                "evaluation": evaluation_result,
                "metadata": {
                    "student_file_id": student_file_id,
                    "teacher_file_ids": teacher_file_ids,
                    "document_statistics": {
                        "student_answer_length": len(student_answer),
                        "reference_docs_count": len(reference_docs),
                        "total_reference_length": len(reference_context)
                    }
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _evaluate_with_llm(self,
                               question: str,
                               student_answer: str,
                               reference_context: str,
                               evaluation_criteria: Dict[str, int]) -> Dict[str, Any]:
        # Implementation remains the same as your current version
        pass