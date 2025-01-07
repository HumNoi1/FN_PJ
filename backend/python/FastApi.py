from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import LlamaCpp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import chromadb
from chromadb.config import Settings
import pypdf
import os
from typing import Dict
from io import BytesIO
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local'))

# Initialize FastAPI
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")

# Create or get collection
collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# LLM
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
llm = LlamaCpp(
    model_path="models/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    temperature=0.1,
    max_tokens=512,
    n_ctx=2048,
    callback_manager=callback_manager,
    n_gpu_layers=1,
    verbose=True,
)

# Embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cuda'}
)

class QueryRequest(BaseModel):
    question: str
    custom_prompt: str | None = None
    filename: str

@app.get("/status/{filename}")
async def check_file_status(filename: str):
    try:
        results = collection.get(
            where={"file_name": filename},
            limit=1
        )
        return {
            "is_processed": len(results['ids']) > 0,
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking file status: {str(e)}"
        )

@app.post("/process-pdf")
async def process_pdf(file: UploadFile):
    try:
        content = await file.read()
        pdf_file = BytesIO(content)
        
        pdf_reader = pypdf.PdfReader(pdf_file)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(text_content)

        # Process chunks and store in ChromaDB
        for i, chunk in enumerate(chunks):
            chunk_embedding = embeddings.embed_query(chunk)
            
            collection.add(
                documents=[chunk],
                embeddings=[chunk_embedding],
                metadatas=[{
                    "file_name": file.filename,
                    "chunk_index": i
                }],
                ids=[f"{file.filename}_chunk_{i}"]
            )

        return {
            "status": "success",
            "message": f"Successfully processed {len(chunks)} chunks",
            "filename": file.filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/query")
async def query(request: QueryRequest):
    try:
        question_embedding = embeddings.embed_query(request.question)
        
        # Query ChromaDB for relevant documents
        results = collection.query(
            query_embeddings=[question_embedding],
            where={"file_name": request.filename},
            n_results=3
        )
        
        if not results['documents'][0]:
            raise HTTPException(status_code=404, detail="No relevant documents found")
            
        context = "\n\n".join(results['documents'][0])

        # Create prompt
        prompt = request.custom_prompt if request.custom_prompt else f"""
        Use the following context to answer the question:

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
    
class CompareRequest(BaseModel):
    teacher_file: str
    student_file: str
    question: str | None = None
    custom_prompt: str | None = None

@app.post("/compare-pdfs")
async def compare_pdfs(request: CompareRequest):
    try:
        # Query ChromaDB for both files
        teacher_results = collection.get(
            where={"file_name": request.teacher_file},
            limit=10
        )
        
        # Read and process student file
        student_content = await process_student_file(request.student_file)
        
        # Create comparison prompt
        context = "\n\n".join(teacher_results['documents'])
        
        default_prompt = f"""
        Compare the following teaching material with the student submission:

        Teaching Material:
        {context}

        Student Submission:
        {student_content}

        Analyze:
        1. Key concepts covered correctly
        2. Missing or incorrect information
        3. Areas needing improvement
        4. Overall assessment

        If a specific question is provided, focus on that aspect:
        {request.question if request.question else 'Provide general comparison'}
        """

        prompt = request.custom_prompt if request.custom_prompt else default_prompt
        
        response = llm(prompt)
        return {"comparison": response.strip()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_student_file(filename: str):
    try:
        # Get student file from storage
        student_pdf = await get_file_from_storage(filename)
        pdf_reader = pypdf.PdfReader(BytesIO(student_pdf))
        
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()
            
        return text_content
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing student file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)