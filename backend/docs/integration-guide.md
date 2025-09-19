# Integration Guide

## Getting Started

This guide helps developers integrate the Course Generation Platform API into their applications. Follow these steps to get up and running quickly.

### Prerequisites

- API key from the Course Generation Platform
- Basic understanding of REST APIs
- HTTP client library in your preferred language

### Quick Start

1. **Get your API key** from the developer console
2. **Test connectivity** with a simple request
3. **Create your first course** using the API
4. **Monitor generation progress** and retrieve results

## Authentication Setup

### Obtaining API Keys

1. Sign up at the [Developer Portal](https://developers.courseplatform.com)
2. Create a new application
3. Generate API keys for your environments:
   - **Development**: For testing and development
   - **Production**: For live applications

### API Key Management

```python
# Store API keys securely
import os

API_KEY = os.getenv('COURSEPLATFORM_API_KEY')
BASE_URL = os.getenv('COURSEPLATFORM_BASE_URL', 'https://api.courseplatform.com/v1')

headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}
```

## Basic Integration Patterns

### 1. Simple Course Creation

Create a course and wait for completion:

```python
import requests
import time

def create_simple_course():
    # Create course
    course_data = {
        "title": "Python Basics",
        "description": "Learn Python programming fundamentals",
        "subject_domain": "Computer Science",
        "target_audience": {
            "proficiency_level": "beginner",
            "prerequisites": ["Basic computer skills"],
            "learning_preferences": ["practical"]
        },
        "estimated_duration": "PT10H"
    }
    
    response = requests.post(
        f"{BASE_URL}/courses",
        json=course_data,
        headers=headers
    )
    
    if response.status_code == 201:
        course = response.json()
        course_id = course['id']
        
        # Poll for completion
        return wait_for_generation(course_id)
    else:
        raise Exception(f"Failed to create course: {response.text}")

def wait_for_generation(course_id, timeout=600):
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{BASE_URL}/courses/{course_id}/generation-status",
            headers=headers
        )
        
        if response.status_code == 200:
            status = response.json()
            
            if status['status'] == 'completed':
                return get_course_details(course_id)
            elif status['status'] == 'failed':
                raise Exception(f"Generation failed: {status.get('error_message')}")
            
            # Wait before next poll
            time.sleep(30)
        
        time.sleep(10)
    
    raise Exception("Generation timeout")

def get_course_details(course_id):
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get course: {response.text}")
```

### 2. Asynchronous Course Creation

For applications that need to handle multiple courses:

```python
import asyncio
import aiohttp

class CourseGenerationClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    async def create_course_async(self, course_data):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/courses",
                json=course_data,
                headers=self.headers
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create course: {await response.text()}")
    
    async def monitor_generation(self, course_id, callback=None):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"{self.base_url}/courses/{course_id}/generation-status",
                    headers=self.headers
                ) as response:
                    
                    if response.status == 200:
                        status = await response.json()
                        
                        if callback:
                            callback(course_id, status)
                        
                        if status['status'] == 'completed':
                            return await self.get_course(course_id)
                        elif status['status'] == 'failed':
                            raise Exception(f"Generation failed: {status.get('error_message')}")
                    
                    await asyncio.sleep(30)
    
    async def get_course(self, course_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/courses/{course_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get course: {await response.text()}")

# Usage
async def main():
    client = CourseGenerationClient(API_KEY, BASE_URL)
    
    # Progress callback
    def on_progress(course_id, status):
        print(f"Course {course_id}: {status['progress_percentage']}% - {status['current_phase']}")
    
    course_data = {
        "title": "Advanced Python",
        "subject_domain": "Computer Science",
        "target_audience": {"proficiency_level": "intermediate"}
    }
    
    # Create and monitor course
    created_course = await client.create_course_async(course_data)
    final_course = await client.monitor_generation(created_course['id'], on_progress)
    
    print(f"Course completed: {final_course['title']}")

# Run the async example
asyncio.run(main())
```

### 3. Batch Course Processing

For creating multiple courses efficiently:

```python
class BatchCourseProcessor:
    def __init__(self, api_key, base_url, max_concurrent=5):
        self.api_key = api_key
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_course_batch(self, courses_data):
        tasks = []
        for course_data in courses_data:
            task = asyncio.create_task(
                self._process_single_course(course_data)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_course(self, course_data):
        async with self.semaphore:
            # Create course
            created_course = await self._create_course(course_data)
            
            # Monitor completion
            completed_course = await self._wait_for_completion(created_course['id'])
            
            return completed_course
    
    async def _create_course(self, course_data):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/courses",
                json=course_data,
                headers=self.headers
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create course: {await response.text()}")
    
    async def _wait_for_completion(self, course_id):
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(
                    f"{self.base_url}/courses/{course_id}/generation-status",
                    headers=self.headers
                ) as response:
                    
                    if response.status == 200:
                        status = await response.json()
                        
                        if status['status'] == 'completed':
                            return await self._get_final_course(course_id)
                        elif status['status'] == 'failed':
                            raise Exception(f"Generation failed: {status.get('error_message')}")
                    
                    await asyncio.sleep(30)
    
    async def _get_final_course(self, course_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/courses/{course_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get course: {await response.text()}")

# Usage example
async def batch_example():
    processor = BatchCourseProcessor(API_KEY, BASE_URL)
    
    courses_to_create = [
        {
            "title": "Python Basics",
            "subject_domain": "Computer Science",
            "target_audience": {"proficiency_level": "beginner"}
        },
        {
            "title": "Data Structures",
            "subject_domain": "Computer Science", 
            "target_audience": {"proficiency_level": "intermediate"}
        },
        {
            "title": "Web Development",
            "subject_domain": "Web Technologies",
            "target_audience": {"proficiency_level": "beginner"}
        }
    ]
    
    results = await processor.process_course_batch(courses_to_create)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Course {i} failed: {result}")
        else:
            print(f"Course {i} completed: {result['title']}")
```

## Error Handling

### Robust Error Handling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CourseAPIClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
        
        return session
    
    def create_course(self, course_data):
        try:
            response = self.session.post(
                f"{self.base_url}/courses",
                json=course_data,
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                raise ValueError(f"Invalid course data: {error_data['message']}")
            elif response.status_code == 401:
                raise PermissionError("Invalid API key")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded. Please wait and retry.")
            else:
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            raise Exception("Request timeout. Please try again.")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error. Please check your network.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def get_generation_status(self, course_id):
        try:
            response = self.session.get(
                f"{self.base_url}/courses/{course_id}/generation-status",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ValueError(f"Course {course_id} not found")
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get generation status: {e}")
```

### Rate Limiting Handling

```python
import time
from functools import wraps

def handle_rate_limit(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        if attempt < max_retries - 1:
                            # Extract retry-after header if available
                            retry_after = int(e.response.headers.get('retry-after', base_delay * (2 ** attempt)))
                            print(f"Rate limited. Waiting {retry_after} seconds...")
                            time.sleep(retry_after)
                            continue
                    raise
            return None
        return wrapper
    return decorator

class RateLimitedClient(CourseAPIClient):
    @handle_rate_limit(max_retries=3, base_delay=2)
    def create_course(self, course_data):
        return super().create_course(course_data)
    
    @handle_rate_limit(max_retries=3, base_delay=1)
    def get_generation_status(self, course_id):
        return super().get_generation_status(course_id)
```

## Integration Examples

### LMS Integration

Example integration with a Learning Management System:

```python
class LMSIntegration:
    def __init__(self, course_api_client, lms_client):
        self.course_api = course_api_client
        self.lms = lms_client
    
    def import_course_to_lms(self, course_title, course_config):
        """Create course via API and import to LMS"""
        
        # 1. Create course using the API
        course_data = {
            "title": course_title,
            **course_config
        }
        
        created_course = self.course_api.create_course(course_data)
        course_id = created_course['id']
        
        # 2. Monitor generation
        final_course = self._wait_for_completion(course_id)
        
        # 3. Export in LMS-compatible format
        export_response = self.course_api.export_course(
            course_id,
            format="scorm2004"
        )
        
        # 4. Download and import to LMS
        course_package = self._download_package(export_response['download_url'])
        lms_course_id = self.lms.import_scorm_package(course_package)
        
        # 5. Update course metadata in LMS
        self.lms.update_course_metadata(lms_course_id, {
            'generated_by': 'Course Generation Platform',
            'api_course_id': course_id,
            'quality_score': final_course['quality_metrics']['pedagogical_alignment']
        })
        
        return {
            'api_course_id': course_id,
            'lms_course_id': lms_course_id,
            'course_data': final_course
        }
    
    def _wait_for_completion(self, course_id):
        """Wait for course generation to complete"""
        while True:
            status = self.course_api.get_generation_status(course_id)
            
            if status['status'] == 'completed':
                return self.course_api.get_course(course_id)
            elif status['status'] == 'failed':
                raise Exception(f"Course generation failed: {status.get('error_message')}")
            
            time.sleep(30)
    
    def _download_package(self, download_url):
        """Download the course package"""
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            return temp_file.name
```

### Webhook Integration

Handle real-time updates using webhooks:

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

class WebhookHandler:
    def __init__(self, webhook_secret):
        self.webhook_secret = webhook_secret
        self.event_handlers = {}
    
    def register_handler(self, event_type, handler_func):
        """Register a handler for specific event types"""
        self.event_handlers[event_type] = handler_func
    
    def verify_signature(self, payload, signature):
        """Verify webhook signature"""
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def handle_webhook(self, payload, signature):
        """Process incoming webhook"""
        if not self.verify_signature(payload, signature):
            raise ValueError("Invalid webhook signature")
        
        event_data = payload
        event_type = event_data.get('event_type')
        
        if event_type in self.event_handlers:
            self.event_handlers[event_type](event_data)
        else:
            print(f"Unhandled event type: {event_type}")

# Initialize webhook handler
webhook_handler = WebhookHandler(os.getenv('WEBHOOK_SECRET'))

# Register event handlers
def on_generation_completed(event_data):
    course_id = event_data['course_id']
    print(f"Course {course_id} generation completed")
    
    # Notify users, update database, etc.
    notify_course_ready(course_id)

def on_generation_failed(event_data):
    course_id = event_data['course_id']
    error_message = event_data.get('error_message')
    print(f"Course {course_id} generation failed: {error_message}")
    
    # Handle failure - notify admin, retry, etc.
    handle_generation_failure(course_id, error_message)

webhook_handler.register_handler('generation.completed', on_generation_completed)
webhook_handler.register_handler('generation.failed', on_generation_failed)

@app.route('/webhooks/courseplatform', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Signature-256')
    payload = request.get_data()
    
    try:
        webhook_handler.handle_webhook(payload, signature)
        return jsonify({'status': 'success'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal error'}), 500
```

## Performance Optimization

### Caching Strategies

```python
import redis
import json
from functools import wraps

class CachedCourseClient:
    def __init__(self, api_client, redis_client, cache_ttl=3600):
        self.api = api_client
        self.cache = redis_client
        self.cache_ttl = cache_ttl
    
    def get_course_cached(self, course_id):
        """Get course with caching"""
        cache_key = f"course:{course_id}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Fetch from API
        course_data = self.api.get_course(course_id)
        
        # Cache for future requests
        self.cache.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(course_data)
        )
        
        return course_data
    
    def invalidate_course_cache(self, course_id):
        """Invalidate cached course data"""
        cache_key = f"course:{course_id}"
        self.cache.delete(cache_key)

# Usage
redis_client = redis.Redis(host='localhost', port=6379, db=0)
cached_client = CachedCourseClient(course_api_client, redis_client)
```

### Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OptimizedAPIClient:
    def __init__(self, api_key, base_url, pool_connections=10, pool_maxsize=20):
        self.session = requests.Session()
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=Retry(
                total=3,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
        
        self.base_url = base_url
```

## Testing

### Unit Testing

```python
import unittest
from unittest.mock import Mock, patch
import requests_mock

class TestCourseAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-api-key"
        self.base_url = "https://api.test.com/v1"
        self.client = CourseAPIClient(self.api_key, self.base_url)
    
    @requests_mock.Mocker()
    def test_create_course_success(self, m):
        # Mock successful course creation
        m.post(
            f"{self.base_url}/courses",
            json={
                'id': 'test-course-id',
                'status': 'generating',
                'generation_task_id': 'task-123'
            },
            status_code=201
        )
        
        course_data = {
            'title': 'Test Course',
            'subject_domain': 'Test',
            'target_audience': {'proficiency_level': 'beginner'}
        }
        
        result = self.client.create_course(course_data)
        
        self.assertEqual(result['id'], 'test-course-id')
        self.assertEqual(result['status'], 'generating')
    
    @requests_mock.Mocker()
    def test_create_course_validation_error(self, m):
        # Mock validation error
        m.post(
            f"{self.base_url}/courses",
            json={
                'error': 'ValidationError',
                'message': 'Title is required'
            },
            status_code=400
        )
        
        course_data = {'subject_domain': 'Test'}  # Missing title
        
        with self.assertRaises(ValueError):
            self.client.create_course(course_data)

if __name__ == '__main__':
    unittest.main()
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API key is correct
   - Check header format: `X-API-Key: your-key`
   - Ensure key has required permissions

2. **Rate Limiting**
   - Implement exponential backoff
   - Monitor rate limit headers
   - Consider upgrading API plan

3. **Generation Timeouts**
   - Complex courses take longer to generate
   - Implement proper polling with timeouts
   - Monitor generation status regularly

4. **Network Issues**
   - Use connection pooling
   - Implement retry logic
   - Handle timeout exceptions

### Debug Tools

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Log all HTTP requests
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```

## Migration Guide

### Upgrading from v1.0 to v1.1

- New `content_preferences` field in course creation
- Enhanced quality metrics in responses
- Additional export formats supported

### Breaking Changes

None in v1.1. All v1.0 integrations remain compatible.

## Support and Resources

- **API Documentation**: https://docs.courseplatform.com/api
- **Developer Forum**: https://community.courseplatform.com
- **Status Page**: https://status.courseplatform.com
- **Support**: developers@courseplatform.com