# routes/milvus_routes.py
from flask import Blueprint, request, jsonify
from services.milvus_service import MilvusService
from utils.cache import cache  # ปรับการ import ให้สอดคล้องกับโครงสร้างใหม่
from utils.monitoring import track_operation

# สร้าง Blueprint สำหรับจัดการ Milvus operations
milvus_bp = Blueprint('milvus', __name__)

# ตัวแปร global สำหรับเก็บ service instance
milvus_service = None

def init_routes(service: MilvusService):
    """
    ฟังก์ชันสำหรับเริ่มต้นค่า routes โดยรับ MilvusService เป็น dependency
    
    Args:
        service: Instance ของ MilvusService ที่จะใช้ในการจัดการ vectors
    """
    global milvus_service
    milvus_service = service

@milvus_bp.route('/collections/<name>', methods=['POST'])
@track_operation
async def create_collection(name):
    """
    สร้าง collection ใหม่ใน Milvus
    
    Args:
        name: ชื่อของ collection ที่ต้องการสร้าง
    """
    try:
        dimension = request.json.get('dimension', 384)
        description = request.json.get('description', '')
        
        collection = await milvus_service.create_collection(
            collection_name=name,
            dimension=dimension,
            description=description
        )
        
        return jsonify({
            "status": "success",
            "message": f"Collection {name} created successfully",
            "data": {
                "name": name,
                "dimension": dimension,
                "description": description
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@milvus_bp.route('/collections/<name>/vectors', methods=['POST'])
@track_operation
@cache.memoize(timeout=300)  # Cache for 5 minutes
async def insert_vectors(name):
    """
    เพิ่ม vectors เข้าไปใน collection ที่ระบุ
    
    Args:
        name: ชื่อของ collection ที่ต้องการเพิ่ม vectors
    """
    try:
        data = request.json
        file_ids = data.get('file_ids', [])
        contents = data.get('contents', [])
        vectors = data.get('vectors', [])
        metadata_list = data.get('metadata_list', [])
        
        ids = await milvus_service.insert_vectors(
            collection_name=name,
            file_ids=file_ids,
            contents=contents,
            vectors=vectors,
            metadata_list=metadata_list
        )
        
        return jsonify({
            "status": "success",
            "message": f"Inserted {len(ids)} vectors successfully",
            "data": {
                "ids": ids
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400