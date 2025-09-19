# Advanced Rate Limiting Guide

This guide explains how to use the advanced rate limiting middleware in the Course Generation Platform API.

## Overview

The rate limiting system provides:

- **Multi-tier rate limiting**: Different limits for different types of endpoints
- **User-based limits**: Higher limits for authenticated, premium, and admin users
- **Redis-based storage**: Distributed rate limiting with memory fallback
- **Sliding window algorithm**: More accurate than fixed windows
- **Comprehensive monitoring**: Detailed headers and health checks

## Quick Start

### 1. Basic Integration

Add rate limiting to your FastAPI application:

```python
from fastapi import FastAPI
from middleware.rate_limiting import RateLimitMiddleware

app = FastAPI()

# Add rate limiting middleware (recommended)
app.add_middleware(RateLimitMiddleware)
```

### 2. Dependency-based Rate Limiting

For more control, use rate limiting as a dependency:

```python
from fastapi import Depends
from middleware.rate_limiting import rate_limit_dependency

@app.get("/api/v1/courses")
async def list_courses(rate_info = Depends(rate_limit_dependency)):
    return {"courses": []}
```

### 3. Endpoint-specific Rate Limiting

Use specialized rate limiting for different endpoint types:

```python
from middleware.rate_limiting import generation_rate_limit, admin_rate_limit

# Generation endpoints (AI operations)
@app.post("/api/v1/courses")
async def create_course(rate_info = Depends(generation_rate_limit())):
    return {"message": "Course creation started"}

# Admin endpoints
@app.get("/api/v1/admin/stats")
async def admin_stats(rate_info = Depends(admin_rate_limit())):
    return {"stats": {}}
```

## Rate Limit Types

### Standard API Endpoints
- **Per second**: 10 requests
- **Per minute**: 100 requests  
- **Per hour**: 2,000 requests
- **Per day**: 20,000 requests

### Generation Endpoints (AI Operations)
- **Per second**: 2 requests
- **Per minute**: 10 requests
- **Per hour**: 50 requests
- **Per day**: 200 requests

### Retrieval Endpoints (Data Fetching)
- **Per second**: 20 requests
- **Per minute**: 200 requests
- **Per hour**: 5,000 requests
- **Per day**: 50,000 requests

### Admin Endpoints
- **Per second**: 5 requests
- **Per minute**: 50 requests
- **Per hour**: 500 requests
- **Per day**: 2,000 requests

### Upload Endpoints
- **Per second**: 1 request
- **Per minute**: 5 requests
- **Per hour**: 20 requests
- **Per day**: 100 requests

## User Type Multipliers

### Anonymous Users
Base rate limits apply (1x multiplier)

### Authenticated Users
2x multiplier on all limits

### Premium Users
5x multiplier on all limits

### Admin Users
10x multiplier on all limits

## Endpoint Classification

The system automatically classifies endpoints based on URL patterns:

### Generation Endpoints
- `POST /api/v1/courses` (course creation)
- `POST /api/v1/courses/{id}/regenerate-*` (regeneration)
- `POST /api/v1/generation/*` (generation operations)

### Retrieval Endpoints
- `GET /api/v1/courses/*` (course data)
- `GET /api/v1/export/*` (exports)
- `GET /health*` (health checks)

### Admin Endpoints
- `*/admin/*` (admin operations)

### Upload Endpoints
- `*/upload*` (file uploads)
- `*/files/*` (file management)

## Configuration

### Environment Variables

```env
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_ENABLED=true

# Redis connection
REDIS_URL=redis://localhost:6379

# Custom rate limits (optional)
RATE_LIMIT_GENERATION_PER_MINUTE=10
RATE_LIMIT_STANDARD_PER_HOUR=2000

# User multipliers (optional)
RATE_LIMIT_AUTHENTICATED_MULTIPLIER=2.0
RATE_LIMIT_PREMIUM_MULTIPLIER=5.0
RATE_LIMIT_ADMIN_MULTIPLIER=10.0
```

### Programmatic Configuration

```python
from middleware.rate_limiting import RateLimitConfig, RateLimitRules, RateLimitType

# Custom rate limit configuration
custom_config = RateLimitConfig(
    requests_per_second=5,
    requests_per_minute=50,
    requests_per_hour=500,
    requests_per_day=5000
)

# Override default rules
RateLimitRules.RULES[RateLimitType.GENERATION] = custom_config
```

## Rate Limit Headers

The system returns informative headers with each response:

```http
X-RateLimit-Second-Limit: 10
X-RateLimit-Second-Remaining: 9
X-RateLimit-Second-Reset: 1640995200
X-RateLimit-Minute-Limit: 100
X-RateLimit-Minute-Remaining: 99
X-RateLimit-Minute-Reset: 1640995260
X-RateLimit-Type: generation
X-RateLimit-User-Type: authenticated
```

## Error Responses

