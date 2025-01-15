# app/__init__.py
from flask import Flask
from flask_cors import CORS
from app.core.config import AppConfig
from app.services.milvus_service import MilvusService
from app.api.routes import register_routes
import redis

def create_app():
    """
    สร้างและกำหนดค่า Flask application
    
    ฟังก์ชันนี้จะ:
    1. สร้าง Flask instance
    2. โหลด configuration
    3. ตั้งค่าการเชื่อมต่อกับ services (Milvus, Redis)
    4. ลงทะเบียน routes
    5. ตั้งค่า CORS และ middleware อื่นๆ
    """
    app = Flask(__name__)
    CORS(app)  # เพิ่ม CORS support สำหรับการเชื่อมต่อกับ frontend

    # โหลด configuration จาก core
    config = AppConfig()
    app.config.from_object(config)

    # สร้างการเชื่อมต่อกับ services
    milvus_service = MilvusService(
        host=config.MILVUS_HOST,
        port=config.MILVUS_PORT
    )

    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=config.REDIS_PASSWORD
    )

    # ลงทะเบียน routes และส่งผ่าน dependencies
    register_routes(app, milvus_service, redis_client)

    return app