# run.py
from app import create_app
from app.core.config import config  # เพิ่มการ import config

app = create_app()

if __name__ == "__main__":
    """
    จุดเริ่มต้นของแอปพลิเคชัน
    ใช้ค่า configuration จาก AppConfig เพื่อกำหนดการทำงานของ server
    """
    app.run(
        host='0.0.0.0',           # รับการเชื่อมต่อจากทุก IP
        port=config.FLASK_PORT,    # ใช้ port จาก configuration
        debug=config.FLASK_DEBUG   # สถานะ debug จาก configuration
    )