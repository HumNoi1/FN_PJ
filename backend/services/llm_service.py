# services/llm_service.py
from typing import Dict, List, Optional
from llama_cpp import Llama

class LLMService:
    def __init__(self, model_path: str = "models/llama-3.2-typhoon2-3b-instruct-q4_k_m.gguf"):
        """
        เริ่มต้น LLM Service โดยโหลด Llama 3.2 model
        model_path: พาธไปยังไฟล์โมเดลที่ quantized แล้ว
        """
        self.model = Llama(
            model_path=model_path,
            n_ctx=4096,  # ขนาด context window
            n_batch=512  # batch size สำหรับการประมวลผล
        )

    async def generate_evaluation(
        self,
        question: str,
        student_answer: str,
        reference_content: str,
        evaluation_criteria: Dict[str, float]
    ) -> Dict:
        """
        ใช้ Llama 2 ในการประเมินคำตอบของนักเรียน
        
        Args:
            question: คำถามที่ใช้ในการประเมิน
            student_answer: คำตอบของนักเรียน
            reference_content: เนื้อหาอ้างอิงที่เกี่ยวข้อง
            evaluation_criteria: เกณฑ์การประเมินและน้ำหนักคะแนน
        
        Returns:
            ผลการประเมินในรูปแบบ dictionary
        """
        # สร้าง prompt ที่เหมาะสมกับ Llama 2
        prompt = f"""[INST] You are an expert teacher evaluating a student's answer.
        Please evaluate the following response based on the given criteria.

        Question:
        {question}

        Reference Content:
        {reference_content}

        Student's Answer:
        {student_answer}

        Evaluation Criteria:
        {self._format_criteria(evaluation_criteria)}

        Provide a detailed evaluation including:
        1. Scores for each criterion with explanations
        2. Strengths and areas for improvement
        3. Specific suggestions for development
        4. Overall score and feedback

        Format your response as JSON. [/INST]"""

        # เรียกใช้ model และรับผลลัพธ์
        response = self.model(
            prompt,
            max_tokens=2048,
            temperature=0.1,  # ตั้งค่าต่ำเพื่อให้ผลลัพธ์คงที่
            top_p=0.9
        )

        # แปลงผลลัพธ์เป็น dictionary
        import json
        try:
            evaluation = json.loads(response['choices'][0]['text'])
            return self._validate_evaluation(evaluation)
        except json.JSONDecodeError:
            return self._create_fallback_evaluation()

    def _format_criteria(self, criteria: Dict[str, float]) -> str:
        """แปลงเกณฑ์การประเมินเป็นข้อความที่อ่านง่าย"""
        return "\n".join([
            f"- {criterion}: {weight} points"
            for criterion, weight in criteria.items()
        ])

    def _validate_evaluation(self, evaluation: Dict) -> Dict:
        """ตรวจสอบและทำให้แน่ใจว่าผลการประเมินอยู่ในรูปแบบที่ถูกต้อง"""
        required_keys = {
            "scores", "strengths", "areas_for_improvement",
            "suggestions", "total_score", "overall_feedback"
        }
        
        if not all(key in evaluation for key in required_keys):
            return self._create_fallback_evaluation()
        
        return evaluation

    def _create_fallback_evaluation(self) -> Dict:
        """สร้างผลการประเมินสำรองในกรณีที่มีข้อผิดพลาด"""
        return {
            "scores": {},
            "strengths": ["Unable to determine strengths"],
            "areas_for_improvement": ["Evaluation failed"],
            "suggestions": ["Please retry evaluation"],
            "total_score": 0,
            "overall_feedback": "Evaluation system encountered an error"
        }