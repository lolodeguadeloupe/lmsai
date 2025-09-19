"""
Security middleware for FastAPI application.

Implements comprehensive security measures including:
- CORS configuration with environment-based origins
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Request validation and security checks
- OWASP security best practices

Security Features:
- Environment-specific CORS origins
- Content Security Policy (CSP)
- Strict Transport Security (HSTS)
- Clickjacking protection (X-Frame-Options)
- MIME type sniffing protection (X-Content-Type-Options)
- XSS protection (X-XSS-Protection)
- Referrer policy control
- Feature policy restrictions
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.config import settings

# Configure logger
logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration with environment-based settings."""
    
    def __init__(self):
        # Environment detection
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # CORS Origins configuration
        self.cors_origins = self._get_cors_origins()
        
        # Security headers configuration
        self.security_headers = self._get_security_headers()
        
        # CSP configuration
        self.csp_policy = self._get_csp_policy()
        
        # Trusted hosts
        self.trusted_hosts = self._get_trusted_hosts()
    
    def _get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment."""
        cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS", "")
        
        if cors_origins_env:
            try:
                # Try to parse as JSON array
                origins = json.loads(cors_origins_env)
                if isinstance(origins, list):
                    return origins
            except json.JSONDecodeError:
                # Fall back to comma-separated values
                return [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        
        # Default origins based on environment
        if self.environment == "production":
            # Production: Only specific domains
            return [
                "https://yourdomain.com",
                "https://app.yourdomain.com",
                "https://admin.yourdomain.com"
            ]
        elif self.environment == "staging":
            # Staging: Include staging domains
            return [
                "https://staging.yourdomain.com",
                "https://staging-app.yourdomain.com",
                "http://localhost:3000",
                "http://localhost:8080"
            ]
        else:
            # Development: Allow common local development ports
            return [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://localhost:8080",
                "http://localhost:8081",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ]
    
    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers based on environment."""
        headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Clickjacking protection
            "X-Frame-Options": "DENY",
            
            # XSS protection (legacy, but still useful)
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Feature policy / Permissions policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "midi=(), "
                "sync-xhr=(), "
                "accelerometer=(), "
                "gyroscope=(), "
                "magnetometer=(), "
                "payment=(), "
                "usb=()"
            ),
            
            # Prevent caching of sensitive content
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        
        # HSTS (only for HTTPS)
        if self.environment == "production":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return headers
    
    def _get_csp_policy(self) -> str:
        """Get Content Security Policy based on environment."""
        if self.environment == "production":
            # Strict CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.yourdomain.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests"
            )
        elif self.environment == "staging":
            # Relaxed CSP for staging
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "font-src 'self' https: data:; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'"
            )
        else:
            # Development CSP (more permissive)
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http: https:; "
                "style-src 'self' 'unsafe-inline' http: https:; "
                "font-src 'self' http: https: data:; "
                "img-src 'self' data: http: https:; "
                "connect-src 'self' http: https: ws: wss:; "
                "frame-ancestors 'self'; "
                "base-uri 'self'"
            )
    
    def _get_trusted_hosts(self) -> List[str]:
        """Get trusted hosts based on environment."""
        if self.environment == "production":
            return [
                "yourdomain.com",
                "api.yourdomain.com",
                "app.yourdomain.com"
            ]
        elif self.environment == "staging":
            return [
                "staging.yourdomain.com",
                "staging-api.yourdomain.com",
                "localhost"
            ]
        else:
            # Development: Allow localhost and common development hosts
            return ["localhost", "127.0.0.1", "0.0.0.0"]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.config.security_headers.items():
            response.headers[header] = value
        
        # Add CSP header
        if self.config.csp_policy:
            response.headers["Content-Security-Policy"] = self.config.csp_policy
        
        return response


