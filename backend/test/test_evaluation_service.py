import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.evaluation_service import EvaluationService
from services.milvus_service import MilvusService
from services.pdf_service import PDFProcessingService
from core.config import AppConfig
import numpy as np
import pytest

# Load configuration
config = AppConfig()

@pytest.fixture
def evaluation_service():
    """Creates and returns an initialized EvaluationService for testing"""
    milvus_service = MilvusService(
        host=config.MILVUS_HOST,
        port=config.MILVUS_PORT
    )
    pdf_service = PDFProcessingService()
    return EvaluationService(milvus_service, pdf_service)

@pytest.fixture
def sample_content():
    """
    สร้างข้อมูลตัวอย่างสำหรับการทดสอบ
    ข้อมูลนี้จะจำลองคำตอบของนักเรียนและเอกสารอ้างอิงของครู
    """
    student_content = [
        {
            "content": """
            Deep Learning เป็นส่วนหนึ่งของ Machine Learning ที่ใช้โครงข่ายประสาทเทียม
            หลายชั้นในการเรียนรู้ การทำงานจะเริ่มจากการรับข้อมูลเข้า ผ่านการประมวลผล
            ในแต่ละชั้น และส่งผลลัพธ์ออกมา
            """,
            "score": 0.95
        }
    ]
    
    reference_content = [
        {
            "content": """
            Deep Learning คือสาขาหนึ่งของ Machine Learning ที่ใช้ Neural Networks 
            หลายชั้นในการเรียนรู้ แต่ละชั้นจะทำการประมวลผลและส่งต่อข้อมูลไปยังชั้นถัดไป
            จนได้ผลลัพธ์สุดท้าย
            """,
            "score": 1.0
        }
    ]
    
    return student_content, reference_content

@pytest.mark.asyncio
async def test_evaluate_content_accuracy(evaluation_service, sample_content):
    """
    ทดสอบการประเมินความถูกต้องของเนื้อหา
    
    ทดสอบว่าฟังก์ชัน evaluate_content_accuracy สามารถ:
    1. คำนวณคะแนนได้อย่างถูกต้อง
    2. ให้ผลลัพธ์อยู่ในช่วงที่กำหนด (0-1)
    3. จัดการกับข้อมูลได้อย่างเหมาะสม
    """
    student_content, reference_content = sample_content
    
    # ทดสอบการประเมิน
    accuracy_score = await evaluation_service._evaluate_content_accuracy(
        student_content,
        reference_content
    )
    
    # ตรวจสอบผลลัพธ์
    assert isinstance(accuracy_score, float), "คะแนนต้องเป็นทศนิยม"
    assert 0 <= accuracy_score <= 1, "คะแนนต้องอยู่ในช่วง 0-1"
    print(f"คะแนนความถูกต้อง: {accuracy_score}")

if __name__ == "__main__":
    # สั่งให้ pytest รันการทดสอบในไฟล์นี้
    pytest.main([__file__, "-v"])