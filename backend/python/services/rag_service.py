# services/rag_service.py
from typing import List, Dict, Any
import numpy as np
from .embedding_service import EmbeddingService

class RAGService:
    def __init__(self, embedding_service: EmbeddingService, llm):
        self.embedding_service = embedding_service
        self.llm = llm
        
    async def prepare_reference_material(self, teacher_file_ids: List[str]) -> Dict[str, Any]:
        """
        เตรียมข้อมูลอ้างอิงจากไฟล์ของอาจารย์
        """
        try:
            # ดึงข้อมูลที่เกี่ยวข้องจาก ChromaDB โดยใช้ file_ids
            reference_docs = await self.embedding_service.query_documents(
                file_ids=teacher_file_ids,
                n_results=10  # ดึงข้อมูลที่เกี่ยวข้องมากที่สุด 10 ส่วน
            )
            
            if not reference_docs['success']:
                raise Exception("Failed to retrieve reference documents")
                
            # รวมข้อมูลเป็นบริบทเดียว
            context = "\n\n".join(reference_docs['documents'])
            
            return {
                "success": True,
                "context": context,
                "source_metadata": reference_docs['metadatas']
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def evaluate_student_answer(self, 
                                    question: str,
                                    student_answer: str,
                                    reference_context: str,
                                    evaluation_criteria: Dict[str, int] = None) -> Dict[str, Any]:
        """
        ประเมินคำตอบของนักเรียนโดยใช้ LLM เปรียบเทียบกับเอกสารอ้างอิง
        """
        try:
            # ถ้าไม่มีเกณฑ์การให้คะแนน ใช้เกณฑ์พื้นฐาน
            if not evaluation_criteria:
                evaluation_criteria = {
                    "ความถูกต้องของเนื้อหา": 40,
                    "ความครบถ้วนของคำตอบ": 30,
                    "การอ้างอิงแนวคิดสำคัญ": 20,
                    "การเรียบเรียงเนื้อหา": 10
                }

            # สร้าง prompt สำหรับ LLM
            prompt = f"""คุณเป็นผู้ประเมินคำตอบ โปรดประเมินคำตอบของนักเรียนตามเกณฑ์ต่อไปนี้:

คำถาม: {question}

เอกสารอ้างอิง:
{reference_context}

คำตอบของนักเรียน:
{student_answer}

เกณฑ์การให้คะแนน:
{', '.join([f'{k} ({v} คะแนน)' for k, v in evaluation_criteria.items()])}

โปรดวิเคราะห์และให้คะแนนในแต่ละด้าน พร้อมคำอธิบายประกอบ โดยแสดงผลในรูปแบบ JSON ดังนี้:
{
    "scores": {
        "ความถูกต้องของเนื้อหา": [คะแนน],
        "ความครบถ้วนของคำตอบ": [คะแนน],
        "การอ้างอิงแนวคิดสำคัญ": [คะแนน],
        "การเรียบเรียงเนื้อหา": [คะแนน]
    },
    "total_score": [คะแนนรวม],
    "feedback": [คำแนะนำโดยละเอียด],
    "improvement_suggestions": [ข้อเสนอแนะในการพัฒนา]
}"""

            # ส่ง prompt ไปยัง LLM และรับผลลัพธ์
            result = self.llm(prompt)
            
            # แปลงผลลัพธ์เป็น JSON
            import json
            evaluation = json.loads(result)
            
            return {
                "success": True,
                "evaluation": evaluation
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def batch_evaluate_answers(self, 
                                   student_file_id: str,
                                   teacher_file_ids: List[str],
                                   questions: List[str]) -> Dict[str, Any]:
        """
        ประเมินคำตอบหลายข้อพร้อมกัน
        """
        try:
            # เตรียมข้อมูลอ้างอิง
            reference_material = await self.prepare_reference_material(teacher_file_ids)
            if not reference_material['success']:
                raise Exception("Failed to prepare reference material")

            # ดึงคำตอบของนักเรียน
            student_answers = await self.embedding_service.query_documents(
                file_ids=[student_file_id]
            )
            if not student_answers['success']:
                raise Exception("Failed to retrieve student answers")

            # ประเมินแต่ละคำตอบ
            evaluations = []
            for question in questions:
                evaluation = await self.evaluate_student_answer(
                    question=question,
                    student_answer=student_answers['documents'][0],  # ต้องปรับให้ตรงกับคำถาม
                    reference_context=reference_material['context']
                )
                evaluations.append(evaluation)

            return {
                "success": True,
                "evaluations": evaluations
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }