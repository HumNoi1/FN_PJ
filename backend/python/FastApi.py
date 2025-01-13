import logging
import os
import platform
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from io import BytesIO

# FastAPI imports
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ML/AI related imports
from langchain_community.llms import LlamaCpp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import chromadb
import torch
import pypdf
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileProcessor:
    """จัดการการประมวลผลและติดตามสถานะของไฟล์"""
    
    def __init__(self):
        self.processed_files = {}
        self.status_file = Path("processed_files.json")
        self._load_status()
    
    def _load_status(self):
        if self.status_file.exists():
            with open(self.status_file, "r") as f:
                self.processed_files = json.load(f)
    
    def _save_status(self):
        with open(self.status_file, "w") as f:
            json.dump(self.processed_files, f)
    
    def mark_as_processed(self, filename: str):
        self.processed_files[filename] = True
        self._save_status()
    
    def is_processed(self, filename: str) -> bool:
        return self.processed_files.get(filename, False)

class SystemConfig:
    """System configuration handler for cross-platform compatibility"""
    
    def __init__(self):
        self.system = platform.system()
        self.device = self._detect_device()
        self.model_path = self._get_model_path()
        self.db_path = self._get_db_path()
        
    def _detect_device(self) -> str:
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'
    
    def _get_model_path(self) -> Path:
        base_path = os.getenv('LLAMA_MODEL_PATH')
        if base_path:
            return Path(base_path).resolve()
            
        possible_paths = [
            Path('models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'),
            Path('../models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'),
            Path('../../models/Llama-3.2-3B-Instruct-Q4_K_M.gguf'),
            Path(os.path.expanduser('~/models/Llama-3.2-3B-Instruct-Q4_K_M.gguf')),
        ]
        
        project_model_path = Path(__file__).parent.parent / 'models' / 'Llama-3.2-3B-Instruct-Q4_K_M.gguf'
        possible_paths.append(project_model_path)
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found model at: {path}")
                return path.resolve()
                
        raise ValueError(
            "Model file not found. Please either:\n"
            "1. Set LLAMA_MODEL_PATH environment variable, or\n"
            "2. Place the model in one of these locations:\n" + 
            "\n".join(f"   - {p}" for p in possible_paths)
        )
    
    def _get_db_path(self) -> Path:
        base_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        return Path(base_path).resolve()
    
    def configure_process_priority(self):
        try:
            if self.system == 'Windows':
                import ctypes
                ctypes.windll.kernel32.SetThreadPriority(
                    ctypes.windll.kernel32.GetCurrentThread(), 
                    2
                )
            else:
                os.nice(10)
        except Exception as e:
            logger.warning(f"Could not set process priority: {str(e)}")
            
    def get_llm_config(self) -> Dict[str, Any]:
        n_gpu_layers = 1 if self.device == 'cuda' else 0
        
        return {
            "model_path": str(self.model_path),
            "temperature": 0.1,
            "max_tokens": 512,
            "n_ctx": 2048,
            "n_gpu_layers": n_gpu_layers,
            "callback_manager": CallbackManager([StreamingStdOutCallbackHandler()]),
            "verbose": True
        }

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    filename: str
    custom_prompt: Optional[str] = None

class CompareRequest(BaseModel):
    teacher_file: str
    student_file: str
    question: Optional[str] = None
    custom_prompt: Optional[str] = None

# Initialize components
system_config = SystemConfig()
file_processor = FileProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initializing application...")
        system_config.configure_process_priority()
        yield
    finally:
        logger.info("Shutting down application...")

# Initialize FastAPI with lifespan manager
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize AI components
try:
    chroma_client = chromadb.PersistentClient(path=str(system_config.db_path))
    collection = chroma_client.get_or_create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )
    
    embeddings = HuggingFaceEmbeddings(
        model_name="setu4993/LaBSE",
        model_kwargs={'device': system_config.device}
    )
    
    llm = LlamaCpp(**system_config.get_llm_config())
    
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}")
    raise

