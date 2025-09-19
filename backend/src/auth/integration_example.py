"""
Example integration of API key authentication with existing FastAPI routes.

This file demonstrates how to integrate the API key authentication system
with the existing course platform API endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database.session import get_db
from .api_key_auth import (
    APIKeyScope,
    require_api_key,
    require_permission,
    validate_api_key,
)
from .middleware import APIKeyMiddleware, get_current_api_key
from .router import router as auth_router

# Example of how to modify existing FastAPI app to include API key auth
def setup_api_key_authentication(app: FastAPI):
    """
    Setup API key authentication for a FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    
    # 1. Add API key middleware (automatic authentication)
    middleware = APIKeyMiddleware(
        protected_paths=["/api/v1/"]  # Protect all v1 API endpoints
    )
    app.middleware("http")(middleware)
    
    # 2. Include authentication router for API key management
    app.include_router(auth_router)
    
    print("✅ API key authentication system enabled")


# Example protected endpoints using different permission levels
def create_protected_endpoints(app: FastAPI):
    """
    Example of how to add protection to course platform endpoints.
    """
    
    # Public endpoint (no authentication required)
    @app.get("/health")
    async def health_check():
        """Public health check endpoint."""
        return {"status": "healthy"}
    
    # Basic API key required (any valid key)
    @app.get("/api/v1/courses")
    async def list_courses(
        api_key = Depends(require_api_key),
        db: Session = Depends(get_db)
    ):
        """
        List courses - requires any valid API key.
        """
        return {
            "courses": [],
            "api_key_info": {
                "name": api_key.name,
                "permission_level": api_key.permission_level,
            }
        }
    
    # Specific permission required
    @app.post("/api/v1/courses")
    async def create_course(
        course_data: dict,
        api_key = Depends(require_permission(APIKeyScope.COURSE_WRITE)),
        db: Session = Depends(get_db)
    ):
        """
        Create course - requires course write permission.
        """
        return {
            "message": "Course created",
            "course_id": "generated-id",
            "created_by_api_key": api_key.name,
        }
    
    # Admin permission required
    @app.delete("/api/v1/courses/{course_id}")
    async def delete_course(
        course_id: str,
        api_key = Depends(require_permission(APIKeyScope.COURSE_DELETE)),
        db: Session = Depends(get_db)
    ):
        """
        Delete course - requires course delete permission.
        """
        return {
            "message": f"Course {course_id} deleted",
            "deleted_by_api_key": api_key.name,
        }
    
    # Generation endpoint with rate limiting consideration
    @app.post("/api/v1/generation/start")
    async def start_generation(
        generation_request: dict,
        request: Request,
        api_key = Depends(require_permission(APIKeyScope.GENERATION_CREATE)),
        db: Session = Depends(get_db)
    ):
        """
        Start course generation - requires generation permission.
        
        This endpoint is typically rate-limited due to resource intensity.
        """
        # Get API key from middleware state
        current_api_key = get_current_api_key(request)
        
        # Check if this is a high-privilege key for higher limits
        if current_api_key and current_api_key.permission_level in ["power_user", "admin"]:
            # Allow higher rate limits for privileged users
            pass
        
        return {
            "message": "Generation started",
            "task_id": "generated-task-id",
            "api_key_limits": {
                "per_hour": current_api_key.rate_limit_per_hour if current_api_key else None,
                "per_day": current_api_key.rate_limit_per_day if current_api_key else None,
            }
        }
    
    # Optional authentication (API key not required but used if present)
    @app.get("/api/v1/public/courses")
    async def list_public_courses(
        request: Request,
        db: Session = Depends(get_db)
    ):
        """
        List public courses - API key optional but provides enhanced access.
        """
        api_key = get_current_api_key(request)
        
        if api_key:
            # Enhanced response for authenticated users
            return {
                "courses": ["course1", "course2", "course3"],
                "total": 3,
                "authenticated_as": api_key.name,
                "enhanced_data": True,
            }
        else:
            # Basic response for unauthenticated users
            return {
                "courses": ["course1", "course2"],
                "total": 2,
                "enhanced_data": False,
            }


