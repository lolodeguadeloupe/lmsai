"""
Test Suite for Advanced Rate Limiting Middleware

Run this test to validate rate limiting functionality:
python test_rate_limiting.py
"""

import asyncio
import time
import pytest
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
import redis
from unittest.mock import Mock, patch

# Import the rate limiting components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from middleware.rate_limiting import (
    RateLimitType,
    RateLimitConfig,
    RateLimitRules,
    EndpointClassifier,
    RateLimitStore,
    AdvancedRateLimiter,
    rate_limit_dependency,
    RateLimitMiddleware
)

class TestEndpointClassifier:
    """Test endpoint classification logic"""
    
    def test_generation_endpoint_classification(self):
        """Test that generation endpoints are correctly classified"""
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/courses") == RateLimitType.GENERATION
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/courses/123/regenerate-chapter") == RateLimitType.GENERATION
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/generation/start") == RateLimitType.GENERATION
    
    def test_retrieval_endpoint_classification(self):
        """Test that retrieval endpoints are correctly classified"""
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/courses/123") == RateLimitType.RETRIEVAL
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/courses/123/chapters") == RateLimitType.RETRIEVAL
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/export/course/123") == RateLimitType.RETRIEVAL
        assert EndpointClassifier.classify_endpoint("GET", "/health") == RateLimitType.RETRIEVAL
    
    def test_admin_endpoint_classification(self):
        """Test that admin endpoints are correctly classified"""
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/admin/users") == RateLimitType.ADMIN
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/users/123/admin") == RateLimitType.ADMIN
    
    def test_upload_endpoint_classification(self):
        """Test that upload endpoints are correctly classified"""
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/upload/file") == RateLimitType.UPLOAD
        assert EndpointClassifier.classify_endpoint("PUT", "/api/v1/files/123") == RateLimitType.UPLOAD
    
    def test_default_classification(self):
        """Test that unknown endpoints default to standard"""
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/unknown") == RateLimitType.STANDARD
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/other") == RateLimitType.STANDARD

class TestRateLimitStore:
    """Test rate limit storage functionality"""
    
    @pytest.fixture
    def store(self):
        """Create a test rate limit store"""
        store = RateLimitStore()
        # Force memory mode for testing
        store.redis_client = None
        return store
    
    @pytest.mark.asyncio
    async def test_memory_rate_limiting(self, store):
        """Test memory-based rate limiting"""
        identifier = "test:user:123"
        
        # First request should be allowed
        allowed, count, limit = await store.check_rate_limit(identifier, 60, 5)
        assert allowed is True
        assert count == 1
        assert limit == 5
        
        # Multiple requests within limit
        for i in range(2, 6):
            allowed, count, limit = await store.check_rate_limit(identifier, 60, 5)
            assert allowed is True
            assert count == i
        
        # Sixth request should be denied
        allowed, count, limit = await store.check_rate_limit(identifier, 60, 5)
        assert allowed is False
        assert count == 5
        assert limit == 5
    
    @pytest.mark.asyncio
    async def test_sliding_window_expiration(self, store):
        """Test that rate limits expire correctly"""
        identifier = "test:user:expire"
        
        # Fill up the rate limit
        for _ in range(3):
            await store.check_rate_limit(identifier, 1, 3)  # 1 second window
        
        # Next request should be denied
        allowed, _, _ = await store.check_rate_limit(identifier, 1, 3)
        assert allowed is False
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should be allowed again
        allowed, count, _ = await store.check_rate_limit(identifier, 1, 3)
        assert allowed is True
        assert count == 1  # Counter should reset

