# Course Generation Task Queue

This module implements a robust background task queue system using Celery for asynchronous course generation and processing operations.

## Features

### Core Tasks
- **Course Generation**: Complete course creation with chapters and assessments
- **Chapter Generation**: Individual chapter content generation (<2 min requirement)
- **Quality Validation**: Content quality assessment and metrics
- **Export Processing**: Multi-format course export (PDF, SCORM, JSON)
- **Chapter Regeneration**: Intelligent chapter improvement and regeneration

### Performance Requirements
- ✅ **<2 minute chapter generation** (FR-021)
- ✅ **100+ simultaneous operations** (FR-022)
- ✅ **95% success rate** target
- ✅ **Real-time progress tracking**
- ✅ **Automatic retry mechanism**

### Architecture
- **Redis**: Message broker and result backend
- **Celery**: Distributed task queue
- **Multiple Workers**: Specialized queues for different task types
- **Monitoring**: Flower dashboard and custom metrics

## Quick Start

### 1. Start Redis
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7.2-alpine

# Or using Docker Compose
docker compose -f docker-compose.tasks.yml up redis -d
```

### 2. Start Celery Workers
```bash
# All queues
python -m src.tasks.worker worker

# Specific queue
python -m src.tasks.worker worker --queues=chapter_generation

# With custom concurrency
python -m src.tasks.worker worker --concurrency=8
```

### 3. Start Monitoring
```bash
# Flower dashboard
python -m src.tasks.worker flower
# Access at http://localhost:5555

# CLI monitoring
python scripts/manage_tasks.py monitor
```

## Task Usage

### Course Generation
```python
from src.tasks import task_manager

# Start course generation
course_data = {
    "id": "course-123",
    "title": "Python Programming",
    "subject_domain": "Computer Science",
    "target_audience": {"proficiency_level": "beginner"},
    "learning_objectives": ["Learn Python basics", "Build applications"],
    "estimated_duration": "PT20H",
    "difficulty_score": 2.0
}

task_id = task_manager.start_course_generation(course_data)

# Monitor progress
status = task_manager.get_task_status(task_id)
print(f"Progress: {status['progress_percentage']}%")
```

### Chapter Generation
```python
# Generate individual chapter
chapter_data = {
    "id": "chapter-456",
    "course_id": "course-123",
    "title": "Variables and Data Types",
    "learning_objectives": ["Understand variables", "Use data types"],
    "estimated_duration": "PT2H",
    "complexity_level": 2.0
}

course_context = {"title": "Python Programming", "difficulty_score": 2.0}
task_id = task_manager.start_chapter_generation(chapter_data, course_context)
```

### Quality Validation
```python
# Validate content quality
validation_criteria = {
    "min_readability_score": 80.0,
    "min_pedagogical_alignment": 0.8,
    "check_bias": True
}

task_id = task_manager.start_quality_validation(content_data, validation_criteria)
```

### Export Processing
```python
# Export course to different formats
task_id = task_manager.start_course_export(
    course_data, 
    "pdf",  # or "scorm", "json"
    {"include_assessments": True}
)
```

### Chapter Regeneration
```python
# Regenerate chapter with improvements
task_id = task_manager.start_chapter_regeneration(
    "chapter-456",
    course_context,
    "Content too advanced for beginners",
    {"focus_area": "simplification"}
)
```

## Configuration

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_MAX_TASKS_PER_CHILD=1000

# Environment
ENVIRONMENT=production  # development, testing, production
```

### Queue Configuration
The system uses specialized queues for optimal performance:

- **course_generation**: Full course generation (priority: 5)
- **chapter_generation**: Individual chapters (priority: 8, highest)
- **quality_validation**: Content validation (priority: 6)
- **export**: Export processing (priority: 4)
- **default**: Miscellaneous tasks (priority: 3)

### Performance Tuning
```python
# In config.py
PERFORMANCE_SETTINGS = {
    "max_concurrent_courses": 100,  # FR-022 requirement
    "chapter_generation_limit": 120,  # 2 min requirement
    "worker_pool_size": 8,
    "prefetch_multiplier": 1,
    "max_retries": 3,
    "success_rate_target": 95.0
}
```

## Monitoring and Management

### CLI Management
```bash
# Check status
python scripts/manage_tasks.py status

# Monitor specific task
python scripts/manage_tasks.py get-task <task-id>

# Real-time monitoring
python scripts/manage_tasks.py monitor

# List active tasks
python scripts/manage_tasks.py active

# Performance analysis
python scripts/manage_tasks.py performance

# Test queue functionality
python scripts/manage_tasks.py test-queue
```

