from flask import Flask
from flask_cors import CORS
from routes.document_routes import document_bp
from routes.milvus_routes import milvus_bp
from routes.health_routes import health_bp
from services.milvus_service import MilvusService
from config import AppConfig
import redis

# สร้าง Flask application
app = Flask(__name__)
CORS(app)  # เพิ่ม CORS support สำหรับการเรียกจาก frontend

# โหลด configuration
config = AppConfig()

# สร้าง instances ของ services
milvus_service = MilvusService(
    host=config.MILVUS_HOST,
    port=config.MILVUS_PORT
)

# เชื่อมต่อ Redis
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    password=config.REDIS_PASSWORD
)

# ลงทะเบียน blueprints
app.register_blueprint(document_bp, url_prefix='/api/documents')
app.register_blueprint(milvus_bp, url_prefix='/api/milvus')
app.register_blueprint(health_bp, url_prefix='/api/health')

# ส่ง service instances ไปยัง routes
from routes.document_routes import init_routes as init_document_routes
from routes.milvus_routes import init_routes as init_milvus_routes
from routes.health_routes import init_health_routes

init_document_routes(milvus_service)
init_milvus_routes(milvus_service)
init_health_routes(milvus_service, redis_client)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)