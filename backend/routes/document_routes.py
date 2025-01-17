# routes/document_routes.py
from flask import Blueprint, request, jsonify
import traceback
from services.milvus_service import MilvusService
from services.pdf_service import PDFProcessingService
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
    มีการตรวจสอบความถูกต้องของข้อมูลอย่างละเอียด
    """
    # 1. ตรวจสอบว่ามีไฟล์ถูกส่งมาหรือไม่
    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "กรุณาเลือกไฟล์ที่ต้องการอัพโหลด",
            "details": "ไม่พบ file field ในคำขอ"
        }), 400

    file = request.files['file']

    # 2. ตรวจสอบชื่อไฟล์
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "กรุณาเลือกไฟล์ที่ต้องการอัพโหลด",
            "details": "ไม่พบชื่อไฟล์"
        }), 400

    # 3. ตรวจสอบนามสกุลไฟล์
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            "status": "error",
            "message": "รองรับเฉพาะไฟล์ PDF เท่านั้น",
            "details": f"ไฟล์ที่อัพโหลด: {file.filename}"
        }), 400

    # 4. ตรวจสอบ document_id
    document_id = request.form.get('document_id')
    if not document_id:
        return jsonify({
            "status": "error",
            "message": "กรุณาระบุ document_id",
            "details": "ไม่พบ document_id ในคำขอ"
        }), 400

    # 5. ตรวจสอบ file_type
    file_type = request.form.get('file_type')
    if not file_type or file_type not in ['teacher', 'student']:
        return jsonify({
            "status": "error",
            "message": "กรุณาระบุประเภทไฟล์ให้ถูกต้อง",
            "details": "file_type ต้องเป็น 'teacher' หรือ 'student'"
        }), 400

    try:
        # บันทึกไฟล์ชั่วคราวพร้อมบันทึก log
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            print(f"กำลังบันทึกไฟล์ชั่วคราวที่: {temp_file.name}")
            file.save(temp_file.name)
            
            # ตรวจสอบขนาดไฟล์
            file_size = os.path.getsize(temp_file.name)
            print(f"ขนาดไฟล์ที่บันทึก: {file_size} bytes")
            
            if file_size == 0:
                os.unlink(temp_file.name)  # ลบไฟล์ที่ว่างเปล่า
                return jsonify({
                    "status": "error",
                    "message": "ไฟล์ว่างเปล่า",
                    "details": "ไฟล์ที่อัพโหลดมีขนาดเป็น 0"
                }), 400

            # ประมวลผลไฟล์
            result = await pdf_service.process_pdf_file(temp_file.name)
            
            # ลบไฟล์ชั่วคราว
            os.unlink(temp_file.name)
            
            return jsonify({
                "status": "success",
                "message": "ประมวลผลไฟล์เสร็จสิ้น",
                "data": {
                    "document_id": document_id,
                    "file_type": file_type,
                    "file_name": file.filename,
                    "chunk_count": len(result['chunks'])
                }
            })

    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}",
            "details": traceback.format_exc()
        }), 500