### Health Checks
```bash
# API health check
curl http://localhost:8000/health/tasks

# Worker status
python -m src.tasks.worker monitor
```

### Flower Dashboard
Access the web-based monitoring dashboard at `http://localhost:5555`:
- Real-time task monitoring
- Worker statistics
- Queue metrics
- Task history
- Performance graphs

## Error Handling

### Automatic Retries
- **Max retries**: 3 attempts per task
- **Exponential backoff**: 60s, 120s, 240s intervals
- **Jitter**: Randomized delays to prevent thundering herd
- **Circuit breaker**: Automatic failure isolation

### Error Recovery
```python
# Check for failed tasks
status = task_manager.get_task_status(task_id)
if status["status"] == "failed":
    error_details = status["error_details"]
    retry_count = status["retry_count"]
    
    # Handle based on error type
    if "timeout" in error_details.lower():
        # Increase time limits
        pass
    elif retry_count < 3:
        # Manual retry if needed
        pass
```

### Common Issues
1. **Worker Not Available**: Check Redis connection and worker processes
2. **Task Timeout**: Increase time limits or optimize task logic
3. **Memory Issues**: Reduce worker concurrency or increase limits
4. **High Failure Rate**: Check error logs and validation logic

## Performance Optimization

### Scaling Workers
```yaml
# docker-compose.tasks.yml
celery-worker-chapter:
  deploy:
    replicas: 3  # Scale horizontally
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
```

### Queue Optimization
- **Priority queues**: Critical tasks processed first
- **Dedicated workers**: Specialized workers per task type
- **Load balancing**: Fair task distribution
- **Resource isolation**: Prevent resource contention

### Monitoring Metrics
- **Task throughput**: Tasks completed per hour
- **Success rate**: Percentage of successful completions
- **Average execution time**: Per task type
- **Queue length**: Pending tasks
- **Worker utilization**: Resource usage

## Testing

### Unit Tests
```bash
# Run task-specific tests
pytest backend/tests/contract/test_task_queue.py

# Integration tests
pytest backend/tests/integration/test_task_queue_integration.py
```

### Load Testing
```python
# Test concurrent generation
python scripts/manage_tasks.py test-queue
```

### Performance Testing
```bash
# Monitor performance during load
python scripts/manage_tasks.py monitor --duration=300
```

## Production Deployment

### Docker Compose
```bash
# Start all services
docker compose -f docker-compose.tasks.yml up -d

# Scale workers
docker compose -f docker-compose.tasks.yml up -d --scale celery-worker-chapter=3
```

### Kubernetes
```yaml
# Example worker deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: celery-worker
  template:
    spec:
      containers:
      - name: worker
        image: course-platform-backend
        command: ["python", "-m", "src.tasks.worker", "worker"]
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Security Considerations
- **Redis Security**: Use authentication and TLS
- **Network Isolation**: Private networks for worker communication
- **Resource Limits**: Prevent resource exhaustion
- **Input Validation**: Sanitize task parameters
- **Access Control**: Restrict worker management endpoints

## Troubleshooting

### Common Commands
```bash
# Check Redis connectivity
redis-cli ping

# Inspect queues
redis-cli LLEN celery

# Clear failed tasks
celery -A src.tasks.celery_app purge

# Restart workers
docker compose -f docker-compose.tasks.yml restart celery-worker-chapter
```

### Log Analysis
```bash
# Worker logs
docker logs course-platform-worker-chapter

# Redis logs
docker logs course-platform-redis

# Application logs
tail -f logs/celery.log
```

### Performance Debugging
```python
# Profile task execution
from src.tasks.utils import get_task_queue_status
status = get_task_queue_status()
print(f"Queue capacity: {status['queue_capacity']}")
```

## API Integration

The task queue integrates with the FastAPI application through:

### Status Endpoints
- `GET /health/tasks` - Queue health check
- `GET /api/v1/courses/{id}/generation-status` - Task progress
- `POST /api/v1/courses/{id}/regenerate-chapter` - Chapter regeneration

### WebSocket Updates (Future)
Real-time progress updates for frontend applications:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks/{task_id}');
ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    updateProgressBar(progress.progress_percentage);
};
```

---

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review logs for error details
3. Use the CLI management tools for diagnostics
4. Monitor worker and queue statistics