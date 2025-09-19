"""
Advanced Rate Limiting Middleware for Course Generation Platform

Features:
- Redis-based distributed rate limiting with fallback to memory
- Configurable rate limits per endpoint pattern and user type
- Burst capacity and sustained rate support
- API key and IP-based rate limiting
- Proper HTTP 429 responses with Retry-After headers
- Integration with existing authentication system
- Performance optimized with Lua scripts for atomic operations
"""

import time
import redis
import json
import hashlib
import asyncio
from typing import Dict, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from datetime import datetime, timedelta
import os

from core.config import settings
from middleware.auth import AuthMiddleware

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

class RateLimitType(Enum):
    """Rate limit types for different endpoint categories"""
    STANDARD = "standard"           # Regular API endpoints
    GENERATION = "generation"       # AI course generation endpoints
    RETRIEVAL = "retrieval"        # Data fetching endpoints
    ADMIN = "admin"                # Administrative endpoints
    UPLOAD = "upload"              # File upload endpoints

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules"""
    requests_per_second: int = 10    # Burst capacity
    requests_per_minute: int = 60    # Short-term limit
    requests_per_hour: int = 1000    # Long-term limit
    requests_per_day: int = 10000    # Daily limit
    
    # Different user types can have different limits
    authenticated_multiplier: float = 2.0  # Authenticated users get 2x limits
    premium_multiplier: float = 5.0        # Premium users get 5x limits
    admin_multiplier: float = 10.0         # Admin users get 10x limits

class RateLimitRules:
    """Predefined rate limiting rules for different endpoint types"""
    
    RULES = {
        RateLimitType.STANDARD: RateLimitConfig(
            requests_per_second=10,
            requests_per_minute=100,
            requests_per_hour=2000,
            requests_per_day=20000
        ),
        RateLimitType.GENERATION: RateLimitConfig(
            requests_per_second=2,
            requests_per_minute=10,
            requests_per_hour=50,
            requests_per_day=200
        ),
        RateLimitType.RETRIEVAL: RateLimitConfig(
            requests_per_second=20,
            requests_per_minute=200,
            requests_per_hour=5000,
            requests_per_day=50000
        ),
        RateLimitType.ADMIN: RateLimitConfig(
            requests_per_second=5,
            requests_per_minute=50,
            requests_per_hour=500,
            requests_per_day=2000
        ),
        RateLimitType.UPLOAD: RateLimitConfig(
            requests_per_second=1,
            requests_per_minute=5,
            requests_per_hour=20,
            requests_per_day=100
        )
    }
    
    @classmethod
    def get_config(cls, limit_type: RateLimitType) -> RateLimitConfig:
        """Get rate limit configuration for a given type"""
        return cls.RULES.get(limit_type, cls.RULES[RateLimitType.STANDARD])

class EndpointClassifier:
    """Classifies endpoints to determine appropriate rate limiting rules"""
    
    ENDPOINT_PATTERNS = {
        RateLimitType.GENERATION: [
            r".*\/courses\/?$",                    # POST /courses (course creation)
            r".*\/courses\/.*\/regenerate-.*",     # Chapter regeneration
            r".*\/generation\/.*",                 # All generation endpoints
            r".*\/generate.*",                     # Any generate endpoints
        ],
        RateLimitType.RETRIEVAL: [
            r".*\/courses\/.*\/chapters.*",        # Chapter retrieval
            r".*\/courses\/[^\/]+$",              # GET specific course
            r".*\/courses\?.*",                   # GET courses list
            r".*\/export\/.*",                    # Export endpoints
            r".*\/health.*",                      # Health check endpoints
        ],
        RateLimitType.ADMIN: [
            r".*\/admin\/.*",                     # Admin endpoints
            r".*\/users\/.*\/admin.*",            # User admin endpoints
        ],
        RateLimitType.UPLOAD: [
            r".*\/upload.*",                      # File upload endpoints
            r".*\/files\/.*",                     # File management
        ]
    }
    
    @classmethod
    def classify_endpoint(cls, method: str, path: str) -> RateLimitType:
        """Classify an endpoint to determine its rate limit type"""
        import re
        
        endpoint_key = f"{method}:{path}"
        
        for limit_type, patterns in cls.ENDPOINT_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, endpoint_key, re.IGNORECASE):
                    return limit_type
        
        return RateLimitType.STANDARD

class RateLimitStore:
    """Redis-based rate limit storage with memory fallback"""
    
    def __init__(self):
        self.redis_client = None
        self._memory_store: Dict[str, Dict] = {}
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection with error handling"""
        try:
            redis_url = settings.REDIS_URL
            self.redis_client = redis.from_url(
                redis_url, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Rate limiter connected to Redis successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory fallback: {e}")
            self.redis_client = None
    
    def _lua_sliding_window_script(self) -> str:
        """Lua script for atomic sliding window rate limiting"""
        return """
        local key = KEYS[1]
        local window = tonumber(ARGV[1])
        local limit = tonumber(ARGV[2])
        local current_time = tonumber(ARGV[3])
        
        -- Remove expired entries
        redis.call('ZREMRANGEBYSCORE', key, 0, current_time - window)
        
        -- Count current requests
        local current_count = redis.call('ZCARD', key)
        
        if current_count < limit then
            -- Add current request
            redis.call('ZADD', key, current_time, current_time .. ':' .. math.random())
            redis.call('EXPIRE', key, window)
            return {1, current_count + 1, limit}
        else
            return {0, current_count, limit}
        end
        """
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        window_seconds: int, 
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window algorithm
        Returns: (allowed, current_count, limit)
        """
        current_time = int(time.time())
        
        if self.redis_client:
            try:
                lua_script = self._lua_sliding_window_script()
                result = self.redis_client.eval(
                    lua_script, 
                    1, 
                    identifier, 
                    window_seconds, 
                    limit, 
                    current_time
                )
                return bool(result[0]), result[1], result[2]
            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}")
                # Fallback to memory
                return await self._check_memory_rate_limit(
                    identifier, window_seconds, limit, current_time
                )
        else:
            return await self._check_memory_rate_limit(
                identifier, window_seconds, limit, current_time
            )
    
    async def _check_memory_rate_limit(
        self, 
        identifier: str, 
        window_seconds: int, 
        limit: int, 
        current_time: int
    ) -> Tuple[bool, int, int]:
        """Memory-based rate limiting fallback"""
        if identifier not in self._memory_store:
            self._memory_store[identifier] = {"requests": []}
        
        data = self._memory_store[identifier]
        window_start = current_time - window_seconds
        
        # Remove expired requests
        data["requests"] = [
            req_time for req_time in data["requests"] 
            if req_time > window_start
        ]
        
        current_count = len(data["requests"])
        
        if current_count < limit:
            data["requests"].append(current_time)
            return True, current_count + 1, limit
        else:
            return False, current_count, limit
    
    async def get_rate_limit_info(self, identifier: str) -> Dict:
        """Get current rate limit information for debugging"""
        if self.redis_client:
            try:
                # Get all rate limit keys for this identifier
                pattern = f"{identifier}:*"
                keys = self.redis_client.keys(pattern)
                info = {}
                for key in keys:
                    count = self.redis_client.zcard(key)
                    ttl = self.redis_client.ttl(key)
                    info[key] = {"count": count, "ttl": ttl}
                return info
            except Exception:
                pass
        
        # Memory fallback
        return {identifier: self._memory_store.get(identifier, {})}

class AdvancedRateLimiter:
    """Advanced rate limiting middleware with multiple time windows"""
    
    def __init__(self):
        self.store = RateLimitStore()
        self.auth_middleware = AuthMiddleware()
    
    def _get_user_info(self, request: Request) -> Dict:
        """Extract user information from request"""
        try:
            # Try to get user from authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                # Simplified token decode for user info
                # In production, use proper JWT validation
                import jwt
                try:
                    payload = jwt.decode(
                        token, 
                        settings.SECRET_KEY, 
                        algorithms=["HS256"],
                        options={"verify_exp": False}  # For demo purposes
                    )
                    return {
                        "user_id": payload.get("sub"),
                        "role": payload.get("role", "user"),
                        "is_authenticated": True,
                        "is_premium": payload.get("is_premium", False)
                    }
                except:
                    pass
            
            return {
                "user_id": None,
                "role": "anonymous",
                "is_authenticated": False,
                "is_premium": False
            }
        except Exception:
            return {
                "user_id": None,
                "role": "anonymous", 
                "is_authenticated": False,
                "is_premium": False
            }
    
    def _get_client_identifier(self, request: Request, user_info: Dict) -> str:
        """Generate unique client identifier for rate limiting"""
        if user_info["is_authenticated"] and user_info["user_id"]:
            return f"user:{user_info['user_id']}"
        
        # Fallback to IP-based identification
        client_ip = request.client.host
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Add request signature for additional uniqueness
        user_agent = request.headers.get("user-agent", "")
        signature = hashlib.md5(f"{client_ip}:{user_agent}".encode()).hexdigest()[:8]
        
        return f"ip:{client_ip}:{signature}"
    
    def _apply_user_multipliers(self, config: RateLimitConfig, user_info: Dict) -> RateLimitConfig:
        """Apply user-type multipliers to rate limit configuration"""
        multiplier = 1.0
        
        if user_info["role"] == "admin":
            multiplier = config.admin_multiplier
        elif user_info["is_premium"]:
            multiplier = config.premium_multiplier
        elif user_info["is_authenticated"]:
            multiplier = config.authenticated_multiplier
        
        return RateLimitConfig(
            requests_per_second=int(config.requests_per_second * multiplier),
            requests_per_minute=int(config.requests_per_minute * multiplier),
            requests_per_hour=int(config.requests_per_hour * multiplier),
            requests_per_day=int(config.requests_per_day * multiplier)
        )
    
    async def check_rate_limits(self, request: Request) -> Dict:
        """
        Check all rate limit windows for a request
        Returns rate limit status and headers
        """
        # Get user information
        user_info = self._get_user_info(request)
        client_id = self._get_client_identifier(request, user_info)
        
        # Classify endpoint
        endpoint_type = EndpointClassifier.classify_endpoint(
            request.method, 
            str(request.url.path)
        )
        
        # Get and apply rate limit configuration
        base_config = RateLimitRules.get_config(endpoint_type)
        config = self._apply_user_multipliers(base_config, user_info)
        
        # Check multiple time windows
        time_windows = [
            ("second", 1, config.requests_per_second),
            ("minute", 60, config.requests_per_minute),
            ("hour", 3600, config.requests_per_hour),
            ("day", 86400, config.requests_per_day)
        ]
        
        rate_limit_info = {
            "allowed": True,
            "endpoint_type": endpoint_type.value,
            "user_type": user_info["role"],
            "limits": {},
            "retry_after": 0
        }
        
        # Check each time window
        for window_name, window_seconds, limit in time_windows:
            key = f"{client_id}:{endpoint_type.value}:{window_name}"
            
            allowed, current_count, max_count = await self.store.check_rate_limit(
                key, window_seconds, limit
            )
            
            rate_limit_info["limits"][window_name] = {
                "current": current_count,
                "limit": max_count,
                "remaining": max(0, max_count - current_count),
                "reset_time": int(time.time()) + window_seconds
            }
            
            if not allowed:
                rate_limit_info["allowed"] = False
                rate_limit_info["retry_after"] = max(
                    rate_limit_info["retry_after"], 
                    window_seconds
                )
                rate_limit_info["exceeded_window"] = window_name
                break
        
        return rate_limit_info
    
    def _generate_rate_limit_headers(self, rate_info: Dict) -> Dict[str, str]:
        """Generate HTTP headers for rate limit information"""
        headers = {}
        
        if not rate_info["allowed"]:
            headers["Retry-After"] = str(rate_info["retry_after"])
        
        # Add informational headers
        for window_name, window_info in rate_info["limits"].items():
            prefix = f"X-RateLimit-{window_name.capitalize()}"
            headers[f"{prefix}-Limit"] = str(window_info["limit"])
            headers[f"{prefix}-Remaining"] = str(window_info["remaining"])
            headers[f"{prefix}-Reset"] = str(window_info["reset_time"])
        
        headers["X-RateLimit-Type"] = rate_info["endpoint_type"]
        headers["X-RateLimit-User-Type"] = rate_info["user_type"]
        
        return headers

# Global rate limiter instance
advanced_rate_limiter = AdvancedRateLimiter()

async def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting"""
    rate_info = await advanced_rate_limiter.check_rate_limits(request)
    
    if not rate_info["allowed"]:
        headers = advanced_rate_limiter._generate_rate_limit_headers(rate_info)
        
        error_detail = (
            f"Rate limit exceeded for {rate_info['endpoint_type']} endpoints. "
            f"Limit exceeded in {rate_info.get('exceeded_window', 'unknown')} window. "
            f"Try again in {rate_info['retry_after']} seconds."
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_detail,
            headers=headers
        )
    
    # Add rate limit headers to successful responses
    request.state.rate_limit_headers = advanced_rate_limiter._generate_rate_limit_headers(rate_info)
    return rate_info

# Convenience decorators for different endpoint types
def generation_rate_limit():
    """Rate limiting decorator for generation endpoints"""
    async def dependency(request: Request):
        # Force classification as generation endpoint
        original_path = str(request.url.path)
        request._url = request.url.replace(path="/generation" + original_path)
        return await rate_limit_dependency(request)
    return Depends(dependency)

def admin_rate_limit():
    """Rate limiting decorator for admin endpoints"""
    async def dependency(request: Request):
        # Force classification as admin endpoint
        original_path = str(request.url.path)
        request._url = request.url.replace(path="/admin" + original_path)
        return await rate_limit_dependency(request)
    return Depends(dependency)

# Middleware class for FastAPI middleware stack
class RateLimitMiddleware:
    """Middleware class that can be added to FastAPI middleware stack"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            try:
                # Check rate limits
                rate_info = await advanced_rate_limiter.check_rate_limits(request)
                
                if not rate_info["allowed"]:
                    headers = advanced_rate_limiter._generate_rate_limit_headers(rate_info)
                    
                    # Create error response
                    response_body = json.dumps({
                        "detail": f"Rate limit exceeded for {rate_info['endpoint_type']} endpoints",
                        "rate_limit_info": rate_info
                    }).encode()
                    
                    await send({
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [
                            [b"content-type", b"application/json"],
                            *[[k.encode(), v.encode()] for k, v in headers.items()]
                        ]
                    })
                    await send({
                        "type": "http.response.body", 
                        "body": response_body
                    })
                    return
                
                # Store headers for response
                scope["rate_limit_headers"] = advanced_rate_limiter._generate_rate_limit_headers(rate_info)
                
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Continue without rate limiting on error
        
        await self.app(scope, receive, send)

# Health check endpoint for rate limiter
async def rate_limiter_health() -> Dict:
    """Health check for rate limiting system"""
    try:
        # Test Redis connection if available
        if advanced_rate_limiter.store.redis_client:
            advanced_rate_limiter.store.redis_client.ping()
            storage_status = "redis_connected"
        else:
            storage_status = "memory_fallback"
        
        return {
            "status": "healthy",
            "storage": storage_status,
            "rate_limiter": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "rate_limiter": "error",
            "timestamp": datetime.utcnow().isoformat()
        }

# Export main components
__all__ = [
    "RateLimitType",
    "RateLimitConfig", 
    "RateLimitRules",
    "AdvancedRateLimiter",
    "advanced_rate_limiter",
    "rate_limit_dependency",
    "generation_rate_limit",
    "admin_rate_limit",
    "RateLimitMiddleware",
    "rate_limiter_health"
]