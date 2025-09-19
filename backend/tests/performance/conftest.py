"""
Performance test configuration and fixtures.
Specialized setup for performance testing scenarios.
"""
import pytest
import asyncio
import psutil
import time
import json
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import existing test configuration
from ..conftest import sample_course_request, sample_course_id

# Performance test configuration
PERFORMANCE_CONFIG = {
    "api_timeout": 30.0,  # 30 seconds for API calls
    "p95_threshold_ms": 200,  # 95th percentile response time threshold
    "p99_threshold_ms": 500,  # 99th percentile response time threshold
    "concurrent_users": 100,  # Number of concurrent users for load testing
    "test_duration": 60,  # Test duration in seconds
    "ramp_up_time": 10,  # Ramp up time in seconds
    "memory_limit_mb": 1024,  # Memory limit in MB
    "cpu_limit_percent": 80,  # CPU usage limit
}

# Database configuration for performance tests
PERF_DATABASE_URL = "sqlite:///./performance_test.db"


@pytest.fixture(scope="session")
def performance_config():
    """Performance testing configuration."""
    return PERFORMANCE_CONFIG


@pytest.fixture(scope="session")
def perf_engine():
    """Create performance test database engine with optimized settings."""
    try:
        from src.database import Base
    except ImportError:
        pytest.skip("Database models not implemented yet")
    
    engine = create_engine(
        PERF_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_size=20,  # Larger pool for performance tests
        max_overflow=30,
        pool_pre_ping=True,
        echo=False  # Disable SQL logging for performance
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def perf_db_session(perf_engine):
    """Create performance test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=perf_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def perf_client(perf_db_session):
    """Create performance test client with dependency override."""
    try:
        from src.main import app
        from src.database import get_db
    except ImportError:
        pytest.skip("FastAPI app not implemented yet")

    def override_get_db():
        try:
            yield perf_db_session
        finally:
            pass  # Don't close session for performance tests

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
async def async_client(perf_client):
    """Create async HTTP client for performance testing."""
    async with httpx.AsyncClient(
        app=perf_client.app,
        base_url="http://testserver",
        timeout=PERFORMANCE_CONFIG["api_timeout"]
    ) as client:
        yield client


@pytest.fixture
def performance_monitor():
    """Resource monitoring fixture for performance tests."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.initial_memory = None
            self.peak_memory = None
            self.initial_cpu = None
            self.cpu_samples = []
            self.process = psutil.Process()
            
        def start_monitoring(self):
            """Start performance monitoring."""
            self.start_time = time.time()
            self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            self.initial_cpu = self.process.cpu_percent()
            self.cpu_samples = []
            
        def sample_resources(self):
            """Sample current resource usage."""
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            current_cpu = self.process.cpu_percent()
            
            if self.peak_memory is None or current_memory > self.peak_memory:
                self.peak_memory = current_memory
                
            self.cpu_samples.append(current_cpu)
            
        def stop_monitoring(self) -> Dict[str, Any]:
            """Stop monitoring and return performance metrics."""
            self.end_time = time.time()
            
            return {
                "execution_time_seconds": self.end_time - self.start_time,
                "initial_memory_mb": self.initial_memory,
                "peak_memory_mb": self.peak_memory or self.initial_memory,
                "memory_increase_mb": (self.peak_memory or self.initial_memory) - self.initial_memory,
                "average_cpu_percent": sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
                "max_cpu_percent": max(self.cpu_samples) if self.cpu_samples else 0,
                "cpu_samples_count": len(self.cpu_samples)
            }
    
    return PerformanceMonitor()


@pytest.fixture
def response_timer():
    """Response time measurement fixture."""
    class ResponseTimer:
        def __init__(self):
            self.start_time = None
            self.response_times = []
            
        @asynccontextmanager
        async def measure(self):
            """Context manager to measure response time."""
            start = time.perf_counter()
            try:
                yield
            finally:
                end = time.perf_counter()
                response_time_ms = (end - start) * 1000
                self.response_times.append(response_time_ms)
                
        def get_stats(self) -> Dict[str, float]:
            """Get response time statistics."""
            if not self.response_times:
                return {}
                
            sorted_times = sorted(self.response_times)
            count = len(sorted_times)
            
            return {
                "count": count,
                "min_ms": min(sorted_times),
                "max_ms": max(sorted_times),
                "mean_ms": sum(sorted_times) / count,
                "median_ms": sorted_times[count // 2],
                "p95_ms": sorted_times[int(count * 0.95)] if count >= 20 else sorted_times[-1],
                "p99_ms": sorted_times[int(count * 0.99)] if count >= 100 else sorted_times[-1],
            }
            
        def reset(self):
            """Reset collected response times."""
            self.response_times = []
    
    return ResponseTimer()


@pytest.fixture
def load_test_data():
    """Generate test data for load testing."""
    def generate_course_requests(count: int = 100):
        """Generate multiple course creation requests."""
        requests = []
        for i in range(count):
            request = {
                "title": f"Load Test Course {i+1}",
                "description": f"This is a load test course generated for performance testing - iteration {i+1}",
                "subject_domain": "COMPUTER_SCIENCE",
                "target_audience": "BEGINNER",
                "difficulty_level": "EASY",
                "estimated_duration_hours": 10,
                "learning_objectives": [
                    f"Learn basic concepts - iteration {i+1}",
                    f"Apply practical skills - iteration {i+1}",
                    f"Complete exercises - iteration {i+1}"
                ]
            }
            requests.append(request)
        return requests
    
    return {
        "course_requests": generate_course_requests(),
        "course_ids": [f"550e8400-e29b-41d4-a716-{str(i).zfill(12)}" for i in range(100)]
    }


@pytest.fixture
def performance_report():
    """Performance test reporting fixture."""
    class PerformanceReport:
        def __init__(self):
            self.test_results = {}
            self.start_time = datetime.now()
            
        def add_test_result(self, test_name: str, metrics: Dict[str, Any]):
            """Add test result to the report."""
            self.test_results[test_name] = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }
            
        def add_benchmark_result(self, test_name: str, benchmark_stats: Dict[str, Any]):
            """Add pytest-benchmark result to the report."""
            self.test_results[test_name] = {
                "timestamp": datetime.now().isoformat(),
                "benchmark": benchmark_stats
            }
            
        def generate_report(self) -> Dict[str, Any]:
            """Generate final performance report."""
            end_time = datetime.now()
            
            return {
                "test_session": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": (end_time - self.start_time).total_seconds()
                },
                "performance_config": PERFORMANCE_CONFIG,
                "test_results": self.test_results,
                "summary": self._generate_summary()
            }
            
        def _generate_summary(self) -> Dict[str, Any]:
            """Generate test summary."""
            total_tests = len(self.test_results)
            passed_tests = 0
            failed_tests = 0
            
            for test_name, result in self.test_results.items():
                # Simple pass/fail based on presence of metrics
                if "metrics" in result or "benchmark" in result:
                    passed_tests += 1
                else:
                    failed_tests += 1
                    
            return {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0
            }
            
        def save_report(self, filename: str = None):
            """Save performance report to file."""
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"performance_report_{timestamp}.json"
                
            report = self.generate_report()
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
                
            return filename
    
    return PerformanceReport()


@pytest.fixture(autouse=True)
def performance_test_setup(performance_report, request):
    """Auto-setup for performance tests."""
    test_name = request.node.name
    
    # Setup
    yield
    
    # Teardown - this runs after each test
    # You can access test results here if needed
    pass


# Async helpers for concurrent testing
async def run_concurrent_requests(client: httpx.AsyncClient, requests: list, max_concurrent: int = 10):
    """Run multiple requests concurrently with controlled concurrency."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_request(request_func):
        async with semaphore:
            return await request_func()
    
    tasks = [limited_request(req) for req in requests]
    return await asyncio.gather(*tasks, return_exceptions=True)


def assert_performance_thresholds(stats: Dict[str, float], config: Dict[str, Any]):
    """Assert that performance stats meet configured thresholds."""
    if "p95_ms" in stats:
        assert stats["p95_ms"] <= config["p95_threshold_ms"], \
            f"P95 response time {stats['p95_ms']:.1f}ms exceeds threshold {config['p95_threshold_ms']}ms"
    
    if "p99_ms" in stats:
        assert stats["p99_ms"] <= config["p99_threshold_ms"], \
            f"P99 response time {stats['p99_ms']:.1f}ms exceeds threshold {config['p99_threshold_ms']}ms"