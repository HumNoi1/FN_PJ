# test_integration.py
import os
import sys
import pytest
import pytest_asyncio
from typing import Dict, Any
from pymilvus import CollectionSchema, FieldSchema, DataType, Collection

# เพิ่ม project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.pdf_service import PDFProcessingService
from services.milvus_service import MilvusService

class TestIntegration:
    """ทดสอบการทำงานร่วมกันของ services"""

    @pytest.fixture
    async def setup_test_collection(self, setup_basic_services):
        """
        เตรียม test collection สำหรับการทดสอบ
        เป็น fixture ที่สร้าง collection ใน Milvus ถ้ายังไม่มี
        """
        services = setup_basic_services
        collection_name = "test_collection"

        try:
            # กำหนดโครงสร้างของ collection
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
                FieldSchema(name="metadata", dtype=DataType.JSON)
            ]
            schema = CollectionSchema(fields=fields)

            # สร้าง collection ถ้ายังไม่มี
            if not await services["milvus"]._collection_exists(collection_name):
                collection = await services["milvus"].create_collection(
                    collection_name=collection_name,
                    dimension=384,
                    description="Test collection for integration testing"
                )
                print(f"สร้าง collection '{collection_name}' สำเร็จ")
            
            yield collection_name

            # Cleanup หลังการทดสอบ (optional)
            # await services["milvus"].drop_collection(collection_name)
            
        except Exception as e:
            pytest.fail(f"ไม่สามารถเตรียม test collection ได้: {str(e)}")

    @pytest.fixture
    def setup_basic_services(self) -> Dict[str, Any]:
        """เตรียม services พื้นฐาน"""
        try:
            return {
                "pdf": PDFProcessingService(),
                "milvus": MilvusService(host="localhost", port=19530)
            }
        except Exception as e:
            pytest.skip(f"ไม่สามารถเตรียม services ได้: {str(e)}")

    @pytest.mark.asyncio(loop_scope="function")  # เปลี่ยนจาก scope เป็น loop_scope
    async def test_pdf_processing(self, setup_basic_services: Dict[str, Any], setup_test_collection: str):
        """ทดสอบการประมวลผล PDF และการจัดเก็บข้อมูล"""
        services = setup_basic_services
        collection_name = setup_test_collection

        try:
            # เตรียมไฟล์ PDF สำหรับทดสอบ
            test_pdf_path = await self._prepare_test_pdf()
            
            # ทดสอบการประมวลผล PDF
            pdf_result = await services["pdf"].process_pdf_file(test_pdf_path)
            
            # ตรวจสอบความถูกต้องของผลลัพธ์
            self._verify_pdf_result(pdf_result)
            
            # ทดสอบการเชื่อมต่อกับ Milvus
            collection_info = await services["milvus"].get_collection_stats(collection_name)
            assert collection_info is not None, "ไม่สามารถเชื่อมต่อกับ Milvus ได้"
            
            print("การทดสอบทั้งหมดสำเร็จ!")
            
        except Exception as e:
            pytest.fail(f"การทดสอบล้มเหลว: {str(e)}")