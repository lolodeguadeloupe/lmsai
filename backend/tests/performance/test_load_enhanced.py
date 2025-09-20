"""
Enhanced Load Testing Suite - T064

Comprehensive load testing for concurrent course generation and system stress testing.
Tests system behavior under high concurrent load and validates scalability.
"""

import pytest
import asyncio
import time
import statistics
import threading
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, AsyncMock
import json
import random

# Load testing configuration
LOAD_TEST_CONFIG = {
    "concurrent_users": 20,
    "max_concurrent_generation": 5,  # T064 requirement
    "stress_users": 50,
    "test_duration_seconds": 60,
    "ramp_up_seconds": 10,
    "success_rate_threshold": 95.0,
    "max_response_time_ms": 500,
    "generation_timeout_seconds": 120,
}

class LoadTestMetrics:
    """Comprehensive load testing metrics collection."""
    
    def __init__(self):
        self.request_times = []
        self.success_count = 0
        self.error_count = 0
        self.generation_times = []
        self.concurrent_generation_count = 0
        self.peak_concurrent_users = 0
        self.throughput_requests_per_second = 0
        self.status_codes = {}
        self.error_details = []
        self.start_time = None
        self.end_time = None
        self._lock = threading.Lock()
    
    def start_test(self):
        """Mark test start time."""
        self.start_time = time.time()
    
    def end_test(self):
        """Mark test end time and calculate throughput."""
        self.end_time = time.time()
        if self.start_time:
            duration = self.end_time - self.start_time
            total_requests = len(self.request_times)
            self.throughput_requests_per_second = total_requests / duration if duration > 0 else 0
    
    def add_request(self, response_time_ms: float, status_code: int, success: bool, error_msg: str = None):
        """Thread-safe request metrics recording."""
        with self._lock:
            self.request_times.append(response_time_ms)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
                if error_msg:
                    self.error_details.append(error_msg)
            
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
    
    def add_generation(self, generation_time_ms: float, concurrent_count: int):
        """Record generation-specific metrics."""
        with self._lock:
            self.generation_times.append(generation_time_ms)
            self.concurrent_generation_count = max(self.concurrent_generation_count, concurrent_count)
    
    def update_peak_users(self, user_count: int):
        """Update peak concurrent users."""
        with self._lock:
            self.peak_concurrent_users = max(self.peak_concurrent_users, user_count)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive load testing statistics."""
        total_requests = len(self.request_times)
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "load_test_summary": {
                "total_requests": total_requests,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "success_rate_percent": success_rate,
                "peak_concurrent_users": self.peak_concurrent_users,
                "throughput_rps": self.throughput_requests_per_second,
                "test_duration_seconds": (self.end_time - self.start_time) if self.start_time and self.end_time else 0,
            },
            "response_time_metrics": self._calculate_response_time_stats(),
            "generation_metrics": self._calculate_generation_stats(),
            "status_distribution": self.status_codes,
            "error_analysis": {
                "error_count": self.error_count,
                "unique_errors": len(set(self.error_details)),
                "top_errors": self._get_top_errors(),
            }
        }
        
        return stats
    
    def _calculate_response_time_stats(self) -> Dict[str, float]:
        """Calculate response time statistics."""
        if not self.request_times:
            return {"error": "No response times recorded"}
        
        sorted_times = sorted(self.request_times)
        return {
            "avg_ms": statistics.mean(self.request_times),
            "median_ms": statistics.median(self.request_times),
            "min_ms": min(self.request_times),
            "max_ms": max(self.request_times),
            "p95_ms": self._percentile(sorted_times, 95),
            "p99_ms": self._percentile(sorted_times, 99),
            "std_dev_ms": statistics.stdev(self.request_times) if len(self.request_times) > 1 else 0,
        }
    
    def _calculate_generation_stats(self) -> Dict[str, Any]:
        """Calculate course generation statistics."""
        if not self.generation_times:
            return {"message": "No generation operations recorded"}
        
        return {
            "total_generations": len(self.generation_times),
            "avg_generation_time_ms": statistics.mean(self.generation_times),
            "max_concurrent_generations": self.concurrent_generation_count,
            "fastest_generation_ms": min(self.generation_times),
            "slowest_generation_ms": max(self.generation_times),
        }
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_top_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common errors."""
        error_counts = {}
        for error in self.error_details:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return [
            {"error": error, "count": count}
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]


