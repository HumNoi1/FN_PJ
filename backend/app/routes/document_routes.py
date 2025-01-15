# app/routes/document_routes.py
from flask import Blueprint, request, jsonify
from app.services.milvus_service import MilvusService
from app.services.pdf_service import PDFProcessingService
import tempfile
import os

# สร้าง Blueprint สำหรับจัดการเอกสาร
document_bp = Blueprint('document', __name__)

# สร้างตัวแปรสำหรับเก็บ service instances
milvus_service = None
pdf_service = PDFProcessingService()

def init_routes(ms: MilvusService):
    """
    ฟังก์ชันสำหรับเริ่มต้นค่า routes โดยรับ dependencies ที่จำเป็น
    
    Args:
        ms: Instance ของ MilvusService ที่จะใช้ในการจัดการ vectors
    """
    global milvus_service
    milvus_service = ms

@document_bp.route('/process', methods=['POST'])
async def process_document():
    """
    Endpoint สำหรับประมวลผลเอกสาร PDF
    - รับไฟล์ PDF
    - แปลงเป็นข้อความ
    - สร้าง embeddings
    - จัดเก็บใน Milvus
    """
    if 'file' not in request.files:
        return jsonify({"error": "ไม่พบไฟล์"}), 400
        
    file = request.files['file']
    if not file.filename.endswith('.pdf'):
        return jsonify({"error": "รองรับเฉพาะไฟล์ PDF เท่านั้น"}), 400
    
    try:
        # บันทึกไฟล์ชั่วคราว
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            
            # ประมวลผลไฟล์
            result = await pdf_service.process_pdf_file(temp_file.name)
            
            # จัดเก็บใน Milvus
            document_id = request.form.get('document_id')
            collection_name = request.form.get('collection_name', 'documents')
            
            # เพิ่ม vectors ลงใน Milvus
            ids = await milvus_service.insert_vectors(
                collection_name=collection_name,
                file_ids=[document_id] * len(result['chunks']),
                contents=result['chunks'],
                vectors=result['embeddings'],
                metadata_list=[{'index': i} for i in range(len(result['chunks']))]
            )
            
            # ลบไฟล์ชั่วคราว
            os.unlink(temp_file.name)
            
            return jsonify({
                "status": "success",
                "message": "ประมวลผลไฟล์เสร็จสิ้น",
                "data": {
                    "document_id": document_id,
                    "chunk_count": len(result['chunks']),
                    "vector_ids": ids
                }
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500