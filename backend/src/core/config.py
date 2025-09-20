"""
Application configuration management.

Handles environment variables and application settings.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = {"extra": "allow", "env_file": ".env", "case_sensitive": True}
    
    # Environment and Debug settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/coursegenai"
    
    # Redis settings  
    REDIS_URL: str = "redis://localhost:6379"
    
    # AI Provider settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None


# Global settings instance
settings = Settings()