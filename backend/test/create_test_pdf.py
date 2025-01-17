# test/create_test_pdf.py
from fpdf import FPDF
import os

def create_teacher_reference():
    """สร้างเอกสารอ้างอิงของอาจารย์เกี่ยวกับแนวคิดวิศวกรรมซอฟต์แวร์"""
    pdf = FPDF()
    pdf.add_page()
    # ใช้ฟอนต์ที่รองรับภาษาไทย
    pdf.add_font('Sarabun', '', 'test/fonts/THSarabunNew.ttf', uni=True)
    pdf.set_font('Sarabun', size=16)  # ปรับขนาดฟอนต์ให้เหมาะสมกับภาษาไทย
    
    content = """แนวคิดวิศวกรรมซอฟต์แวร์

1. วงจรการพัฒนาซอฟต์แวร์ (Software Development Life Cycle: SDLC)
วงจรการพัฒนาซอฟต์แวร์เป็นกระบวนการที่มีระเบียบแบบแผน ประกอบด้วยขั้นตอนดังนี้:

การวิเคราะห์ความต้องการ: 
- การเก็บรวบรวมความต้องการจากผู้ใช้งาน
- การวิเคราะห์ความเป็นไปได้ของระบบ
- การจัดทำเอกสารข้อกำหนดความต้องการ

การออกแบบ:
- การออกแบบสถาปัตยกรรมระบบ
- การออกแบบฐานข้อมูล
- การออกแบบส่วนติดต่อผู้ใช้
- การออกแบบโมดูลและคลาส

การพัฒนา:
- การเขียนโค้ดตามที่ได้ออกแบบไว้
- การทำ Code Review
- การทำ Unit Testing

การทดสอบ:
- การทดสอบระดับโมดูล
- การทดสอบการทำงานร่วมกัน
- การทดสอบระบบโดยรวม
- การทดสอบการยอมรับโดยผู้ใช้

2. แนวคิดการพัฒนาแบบอไจล์ (Agile)
แนวคิดการพัฒนาแบบอไจล์เน้นความยืดหยุ่นและการปรับตัว โดยมีหลักการสำคัญ:
- การพัฒนาแบบค่อยเป็นค่อยไปและต่อเนื่อง
- การทำงานเป็นทีมแบบ Self-organizing
- การสื่อสารแบบใกล้ชิดกับลูกค้า
- การพร้อมรับมือกับการเปลี่ยนแปลง

3. การประกันคุณภาพซอฟต์แวร์
การประกันคุณภาพซอฟต์แวร์มีองค์ประกอบที่สำคัญ:
- คุณภาพของโค้ด: การเขียนโค้ดที่อ่านง่าย บำรุงรักษาได้
- กลยุทธ์การทดสอบ: วิธีการทดสอบที่ครอบคลุม
- การจัดทำเอกสาร: เอกสารประกอบที่ครบถ้วน
- ประสิทธิภาพ: การทำงานที่รวดเร็วและใช้ทรัพยากรอย่างเหมาะสม"""
    
    pdf.multi_cell(0, 10, content)
    pdf.output("test/test_files/teacher_reference.pdf")

