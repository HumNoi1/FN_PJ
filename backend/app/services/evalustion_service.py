# services/evaluation_service.py
from typing import Dict, List, Optional
import numpy as np
from services.milvus_service import MilvusService
from services.pdf_service import PDFProcessingService

class EvaluationService:
    def __init__(self, milvus_service: MilvusService, pdf_service: PDFProcessingService):
        self.milvus_service = milvus_service
        self.pdf_service = pdf_service
        
    async def evaluate_answer(
        self,
        question: str,
        student_file_id: str,
        teacher_file_ids: List[str],
        evaluation_criteria: Dict[str, float]
    ) -> Dict:
        """
        ประเมินคำตอบของนักเรียนโดยเทียบกับเอกสารอ้างอิงของอาจารย์
        
        Args:
            question: คำถามที่ใช้ในการประเมิน
            student_file_id: ID ของไฟล์คำตอบนักเรียน
            teacher_file_ids: รายการ ID ของไฟล์อ้างอิงจากอาจารย์
            evaluation_criteria: เกณฑ์การประเมินและน้ำหนักคะแนน
            
        Returns:
            ผลการประเมินพร้อมคะแนนและคำแนะนำ
        """
        # สร้าง embedding สำหรับคำถาม
        question_embedding = await self.pdf_service.create_embeddings([question])
        
        # ดึงเนื้อหาที่เกี่ยวข้องจากเอกสารอ้างอิง
        reference_results = await self.milvus_service.search_vectors(
            collection_name="teacher_documents",
            query_vectors=question_embedding,
            limit=5,
            filter_expr=f"file_id in {teacher_file_ids}",
            output_fields=["content"]
        )
        
        # ดึงคำตอบของนักเรียน
        student_results = await self.milvus_service.search_vectors(
            collection_name="student_documents",
            query_vectors=question_embedding,
            limit=5,
            filter_expr=f"file_id == '{student_file_id}'",
            output_fields=["content"]
        )

        # คำนวณคะแนนแต่ละด้าน
        scores = {}
        for criterion, weight in evaluation_criteria.items():
            if criterion == "ความถูกต้องของเนื้อหา":
                scores[criterion] = self._evaluate_content_accuracy(
                    student_results,
                    reference_results
                ) * weight
            elif criterion == "ความครบถ้วนของคำตอบ":
                scores[criterion] = self._evaluate_completeness(
                    student_results,
                    reference_results
                ) * weight
            # เพิ่มเกณฑ์การประเมินอื่นๆ ตามต้องการ

        # คำนวณคะแนนรวม
        total_score = sum(scores.values())

        # สร้างข้อเสนอแนะ
        feedback = self._generate_feedback(scores, reference_results)
        improvements = self._suggest_improvements(scores, reference_results)

        return {
            "total_score": total_score,
            "scores": scores,
            "feedback": feedback,
            "improvement_suggestions": improvements
        }

    def _evaluate_content_accuracy(
        self,
        student_content: List[Dict],
        reference_content: List[Dict]
    ) -> float:
        """ประเมินความถูกต้องของเนื้อหา"""
        # ตรวจสอบความสอดคล้องระหว่างคำตอบนักเรียนและเอกสารอ้างอิง
        # คืนค่าคะแนนระหว่าง 0-1
        pass

    def _evaluate_completeness(
        self,
        student_content: List[Dict],
        reference_content: List[Dict]
    ) -> float:
        """ประเมินความครบถ้วนของคำตอบ"""
        # ตรวจสอบว่าคำตอบครอบคลุมประเด็นสำคัญทั้งหมดหรือไม่
        # คืนค่าคะแนนระหว่าง 0-1
        pass

    def _generate_feedback(
        self,
        scores: Dict[str, float],
        reference_content: List[Dict]
    ) -> str:
        """สร้างข้อเสนอแนะจากผลการประเมิน"""
        # สร้างข้อเสนอแนะที่เป็นประโยชน์ต่อนักเรียน
        pass

    def _suggest_improvements(
        self,
        scores: Dict[str, float],
        reference_content: List[Dict]
    ) -> str:
        """แนะนำแนวทางการพัฒนา"""
        # เสนอแนะวิธีการปรับปรุงคำตอบ
        pass