# --- Imports ---
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from io import BytesIO

# FastAPI imports
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ML/AI related imports
from langchain_community.llms import LlamaCpp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
import chromadb
import torch
import pypdf
from dotenv import load_dotenv

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
load_dotenv()

# --- Helper Functions ---
def get_device():
    """
    ตรวจสอบและเลือกอุปกรณ์ที่เหมาะสมสำหรับการประมวลผล
    """
    if torch.cuda.is_available():
        return 'cuda'
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'

def configure_system_settings():
    """
    ตั้งค่าระบบให้เหมาะสมกับแต่ละ platform
    """
    if os.name == 'nt':  # Windows
        import ctypes
        try:
            ctypes.windll.kernel32.SetThreadPriority(
                ctypes.windll.kernel32.GetCurrentThread(), 2)
        except:
            logger.warning("ไม่สามารถตั้งค่า Windows thread priority ได้")
    else:  # Unix-like systems
        try:
            os.nice(10)
        except:
            logger.warning("ไม่สามารถตั้งค่า process nice value ได้")
            
def setup_model_cache():
    """
    จัดการพื้นที่เก็บ cache สำหรับโมเดล
    Returns:
        str: path ของ cache directory
    """
    cache_dir = os.path.join(os.getcwd(), "model_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def initialize_embeddings(device: str, cache_dir: str):
    """
    เริ่มต้นการทำงานของ embeddings model พร้อมระบบ cache
    Args:
        device (str): อุปกรณ์ที่ใช้ประมวลผล (cuda, mps, cpu)
        cache_dir (str): ตำแหน่งที่เก็บ cache
    Returns:
        HuggingFaceEmbeddings: embeddings model ที่พร้อมใช้งาน
    """
    try:
        # โหลด model ก่อนเพื่อให้มั่นใจว่ามีการ download
        model = SentenceTransformer('setu4993/LaBSE', cache_folder=cache_dir)
        
        return HuggingFaceEmbeddings(
            model_name="setu4993/LaBSE",
            model_kwargs={'device': device},
            cache_folder=cache_dir
        )
    except Exception as e:
        logger.error(f"ไม่สามารถโหลด embeddings model ได้: {str(e)}")
        raise

def initialize_llm():
    """
    เริ่มต้นการทำงานของ LLM พร้อมการจัดการหน่วยความจำที่เหมาะสม
    """
    model_path = os.getenv('LLAMA_MODEL_PATH')
    if not model_path:
        raise ValueError("กรุณาตั้งค่า LLAMA_MODEL_PATH ใน .env file")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"ไม่พบไฟล์โมเดลที่ {model_path}")

    device = get_device()
    n_gpu_layers = 1 if device == 'cuda' else 0
    
    # เพิ่มการจัดการหน่วยความจำ
    n_ctx = 4096  # เพิ่มขนาด context
    n_batch = 512  # ลดขนาด batch ลง
    
    logger.info(f"กำลังโหลด LLM บน {device} พร้อมค่า n_ctx={n_ctx}, n_batch={n_batch}")
    
    return LlamaCpp(
        model_path=model_path,
        temperature=0.1,
        max_tokens=512,
        n_ctx=n_ctx,
        n_batch=n_batch,
        n_gpu_layers=n_gpu_layers,
        verbose=True,
        seed=42,  # เพิ่มการกำหนดค่า seed เพื่อความเสถียร
    )

async def extract_pdf_text(file: UploadFile) -> str:
    """
    แปลงไฟล์ PDF เป็นข้อความ
    """
    content = await file.read()
    pdf_reader = pypdf.PdfReader(BytesIO(content))
    return "".join(page.extract_text() for page in pdf_reader.pages)

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    """โครงสร้างคำขอสำหรับการค้นหาเอกสาร"""
    question: str
    filename: str
    student_filename: Optional[str] = None
    custom_prompt: Optional[str] = None