# Example of custom permission checking in route handlers
def create_advanced_endpoints(app: FastAPI):
    """
    Examples of advanced permission checking patterns.
    """
    
    @app.get("/api/v1/courses/{course_id}/analytics")
    async def get_course_analytics(
        course_id: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
        """
        Get course analytics with dynamic permission checking.
        """
        from .middleware import check_api_key_scope, require_api_key_scope
        
        # Basic read permission required
        require_api_key_scope(request, APIKeyScope.COURSE_READ.value)
        
        # Check for enhanced permissions for detailed analytics
        has_admin_access = check_api_key_scope(request, APIKeyScope.ADMIN_READ.value)
        
        if has_admin_access:
            return {
                "course_id": course_id,
                "basic_analytics": {"views": 100, "completions": 80},
                "detailed_analytics": {
                    "user_behavior": {},
                    "performance_metrics": {},
                    "revenue_data": {},
                },
            }
        else:
            return {
                "course_id": course_id,
                "basic_analytics": {"views": 100, "completions": 80},
            }
    
    @app.put("/api/v1/courses/{course_id}/settings")
    async def update_course_settings(
        course_id: str,
        settings: dict,
        request: Request,
        api_key = Depends(require_permission(APIKeyScope.COURSE_WRITE)),
        db: Session = Depends(get_db)
    ):
        """
        Update course settings with ownership validation.
        """
        from .middleware import check_api_key_scope
        
        # Additional check for sensitive settings
        if "pricing" in settings or "access_control" in settings:
            if not check_api_key_scope(request, APIKeyScope.ADMIN_WRITE.value):
                raise HTTPException(
                    status_code=403,
                    detail="Admin permission required to modify pricing or access control"
                )
        
        return {
            "message": f"Course {course_id} settings updated",
            "updated_fields": list(settings.keys()),
            "updated_by": api_key.name,
        }


# Example of integrating with existing middleware
def integrate_with_existing_auth(app: FastAPI):
    """
    Example of integrating API key auth with existing JWT auth system.
    """
    
    @app.get("/api/v1/user/courses")
    async def get_user_courses(
        request: Request,
        db: Session = Depends(get_db)
    ):
        """
        Get user courses - supports both JWT and API key authentication.
        """
        # Check for API key first
        api_key = get_current_api_key(request)
        
        if api_key:
            # API key authentication
            return {
                "courses": ["api-course-1", "api-course-2"],
                "auth_method": "api_key",
                "api_key_name": api_key.name,
            }
        
        # Fall back to JWT authentication (existing middleware)
        try:
            from ..middleware.auth import AuthMiddleware
            # Use existing JWT auth logic
            user = AuthMiddleware.get_current_user(request, db)
            return {
                "courses": ["user-course-1", "user-course-2"],
                "auth_method": "jwt",
                "user_id": user["id"],
            }
        except HTTPException:
            raise HTTPException(
                status_code=401,
                detail="Authentication required (JWT token or API key)"
            )


# Complete example application setup
def create_example_app() -> FastAPI:
    """
    Create a complete example FastAPI application with API key authentication.
    """
    app = FastAPI(
        title="Course Platform API with API Key Authentication",
        description="Example integration of API key authentication system",
        version="1.0.0"
    )
    
    # Setup authentication
    setup_api_key_authentication(app)
    
    # Add protected endpoints
    create_protected_endpoints(app)
    create_advanced_endpoints(app)
    integrate_with_existing_auth(app)
    
    return app


if __name__ == "__main__":
    # Example of how to run the application
    import uvicorn
    
    app = create_example_app()
    
    print("🚀 Starting example application with API key authentication...")
    print("📖 API Documentation available at: http://localhost:8000/docs")
    print("🔑 API Key Management available at: http://localhost:8000/api/v1/auth/")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)