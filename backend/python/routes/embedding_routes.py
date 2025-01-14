# routes/embedding_routes.py

from flask import Blueprint, request, jsonify
from services import embedding_service

embedding_bp = Blueprint('embedding', __name__)

@embedding_bp.route('/process-file', methods=['POST'])
async def process_file():
    data = request.get_json()
    
    if not data or 'file_url' not in data or 'file_id' not in data or 'file_type' not in data:
        return jsonify({"error": "Missing required parameters"}), 400
        
    try:
        result = await embedding_service.process_file_from_url(
            file_url=data['file_url'],
            file_id=data['file_id'],
            file_type=data['file_type']
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@embedding_bp.route('/query', methods=['POST'])
async def query_documents():
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({"error": "Missing required parameters"}), 400
        
    try:
        result = await embedding_service.query_documents(
            question=data['question'],
            file_types=data.get('file_types'),  # Optional parameter
            n_results=data.get('n_results', 3)  # Optional parameter with default value
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500