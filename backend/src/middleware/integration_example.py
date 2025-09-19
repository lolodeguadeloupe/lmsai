"""
Integration Example for Advanced Rate Limiting Middleware

This file shows how to integrate the rate limiting middleware into your FastAPI application.
Copy the relevant code sections into your main.py or API route files.
"""

from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse

# Import the rate limiting components
from middleware.rate_limiting import (
    RateLimitMiddleware,
    rate_limit_dependency,
    generation_rate_limit,
    admin_rate_limit,
    rate_limiter_health,
    advanced_rate_limiter
)

# Example 1: Adding rate limiting as FastAPI middleware (global)
def setup_global_rate_limiting(app: FastAPI):
    """Add rate limiting middleware to the entire application"""
    app.add_middleware(RateLimitMiddleware)

# Example 2: Using rate limiting as a dependency (per-endpoint)
def setup_dependency_rate_limiting():
    """Examples of using rate limiting as dependencies"""
    
    from fastapi import APIRouter
    router = APIRouter()
    
    # Standard rate limiting for any endpoint
    @router.get("/api/v1/example")
    async def example_endpoint(
        request: Request,
        rate_info = Depends(rate_limit_dependency)
    ):
        return {"message": "This endpoint is rate limited"}
    
    # Generation endpoints with specific rate limiting
    @router.post("/api/v1/courses")
    async def create_course(
        request: Request,
        rate_info = Depends(generation_rate_limit())
    ):
        return {"message": "Course creation with generation rate limiting"}
    
    # Admin endpoints with specific rate limiting
    @router.get("/api/v1/admin/stats")
    async def admin_stats(
        request: Request,
        rate_info = Depends(admin_rate_limit())
    ):
        return {"message": "Admin endpoint with admin rate limiting"}
    
    return router

# Example 3: Adding rate limit headers to responses
def setup_response_headers_middleware(app: FastAPI):
    """Add rate limit headers to all responses"""
    
    @app.middleware("http")
    async def add_rate_limit_headers(request: Request, call_next):
        response = await call_next(request)
        
        # Add rate limit headers if they were set by the rate limiter
        if hasattr(request.state, 'rate_limit_headers'):
            for key, value in request.state.rate_limit_headers.items():
                response.headers[key] = value
        
        return response

# Example 4: Health check integration
def setup_health_endpoints(app: FastAPI):
    """Add health check endpoints including rate limiter health"""
    
    @app.get("/health/rate-limiter")
    async def rate_limiter_health_endpoint():
        """Rate limiter specific health check"""
        return await rate_limiter_health()
    
    @app.get("/health/detailed")
    async def detailed_health():
        """Comprehensive health check including rate limiter"""
        rate_limiter_status = await rate_limiter_health()
        
        return {
            "api": {"status": "healthy"},
            "rate_limiter": rate_limiter_status,
            "timestamp": rate_limiter_status["timestamp"]
        }

# Example 5: Custom error handling for rate limits
def setup_custom_error_handling(app: FastAPI):
    """Add custom error handling for rate limit errors"""
    
    from fastapi import HTTPException, status
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(429)  # HTTP_429_TOO_MANY_REQUESTS
    async def rate_limit_handler(request: Request, exc: HTTPException):
        """Custom rate limit error response"""
        
        # Get detailed rate limit info if available
        try:
            user_info = advanced_rate_limiter._get_user_info(request)
            client_id = advanced_rate_limiter._get_client_identifier(request, user_info)
            rate_info = await advanced_rate_limiter.store.get_rate_limit_info(client_id)
        except:
            rate_info = {}
        
        error_response = {
            "error": "Rate limit exceeded",
            "message": exc.detail,
            "retry_after_seconds": exc.headers.get("Retry-After", "unknown"),
            "documentation": "/docs#rate-limiting",
            "rate_limit_info": rate_info
        }
        
        return JSONResponse(
            status_code=429,
            content=error_response,
            headers=exc.headers or {}
        )

# Example 6: Complete integration in main.py
def create_app_with_rate_limiting():
    """Complete example of FastAPI app with rate limiting"""
    
    app = FastAPI(
        title="Course Generation Platform API",
        description="AI-powered course creation with advanced rate limiting",
        version="1.0.0"
    )
    
    # Method 1: Add as global middleware (recommended for most cases)
    setup_global_rate_limiting(app)
    
    # Method 2: Add response headers middleware
    setup_response_headers_middleware(app)
    
    # Method 3: Add health check endpoints
    setup_health_endpoints(app)
    
    # Method 4: Add custom error handling
    setup_custom_error_handling(app)
    
    # Method 5: Include routes with dependency-based rate limiting
    rate_limited_router = setup_dependency_rate_limiting()
    app.include_router(rate_limited_router)
    
    return app

# Example 7: Configuration-based rate limiting
def setup_configurable_rate_limiting(app: FastAPI):
    """Example of how to make rate limiting configurable"""
    
    from core.config import settings
    
    # Only add rate limiting if enabled in configuration
    if settings.RATE_LIMIT_ENABLED:
        setup_global_rate_limiting(app)
        
        # Log rate limiting status
        import logging
        logger = logging.getLogger(__name__)
        
        storage_type = "Redis" if settings.RATE_LIMIT_REDIS_ENABLED else "Memory"
        logger.info(f"Rate limiting enabled with {storage_type} storage")
        
        # Add health checks
        setup_health_endpoints(app)
    else:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Rate limiting disabled by configuration")

# Example 8: Testing rate limits (for development)
def setup_rate_limit_testing_endpoints(app: FastAPI):
    """Add endpoints for testing rate limiting (development only)"""
    
    from core.config import settings
    
    if settings.DEBUG:
        @app.get("/test/rate-limit")
        async def test_rate_limit(request: Request):
            """Test endpoint to trigger rate limiting"""
            return {"message": "Rate limit test endpoint", "timestamp": "now"}
        
        @app.get("/test/rate-limit/info")
        async def get_rate_limit_info(request: Request):
            """Get current rate limit information for debugging"""
            user_info = advanced_rate_limiter._get_user_info(request)
            client_id = advanced_rate_limiter._get_client_identifier(request, user_info)
            rate_info = await advanced_rate_limiter.store.get_rate_limit_info(client_id)
            
            return {
                "client_id": client_id,
                "user_info": user_info,
                "rate_limit_data": rate_info
            }

# Example usage in main.py:
"""
from middleware.integration_example import (
    setup_global_rate_limiting,
    setup_response_headers_middleware,
    setup_health_endpoints,
    setup_custom_error_handling
)

app = FastAPI(title="Your API")

# Add rate limiting
setup_global_rate_limiting(app)
setup_response_headers_middleware(app)
setup_health_endpoints(app)
setup_custom_error_handling(app)

# Your existing routes...
"""