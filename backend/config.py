# config.py
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # Database
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'hdt_database')
    DB_USER = os.getenv('DB_USER', 'postgres')
    RAW_DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_PASSWORD = quote_plus(RAW_DB_PASSWORD)

    
    # Build database URL
    DATABASE_URL = "postgresql+psycopg2://postgres:1234@127.0.0.1:5432/hdt_database"



    
    # Google Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Application Settings
    MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '1'))
    CODE_GENERATION_MAX_LINES = int(os.getenv('CODE_GENERATION_MAX_LINES', '1000'))
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '90'))
    REFRESH_RATE_SECONDS = int(os.getenv('REFRESH_RATE_SECONDS', '1'))
    
    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:5500').split(',')
    
    # JWT Settings
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.GEMINI_API_KEY:
            print("⚠️  WARNING: GEMINI_API_KEY not set! AI features will not work.")
        
        if Config.DEBUG:
            print("⚠️  WARNING: Running in DEBUG mode. Do not use in production!")
        
        return True