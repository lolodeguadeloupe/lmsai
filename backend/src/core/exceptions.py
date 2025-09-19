"""
Comprehensive exception handling system for the AI course generation platform.

This module provides:
- Custom exception classes for domain-specific errors
- Global exception handlers for FastAPI
- Error response standardization
- Logging integration with sensitive data protection
- Support for error recovery and retries
"""

import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import HTTPException, Request, Response, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError
)

# Configure logger
logger = logging.getLogger(__name__)


# Error Code Enumerations
class ErrorCode(str, Enum):
    """Standardized error codes for the platform."""
    
    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    
    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_INTEGRITY_ERROR = "DATABASE_INTEGRITY_ERROR"
    DATABASE_OPERATION_ERROR = "DATABASE_OPERATION_ERROR"
    
    # AI Service errors
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_SERVICE_TIMEOUT = "AI_SERVICE_TIMEOUT"
    AI_SERVICE_QUOTA_EXCEEDED = "AI_SERVICE_QUOTA_EXCEEDED"
    AI_GENERATION_FAILED = "AI_GENERATION_FAILED"
    AI_CONTENT_FILTERED = "AI_CONTENT_FILTERED"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    
    # Course generation errors
    COURSE_GENERATION_FAILED = "COURSE_GENERATION_FAILED"
    COURSE_STRUCTURE_INVALID = "COURSE_STRUCTURE_INVALID"
    CHAPTER_GENERATION_FAILED = "CHAPTER_GENERATION_FAILED"
    CONTENT_QUALITY_FAILED = "CONTENT_QUALITY_FAILED"
    GENERATION_TIMEOUT = "GENERATION_TIMEOUT"
    
    # Vector database errors
    VECTOR_DB_CONNECTION_ERROR = "VECTOR_DB_CONNECTION_ERROR"
    VECTOR_EMBEDDING_FAILED = "VECTOR_EMBEDDING_FAILED"
    VECTOR_SEARCH_FAILED = "VECTOR_SEARCH_FAILED"
    
    # Business logic errors
    INVALID_COURSE_STATE = "INVALID_COURSE_STATE"
    INVALID_CHAPTER_STATE = "INVALID_CHAPTER_STATE"
    QUIZ_GENERATION_FAILED = "QUIZ_GENERATION_FAILED"
    EXPORT_FAILED = "EXPORT_FAILED"
    IMPORT_FAILED = "IMPORT_FAILED"


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting."""
    
    LOW = "low"          # Minor issues, graceful degradation possible
    MEDIUM = "medium"    # Significant issues, user impact but recoverable
    HIGH = "high"        # Major issues, service degradation
    CRITICAL = "critical"  # System failures, immediate attention required


# Response Models
class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    
    error: bool = True
    code: ErrorCode
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry
    support_id: Optional[str] = None   # Reference for support team


# Base Exception Classes
class PlatformException(Exception):
    """Base exception for all platform-specific errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[List[ErrorDetail]] = None,
        retry_after: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.severity = severity
        self.details = details or []
        self.retry_after = retry_after
        self.cause = cause
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "code": self.code.value,
            "message": self.message,
            "severity": self.severity.value,
            "details": [detail.dict() if hasattr(detail, 'dict') else detail for detail in self.details],
            "retry_after": self.retry_after,
            "timestamp": self.timestamp.isoformat()
        }


class ValidationException(PlatformException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None
    ):
        if field and not details:
            details = [ErrorDetail(field=field, message=message)]
        
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            details=details
        )


class ResourceNotFoundException(PlatformException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Union[str, UUID],
        message: Optional[str] = None
    ):
        if not message:
            message = f"{resource_type} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            severity=ErrorSeverity.LOW,
            details=[ErrorDetail(
                field="id",
                message=f"{resource_type} not found",
                code="NOT_FOUND"
            )]
        )


class ResourceConflictException(PlatformException):
    """Exception for resource conflict errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            details=details
        )


class DatabaseException(PlatformException):
    """Exception for database-related errors."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        # Determine specific code based on the cause
        code = ErrorCode.DATABASE_OPERATION_ERROR
        if isinstance(cause, OperationalError):
            code = ErrorCode.DATABASE_CONNECTION_ERROR
        elif isinstance(cause, IntegrityError):
            code = ErrorCode.DATABASE_INTEGRITY_ERROR
        
        super().__init__(
            message=message,
            code=code,
            severity=ErrorSeverity.HIGH,
            cause=cause
        )
        self.operation = operation


