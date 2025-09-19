"""
Request/Response Logging Middleware for Course Generation Platform
Provides structured logging with correlation IDs, performance metrics, and security features.
"""

import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, Set
from contextvars import ContextVar
from urllib.parse import quote_plus

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


# Context variables for correlation tracking
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

# Sensitive data patterns to mask in logs
SENSITIVE_HEADERS: Set[str] = {
    'authorization', 'x-api-key', 'x-auth-token', 'cookie', 'set-cookie'
}

SENSITIVE_PARAMS: Set[str] = {
    'password', 'token', 'secret', 'key', 'auth', 'credential'
}

SENSITIVE_BODY_KEYS: Set[str] = {
    'password', 'token', 'secret_key', 'api_key', 'auth_token', 'credential'
}

# Skip logging for certain paths to reduce noise
SKIP_PATHS: Set[str] = {
    '/health', '/metrics', '/favicon.ico', '/robots.txt'
}

# Maximum body size to log (in bytes)
MAX_BODY_SIZE = 10000  # 10KB


class StructuredLogger:
    """Structured JSON logger for HTTP requests and responses"""
    
    def __init__(self, name: str = "course_platform.middleware.logging"):
        self.logger = logging.getLogger(name)
        
        # Ensure logger is configured for JSON output
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(self._get_json_formatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_json_formatter(self) -> logging.Formatter:
        """Create JSON formatter for structured logging"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': self.formatTime(record, self.datefmt),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'request_id': request_id_context.get(''),
                    'user_id': user_id_context.get(None),
                }
                
                # Add extra fields from record
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                                 'pathname', 'filename', 'module', 'lineno', 
                                 'funcName', 'created', 'msecs', 'relativeCreated', 
                                 'thread', 'threadName', 'processName', 'process',
                                 'exc_info', 'exc_text', 'stack_info', 'getMessage']:
                        log_data[key] = value
                
                return json.dumps(log_data, default=str, ensure_ascii=False)
        
        return JsonFormatter()
    
    def log_request(self, **kwargs):
        """Log HTTP request details"""
        self.logger.info("HTTP Request", extra=kwargs)
    
    def log_response(self, **kwargs):
        """Log HTTP response details"""
        self.logger.info("HTTP Response", extra=kwargs)
    
    def log_error(self, **kwargs):
        """Log HTTP error details"""
        self.logger.error("HTTP Error", extra=kwargs)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for comprehensive request/response logging
    
    Features:
    - Correlation ID generation and tracking
    - Performance metrics (response time, sizes)
    - Sensitive data masking
    - Structured JSON logging
    - Error tracking and correlation
    - Request/response body logging (with size limits)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        *,
        skip_paths: Optional[Set[str]] = None,
        max_body_size: int = MAX_BODY_SIZE,
        log_request_body: bool = True,
        log_response_body: bool = True,
        logger_name: str = "course_platform.middleware.logging"
    ):
        super().__init__(app)
        self.skip_paths = skip_paths or SKIP_PATHS
        self.max_body_size = max_body_size
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.logger = StructuredLogger(logger_name)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main middleware dispatch method"""
        
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request_id_context.set(correlation_id)
        
        # Extract user ID from auth header if available
        user_id = self._extract_user_id(request)
        user_id_context.set(user_id)
        
        # Start timing
        start_time = time.time()
        
        # Read and log request
        request_data = await self._prepare_request_data(request, correlation_id, user_id)
        self.logger.log_request(**request_data)
        
        # Process request and handle response
        try:
            response = await call_next(request)
            
            # Calculate timing
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log response
            response_data = await self._prepare_response_data(
                request, response, correlation_id, user_id, duration_ms
            )
            self.logger.log_response(**response_data)
            
            return response
            
        except Exception as exc:
            # Calculate timing for error case
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log error
            error_data = {
                'event_type': 'http_error',
                'correlation_id': correlation_id,
                'user_id': user_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': self._mask_sensitive_params(dict(request.query_params)),
                'duration_ms': duration_ms,
                'error_type': type(exc).__name__,
                'error_message': str(exc),
                'status_code': 500
            }
            
            self.logger.log_error(**error_data)
            raise
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from authorization header or context"""
        try:
            # Try to extract from Authorization header
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                # In a real implementation, you'd decode the JWT here
                # For now, we'll use a placeholder approach
                return "user_from_jwt"  # Replace with actual JWT decoding
            
            # Try to extract from custom headers
            user_id = request.headers.get('x-user-id')
            if user_id:
                return user_id
                
        except Exception:
            # Don't fail request if user extraction fails
            pass
        
        return None
    
    async def _prepare_request_data(
        self, 
        request: Request, 
        correlation_id: str, 
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare request data for logging"""
        
        # Basic request information
        data = {
            'event_type': 'http_request',
            'correlation_id': correlation_id,
            'user_id': user_id,
            'method': request.method,
            'path': request.url.path,
            'query_params': self._mask_sensitive_params(dict(request.query_params)),
            'headers': self._mask_sensitive_headers(dict(request.headers)),
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent', ''),
            'content_type': request.headers.get('content-type', ''),
            'content_length': request.headers.get('content-length', 0)
        }
        
        # Add request body if enabled and appropriate
        if self.log_request_body and request.method in ['POST', 'PUT', 'PATCH']:
            body = await self._get_request_body(request)
            if body:
                data['request_body'] = body
                data['request_body_size'] = len(str(body))
        
        return data
    
    async def _prepare_response_data(
        self,
        request: Request,
        response: Response,
        correlation_id: str,
        user_id: Optional[str],
        duration_ms: float
    ) -> Dict[str, Any]:
        """Prepare response data for logging"""
        
        data = {
            'event_type': 'http_response',
            'correlation_id': correlation_id,
            'user_id': user_id,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms,
            'response_headers': self._mask_sensitive_headers(dict(response.headers)),
        }
        
        # Add response size if available
        content_length = response.headers.get('content-length')
        if content_length:
            data['response_size'] = int(content_length)
        
        # Add response body if enabled and not a streaming response
        if (self.log_response_body and 
            not isinstance(response, StreamingResponse) and
            hasattr(response, 'body')):
            
            body = await self._get_response_body(response)
            if body:
                data['response_body'] = body
                data['response_body_size'] = len(str(body))
        
        return data
    
    async def _get_request_body(self, request: Request) -> Optional[Any]:
        """Safely extract and mask request body"""
        try:
            # Check content type
            content_type = request.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                body = await request.body()
                if len(body) > self.max_body_size:
                    return f"[Body too large: {len(body)} bytes]"
                
                try:
                    json_body = json.loads(body)
                    return self._mask_sensitive_json(json_body)
                except json.JSONDecodeError:
                    return "[Invalid JSON]"
            
            elif 'application/x-www-form-urlencoded' in content_type:
                form = await request.form()
                return self._mask_sensitive_params(dict(form))
            
            elif content_type.startswith('text/'):
                body = await request.body()
                if len(body) > self.max_body_size:
                    return f"[Body too large: {len(body)} bytes]"
                return body.decode('utf-8', errors='replace')
            
            else:
                # For other content types, just log the size
                body = await request.body()
                return f"[Binary content: {len(body)} bytes]"
                
        except Exception as e:
            return f"[Error reading body: {str(e)}]"
    
    async def _get_response_body(self, response: Response) -> Optional[Any]:
        """Safely extract response body"""
        try:
            if hasattr(response, 'body') and response.body:
                body = response.body
                
                if len(body) > self.max_body_size:
                    return f"[Body too large: {len(body)} bytes]"
                
                # Try to decode as JSON first
                try:
                    json_body = json.loads(body)
                    return self._mask_sensitive_json(json_body)
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, try as text
                    try:
                        return body.decode('utf-8', errors='replace')
                    except (UnicodeDecodeError, AttributeError):
                        return f"[Binary content: {len(body)} bytes]"
            
        except Exception as e:
            return f"[Error reading response body: {str(e)}]"
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive headers for logging"""
        masked = {}
        for key, value in headers.items():
            if key.lower() in SENSITIVE_HEADERS:
                masked[key] = '[MASKED]'
            else:
                masked[key] = value
        return masked
    
    def _mask_sensitive_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive query parameters"""
        masked = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_PARAMS):
                masked[key] = '[MASKED]'
            else:
                masked[key] = value
        return masked
    
    def _mask_sensitive_json(self, data: Any) -> Any:
        """Recursively mask sensitive fields in JSON data"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in SENSITIVE_BODY_KEYS):
                    masked[key] = '[MASKED]'
                else:
                    masked[key] = self._mask_sensitive_json(value)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_json(item) for item in data]
        else:
            return data


def get_correlation_id() -> str:
    """Get the current request correlation ID"""
    return request_id_context.get('')


def get_user_id() -> Optional[str]:
    """Get the current user ID from context"""
    return user_id_context.get(None)


def create_logging_middleware(
    *,
    skip_paths: Optional[Set[str]] = None,
    max_body_size: int = MAX_BODY_SIZE,
    log_request_body: bool = True,
    log_response_body: bool = True,
    logger_name: str = "course_platform.middleware.logging"
) -> RequestResponseLoggingMiddleware:
    """
    Factory function to create configured logging middleware
    
    Args:
        skip_paths: Set of paths to skip logging for
        max_body_size: Maximum body size to log (bytes)
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        logger_name: Name for the logger
    
    Returns:
        Configured logging middleware instance
    """
    def middleware_factory(app: ASGIApp) -> RequestResponseLoggingMiddleware:
        return RequestResponseLoggingMiddleware(
            app,
            skip_paths=skip_paths,
            max_body_size=max_body_size,
            log_request_body=log_request_body,
            log_response_body=log_response_body,
            logger_name=logger_name
        )
    
    return middleware_factory


# Example usage and configuration
if __name__ == "__main__":
    # Example of how to configure and add to FastAPI app
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Add the logging middleware
    app.add_middleware(
        RequestResponseLoggingMiddleware,
        skip_paths={'/health', '/metrics'},
        max_body_size=10000,
        log_request_body=True,
        log_response_body=True
    )
    
    @app.get("/test")
    async def test_endpoint():
        logger = StructuredLogger()
        logger.logger.info("Test endpoint called", extra={
            'correlation_id': get_correlation_id(),
            'user_id': get_user_id(),
            'custom_field': 'test_value'
        })
        return {"message": "Hello World", "correlation_id": get_correlation_id()}