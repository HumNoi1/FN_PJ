# main.py
from flask import Flask
from flask_cors import CORS
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from services.embedding_service import EmbeddingService
from services.rag_service import RAGService
from routes.evaluation_routes import create_evaluation_routes
from routes.embedding_routes import embedding_bp

app = Flask(__name__)
CORS(app)

def setup_services():
    # สร้าง embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    # สร้าง ChromaDB collection
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )
    
    # สร้าง services
    embedding_service = EmbeddingService(embeddings, collection)
    
    from llama_cpp import Llama
    llm = Llama(
        model_path="models/llama3.2-typhoon2-3b-instruct-q4_k_m.gguf",
        n_ctx=2048,
        n_threads=4
    )
    
    rag_service = RAGService(embedding_service, llm)
    
    return embedding_service, rag_service

# สร้าง services
embedding_service, rag_service = setup_services()

# สร้างและลงทะเบียน routes
evaluation_bp = create_evaluation_routes(rag_service)
app.register_blueprint(evaluation_bp, url_prefix='/api/evaluation')
app.register_blueprint(embedding_bp, url_prefix='/api/embedding')

if __name__ == '__main__':
    print("Flask server starting on http://localhost:5001")
    app.run(debug=True, port=5001)