# AI Service Exceptions
class AIServiceException(PlatformException):
    """Base exception for AI service errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.AI_SERVICE_UNAVAILABLE,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        provider: Optional[str] = None,
        retry_after: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            severity=severity,
            retry_after=retry_after,
            cause=cause
        )
        self.provider = provider


class AIServiceUnavailableException(AIServiceException):
    """Exception for AI service unavailability."""
    
    def __init__(
        self,
        provider: str,
        retry_after: int = 60,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"AI service '{provider}' is currently unavailable",
            code=ErrorCode.AI_SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.HIGH,
            provider=provider,
            retry_after=retry_after,
            cause=cause
        )


class AIServiceTimeoutException(AIServiceException):
    """Exception for AI service timeouts."""
    
    def __init__(
        self,
        provider: str,
        timeout_seconds: int,
        operation: str = "generation",
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"AI service '{provider}' timed out after {timeout_seconds}s during {operation}",
            code=ErrorCode.AI_SERVICE_TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            provider=provider,
            retry_after=30,
            cause=cause
        )


class AIQuotaExceededException(AIServiceException):
    """Exception for AI service quota exceeded."""
    
    def __init__(
        self,
        provider: str,
        retry_after: int = 3600,  # 1 hour default
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"AI service '{provider}' quota exceeded",
            code=ErrorCode.AI_SERVICE_QUOTA_EXCEEDED,
            severity=ErrorSeverity.MEDIUM,
            provider=provider,
            retry_after=retry_after,
            cause=cause
        )


class AIGenerationFailedException(AIServiceException):
    """Exception for AI generation failures."""
    
    def __init__(
        self,
        operation: str,
        provider: str,
        reason: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        message = f"AI {operation} failed using {provider}"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            code=ErrorCode.AI_GENERATION_FAILED,
            severity=ErrorSeverity.MEDIUM,
            provider=provider,
            cause=cause
        )


class AIContentFilteredException(AIServiceException):
    """Exception for AI content filtered by safety systems."""
    
    def __init__(
        self,
        provider: str,
        filter_reason: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Content filtered by {provider}: {filter_reason}",
            code=ErrorCode.AI_CONTENT_FILTERED,
            severity=ErrorSeverity.LOW,
            provider=provider,
            cause=cause
        )


# Course Generation Exceptions
class CourseGenerationException(PlatformException):
    """Base exception for course generation errors."""
    
    def __init__(
        self,
        message: str,
        course_id: Optional[UUID] = None,
        phase: Optional[str] = None,
        code: ErrorCode = ErrorCode.COURSE_GENERATION_FAILED,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            severity=severity,
            cause=cause
        )
        self.course_id = course_id
        self.phase = phase


class CourseStructureInvalidException(CourseGenerationException):
    """Exception for invalid course structure."""
    
    def __init__(
        self,
        message: str,
        course_id: Optional[UUID] = None,
        validation_errors: Optional[List[str]] = None
    ):
        details = []
        if validation_errors:
            details = [
                ErrorDetail(field="structure", message=error, code="INVALID_STRUCTURE")
                for error in validation_errors
            ]
        
        super().__init__(
            message=message,
            course_id=course_id,
            phase="structure_generation",
            code=ErrorCode.COURSE_STRUCTURE_INVALID,
            severity=ErrorSeverity.MEDIUM
        )
        self.details = details


class ChapterGenerationFailedException(CourseGenerationException):
    """Exception for chapter generation failures."""
    
    def __init__(
        self,
        message: str,
        course_id: UUID,
        chapter_number: int,
        chapter_title: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        if chapter_title:
            message = f"Chapter {chapter_number} '{chapter_title}' generation failed: {message}"
        else:
            message = f"Chapter {chapter_number} generation failed: {message}"
        
        super().__init__(
            message=message,
            course_id=course_id,
            phase="chapter_generation",
            code=ErrorCode.CHAPTER_GENERATION_FAILED,
            severity=ErrorSeverity.MEDIUM,
            cause=cause
        )
        self.chapter_number = chapter_number
        self.chapter_title = chapter_title


class ContentQualityException(CourseGenerationException):
    """Exception for content quality validation failures."""
    
    def __init__(
        self,
        message: str,
        course_id: UUID,
        quality_scores: Optional[Dict[str, float]] = None,
        failed_metrics: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            course_id=course_id,
            phase="quality_validation",
            code=ErrorCode.CONTENT_QUALITY_FAILED,
            severity=ErrorSeverity.MEDIUM
        )
        self.quality_scores = quality_scores
        self.failed_metrics = failed_metrics or []


class GenerationTimeoutException(CourseGenerationException):
    """Exception for generation timeout."""
    
    def __init__(
        self,
        operation: str,
        timeout_seconds: int,
        course_id: Optional[UUID] = None
    ):
        super().__init__(
            message=f"{operation} timed out after {timeout_seconds} seconds",
            course_id=course_id,
            code=ErrorCode.GENERATION_TIMEOUT,
            severity=ErrorSeverity.MEDIUM
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


# Vector Database Exceptions
class VectorDatabaseException(PlatformException):
    """Base exception for vector database errors."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        backend: Optional[str] = None,
        code: ErrorCode = ErrorCode.VECTOR_DB_CONNECTION_ERROR,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            severity=ErrorSeverity.MEDIUM,
            cause=cause
        )
        self.operation = operation
        self.backend = backend


