from typing import List, Dict, Any, Optional
import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
    connections,
    Index
)

class MilvusService:
    """
    Service class ที่จัดการการทำงานกับ Milvus
    รับผิดชอบการจัดการ collections, vectors, และ indexes
    """
    def __init__(self, host: str, port: int):
        """
        ตั้งค่าการเชื่อมต่อกับ Milvus server
        
        Args:
            host: Milvus server hostname
            port: Milvus server port
        """
        self.host = host
        self.port = port
        self._connect()

    def _connect(self) -> None:
        """เชื่อมต่อกับ Milvus server"""
        try:
            connections.connect(
                alias="default", 
                host=self.host, 
                port=self.port
            )
        except Exception as e:
            raise ConnectionError(f"ไม่สามารถเชื่อมต่อกับ Milvus server ได้: {str(e)}")

    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        description: str = ""
    ) -> Collection:
        """
        สร้าง collection ใหม่สำหรับเก็บ vectors
        
        Args:
            collection_name: ชื่อของ collection
            dimension: ขนาดมิติของ vector
            description: คำอธิบาย collection (optional)
            
        Returns:
            Collection object ที่สร้างขึ้น
        """
        if utility.has_collection(collection_name):
            raise ValueError(f"Collection {collection_name} มีอยู่แล้ว")

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]

        schema = CollectionSchema(
            fields=fields,
            description=description
        )

        collection = Collection(
            name=collection_name,
            schema=schema,
            using='default'
        )

        return collection

    async def create_index(
        self,
        collection_name: str,
        field_name: str = "embedding",
        index_type: str = "IVF_FLAT",
        metric_type: str = "COSINE",
        params: Dict[str, Any] = {"nlist": 1024}
    ) -> None:
        """
        สร้าง index สำหรับ vector field
        
        Args:
            collection_name: ชื่อของ collection
            field_name: ชื่อ field ที่ต้องการสร้าง index (default: "embedding")
            index_type: ประเภทของ index (default: "IVF_FLAT")
            metric_type: วิธีการคำนวณระยะห่าง (default: "COSINE")
            params: พารามิเตอร์เพิ่มเติมสำหรับ index
        """
        collection = Collection(collection_name)
        
        index_params = {
            "metric_type": metric_type,
            "index_type": index_type,
            "params": params
        }

        try:
            collection.create_index(
                field_name=field_name,
                index_params=index_params
            )
            # Load collection เข้า memory เพื่อให้พร้อมใช้งาน
            collection.load()
        except Exception as e:
            raise Exception(f"ไม่สามารถสร้าง index ได้: {str(e)}")

    async def insert_vectors(
        self,
        collection_name: str,
        file_ids: List[str],
        contents: List[str],
        vectors: List[List[float]],
        metadata_list: List[Dict] = None
    ) -> List[int]:
        """
        เพิ่ม vectors และข้อมูลที่เกี่ยวข้องเข้าไปใน collection
        
        Args:
            collection_name: ชื่อของ collection
            file_ids: รายการของ file IDs
            contents: รายการของเนื้อหาข้อความ
            vectors: รายการของ vectors
            metadata_list: รายการของ metadata (optional)
            
        Returns:
            รายการของ IDs ที่ถูกสร้างขึ้น
        """
        collection = Collection(collection_name)
        
        if metadata_list is None:
            metadata_list = [{} for _ in range(len(vectors))]

        try:
            mr = collection.insert([
                file_ids,
                contents,
                vectors,
                metadata_list
            ])
            return mr.primary_keys
        except Exception as e:
            raise Exception(f"ไม่สามารถเพิ่ม vectors ได้: {str(e)}")

    async def search_vectors(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        limit: int = 10,
        field_name: str = "embedding",
        output_fields: List[str] = None,
        filter_expr: str = None
    ) -> List[Dict[str, Any]]:
        """
        ค้นหา vectors ที่ใกล้เคียงที่สุด
        
        Args:
            collection_name: ชื่อของ collection
            query_vectors: vectors ที่ต้องการค้นหา
            limit: จำนวนผลลัพธ์ที่ต้องการ (default: 10)
            field_name: ชื่อ field ที่ต้องการค้นหา (default: "embedding")
            output_fields: รายการ fields ที่ต้องการในผลลัพธ์
            filter_expr: expression สำหรับกรองผลลัพธ์
            
        Returns:
            รายการของผลการค้นหา พร้อมระยะห่างและข้อมูลที่เกี่ยวข้อง
        """
        collection = Collection(collection_name)
        collection.load()  # Make sure collection is loaded

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 16}
        }

        try:
            results = collection.search(
                data=query_vectors,
                anns_field=field_name,
                param=search_params,
                limit=limit,
                output_fields=output_fields,
                expr=filter_expr
            )

            search_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        "id": hit.id,
                        "distance": hit.distance,
                        "score": 1 - hit.distance  # Convert distance to similarity score
                    }
                    
                    # Add output fields if available
                    if output_fields:
                        for field in output_fields:
                            result[field] = hit.entity.get(field)
                            
                    search_results.append(result)

            return search_results
            
        except Exception as e:
            raise Exception(f"ไม่สามารถค้นหา vectors ได้: {str(e)}")

    async def drop_collection(self, collection_name: str) -> None:
        """
        ลบ collection
        
        Args:
            collection_name: ชื่อของ collection ที่ต้องการลบ
        """
        try:
            utility.drop_collection(collection_name)
        except Exception as e:
            raise Exception(f"ไม่สามารถลบ collection ได้: {str(e)}")

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        ดึงข้อมูลสถิติของ collection
        
        Args:
            collection_name: ชื่อของ collection
            
        Returns:
            ข้อมูลสถิติของ collection
        """
        collection = Collection(collection_name)
        try:
            stats = {
                "row_count": collection.num_entities,
                "index_status": collection.indexes,
                "description": collection.schema.description
            }
            return stats
        except Exception as e:
            raise Exception(f"ไม่สามารถดึงข้อมูลสถิติได้: {str(e)}")