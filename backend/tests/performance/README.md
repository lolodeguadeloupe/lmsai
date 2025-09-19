# Performance Testing Suite

Comprehensive performance testing framework for the course generation platform, designed to validate all performance requirements and provide actionable optimization insights.

## 🎯 Performance Targets

Based on the project requirements, the system must meet these performance targets:

- **API Response Time**: <200ms (95th percentile)
- **Chapter Generation**: <2 minutes per chapter
- **Concurrent Operations**: 100 simultaneous users
- **Success Rate**: 95% minimum
- **Memory Usage**: <1GB under normal load
- **CPU Usage**: <80% under peak load

## 📁 Test Structure

```
tests/performance/
├── conftest.py              # Performance test configuration and fixtures
├── benchmarks.py            # Benchmarking utilities and helpers
├── test_api_performance.py  # API endpoint performance tests
├── test_load.py            # Load testing and concurrent operations
├── locustfile.py           # Locust-based web load testing
└── README.md               # This documentation
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install performance testing dependencies
pip install pytest pytest-asyncio pytest-benchmark httpx psutil locust

# Or install from requirements.txt (already includes these)
pip install -r requirements.txt
```

### Running Tests

#### 1. API Performance Tests
Test individual API endpoint performance:

```bash
# Run all API performance tests
pytest tests/performance/test_api_performance.py -v

# Run specific test class
pytest tests/performance/test_api_performance.py::TestAPIPerformance -v

# Run with benchmark output
pytest tests/performance/test_api_performance.py --benchmark-only
```

#### 2. Load Tests
Test concurrent operations and sustained load:

```bash
# Run all load tests
pytest tests/performance/test_load.py -v

# Run concurrent load tests only
pytest tests/performance/test_load.py::TestConcurrentLoad -v

# Run with custom concurrency
PERFORMANCE_CONCURRENT_USERS=50 pytest tests/performance/test_load.py -v
```

#### 3. Web-based Load Testing with Locust
Interactive web-based load testing:

```bash
# Start Locust web interface
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Run headless with specific parameters
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 300s --headless
```

#### 4. Complete Performance Suite
Run all performance tests with reporting:

```bash
# Run custom performance test script
python scripts/run_performance_tests.py --suite all --duration 60 --concurrent-users 100

# Run API tests only
python scripts/run_performance_tests.py --suite api

# Run with verbose output
python scripts/run_performance_tests.py --suite all --verbose
```

## 🔧 Configuration

### Environment Variables

Configure test behavior using environment variables:

```bash
# Test duration (seconds)
export PERFORMANCE_TEST_DURATION=60

# Concurrent users for load tests
export PERFORMANCE_CONCURRENT_USERS=100

# API timeout (seconds)
export PERFORMANCE_API_TIMEOUT=30

# Memory limit (MB)
export PERFORMANCE_MEMORY_LIMIT=1024

# CPU limit (percentage)
export PERFORMANCE_CPU_LIMIT=80
```

### Test Configuration

Modify `conftest.py` to adjust performance thresholds:

```python
PERFORMANCE_CONFIG = {
    "api_timeout": 30.0,
    "p95_threshold_ms": 200,    # P95 response time threshold
    "p99_threshold_ms": 500,    # P99 response time threshold
    "concurrent_users": 100,
    "test_duration": 60,
    "memory_limit_mb": 1024,
    "cpu_limit_percent": 80,
}
```

## 📊 Test Categories

### 1. API Performance Tests (`test_api_performance.py`)

Tests individual API endpoints for response time and throughput:

- **Health Endpoint**: Should respond in <50ms
- **Course CRUD Operations**: Create, read, update, delete performance
- **Generation Status**: Course generation monitoring performance
- **Export Operations**: File export performance (more lenient thresholds)
- **Resource Usage**: Memory and CPU usage under API load

**Key Metrics:**
- Response time percentiles (P95, P99)
- Requests per second
- Success rates
- Resource usage

### 2. Load Tests (`test_load.py`)

Tests system behavior under concurrent load:

- **Concurrent Creation**: 100 simultaneous course creations
- **Mixed Operations**: Realistic mix of read/write operations
- **Sustained Load**: Long-running tests with gradual user ramp-up
- **Spike Handling**: Sudden load increases and recovery
- **Resource Scaling**: Memory and CPU scaling with load

**Key Metrics:**
- Concurrent user handling
- Performance degradation under load
- System recovery characteristics
- Resource scaling efficiency

### 3. Locust Load Testing (`locustfile.py`)

Web-based load testing with realistic user behavior:

- **User Simulation**: Different user types (regular, power, admin)
- **Realistic Workflows**: Weighted task distribution
- **Interactive Testing**: Web UI for real-time monitoring
- **Scalable Testing**: Distributed load generation support