class TestAdvancedRateLimiter:
    """Test the advanced rate limiter functionality"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a test rate limiter"""
        limiter = AdvancedRateLimiter()
        # Force memory mode for testing
        limiter.store.redis_client = None
        return limiter
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object"""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/v1/courses"
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request
    
    def test_get_user_info_anonymous(self, rate_limiter, mock_request):
        """Test user info extraction for anonymous users"""
        user_info = rate_limiter._get_user_info(mock_request)
        
        assert user_info["user_id"] is None
        assert user_info["role"] == "anonymous"
        assert user_info["is_authenticated"] is False
        assert user_info["is_premium"] is False
    
    def test_get_user_info_authenticated(self, rate_limiter, mock_request):
        """Test user info extraction for authenticated users"""
        # Mock JWT token
        mock_request.headers = {
            "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIiwicm9sZSI6InVzZXIifQ.test"
        }
        
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "user123",
                "role": "user",
                "is_premium": False
            }
            
            user_info = rate_limiter._get_user_info(mock_request)
            
            assert user_info["user_id"] == "user123"
            assert user_info["role"] == "user"
            assert user_info["is_authenticated"] is True
            assert user_info["is_premium"] is False
    
    def test_client_identifier_generation(self, rate_limiter, mock_request):
        """Test client identifier generation"""
        # Anonymous user
        user_info = {"is_authenticated": False, "user_id": None}
        client_id = rate_limiter._get_client_identifier(mock_request, user_info)
        assert client_id.startswith("ip:127.0.0.1:")
        
        # Authenticated user
        user_info = {"is_authenticated": True, "user_id": "user123"}
        client_id = rate_limiter._get_client_identifier(mock_request, user_info)
        assert client_id == "user:user123"
    
    def test_user_multipliers(self, rate_limiter):
        """Test user type multipliers"""
        base_config = RateLimitConfig(requests_per_minute=100)
        
        # Anonymous user
        user_info = {"role": "anonymous", "is_authenticated": False, "is_premium": False}
        config = rate_limiter._apply_user_multipliers(base_config, user_info)
        assert config.requests_per_minute == 100
        
        # Authenticated user
        user_info = {"role": "user", "is_authenticated": True, "is_premium": False}
        config = rate_limiter._apply_user_multipliers(base_config, user_info)
        assert config.requests_per_minute == 200  # 2x multiplier
        
        # Premium user
        user_info = {"role": "user", "is_authenticated": True, "is_premium": True}
        config = rate_limiter._apply_user_multipliers(base_config, user_info)
        assert config.requests_per_minute == 500  # 5x multiplier
        
        # Admin user
        user_info = {"role": "admin", "is_authenticated": True, "is_premium": False}
        config = rate_limiter._apply_user_multipliers(base_config, user_info)
        assert config.requests_per_minute == 1000  # 10x multiplier
    
    @pytest.mark.asyncio
    async def test_rate_limit_checking(self, rate_limiter, mock_request):
        """Test rate limit checking functionality"""
        # First request should be allowed
        rate_info = await rate_limiter.check_rate_limits(mock_request)
        
        assert rate_info["allowed"] is True
        assert rate_info["endpoint_type"] == "retrieval"  # GET /api/v1/courses
        assert rate_info["user_type"] == "anonymous"
        assert "limits" in rate_info
        assert "second" in rate_info["limits"]
        assert "minute" in rate_info["limits"]
        assert "hour" in rate_info["limits"]
        assert "day" in rate_info["limits"]

class TestFastAPIIntegration:
    """Test FastAPI integration"""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with rate limiting"""
        app = FastAPI()
        
        # Add rate limiting middleware
        app.add_middleware(RateLimitMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/test/rate-limited")
        async def rate_limited_endpoint(rate_info = Depends(rate_limit_dependency)):
            return {"message": "rate limited", "rate_info": rate_info}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client"""
        return TestClient(app)
    
    def test_middleware_integration(self, client):
        """Test that middleware is working"""
        response = client.get("/test")
        assert response.status_code == 200
        
        # Check for rate limit headers
        assert any(header.startswith("X-RateLimit") for header in response.headers.keys())
    
    def test_dependency_integration(self, client):
        """Test that dependency is working"""
        response = client.get("/test/rate-limited")
        assert response.status_code == 200
        
        data = response.json()
        assert "rate_info" in data
    
    def test_rate_limit_exceeded(self, client):
        """Test rate limit exceeded response"""
        # This test would need to be implemented with a very low rate limit
        # for practical testing, or with time manipulation
        pass

def run_performance_test():
    """Run a simple performance test"""
    print("Running performance test...")
    
    # Create rate limiter
    rate_limiter = AdvancedRateLimiter()
    rate_limiter.store.redis_client = None  # Force memory mode
    
    # Create mock request
    request = Mock(spec=Request)
    request.method = "GET"
    request.url.path = "/api/v1/test"
    request.client.host = "127.0.0.1"
    request.headers = {}
    
    # Test performance
    start_time = time.time()
    iterations = 1000
    
    for _ in range(iterations):
        asyncio.run(rate_limiter.check_rate_limits(request))
    
    end_time = time.time()
    duration = end_time - start_time
    rate = iterations / duration
    
    print(f"Processed {iterations} requests in {duration:.2f}s")
    print(f"Rate: {rate:.2f} requests/second")
    print(f"Average latency: {(duration/iterations)*1000:.2f}ms per request")

def run_redis_connection_test():
    """Test Redis connection"""
    print("Testing Redis connection...")
    
    try:
        from core.config import settings
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        print("✅ Redis connection successful")
        
        # Test rate limiting operations
        client.zadd("test:rate:limit", {"test1": time.time()})
        count = client.zcard("test:rate:limit")
        client.delete("test:rate:limit")
        
        print(f"✅ Redis operations working (test count: {count})")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Rate limiting will fall back to memory storage")

if __name__ == "__main__":
    print("Advanced Rate Limiting Test Suite")
    print("=" * 50)
    
    # Run basic tests
    print("\n1. Testing Redis connection...")
    run_redis_connection_test()
    
    print("\n2. Running performance test...")
    run_performance_test()
    
    print("\n3. Running unit tests...")
    pytest.main([__file__, "-v"])
    
    print("\n✅ All tests completed!")
    print("\nTo run specific tests:")
    print("  pytest test_rate_limiting.py::TestEndpointClassifier -v")
    print("  pytest test_rate_limiting.py::TestRateLimitStore -v")
    print("  pytest test_rate_limiting.py::TestAdvancedRateLimiter -v")