class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and security checks."""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE", "10485760"))  # 10MB
        self.blocked_user_agents = [
            "curl",  # Block basic curl requests in production
            "wget",
            "python-requests",
        ] if config.environment == "production" else []
    
    async def dispatch(self, request: Request, call_next):
        """Validate request for security issues."""
        try:
            # Check request size
            if await self._check_request_size(request):
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request entity too large"}
                )
            
            # Check for malicious patterns in production
            if self.config.environment == "production":
                if await self._check_malicious_patterns(request):
                    logger.warning(f"Blocked suspicious request from {request.client.host}")
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Request blocked"}
                    )
            
            # Check user agent in production
            if self.config.environment == "production":
                if await self._check_user_agent(request):
                    return JSONResponse(
                        status_code=403,
                        content={"error": "User agent not allowed"}
                    )
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    async def _check_request_size(self, request: Request) -> bool:
        """Check if request size exceeds limit."""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return True
        return False
    
    async def _check_malicious_patterns(self, request: Request) -> bool:
        """Check for common malicious patterns."""
        url = str(request.url)
        
        # Common attack patterns
        malicious_patterns = [
            "../",  # Path traversal
            "..\\",  # Windows path traversal
            "<script",  # XSS
            "javascript:",  # JavaScript injection
            "data:text/html",  # Data URI XSS
            "union select",  # SQL injection
            "drop table",  # SQL injection
            "insert into",  # SQL injection
            "delete from",  # SQL injection
        ]
        
        url_lower = url.lower()
        for pattern in malicious_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    async def _check_user_agent(self, request: Request) -> bool:
        """Check if user agent is blocked."""
        user_agent = request.headers.get("user-agent", "").lower()
        
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent in user_agent:
                return True
        
        return False


def setup_security_middleware(app: FastAPI) -> None:
    """
    Set up comprehensive security middleware for FastAPI application.
    
    This function should be called during application initialization to add
    all security-related middleware in the correct order.
    
    Args:
        app: FastAPI application instance
    """
    config = SecurityConfig()
    
    # Log security configuration
    logger.info(f"Setting up security middleware for environment: {config.environment}")
    logger.info(f"CORS origins: {config.cors_origins}")
    logger.info(f"Trusted hosts: {config.trusted_hosts}")
    
    # 1. Trusted Host middleware (first for host validation)
    if config.trusted_hosts and config.environment != "development":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config.trusted_hosts
        )
        logger.info("Added TrustedHostMiddleware")
    
    # 2. Security validation middleware
    app.add_middleware(SecurityValidationMiddleware, config=config)
    logger.info("Added SecurityValidationMiddleware")
    
    # 3. Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware, config=config)
    logger.info("Added SecurityHeadersMiddleware")
    
    # 4. CORS middleware (last to ensure proper handling)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        expose_headers=[
            "X-Total-Count",
            "X-Page-Count",
            "X-Per-Page",
            "X-Current-Page",
        ],
        max_age=86400,  # 24 hours
    )
    logger.info("Added CORSMiddleware")


def get_security_info() -> Dict[str, Any]:
    """
    Get current security configuration information.
    
    Returns:
        Dictionary containing security configuration details
    """
    config = SecurityConfig()
    
    return {
        "environment": config.environment,
        "cors_origins_count": len(config.cors_origins),
        "cors_origins": config.cors_origins if config.debug else "hidden",
        "trusted_hosts": config.trusted_hosts if config.debug else "hidden",
        "security_headers_count": len(config.security_headers),
        "csp_enabled": bool(config.csp_policy),
        "debug_mode": config.debug,
    }


def validate_security_config() -> Dict[str, Any]:
    """
    Validate security configuration and return recommendations.
    
    Returns:
        Dictionary containing validation results and recommendations
    """
    config = SecurityConfig()
    issues = []
    recommendations = []
    
    # Check for production readiness
    if config.environment == "production":
        if config.debug:
            issues.append("Debug mode is enabled in production")
        
        if "*" in config.cors_origins:
            issues.append("Wildcard CORS origins in production")
        
        if not any("https://" in origin for origin in config.cors_origins):
            issues.append("No HTTPS origins configured for production")
    
    # Check for insecure configurations
    if "http://localhost" in config.cors_origins and config.environment == "production":
        issues.append("Localhost origins configured in production")
    
    # Recommendations
    if config.environment != "production":
        recommendations.append("Review security settings before production deployment")
    
    if not os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY") == "your-secret-key-here":
        issues.append("Default or missing SECRET_KEY")
    
    return {
        "environment": config.environment,
        "issues": issues,
        "recommendations": recommendations,
        "security_score": max(0, 100 - (len(issues) * 20)),
    }