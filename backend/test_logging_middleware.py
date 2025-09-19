"""
Test script to demonstrate the logging middleware functionality
Run this to see the structured logging in action.
"""

import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Import our logging middleware
from src.middleware.logging import RequestResponseLoggingMiddleware, get_correlation_id
from src.config.logging_config import configure_logging, get_logger

# Configure logging
configure_logging()

# Create test app
app = FastAPI(title="Logging Test API")

# Add logging middleware
app.add_middleware(
    RequestResponseLoggingMiddleware,
    skip_paths={'/health'},
    max_body_size=1000,
    log_request_body=True,
    log_response_body=True,
    logger_name="course_platform.test"
)

# Test models
class UserRequest(BaseModel):
    name: str
    email: str
    password: str  # This should be masked in logs
    api_key: str   # This should be masked in logs

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    correlation_id: str

# Test endpoints
@app.get("/health")
async def health():
    """Health endpoint that should be skipped in logs"""
    return {"status": "healthy"}

@app.get("/test")
async def test_get():
    """Simple GET endpoint"""
    logger = get_logger('test_endpoint')
    logger.info("Test GET endpoint called")
    
    return {
        "message": "Hello World",
        "correlation_id": get_correlation_id()
    }

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserRequest):
    """POST endpoint with sensitive data"""
    logger = get_logger('user_creation')
    logger.info("Creating new user", extra={
        'user_email': user.email,
        'correlation_id': get_correlation_id()
    })
    
    # Simulate user creation
    return UserResponse(
        id=123,
        name=user.name,
        email=user.email,
        correlation_id=get_correlation_id()
    )

@app.get("/error")
async def test_error():
    """Endpoint that raises an error"""
    logger = get_logger('error_test')
    logger.warning("About to raise test error")
    raise HTTPException(status_code=400, detail="Test error for logging")

@app.get("/large-response")
async def large_response():
    """Endpoint with large response to test size limits"""
    return {
        "data": "x" * 20000,  # 20KB of data
        "correlation_id": get_correlation_id()
    }

def run_tests():
    """Run test requests to demonstrate logging"""
    client = TestClient(app)
    
    print("🧪 Testing Logging Middleware")
    print("=" * 50)
    
    # Test 1: Health endpoint (should be skipped)
    print("\n1. Testing health endpoint (should be skipped in logs):")
    response = client.get("/health")
    print(f"Response: {response.json()}")
    
    # Test 2: Simple GET request
    print("\n2. Testing simple GET request:")
    response = client.get("/test")
    print(f"Response: {response.json()}")
    
    # Test 3: GET with query parameters
    print("\n3. Testing GET with query parameters (including sensitive data):")
    response = client.get("/test?name=john&password=secret123&api_key=abc123")
    print(f"Response: {response.json()}")
    
    # Test 4: POST with sensitive data in body
    print("\n4. Testing POST with sensitive data in body:")
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "supersecret123",
        "api_key": "secret-api-key-456"
    }
    response = client.post("/users", json=user_data)
    print(f"Response: {response.json()}")
    
    # Test 5: Error handling
    print("\n5. Testing error handling:")
    try:
        response = client.get("/error")
    except:
        pass
    
    # Test 6: Large response
    print("\n6. Testing large response (should be truncated):")
    response = client.get("/large-response")
    print(f"Response size: {len(str(response.json()))} characters")
    
    print("\n✅ All tests completed. Check the logs above to see structured logging output.")
    print("\nKey features demonstrated:")
    print("- ✅ Correlation ID generation and tracking")
    print("- ✅ Sensitive data masking (passwords, API keys)")
    print("- ✅ Request/response timing")
    print("- ✅ Path skipping for health endpoints")
    print("- ✅ Error logging with correlation")
    print("- ✅ Large body truncation")
    print("- ✅ JSON structured logging format")

if __name__ == "__main__":
    # Set up console logging to see output
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    run_tests()