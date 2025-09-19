"""
API Key Authentication system for the Course Platform API.

Provides secure API key-based authentication with:
- Database-backed key storage and validation
- Permission-based access control 
- Rate limiting per API key
- Key expiration and revocation
- Usage tracking and analytics
- Secure key generation and hashing
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..models.base import Base


class APIKeyStatus(str, Enum):
    """API Key status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKeyScope(str, Enum):
    """API Key permission scopes."""
    # Course operations
    COURSE_READ = "course:read"
    COURSE_WRITE = "course:write"
    COURSE_DELETE = "course:delete"
    
    # Chapter operations
    CHAPTER_READ = "chapter:read"
    CHAPTER_WRITE = "chapter:write"
    CHAPTER_DELETE = "chapter:delete"
    
    # Quiz operations
    QUIZ_READ = "quiz:read"
    QUIZ_WRITE = "quiz:write"
    QUIZ_DELETE = "quiz:delete"
    
    # Generation operations
    GENERATION_CREATE = "generation:create"
    GENERATION_READ = "generation:read"
    GENERATION_CANCEL = "generation:cancel"
    
    # Export operations
    EXPORT_PDF = "export:pdf"
    EXPORT_WORD = "export:word"
    EXPORT_HTML = "export:html"
    
    # Quality operations
    QUALITY_CHECK = "quality:check"
    QUALITY_REPORT = "quality:report"
    
    # Admin operations
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    API_KEY_MANAGE = "api_key:manage"


class APIKeyPermission(str, Enum):
    """Predefined permission levels."""
    READ_ONLY = "read_only"
    CONTENT_CREATOR = "content_creator"
    POWER_USER = "power_user"
    ADMIN = "admin"


# Permission mappings
PERMISSION_SCOPES: Dict[APIKeyPermission, Set[APIKeyScope]] = {
    APIKeyPermission.READ_ONLY: {
        APIKeyScope.COURSE_READ,
        APIKeyScope.CHAPTER_READ,
        APIKeyScope.QUIZ_READ,
        APIKeyScope.GENERATION_READ,
    },
    APIKeyPermission.CONTENT_CREATOR: {
        APIKeyScope.COURSE_READ,
        APIKeyScope.COURSE_WRITE,
        APIKeyScope.CHAPTER_READ,
        APIKeyScope.CHAPTER_WRITE,
        APIKeyScope.QUIZ_READ,
        APIKeyScope.QUIZ_WRITE,
        APIKeyScope.GENERATION_CREATE,
        APIKeyScope.GENERATION_READ,
        APIKeyScope.EXPORT_PDF,
        APIKeyScope.EXPORT_WORD,
        APIKeyScope.EXPORT_HTML,
        APIKeyScope.QUALITY_CHECK,
    },
    APIKeyPermission.POWER_USER: {
        APIKeyScope.COURSE_READ,
        APIKeyScope.COURSE_WRITE,
        APIKeyScope.COURSE_DELETE,
        APIKeyScope.CHAPTER_READ,
        APIKeyScope.CHAPTER_WRITE,
        APIKeyScope.CHAPTER_DELETE,
        APIKeyScope.QUIZ_READ,
        APIKeyScope.QUIZ_WRITE,
        APIKeyScope.QUIZ_DELETE,
        APIKeyScope.GENERATION_CREATE,
        APIKeyScope.GENERATION_READ,
        APIKeyScope.GENERATION_CANCEL,
        APIKeyScope.EXPORT_PDF,
        APIKeyScope.EXPORT_WORD,
        APIKeyScope.EXPORT_HTML,
        APIKeyScope.QUALITY_CHECK,
        APIKeyScope.QUALITY_REPORT,
    },
    APIKeyPermission.ADMIN: set(APIKeyScope),  # All scopes
}


