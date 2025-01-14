# services/embedding_service.py
from typing import List, Dict, Any, Optional
import json

class EmbeddingService:
    def __init__(self, embeddings, collection):
        self.embeddings = embeddings
        self.collection = collection

    async def process_file_from_url(self, file_url: str, file_id: str, file_type: str) -> Dict[str, Any]:
        """
        ดาวน์โหลดไฟล์จาก URL และทำ embedding พร้อมบันทึกลง ChromaDB
        """
        try:
            # ดาวน์โหลดและประมวลผลไฟล์เหมือนเดิม...
            
            # เพิ่มการตรวจสอบการบันทึกข้อมูล
            chunks_with_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_id}_{i}"
                metadata = {
                    "file_id": file_id,
                    "file_type": file_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source_url": file_url
                }
                chunks_with_metadata.append((chunk_id, chunk, metadata))
            
            # บันทึกลง ChromaDB พร้อมตรวจสอบ
            try:
                self.collection.add(
                    ids=[item[0] for item in chunks_with_metadata],
                    documents=[item[1] for item in chunks_with_metadata],
                    metadatas=[item[2] for item in chunks_with_metadata],
                    embeddings=self.embeddings.embed_documents([item[1] for item in chunks_with_metadata])
                )
                
                # ตรวจสอบว่าบันทึกสำเร็จหรือไม่
                verify = await self.get_document_by_id(file_id)
                if not verify['success']:
                    raise Exception(f"ไม่สามารถยืนยันการบันทึกข้อมูลได้: {verify['error']}")
                
            except Exception as e:
                raise Exception(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}")

            return {
                "success": True,
                "chunks_processed": len(chunks),
                "file_id": file_id,
                "metadata": chunks_with_metadata[0][2]  # ส่งคืน metadata ตัวอย่าง
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_id": file_id
            }

    async def get_document_by_id(self, file_id: str) -> Dict[str, Any]:
        """
        ดึงเอกสารจาก ChromaDB โดยใช้ file_id พร้อมการตรวจสอบและ logging ที่ละเอียด
        """
        try:
            # แสดงข้อมูลการค้นหาเพื่อการตรวจสอบ
            print(f"กำลังค้นหาเอกสาร ID: {file_id}")
            
            # ลองดึงข้อมูลทั้งหมดก่อนเพื่อตรวจสอบ
            all_data = self.collection.get()
            print(f"จำนวนเอกสารทั้งหมดใน collection: {len(all_data['ids'])}")
            
            # ค้นหาเอกสารที่ต้องการ
            results = self.collection.get(
                where={"file_id": file_id}
            )
            
            if not results['documents']:
                # ถ้าไม่พบ ลองตรวจสอบ metadata ทั้งหมดเพื่อหาปัญหา
                all_metadata = all_data['metadatas']
                file_ids_found = set(meta.get('file_id') for meta in all_metadata if meta.get('file_id'))
                print(f"file_ids ที่พบในระบบ: {json.dumps(list(file_ids_found), indent=2)}")
                
                return {
                    "success": False,
                    "error": f"ไม่พบเอกสารที่มี ID: {file_id}",
                    "debug_info": {
                        "total_documents": len(all_data['ids']),
                        "available_file_ids": list(file_ids_found)
                    }
                }

            # รวมชิ้นส่วนเอกสารเข้าด้วยกันตามลำดับ
            sorted_chunks = sorted(zip(results['documents'], results['metadatas']), 
                                key=lambda x: x[1].get('chunk_index', 0))
            
            complete_document = "\n".join(chunk[0] for chunk in sorted_chunks)
            
            return {
                "success": True,
                "document": complete_document,
                "metadata": sorted_chunks[0][1],  # ใช้ metadata จากชิ้นแรก
                "total_chunks": len(sorted_chunks)
            }
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการดึงเอกสาร: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def debug_collection(self) -> Dict[str, Any]:
        """
        เมธอดสำหรับตรวจสอบข้อมูลใน collection
        """
        try:
            all_data = self.collection.get()
            return {
                "success": True,
                "total_documents": len(all_data['ids']),
                "metadata_samples": all_data['metadatas'][:5],
                "ids_sample": all_data['ids'][:5]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }