# app/api/routes.py
def register_routes(app, milvus_service, redis_client):
    """
    ลงทะเบียน blueprints และ routes ทั้งหมดของแอปพลิเคชัน
    
    Args:
        app: Flask application instance
        milvus_service: Instance ของ MilvusService
        redis_client: Instance ของ Redis client
    """
    # Import blueprints
    from routes.document_routes import document_bp, init_routes as init_document_routes
    from routes.milvus_routes import milvus_bp, init_routes as init_milvus_routes
    from routes.health_routes import health_bp, init_health_routes

    # Initialize routes with services
    init_document_routes(milvus_service)
    init_milvus_routes(milvus_service)
    init_health_routes(milvus_service, redis_client)

    # Register blueprints
    app.register_blueprint(document_bp, url_prefix='/api/documents')
    app.register_blueprint(milvus_bp, url_prefix='/api/milvus')
    app.register_blueprint(health_bp, url_prefix='/api/health')