class APIKeyTable(Base):
    """SQLAlchemy model for API Key storage."""
    
    __tablename__ = "api_keys"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    key_prefix = Column(String(16), nullable=False, index=True)  # First 8 chars for identification
    
    # Permission and access control
    permission_level = Column(String(50), nullable=False)
    scopes = Column(JSON, nullable=False)  # List of allowed scopes
    
    # Usage and rate limiting
    rate_limit_per_hour = Column(Integer, nullable=False, default=1000)
    rate_limit_per_day = Column(Integer, nullable=False, default=10000)
    usage_count = Column(Integer, nullable=False, default=0)
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=APIKeyStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(Text, nullable=True)
    
    # Metadata
    created_by = Column(String(100), nullable=True)  # User ID or email
    allowed_ips = Column(JSON, nullable=True)  # List of allowed IP addresses
    user_agent_patterns = Column(JSON, nullable=True)  # Allowed user agent patterns
    
    # Usage tracking
    last_request_ip = Column(String(45), nullable=True)  # IPv6 compatible
    last_request_user_agent = Column(Text, nullable=True)
    total_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)


class APIKeyUsageLog(Base):
    """SQLAlchemy model for API Key usage logging."""
    
    __tablename__ = "api_key_usage_logs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    api_key_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Request details
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    # Client details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Additional metadata
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)


class APIKeyBase(BaseModel):
    """Base schema for API Key operations."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    permission_level: APIKeyPermission
    rate_limit_per_hour: int = Field(1000, ge=1, le=10000)
    rate_limit_per_day: int = Field(10000, ge=1, le=100000)
    expires_at: Optional[datetime] = None
    allowed_ips: Optional[List[str]] = None
    user_agent_patterns: Optional[List[str]] = None
    
    @validator("expires_at")
    def validate_expiration(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v
    
    @validator("rate_limit_per_day")
    def validate_daily_limit(cls, v, values):
        if "rate_limit_per_hour" in values:
            hourly = values["rate_limit_per_hour"]
            if v < hourly:
                raise ValueError("Daily limit must be >= hourly limit")
        return v


class APIKeyCreate(APIKeyBase):
    """Schema for creating a new API key."""
    created_by: Optional[str] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response (without sensitive data)."""
    
    id: UUID
    name: str
    description: Optional[str]
    permission_level: str
    scopes: List[str]
    rate_limit_per_hour: int
    rate_limit_per_day: int
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    key_prefix: str  # Only show first 8 characters
    
    class Config:
        from_attributes = True


class APIKeyCreateResponse(APIKeyResponse):
    """Schema for API key creation response (includes full key once)."""
    
    key: str  # Full API key - only returned once during creation


