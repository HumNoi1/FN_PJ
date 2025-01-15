from pydantic_settings import BaseSettings
from typing import Optional

class AppConfig(BaseSettings):
    """แอปพลิเคชันคอนฟิก"""
    
    # Milvus Configuration
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    DEFAULT_VECTOR_DIM: int = 384
    
    # Flask Configuration
    FLASK_APP: str = "app"
    FLASK_ENV: str = "development"
    FLASK_DEBUG: bool = True
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
    
    # Cache Configuration
    CACHE_TYPE: str = "redis"
    CACHE_REDIS_HOST: str = "localhost"
    CACHE_REDIS_PORT: int = 6379
    CACHE_DEFAULT_TIMEOUT: int = 300
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# สร้าง instance ของคอนฟิก
config = AppConfig()