class VectorEmbeddingFailedException(VectorDatabaseException):
    """Exception for vector embedding failures."""
    
    def __init__(
        self,
        content_type: str,
        content_id: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Failed to generate embedding for {content_type} '{content_id}'",
            operation="embedding_generation",
            code=ErrorCode.VECTOR_EMBEDDING_FAILED,
            cause=cause
        )


class VectorSearchFailedException(VectorDatabaseException):
    """Exception for vector search failures."""
    
    def __init__(
        self,
        query: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Vector search failed for query: {query[:100]}...",
            operation="vector_search",
            code=ErrorCode.VECTOR_SEARCH_FAILED,
            cause=cause
        )


# Business Logic Exceptions
class InvalidStateException(PlatformException):
    """Exception for invalid business logic state."""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: UUID,
        current_state: str,
        required_states: List[str],
        operation: str
    ):
        message = (
            f"Cannot perform '{operation}' on {entity_type} '{entity_id}'. "
            f"Current state: {current_state}, required states: {', '.join(required_states)}"
        )
        
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_COURSE_STATE if "course" in entity_type.lower() 
                  else ErrorCode.INVALID_CHAPTER_STATE,
            severity=ErrorSeverity.LOW
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.current_state = current_state
        self.required_states = required_states
        self.operation = operation


# Utility Functions
def _sanitize_error_message(message: str, sensitive_patterns: Optional[List[str]] = None) -> str:
    """
    Sanitize error messages to remove sensitive information.
    
    Args:
        message: Original error message
        sensitive_patterns: Patterns to remove/mask
        
    Returns:
        Sanitized error message
    """
    if not sensitive_patterns:
        # Default patterns for common sensitive data
        sensitive_patterns = [
            r'password[=:]\s*\S+',
            r'token[=:]\s*\S+',
            r'key[=:]\s*\S+',
            r'secret[=:]\s*\S+',
            r'api[_-]key[=:]\s*\S+',
        ]
    
    import re
    sanitized = message
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def _extract_request_context(request: Request) -> Dict[str, Any]:
    """Extract relevant context from request for error logging."""
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": {
            key: value for key, value in request.headers.items()
            if key.lower() not in ['authorization', 'cookie', 'x-api-key']
        },
        "query_params": dict(request.query_params),
        "client_host": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }


def _generate_support_id() -> str:
    """Generate a unique support reference ID."""
    import uuid
    return f"SUP-{uuid.uuid4().hex[:8].upper()}"


