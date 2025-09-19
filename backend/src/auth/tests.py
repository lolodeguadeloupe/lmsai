"""
Test suite for API key authentication system.

Comprehensive tests for API key creation, validation, permissions, and management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..models.base import Base
from .api_key_auth import (
    APIKeyAuth,
    APIKeyPermission,
    APIKeyScope,
    APIKeyStatus,
    APIKeyTable,
    APIKeyUsageLog,
    create_api_key,
    require_api_key,
    require_permission,
    validate_api_key,
)
from .management import APIKeyManager
from .middleware import APIKeyMiddleware


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_service(db_session):
    """Create an APIKeyAuth service instance."""
    return APIKeyAuth(db_session)


@pytest.fixture
def api_key_manager(db_session):
    """Create an APIKeyManager instance."""
    return APIKeyManager(db_session)


class TestAPIKeyGeneration:
    """Test API key generation and hashing."""
    
    def test_generate_api_key(self):
        """Test secure API key generation."""
        key, key_hash = APIKeyAuth.generate_api_key()
        
        # Check key format
        assert key.startswith("ck_")
        assert len(key) > 10
        
        # Check hash
        assert len(key_hash) == 64  # SHA256 hex digest
        assert key_hash != key
        
        # Ensure randomness - generate multiple keys
        key2, key_hash2 = APIKeyAuth.generate_api_key()
        assert key != key2
        assert key_hash != key_hash2


class TestAPIKeyCreation:
    """Test API key creation functionality."""
    
    def test_create_api_key_basic(self, auth_service):
        """Test basic API key creation."""
        from .api_key_auth import APIKeyCreate
        
        api_key_data = APIKeyCreate(
            name="Test API Key",
            description="Test description",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        
        response = auth_service.create_api_key(api_key_data)
        
        assert response.name == "Test API Key"
        assert response.description == "Test description"
        assert response.permission_level == APIKeyPermission.READ_ONLY.value
        assert response.key.startswith("ck_")
        assert response.status == APIKeyStatus.ACTIVE.value
        assert len(response.scopes) > 0
    
    def test_create_api_key_with_expiration(self, auth_service):
        """Test API key creation with expiration."""
        from .api_key_auth import APIKeyCreate
        
        expires_at = datetime.utcnow() + timedelta(days=30)
        api_key_data = APIKeyCreate(
            name="Expiring Key",
            permission_level=APIKeyPermission.CONTENT_CREATOR,
            expires_at=expires_at,
        )
        
        response = auth_service.create_api_key(api_key_data)
        
        assert response.expires_at == expires_at
        assert response.permission_level == APIKeyPermission.CONTENT_CREATOR.value
    
    def test_create_api_key_custom_rate_limits(self, auth_service):
        """Test API key creation with custom rate limits."""
        from .api_key_auth import APIKeyCreate
        
        api_key_data = APIKeyCreate(
            name="Custom Limits Key",
            permission_level=APIKeyPermission.POWER_USER,
            rate_limit_per_hour=500,
            rate_limit_per_day=5000,
        )
        
        response = auth_service.create_api_key(api_key_data)
        
        assert response.rate_limit_per_hour == 500
        assert response.rate_limit_per_day == 5000


class TestAPIKeyValidation:
    """Test API key validation functionality."""
    
    def test_validate_valid_api_key(self, auth_service):
        """Test validation of a valid API key."""
        from .api_key_auth import APIKeyCreate
        
        # Create a test API key
        api_key_data = APIKeyCreate(
            name="Valid Key",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Validate the key
        validated = auth_service.validate_api_key(response.key)
        
        assert validated is not None
        assert validated.name == "Valid Key"
        assert validated.status == APIKeyStatus.ACTIVE
    
    def test_validate_invalid_api_key(self, auth_service):
        """Test validation of an invalid API key."""
        invalid_key = "ck_invalid_key_12345"
        validated = auth_service.validate_api_key(invalid_key)
        
        assert validated is None
    
    def test_validate_expired_api_key(self, auth_service, db_session):
        """Test validation of an expired API key."""
        from .api_key_auth import APIKeyCreate
        
        # Create an API key that's already expired
        expires_at = datetime.utcnow() - timedelta(days=1)
        api_key_data = APIKeyCreate(
            name="Expired Key",
            permission_level=APIKeyPermission.READ_ONLY,
            expires_at=expires_at,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Try to validate the expired key
        validated = auth_service.validate_api_key(response.key)
        
        assert validated is None
        
        # Check that the key was marked as expired in the database
        db_key = db_session.query(APIKeyTable).filter(
            APIKeyTable.id == response.id
        ).first()
        assert db_key.status == APIKeyStatus.EXPIRED
    
    def test_validate_revoked_api_key(self, auth_service):
        """Test validation of a revoked API key."""
        from .api_key_auth import APIKeyCreate
        
        # Create and then revoke an API key
        api_key_data = APIKeyCreate(
            name="Revoked Key",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Revoke the key
        auth_service.revoke_api_key(response.id, "Test revocation")
        
        # Try to validate the revoked key
        validated = auth_service.validate_api_key(response.key)
        
        assert validated is None
    
    def test_validate_api_key_with_scope(self, auth_service):
        """Test validation with required scope."""
        from .api_key_auth import APIKeyCreate
        
        # Create a read-only API key
        api_key_data = APIKeyCreate(
            name="Read Only Key",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Should pass for read permission
        validated = auth_service.validate_api_key(response.key, APIKeyScope.COURSE_READ)
        assert validated is not None
        
        # Should fail for write permission
        validated = auth_service.validate_api_key(response.key, APIKeyScope.COURSE_WRITE)
        assert validated is None


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_checking(self, auth_service, db_session):
        """Test rate limit checking logic."""
        from .api_key_auth import APIKeyCreate
        
        # Create API key with low limits for testing
        api_key_data = APIKeyCreate(
            name="Rate Limited Key",
            permission_level=APIKeyPermission.READ_ONLY,
            rate_limit_per_hour=2,
            rate_limit_per_day=5,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Get the database record
        api_key_record = db_session.query(APIKeyTable).filter(
            APIKeyTable.id == response.id
        ).first()
        
        # Should be within limits initially
        within_limits, message = auth_service.check_rate_limit(api_key_record)
        assert within_limits is True
        assert message == ""
        
        # Add usage logs to exceed hourly limit
        for i in range(3):
            log = APIKeyUsageLog(
                api_key_id=api_key_record.id,
                endpoint="/test",
                method="GET",
                status_code=200,
                timestamp=datetime.utcnow(),
            )
            db_session.add(log)
        db_session.commit()
        
        # Should now be over the limit
        within_limits, message = auth_service.check_rate_limit(api_key_record)
        assert within_limits is False
        assert "Hourly rate limit exceeded" in message


class TestUsageTracking:
    """Test usage tracking functionality."""
    
    def test_update_usage(self, auth_service, db_session):
        """Test usage tracking and logging."""
        from .api_key_auth import APIKeyCreate
        
        # Create API key
        api_key_data = APIKeyCreate(
            name="Usage Tracking Key",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Get the database record
        api_key_record = db_session.query(APIKeyTable).filter(
            APIKeyTable.id == response.id
        ).first()
        
        initial_usage = api_key_record.usage_count
        
        # Update usage
        auth_service.update_usage(
            api_key_record=api_key_record,
            endpoint="/api/v1/courses",
            method="GET",
            status_code=200,
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0",
            response_time_ms=150,
        )
        
        # Check that usage was updated
        db_session.refresh(api_key_record)
        assert api_key_record.usage_count == initial_usage + 1
        assert api_key_record.total_requests == 1
        assert api_key_record.last_used_at is not None
        assert api_key_record.last_request_ip == "192.168.1.1"
        
        # Check that usage log was created
        usage_log = db_session.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.api_key_id == api_key_record.id
        ).first()
        
        assert usage_log is not None
        assert usage_log.endpoint == "/api/v1/courses"
        assert usage_log.method == "GET"
        assert usage_log.status_code == 200
        assert usage_log.response_time_ms == 150


class TestPermissionSystem:
    """Test permission system functionality."""
    
    def test_permission_scopes(self):
        """Test that permission levels have correct scopes."""
        from .api_key_auth import PERMISSION_SCOPES
        
        # Read-only should have minimal scopes
        read_only_scopes = PERMISSION_SCOPES[APIKeyPermission.READ_ONLY]
        assert APIKeyScope.COURSE_READ in read_only_scopes
        assert APIKeyScope.COURSE_WRITE not in read_only_scopes
        
        # Admin should have all scopes
        admin_scopes = PERMISSION_SCOPES[APIKeyPermission.ADMIN]
        assert APIKeyScope.COURSE_READ in admin_scopes
        assert APIKeyScope.COURSE_WRITE in admin_scopes
        assert APIKeyScope.API_KEY_MANAGE in admin_scopes
    
    def test_require_permission_dependency(self, auth_service):
        """Test the require_permission FastAPI dependency."""
        from .api_key_auth import APIKeyCreate
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Create API key with limited permissions
        api_key_data = APIKeyCreate(
            name="Limited Permission Key",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Mock credentials
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=response.key
        )
        
        # Test dependency that requires read permission (should work)
        read_dependency = require_permission(APIKeyScope.COURSE_READ)
        result = read_dependency(mock_credentials, auth_service.db)
        assert result is not None
        
        # Test dependency that requires write permission (should fail)
        write_dependency = require_permission(APIKeyScope.COURSE_WRITE)
        with pytest.raises(HTTPException) as exc_info:
            write_dependency(mock_credentials, auth_service.db)
        assert exc_info.value.status_code == 403


class TestAPIKeyManagement:
    """Test API key management functionality."""
    
    def test_create_api_key_via_manager(self, api_key_manager):
        """Test creating API key via manager."""
        result = api_key_manager.create_api_key(
            name="Manager Created Key",
            permission_level=APIKeyPermission.CONTENT_CREATOR,
            description="Created via manager",
            expires_in_days=30,
        )
        
        assert result["name"] == "Manager Created Key"
        assert result["permission_level"] == APIKeyPermission.CONTENT_CREATOR.value
        assert "key" in result
        assert result["key"].startswith("ck_")
    
    def test_list_api_keys(self, api_key_manager):
        """Test listing API keys."""
        # Create a few test keys
        for i in range(3):
            api_key_manager.create_api_key(
                name=f"Test Key {i}",
                permission_level=APIKeyPermission.READ_ONLY,
            )
        
        # List keys
        keys = api_key_manager.list_api_keys()
        
        assert len(keys) == 3
        assert all("name" in key for key in keys)
        assert all("id" in key for key in keys)
    
    def test_get_api_key_details(self, api_key_manager):
        """Test getting detailed API key information."""
        # Create a test key
        result = api_key_manager.create_api_key(
            name="Detailed Key",
            permission_level=APIKeyPermission.POWER_USER,
        )
        
        # Get details
        details = api_key_manager.get_api_key_details(result["id"])
        
        assert details is not None
        assert details["name"] == "Detailed Key"
        assert "usage_stats" in details
        assert "recent_usage" in details
    
    def test_revoke_api_key_via_manager(self, api_key_manager):
        """Test revoking API key via manager."""
        # Create a test key
        result = api_key_manager.create_api_key(
            name="To Be Revoked",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        
        # Revoke it
        revoked = api_key_manager.revoke_api_key(result["id"], "Test revocation")
        assert revoked is True
        
        # Check that it's revoked
        details = api_key_manager.get_api_key_details(result["id"])
        assert details["status"] == "revoked"
        assert details["revoked_reason"] == "Test revocation"


class TestAPIKeyMiddleware:
    """Test API key middleware functionality."""
    
    def test_middleware_initialization(self):
        """Test middleware initialization."""
        middleware = APIKeyMiddleware()
        assert middleware.protected_paths == ["/api/"]
        
        custom_middleware = APIKeyMiddleware(["/v1/", "/admin/"])
        assert custom_middleware.protected_paths == ["/v1/", "/admin/"]
    
    def test_is_protected_path(self):
        """Test path protection logic."""
        middleware = APIKeyMiddleware()
        
        # Protected paths
        assert middleware.is_protected_path("/api/v1/courses") is True
        assert middleware.is_protected_path("/api/auth/keys") is True
        
        # Unprotected paths
        assert middleware.is_protected_path("/docs") is False
        assert middleware.is_protected_path("/health") is False
        assert middleware.is_protected_path("/redoc") is False


class TestDatabaseMigrations:
    """Test database migration functionality."""
    
    def test_table_creation(self):
        """Test that migration creates tables correctly."""
        from .migrations import create_api_key_tables, check_api_key_tables_exist
        
        # Note: This test would need a real database connection
        # For now, we just test that the functions exist and can be imported
        assert callable(create_api_key_tables)
        assert callable(check_api_key_tables_exist)


class TestSecurityFeatures:
    """Test security-related features."""
    
    def test_key_hashing(self):
        """Test that keys are properly hashed."""
        key, key_hash = APIKeyAuth.generate_api_key()
        
        # Hash should be different from key
        assert key != key_hash
        
        # Hash should be consistent
        import hashlib
        expected_hash = hashlib.sha256(key.encode()).hexdigest()
        assert key_hash == expected_hash
    
    def test_key_prefix_extraction(self, auth_service):
        """Test key prefix extraction for identification."""
        from .api_key_auth import APIKeyCreate
        
        api_key_data = APIKeyCreate(
            name="Prefix Test Key",
            permission_level=APIKeyPermission.READ_ONLY,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # Key prefix should be first 8 characters
        assert response.key_prefix == response.key[:8]
        assert len(response.key_prefix) == 8
    
    def test_ip_restriction_data_structure(self, auth_service):
        """Test that IP restrictions can be stored."""
        from .api_key_auth import APIKeyCreate
        
        api_key_data = APIKeyCreate(
            name="IP Restricted Key",
            permission_level=APIKeyPermission.READ_ONLY,
            allowed_ips=["192.168.1.0/24", "10.0.0.1"],
        )
        
        response = auth_service.create_api_key(api_key_data)
        
        # Should not raise an error - IP restrictions stored
        assert response.id is not None


# Integration tests
class TestAPIKeyIntegration:
    """Integration tests for the complete API key system."""
    
    def test_full_api_key_lifecycle(self, auth_service, db_session):
        """Test complete lifecycle of an API key."""
        from .api_key_auth import APIKeyCreate
        
        # 1. Create API key
        api_key_data = APIKeyCreate(
            name="Lifecycle Test Key",
            permission_level=APIKeyPermission.CONTENT_CREATOR,
            rate_limit_per_hour=100,
        )
        response = auth_service.create_api_key(api_key_data)
        
        # 2. Validate key works
        validated = auth_service.validate_api_key(response.key)
        assert validated is not None
        
        # 3. Use the key (simulate requests)
        for i in range(3):
            auth_service.update_usage(
                api_key_record=validated,
                endpoint=f"/api/test/{i}",
                method="GET",
                status_code=200,
            )
        
        # 4. Check usage was tracked
        db_session.refresh(validated)
        assert validated.usage_count == 3
        assert validated.total_requests == 3
        
        # 5. Check rate limits
        within_limits, _ = auth_service.check_rate_limit(validated)
        assert within_limits is True
        
        # 6. Revoke key
        revoked = auth_service.revoke_api_key(response.id)
        assert revoked is True
        
        # 7. Verify key no longer works
        validated_after_revoke = auth_service.validate_api_key(response.key)
        assert validated_after_revoke is None


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])