## 📈 Performance Monitoring

### Real-time Metrics

The test suite collects comprehensive metrics:

```python
# Response time statistics
{
    "min_ms": 45.2,
    "max_ms": 892.1,
    "mean_ms": 156.7,
    "median_ms": 142.3,
    "p95_ms": 278.9,
    "p99_ms": 445.6
}

# Throughput statistics
{
    "requests_per_second": 85.3,
    "successful_requests_per_second": 81.2
}

# Resource usage
{
    "peak_memory_mb": 456.7,
    "average_cpu_percent": 34.2,
    "memory_increase_mb": 123.4
}
```

### Performance Reports

Tests generate comprehensive reports:

- **JSON Reports**: Machine-readable metrics for CI/CD
- **HTML Reports**: Human-readable dashboards
- **Benchmark Reports**: Detailed performance comparisons
- **Real-time Dashboards**: Locust web interface

## 🎮 Usage Examples

### Example 1: API Performance Validation

```bash
# Test all API endpoints meet <200ms P95 requirement
pytest tests/performance/test_api_performance.py::TestAPIPerformance::test_health_endpoint_performance -v

# Expected output:
# ✅ P95 response time: 45ms (threshold: 50ms)
# ✅ Throughput: 156 req/s
# ✅ Success rate: 100.0%
```

### Example 2: Concurrent Load Testing

```bash
# Test 100 concurrent course creations
pytest tests/performance/test_load.py::TestConcurrentLoad::test_concurrent_course_creation -v

# Expected output:
# ✅ P95 response time: 756ms (threshold: 1000ms)
# ✅ Success rate: 97.2%
# ✅ Throughput: 23.4 req/s
```

### Example 3: Sustained Load Testing

```bash
# Run 60-second sustained load test
PERFORMANCE_TEST_DURATION=60 pytest tests/performance/test_load.py::TestSustainedLoad::test_sustained_api_load -v

# Expected output:
# ✅ P95 response time: 234ms (threshold: 500ms)
# ✅ Total requests: 4,567
# ✅ Success rate: 98.1%
```

### Example 4: Interactive Load Testing

```bash
# Start Locust web interface
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure: 100 users, spawn rate 10/s, run for 5 minutes
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Tests Timeout
```bash
# Increase timeout in pytest.ini or use environment variable
export PYTEST_TIMEOUT=600  # 10 minutes
```

#### 2. Memory Errors
```bash
# Reduce concurrent users
export PERFORMANCE_CONCURRENT_USERS=50

# Monitor system resources
htop  # or top
```

#### 3. Database Connection Issues
```bash
# Ensure test database is running
python -m alembic upgrade head

# Check database connection
python -c "from src.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 4. Import Errors
```bash
# Ensure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or run from project root
cd backend && python -m pytest tests/performance/
```

### Performance Debugging

#### 1. Enable Detailed Logging
```bash
pytest tests/performance/ -v -s --log-cli-level=DEBUG
```

#### 2. Profile Memory Usage
```python
# Add to test for memory profiling
import tracemalloc
tracemalloc.start()
# ... run test code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')[:10]
```

#### 3. Monitor Resource Usage
```bash
# Run alongside tests
watch -n 1 'ps aux | grep python | head -5'
```

## 📋 Test Checklist

Before deploying to production, ensure all performance tests pass:

- [ ] **API Performance**: All endpoints respond within thresholds
- [ ] **Concurrent Load**: System handles 100 concurrent users
- [ ] **Sustained Load**: Performance maintained over time
- [ ] **Resource Usage**: Memory and CPU within limits
- [ ] **Error Rates**: <5% error rate under load
- [ ] **Recovery**: System recovers from load spikes
- [ ] **Scalability**: Performance scales with user load

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests
on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run performance tests
        run: |
          python scripts/run_performance_tests.py --suite api --duration 30
      
      - name: Upload performance reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: performance_reports/
```

## 🎯 Performance Optimization

Based on test results, consider these optimizations:

### Database Optimization
- Add indexes for frequently queried fields
- Implement connection pooling
- Use read replicas for read-heavy operations

### API Optimization
- Implement response caching
- Add compression middleware
- Optimize serialization/deserialization

### Infrastructure Optimization
- Scale horizontally with load balancers
- Implement CDN for static content
- Use async processing for heavy operations

## 📚 Additional Resources

- [FastAPI Performance](https://fastapi.tiangolo.com/async/)
- [SQLAlchemy Performance](https://docs.sqlalchemy.org/en/14/core/performance.html)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [HTTP Load Testing Best Practices](https://blog.loadimpact.com/blog/http-load-testing-best-practices/)