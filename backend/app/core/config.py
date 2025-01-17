# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class AppConfig(BaseSettings):
    """
    คลาส AppConfig จัดการการตั้งค่าของแอปพลิเคชันทั้งหมด
    การใช้ pydantic_settings ช่วยให้เราสามารถตรวจสอบและจัดการค่าต่างๆ ได้อย่างมีประสิทธิภาพ
    """
    
    # Milvus Configuration
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    DEFAULT_VECTOR_DIM: int = 384
    
    # Flask Configuration
    FLASK_APP: str = "app"
    FLASK_ENV: str = "development"
    FLASK_DEBUG: bool = True
    FLASK_PORT: int = 5001  # เพิ่มการกำหนดค่า FLASK_PORT
    API_PREFIX: str = "/api/v1"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Monitoring Configuration
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    PROMETHEUS_PORT: int = 8000
    SERVICE_NAME: str = "milvus-service"
    
    class Config:
        """
        การตั้งค่าพิเศษสำหรับ pydantic BaseSettings
        - env_file: ระบุไฟล์ environment variables
        - case_sensitive: ให้ความสำคัญกับตัวพิมพ์ใหญ่-เล็ก
        - extra: อนุญาตให้มีค่าเพิ่มเติมได้
        """
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # อนุญาตให้มีค่าเพิ่มเติมโดยไม่แจ้งเตือน

# สร้าง instance ของ AppConfig
config = AppConfig()