When rate limits are exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{
  "detail": "Rate limit exceeded for generation endpoints. Limit exceeded in minute window. Try again in 60 seconds.",
  "rate_limit_info": {
    "endpoint_type": "generation",
    "user_type": "authenticated",
    "exceeded_window": "minute",
    "retry_after": 60
  }
}
```

## Health Checks

Monitor rate limiting system health:

```bash
# Check rate limiter health
curl http://localhost:8000/health/rate-limiter

# Response
{
  "status": "healthy",
  "storage": "redis_connected",
  "rate_limiter": "operational",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## Advanced Usage

### Custom Middleware

```python
from middleware.rate_limiting import AdvancedRateLimiter

class CustomRateLimitMiddleware:
    def __init__(self, app):
        self.app = app
        self.rate_limiter = AdvancedRateLimiter()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Custom logic here
            rate_info = await self.rate_limiter.check_rate_limits(request)
            
            if not rate_info["allowed"]:
                # Custom error handling
                pass
        
        await self.app(scope, receive, send)
```

### Manual Rate Checking

```python
from middleware.rate_limiting import advanced_rate_limiter

async def custom_endpoint(request: Request):
    # Manual rate limit check
    rate_info = await advanced_rate_limiter.check_rate_limits(request)
    
    if not rate_info["allowed"]:
        # Handle rate limit exceeded
        raise HTTPException(status_code=429, detail="Custom rate limit message")
    
    # Continue with endpoint logic
    return {"data": "success"}
```

### Rate Limit Bypass

```python
async def bypass_rate_limit(request: Request):
    # Check if user should bypass rate limits
    user_info = advanced_rate_limiter._get_user_info(request)
    
    if user_info["role"] == "system":
        # Skip rate limiting for system users
        return {"bypassed": True}
    
    # Apply normal rate limiting
    return await rate_limit_dependency(request)
```

## Performance Considerations

### Redis Optimization

```python
# Configure Redis for optimal performance
redis_settings = {
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "health_check_interval": 30,
    "max_connections": 100
}
```

### Memory Fallback

When Redis is unavailable, the system automatically falls back to in-memory storage:

- Single-process applications: Works normally
- Multi-process applications: Each process has separate counters
- Distributed deployments: Rate limits are per-instance

### Lua Scripts

The system uses Lua scripts for atomic Redis operations:

```lua
-- Sliding window rate limiting
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
```

## Testing

### Unit Tests

```bash
# Run all rate limiting tests
python test_rate_limiting.py

# Run specific test classes
pytest test_rate_limiting.py::TestEndpointClassifier -v
pytest test_rate_limiting.py::TestRateLimitStore -v
```

### Manual Testing

```bash
# Test rate limiting with curl
for i in {1..20}; do
  curl -H "Authorization: Bearer your-token" \
       -w "Status: %{http_code}, Time: %{time_total}s\n" \
       http://localhost:8000/api/v1/courses
  sleep 0.1
done
```

### Load Testing

```python
import asyncio
import aiohttp

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.get('http://localhost:8000/api/v1/courses')
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        status_codes = [resp.status for resp in responses]
        print(f"Status codes: {set(status_codes)}")
        print(f"Rate limited: {status_codes.count(429)}")

# Run load test
asyncio.run(load_test())
```

## Troubleshooting

### Common Issues

1. **Rate limits too strict**: Adjust configuration values
2. **Redis connection issues**: Check Redis availability and network
3. **Memory usage high**: Enable Redis or tune cleanup intervals
4. **Inconsistent limits**: Ensure Redis is used for distributed deployments

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger("middleware.rate_limiting").setLevel(logging.DEBUG)

# View rate limit information
@app.get("/debug/rate-limit")
async def debug_rate_limit(request: Request):
    user_info = advanced_rate_limiter._get_user_info(request)
    client_id = advanced_rate_limiter._get_client_identifier(request, user_info)
    rate_info = await advanced_rate_limiter.store.get_rate_limit_info(client_id)
    
    return {
        "client_id": client_id,
        "user_info": user_info,
        "rate_data": rate_info
    }
```

### Monitoring

```python
# Add custom metrics
from prometheus_client import Counter, Histogram

rate_limit_exceeded = Counter('rate_limit_exceeded_total', 'Rate limit exceeded', ['endpoint_type'])
rate_limit_latency = Histogram('rate_limit_check_duration_seconds', 'Rate limit check duration')

# Use in middleware
with rate_limit_latency.time():
    rate_info = await rate_limiter.check_rate_limits(request)

if not rate_info["allowed"]:
    rate_limit_exceeded.labels(endpoint_type=rate_info["endpoint_type"]).inc()
```

## Best Practices

1. **Use Redis for production**: Ensures consistent limits across instances
2. **Monitor rate limit headers**: Help users understand their usage
3. **Implement graceful degradation**: Continue serving when rate limiter fails
4. **Log rate limit events**: Track usage patterns and potential abuse
5. **Test thoroughly**: Verify rate limits work as expected under load
6. **Document limits**: Make rate limits clear to API consumers
7. **Provide feedback**: Help users understand why they're rate limited
8. **Consider business logic**: Rate limits should align with business requirements