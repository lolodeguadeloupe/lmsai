# Exception Handling Guide

## Overview

The AI Course Generation Platform includes a comprehensive exception handling system designed to provide:

- **Consistent Error Responses**: Standardized error format across all endpoints
- **Detailed Error Information**: Rich error details for debugging and user feedback
- **Proper HTTP Status Codes**: Correct HTTP status codes for different error types
- **Security**: Sensitive information protection in error messages
- **Monitoring**: Structured logging for error tracking and alerting
- **Recovery Support**: Built-in retry mechanisms and error recovery patterns

## Architecture

### Exception Hierarchy

```
PlatformException (Base)
├── ValidationException
├── ResourceNotFoundException
├── ResourceConflictException
├── DatabaseException
├── AIServiceException
│   ├── AIServiceUnavailableException
│   ├── AIServiceTimeoutException
│   ├── AIQuotaExceededException
│   ├── AIGenerationFailedException
│   └── AIContentFilteredException
├── CourseGenerationException
│   ├── CourseStructureInvalidException
│   ├── ChapterGenerationFailedException
│   ├── ContentQualityException
│   └── GenerationTimeoutException
├── VectorDatabaseException
│   ├── VectorEmbeddingFailedException
│   └── VectorSearchFailedException
└── InvalidStateException
```

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": [
    {
      "field": "field_name",
      "message": "Specific field error",
      "code": "FIELD_ERROR_CODE"
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456",
  "retry_after": 60,
  "support_id": "SUP-ABC12345"
}
```

## Usage Examples

### 1. Basic Exception Usage

```python
from core.exceptions import ResourceNotFoundException, ValidationException

# Resource not found
raise ResourceNotFoundException(
    resource_type="Course",
    resource_id=course_id
)

# Validation error with field details
raise ValidationException(
    message="Invalid course data",
    field="title",
    details=[ErrorDetail(
        field="title",
        message="Title must be unique",
        code="DUPLICATE_TITLE"
    )]
)
```

### 2. API Endpoint Implementation

```python
from core.exceptions import (
    ResourceNotFoundException,
    ResourceConflictException,
    DatabaseException,
    InvalidStateException
)

@router.get("/{course_id}")
async def get_course(course_id: UUID, db: Session = Depends(get_db)):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise ResourceNotFoundException(
                resource_type="Course",
                resource_id=course_id
            )
        
        return CourseResponse.from_orm(course)
        
    except ResourceNotFoundException:
        # Re-raise platform exceptions (handled by global handler)
        raise
    except SQLAlchemyError as e:
        # Convert database errors to platform exceptions
        raise DatabaseException(
            message="Failed to fetch course",
            operation="course_retrieval",
            cause=e
        )
```

### 3. AI Service Error Handling

```python
from core.exceptions import (
    AIServiceUnavailableException,
    AIServiceTimeoutException,
    AIQuotaExceededException
)

async def generate_content(prompt: str, provider: str):
    try:
        # AI service call
        response = await ai_client.generate(prompt)
        return response
        
    except ConnectionError as e:
        raise AIServiceUnavailableException(
            provider=provider,
            retry_after=60,
            cause=e
        )
    except TimeoutError as e:
        raise AIServiceTimeoutException(
            provider=provider,
            timeout_seconds=30,
            operation="content_generation",
            cause=e
        )
    except QuotaExceededError as e:
        raise AIQuotaExceededException(
            provider=provider,
            retry_after=3600,  # 1 hour
            cause=e
        )
```

### 4. Business Logic State Validation

```python
from core.exceptions import InvalidStateException

async def update_course(course_id: UUID, updates: dict):
    course = await get_course(course_id)
    
    # Check if course can be updated
    updatable_states = [CourseStatus.DRAFT, CourseStatus.READY]
    if course.status not in updatable_states:
        raise InvalidStateException(
            entity_type="Course",
            entity_id=course_id,
            current_state=course.status.value,
            required_states=[state.value for state in updatable_states],
            operation="update"
        )
    
    # Proceed with update
    ...
```

### 5. Retry Decorator Usage

```python
from core.exceptions import with_retry, AIServiceException

@with_retry(
    max_attempts=3,
    delay_seconds=1.0,
    exponential_backoff=True,
    exceptions=(AIServiceException,)
)
async def generate_chapter_with_retry(chapter_data):
    return await ai_service.generate_chapter(chapter_data)
