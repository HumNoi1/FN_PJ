from flask_caching import Cache
from functools import wraps
import hashlib
import json

# สร้าง Cache instance
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_KEY_PREFIX': 'milvus_',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default
})

def cache_key_builder(*args, **kwargs):
    """สร้าง cache key จาก arguments"""
    key_dict = {
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def vectordb_cache(timeout=300):
    """
    Decorator สำหรับ cache ผลลัพธ์จาก vector operations
    
    Args:
        timeout: ระยะเวลาที่จะเก็บ cache (วินาที)
    """
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            cache_key = cache_key_builder(f.__name__, *args, **kwargs)
            
            # พยายามดึงผลลัพธ์จาก cache
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
                
            # ถ้าไม่มีใน cache ให้เรียกฟังก์ชันและเก็บผลลัพธ์
            rv = await f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
            
        return decorated_function
    return decorator

def clear_collection_cache(collection_name: str):
    """ล้าง cache ทั้งหมดที่เกี่ยวข้องกับ collection"""
    cache.delete_memoized(collection_name)