# create_test_pdf.py
from fpdf import FPDF

def create_sample_pdf():
    # สร้าง PDF object
    pdf = FPDF()
    
    # เพิ่มหน้าใหม่
    pdf.add_page()
    
    # ตั้งค่าฟอนต์
    pdf.set_font('Arial', 'B', 16)
    
    # เพิ่มข้อความตัวอย่าง
    pdf.cell(0, 10, 'Sample PDF Document', ln=True, align='C')
    
    pdf.set_font('Arial', '', 12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, 'This is a test document created for testing document processing functionality. It contains multiple paragraphs to ensure proper text extraction.')
    
    pdf.ln(10)
    pdf.multi_cell(0, 10, 'The system should be able to extract this text and process it correctly. This will help verify that our PDF processing pipeline is working as expected.')
    
    # บันทึกไฟล์
    pdf.output('test.pdf')

if __name__ == '__main__':
    create_sample_pdf()
    print("Created test.pdf successfully!")