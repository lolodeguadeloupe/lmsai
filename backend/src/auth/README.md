# API Key Authentication System

A comprehensive API key authentication system for the Course Platform API, providing secure access control, rate limiting, usage tracking, and permission management.

## 🔐 Features

- **Secure API Key Generation**: Cryptographically secure keys with SHA-256 hashing
- **Permission-Based Access Control**: Granular permissions with predefined roles
- **Rate Limiting**: Per-hour and per-day request limits with automatic enforcement
- **Usage Tracking**: Detailed logging and analytics for all API requests
- **Key Management**: Full lifecycle management including creation, revocation, and monitoring
- **Database Integration**: PostgreSQL-backed storage with optimized queries
- **FastAPI Integration**: Native FastAPI dependencies and middleware support

## 🚀 Quick Start

### 1. Database Setup

First, initialize the API key tables:

```python
from auth.migrations import initialize_api_key_system

# Create tables and indexes
initialize_api_key_system()
```

### 2. Create Your First API Key

```python
from auth.api_key_auth import create_api_key, APIKeyPermission
from database.session import get_db_session

with get_db_session() as db:
    response = create_api_key(
        name="My First API Key",
        permission_level=APIKeyPermission.CONTENT_CREATOR,
        db=db,
        description="API key for course creation",
        expires_at=None,  # No expiration
        rate_limit_per_hour=1000,
        rate_limit_per_day=10000,
    )
    
    print(f"API Key: {response.key}")
    print(f"Key ID: {response.id}")
```

**⚠️ Important**: Save the API key immediately! It's only shown once during creation.

### 3. Protect Your Endpoints

```python
from fastapi import FastAPI, Depends
from auth.api_key_auth import require_api_key, require_permission, APIKeyScope

app = FastAPI()

# Require any valid API key
@app.get("/api/v1/courses")
async def get_courses(api_key = Depends(require_api_key)):
    return {"courses": []}

# Require specific permission
@app.post("/api/v1/courses")
async def create_course(api_key = Depends(require_permission(APIKeyScope.COURSE_WRITE))):
    return {"message": "Course created"}

# Require admin permission
@app.delete("/api/v1/courses/{course_id}")
async def delete_course(course_id: str, api_key = Depends(require_permission(APIKeyScope.COURSE_DELETE))):
    return {"message": "Course deleted"}
```

### 4. Use API Keys

Include the API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer ck_your_api_key_here" \
     https://your-api.com/api/v1/courses
```

## 📊 Permission Levels

### Read Only
- View courses, chapters, quizzes
- Read generation status
- Basic API access

**Scopes**: `course:read`, `chapter:read`, `quiz:read`, `generation:read`

### Content Creator  
- All read permissions
- Create and edit courses, chapters, quizzes
- Generate content
- Export courses

**Scopes**: Read permissions + `course:write`, `chapter:write`, `quiz:write`, `generation:create`, `export:*`, `quality:check`

### Power User
- All content creator permissions
- Delete courses, chapters, quizzes
- Cancel generation tasks
- Access quality reports

**Scopes**: Content creator permissions + `*:delete`, `generation:cancel`, `quality:report`

### Admin
- All permissions
- Manage API keys
- Access admin endpoints

**Scopes**: All available scopes

## 🛠️ Management Commands

Use the CLI for easy API key management:

```bash
# Create a new API key
python -m auth.management create \
  --name "Production API Key" \
  --permission content_creator \
  --description "Main production key" \
  --expires-in-days 365

# List all API keys
python -m auth.management list

# Get detailed information
python -m auth.management details <api_key_id>

# Revoke an API key
python -m auth.management revoke <api_key_id> --reason "Security rotation"

# View usage statistics
python -m auth.management stats --days 30
```

## 🔧 Configuration

### Rate Limiting

Default rate limits can be customized per API key:

```python
# Conservative limits for external partners
api_key_data = APIKeyCreate(
    name="Partner API Key",
    permission_level=APIKeyPermission.READ_ONLY,
    rate_limit_per_hour=100,
    rate_limit_per_day=1000,
)

# Higher limits for internal services
api_key_data = APIKeyCreate(
    name="Internal Service Key",
    permission_level=APIKeyPermission.POWER_USER,
    rate_limit_per_hour=5000,
    rate_limit_per_day=50000,
)
```

### Security Features

#### IP Restrictions
```python
api_key_data = APIKeyCreate(
    name="Office Network Key",
    permission_level=APIKeyPermission.CONTENT_CREATOR,
    allowed_ips=["192.168.1.0/24", "10.0.0.1"],
)
```

#### User Agent Patterns
```python
api_key_data = APIKeyCreate(
    name="Mobile App Key",
    permission_level=APIKeyPermission.READ_ONLY,
    user_agent_patterns=["MobileApp/1.*", "MobileApp/2.*"],
)
```

## 📈 Monitoring and Analytics

### Usage Statistics

Get comprehensive usage analytics:

```python
from auth.management import APIKeyManager

with get_db_session() as db:
    manager = APIKeyManager(db)
    stats = manager.get_usage_statistics(days=30)
    
    print(f"Total requests: {stats['total_requests']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Active API keys: {stats['active_api_keys']}")
