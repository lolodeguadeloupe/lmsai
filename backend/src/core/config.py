"""
Application configuration management.

Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost/coursedb"
    
    # Redis settings  
    REDIS_URL: str = "redis://localhost:6379"
    
    # AI Provider settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Vector database settings
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    
    # Application settings
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    API_V1_STR: str = "/api/v1"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Content generation settings
    MAX_CHAPTER_GENERATION_TIME: int = 120  # seconds
    DEFAULT_AI_PROVIDER: str = "openai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()