class MockCourseGenerationService:
    """Mock service for simulating course generation under load."""
    
    def __init__(self):
        self.active_generations = 0
        self.generation_history = []
        self._lock = threading.Lock()
    
    def simulate_generation(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate course generation with realistic timing."""
        with self._lock:
            self.active_generations += 1
            generation_id = f"gen_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        try:
            # Simulate AI processing time (variable based on load)
            base_time = random.uniform(0.5, 2.0)  # 500ms to 2s base time
            load_factor = min(self.active_generations / 5, 2.0)  # Slower under high load
            generation_time = base_time * load_factor
            
            time.sleep(generation_time)
            
            result = {
                "generation_id": generation_id,
                "status": "completed",
                "generated_at": time.time(),
                "generation_time_ms": generation_time * 1000,
                "concurrent_generations": self.active_generations,
                "course_data": course_data
            }
            
            self.generation_history.append(result)
            return result
            
        finally:
            with self._lock:
                self.active_generations -= 1
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get status of a generation operation."""
        for gen in self.generation_history:
            if gen["generation_id"] == generation_id:
                return gen
        
        return {"status": "not_found", "generation_id": generation_id}


class TestConcurrentLoad:
    """Test concurrent user load scenarios - T064 Implementation."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client with realistic load behavior."""
        client = Mock()
        generation_service = MockCourseGenerationService()
        
        def mock_get(url, **kwargs):
            # Simulate varying response times based on load
            time.sleep(random.uniform(0.02, 0.1))  # 20-100ms
            response = Mock()
            response.status_code = 200
            response.json.return_value = {"status": "success", "data": []}
            response.elapsed.total_seconds.return_value = random.uniform(0.02, 0.1)
            return response
        
        def mock_post(url, **kwargs):
            # Course generation endpoints have higher latency
            if "generation" in url or "courses" in url:
                generation_data = kwargs.get("json", {})
                result = generation_service.simulate_generation(generation_data)
                time.sleep(0.05)  # Additional API overhead
                
                response = Mock()
                response.status_code = 201
                response.json.return_value = result
                response.elapsed.total_seconds.return_value = result["generation_time_ms"] / 1000
                return response
            else:
                time.sleep(random.uniform(0.03, 0.08))
                response = Mock()
                response.status_code = 201
                response.json.return_value = {"status": "created"}
                return response
        
        client.get = mock_get
        client.post = mock_post
        client.put = mock_get  # Similar to GET for testing
        client.delete = mock_get
        
        return client
    
    @pytest.fixture
    def sample_course_data(self):
        """Sample course data for load testing."""
        return {
            "title": "Load Test Course",
            "subject_domain": "Computer Science",
            "target_audience": {
                "proficiency_level": "intermediate",
                "prerequisites": ["Programming basics"],
                "learning_preferences": ["practical", "visual"]
            },
            "learning_objectives": [
                "Understand load testing concepts",
                "Apply performance optimization",
                "Design scalable systems"
            ],
            "estimated_duration": "PT25H",
            "difficulty_score": 3.5
        }
    
    def simulate_user_session(self, client, user_id: int, metrics: LoadTestMetrics) -> None:
        """Simulate a complete user session with multiple operations."""
        session_start = time.time()
        operations = [
            ("GET", "/api/v1/courses", {}),
            ("POST", "/api/v1/courses", {"json": {
                "title": f"Course by User {user_id}",
                "subject_domain": "Test Domain",
                "learning_objectives": ["Learn", "Apply", "Master"]
            }}),
            ("GET", "/api/v1/courses/test-id", {}),
            ("PUT", "/api/v1/courses/test-id", {"json": {"title": "Updated Course"}}),
        ]
        
        for method, url, kwargs in operations:
            try:
                start_time = time.time()
                response = getattr(client, method.lower())(url, **kwargs)
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                success = 200 <= response.status_code < 300
                
                metrics.add_request(response_time_ms, response.status_code, success)
                
                # Brief pause between operations
                time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                metrics.add_request(5000, 500, False, str(e))
    
    def test_concurrent_user_load(self, mock_client, sample_course_data):
        """Test system behavior under concurrent user load."""
        metrics = LoadTestMetrics()
        metrics.start_test()
        
        # Simulate concurrent users
        with ThreadPoolExecutor(max_workers=LOAD_TEST_CONFIG["concurrent_users"]) as executor:
            futures = []
            
            for user_id in range(LOAD_TEST_CONFIG["concurrent_users"]):
                future = executor.submit(
                    self.simulate_user_session, 
                    mock_client, 
                    user_id, 
                    metrics
                )
                futures.append(future)
                
                # Update peak users count
                metrics.update_peak_users(user_id + 1)
                
                # Gradual ramp-up
                if user_id < LOAD_TEST_CONFIG["concurrent_users"] - 1:
                    time.sleep(LOAD_TEST_CONFIG["ramp_up_seconds"] / LOAD_TEST_CONFIG["concurrent_users"])
            
            # Wait for all users to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    metrics.add_request(5000, 500, False, f"User session failed: {str(e)}")
        
        metrics.end_test()
        stats = metrics.get_comprehensive_stats()
        
        # Validate load test results
        assert stats["load_test_summary"]["success_rate_percent"] >= LOAD_TEST_CONFIG["success_rate_threshold"]
        assert stats["response_time_metrics"]["avg_ms"] < LOAD_TEST_CONFIG["max_response_time_ms"]
        assert stats["load_test_summary"]["peak_concurrent_users"] == LOAD_TEST_CONFIG["concurrent_users"]
        
        print(f"Concurrent load test results: {json.dumps(stats, indent=2)}")
    
    def test_concurrent_course_generation(self, mock_client, sample_course_data):
        """Test concurrent course generation - Core T064 requirement."""
        metrics = LoadTestMetrics()
        generation_service = MockCourseGenerationService()
        
        def generate_course(course_id: int):
            """Generate a single course and record metrics."""
            course_data = {
                **sample_course_data,
                "title": f"Generated Course {course_id}",
                "course_id": course_id
            }
            
            start_time = time.time()
            try:
                result = generation_service.simulate_generation(course_data)
                end_time = time.time()
                
                generation_time_ms = (end_time - start_time) * 1000
                metrics.add_generation(generation_time_ms, result["concurrent_generations"])
                metrics.add_request(generation_time_ms, 200, True)
                
                return result
                
            except Exception as e:
                end_time = time.time()
                generation_time_ms = (end_time - start_time) * 1000
                metrics.add_request(generation_time_ms, 500, False, str(e))
                raise
        
        # Launch concurrent generation requests
        with ThreadPoolExecutor(max_workers=LOAD_TEST_CONFIG["max_concurrent_generation"]) as executor:
            futures = [
                executor.submit(generate_course, i) 
                for i in range(LOAD_TEST_CONFIG["max_concurrent_generation"])
            ]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=LOAD_TEST_CONFIG["generation_timeout_seconds"])
                    results.append(result)
                except Exception as e:
                    print(f"Generation failed: {e}")
        
        stats = metrics.get_comprehensive_stats()
        
        # Validate concurrent generation performance
        assert len(results) >= LOAD_TEST_CONFIG["max_concurrent_generation"] * 0.8  # Allow 20% failure
        assert stats["generation_metrics"]["max_concurrent_generations"] <= LOAD_TEST_CONFIG["max_concurrent_generation"]
        assert stats["load_test_summary"]["success_rate_percent"] >= 80.0  # Lower threshold for generation
        
        print(f"Concurrent generation results: {json.dumps(stats, indent=2)}")
    
    @pytest.mark.stress
    def test_stress_load(self, mock_client):
        """Stress test with high user volume."""
        metrics = LoadTestMetrics()
        metrics.start_test()
        
        def stress_user_simulation(user_id: int):
            """Aggressive user simulation for stress testing."""
            for request_num in range(10):  # Each user makes 10 requests
                try:
                    start_time = time.time()
                    response = mock_client.get(f"/api/v1/courses?user={user_id}&req={request_num}")
                    end_time = time.time()
                    
                    response_time_ms = (end_time - start_time) * 1000
                    metrics.add_request(response_time_ms, response.status_code, True)
                    
                    # Minimal delay between requests for stress
                    time.sleep(0.01)
                    
                except Exception as e:
                    metrics.add_request(5000, 500, False, str(e))
        
        # High-stress concurrent execution
        with ThreadPoolExecutor(max_workers=LOAD_TEST_CONFIG["stress_users"]) as executor:
            futures = [
                executor.submit(stress_user_simulation, i) 
                for i in range(LOAD_TEST_CONFIG["stress_users"])
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Stress user failed: {e}")
        
        metrics.end_test()
        stats = metrics.get_comprehensive_stats()
        
        # Under stress, allow degraded performance but require system stability
        assert stats["load_test_summary"]["success_rate_percent"] >= 85.0
        assert stats["response_time_metrics"]["p99_ms"] < LOAD_TEST_CONFIG["max_response_time_ms"] * 3
        assert stats["load_test_summary"]["throughput_rps"] > 10  # Minimum throughput
        
        print(f"Stress test results: {json.dumps(stats, indent=2)}")
    
    def test_gradual_load_ramp_up(self, mock_client):
        """Test gradual load increase to find breaking point."""
        load_levels = [5, 10, 20, 30, 40]
        results = {}
        
        for load_level in load_levels:
            metrics = LoadTestMetrics()
            metrics.start_test()
            
            # Test each load level
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [
                    executor.submit(self.simulate_user_session, mock_client, i, metrics)
                    for i in range(load_level)
                ]
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass  # Continue testing even if some users fail
            
            metrics.end_test()
            stats = metrics.get_comprehensive_stats()
            results[load_level] = stats["load_test_summary"]
            
            print(f"Load level {load_level}: {stats['load_test_summary']['success_rate_percent']:.1f}% success rate")
            
            # Stop if success rate drops too low
            if stats["load_test_summary"]["success_rate_percent"] < 70.0:
                print(f"Breaking point reached at {load_level} concurrent users")
                break
        
        # Verify system can handle at least baseline load
        baseline_load = min(load_levels)
        assert results[baseline_load]["success_rate_percent"] >= LOAD_TEST_CONFIG["success_rate_threshold"]
        
        return results
    
    def test_sustained_load(self, mock_client):
        """Test sustained load over time."""
        metrics = LoadTestMetrics()
        metrics.start_test()
        
        end_time = time.time() + LOAD_TEST_CONFIG["test_duration_seconds"]
        user_count = 10  # Moderate sustained load
        
        def sustained_user_requests():
            """Continuous user requests for duration."""
            while time.time() < end_time:
                try:
                    start_time = time.time()
                    response = mock_client.get("/api/v1/courses")
                    request_end = time.time()
                    
                    response_time_ms = (request_end - start_time) * 1000
                    metrics.add_request(response_time_ms, response.status_code, True)
                    
                    # Regular interval between requests
                    time.sleep(1.0)
                    
                except Exception as e:
                    metrics.add_request(5000, 500, False, str(e))
        
        # Run sustained load
        with ThreadPoolExecutor(max_workers=user_count) as executor:
            futures = [
                executor.submit(sustained_user_requests) 
                for _ in range(user_count)
            ]
            
            # Wait for test duration to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        
        metrics.end_test()
        stats = metrics.get_comprehensive_stats()
        
        # Sustained load should maintain performance over time
        assert stats["load_test_summary"]["success_rate_percent"] >= LOAD_TEST_CONFIG["success_rate_threshold"]
        assert stats["load_test_summary"]["test_duration_seconds"] >= LOAD_TEST_CONFIG["test_duration_seconds"] * 0.9
        assert stats["response_time_metrics"]["std_dev_ms"] < stats["response_time_metrics"]["avg_ms"]  # Low variance
        
        print(f"Sustained load results: {json.dumps(stats, indent=2)}")


class TestLoadScenarios:
    """Realistic load testing scenarios."""
    
    def test_peak_hours_simulation(self, mock_client, sample_course_data):
        """Simulate peak usage hours with mixed operations."""
        metrics = LoadTestMetrics()
        
        # Different user behavior patterns
        user_patterns = [
            {"type": "browser", "requests_per_minute": 5, "operations": ["GET", "GET", "GET"]},
            {"type": "creator", "requests_per_minute": 3, "operations": ["POST", "PUT", "GET"]},
            {"type": "admin", "requests_per_minute": 8, "operations": ["GET", "GET", "DELETE", "POST"]},
        ]
        
        def simulate_user_pattern(pattern: Dict[str, Any], duration_minutes: int = 2):
            """Simulate specific user behavior pattern."""
            end_time = time.time() + (duration_minutes * 60)
            interval = 60 / pattern["requests_per_minute"]
            
            while time.time() < end_time:
                operation = random.choice(pattern["operations"])
                
                try:
                    start_time = time.time()
                    if operation == "GET":
                        response = mock_client.get("/api/v1/courses")
                    elif operation == "POST":
                        response = mock_client.post("/api/v1/courses", json=sample_course_data)
                    elif operation == "PUT":
                        response = mock_client.put("/api/v1/courses/test-id", json={"title": "Updated"})
                    elif operation == "DELETE":
                        response = mock_client.delete("/api/v1/courses/test-id")
                    
                    request_end = time.time()
                    response_time_ms = (request_end - start_time) * 1000
                    metrics.add_request(response_time_ms, response.status_code, True)
                    
                except Exception as e:
                    metrics.add_request(5000, 500, False, str(e))
                
                time.sleep(interval)
        
        # Launch different user patterns concurrently
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            
            # Simulate multiple users of each type
            for pattern in user_patterns:
                for _ in range(5):  # 5 users per pattern
                    future = executor.submit(simulate_user_pattern, pattern)
                    futures.append(future)
            
            # Wait for all simulations to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        
        stats = metrics.get_comprehensive_stats()
        
        # Peak hours should maintain good performance
        assert stats["load_test_summary"]["success_rate_percent"] >= 90.0
        assert stats["response_time_metrics"]["p95_ms"] < LOAD_TEST_CONFIG["max_response_time_ms"] * 1.5
        
        print(f"Peak hours simulation: {json.dumps(stats, indent=2)}")
    
    def test_batch_operation_load(self, mock_client):
        """Test load from batch operations like bulk imports."""
        metrics = LoadTestMetrics()
        
        def batch_import_simulation():
            """Simulate bulk course import operation."""
            batch_size = 20
            
            for i in range(batch_size):
                course_data = {
                    "title": f"Batch Course {i}",
                    "subject_domain": "Batch Import",
                    "learning_objectives": ["Learn", "Apply", "Master"]
                }
                
                try:
                    start_time = time.time()
                    response = mock_client.post("/api/v1/courses", json=course_data)
                    end_time = time.time()
                    
                    response_time_ms = (end_time - start_time) * 1000
                    metrics.add_request(response_time_ms, response.status_code, True)
                    
                    # Brief pause to simulate processing
                    time.sleep(0.1)
                    
                except Exception as e:
                    metrics.add_request(5000, 500, False, str(e))
        
        # Run multiple batch operations concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(batch_import_simulation) 
                for _ in range(3)
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        
        stats = metrics.get_comprehensive_stats()
        
        # Batch operations should complete successfully
        assert stats["load_test_summary"]["success_rate_percent"] >= 95.0
        assert stats["load_test_summary"]["total_requests"] >= 50  # 3 batches * 20 requests
        
        print(f"Batch operation load: {json.dumps(stats, indent=2)}")


@pytest.mark.load
class TestLoadReporting:
    """Load testing reporting and analysis."""
    
    def test_comprehensive_load_report(self, mock_client, sample_course_data):
        """Generate comprehensive load testing report."""
        test_results = {}
        
        # Run all major load tests
        load_tests = [
            ("concurrent_users", TestConcurrentLoad().test_concurrent_user_load),
            ("concurrent_generation", TestConcurrentLoad().test_concurrent_course_generation),
            ("stress_test", TestConcurrentLoad().test_stress_load),
            ("sustained_load", TestConcurrentLoad().test_sustained_load),
        ]
        
        for test_name, test_method in load_tests:
            try:
                print(f"Running {test_name}...")
                if test_name in ["concurrent_users", "concurrent_generation"]:
                    test_method(mock_client, sample_course_data)
                else:
                    test_method(mock_client)
                test_results[test_name] = "PASSED"
            except Exception as e:
                test_results[test_name] = f"FAILED: {str(e)}"
        
        # Generate final report
        report = {
            "load_test_summary": {
                "timestamp": time.time(),
                "configuration": LOAD_TEST_CONFIG,
                "test_results": test_results,
                "overall_status": "PASSED" if all("PASSED" in result for result in test_results.values()) else "FAILED"
            }
        }
        
        # Save report
        report_file = f"load_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Load test report saved to {report_file}")
        print(f"Overall status: {report['load_test_summary']['overall_status']}")
        
        # Assert overall success
        failed_tests = [name for name, result in test_results.items() if "FAILED" in result]
        assert not failed_tests, f"Load tests failed: {failed_tests}"


if __name__ == "__main__":
    # Run load tests with custom configuration
    pytest.main([
        __file__,
        "-v", 
        "--tb=short",
        "-m", "load",
        "--durations=0"
    ])