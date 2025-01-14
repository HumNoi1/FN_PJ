from flask import Flask
from flask_cors import CORS  # เพิ่มการ import CORS
from routes.embedding_routes import embedding_bp
from routes.evaluation_routes import evaluation_bp

# สร้าง Flask application
app = Flask(__name__)

# กำหนดค่า CORS ให้กับ application
# เราจำเป็นต้องกำหนดค่านี้เพื่อให้ Next.js frontend สามารถเรียกใช้ API ได้
CORS(app, resources={
    r"/api/*": {  # กำหนดให้ทุก endpoint ที่ขึ้นต้นด้วย /api/
        "origins": [
            "http://localhost:3000",   # สำหรับ development บน localhost
            "http://127.0.0.1:3000",   # สำหรับกรณีใช้ IP แทน localhost
        ],
        # อนุญาต methods ทั้งหมดที่จำเป็น
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        # อนุญาต headers ที่จำเป็น
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ลงทะเบียน blueprints เหมือนเดิม
app.register_blueprint(embedding_bp, url_prefix='/api/embedding')
app.register_blueprint(evaluation_bp, url_prefix='/api/evaluation')

# เพิ่ม error handler เพื่อจัดการข้อผิดพลาดทั่วไป
@app.errorhandler(Exception)
def handle_error(error):
    return {
        "success": False,
        "error": str(error),
        "error_type": error.__class__.__name__
    }, getattr(error, 'code', 500)

if __name__ == '__main__':
    # รัน Flask application
    app.run(
        host='0.0.0.0',  # อนุญาตการเข้าถึงจากภายนอก
        port=5000,       # กำหนด port เป็น 5000
        debug=True       # เปิดโหมด debug สำหรับการพัฒนา
    )