# routes/health_routes.py
from flask import Blueprint, jsonify
from datetime import datetime
import redis
from ..services.milvus_service import MilvusService
from pymilvus import connections

health_bp = Blueprint('health', __name__)

milvus_service = None
redis_client = None

def init_health_routes(ms: MilvusService, rc: redis.Redis):
    """
    ฟังก์ชันสำหรับเริ่มต้นค่า routes พร้อมกับ dependencies ที่จำเป็น
    """
    global milvus_service, redis_client
    milvus_service = ms
    redis_client = rc

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint ที่ทำงานอยู่แล้ว"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "milvus-service"
    })

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    ตรวจสอบความพร้อมของระบบและการเชื่อมต่อกับ dependencies ทั้งหมด
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        # ตรวจสอบ Milvus
        if milvus_service:
            connections.get_connection_addr('default')
            status["checks"]["milvus"] = {"status": "healthy"}
        else:
            raise Exception("Milvus service not initialized")
            
        # ตรวจสอบ Redis
        if redis_client:
            redis_client.ping()
            status["checks"]["redis"] = {"status": "healthy"}
        else:
            raise Exception("Redis client not initialized")
            
        return jsonify(status)
        
    except Exception as e:
        status["status"] = "unhealthy"
        status["error"] = str(e)
        return jsonify(status), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """
    ตรวจสอบว่าแอปพลิเคชันยังทำงานอยู่หรือไม่
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    })