```

## Error Codes Reference

### General Errors
- `INTERNAL_ERROR`: Unexpected system error
- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Authentication required
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Too many requests

### Resource Errors
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `RESOURCE_ALREADY_EXISTS`: Resource creation conflict
- `RESOURCE_CONFLICT`: Resource state conflict
- `RESOURCE_LOCKED`: Resource temporarily unavailable

### Database Errors
- `DATABASE_CONNECTION_ERROR`: Database connectivity issues
- `DATABASE_INTEGRITY_ERROR`: Database constraint violations
- `DATABASE_OPERATION_ERROR`: General database operation failures

### AI Service Errors
- `AI_SERVICE_UNAVAILABLE`: AI service not available
- `AI_SERVICE_TIMEOUT`: AI service request timeout
- `AI_SERVICE_QUOTA_EXCEEDED`: AI service quota limits
- `AI_GENERATION_FAILED`: Content generation failed
- `AI_CONTENT_FILTERED`: Content blocked by safety filters
- `AI_INVALID_RESPONSE`: Malformed AI service response

### Course Generation Errors
- `COURSE_GENERATION_FAILED`: Overall course generation failure
- `COURSE_STRUCTURE_INVALID`: Invalid course structure
- `CHAPTER_GENERATION_FAILED`: Chapter generation failure
- `CONTENT_QUALITY_FAILED`: Content quality validation failed
- `GENERATION_TIMEOUT`: Generation process timeout

### Vector Database Errors
- `VECTOR_DB_CONNECTION_ERROR`: Vector database connectivity
- `VECTOR_EMBEDDING_FAILED`: Embedding generation failed
- `VECTOR_SEARCH_FAILED`: Vector search operation failed

### Business Logic Errors
- `INVALID_COURSE_STATE`: Course in invalid state for operation
- `INVALID_CHAPTER_STATE`: Chapter in invalid state for operation
- `QUIZ_GENERATION_FAILED`: Quiz generation failed
- `EXPORT_FAILED`: Course export failed
- `IMPORT_FAILED`: Course import failed

## HTTP Status Code Mapping

The exception system automatically maps error codes to appropriate HTTP status codes:

- `400 Bad Request`: Validation errors, invalid requests
- `401 Unauthorized`: Authentication errors
- `403 Forbidden`: Authorization errors
- `404 Not Found`: Resource not found errors
- `409 Conflict`: Resource conflicts, invalid state errors
- `429 Too Many Requests`: Rate limiting, quota exceeded
- `500 Internal Server Error`: System errors, unexpected failures
- `502 Bad Gateway`: External service errors
- `503 Service Unavailable`: Service temporarily unavailable
- `504 Gateway Timeout`: External service timeouts

## Logging and Monitoring

### Log Levels
- **ERROR**: Platform exceptions, database errors, external service failures
- **WARNING**: HTTP exceptions, validation errors, business logic violations
- **CRITICAL**: Unexpected exceptions, system failures

### Log Format
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "ERROR",
  "message": "Platform exception [SUP-ABC12345]: RESOURCE_NOT_FOUND - Course with ID 'abc-123' not found",
  "error_code": "RESOURCE_NOT_FOUND",
  "error_severity": "low",
  "support_id": "SUP-ABC12345",
  "request_context": {
    "method": "GET",
    "url": "/api/v1/courses/abc-123",
    "client_host": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "exception_details": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Course with ID 'abc-123' not found",
    "severity": "low"
  }
}
```

### Monitoring Integration
- **Support IDs**: Generated for high/critical severity errors
- **Request Correlation**: X-Request-ID header tracking
- **Error Metrics**: Error rate and type tracking
- **Alerting**: Automatic alerts for critical errors

## Security Considerations

### Sensitive Data Protection
The system automatically sanitizes error messages to prevent exposure of:
- Passwords and API keys
- Database connection strings
- Internal system paths
- Personal information

### Error Message Sanitization
```python
# Automatic sanitization patterns
sensitive_patterns = [
    r'password[=:]\s*\S+',
    r'token[=:]\s*\S+', 
    r'key[=:]\s*\S+',
    r'secret[=:]\s*\S+',
    r'api[_-]key[=:]\s*\S+'
]
```

## Best Practices

### 1. Exception Selection
- Use the most specific exception type available
- Provide detailed error information for debugging
- Include relevant context (IDs, operation type, etc.)

### 2. Error Recovery
- Implement retry logic for transient failures
- Provide clear guidance on error resolution
- Use appropriate retry delays and backoff strategies

### 3. Logging
- Log all errors with sufficient context
- Include correlation IDs for request tracking
- Avoid logging sensitive information

### 4. User Experience
- Provide user-friendly error messages
- Include actionable guidance when possible
- Maintain consistent error response format

### 5. Testing
- Test error scenarios thoroughly
- Verify error responses match documentation
- Test retry and recovery mechanisms

## Integration Checklist

When integrating the exception system:

- [ ] Import required exception classes
- [ ] Replace HTTPException with platform exceptions
- [ ] Add proper exception handling in try/catch blocks
- [ ] Include detailed error information
- [ ] Use appropriate error codes
- [ ] Test error scenarios
- [ ] Verify logging output
- [ ] Check error response format
- [ ] Validate HTTP status codes
- [ ] Test retry mechanisms

## Support and Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `core.exceptions` is properly imported
2. **Missing Error Details**: Include ErrorDetail objects for validation errors
3. **Incorrect Status Codes**: Use platform exceptions instead of HTTPException
4. **Logging Issues**: Verify logger configuration and format

### Debugging Tips

1. Check support IDs in logs for critical errors
2. Use request correlation IDs to trace errors
3. Verify exception hierarchy and inheritance
4. Test error scenarios in isolation
5. Monitor error rates and patterns

For additional support, contact the development team with:
- Error logs and stack traces
- Request correlation IDs
- Support reference IDs
- Steps to reproduce the issue