from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import LlamaCpp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
import pypdf
from typing import Dict, Optional
from pydantic import BaseModel
import os

# Initialize FastAPI and middleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Initialize ChromaDB collections for different document types
chroma_client = chromadb.PersistentClient(path="./chroma_db")
teacher_collection = chroma_client.get_or_create_collection(name="teacher_documents")
student_collection = chroma_client.get_or_create_collection(name="student_documents")

# Initialize AI components
embeddings = HuggingFaceEmbeddings(
    model_name="setu4993/LaBSE",
    model_kwargs={'device': 'mps' if torch.backends.mps.is_available() else 'cpu'}
)

llm = LlamaCpp(
    model_path="path/to/model.gguf",
    temperature=0.1,
    max_tokens=512,
    n_ctx=2048
)

class QueryRequest(BaseModel):
    question: str
    filename: str
    student_filename: Optional[str] = None
    custom_prompt: Optional[str] = None

@app.post("/process-teacher-document")
async def process_teacher_document(file: UploadFile):
    """Process teacher's document with vector embeddings for later retrieval"""
    try:
        # 1. Extract text from PDF
        text_content = await extract_pdf_text(file)
        
        # 2. Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        # 3. Generate embeddings and store in ChromaDB
        embeddings_list = embeddings.embed_documents(chunks)
        
        # 4. Store in teacher collection
        teacher_collection.add(
            documents=chunks,
            embeddings=embeddings_list,
            metadatas=[{"file_name": file.filename, "type": "teacher"} for _ in chunks],
            ids=[f"{file.filename}_chunk_{i}" for i in range(len(chunks))]
        )
        
        return {"status": "success", "message": "Teacher document processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-student-document")
async def process_student_document(file: UploadFile):
    """Process student's document for comparison"""
    try:
        # 1. Extract text from PDF
        text_content = await extract_pdf_text(file)
        
        # 2. Split and store in student collection
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text_content)
        
        # 3. Store in student collection
        student_collection.add(
            documents=chunks,
            metadatas=[{"file_name": file.filename, "type": "student"} for _ in chunks],
            ids=[f"{file.filename}_chunk_{i}" for i in range(len(chunks))]
        )
        
        return {"status": "success", "message": "Student document processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare-documents")
async def compare_documents(request: ComparisonRequest):
    """Compare teacher and student documents"""
    try:
        # 1. Retrieve documents
        teacher_docs = teacher_collection.get(
            where={"file_name": request.teacher_file}
        )
        student_docs = student_collection.get(
            where={"file_name": request.student_file}
        )

        # 2. Generate comparison prompt
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

        # 3. Generate comparison using LLM
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
    
@app.get("/status/{filename}")
async def check_document_status(filename: str):
    """ตรวจสอบสถานะการประมวลผลของเอกสาร"""
    try:
        # ตรวจสอบในทั้งสองคอลเลกชัน
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
        # 1. ค้นหาเอกสารอ้างอิงของครู
        question_embedding = embeddings.embed_query(request.question)
        teacher_docs = teacher_collection.query(
            query_embeddings=[question_embedding],
            where={"file_name": request.filename},
            n_results=3
        )

        # 2. ถ้ามีการระบุไฟล์นักเรียน ให้ดึงข้อมูลมาเปรียบเทียบด้วย
        context = "\n\n".join(teacher_docs['documents'][0])
        if request.student_filename:
            student_docs = student_collection.get(
                where={"file_name": request.student_filename}
            )
            if student_docs['documents']:
                context += f"\n\nStudent's document:\n{student_docs['documents'][0]}"

        # 3. สร้าง prompt ตามบริบท
        prompt = request.custom_prompt or f"""
        Based on the following context, provide a clear and detailed answer.
        If student's document is provided, include analysis of the student's understanding.

        Context:
        {context}

        Question:
        {request.question}

        Answer:
        """

        # 4. สร้างคำตอบโดยใช้ LLM
        response = llm(prompt)
        return {"response": response.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def extract_pdf_text(file: UploadFile) -> str:
    """Helper function to extract text from PDF"""
    content = await file.read()
    pdf_reader = pypdf.PdfReader(BytesIO(content))
    text_content = ""
    for page in pdf_reader.pages:
        text_content += page.extract_text()
    return text_content