class APIKeyAuth:
    """API Key authentication and validation service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """
        Generate a secure API key and its hash.
        
        Returns:
            Tuple of (api_key, key_hash)
        """
        # Generate a secure random key
        key = f"ck_{secrets.token_urlsafe(48)}"  # ck = course key prefix
        
        # Create hash for storage
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        return key, key_hash
    
    def create_api_key(self, api_key_data: APIKeyCreate) -> APIKeyCreateResponse:
        """
        Create a new API key.
        
        Args:
            api_key_data: API key creation data
            
        Returns:
            API key response with full key (only time it's returned)
        """
        # Generate secure key and hash
        api_key, key_hash = self.generate_api_key()
        key_prefix = api_key[:8]
        
        # Get scopes for permission level
        scopes = list(PERMISSION_SCOPES[api_key_data.permission_level])
        
        # Create database record
        db_api_key = APIKeyTable(
            name=api_key_data.name,
            description=api_key_data.description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permission_level=api_key_data.permission_level.value,
            scopes=scopes,
            rate_limit_per_hour=api_key_data.rate_limit_per_hour,
            rate_limit_per_day=api_key_data.rate_limit_per_day,
            expires_at=api_key_data.expires_at,
            created_by=api_key_data.created_by,
            allowed_ips=api_key_data.allowed_ips,
            user_agent_patterns=api_key_data.user_agent_patterns,
        )
        
        self.db.add(db_api_key)
        self.db.commit()
        self.db.refresh(db_api_key)
        
        # Return response with full key
        return APIKeyCreateResponse(
            id=db_api_key.id,
            name=db_api_key.name,
            description=db_api_key.description,
            permission_level=db_api_key.permission_level,
            scopes=db_api_key.scopes,
            rate_limit_per_hour=db_api_key.rate_limit_per_hour,
            rate_limit_per_day=db_api_key.rate_limit_per_day,
            status=db_api_key.status,
            created_at=db_api_key.created_at,
            expires_at=db_api_key.expires_at,
            last_used_at=db_api_key.last_used_at,
            usage_count=db_api_key.usage_count,
            key_prefix=db_api_key.key_prefix,
            key=api_key,  # Full key only returned here
        )
    
    def validate_api_key(self, api_key: str, required_scope: Optional[APIKeyScope] = None) -> Optional[APIKeyTable]:
        """
        Validate an API key and return the associated record.
        
        Args:
            api_key: The API key to validate
            required_scope: Optional required scope for access
            
        Returns:
            API key record if valid, None otherwise
        """
        if not api_key or not api_key.startswith("ck_"):
            return None
        
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Query the database
        db_api_key = self.db.query(APIKeyTable).filter(
            APIKeyTable.key_hash == key_hash
        ).first()
        
        if not db_api_key:
            return None
        
        # Check status
        if db_api_key.status != APIKeyStatus.ACTIVE:
            return None
        
        # Check expiration
        if db_api_key.expires_at and db_api_key.expires_at <= datetime.utcnow():
            # Mark as expired
            db_api_key.status = APIKeyStatus.EXPIRED
            self.db.commit()
            return None
        
        # Check scope if required
        if required_scope and required_scope.value not in db_api_key.scopes:
            return None
        
        return db_api_key
    
    def update_usage(self, api_key_record: APIKeyTable, endpoint: str, method: str, 
                    status_code: int, ip_address: str = None, user_agent: str = None,
                    response_time_ms: int = None):
        """
        Update API key usage statistics and log the request.
        
        Args:
            api_key_record: The API key database record
            endpoint: The accessed endpoint
            method: HTTP method
            status_code: Response status code
            ip_address: Client IP address
            user_agent: Client user agent
            response_time_ms: Response time in milliseconds
        """
        # Update API key usage
        api_key_record.usage_count += 1
        api_key_record.total_requests += 1
        api_key_record.last_used_at = datetime.utcnow()
        api_key_record.last_request_ip = ip_address
        api_key_record.last_request_user_agent = user_agent
        
        if status_code >= 400:
            api_key_record.failed_requests += 1
        
        # Create usage log entry
        usage_log = APIKeyUsageLog(
            api_key_id=api_key_record.id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.db.add(usage_log)
        self.db.commit()
    
    def check_rate_limit(self, api_key_record: APIKeyTable) -> tuple[bool, str]:
        """
        Check if API key is within rate limits.
        
        Args:
            api_key_record: The API key database record
            
        Returns:
            Tuple of (is_within_limits, error_message)
        """
        now = datetime.utcnow()
        
        # Check hourly limit
        hour_ago = now - timedelta(hours=1)
        hourly_usage = self.db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.api_key_id == api_key_record.id,
            APIKeyUsageLog.timestamp >= hour_ago
        ).count()
        
        if hourly_usage >= api_key_record.rate_limit_per_hour:
            return False, f"Hourly rate limit exceeded ({api_key_record.rate_limit_per_hour}/hour)"
        
        # Check daily limit
        day_ago = now - timedelta(days=1)
        daily_usage = self.db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.api_key_id == api_key_record.id,
            APIKeyUsageLog.timestamp >= day_ago
        ).count()
        
        if daily_usage >= api_key_record.rate_limit_per_day:
            return False, f"Daily rate limit exceeded ({api_key_record.rate_limit_per_day}/day)"
        
        return True, ""
    
    def revoke_api_key(self, api_key_id: UUID, reason: str = None) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key_id: ID of the API key to revoke
            reason: Optional reason for revocation
            
        Returns:
            True if revoked successfully, False if not found
        """
        db_api_key = self.db.query(APIKeyTable).filter(
            APIKeyTable.id == api_key_id
        ).first()
        
        if not db_api_key:
            return False
        
        db_api_key.status = APIKeyStatus.REVOKED
        db_api_key.revoked_at = datetime.utcnow()
        db_api_key.revoked_reason = reason
        
        self.db.commit()
        return True
    
    def list_api_keys(self, limit: int = 100, offset: int = 0) -> List[APIKeyResponse]:
        """
        List API keys (without sensitive data).
        
        Args:
            limit: Maximum number of keys to return
            offset: Number of keys to skip
            
        Returns:
            List of API key responses
        """
        db_api_keys = self.db.query(APIKeyTable).offset(offset).limit(limit).all()
        
        return [
            APIKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                permission_level=key.permission_level,
                scopes=key.scopes,
                rate_limit_per_hour=key.rate_limit_per_hour,
                rate_limit_per_day=key.rate_limit_per_day,
                status=key.status,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                key_prefix=key.key_prefix,
            )
            for key in db_api_keys
        ]