# API Endpoints

@app.get("/system-info")
async def get_system_info():
    """แสดงข้อมูลการตั้งค่าระบบ"""
    return {
        "platform": system_config.system,
        "device": system_config.device,
        "model_path": str(system_config.model_path),
        "db_path": str(system_config.db_path),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "mps_available": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    }

@app.get("/status/{filename}")
async def check_file_status(filename: str):
    """ตรวจสอบสถานะการประมวลผลของไฟล์"""
    return {
        "filename": filename,
        "is_processed": file_processor.is_processed(filename)
    }

@app.post("/process-pdf")
async def process_pdf(
    file: UploadFile,
    is_teacher: bool = False
):
    """ประมวลผลไฟล์ PDF และจัดเก็บใน ChromaDB"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        contents = await file.read()
        pdf_file = BytesIO(contents)
        
        # อ่านเนื้อหา PDF
        pdf_reader = pypdf.PdfReader(pdf_file)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()
        
        # แบ่งเนื้อหาเป็นส่วนย่อย
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(text_content)
        
        # สร้าง embeddings สำหรับไฟล์ของครู
        if is_teacher:
            embeddings_list = embeddings.embed_documents(chunks)
            collection.add(
                documents=chunks,
                embeddings=embeddings_list,
                ids=[f"{file.filename}-chunk-{i}" for i in range(len(chunks))],
                metadatas=[{"source": file.filename} for _ in chunks]
            )
        
        file_processor.mark_as_processed(file.filename)
        return {"message": "File processed successfully"}
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_document(request: QueryRequest):
    """ค้นหาคำตอบจากเอกสารโดยใช้ LLM"""
    try:
        # ค้นหาข้อความที่เกี่ยวข้องจาก ChromaDB
        results = collection.query(
            query_texts=[request.question],
            n_results=5,
            where={"source": request.filename}
        )
        
        # สร้าง prompt สำหรับ LLM
        context = "\n".join(results["documents"][0])
        prompt = f"""Based on the following context, please answer the question.
        
Context:
{context}

Question: {request.question}

Answer:"""
        
        # ใช้ custom prompt ถ้ามี
        if request.custom_prompt:
            prompt = f"{request.custom_prompt}\n\nContext:\n{context}"
        
        # ส่ง prompt ไปยัง LLM
        response = llm(prompt)
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Error querying document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    """ลบข้อมูลไฟล์ออกจาก ChromaDB"""
    try:
        collection.delete(
            where={"source": filename}
        )
        
        if filename in file_processor.processed_files:
            del file_processor.processed_files[filename]
            file_processor._save_status()
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-pdfs")
async def compare_documents(request: CompareRequest):
    """เปรียบเทียบเอกสารของครูและนักเรียน"""
    try:
        # ค้นหาเนื้อหาของไฟล์ครู
        teacher_results = collection.query(
            query_texts=[""],
            n_results=10,
            where={"source": request.teacher_file}
        )
        
        # สร้าง prompt สำหรับการเปรียบเทียบ
        teacher_context = "\n".join(teacher_results["documents"][0])
        
        if request.question:
            prompt = f"""Compare the teacher's document with the student's answer:

Teacher's document:
{teacher_context}

Question: {request.question}

Please analyze and provide feedback on:
1. The accuracy of the student's answer
2. What was done well
3. Areas for improvement
4. Suggested corrections
"""
        else:
            prompt = f"""Analyze the content and provide:
1. Main points covered
2. Accuracy of information
3. Areas that need clarification
4. Suggestions for improvement
"""
        
        # ใช้ custom prompt ถ้ามี
        if request.custom_prompt:
            prompt = f"{request.custom_prompt}\n\nTeacher's document:\n{teacher_context}"
        
        # ส่ง prompt ไปยัง LLM
        comparison = llm(prompt)
        return {"comparison": comparison}
        
    except Exception as e:
        logger.error(f"Error comparing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)