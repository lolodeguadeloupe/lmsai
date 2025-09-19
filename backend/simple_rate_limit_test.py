#!/usr/bin/env python3
"""
Simple Rate Limiting Test Script (No external dependencies)

This script tests the basic functionality of the rate limiting middleware
without requiring pytest or other external dependencies.
"""

import asyncio
import sys
import os
import time
from unittest.mock import Mock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all rate limiting modules can be imported"""
    try:
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
        print("✅ All rate limiting modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_endpoint_classifier():
    """Test endpoint classification logic"""
    try:
        from middleware.rate_limiting import EndpointClassifier, RateLimitType
        
        # Test generation endpoints
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/courses") == RateLimitType.GENERATION
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/courses/123/regenerate-chapter") == RateLimitType.GENERATION
        
        # Test retrieval endpoints  
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/courses/123") == RateLimitType.RETRIEVAL
        assert EndpointClassifier.classify_endpoint("GET", "/health") == RateLimitType.RETRIEVAL
        
        # Test admin endpoints
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/admin/users") == RateLimitType.ADMIN
        
        # Test upload endpoints
        assert EndpointClassifier.classify_endpoint("POST", "/api/v1/upload/file") == RateLimitType.UPLOAD
        
        # Test default classification
        assert EndpointClassifier.classify_endpoint("GET", "/api/v1/unknown") == RateLimitType.STANDARD
        
        print("✅ Endpoint classification tests passed")
        return True
    except Exception as e:
        print(f"❌ Endpoint classifier test failed: {e}")
        return False

def test_rate_limit_config():
    """Test rate limit configuration"""
    try:
        from middleware.rate_limiting import RateLimitConfig, RateLimitRules, RateLimitType
        
        # Test getting configurations
        gen_config = RateLimitRules.get_config(RateLimitType.GENERATION)
        assert gen_config.requests_per_minute == 10
        assert gen_config.requests_per_hour == 50
        
        std_config = RateLimitRules.get_config(RateLimitType.STANDARD)
        assert std_config.requests_per_minute == 100
        assert std_config.requests_per_hour == 2000
        
        print("✅ Rate limit configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Rate limit config test failed: {e}")
        return False

async def test_rate_limit_store():
    """Test rate limit storage functionality"""
    try:
        from middleware.rate_limiting import RateLimitStore
        
        # Create store (will use memory mode for testing)
        store = RateLimitStore()
        store.redis_client = None  # Force memory mode
        
        # Test basic rate limiting
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
        
        print("✅ Rate limit store tests passed")
        return True
    except Exception as e:
        print(f"❌ Rate limit store test failed: {e}")
        return False

async def test_advanced_rate_limiter():
    """Test the advanced rate limiter"""
    try:
        from middleware.rate_limiting import AdvancedRateLimiter
        from fastapi import Request
        
        # Create rate limiter
        rate_limiter = AdvancedRateLimiter()
        rate_limiter.store.redis_client = None  # Force memory mode
        
        # Create mock request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/v1/courses"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        # Test user info extraction for anonymous user
        user_info = rate_limiter._get_user_info(request)
        assert user_info["role"] == "anonymous"
        assert user_info["is_authenticated"] is False
        
        # Test client identifier generation
        client_id = rate_limiter._get_client_identifier(request, user_info)
        assert client_id.startswith("ip:127.0.0.1:")
        
        # Test rate limit checking
        rate_info = await rate_limiter.check_rate_limits(request)
        assert rate_info["allowed"] is True
        assert rate_info["endpoint_type"] == "retrieval"  # GET /api/v1/courses
        assert rate_info["user_type"] == "anonymous"
        assert "limits" in rate_info
        
        print("✅ Advanced rate limiter tests passed")
        return True
    except Exception as e:
        print(f"❌ Advanced rate limiter test failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        from core.config import settings
        import redis
        
        print(f"Testing Redis connection to: {settings.REDIS_URL}")
        
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        print("✅ Redis connection successful")
        
        # Test rate limiting operations
        test_key = "test:rate:limit"
        client.zadd(test_key, {"test1": time.time()})
        count = client.zcard(test_key)
        client.delete(test_key)
        
        print(f"✅ Redis operations working (test count: {count})")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Rate limiting will fall back to memory storage")
        return False

async def test_performance():
    """Run a simple performance test"""
    try:
        from middleware.rate_limiting import AdvancedRateLimiter
        from fastapi import Request
        
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
        iterations = 100  # Reduced for simple test
        
        for _ in range(iterations):
            await rate_limiter.check_rate_limits(request)
        
        end_time = time.time()
        duration = end_time - start_time
        rate = iterations / duration
        
        print(f"✅ Processed {iterations} requests in {duration:.2f}s")
        print(f"   Rate: {rate:.2f} requests/second")
        print(f"   Average latency: {(duration/iterations)*1000:.2f}ms per request")
        
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Advanced Rate Limiting Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Endpoint Classifier", test_endpoint_classifier),
        ("Rate Limit Config", test_rate_limit_config),
        ("Redis Connection", test_redis_connection),
    ]
    
    async_tests = [
        ("Rate Limit Store", test_rate_limit_store),
        ("Advanced Rate Limiter", test_advanced_rate_limiter),
        ("Performance Test", test_performance),
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    # Run asynchronous tests
    for test_name, test_func in async_tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Tests Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)