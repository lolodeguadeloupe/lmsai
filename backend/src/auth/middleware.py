"""
Authentication middleware integration for API key authentication.

Provides middleware that automatically validates API keys and tracks usage.
"""

import time
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

from ..database.session import get_db_session
from .api_key_auth import APIKeyAuth, APIKeyTable


class APIKeyMiddleware:
    """
    Middleware for automatic API key validation and usage tracking.
    
    This middleware automatically:
    - Validates API keys on protected routes
    - Enforces rate limits
    - Tracks usage statistics
    - Logs API key usage
    """
    
    def __init__(self, protected_paths: Optional[list] = None):
        """
        Initialize middleware.
        
        Args:
            protected_paths: List of path prefixes that require API key auth.
                           If None, all /api/ paths are protected.
        """
        self.protected_paths = protected_paths or ["/api/"]
    
    def is_protected_path(self, path: str) -> bool:
        """
        Check if a path requires API key authentication.
        
        Args:
            path: Request path to check
            
        Returns:
            True if path requires API key, False otherwise
        """
        # Skip certain paths that don't need auth
        skip_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/api/v1/health",
        ]
        
        if any(path.startswith(skip) for skip in skip_paths):
            return False
        
        return any(path.startswith(prefix) for prefix in self.protected_paths)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through API key middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler
            
        Returns:
            Response from downstream handler
        """
        start_time = time.time()
        
        # Check if this path requires API key authentication
        if not self.is_protected_path(request.url.path):
            response = await call_next(request)
            return response
        
        # Extract API key from Authorization header
        authorization = request.headers.get("authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        
        if not authorization or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Please provide a valid API key in the Authorization header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate API key and check rate limits
        with get_db_session() as db:
            auth_service = APIKeyAuth(db)
            api_key_record = auth_service.validate_api_key(credentials)
            
            if not api_key_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check rate limits
            within_limits, error_message = auth_service.check_rate_limit(api_key_record)
            if not within_limits:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_message,
                    headers={
                        "Retry-After": "3600",
                        "X-RateLimit-Limit": str(api_key_record.rate_limit_per_hour),
                        "X-RateLimit-Remaining": "0",
                    },
                )
            
            # Store API key info in request state for use by route handlers
            request.state.api_key = api_key_record
            request.state.api_key_id = api_key_record.id
            request.state.api_key_scopes = api_key_record.scopes
            
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log usage (async to avoid blocking response)
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            auth_service.update_usage(
                api_key_record=api_key_record,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                ip_address=client_ip,
                user_agent=user_agent,
                response_time_ms=response_time_ms,
            )
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(api_key_record.rate_limit_per_hour)
            response.headers["X-API-Key-ID"] = str(api_key_record.id)
            
            return response


def create_api_key_middleware(protected_paths: Optional[list] = None) -> APIKeyMiddleware:
    """
    Factory function to create API key middleware.
    
    Args:
        protected_paths: List of path prefixes that require API key auth
        
    Returns:
        Configured APIKeyMiddleware instance
    """
    return APIKeyMiddleware(protected_paths=protected_paths)


# Utility functions to check API key permissions in route handlers
def get_current_api_key(request: Request) -> Optional[APIKeyTable]:
    """
    Get the current API key from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key record if available, None otherwise
    """
    return getattr(request.state, "api_key", None)


def check_api_key_scope(request: Request, required_scope: str) -> bool:
    """
    Check if current API key has required scope.
    
    Args:
        request: FastAPI request object
        required_scope: Required scope string
        
    Returns:
        True if API key has scope, False otherwise
    """
    scopes = getattr(request.state, "api_key_scopes", [])
    return required_scope in scopes


def require_api_key_scope(request: Request, required_scope: str) -> None:
    """
    Require API key to have specific scope, raise exception if not.
    
    Args:
        request: FastAPI request object
        required_scope: Required scope string
        
    Raises:
        HTTPException if scope not available
    """
    if not check_api_key_scope(request, required_scope):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key does not have required permission: {required_scope}",
        )