def create_student_answers():
    """สร้างตัวอย่างคำตอบของนักเรียนในระดับคุณภาพต่างๆ"""
    # คำตอบคุณภาพดี
    good_answer = FPDF()
    good_answer.add_page()
    good_answer.add_font('Sarabun', '', 'test/fonts/THSarabunNew.ttf', uni=True)
    good_answer.set_font('Sarabun', size=16)
    good_content = """คำตอบเรื่อง แนวคิดวิศวกรรมซอฟต์แวร์

วงจรการพัฒนาซอฟต์แวร์ (SDLC) เป็นกระบวนการที่มีความสำคัญในการพัฒนาซอฟต์แวร์ เริ่มจากการวิเคราะห์ความต้องการที่ต้องทำอย่างละเอียด เพื่อให้เข้าใจปัญหาและความต้องการของผู้ใช้อย่างถ่องแท้ 

ในขั้นตอนการออกแบบ เราต้องคำนึงถึงทั้งสถาปัตยกรรมระบบและการออกแบบในระดับละเอียด ซึ่งจะส่งผลต่อความยืดหยุ่นและการบำรุงรักษาระบบในอนาคต การออกแบบที่ดีจะช่วยลดปัญหาในการพัฒนาและการแก้ไขระบบ

การพัฒนาต้องยึดตามแบบที่ได้ออกแบบไว้ และมีการทำ Code Review เพื่อให้แน่ใจว่าโค้ดมีคุณภาพ การทดสอบต้องทำอย่างครอบคลุมทั้ง Unit Testing, Integration Testing และ System Testing

แนวคิดแบบอไจล์ช่วยให้ทีมพัฒนาซอฟต์แวร์ได้อย่างมีประสิทธิภาพ โดยเน้นการทำงานเป็น Sprint และมีการ Review กับลูกค้าอย่างสม่ำเสมอ ทำให้สามารถปรับเปลี่ยนตามความต้องการที่เปลี่ยนแปลงได้ทันที"""
    
    good_answer.multi_cell(0, 10, good_content)
    good_answer.output("test/test_files/student_good.pdf")

    # คำตอบคุณภาพปานกลาง
    average_answer = FPDF()
    average_answer.add_page()
    average_answer.add_font('Sarabun', '', 'test/fonts/THSarabunNew.ttf', uni=True)
    average_answer.set_font('Sarabun', size=16)
    average_content = """คำตอบเรื่อง แนวคิดวิศวกรรมซอฟต์แวร์

SDLC คือขั้นตอนการพัฒนาซอฟต์แวร์ ประกอบด้วยการวิเคราะห์ความต้องการ การออกแบบ การพัฒนา การทดสอบ และการนำไปใช้งาน แต่ละขั้นตอนมีความสำคัญต่อการพัฒนาซอฟต์แวร์

การพัฒนาแบบอไจล์เป็นวิธีการที่ทำงานเป็นรอบๆ มีการพูดคุยกับลูกค้าบ่อยๆ และสามารถปรับเปลี่ยนได้ตามความต้องการ การทำงานแบบนี้ช่วยให้พัฒนาซอฟต์แวร์ได้รวดเร็วขึ้น"""
    
    average_answer.multi_cell(0, 10, average_content)
    average_answer.output("test/test_files/student_average.pdf")

    # คำตอบคุณภาพต่ำ
    poor_answer = FPDF()
    poor_answer.add_page()
    poor_answer.add_font('Sarabun', '', 'test/fonts/THSarabunNew.ttf', uni=True)
    poor_answer.set_font('Sarabun', size=16)
    poor_content = """คำตอบเรื่อง แนวคิดวิศวกรรมซอฟต์แวร์

SDLC มีหลายขั้นตอน เริ่มจากวิเคราะห์ แล้วก็พัฒนา แล้วก็ทดสอบ ต้องทำตามขั้นตอนให้ครบ

อไจล์คือการทำงานแบบยืดหยุ่น ทำให้ทำงานได้เร็วขึ้น"""
    
    poor_answer.multi_cell(0, 10, poor_content)
    poor_answer.output("test/test_files/student_poor.pdf")

def setup_test_environment():
    """เตรียมสภาพแวดล้อมสำหรับการทดสอบ"""
    # สร้างโฟลเดอร์สำหรับเก็บไฟล์ทดสอบ
    os.makedirs("test/test_files", exist_ok=True)
    
    # สร้างโฟลเดอร์สำหรับเก็บฟอนต์
    os.makedirs("test/fonts", exist_ok=True)
    
    # ตรวจสอบว่ามีฟอนต์หรือไม่
    if not os.path.exists("test/fonts/THSarabunNew.ttf"):
        print("กรุณาดาวน์โหลดฟอนต์ THSarabunNew.ttf และวางในโฟลเดอร์ test/fonts")
        return False
    return True

if __name__ == "__main__":
    if setup_test_environment():
        create_teacher_reference()
        create_student_answers()
        print("สร้างไฟล์ PDF สำหรับทดสอบเรียบร้อยแล้ว")
    else:
        print("ไม่สามารถสร้างไฟล์ PDF ได้ กรุณาตรวจสอบการติดตั้งฟอนต์")