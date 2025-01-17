from flask import Flask
from flask_cors import CORS

def create_app():
    """
    Factory function สำหรับสร้าง Flask application
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    CORS(app)
    
    # Import และลงทะเบียน blueprints
    from .routes.document_routes import document_bp
    from .routes.milvus_routes import milvus_bp
    from .routes.health_routes import health_bp
    
    app.register_blueprint(document_bp, url_prefix='/api/documents')
    app.register_blueprint(milvus_bp, url_prefix='/api/milvus')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    
    return app