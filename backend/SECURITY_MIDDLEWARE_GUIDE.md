# Security Middleware Implementation Guide

## Overview

The security middleware provides comprehensive protection for the AI Course Generation Platform, implementing OWASP security best practices, environment-based CORS configuration, and essential security headers.

## Features

### 🔒 Security Headers
- **HSTS** (HTTP Strict Transport Security) - Forces HTTPS in production
- **CSP** (Content Security Policy) - Prevents XSS and injection attacks
- **X-Frame-Options** - Prevents clickjacking attacks
- **X-Content-Type-Options** - Prevents MIME type sniffing
- **X-XSS-Protection** - Legacy XSS protection
- **Referrer-Policy** - Controls referrer information leakage
- **Permissions-Policy** - Restricts browser features
- **Cache-Control** - Prevents sensitive data caching

### 🌐 CORS Configuration
- Environment-based origin configuration
- Support for JSON array or comma-separated origins
- Automatic environment detection (development/staging/production)
- Proper preflight request handling
- Configurable methods and headers

### 🛡️ Request Validation
- Request size limits
- Malicious pattern detection
- User agent filtering (production only)
- Path traversal protection
- XSS and SQL injection pattern blocking

### 🏠 Trusted Host Protection
- Environment-specific host validation
- Prevents Host header attacks
- Configurable trusted domains

## Installation and Setup

### 1. Environment Configuration

Update your `.env` file with security-specific settings:

```env
# Environment Settings
ENVIRONMENT=development  # development, staging, production
DEBUG=false
SECRET_KEY=your-secure-secret-key-here

# CORS Settings
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
# Or comma-separated: BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Security Settings
MAX_REQUEST_SIZE=10485760  # 10MB
TRUSTED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### 2. Application Integration

Replace the basic CORS middleware in your FastAPI app:

```python
# OLD: Basic CORS setup
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, ...)

# NEW: Comprehensive security middleware
from middleware.security import setup_security_middleware
setup_security_middleware(app)
```

### 3. Complete Example

```python
from fastapi import FastAPI
from middleware.security import setup_security_middleware

app = FastAPI(title="Your API")

# Set up all security middleware
setup_security_middleware(app)

# Your routes...
```

## Environment-Specific Configurations

### Development Environment
```env
ENVIRONMENT=development
DEBUG=true
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]
```

**Features:**
- Permissive CORS for local development
- Relaxed CSP policy
- All localhost variations allowed
- Security headers enabled but less strict

### Staging Environment
```env
ENVIRONMENT=staging
DEBUG=false
BACKEND_CORS_ORIGINS=["https://staging.yourdomain.com", "http://localhost:3000"]
```

**Features:**
- Staging domain CORS + localhost for testing
- Moderate CSP policy
- Security headers enforced
- Request validation enabled

### Production Environment
```env
ENVIRONMENT=production
DEBUG=false
BACKEND_CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
SECRET_KEY=your-very-secure-production-key
```

**Features:**
- Strict CORS (HTTPS only)
- Strict CSP policy
- HSTS enabled
- Full request validation
- User agent filtering
- Malicious pattern blocking

## Security Endpoints

The middleware includes monitoring endpoints:

### GET /api/v1/security/info
Returns security configuration information:
```json
{
  "status": "success",
  "data": {
    "environment": "development",
    "cors_origins_count": 3,
    "security_headers_count": 8,
    "csp_enabled": true,
    "debug_mode": true
  }
}
```

### GET /api/v1/security/validate
Validates security configuration:
```json
{
  "status": "warning",
  "security_score": 75,
  "environment": "development",
  "issues": ["Debug mode enabled"],
  "recommendations": ["Review settings before production"]
}
```

### GET /api/v1/security/headers
Test endpoint to verify security headers are applied.

### GET /api/v1/security/cors-test
Test endpoint for CORS configuration verification.

## Testing the Security Middleware

### 1. Manual Testing
```bash
# Test security headers
curl -I http://localhost:8000/api/v1/security/headers

# Test CORS preflight
curl -X OPTIONS http://localhost:8000/api/v1/security/cors-test \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST"

# Test security validation
curl http://localhost:8000/api/v1/security/validate
```

### 2. Automated Testing
Run the provided test script:
```bash
python test_security_middleware.py
```

This will test:
- Security headers presence
- CORS configuration
- Security validation
- Malicious request blocking

## Security Score Interpretation

| Score Range | Status | Meaning |
|-------------|--------|---------|
| 80-100 | Good | Production ready, minimal issues |
| 60-79 | Warning | Some issues need attention |
| 0-59 | Critical | Significant security improvements needed |

## Common Issues and Solutions

### Issue: CORS Errors in Browser
**Symptoms:** Browser blocks requests with CORS errors
**Solution:**
1. Check `BACKEND_CORS_ORIGINS` includes your frontend URL
2. Verify environment is set correctly
3. Check browser developer tools for specific error

### Issue: Security Headers Missing
**Symptoms:** Security scanners report missing headers
**Solution:**
1. Ensure `setup_security_middleware()` is called
2. Check middleware order (security should be early)
3. Verify no other middleware is overriding headers

### Issue: High Security Score Issues
**Symptoms:** Security validation reports issues
**Solution:**
1. Set strong `SECRET_KEY` (not default)
2. Disable `DEBUG` in production
3. Use HTTPS URLs for production CORS origins
4. Set `ENVIRONMENT=production` for production deployment

### Issue: Requests Being Blocked
**Symptoms:** Legitimate requests return 403 errors
**Solution:**
1. Check request size limits
2. Review malicious pattern detection
3. Verify trusted hosts configuration
4. Check user agent restrictions

## Advanced Configuration

### Custom CSP Policy
Override the default CSP by modifying `SecurityConfig._get_csp_policy()`:

```python
def _get_csp_policy(self) -> str:
    if self.environment == "production":
        return "default-src 'self'; script-src 'self' https://trusted-cdn.com; ..."
    # ... rest of the method
```

### Custom Security Headers
Add additional headers in `SecurityConfig._get_security_headers()`:

```python
def _get_security_headers(self) -> Dict[str, str]:
    headers = {
        # ... existing headers
        "Custom-Security-Header": "your-value"
    }
    return headers
```

### Request Size Limits
Adjust per endpoint by setting `MAX_REQUEST_SIZE` environment variable or creating custom middleware.

## Production Deployment Checklist

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] Strong `SECRET_KEY` set
- [ ] HTTPS-only CORS origins
- [ ] `TRUSTED_HOSTS` configured
- [ ] Security validation score > 80
- [ ] All security headers present
- [ ] CSP policy tested
- [ ] CORS configuration tested

## Monitoring and Maintenance

### Regular Checks
1. Run security validation endpoint weekly
2. Monitor security header presence
3. Review CORS configuration changes
4. Update CSP policy as needed
5. Monitor for new security issues

### Security Updates
1. Review security middleware quarterly
2. Update blocked patterns as threats evolve
3. Adjust security headers based on new standards
4. Monitor OWASP recommendations

## Support and Troubleshooting

### Debug Mode
Enable debug mode for detailed security information:
```env
DEBUG=true
```

This will expose detailed configuration in security endpoints (development only).

### Logging
Security middleware logs important events:
- Middleware setup
- Blocked requests
- Configuration warnings

Check application logs for security-related messages.

For additional support, refer to:
- FastAPI Security documentation
- OWASP Security Guidelines  
- MDN Web Security documentation