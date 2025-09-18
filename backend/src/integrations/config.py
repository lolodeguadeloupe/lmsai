"""
Configuration management for vector database integrations.

Provides centralized configuration for different vector database backends
with environment variable support and validation.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from .vector_client import VectorConfig, VectorBackend


class VectorDatabaseSettings(BaseSettings):
    """Settings for vector database configuration."""
    
    # Backend selection
    vector_backend: VectorBackend = Field(
        default=VectorBackend.CHROMA,
        description="Vector database backend to use"
    )
    
    # Pinecone settings
    pinecone_api_key: Optional[str] = Field(
        default=None,
        description="Pinecone API key"
    )
    pinecone_environment: Optional[str] = Field(
        default=None,
        description="Pinecone environment (e.g., 'us-west1-gcp')"
    )
    pinecone_index_name: str = Field(
        default="course-embeddings",
        description="Pinecone index name"
    )
    
    # ChromaDB settings
    chroma_host: str = Field(
        default="localhost",
        description="ChromaDB host"
    )
    chroma_port: int = Field(
        default=8000,
        description="ChromaDB port"
    )
    chroma_collection_name: str = Field(
        default="course_embeddings",
        description="ChromaDB collection name"
    )
    
    # General settings
    embedding_dimension: int = Field(
        default=1536,
        description="Embedding vector dimension"
    )
    connection_pool_size: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Connection pool size"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Operation timeout in seconds"
    )
    
    class Config:
        env_prefix = "VECTOR_"
        case_sensitive = False
        
    @field_validator("vector_backend", mode="before")
    @classmethod
    def validate_backend(cls, v):
        """Validate and convert backend string to enum."""
        if isinstance(v, str):
            return VectorBackend(v.lower())
        return v
    
    @field_validator("pinecone_api_key")
    @classmethod
    def validate_pinecone_config(cls, v, info):
        """Validate Pinecone configuration when backend is Pinecone."""
        if hasattr(info, 'data') and info.data:
            backend = info.data.get("vector_backend")
            if backend == VectorBackend.PINECONE and not v:
                raise ValueError("Pinecone API key is required when using Pinecone backend")
        return v
    
    def to_vector_config(self) -> VectorConfig:
        """Convert to VectorConfig for use with vector client."""
        return VectorConfig(
            backend=self.vector_backend,
            pinecone_api_key=self.pinecone_api_key,
            pinecone_environment=self.pinecone_environment,
            pinecone_index_name=self.pinecone_index_name,
            chroma_host=self.chroma_host,
            chroma_port=self.chroma_port,
            chroma_collection_name=self.chroma_collection_name,
            embedding_dimension=self.embedding_dimension,
            connection_pool_size=self.connection_pool_size,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds
        )


def get_vector_settings() -> VectorDatabaseSettings:
    """Get vector database settings from environment."""
    return VectorDatabaseSettings()


def create_vector_config_from_env() -> VectorConfig:
    """Create VectorConfig from environment variables."""
    settings = get_vector_settings()
    return settings.to_vector_config()


# Environment-specific configurations
class DevelopmentVectorSettings(VectorDatabaseSettings):
    """Development environment vector settings."""
    
    vector_backend: VectorBackend = VectorBackend.CHROMA
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "dev_course_embeddings"
    connection_pool_size: int = 5
    timeout_seconds: int = 60


class ProductionVectorSettings(VectorDatabaseSettings):
    """Production environment vector settings."""
    
    vector_backend: VectorBackend = VectorBackend.PINECONE
    connection_pool_size: int = 20
    max_retries: int = 5
    timeout_seconds: int = 30
    
    @field_validator("pinecone_api_key")
    @classmethod
    def require_pinecone_key(cls, v):
        """Require Pinecone API key in production."""
        if not v:
            raise ValueError("Pinecone API key is required in production")
        return v
    
    @field_validator("pinecone_environment")
    @classmethod
    def require_pinecone_env(cls, v):
        """Require Pinecone environment in production."""
        if not v:
            raise ValueError("Pinecone environment is required in production")
        return v


class TestVectorSettings(VectorDatabaseSettings):
    """Test environment vector settings."""
    
    vector_backend: VectorBackend = VectorBackend.CHROMA
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "test_course_embeddings"
    connection_pool_size: int = 2
    timeout_seconds: int = 10


def get_environment_settings() -> VectorDatabaseSettings:
    """Get vector settings based on current environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionVectorSettings()
    elif env == "test":
        return TestVectorSettings()
    else:
        return DevelopmentVectorSettings()


# Validation functions
def validate_vector_config(config: VectorConfig) -> bool:
    """Validate vector database configuration."""
    try:
        if config.backend == VectorBackend.PINECONE:
            if not config.pinecone_api_key:
                raise ValueError("Pinecone API key is required")
            if not config.pinecone_environment:
                raise ValueError("Pinecone environment is required")
        
        if config.embedding_dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
        
        if config.connection_pool_size <= 0:
            raise ValueError("Connection pool size must be positive")
        
        if config.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        
        return True
        
    except ValueError as e:
        print(f"Vector config validation error: {e}")
        return False


# Configuration presets for common use cases
CHROMA_LOCAL_CONFIG = VectorConfig(
    backend=VectorBackend.CHROMA,
    chroma_host="localhost",
    chroma_port=8000,
    chroma_collection_name="course_embeddings"
)

CHROMA_DOCKER_CONFIG = VectorConfig(
    backend=VectorBackend.CHROMA,
    chroma_host="chroma",
    chroma_port=8000,
    chroma_collection_name="course_embeddings"
)

def get_pinecone_config(api_key: str, environment: str, index_name: str = "course-embeddings") -> VectorConfig:
    """Get Pinecone configuration with provided credentials."""
    return VectorConfig(
        backend=VectorBackend.PINECONE,
        pinecone_api_key=api_key,
        pinecone_environment=environment,
        pinecone_index_name=index_name
    )