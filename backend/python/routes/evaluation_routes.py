# routes/evaluation_routes.py
from flask import Blueprint, request, jsonify
from services import rag_service

evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route('/evaluate-answer', methods=['POST'])
async def evaluate_answer():
    """
    ประเมินคำตอบเดี่ยว
    """
    data = request.get_json()
    
    required_fields = ['question', 'student_file_id', 'teacher_file_ids']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        # ประเมินคำตอบ
        result = await rag_service.evaluate_student_answer(
            question=data['question'],
            student_file_id=data['student_file_id'],
            teacher_file_ids=data['teacher_file_ids'],
            evaluation_criteria=data.get('evaluation_criteria')  # Optional
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@evaluation_bp.route('/batch-evaluate', methods=['POST'])
async def batch_evaluate():
    """
    ประเมินคำตอบหลายข้อพร้อมกัน
    """
    data = request.get_json()
    
    required_fields = ['questions', 'student_file_id', 'teacher_file_ids']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        result = await rag_service.batch_evaluate_answers(
            student_file_id=data['student_file_id'],
            teacher_file_ids=data['teacher_file_ids'],
            questions=data['questions']
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['error']}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500