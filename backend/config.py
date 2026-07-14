"""
==============================================================================
Configuration Module
==============================================================================
This module handles all configuration settings for the application.
It loads environment variables and sets up database connections.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    ===========================================================================
    Main Configuration Class
    ===========================================================================
    Central configuration for the entire application including:
    - Flask settings
    - Database connection
    - AI/LLM settings
    - Security settings
    """
    
    # -------------------------------------------------------------------------
    # Flask Configuration
    # -------------------------------------------------------------------------
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # -------------------------------------------------------------------------
    # Database Configuration (PostgreSQL)
    # -------------------------------------------------------------------------
    # Format: postgresql://username:password@host:port/database_name
    DB_USERNAME = os.getenv('DB_USERNAME', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'hcp_crm_db')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable to save memory
    
    # -------------------------------------------------------------------------
    # Groq LLM Configuration
    # -------------------------------------------------------------------------
    # Get your API key from: https://console.groq.com/
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'your-groq-api-key')
    
    # Model configurations as specified in the requirements
    GROQ_MODEL_PRIMARY = "meta-llama/llama-4-scout-17b-16e-instruct"  # Primary model for tool calls
    GROQ_MODEL_CONTEXT = "meta-llama/llama-4-scout-17b-16e-instruct"  # For longer context
    
    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    MAX_INTERACTIONS_PER_PAGE = 10
    CHAT_HISTORY_LIMIT = 50  # Maximum messages to keep in chat history


class DevelopmentConfig(Config):
    """Development environment specific settings"""
    DEBUG = True


class ProductionConfig(Config):
    """Production environment specific settings"""
    DEBUG = False


class TestingConfig(Config):
    """Testing environment specific settings"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory DB for tests


# Dictionary to easily access configurations by name
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}