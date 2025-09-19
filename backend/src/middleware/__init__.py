"""
Middleware package for the Course Generation Platform.

Contains all middleware components including:
- Security middleware (CORS, headers, validation)
- Authentication middleware
- Rate limiting middleware
"""

from .security import (
    setup_security_middleware,
    get_security_info,
    validate_security_config,
    SecurityConfig,
    SecurityHeadersMiddleware,
    SecurityValidationMiddleware,
)

__all__ = [
    "setup_security_middleware",
    "get_security_info", 
    "validate_security_config",
    "SecurityConfig",
    "SecurityHeadersMiddleware",
    "SecurityValidationMiddleware",
]