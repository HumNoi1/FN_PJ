# test/test_milvus.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.milvus_service import MilvusService
from pymilvus import Collection, utility  # เพิ่ม imports ที่จำเป็น
import asyncio  # เพิ่ม import สำหรับ async/await

async def test_milvus_connection():
    try:
        # สร้าง instance ของ MilvusService
        milvus = MilvusService(host="localhost", port=19530)
        
        # ตรวจสอบ collections ที่มีอยู่
        collections = utility.list_collections()
        print("Available collections:", collections)
        
        # ตรวจสอบข้อมูลใน collection
        if "documents" in collections:
            collection = Collection("documents")
            print("Number of entities:", collection.num_entities)
        else:
            print("Collection 'documents' not found")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")

# ฟังก์ชันสำหรับรัน async function
def run_test():
    asyncio.run(test_milvus_connection())

if __name__ == "__main__":
    run_test()