class ComparisonRequest(BaseModel):
    """โครงสร้างคำขอสำหรับการเปรียบเทียบเอกสาร"""
    teacher_file: str
    student_file: str
    custom_prompt: Optional[str] = None

# --- Application Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """จัดการ startup และ shutdown events"""
    try:
        logger.info("กำลังเริ่มต้นแอปพลิเคชัน...")
        configure_system_settings()
        
        # แยกการโหลดคอมโพเนนต์เป็นฟังก์ชันย่อย
        await initialize_components()
        
        yield
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้นแอปพลิเคชัน: {str(e)}")
        raise
    finally:
        logger.info("กำลังปิดแอปพลิเคชัน...")

async def initialize_components():
    """เริ่มต้นคอมโพเนนต์ต่างๆ แบบ async"""
    try:
        global chroma_client, teacher_collection, student_collection, embeddings, llm
        
        # ตั้งค่า cache directory
        cache_dir = setup_model_cache()
        
        # Initialize ChromaDB
        chroma_db_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        logger.info(f"กำลังเชื่อมต่อกับ ChromaDB ที่ {chroma_db_path}")
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        
        # สร้าง collections
        teacher_collection = chroma_client.get_or_create_collection("teacher_documents")
        student_collection = chroma_client.get_or_create_collection("student_documents")
        
        # Initialize embeddings
        device = get_device()
        embeddings = initialize_embeddings(device, cache_dir)
        
        # Initialize LLM แบบ non-blocking
        llm = await asyncio.to_thread(initialize_llm)
        
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้นคอมโพเนนต์: {str(e)}")
        raise

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Initialize Components ---
try:
    # ตั้งค่า cache directory
    cache_dir = setup_model_cache()
    
    # Initialize ChromaDB with better error handling
    chroma_db_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
    logger.info(f"กำลังเชื่อมต่อกับ ChromaDB ที่ {chroma_db_path}")
    chroma_client = chromadb.PersistentClient(path=chroma_db_path)
    teacher_collection = chroma_client.get_or_create_collection(
        name="teacher_documents",
        metadata={"description": "เอกสารสำหรับครูผู้สอน"}
    )
    student_collection = chroma_client.get_or_create_collection(
        name="student_documents",
        metadata={"description": "เอกสารของนักเรียน"}
    )
    logger.info("เชื่อมต่อ ChromaDB สำเร็จ")
    
    # Initialize device and embeddings
    device = get_device()
    logger.info(f"กำลังใช้งานอุปกรณ์: {device}")
    embeddings = initialize_embeddings(device, cache_dir)
    logger.info("โหลด embeddings model สำเร็จ")
    
    # Initialize LLM
    llm = initialize_llm()
    logger.info("โหลด LLM สำเร็จ")

except Exception as e:
    logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้นคอมโพเนนต์: {str(e)}")
    raise

# --- API Endpoints ---
@app.get("/system-check")
async def system_check():
    """ตรวจสอบการตั้งค่าระบบ"""
    return {
        "model_path_exists": os.path.exists(os.getenv('LLAMA_MODEL_PATH', '')),
        "device": get_device(),
        "pytorch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "env_vars": {
            "llama_model_path": os.getenv('LLAMA_MODEL_PATH'),
            "chroma_db_path": os.getenv('CHROMA_DB_PATH')
        }
    }

