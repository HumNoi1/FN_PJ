from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import LlamaCpp
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from pymilvus import (
    connections,
    utility,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType
)
import pypdf
import os
from typing import Dict, List
from io import BytesIO
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local'))

# Initialize FastAPI
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Milvus
connections.connect(
    alias="default",
    host=os.getenv("MILVUS_HOST", "localhost"),
    port=os.getenv("MILVUS_PORT", "19530")
)

# Define collection schema
dim = 384  # Dimension for all-MiniLM-L6-v2 embeddings
collection_name = "documents"

def create_collection():
    """Create Milvus collection if it doesn't exist"""
    if utility.has_collection(collection_name):
        return Collection(collection_name)

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
        FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=200),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]
    schema = CollectionSchema(fields=fields, description="Document collection")
    collection = Collection(name=collection_name, schema=schema)
    
    # Create index for vector field
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    return collection

# Initialize collection
collection = create_collection()

# Initialize LLM
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

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="setu4993/LaBSE",
    model_kwargs={'device': 'cuda'},
    cache_folder="models"
)

class QueryRequest(BaseModel):
    question: str
    custom_prompt: str | None = None
    filename: str

@app.get("/status/{filename}")
async def check_file_status(filename: str):
    try:
        collection.load()
        results = collection.query(
            expr=f'file_name == "{filename}"',
            limit=1
        )
        return {
            "is_processed": len(results) > 0,
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking file status: {str(e)}"
        )

@app.post("/process-pdf")
async def process_pdf(file: UploadFile, is_teacher: bool = True):
    """
    Unified endpoint for processing PDF files.
    """
    try:
        content = await file.read()
        pdf_file = BytesIO(content)
        
        # อ่านและแปลง PDF เป็นข้อความ
        pdf_reader = pypdf.PdfReader(pdf_file)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()

        # ประมวลผลเฉพาะไฟล์ของครูเท่านั้น
        if is_teacher:
            # แบ่งข้อความเป็น chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(text_content)
            
            # โหลด collection และเตรียมการ insert
            collection.load()
            total_chunks = len(chunks)
            
            # ประมวลผลทีละ chunk เพื่อป้องกันปัญหาจำนวนแถวไม่ตรงกัน
            for i, chunk in enumerate(chunks):
                # สร้าง embedding สำหรับ chunk นี้
                chunk_embedding = embeddings.embed_query(chunk)
                
                # Insert ข้อมูลทีละ chunk โดยให้ทุก field มีข้อมูล 1 แถว
                collection.insert([
                    [f"{file.filename}_chunk_{i}"],  # id
                    [file.filename],                 # file_name
                    [i],                            # chunk_index
                    [chunk],                        # content
                    [chunk_embedding]               # embedding - ส่งเป็น list 1 มิติ
                ])

                # Flush ทุก 100 chunks เพื่อประสิทธิภาพ
                if (i + 1) % 100 == 0:
                    collection.flush()
            
            # Flush ครั้งสุดท้ายเพื่อให้แน่ใจว่าข้อมูลถูกบันทึกทั้งหมด
            collection.flush()
            message = f"Successfully processed {total_chunks} chunks"
        else:
            message = "File validated successfully"

        return {
            "status": "success",
            "message": message,
            "filename": file.filename,
            "is_teacher": is_teacher
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
        
        # Query Milvus for relevant documents
        collection.load()
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=[question_embedding],
            anns_field="embedding",
            param=search_params,
            limit=3,
            expr=f'file_name == "{request.filename}"',
            output_fields=["content"]
        )
        
        if not results or len(results[0]) == 0:
            raise HTTPException(status_code=404, detail="No relevant documents found")
            
        context = "\n\n".join([hit.entity.get('content') for hit in results[0]])

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)