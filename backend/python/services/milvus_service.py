# services/milvus_service.py
from typing import List, Dict, Any, Optional
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from .milvus_pool import MilvusConnectionPool
import logging
from functools import wraps
import time
import redis

def with_retry(max_retries=3, delay=1):
    """
    Decorator สำหรับ retry กรณีที่การเชื่อมต่อล้มเหลว
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
            raise last_exception
        return wrapper
    return decorator

class MilvusEmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-m3", cache_url: str = "redis://localhost:6379"):
        """
        Initialize service with model and caching
        """
        self.model_name = model_name
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.connection_pool = MilvusConnectionPool()
        
        # Initialize Redis for caching
        self.cache = redis.from_url(cache_url)
        self.cache_ttl = 3600  # 1 hour cache expiry
        
        self._initialize_collection()
        
    def _initialize_collection(self):
        """
        Initialize Milvus collection with connection pool
        """
        try:
            self.connection_pool.get_connection()
            
            if "document_store" not in Collection.list_collections():
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
                ]
                
                schema = CollectionSchema(fields, "Document collection for RAG system")
                self.collection = Collection("document_store", schema)
                
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024}
                }
                self.collection.create_index("embedding", index_params)
            else:
                self.collection = Collection("document_store")
                
            self.collection.load()
        finally:
            self.connection_pool.release_connection()

    @with_retry(max_retries=3)
    async def store_document(self, content: str, file_id: str, file_type: str) -> Dict[str, Any]:
        """
        Store document with connection pool and retry logic
        """
        try:
            self.connection_pool.get_connection()
            
            embedding = self._generate_embedding(content)
            
            data = {
                "file_id": [file_id],
                "file_type": [file_type],
                "content": [content],
                "embedding": [embedding.tolist()]
            }
            
            insert_result = self.collection.insert(data)
            
            # Invalidate cache for this file_id
            cache_key = f"doc:{file_id}"
            self.cache.delete(cache_key)
            
            return {
                "success": True,
                "id": insert_result.primary_keys[0]
            }
            
        except Exception as e:
            logging.error(f"Error storing document: {str(e)}")
            raise
        finally:
            self.connection_pool.release_connection()

    @with_retry(max_retries=3)
    async def query_documents(self, 
                            question: str = "",
                            file_types: Optional[List[str]] = None,
                            n_results: int = 3) -> Dict[str, Any]:
        """
        Query documents with caching and connection pool
        """
        try:
            # Check cache first
            cache_key = f"query:{question}:{','.join(file_types or [])}"
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return eval(cached_result)  # Convert string back to dict
            
            self.connection_pool.get_connection()
            
            query_embedding = self._generate_embedding(question)
            
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            expr = f"file_type in {file_types}" if file_types else None
            
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=n_results,
                expr=expr,
                output_fields=["file_id", "file_type", "content"]
            )
            
            documents = []
            for hits in results:
                for hit in hits:
                    documents.append({
                        "file_id": hit.entity.get("file_id"),
                        "file_type": hit.entity.get("file_type"),
                        "content": hit.entity.get("content"),
                        "score": hit.score
                    })
            
            result = {
                "success": True,
                "documents": documents
            }
            
            # Cache the result
            self.cache.setex(cache_key, self.cache_ttl, str(result))
            
            return result
            
        except Exception as e:
            logging.error(f"Error querying documents: {str(e)}")
            raise
        finally:
            self.connection_pool.release_connection()

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding with error handling
        """
        try:
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                embeddings = self.model(**inputs).pooler_output
            return embeddings.numpy().flatten()
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            raise