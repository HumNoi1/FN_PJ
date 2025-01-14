# routes/evaluation_routes.py
from flask import Blueprint, request, jsonify

def create_evaluation_routes(rag_service):
    evaluation_bp = Blueprint('evaluation', __name__)

    @evaluation_bp.route('/evaluate-answer', methods=['POST'])
    async def evaluate_answer():
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
                
            required_fields = ['question', 'student_file_id', 'teacher_file_ids']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400

            result = await rag_service.evaluate_student_answer(
                question=data['question'],
                student_file_id=data['student_file_id'],
                teacher_file_ids=data['teacher_file_ids'],
                evaluation_criteria=data.get('evaluation_criteria')
            )

            return jsonify(result)
                
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500

    return evaluation_bp