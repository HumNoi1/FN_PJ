# test_integration.py
import os
import sys
import pytest
import pytest_asyncio
from typing import Dict, Any
from pymilvus import CollectionSchema, FieldSchema, DataType, Collection
from reportlab.pdfgen import canvas

# เพิ่ม project root path เพื่อให้สามารถ import modules จาก parent directory ได้
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.pdf_service import PDFProcessingService
from services.milvus_service import MilvusService

class TestIntegration:
    """
    คลาสสำหรับทดสอบการทำงานร่วมกันของ services ต่างๆ
    รวมถึงการทดสอบการประมวลผล PDF และการจัดเก็บข้อมูลใน Milvus
    """

    async def _prepare_test_pdf(self) -> str:
        """
        เตรียมไฟล์ PDF สำหรับการทดสอบ
        สร้างไฟล์ PDF ที่มีเนื้อหาสำหรับทดสอบการประมวลผล
        
        Returns:
            str: พาธของไฟล์ PDF ที่สร้างขึ้น
        """
        test_file_path = os.path.join(os.path.dirname(__file__), "test_document.pdf")
        
        # สร้างไฟล์ PDF ที่มีเนื้อหาหลากหลายสำหรับทดสอบ
        c = canvas.Canvas(test_file_path)
        c.drawString(100, 750, "This is a test PDF document")
        c.drawString(100, 700, "Multiple lines of text")
        c.drawString(100, 650, "For testing document processing")
        c.drawString(100, 600, "Including various content")
        c.drawString(100, 550, "To test embedding generation")
        c.save()
        
        return test_file_path

    def _verify_pdf_result(self, result: Dict) -> None:
        """
        ตรวจสอบความถูกต้องของผลลัพธ์การประมวลผล PDF
        
        Args:
            result: Dictionary ที่มีข้อมูล text, chunks และ embeddings
        Raises:
            AssertionError: เมื่อผลลัพธ์ไม่ตรงตามที่คาดหวัง
        """
        # ตรวจสอบโครงสร้างของข้อมูล
        assert isinstance(result, dict), "ผลลัพธ์ต้องเป็น dictionary"
        assert "text" in result, "ไม่พบข้อมูล text ในผลลัพธ์"
        assert "chunks" in result, "ไม่พบข้อมูล chunks ในผลลัพธ์"
        assert "embeddings" in result, "ไม่พบข้อมูล embeddings ในผลลัพธ์"
        
        # ตรวจสอบข้อมูลไม่ว่างเปล่า
        assert len(result["text"]) > 0, "text ว่างเปล่า"
        assert len(result["chunks"]) > 0, "chunks ว่างเปล่า"
        assert len(result["embeddings"]) > 0, "embeddings ว่างเปล่า"
        
        # ตรวจสอบความสัมพันธ์ของข้อมูล
        assert len(result["chunks"]) == len(result["embeddings"]), (
            f"จำนวน chunks ({len(result['chunks'])}) "
            f"ไม่ตรงกับจำนวน embeddings ({len(result['embeddings'])})"
        )
        
        # ตรวจสอบมิติของ embeddings
        for i, embedding in enumerate(result["embeddings"]):
            assert len(embedding) == 384, f"embedding ที่ {i} มีมิติไม่ถูกต้อง"

    @pytest_asyncio.fixture
    async def setup_basic_services(self) -> Dict[str, Any]:
        """
        เตรียม services พื้นฐานที่จำเป็นสำหรับการทดสอบ
        
        Returns:
            Dictionary ที่มี instances ของ services ต่างๆ
        """
        try:
            return {
                "pdf": PDFProcessingService(),
                "milvus": MilvusService(host="localhost", port=19530)
            }
        except Exception as e:
            pytest.skip(f"ไม่สามารถเตรียม services ได้: {str(e)}")

    @pytest_asyncio.fixture
    async def setup_test_collection(self, setup_basic_services) -> str:
        """
        เตรียม collection สำหรับทดสอบใน Milvus
        
        Args:
            setup_basic_services: fixture ที่ให้ services พื้นฐาน
            
        Returns:
            str: ชื่อของ collection ที่สร้าง
        """
        services = setup_basic_services
        collection_name = "test_collection"

        try:
            # ลบ collection เดิมถ้ามีอยู่
            if await services["milvus"]._collection_exists(collection_name):
                await services["milvus"].drop_collection(collection_name)

            # สร้าง collection ใหม่
            await services["milvus"].create_collection(
                collection_name=collection_name,
                dimension=384,
                description="Test collection for integration testing"
            )
            
            return collection_name
            
        except Exception as e:
            pytest.fail(f"ไม่สามารถเตรียม test collection ได้: {str(e)}")

    @pytest.mark.asyncio
    async def test_pdf_processing(self, setup_basic_services: Dict[str, Any], setup_test_collection: str):
        """
        ทดสอบการทำงานร่วมกันของการประมวลผล PDF และการจัดเก็บข้อมูลใน Milvus
        
        Args:
            setup_basic_services: fixture ที่ให้ services พื้นฐาน
            setup_test_collection: fixture ที่ให้ชื่อ collection สำหรับทดสอบ
        """
        services = setup_basic_services
        collection_name = setup_test_collection
        test_pdf_path = None

        try:
            # เตรียมและประมวลผล PDF
            test_pdf_path = await self._prepare_test_pdf()
            pdf_result = await services["pdf"].process_pdf_file(test_pdf_path)
            self._verify_pdf_result(pdf_result)

            # ทดสอบการเชื่อมต่อและการทำงานกับ Milvus
            collection_info = await services["milvus"].get_collection_stats(collection_name)
            assert collection_info is not None, "ไม่สามารถเชื่อมต่อกับ Milvus ได้"

            print("การทดสอบทั้งหมดสำเร็จ!")

        except Exception as e:
            pytest.fail(f"การทดสอบล้มเหลว: {str(e)}")
            
        finally:
            # ทำความสะอาดหลังการทดสอบ
            if test_pdf_path and os.path.exists(test_pdf_path):
                os.remove(test_pdf_path)
            if collection_name:
                await services["milvus"].drop_collection(collection_name)