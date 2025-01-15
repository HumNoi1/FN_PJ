# services/pdf_service.py
from pypdf import PdfReader
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import numpy as np

class PDFProcessingService:
    def __init__(self):
        # ใช้ MiniLM-L6-v2 model สำหรับสร้าง embeddings เพราะมีความสมดุลระหว่างประสิทธิภาพและขนาด
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # กำหนดความยาวสูงสุดของ chunk เพื่อไม่ให้ข้อความยาวเกินไป
        self.max_chunk_length = 512

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """
        อ่านไฟล์ PDF และแปลงเป็นข้อความ
        
        Args:
            file_path: พาธของไฟล์ PDF
            
        Returns:
            ข้อความทั้งหมดจากไฟล์ PDF
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"ไม่สามารถอ่านไฟล์ PDF ได้: {str(e)}")

    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        แบ่งข้อความเป็นส่วนย่อยๆ เพื่อให้เหมาะกับการสร้าง embeddings
        
        Args:
            text: ข้อความที่ต้องการแบ่ง
            
        Returns:
            รายการของข้อความที่แบ่งแล้ว
        """
        # แบ่งตามย่อหน้า
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        chunks = []
        
        current_chunk = ""
        for paragraph in paragraphs:
            # ถ้า paragraph เดียวยาวเกินไป ให้แบ่งตามประโยค
            if len(paragraph) > self.max_chunk_length:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= self.max_chunk_length:
                        current_chunk += sentence + '. '
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
            else:
                if len(current_chunk) + len(paragraph) <= self.max_chunk_length:
                    current_chunk += paragraph + '\n'
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    async def create_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        """
        สร้าง embeddings จากข้อความ
        
        Args:
            chunks: รายการของข้อความที่ต้องการแปลงเป็น embeddings
            
        Returns:
            รายการของ embeddings vectors
        """
        try:
            embeddings = self.model.encode(chunks)
            return embeddings.tolist()
        except Exception as e:
            raise Exception(f"ไม่สามารถสร้าง embeddings ได้: {str(e)}")

    async def process_pdf_file(self, file_path: str) -> Dict:
        """
        ประมวลผลไฟล์ PDF ทั้งหมด ตั้งแต่การอ่านไฟล์จนถึงการสร้าง embeddings
        
        Args:
            file_path: พาธของไฟล์ PDF
            
        Returns:
            Dictionary ที่มีข้อความและ embeddings
        """
        # อ่านข้อความจาก PDF
        text = await self.extract_text_from_pdf(file_path)
        
        # แบ่งข้อความเป็นส่วนย่อย
        chunks = self.split_text_into_chunks(text)
        
        # สร้าง embeddings
        embeddings = await self.create_embeddings(chunks)
        
        return {
            "text": text,
            "chunks": chunks,
            "embeddings": embeddings
        }