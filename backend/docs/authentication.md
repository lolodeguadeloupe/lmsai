# Authentication and Security Guide

## Overview

The Course Generation Platform API uses API key-based authentication with comprehensive security features. This guide covers authentication setup, security best practices, and advanced security configurations.

## API Key Authentication

### How It Works

All API requests require an API key passed in the `X-API-Key` header:

```http
X-API-Key: your-api-key-here
```

The API key system provides:
- **Secure access control** with scoped permissions
- **Rate limiting** per API key
- **Usage tracking** and analytics
- **Key rotation** and revocation capabilities
- **Environment separation** (development/production keys)

### Getting Your API Key

1. **Sign up** at the [Developer Portal](https://developers.courseplatform.com)
2. **Create an application** and configure your project details
3. **Generate API keys** for your environments:
   - **Development keys**: For testing and development
   - **Production keys**: For live applications

### API Key Types

#### Development Keys
- **Purpose**: Testing and development
- **Rate limits**: 50 requests per minute
- **Features**: Full API access, test data, sandbox environment
- **Regeneration**: Unlimited

#### Production Keys
- **Purpose**: Live applications
- **Rate limits**: 100-1000 requests per minute (based on plan)
- **Features**: Full API access, production data
- **Regeneration**: Limited for security

#### Restricted Keys
- **Purpose**: Limited scope access
- **Permissions**: Configurable scopes (read-only, specific endpoints)
- **Use case**: Third-party integrations, customer access

## Authentication Implementation

### Python Implementation

```python
import os
import requests
from typing import Optional

class CourseAPIAuth:
    def __init__(self, api_key: Optional[str] = None):
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv('COURSEPLATFORM_API_KEY')
        
        if not self.api_key:
            raise ValueError("API key is required. Set COURSEPLATFORM_API_KEY environment variable or pass api_key parameter.")
        
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'CourseAPI-Python/1.0'
        }
    
    def make_authenticated_request(self, method: str, url: str, **kwargs):
        """Make an authenticated request to the API"""
        kwargs.setdefault('headers', {}).update(self.headers)
        
        response = requests.request(method, url, **kwargs)
        
        # Handle authentication errors
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key or expired token")
        elif response.status_code == 403:
            raise PermissionError("Insufficient permissions for this operation")
        
        return response

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

# Usage example
def main():
    # Initialize with API key from environment
    auth = CourseAPIAuth()
    
    # Make authenticated request
    try:
        response = auth.make_authenticated_request(
            'GET',
            'https://api.courseplatform.com/v1/courses'
        )
        
        if response.status_code == 200:
            courses = response.json()
            print(f"Found {len(courses['courses'])} courses")
        
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except PermissionError as e:
        print(f"Permission denied: {e}")

if __name__ == "__main__":
    main()
```

### JavaScript/Node.js Implementation

```javascript
const axios = require('axios');

class CourseAPIAuth {
    constructor(apiKey = null) {
        this.apiKey = apiKey || process.env.COURSEPLATFORM_API_KEY;
        
        if (!this.apiKey) {
            throw new Error('API key is required. Set COURSEPLATFORM_API_KEY environment variable or pass apiKey parameter.');
        }
        
        // Create axios instance with default headers
        this.client = axios.create({
            baseURL: 'https://api.courseplatform.com/v1',
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json',
                'User-Agent': 'CourseAPI-Node/1.0'
            }
        });
        
        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => {
                if (error.response) {
                    const status = error.response.status;
                    if (status === 401) {
                        throw new AuthenticationError('Invalid API key or expired token');
                    } else if (status === 403) {
                        throw new PermissionError('Insufficient permissions for this operation');
                    }
                }
                throw error;
            }
        );
    }
    
    async makeRequest(method, endpoint, data = null) {
        try {
            const response = await this.client({
                method,
                url: endpoint,
                data
            });
            return response.data;
        } catch (error) {
            console.error(`API request failed: ${error.message}`);
            throw error;
        }
    }
}

class AuthenticationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'AuthenticationError';
    }
}

class PermissionError extends Error {
    constructor(message) {
        super(message);
        this.name = 'PermissionError';
    }
}

// Usage example
async function main() {
    try {
        const auth = new CourseAPIAuth();
        
        const courses = await auth.makeRequest('GET', '/courses');
        console.log(`Found ${courses.courses.length} courses`);
        
    } catch (error) {
        if (error instanceof AuthenticationError) {
            console.error('Authentication failed:', error.message);
        } else if (error instanceof PermissionError) {
            console.error('Permission denied:', error.message);
        } else {
            console.error('Request failed:', error.message);
        }
    }
}

main();
```

### PHP Implementation

```php
<?php

class CourseAPIAuth {
    private $apiKey;
    private $baseUrl;
    
    public function __construct($apiKey = null, $baseUrl = 'https://api.courseplatform.com/v1') {
        $this->apiKey = $apiKey ?: getenv('COURSEPLATFORM_API_KEY');
        $this->baseUrl = $baseUrl;
        
        if (!$this->apiKey) {
            throw new InvalidArgumentException('API key is required. Set COURSEPLATFORM_API_KEY environment variable or pass apiKey parameter.');
        }
    }
    
    public function makeRequest($method, $endpoint, $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $headers = [
            'X-API-Key: ' . $this->apiKey,
            'Content-Type: application/json',
            'User-Agent: CourseAPI-PHP/1.0'
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        // Handle authentication errors
        if ($httpCode === 401) {
            throw new AuthenticationException('Invalid API key or expired token');
        } elseif ($httpCode === 403) {
            throw new PermissionException('Insufficient permissions for this operation');
        } elseif ($httpCode >= 400) {
            $decoded = json_decode($response, true);
            throw new Exception("API Error ({$httpCode}): " . ($decoded['message'] ?? 'Unknown error'));
        }
        
        return json_decode($response, true);
    }
}

class AuthenticationException extends Exception {}
class PermissionException extends Exception {}

// Usage example
try {
    $auth = new CourseAPIAuth();
    
    $courses = $auth->makeRequest('GET', '/courses');
    echo "Found " . count($courses['courses']) . " courses\n";
    
} catch (AuthenticationException $e) {
    echo "Authentication failed: " . $e->getMessage() . "\n";
} catch (PermissionException $e) {
    echo "Permission denied: " . $e->getMessage() . "\n";
} catch (Exception $e) {
    echo "Request failed: " . $e->getMessage() . "\n";
}
?>
```

## Security Best Practices

### API Key Management

#### Secure Storage

**✅ DO:**
```bash
# Environment variables
export COURSEPLATFORM_API_KEY="your-api-key"

# .env files (add to .gitignore)
COURSEPLATFORM_API_KEY=your-api-key

# AWS Secrets Manager, Azure Key Vault, etc.
```

**❌ DON'T:**
```python
# Hard-coded in source code
api_key = "sk-abcd1234efgh5678"  # Never do this!

# Committed to version control
# config.py with API keys

# Logged in plain text
print(f"Using API key: {api_key}")  # Don't log keys
```

#### Key Rotation

Rotate API keys regularly:

```python
import os
from datetime import datetime, timedelta

class APIKeyManager:
    def __init__(self):
        self.primary_key = os.getenv('COURSEPLATFORM_API_KEY_PRIMARY')
        self.secondary_key = os.getenv('COURSEPLATFORM_API_KEY_SECONDARY')
        self.last_rotation = self._get_last_rotation_date()
    
    def should_rotate(self, rotation_days=90):
        """Check if keys should be rotated"""
        if not self.last_rotation:
            return True
        
        return datetime.now() - self.last_rotation > timedelta(days=rotation_days)
    
    def get_active_key(self):
        """Get the currently active API key"""
        # Implement key rotation logic
        if self.should_rotate():
            self._rotate_keys()
        
        return self.primary_key
    
    def _rotate_keys(self):
        """Rotate API keys (implement based on your key management system)"""
        # 1. Generate new key
        # 2. Update primary key
        # 3. Keep secondary key as backup
        # 4. Update last rotation date
        pass
    
    def _get_last_rotation_date(self):
        """Get last rotation date from secure storage"""
        # Implement based on your storage system
        pass
```

### Request Security

#### HTTPS Only

Always use HTTPS in production:

```python
import requests
from urllib3.exceptions import InsecureRequestWarning

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class SecureAPIClient:
    def __init__(self, api_key, verify_ssl=True):
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.base_url = "https://api.courseplatform.com/v1"  # Always HTTPS
        
        if not verify_ssl:
            print("WARNING: SSL verification disabled")
    
    def make_request(self, method, endpoint, **kwargs):
        kwargs.setdefault('verify', self.verify_ssl)
        kwargs.setdefault('timeout', 30)
        
        headers = kwargs.get('headers', {})
        headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers
        
        return requests.request(method, f"{self.base_url}{endpoint}", **kwargs)
```

#### Request Signing (Advanced)

For high-security environments, implement request signing:

```python
import hmac
import hashlib
import time
from datetime import datetime

class SignedAPIClient:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
    
    def _generate_signature(self, method, endpoint, body, timestamp):
        """Generate HMAC-SHA256 signature for request"""
        # Create string to sign
        string_to_sign = f"{method}\n{endpoint}\n{body}\n{timestamp}"
        
        # Generate signature
        signature = hmac.new(
            self.secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def make_signed_request(self, method, endpoint, data=None):
        """Make a signed API request"""
        timestamp = str(int(time.time()))
        body = json.dumps(data) if data else ""
        
        signature = self._generate_signature(method, endpoint, body, timestamp)
        
        headers = {
            'X-API-Key': self.api_key,
            'X-Timestamp': timestamp,
            'X-Signature': signature,
            'Content-Type': 'application/json'
        }
        
        return requests.request(
            method,
            f"https://api.courseplatform.com/v1{endpoint}",
            headers=headers,
            data=body if body else None
        )
```

### Error Handling

#### Secure Error Messages

Don't expose sensitive information in error messages:

```python
class SecureErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_api_error(self, response):
        """Handle API errors securely"""
        status_code = response.status_code
        
        if status_code == 401:
            # Don't expose whether key exists or is just invalid
            public_message = "Authentication required"
            private_message = f"Invalid API key: {response.text}"
            
        elif status_code == 403:
            public_message = "Access denied"
            private_message = f"Permission error: {response.text}"
            
        elif status_code == 429:
            public_message = "Rate limit exceeded"
            private_message = f"Rate limited: {response.headers.get('x-ratelimit-reset')}"
            
        else:
            public_message = "Request failed"
            private_message = f"HTTP {status_code}: {response.text}"
        
        # Log detailed error internally
        self.logger.error(private_message)
        
        # Return generic message to user
        return {
            'error': public_message,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
```

## Permission Scopes

API keys can be configured with specific permission scopes to limit access:

### Available Scopes

```python
# Course operations
COURSE_READ = "course:read"         # List and view courses
COURSE_WRITE = "course:write"       # Create and update courses
COURSE_DELETE = "course:delete"     # Delete courses

# Chapter operations  
CHAPTER_READ = "chapter:read"       # View chapter details
CHAPTER_WRITE = "chapter:write"     # Update chapters
CHAPTER_DELETE = "chapter:delete"   # Delete chapters

# Assessment operations
ASSESSMENT_READ = "assessment:read"     # View quizzes and assessments
ASSESSMENT_WRITE = "assessment:write"   # Create and update assessments
ASSESSMENT_DELETE = "assessment:delete" # Delete assessments

# Export operations
EXPORT_READ = "export:read"         # View export status
EXPORT_WRITE = "export:write"       # Create exports

# Quality operations
QUALITY_READ = "quality:read"       # View quality metrics
QUALITY_WRITE = "quality:write"     # Update quality settings

# Generation operations
GENERATION_READ = "generation:read"     # View generation status
GENERATION_WRITE = "generation:write"   # Start/stop generation

# Admin operations
ADMIN_READ = "admin:read"           # View admin data
ADMIN_WRITE = "admin:write"         # Admin operations
```

### Scope-Based Client

```python
class ScopedAPIClient:
    def __init__(self, api_key, required_scopes=None):
        self.api_key = api_key
        self.required_scopes = required_scopes or []
        self.permissions = self._get_key_permissions()
    
    def _get_key_permissions(self):
        """Get permissions for the current API key"""
        response = requests.get(
            "https://api.courseplatform.com/v1/auth/permissions",
            headers={'X-API-Key': self.api_key}
        )
        
        if response.status_code == 200:
            return response.json()['scopes']
        else:
            raise AuthenticationError("Failed to get API key permissions")
    
    def _check_permission(self, required_scope):
        """Check if API key has required permission"""
        if required_scope not in self.permissions:
            raise PermissionError(f"API key lacks required scope: {required_scope}")
    
    def create_course(self, course_data):
        """Create course (requires course:write scope)"""
        self._check_permission("course:write")
        
        response = requests.post(
            "https://api.courseplatform.com/v1/courses",
            json=course_data,
            headers={'X-API-Key': self.api_key}
        )
        
        return response.json()
    
    def list_courses(self, **filters):
        """List courses (requires course:read scope)"""
        self._check_permission("course:read")
        
        response = requests.get(
            "https://api.courseplatform.com/v1/courses",
            params=filters,
            headers={'X-API-Key': self.api_key}
        )
        
        return response.json()
```

## Rate Limiting

### Understanding Rate Limits

Rate limits are enforced per API key:

| Key Type | Requests/Minute | Burst Limit |
|----------|----------------|-------------|
| Development | 50 | 20/10 seconds |
| Production | 100-1000 | 50/10 seconds |
| Enterprise | Custom | Custom |

### Rate Limit Headers

Response headers provide rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 60
```

### Handling Rate Limits

```python
import time
from datetime import datetime

class RateLimitHandler:
    def __init__(self, api_client):
        self.api_client = api_client
        self.last_request_time = 0
        self.min_interval = 0.6  # Minimum seconds between requests
    
    def make_rate_limited_request(self, method, endpoint, **kwargs):
        """Make request with rate limiting"""
        # Implement basic rate limiting
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        response = self.api_client.make_request(method, endpoint, **kwargs)
        self.last_request_time = time.time()
        
        # Check rate limit headers
        if 'x-ratelimit-remaining' in response.headers:
            remaining = int(response.headers['x-ratelimit-remaining'])
            
            if remaining < 10:  # Less than 10 requests remaining
                reset_time = int(response.headers.get('x-ratelimit-reset', 0))
                wait_time = reset_time - time.time()
                
                if wait_time > 0:
                    print(f"Rate limit low. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
        
        # Handle rate limit exceeded
        if response.status_code == 429:
            retry_after = int(response.headers.get('retry-after', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            
            # Retry the request
            return self.make_rate_limited_request(method, endpoint, **kwargs)
        
        return response
```

## Monitoring and Logging

### Security Logging

```python
import logging
import hashlib
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Create secure log handler
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_api_request(self, method, endpoint, api_key, status_code, response_time):
        """Log API request securely"""
        # Hash API key for logging (don't log full key)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
        
        self.logger.info(
            f"API_REQUEST method={method} endpoint={endpoint} "
            f"key_hash={key_hash} status={status_code} "
            f"response_time={response_time}ms"
        )
    
    def log_authentication_failure(self, api_key, endpoint, reason):
        """Log authentication failures"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
        
        self.logger.warning(
            f"AUTH_FAILURE key_hash={key_hash} endpoint={endpoint} "
            f"reason={reason} timestamp={datetime.now().isoformat()}"
        )
    
    def log_permission_denial(self, api_key, endpoint, required_scope):
        """Log permission denials"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
        
        self.logger.warning(
            f"PERMISSION_DENIED key_hash={key_hash} endpoint={endpoint} "
            f"required_scope={required_scope}"
        )
```

### Usage Analytics

```python
class UsageAnalytics:
    def __init__(self, api_client):
        self.api_client = api_client
    
    def get_usage_stats(self, start_date, end_date):
        """Get API usage statistics"""
        response = self.api_client.make_request(
            'GET',
            '/analytics/usage',
            params={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        )
        
        return {
            'total_requests': response['total_requests'],
            'successful_requests': response['successful_requests'],
            'failed_requests': response['failed_requests'],
            'rate_limited_requests': response['rate_limited_requests'],
            'endpoints_used': response['endpoints_used'],
            'peak_usage_hour': response['peak_usage_hour']
        }
    
    def get_quota_status(self):
        """Get current quota usage"""
        response = self.api_client.make_request('GET', '/analytics/quota')
        
        return {
            'current_usage': response['current_usage'],
            'quota_limit': response['quota_limit'],
            'reset_date': response['reset_date'],
            'overage_cost': response.get('overage_cost', 0)
        }
```

## Testing Authentication

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch
import requests_mock

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-api-key"
        self.client = CourseAPIAuth(self.api_key)
    
    @requests_mock.Mocker()
    def test_valid_authentication(self, m):
        m.get(
            'https://api.courseplatform.com/v1/courses',
            json={'courses': []},
            status_code=200
        )
        
        response = self.client.make_authenticated_request(
            'GET',
            'https://api.courseplatform.com/v1/courses'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-API-Key', m.last_request.headers)
        self.assertEqual(m.last_request.headers['X-API-Key'], self.api_key)
    
    @requests_mock.Mocker()
    def test_invalid_api_key(self, m):
        m.get(
            'https://api.courseplatform.com/v1/courses',
            json={'error': 'Invalid API key'},
            status_code=401
        )
        
        with self.assertRaises(AuthenticationError):
            self.client.make_authenticated_request(
                'GET',
                'https://api.courseplatform.com/v1/courses'
            )
    
    @requests_mock.Mocker()
    def test_insufficient_permissions(self, m):
        m.post(
            'https://api.courseplatform.com/v1/courses',
            json={'error': 'Insufficient permissions'},
            status_code=403
        )
        
        with self.assertRaises(PermissionError):
            self.client.make_authenticated_request(
                'POST',
                'https://api.courseplatform.com/v1/courses',
                json={'title': 'Test Course'}
            )

if __name__ == '__main__':
    unittest.main()
```

## Troubleshooting

### Common Authentication Issues

#### 1. Invalid API Key Format

**Error**: `401 Unauthorized - Invalid API key format`

**Solution**:
```python
# Check API key format
def validate_api_key_format(api_key):
    if not api_key:
        raise ValueError("API key is required")
    
    if not api_key.startswith('cp_'):
        raise ValueError("API key must start with 'cp_'")
    
    if len(api_key) < 40:
        raise ValueError("API key is too short")
    
    return True
```

#### 2. Expired API Key

**Error**: `401 Unauthorized - API key expired`

**Solution**:
```python
# Check key expiration
response = requests.get(
    'https://api.courseplatform.com/v1/auth/validate',
    headers={'X-API-Key': api_key}
)

if response.status_code == 401:
    error_data = response.json()
    if 'expired' in error_data.get('message', '').lower():
        print("API key has expired. Please generate a new key.")
```

#### 3. Rate Limiting

**Error**: `429 Too Many Requests`

**Solution**: Implement exponential backoff:
```python
import time
import random

def exponential_backoff_request(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                    continue
            raise
    
    raise Exception("Max retries exceeded")
```

### Debug Tools

#### API Key Validator

```python
class APIKeyValidator:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def validate(self):
        """Comprehensive API key validation"""
        checks = {
            'format': self._check_format(),
            'authentication': self._check_authentication(),
            'permissions': self._check_permissions(),
            'rate_limits': self._check_rate_limits()
        }
        
        return checks
    
    def _check_format(self):
        """Check API key format"""
        try:
            validate_api_key_format(self.api_key)
            return {'status': 'pass', 'message': 'Valid format'}
        except ValueError as e:
            return {'status': 'fail', 'message': str(e)}
    
    def _check_authentication(self):
        """Check if API key authenticates successfully"""
        try:
            response = requests.get(
                'https://api.courseplatform.com/v1/auth/validate',
                headers={'X-API-Key': self.api_key}
            )
            
            if response.status_code == 200:
                return {'status': 'pass', 'message': 'Authentication successful'}
            else:
                return {'status': 'fail', 'message': response.json().get('message')}
                
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def _check_permissions(self):
        """Check API key permissions"""
        try:
            response = requests.get(
                'https://api.courseplatform.com/v1/auth/permissions',
                headers={'X-API-Key': self.api_key}
            )
            
            if response.status_code == 200:
                permissions = response.json()['scopes']
                return {
                    'status': 'pass',
                    'message': f'Permissions: {", ".join(permissions)}'
                }
            else:
                return {'status': 'fail', 'message': 'Could not retrieve permissions'}
                
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}
    
    def _check_rate_limits(self):
        """Check current rate limit status"""
        try:
            response = requests.get(
                'https://api.courseplatform.com/v1/courses',
                headers={'X-API-Key': self.api_key}
            )
            
            if 'x-ratelimit-remaining' in response.headers:
                remaining = response.headers['x-ratelimit-remaining']
                limit = response.headers['x-ratelimit-limit']
                return {
                    'status': 'pass',
                    'message': f'Rate limit: {remaining}/{limit} requests remaining'
                }
            else:
                return {'status': 'unknown', 'message': 'Rate limit headers not present'}
                
        except Exception as e:
            return {'status': 'fail', 'message': str(e)}

# Usage
validator = APIKeyValidator("your-api-key")
results = validator.validate()

for check, result in results.items():
    print(f"{check}: {result['status']} - {result['message']}")
```

## Migration and Updates

### API Version Migration

When migrating between API versions:

```python
class VersionMigrator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.v1_client = CourseAPIClient(api_key, "https://api.courseplatform.com/v1")
        self.v2_client = CourseAPIClient(api_key, "https://api.courseplatform.com/v2")
    
    def test_v2_compatibility(self):
        """Test if API key works with v2"""
        try:
            response = self.v2_client.make_request('GET', '/health')
            return True
        except AuthenticationError:
            return False
    
    def migrate_to_v2(self):
        """Migrate from v1 to v2"""
        if not self.test_v2_compatibility():
            raise Exception("API key not compatible with v2")
        
        # Implement migration logic
        pass
```

This authentication guide provides comprehensive coverage of security best practices for the Course Generation Platform API. Always follow security best practices and keep your API keys secure.