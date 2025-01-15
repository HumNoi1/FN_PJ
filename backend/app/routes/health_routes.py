from flask import Blueprint, jsonify
from ..services.milvus_service import MilvusService
from pymilvus import connections
import redis
from datetime import datetime

health_bp = Blueprint('health', __name__)

milvus_service = None
redis_client = None

def init_health_routes(ms: MilvusService, rc: redis.Redis):
    global milvus_service, redis_client
    milvus_service = ms
    redis_client = rc

@health_bp.route('/health', methods=['GET'])
async def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "milvus-service"
    })

@health_bp.route('/health/ready', methods=['GET'])
async def readiness_check():
    """
    Detailed health check ที่ตรวจสอบการเชื่อมต่อกับ dependencies ทั้งหมด
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # ตรวจสอบ Milvus
    try:
        connections.get_connection_addr('default')
        status["checks"]["milvus"] = {
            "status": "healthy"
        }
    except Exception as e:
        status["checks"]["milvus"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    # ตรวจสอบ Redis
    try:
        redis_client.ping()
        status["checks"]["redis"] = {
            "status": "healthy"
        }
    except Exception as e:
        status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        status["status"] = "unhealthy"
    
    status_code = 200 if status["status"] == "healthy" else 503
    return jsonify(status), status_code

@health_bp.route('/health/live', methods=['GET'])
async def liveness_check():
    """
    ตรวจสอบว่าแอปพลิเคชันยังทำงานอยู่หรือไม่
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    })

@health_bp.route('/metrics/basic', methods=['GET'])
async def basic_metrics():
    """
    ดึงข้อมูล metrics พื้นฐาน
    """
    try:
        # ดึงข้อมูลจำนวน collections
        num_collections = len(utility.list_collections())
        
        # ดึงข้อมูลการใช้งาน Redis
        redis_info = redis_client.info()
        
        metrics = {
            "collections_count": num_collections,
            "redis_usage": {
                "connected_clients": redis_info["connected_clients"],
                "used_memory_human": redis_info["used_memory_human"],
                "total_connections_received": redis_info["total_connections_received"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500