@app.post("/process-teacher-document")
async def process_teacher_document(file: UploadFile):
    """ประมวลผลเอกสารของครู"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF เท่านั้น")
        
        logger.info(f"กำลังประมวลผลเอกสารครู: {file.filename}")
        text_content = await extract_pdf_text(file)
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="ไม่สามารถดึงข้อความจาก PDF ได้ หรือไฟล์ว่างเปล่า")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="ไม่สามารถแบ่งเนื้อหาเป็นส่วนย่อยได้")
        
        embeddings_list = embeddings.embed_documents(chunks)
        
        teacher_collection.add(
            documents=chunks,
            embeddings=embeddings_list,
            metadatas=[{"file_name": file.filename, "type": "teacher", "chunk_index": i} for i in range(len(chunks))],
            ids=[f"{file.filename}_chunk_{i}" for i in range(len(chunks))]
        )
        
        logger.info(f"ประมวลผลเอกสารครูสำเร็จ: {file.filename}")
        return {
            "status": "success",
            "message": "เอกสารครูถูกประมวลผลเรียบร้อยแล้ว",
            "chunks_processed": len(chunks)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการประมวลผลเอกสารครู: {str(e)}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}")

@app.post("/process-student-document")
async def process_student_document(file: UploadFile):
    """ประมวลผลเอกสารของนักเรียน"""
    try:
        text_content = await extract_pdf_text(file)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        student_collection.add(
            documents=chunks,
            metadatas=[{"file_name": file.filename, "type": "student"} for _ in chunks],
            ids=[f"{file.filename}_chunk_{i}" for i in range(len(chunks))]
        )
        
        return {"status": "success", "message": "เอกสารนักเรียนถูกประมวลผลเรียบร้อยแล้ว"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{filename}")
async def check_document_status(filename: str):
    """ตรวจสอบสถานะการประมวลผลของเอกสาร"""
    try:
        teacher_result = teacher_collection.get(
            where={"file_name": filename},
            limit=1
        )
        student_result = student_collection.get(
            where={"file_name": filename},
            limit=1
        )
        
        return {
            "is_processed": len(teacher_result['ids']) > 0 or len(student_result['ids']) > 0,
            "type": "teacher" if len(teacher_result['ids']) > 0 else "student" if len(student_result['ids']) > 0 else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_document(request: QueryRequest):
    """ค้นหาข้อมูลจากเอกสารโดยใช้ RAG"""
    try:
        question_embedding = embeddings.embed_query(request.question)
        teacher_docs = teacher_collection.query(
            query_embeddings=[question_embedding],
            where={"file_name": request.filename},
            n_results=3
        )

        context = "\n\n".join(teacher_docs['documents'][0])
        if request.student_filename:
            student_docs = student_collection.get(
                where={"file_name": request.student_filename}
            )
            if student_docs['documents']:
                context += f"\n\nStudent's document:\n{student_docs['documents'][0]}"

        prompt = request.custom_prompt or f"""
        Based on the following context, provide a clear and detailed answer.
        If student's document is provided, include analysis of the student's understanding.

        Context:
        {context}

        Question:
        {request.question}

        Answer:
        """

        response = llm(prompt)
        return {"response": response.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-documents")
async def compare_documents(request: ComparisonRequest):
    """เปรียบเทียบเอกสารครูและนักเรียน"""
    try:
        teacher_docs = teacher_collection.get(
            where={"file_name": request.teacher_file}
        )
        student_docs = student_collection.get(
            where={"file_name": request.student_file}
        )

        base_prompt = request.custom_prompt or """
        Compare the following teacher's reference document and student's submission.
        Provide detailed feedback on:
        1. Content accuracy
        2. Completeness
        3. Understanding of concepts
        
        Teacher's document:
        {teacher_content}
        
        Student's submission:
        {student_content}
        
        Analysis:
        """

        response = llm(base_prompt.format(
            teacher_content="\n".join(teacher_docs['documents']),
            student_content="\n".join(student_docs['documents'])
        ))

        return {
            "comparison_result": response,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """ตรวจสอบสถานะของระบบ"""
    try:
        # ทดสอบการทำงานของ LLM
        test_prompt = "Hello"
        response = llm(test_prompt)
        
        return {
            "status": "healthy",
            "components": {
                "llm": "operational",
                "embeddings": "operational",
                "chromadb": "operational"
            },
            "device": get_device(),
            "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024  # MB
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ระบบไม่พร้อมใช้งาน: {str(e)}"
        )