import logging
import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from io import BytesIO

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

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

class SystemConfig:
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
            Path('models/llama3.2-typhoon2-3b-instruct-q4_k_m.gguf'),
        ]
        
        project_model_path = Path(__file__).parent.parent / 'models' / 'llama3.2-typhoon2-3b-instruct-q4_k_m.gguf'
        possible_paths.append(project_model_path)
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found model at: {path}")
                return path.resolve()
                
        raise ValueError(
            "Model file not found. Please set LLAMA_MODEL_PATH or place model in standard locations"
        )
    
    def _get_db_path(self) -> Path:
        base_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        return Path(base_path).resolve()

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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize system configuration
system_config = SystemConfig()

# Initialize components
try:
    chroma_client = chromadb.PersistentClient(path=str(system_config.db_path))
    collection = chroma_client.get_or_create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )
    
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={'device': system_config.device}
    )
    
    llm = LlamaCpp(**system_config.get_llm_config())
    
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}")
    raise

@app.route('/system-info', methods=['GET'])
def get_system_info():
    return jsonify({
        "platform": system_config.system,
        "device": system_config.device,
        "model_path": str(system_config.model_path),
        "db_path": str(system_config.db_path),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "mps_available": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    })

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if not file.filename.endswith('.pdf'):
        return jsonify({"error": "File must be PDF"}), 400

    try:
        # Process PDF file
        pdf_reader = pypdf.PdfReader(BytesIO(file.read()))
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter()
        chunks = text_splitter.split_text(text_content)

        # Generate embeddings and store in ChromaDB
        embeddings_list = embeddings.embed_documents(chunks)
        
        collection.add(
            embeddings=embeddings_list,
            documents=chunks,
            ids=[f"{secure_filename(file.filename)}_{i}" for i in range(len(chunks))]
        )

        return jsonify({"message": "PDF processed successfully"})
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    
    if not data or 'question' not in data or 'filename' not in data:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Get relevant chunks from ChromaDB
        results = collection.query(
            query_texts=[data['question']],
            n_results=3
        )

        # Format prompt
        context = "\n".join(results['documents'][0])
        custom_prompt = data.get('custom_prompt', '')
        
        prompt = f"""Based on the following context:
{context}

{custom_prompt if custom_prompt else 'Answer the following question:'}
{data['question']}"""

        # Get response from LLM
        response = llm(prompt)
        
        return jsonify({"response": response})
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)