# routes/health_routes.py
from flask import Blueprint, jsonify
from datetime import datetime
import redis
from services.milvus_service import MilvusService
from pymilvus import connections

# Create a Blueprint for health check routes
health_bp = Blueprint('health', __name__)

# Initialize service instances as None
milvus_service = None
redis_client = None

def init_health_routes(ms: MilvusService, rc: redis.Redis):
    """
    Initialize the health routes with required dependencies.
    
    Args:
        ms: MilvusService instance for vector database operations
        rc: Redis client instance for caching operations
    """
    global milvus_service, redis_client
    milvus_service = ms
    redis_client = rc

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint that returns service status and timestamp.
    
    Returns:
        JSON response with service status and current timestamp
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "milvus-service"
    })

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Comprehensive readiness check that verifies all service dependencies.
    
    This endpoint checks the connection status of both Milvus and Redis
    to ensure the service is fully operational.
    
    Returns:
        JSON response with detailed status of each component
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        # Check Milvus connection
        if milvus_service:
            connections.get_connection_addr('default')
            status["checks"]["milvus"] = {"status": "healthy"}
        else:
            raise Exception("Milvus service not initialized")
            
        # Check Redis connection
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
    Simple liveness check to verify the application is running.
    
    Returns:
        JSON response indicating the service is alive with current timestamp
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    })