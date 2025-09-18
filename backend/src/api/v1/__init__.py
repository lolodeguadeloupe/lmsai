from fastapi import APIRouter
from .courses import router as courses_router
from .generation import router as generation_router
from .export import router as export_router
from .quality import router as quality_router
from .chapters import router as chapters_router
from .quizzes import router as quizzes_router

# Create the main API v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_v1_router.include_router(courses_router)
api_v1_router.include_router(generation_router)
api_v1_router.include_router(export_router)
api_v1_router.include_router(quality_router)
api_v1_router.include_router(chapters_router)
api_v1_router.include_router(quizzes_router)

# Health check endpoint
@api_v1_router.get("/health")
async def health_check():
    """
    Health check endpoint for the API.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Course Generation Platform API"
    }

# API info endpoint
@api_v1_router.get("/info")
async def api_info():
    """
    API information endpoint.
    """
    return {
        "name": "Course Generation Platform API",
        "version": "1.0.0",
        "description": "AI-powered course creation and management platform",
        "endpoints": {
            "courses": "Course management (CRUD operations)",
            "generation": "Course generation status and control",
            "export": "Course export in various formats",
            "quality": "Quality metrics and analysis",
            "chapters": "Chapter content access",
            "quizzes": "Quiz content and attempt handling"
        },
        "documentation": "/docs"
    }