```

### Individual Key Monitoring

```python
details = manager.get_api_key_details(api_key_id)

print(f"Total requests: {details['usage_stats']['total_requests']}")
print(f"Failed requests: {details['usage_stats']['failed_requests']}")
print(f"Success rate: {details['usage_stats']['success_rate']:.1%}")

# Recent activity
for usage in details['recent_usage']:
    print(f"{usage['timestamp']}: {usage['method']} {usage['endpoint']} - {usage['status_code']}")
```

## 🔄 Middleware Integration

### Automatic Authentication

Add middleware for automatic API key validation:

```python
from fastapi import FastAPI
from auth.middleware import create_api_key_middleware

app = FastAPI()

# Add API key middleware
middleware = create_api_key_middleware(
    protected_paths=["/api/v1/", "/admin/"]
)
app.middleware("http")(middleware)
```

### Manual Validation

For more control, use dependencies:

```python
from fastapi import Request, Depends
from auth.middleware import get_current_api_key, require_api_key_scope

@app.get("/api/v1/courses")
async def get_courses(request: Request):
    api_key = get_current_api_key(request)
    if api_key:
        print(f"Request from API key: {api_key.name}")
    
    # Check specific permission
    require_api_key_scope(request, "course:read")
    
    return {"courses": []}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest auth/tests.py -v

# Run specific test categories
pytest auth/tests.py::TestAPIKeyCreation -v
pytest auth/tests.py::TestRateLimiting -v
pytest auth/tests.py::TestPermissionSystem -v
```

## 🗄️ Database Schema

### API Keys Table (`api_keys`)
- `id` - UUID primary key
- `name` - Human-readable name
- `description` - Optional description
- `key_hash` - SHA-256 hash of the API key
- `key_prefix` - First 8 characters (for identification)
- `permission_level` - Permission level (read_only, content_creator, etc.)
- `scopes` - JSON array of allowed scopes
- `rate_limit_per_hour` - Hourly request limit
- `rate_limit_per_day` - Daily request limit
- `status` - active, inactive, revoked, expired
- `created_at`, `expires_at`, `last_used_at` - Timestamps
- `usage_count` - Total number of requests
- Security fields: `allowed_ips`, `user_agent_patterns`

### Usage Logs Table (`api_key_usage_logs`)
- `id` - UUID primary key
- `api_key_id` - Foreign key to api_keys
- `timestamp` - Request timestamp
- `endpoint` - Accessed endpoint
- `method` - HTTP method
- `status_code` - Response status
- `response_time_ms` - Response time
- `ip_address` - Client IP
- `user_agent` - Client user agent

## 🔧 Maintenance

### Regular Cleanup

Schedule regular cleanup of expired keys and old logs:

```python
from auth.migrations import cleanup_expired_keys

# Run daily cleanup
cleanup_expired_keys()
```

### Key Rotation

Best practices for API key rotation:

1. **Create new key** with same permissions
2. **Update clients** to use new key
3. **Monitor usage** to ensure transition
4. **Revoke old key** after verification

```python
# Create replacement key
new_key = create_api_key(
    name=f"{old_key.name} (Rotated)",
    permission_level=old_key.permission_level,
    db=db,
)

# After client updates, revoke old key
manager.revoke_api_key(old_key_id, "Security rotation")
```

## 🛡️ Security Best Practices

1. **Store keys securely** - Never log or expose full API keys
2. **Use HTTPS only** - Always encrypt API key transmission
3. **Implement IP restrictions** for sensitive keys
4. **Monitor usage patterns** for anomalies
5. **Rotate keys regularly** - Especially for high-privilege keys
6. **Set appropriate expiration** dates for temporary access
7. **Use minimum required permissions** - Follow principle of least privilege
8. **Log security events** - Monitor failed authentication attempts

## 🐛 Troubleshooting

### Common Issues

**"Invalid or expired API key"**
- Check if key is correctly formatted (starts with `ck_`)
- Verify key hasn't expired or been revoked
- Ensure key has required permissions for the endpoint

**"Rate limit exceeded"**
- Check current usage against limits
- Consider increasing limits for the key
- Implement exponential backoff in client

**"API key does not have required permission"**
- Verify the key's permission level
- Check if specific scope is included in key's scopes
- Consider upgrading to higher permission level

### Debug Commands

```bash
# Check API key details
python -m auth.management details <api_key_id>

# View recent usage
python -m auth.management stats --days 1

# Test API key validation
python -c "
from auth.api_key_auth import APIKeyAuth
from database.session import get_db_session
with get_db_session() as db:
    auth = APIKeyAuth(db)
    result = auth.validate_api_key('your_key_here')
    print('Valid!' if result else 'Invalid!')
"
```

## 📚 API Reference

See the full API documentation at `/docs` when the server is running, or check `auth/router.py` for endpoint definitions.

Key endpoints:
- `POST /api/v1/auth/api-keys` - Create API key
- `GET /api/v1/auth/api-keys` - List API keys  
- `GET /api/v1/auth/api-keys/{id}` - Get API key details
- `DELETE /api/v1/auth/api-keys/{id}` - Revoke API key
- `GET /api/v1/auth/api-keys/current/info` - Get current key info
- `GET /api/v1/auth/permissions/check` - Check permissions