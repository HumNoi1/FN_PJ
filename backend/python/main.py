# main.py
from flask import Flask
from flask_cors import CORS
from services.milvus_service import MilvusEmbeddingService
from services.rag_service import RAGService
from routes.evaluation_routes import create_evaluation_routes
from routes.embedding_routes import embedding_bp

app = Flask(__name__)
CORS(app)

def setup_services():
    # สร้าง Milvus embedding service
    embedding_service = MilvusEmbeddingService(
        model_name="sentence-transformers/all-MiniLM-L6-v2"  # หรือจะใช้โมเดลอื่นก็ได้
    )
    
    # สร้าง LLM service
    from llama_cpp import Llama
    llm = Llama(
        model_path="models/llama3.2-typhoon2-3b-instruct-q4_k_m.gguf",
        n_ctx=2048,
        n_threads=4
    )
    
    # สร้าง RAG service
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