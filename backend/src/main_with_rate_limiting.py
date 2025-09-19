"""
FastAPI main application entry point with Advanced Rate Limiting.
Course Generation Platform API with comprehensive rate limiting implementation.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import core configuration and exception handling
from core.config import settings
from core.exceptions import register_exception_handlers

# Import rate limiting components
from middleware.rate_limiting import (
    RateLimitMiddleware,
    rate_limiter_health,
    advanced_rate_limiter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from tasks.utils import get_task_queue_status
except ImportError:
    # Fallback for development
    def get_task_queue_status():
        return {"queue_health": "healthy", "note": "Task queue not configured"}

try:
    from api import api_v1_router
    logger.info("✅ API v1 router imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import API router: {e}")
    # Fallback if API router not available
    from fastapi import APIRouter
    api_v1_router = APIRouter(prefix="/api/v1")
    
    @api_v1_router.get("/health")
    async def fallback_health():
        return {"status": "fallback", "message": "API router not fully loaded"}

# Create FastAPI application
app = FastAPI(
    title="Course Generation Platform API",
    description="AI-powered course creation and management platform with advanced rate limiting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register exception handlers first (before middleware)
register_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (only if enabled in configuration)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)
    logger.info("✅ Rate limiting middleware enabled")
    
    # Add middleware to inject rate limit headers into responses
    @app.middleware("http")
    async def add_rate_limit_headers(request: Request, call_next):
        """Add rate limit headers to all responses"""
        response = await call_next(request)
        
        # Add rate limit headers if they were set by the rate limiter
        if hasattr(request.state, 'rate_limit_headers'):
            for key, value in request.state.rate_limit_headers.items():
                response.headers[key] = value
        
        return response
    
    logger.info(f"Rate limiting storage: {'Redis' if settings.RATE_LIMIT_REDIS_ENABLED else 'Memory'}")
else:
    logger.info("⚠️ Rate limiting disabled by configuration")

# Include API v1 router
app.include_router(api_v1_router)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with rate limiting information"""
    response = {
        "message": "Course Generation Platform API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
        "features": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "redis_storage": settings.RATE_LIMIT_REDIS_ENABLED if settings.RATE_LIMIT_ENABLED else False,
            "ai_generation": True,
            "course_management": True
        }
    }
    
    if settings.RATE_LIMIT_ENABLED:
        response["rate_limiting"] = {
            "enabled": True,
            "endpoints": {
                "generation": "/docs#tag/generation",
                "courses": "/docs#tag/courses",
                "admin": "/docs#tag/admin"
            },
            "headers": "X-RateLimit-*",
            "health_check": "/health/rate-limiter"
        }
    
    return response

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    health_data = {
        "status": "healthy", 
        "service": "course-platform-api",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    # Add rate limiting status if enabled
    if settings.RATE_LIMIT_ENABLED:
        try:
            rate_limiter_status = await rate_limiter_health()
            health_data["rate_limiter"] = rate_limiter_status
        except Exception as e:
            health_data["rate_limiter"] = {
                "status": "error",
                "error": str(e)
            }
    
    return health_data

@app.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check including all components"""
    health_data = {
        "api": {"status": "healthy", "version": "1.0.0"},
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    # Rate limiter health
    if settings.RATE_LIMIT_ENABLED:
        try:
            health_data["rate_limiter"] = await rate_limiter_health()
        except Exception as e:
            health_data["rate_limiter"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        health_data["rate_limiter"] = {"status": "disabled"}
    
    # Task queue health
    try:
        health_data["task_queue"] = get_task_queue_status()
    except Exception as e:
        health_data["task_queue"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Overall status
    component_statuses = [
        health_data["api"]["status"],
        health_data["rate_limiter"]["status"],
        health_data["task_queue"].get("queue_health", "unknown")
    ]
    
    overall_status = "healthy" if all(s == "healthy" for s in component_statuses) else "degraded"
    health_data["overall_status"] = overall_status
    
    return health_data

@app.get("/health/rate-limiter")
async def rate_limiter_health_endpoint():
    """Rate limiter specific health check"""
    if not settings.RATE_LIMIT_ENABLED:
        return {
            "status": "disabled",
            "message": "Rate limiting is disabled in configuration"
        }
    
    return await rate_limiter_health()

@app.get("/health/tasks")
async def task_queue_health():
    """Task queue health check endpoint"""
    try:
        queue_status = get_task_queue_status()
        return {
            "status": "healthy" if queue_status.get("queue_health") == "healthy" else "unhealthy",
            "queue_info": queue_status
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "error": str(exc)
        }

# Development and testing endpoints (only in debug mode)
if settings.DEBUG:
    @app.get("/debug/rate-limit")
    async def debug_rate_limit_info(request: Request):
        """Get current rate limit information for debugging (DEBUG mode only)"""
        if not settings.RATE_LIMIT_ENABLED:
            return {"error": "Rate limiting is disabled"}
        
        try:
            user_info = advanced_rate_limiter._get_user_info(request)
            client_id = advanced_rate_limiter._get_client_identifier(request, user_info)
            rate_info = await advanced_rate_limiter.store.get_rate_limit_info(client_id)
            
            return {
                "client_id": client_id,
                "user_info": user_info,
                "rate_limit_data": rate_info,
                "debug_mode": True
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/debug/config")
    async def debug_configuration():
        """Get current configuration for debugging (DEBUG mode only)"""
        return {
            "rate_limiting": {
                "enabled": settings.RATE_LIMIT_ENABLED,
                "redis_enabled": settings.RATE_LIMIT_REDIS_ENABLED,
                "redis_url": settings.REDIS_URL if settings.RATE_LIMIT_REDIS_ENABLED else None,
                "standard_limits": {
                    "per_second": settings.RATE_LIMIT_STANDARD_PER_SECOND,
                    "per_minute": settings.RATE_LIMIT_STANDARD_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_STANDARD_PER_HOUR,
                    "per_day": settings.RATE_LIMIT_STANDARD_PER_DAY
                },
                "generation_limits": {
                    "per_second": settings.RATE_LIMIT_GENERATION_PER_SECOND,
                    "per_minute": settings.RATE_LIMIT_GENERATION_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_GENERATION_PER_HOUR,
                    "per_day": settings.RATE_LIMIT_GENERATION_PER_DAY
                },
                "multipliers": {
                    "authenticated": settings.RATE_LIMIT_AUTHENTICATED_MULTIPLIER,
                    "premium": settings.RATE_LIMIT_PREMIUM_MULTIPLIER,
                    "admin": settings.RATE_LIMIT_ADMIN_MULTIPLIER
                }
            },
            "concurrency": {
                "max_course_generations": settings.MAX_CONCURRENT_COURSE_GENERATIONS,
                "max_chapter_generations": settings.MAX_CONCURRENT_CHAPTER_GENERATIONS
            },
            "debug_mode": settings.DEBUG
        }
    
    @app.post("/debug/test-rate-limit")
    async def test_rate_limit_endpoint():
        """Test endpoint for triggering rate limits (DEBUG mode only)"""
        return {
            "message": "This endpoint can be used to test rate limiting",
            "timestamp": "2024-01-01T00:00:00Z",
            "debug_mode": True
        }

# Custom error handler for rate limiting (HTTP 429)
@app.exception_handler(429)
async def rate_limit_exception_handler(request: Request, exc):
    """Custom error handler for rate limit exceptions"""
    # Get additional context if possible
    error_context = {
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please slow down and try again later.",
        "documentation": "/docs#rate-limiting",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    # Add rate limit information if available in exception
    if hasattr(exc, 'headers') and exc.headers:
        retry_after = exc.headers.get('Retry-After')
        if retry_after:
            error_context["retry_after_seconds"] = int(retry_after)
            error_context["retry_advice"] = f"Try again in {retry_after} seconds"
    
    # Add helpful information for different user types
    user_agent = request.headers.get("user-agent", "")
    if "curl" in user_agent.lower():
        error_context["curl_example"] = f"curl -H 'Authorization: Bearer YOUR_TOKEN' {request.url}"
    
    response = JSONResponse(
        status_code=429,
        content=error_context
    )
    
    # Preserve original headers
    if hasattr(exc, 'headers') and exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value
    
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Course Generation Platform API starting up...")
    
    if settings.RATE_LIMIT_ENABLED:
        logger.info("✅ Rate limiting enabled")
        # Test Redis connection if enabled
        if settings.RATE_LIMIT_REDIS_ENABLED:
            try:
                if advanced_rate_limiter.store.redis_client:
                    advanced_rate_limiter.store.redis_client.ping()
                    logger.info("✅ Redis connection for rate limiting: OK")
                else:
                    logger.warning("⚠️ Redis not available, using memory storage")
            except Exception as e:
                logger.error(f"❌ Redis connection error: {e}")
                logger.info("📝 Falling back to memory storage")
    
    logger.info("🎯 API documentation available at: /docs")
    logger.info("🔍 Health checks available at: /health")
    if settings.DEBUG:
        logger.info("🐛 Debug endpoints available at: /debug/*")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 Course Generation Platform API shutting down...")
    
    # Cleanup rate limiter resources if needed
    if settings.RATE_LIMIT_ENABLED and advanced_rate_limiter.store.redis_client:
        try:
            advanced_rate_limiter.store.redis_client.close()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing Redis connection: {e}")
    
    logger.info("👋 Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Course Generation Platform API...")
    logger.info(f"Rate limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"Debug mode: {'Enabled' if settings.DEBUG else 'Disabled'}")
    
    uvicorn.run(
        "main_with_rate_limiting:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG,
        log_level="info"
    )