# Exception Handlers
async def platform_exception_handler(request: Request, exc: PlatformException) -> JSONResponse:
    """
    Global handler for platform-specific exceptions.
    
    Provides standardized error response format with proper logging.
    """
    # Generate support ID for tracking
    support_id = _generate_support_id()
    
    # Extract request context
    request_context = _extract_request_context(request)
    
    # Log error with context
    logger.error(
        f"Platform exception [{support_id}]: {exc.code.value} - {exc.message}",
        extra={
            "error_code": exc.code.value,
            "error_severity": exc.severity.value,
            "support_id": support_id,
            "request_context": request_context,
            "exception_details": exc.to_dict(),
            "stack_trace": traceback.format_exc() if exc.cause else None
        }
    )
    
    # Determine HTTP status code
    status_code_map = {
        ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorCode.AUTHENTICATION_ERROR: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.AUTHORIZATION_ERROR: status.HTTP_403_FORBIDDEN,
        ErrorCode.RESOURCE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorCode.RESOURCE_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
        ErrorCode.RESOURCE_CONFLICT: status.HTTP_409_CONFLICT,
        ErrorCode.INVALID_COURSE_STATE: status.HTTP_409_CONFLICT,
        ErrorCode.INVALID_CHAPTER_STATE: status.HTTP_409_CONFLICT,
        ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.AI_SERVICE_QUOTA_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    }
    
    http_status = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Create error response
    error_response = ErrorResponse(
        code=exc.code,
        message=_sanitize_error_message(exc.message),
        details=exc.details,
        request_id=request.headers.get("x-request-id"),
        retry_after=exc.retry_after,
        support_id=support_id if exc.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
    )
    
    # Add retry headers if applicable
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=http_status,
        content=error_response.dict(),
        headers=headers
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler for SQLAlchemy database exceptions.
    
    Converts database errors to standardized platform exceptions.
    """
    # Convert to platform exception
    if isinstance(exc, IntegrityError):
        platform_exc = DatabaseException(
            message="Database integrity constraint violation",
            operation="database_operation",
            cause=exc
        )
    elif isinstance(exc, OperationalError):
        platform_exc = DatabaseException(
            message="Database connection or operational error",
            operation="database_connection",
            cause=exc
        )
    else:
        platform_exc = DatabaseException(
            message="Database operation failed",
            operation="database_operation",
            cause=exc
        )
    
    return await platform_exception_handler(request, platform_exc)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Fallback handler for unexpected exceptions.
    
    Ensures all exceptions are properly logged and return structured responses.
    """
    # Generate support ID for tracking
    support_id = _generate_support_id()
    
    # Extract request context
    request_context = _extract_request_context(request)
    
    # Log unexpected error
    logger.critical(
        f"Unexpected exception [{support_id}]: {type(exc).__name__} - {str(exc)}",
        extra={
            "support_id": support_id,
            "request_context": request_context,
            "stack_trace": traceback.format_exc()
        }
    )
    
    # Create standardized error response
    error_response = ErrorResponse(
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred. Please contact support.",
        request_id=request.headers.get("x-request-id"),
        support_id=support_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


async def http_exception_wrapper(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Wrapper for FastAPI's default HTTP exception handler.
    
    Adds logging and standardizes response format.
    """
    # Log HTTP exceptions
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "request_context": _extract_request_context(request)
        }
    )
    
    # Use FastAPI's default handler but ensure consistent format
    response = await http_exception_handler(request, exc)
    
    # If response is not in our format, convert it
    if hasattr(response, 'body'):
        try:
            import json
            body = json.loads(response.body)
            if not body.get('error'):
                # Convert to our format
                error_response = ErrorResponse(
                    code=ErrorCode.VALIDATION_ERROR if exc.status_code == 400 
                          else ErrorCode.INTERNAL_ERROR,
                    message=exc.detail if isinstance(exc.detail, str) else "HTTP error",
                    request_id=request.headers.get("x-request-id")
                )
                response = JSONResponse(
                    status_code=exc.status_code,
                    content=error_response.dict()
                )
        except Exception:
            # If conversion fails, use original response
            pass
    
    return response


# Exception Registration Function
def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Platform-specific exceptions
    app.add_exception_handler(PlatformException, platform_exception_handler)
    
    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # HTTP exceptions (override default)
    app.add_exception_handler(HTTPException, http_exception_wrapper)
    
    # General exception fallback
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")


# Retry Decorator
def with_retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        exponential_backoff: Whether to use exponential backoff
        exceptions: Tuple of exceptions to retry on
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = delay_seconds * (2 ** attempt if exponential_backoff else 1)
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}). "
                            f"Retrying in {delay}s: {str(e)}"
                        )
                        import asyncio
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
            
            raise last_exception
        
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = delay_seconds * (2 ** attempt if exponential_backoff else 1)
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}). "
                            f"Retrying in {delay}s: {str(e)}"
                        )
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator