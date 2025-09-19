"""
Application configuration management.

Handles environment variables and application settings.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment and Debug settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    API_V1_STR: str = "/api/v1"
    
    # Security Settings
    BACKEND_CORS_ORIGINS: str = ""  # JSON array or comma-separated string
    MAX_REQUEST_SIZE: int = 10485760  # 10MB
    TRUSTED_HOSTS: str = ""  # Comma-separated list
    
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
    
    # Legacy rate limiting (deprecated - use advanced rate limiter)
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Advanced Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REDIS_ENABLED: bool = True
    
    # Standard API Rate Limits
    RATE_LIMIT_STANDARD_PER_SECOND: int = 10
    RATE_LIMIT_STANDARD_PER_MINUTE: int = 100
    RATE_LIMIT_STANDARD_PER_HOUR: int = 2000
    RATE_LIMIT_STANDARD_PER_DAY: int = 20000
    
    # Generation Endpoint Rate Limits (AI-powered operations)
    RATE_LIMIT_GENERATION_PER_SECOND: int = 2
    RATE_LIMIT_GENERATION_PER_MINUTE: int = 10
    RATE_LIMIT_GENERATION_PER_HOUR: int = 50
    RATE_LIMIT_GENERATION_PER_DAY: int = 200
    
    # Retrieval Endpoint Rate Limits (data fetching)
    RATE_LIMIT_RETRIEVAL_PER_SECOND: int = 20
    RATE_LIMIT_RETRIEVAL_PER_MINUTE: int = 200
    RATE_LIMIT_RETRIEVAL_PER_HOUR: int = 5000
    RATE_LIMIT_RETRIEVAL_PER_DAY: int = 50000
    
    # Admin Endpoint Rate Limits
    RATE_LIMIT_ADMIN_PER_SECOND: int = 5
    RATE_LIMIT_ADMIN_PER_MINUTE: int = 50
    RATE_LIMIT_ADMIN_PER_HOUR: int = 500
    RATE_LIMIT_ADMIN_PER_DAY: int = 2000
    
    # Upload Endpoint Rate Limits
    RATE_LIMIT_UPLOAD_PER_SECOND: int = 1
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 5
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 20
    RATE_LIMIT_UPLOAD_PER_DAY: int = 100
    
    # User Type Multipliers
    RATE_LIMIT_AUTHENTICATED_MULTIPLIER: float = 2.0  # 2x limits for logged-in users
    RATE_LIMIT_PREMIUM_MULTIPLIER: float = 5.0        # 5x limits for premium users
    RATE_LIMIT_ADMIN_MULTIPLIER: float = 10.0         # 10x limits for admin users
    
    # Rate Limit Storage Settings
    RATE_LIMIT_REDIS_CONNECTION_TIMEOUT: int = 5      # seconds
    RATE_LIMIT_REDIS_SOCKET_TIMEOUT: int = 5          # seconds
    RATE_LIMIT_MEMORY_CLEANUP_INTERVAL: int = 300     # seconds (5 minutes)
    
    # Content generation settings
    MAX_CHAPTER_GENERATION_TIME: int = 120  # seconds
    DEFAULT_AI_PROVIDER: str = "openai"
    
    # Course Generation Concurrency Limits
    MAX_CONCURRENT_COURSE_GENERATIONS: int = 100
    MAX_CONCURRENT_CHAPTER_GENERATIONS: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()