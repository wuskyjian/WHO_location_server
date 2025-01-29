from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from config import TestConfig, DevelopmentConfig, ProductionConfig
import os

# Initialize extensions
db = SQLAlchemy()  # Database ORM
migrate = Migrate()  # Database migrations
bcrypt = Bcrypt()  # Password hashing
jwt = JWTManager()  # JWT authentication
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")  # Real-time communication

def init_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

def register_blueprints(app):
    """Register Flask blueprints."""
    from app.routes import bp as api_bp
    from app.auth import auth_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

def init_database(app):
    """Initialize database and ensure required data exists."""
    with app.app_context():
        db.create_all()
        from app.models import GlobalCounter
        try:
            GlobalCounter.initialize()
        except Exception as e:
            app.logger.error(f"Failed to initialize GlobalCounter: {e}")

def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Select configuration based on environment
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'development')
        config_class = {
            'development': DevelopmentConfig,
            'production': ProductionConfig,
            'testing': TestConfig
        }.get(env, DevelopmentConfig)
    
    # Use provided configuration if it's a dictionary
    if isinstance(config_class, dict):
        app.config.update(config_class)
    else:
        app.config.from_object(config_class)
    
    # Initialize application components
    init_extensions(app)
    register_blueprints(app)
    init_database(app)
    
    return app