# FastAPI dependencies
security = HTTPBearer(auto_error=False)


def get_api_key_auth(db: Session = Depends(get_db)) -> APIKeyAuth:
    """Dependency to get API key authentication service."""
    return APIKeyAuth(db)


def validate_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> Optional[APIKeyTable]:
    """
    FastAPI dependency to validate API key from Authorization header.
    
    Returns None if no valid API key is provided (for optional auth).
    """
    if not credentials or not credentials.credentials:
        return None
    
    auth_service = APIKeyAuth(db)
    return auth_service.validate_api_key(credentials.credentials)


def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db),
) -> APIKeyTable:
    """
    FastAPI dependency that requires a valid API key.
    
    Raises HTTPException if no valid API key is provided.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = APIKeyAuth(db)
    api_key_record = auth_service.validate_api_key(credentials.credentials)
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key_record


def require_permission(required_scope: APIKeyScope):
    """
    Create a dependency that requires a specific permission scope.
    
    Args:
        required_scope: The required API key scope
        
    Returns:
        FastAPI dependency function
    """
    def dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
        db: Session = Depends(get_db),
    ) -> APIKeyTable:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        auth_service = APIKeyAuth(db)
        api_key_record = auth_service.validate_api_key(credentials.credentials, required_scope)
        
        if not api_key_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API key does not have required permission: {required_scope.value}",
            )
        
        return api_key_record
    
    return dependency


# Convenience functions for common permission levels
def require_read_permission():
    """Require read permission for endpoints."""
    return require_permission(APIKeyScope.COURSE_READ)


def require_write_permission():
    """Require write permission for endpoints."""
    return require_permission(APIKeyScope.COURSE_WRITE)


def require_admin_permission():
    """Require admin permission for endpoints."""
    return require_permission(APIKeyScope.ADMIN_READ)


# Utility function to create API keys programmatically
def create_api_key(
    name: str,
    permission_level: APIKeyPermission,
    db: Session,
    description: str = None,
    expires_at: datetime = None,
    rate_limit_per_hour: int = 1000,
    rate_limit_per_day: int = 10000,
    created_by: str = None,
) -> APIKeyCreateResponse:
    """
    Utility function to create an API key programmatically.
    
    Args:
        name: Name for the API key
        permission_level: Permission level for the key
        db: Database session
        description: Optional description
        expires_at: Optional expiration date
        rate_limit_per_hour: Hourly rate limit
        rate_limit_per_day: Daily rate limit
        created_by: Who created the key
        
    Returns:
        API key creation response with full key
    """
    auth_service = APIKeyAuth(db)
    api_key_data = APIKeyCreate(
        name=name,
        description=description,
        permission_level=permission_level,
        rate_limit_per_hour=rate_limit_per_hour,
        rate_limit_per_day=rate_limit_per_day,
        expires_at=expires_at,
        created_by=created_by,
    )
    
    return auth_service.create_api_key(api_key_data)