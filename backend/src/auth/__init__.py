"""
Authentication module for the Course Platform API.

Provides API key authentication, JWT authentication, and related utilities.
"""

from .api_key_auth import (
    APIKeyAuth,
    APIKeyPermission,
    APIKeyScope,
    APIKeyStatus,
    create_api_key,
    get_api_key_auth,
    require_api_key,
    require_permission,
    validate_api_key,
)

__all__ = [
    "APIKeyAuth",
    "APIKeyPermission", 
    "APIKeyScope",
    "APIKeyStatus",
    "create_api_key",
    "get_api_key_auth",
    "require_api_key",
    "require_permission",
    "validate_api_key",
]