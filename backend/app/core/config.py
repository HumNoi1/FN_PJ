from pydantic_settings import BaseSettings
from typing import Optional

class MilvusSettings(BaseSettings):
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    COLLECTION_NAME: str = "document_store"
    VECTOR_DIM: int = 384  # สำหรับ MiniLM-L12-v2 model
    METRIC_TYPE: str = "COSINE"
    INDEX_TYPE: str = "IVF_FLAT"
    NLIST: int = 1024  # จำนวน clusters สำหรับ index building
    NPROBE: int = 16   # จำนวน clusters ที่จะค้นหา
    
    class Config:
        env_file = ".env"

milvus_settings = MilvusSettings()