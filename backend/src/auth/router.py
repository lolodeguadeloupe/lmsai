"""
API router for API key management endpoints.

Provides REST endpoints for managing API keys.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database.session import get_db
from .api_key_auth import (
    APIKeyAuth,
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyScope,
    require_permission,
)
from .management import APIKeyManager

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.API_KEY_MANAGE)),
):
    """
    Create a new API key.
    
    Requires admin permission to create API keys.
    
    **Note**: The full API key is only returned once during creation.
    Store it securely as it cannot be retrieved later.
    """
    auth_service = APIKeyAuth(db)
    
    try:
        return auth_service.create_api_key(api_key_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of keys to return"),
    offset: int = Query(0, ge=0, description="Number of keys to skip"),
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.API_KEY_MANAGE)),
):
    """
    List API keys with pagination.
    
    Requires admin permission. Returns API key information without sensitive data.
    """
    auth_service = APIKeyAuth(db)
    return auth_service.list_api_keys(limit=limit, offset=offset)


@router.get("/api-keys/{api_key_id}", response_model=dict)
async def get_api_key_details(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.API_KEY_MANAGE)),
):
    """
    Get detailed information about a specific API key.
    
    Includes usage statistics and recent activity.
    """
    manager = APIKeyManager(db)
    details = manager.get_api_key_details(str(api_key_id))
    
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return details


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: UUID,
    reason: Optional[str] = Query(None, description="Reason for revocation"),
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.API_KEY_MANAGE)),
):
    """
    Revoke an API key.
    
    Once revoked, the API key cannot be used for authentication.
    """
    manager = APIKeyManager(db)
    
    if not manager.revoke_api_key(str(api_key_id), reason):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully"}


@router.put("/api-keys/{api_key_id}/rate-limits")
async def update_rate_limits(
    api_key_id: UUID,
    rate_limit_per_hour: Optional[int] = Query(None, ge=1, le=10000),
    rate_limit_per_day: Optional[int] = Query(None, ge=1, le=100000),
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.API_KEY_MANAGE)),
):
    """
    Update rate limits for an API key.
    
    At least one rate limit must be specified.
    """
    if rate_limit_per_hour is None and rate_limit_per_day is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one rate limit must be specified"
        )
    
    if rate_limit_per_day and rate_limit_per_hour and rate_limit_per_day < rate_limit_per_hour:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily rate limit must be >= hourly rate limit"
        )
    
    manager = APIKeyManager(db)
    
    if not manager.update_rate_limits(
        str(api_key_id),
        rate_limit_per_hour=rate_limit_per_hour,
        rate_limit_per_day=rate_limit_per_day,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "Rate limits updated successfully"}


@router.get("/api-keys/usage/statistics")
async def get_usage_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.ADMIN_READ)),
):
    """
    Get usage statistics across all API keys.
    
    Provides insights into API usage patterns and performance.
    """
    manager = APIKeyManager(db)
    return manager.get_usage_statistics(days=days)


@router.get("/api-keys/current/info")
async def get_current_api_key_info(
    db: Session = Depends(get_db),
    current_api_key = Depends(require_permission(APIKeyScope.COURSE_READ)),
):
    """
    Get information about the current API key.
    
    Returns basic information about the API key being used for this request.
    """
    return {
        "id": str(current_api_key.id),
        "name": current_api_key.name,
        "permission_level": current_api_key.permission_level,
        "scopes": current_api_key.scopes,
        "rate_limits": {
            "per_hour": current_api_key.rate_limit_per_hour,
            "per_day": current_api_key.rate_limit_per_day,
        },
        "usage_count": current_api_key.usage_count,
        "last_used_at": current_api_key.last_used_at,
        "status": current_api_key.status,
    }


@router.get("/permissions/check")
async def check_permissions(
    scope: APIKeyScope = Query(..., description="Permission scope to check"),
    current_api_key = Depends(require_permission(APIKeyScope.COURSE_READ)),
):
    """
    Check if current API key has a specific permission.
    
    Useful for frontend applications to conditionally show features.
    """
    has_permission = scope.value in current_api_key.scopes
    
    return {
        "scope": scope.value,
        "has_permission": has_permission,
        "api_key_id": str(current_api_key.id),
        "permission_level": current_api_key.permission_level,
    }