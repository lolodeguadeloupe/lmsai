"""Core configuration and utilities package."""

# Import config with fallback for missing dependencies
try:
    from .config import settings
except ImportError:
    # Fallback for testing without full dependencies
    settings = None

from .exceptions import (
    # Error codes and responses
    ErrorCode,
    ErrorSeverity,
    ErrorDetail,
    ErrorResponse,
    
    # Base exceptions
    PlatformException,
    ValidationException,
    ResourceNotFoundException,
    ResourceConflictException,
    DatabaseException,
    
    # AI service exceptions
    AIServiceException,
    AIServiceUnavailableException,
    AIServiceTimeoutException,
    AIQuotaExceededException,
    AIGenerationFailedException,
    AIContentFilteredException,
    
    # Course generation exceptions
    CourseGenerationException,
    CourseStructureInvalidException,
    ChapterGenerationFailedException,
    ContentQualityException,
    GenerationTimeoutException,
    
    # Vector database exceptions
    VectorDatabaseException,
    VectorEmbeddingFailedException,
    VectorSearchFailedException,
    
    # Business logic exceptions
    InvalidStateException,
    
    # Utilities
    register_exception_handlers,
    with_retry,
)

__all__ = [
    # Config (may be None if dependencies missing)
    "settings",
    
    # Error codes and responses
    "ErrorCode",
    "ErrorSeverity", 
    "ErrorDetail",
    "ErrorResponse",
    
    # Base exceptions
    "PlatformException",
    "ValidationException",
    "ResourceNotFoundException",
    "ResourceConflictException",
    "DatabaseException",
    
    # AI service exceptions
    "AIServiceException",
    "AIServiceUnavailableException",
    "AIServiceTimeoutException",
    "AIQuotaExceededException",
    "AIGenerationFailedException",
    "AIContentFilteredException",
    
    # Course generation exceptions
    "CourseGenerationException",
    "CourseStructureInvalidException",
    "ChapterGenerationFailedException",
    "ContentQualityException",
    "GenerationTimeoutException",
    
    # Vector database exceptions
    "VectorDatabaseException",
    "VectorEmbeddingFailedException",
    "VectorSearchFailedException",
    
    # Business logic exceptions
    "InvalidStateException",
    
    # Utilities
    "register_exception_handlers",
    "with_retry",
]