# run.py
from flask import Flask
from flask_cors import CORS
import redis
from core.config import AppConfig
from routes.document_routes import document_bp, init_routes as init_document_routes
from routes.milvus_routes import milvus_bp, init_routes as init_milvus_routes
from routes.health_routes import health_bp, init_health_routes
from services.milvus_service import MilvusService

def create_app():
    """สร้างและกำหนดค่า Flask application"""
    # สร้าง Flask application
    app = Flask(__name__)
    CORS(app)  # เพิ่ม CORS support

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

    # เริ่มต้นค่า routes ด้วย services ที่จำเป็น
    init_document_routes(milvus_service)
    init_milvus_routes(milvus_service)
    init_health_routes(milvus_service, redis_client)

    # ลงทะเบียน blueprints
    app.register_blueprint(document_bp, url_prefix='/api/documents')
    app.register_blueprint(milvus_bp, url_prefix='/api/milvus')
    app.register_blueprint(health_bp, url_prefix='/api/health')

    return app

if __name__ == "__main__":
    app = create_app()
    config = AppConfig()
    app.run(
        host='0.0.0.0',
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )