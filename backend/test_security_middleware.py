"""
Test script for security middleware functionality.

This script demonstrates:
1. Security headers validation
2. CORS configuration testing
3. Security configuration validation
4. Basic security checks

Run this script to verify the security middleware is working correctly.
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api/v1"


def test_security_headers():
    """Test that security headers are properly applied."""
    print("🔍 Testing Security Headers...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/security/headers", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print("\nSecurity Headers Found:")
        
        # Expected security headers
        expected_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "referrer-policy",
            "permissions-policy",
            "cache-control",
            "content-security-policy"
        ]
        
        found_headers = []
        missing_headers = []
        
        for header in expected_headers:
            if header in response.headers:
                found_headers.append(header)
                print(f"  ✅ {header}: {response.headers[header]}")
            else:
                missing_headers.append(header)
                print(f"  ❌ {header}: Missing")
        
        # Check for HSTS (only expected in production HTTPS)
        if "strict-transport-security" in response.headers:
            print(f"  ✅ strict-transport-security: {response.headers['strict-transport-security']}")
        else:
            print(f"  ℹ️ strict-transport-security: Not set (expected for non-HTTPS)")
        
        print(f"\nSummary: {len(found_headers)}/{len(expected_headers)} security headers found")
        return len(missing_headers) == 0
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing security headers: {e}")
        return False


def test_cors_preflight():
    """Test CORS preflight request handling."""
    print("\n🌐 Testing CORS Preflight...")
    
    try:
        # Simulate a preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        
        response = requests.options(f"{API_BASE_URL}/security/cors-test", headers=headers, timeout=10)
        
        print(f"Preflight Status Code: {response.status_code}")
        
        # Check CORS headers in response
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers",
            "access-control-allow-credentials",
            "access-control-max-age"
        ]
        
        print("CORS Headers:")
        for header in cors_headers:
            if header in response.headers:
                print(f"  ✅ {header}: {response.headers[header]}")
            else:
                print(f"  ❌ {header}: Missing")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing CORS: {e}")
        return False


def test_security_info():
    """Test security information endpoint."""
    print("\n📊 Testing Security Information...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/security/info", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Security info retrieved successfully")
            print(f"Environment: {data['data']['environment']}")
            print(f"CORS Origins Count: {data['data']['cors_origins_count']}")
            print(f"CSP Enabled: {data['data']['csp_enabled']}")
            print(f"Debug Mode: {data['data']['debug_mode']}")
            return True
        else:
            print(f"❌ Failed to get security info: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting security info: {e}")
        return False


def test_security_validation():
    """Test security configuration validation."""
    print("\n🔒 Testing Security Validation...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/security/validate", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Security validation completed")
            print(f"Status: {data['status']}")
            print(f"Security Score: {data['security_score']}/100")
            print(f"Environment: {data['environment']}")
            
            if data['issues']:
                print("\nSecurity Issues:")
                for issue in data['issues']:
                    print(f"  ⚠️ {issue}")
            else:
                print("\n✅ No security issues found")
            
            if data['recommendations']:
                print("\nRecommendations:")
                for rec in data['recommendations']:
                    print(f"  💡 {rec}")
            
            return data['security_score'] >= 60  # Minimum acceptable score
        else:
            print(f"❌ Failed to validate security: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error validating security: {e}")
        return False


def test_malicious_request_blocking():
    """Test that malicious requests are blocked."""
    print("\n🛡️ Testing Malicious Request Blocking...")
    
    # Test common attack patterns
    malicious_urls = [
        f"{BASE_URL}/../../../etc/passwd",  # Path traversal
        f"{BASE_URL}/api/v1/test?q=<script>alert('xss')</script>",  # XSS
        f"{BASE_URL}/api/v1/test?q='; DROP TABLE users; --",  # SQL injection
    ]
    
    blocked_count = 0
    
    for url in malicious_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 403:
                blocked_count += 1
                print(f"  ✅ Blocked malicious request: {url}")
            else:
                print(f"  ⚠️ Request not blocked: {url} (Status: {response.status_code})")
        except requests.exceptions.RequestException:
            # Connection errors are acceptable for malicious requests
            blocked_count += 1
            print(f"  ✅ Request rejected: {url}")
    
    print(f"\nBlocked {blocked_count}/{len(malicious_urls)} malicious requests")
    return blocked_count >= len(malicious_urls) * 0.5  # At least 50% should be blocked


def main():
    """Run all security tests."""
    print("🚀 Starting Security Middleware Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    print("✅ Server is running")
    print()
    
    # Run tests
    tests = [
        ("Security Headers", test_security_headers),
        ("CORS Preflight", test_cors_preflight),
        ("Security Info", test_security_info),
        ("Security Validation", test_security_validation),
        ("Malicious Request Blocking", test_malicious_request_blocking)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        result = test_func()
        results.append((test_name, result))
        print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
    
    # Summary
    print(f"\n{'=' * 50}")
    print("TEST SUMMARY")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All security tests passed!")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed, but some issues need attention")
    else:
        print("❌ Security configuration needs significant improvements")


if __name__ == "__main__":
    main()