"""
Security API endpoints for the Course Generation Platform.

Provides endpoints for security configuration, health checks,
and security monitoring.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from middleware.security import get_security_info, validate_security_config

# Create router
router = APIRouter(prefix="/security", tags=["security"])


@router.get("/info")
async def security_info() -> Dict[str, Any]:
    """
    Get current security configuration information.
    
    Returns information about:
    - Environment type
    - CORS configuration 
    - Security headers status
    - CSP policy status
    
    Note: Sensitive details are hidden in production mode.
    """
    try:
        info = get_security_info()
        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security info: {str(e)}"
        )


@router.get("/validate")
async def security_validation() -> Dict[str, Any]:
    """
    Validate current security configuration.
    
    Checks for:
    - Production readiness
    - Common security misconfigurations
    - Recommendations for improvement
    
    Returns a security score and list of issues/recommendations.
    """
    try:
        validation = validate_security_config()
        
        # Determine response status based on security score
        if validation["security_score"] >= 80:
            response_status = "good"
        elif validation["security_score"] >= 60:
            response_status = "warning"
        else:
            response_status = "critical"
        
        return {
            "status": response_status,
            "security_score": validation["security_score"],
            "environment": validation["environment"],
            "issues": validation["issues"],
            "recommendations": validation["recommendations"],
            "timestamp": None  # Could add timestamp if needed
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate security config: {str(e)}"
        )


@router.get("/headers")
async def security_headers_test() -> JSONResponse:
    """
    Test endpoint to verify security headers are properly applied.
    
    This endpoint returns a simple response that allows clients
    to inspect the security headers being set by the middleware.
    """
    return JSONResponse(
        content={
            "message": "Security headers test endpoint",
            "note": "Check response headers to verify security middleware is working",
            "headers_to_check": [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Referrer-Policy",
                "Content-Security-Policy",
                "Permissions-Policy",
                "Strict-Transport-Security",  # Only in HTTPS production
                "Cache-Control"
            ]
        }
    )


@router.get("/cors-test")
async def cors_test() -> Dict[str, Any]:
    """
    Test endpoint for CORS configuration verification.
    
    This endpoint can be used to test CORS from different origins
    to verify the configuration is working correctly.
    """
    return {
        "message": "CORS test endpoint",
        "note": "Use this endpoint to test cross-origin requests",
        "cors_info": {
            "methods_allowed": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "credentials_supported": True,
            "max_age": "86400 seconds (24 hours)"
        }
    }