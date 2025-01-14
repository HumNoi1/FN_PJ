# services/rag_service.py
from typing import Dict, List, Any, Optional
from .embedding_service import EmbeddingService

class RAGService:
    def __init__(self, embedding_service: EmbeddingService, llm):
        """
        สร้าง RAGService สำหรับการประเมินคำตอบโดยใช้ LLM และ embedding service
        
        Parameters:
            embedding_service: บริการสำหรับการสร้างและค้นหา embeddings
            llm: โมเดลภาษาที่ใช้ในการประเมินคำตอบ
        """
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

            # ดึงคำตอบของนักเรียนโดยตรงจาก ID
            student_response = await self.embedding_service.get_document_by_id(student_file_id)
            if not student_response['success']:
                raise Exception(f"ไม่สามารถดึงคำตอบของนักเรียนได้: {student_response['error']}")

            # ดึงเอกสารอ้างอิงของอาจารย์
            teacher_docs = []
            for teacher_file_id in teacher_file_ids:
                doc_response = await self.embedding_service.get_document_by_id(teacher_file_id)
                if doc_response['success']:
                    teacher_docs.append(doc_response['document'])
                else:
                    print(f"ไม่สามารถดึงเอกสารอ้างอิง {teacher_file_id}: {doc_response['error']}")

            if not teacher_docs:
                raise Exception("ไม่สามารถดึงเอกสารอ้างอิงได้")

            # สร้างบริบทการประเมิน
            reference_context = "\n\n".join(teacher_docs)
            student_answer = student_response['document']

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
                        "reference_docs_count": len(teacher_docs),
                        "total_reference_length": len(reference_context)
                    }
                }
            }

        except Exception as e:
            print(f"Error in evaluate_student_answer: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _evaluate_with_llm(self,
                               question: str,
                               student_answer: str,
                               reference_context: str,
                               evaluation_criteria: Dict[str, int]) -> Dict[str, Any]:
        """
        ใช้ LLM ในการประเมินคำตอบของนักเรียน
        """
        try:
            prompt = f"""คุณเป็นผู้ประเมินคำตอบ กรุณาประเมินคำตอบของนักเรียนตามเกณฑ์ต่อไปนี้:

คำถาม:
{question}

เอกสารอ้างอิง:
{reference_context}

คำตอบของนักเรียน:
{student_answer}

เกณฑ์การให้คะแนน (คะแนนเต็มแต่ละด้าน):
{', '.join([f'{k} ({v} คะแนน)' for k, v in evaluation_criteria.items()])}

กรุณาวิเคราะห์และให้คะแนนในแต่ละด้าน พร้อมคำอธิบายประกอบ"""

            # เรียกใช้ LLM และรับผลลัพธ์
            response = self.llm(prompt)
            
            # แปลงผลลัพธ์เป็นรูปแบบที่ต้องการ
            if isinstance(response, dict):
                return response
            
            # ถ้าผลลัพธ์เป็น string ให้แปลงเป็น dict
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                raise Exception("ไม่สามารถแปลงผลการประเมินเป็น JSON ได้")

        except Exception as e:
            raise Exception(f"เกิดข้อผิดพลาดในการประเมิน: {str(e)}")