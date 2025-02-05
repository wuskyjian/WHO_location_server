import os
from datetime import timedelta
import pytz

class Config:
    """Base configuration class."""
    
    # Basic configuration
    SECRET_KEY = 'dev-secret-key'
    DEBUG = False
    TESTING = False
    
    # Timezone configuration
    SERVER_TIMEZONE = pytz.timezone('Europe/Rome')  # Change this to your server's timezone
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = '12b47f3c1af1d8a36dc4bfa5f1a8d1f1c7c89f3c11b9d2a3f9c1e7f5d6f3e8d2'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=10)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Socket.IO configuration
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit

    # Reports directory configuration
    REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

class TestConfig(Config):
    """Test environment configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory database for testing
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    SECRET_KEY = 'test-secret-key'

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    # Add development-specific configurations here

class ProductionConfig(Config):
    """Production environment configuration."""
    # Use environment variables for sensitive information in production
    def __init__(self):
        super().__init__()
        # Only override sensitive configurations from environment variables in production
        if os.environ.get('DATABASE_URL'):
            self.SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
        if os.environ.get('JWT_SECRET_KEY'):
            self.JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
        if os.environ.get('SECRET_KEY'):
            self.SECRET_KEY = os.environ.get('SECRET_KEY')