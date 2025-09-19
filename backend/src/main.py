"""
FastAPI main application entry point.
Course Generation Platform API with full endpoint implementation.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import exception handling system
from core.exceptions import register_exception_handlers

try:
    from tasks.utils import get_task_queue_status
except ImportError:
    # Fallback for development
    def get_task_queue_status():
        return {"queue_health": "healthy", "note": "Task queue not configured"}

try:
    from api import api_v1_router
    print("✅ API v1 router imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import API router: {e}")
    # Fallback if API router not available
    from fastapi import APIRouter
    api_v1_router = APIRouter(prefix="/api/v1")
    
    @api_v1_router.get("/health")
    async def fallback_health():
        return {"status": "fallback", "message": "API router not fully loaded"}

# Create FastAPI application
app = FastAPI(
    title="Course Generation Platform API",
    description="AI-powered course creation and management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register exception handlers
register_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_v1_router)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Course Generation Platform API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "course-platform-api"}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
