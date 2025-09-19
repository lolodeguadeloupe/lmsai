"""
Performance benchmarking utilities for the course generation platform.
Provides comprehensive metrics collection and analysis tools.
"""
import time
import statistics
import psutil
import asyncio
from typing import Dict, List, Any, Callable, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json

import httpx
from sqlalchemy.orm import Session


@dataclass
class BenchmarkResult:
    """Container for benchmark results with comprehensive metrics."""
    name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    iterations: int
    success_count: int
    error_count: int
    
    # Response time metrics (in milliseconds)
    response_times: List[float] = field(default_factory=list)
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    mean_response_time: float = 0.0
    median_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # Throughput metrics
    requests_per_second: float = 0.0
    successful_requests_per_second: float = 0.0
    
    # Resource usage metrics
    initial_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    memory_increase_mb: float = 0.0
    average_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    
    # Error information
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        self._calculate_response_time_stats()
        self._calculate_throughput_stats()
    
    def _calculate_response_time_stats(self):
        """Calculate response time statistics."""
        if not self.response_times:
            return
            
        sorted_times = sorted(self.response_times)
        count = len(sorted_times)
        
        self.min_response_time = min(sorted_times)
        self.max_response_time = max(sorted_times)
        self.mean_response_time = statistics.mean(sorted_times)
        self.median_response_time = statistics.median(sorted_times)
        
        if count >= 20:
            self.p95_response_time = sorted_times[int(count * 0.95)]
        else:
            self.p95_response_time = self.max_response_time
            
        if count >= 100:
            self.p99_response_time = sorted_times[int(count * 0.99)]
        else:
            self.p99_response_time = self.max_response_time
    
    def _calculate_throughput_stats(self):
        """Calculate throughput statistics."""
        if self.duration_seconds > 0:
            self.requests_per_second = self.iterations / self.duration_seconds
            self.successful_requests_per_second = self.success_count / self.duration_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert benchmark result to dictionary."""
        return {
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "iterations": self.iterations,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "response_time_stats": {
                "min_ms": self.min_response_time,
                "max_ms": self.max_response_time,
                "mean_ms": self.mean_response_time,
                "median_ms": self.median_response_time,
                "p95_ms": self.p95_response_time,
                "p99_ms": self.p99_response_time,
            },
            "throughput_stats": {
                "requests_per_second": self.requests_per_second,
                "successful_requests_per_second": self.successful_requests_per_second,
            },
            "resource_stats": {
                "initial_memory_mb": self.initial_memory_mb,
                "peak_memory_mb": self.peak_memory_mb,
                "memory_increase_mb": self.memory_increase_mb,
                "average_cpu_percent": self.average_cpu_percent,
                "peak_cpu_percent": self.peak_cpu_percent,
            },
            "errors": self.errors
        }


class PerformanceBenchmark:
    """Comprehensive performance benchmarking class."""
    
    def __init__(self, name: str):
        self.name = name
        self.process = psutil.Process()
        self.reset()
    
    def reset(self):
        """Reset benchmark state."""
        self.start_time = None
        self.end_time = None
        self.response_times = []
        self.errors = []
        self.success_count = 0
        self.error_count = 0
        
        # Resource monitoring
        self.initial_memory = None
        self.peak_memory = None
        self.cpu_samples = []
        self.monitoring_active = False
    
    def start(self):
        """Start the benchmark."""
        self.start_time = datetime.now()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        self.monitoring_active = True
        return self
    
    def stop(self) -> BenchmarkResult:
        """Stop the benchmark and return results."""
        self.end_time = datetime.now()
        self.monitoring_active = False
        
        duration = (self.end_time - self.start_time).total_seconds()
        iterations = len(self.response_times) + len(self.errors)
        
        result = BenchmarkResult(
            name=self.name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=duration,
            iterations=iterations,
            success_count=self.success_count,
            error_count=self.error_count,
            response_times=self.response_times.copy(),
            initial_memory_mb=self.initial_memory,
            peak_memory_mb=self.peak_memory,
            memory_increase_mb=self.peak_memory - self.initial_memory,
            average_cpu_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0.0,
            peak_cpu_percent=max(self.cpu_samples) if self.cpu_samples else 0.0,
            errors=self.errors.copy()
        )
        
        return result
    
    def record_success(self, response_time_ms: float):
        """Record a successful operation."""
        self.response_times.append(response_time_ms)
        self.success_count += 1
        self._sample_resources()
    
    def record_error(self, error_info: Dict[str, Any]):
        """Record an error."""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            **error_info
        })
        self.error_count += 1
        self._sample_resources()
    
    def _sample_resources(self):
        """Sample current resource usage."""
        if not self.monitoring_active:
            return
            
        try:
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            current_cpu = self.process.cpu_percent()
            
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory
                
            self.cpu_samples.append(current_cpu)
        except psutil.NoSuchProcess:
            # Process might have ended
            pass
    
    @asynccontextmanager
    async def measure_async(self):
        """Context manager for measuring async operations."""
        start = time.perf_counter()
        error_occurred = False
        error_info = {}
        
        try:
            yield
        except Exception as e:
            error_occurred = True
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
            raise
        finally:
            end = time.perf_counter()
            response_time_ms = (end - start) * 1000
            
            if error_occurred:
                error_info["response_time_ms"] = response_time_ms
                self.record_error(error_info)
            else:
                self.record_success(response_time_ms)


class DatabaseBenchmark:
    """Specialized benchmarking for database operations."""
    
    @staticmethod
    async def benchmark_query_performance(
        db: Session,
        query_func: Callable[[Session], Any],
        iterations: int = 100,
        name: str = "Database Query"
    ) -> BenchmarkResult:
        """Benchmark database query performance."""
        benchmark = PerformanceBenchmark(name).start()
        
        for i in range(iterations):
            try:
                async with benchmark.measure_async():
                    result = query_func(db)
                    # Force query execution
                    if hasattr(result, 'all'):
                        result.all()
                    elif hasattr(result, 'first'):
                        result.first()
            except Exception as e:
                # Error already recorded by measure_async
                continue
        
        return benchmark.stop()
    
    @staticmethod
    async def benchmark_transaction_performance(
        db: Session,
        transaction_func: Callable[[Session], Any],
        iterations: int = 50,
        name: str = "Database Transaction"
    ) -> BenchmarkResult:
        """Benchmark database transaction performance."""
        benchmark = PerformanceBenchmark(name).start()
        
        for i in range(iterations):
            try:
                async with benchmark.measure_async():
                    transaction_func(db)
                    db.commit()
            except Exception as e:
                db.rollback()
                # Error already recorded by measure_async
                continue
        
        return benchmark.stop()


class APiBenchmark:
    """Specialized benchmarking for API endpoints."""
    
    @staticmethod
    async def benchmark_endpoint(
        client: httpx.AsyncClient,
        method: str,
        url: str,
        iterations: int = 100,
        concurrent: int = 10,
        name: str = None,
        **request_kwargs
    ) -> BenchmarkResult:
        """Benchmark API endpoint performance."""
        if name is None:
            name = f"{method.upper()} {url}"
            
        benchmark = PerformanceBenchmark(name).start()
        semaphore = asyncio.Semaphore(concurrent)
        
        async def make_request():
            async with semaphore:
                async with benchmark.measure_async():
                    response = await client.request(method, url, **request_kwargs)
                    response.raise_for_status()
                    return response
        
        # Create tasks for concurrent execution
        tasks = [make_request() for _ in range(iterations)]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return benchmark.stop()
    
    @staticmethod
    async def benchmark_endpoint_with_data(
        client: httpx.AsyncClient,
        method: str,
        url: str,
        data_list: List[Dict[str, Any]],
        concurrent: int = 10,
        name: str = None,
        **request_kwargs
    ) -> BenchmarkResult:
        """Benchmark API endpoint with different data sets."""
        if name is None:
            name = f"{method.upper()} {url} (with data)"
            
        benchmark = PerformanceBenchmark(name).start()
        semaphore = asyncio.Semaphore(concurrent)
        
        async def make_request(data):
            async with semaphore:
                async with benchmark.measure_async():
                    if method.upper() in ['POST', 'PUT', 'PATCH']:
                        response = await client.request(method, url, json=data, **request_kwargs)
                    else:
                        response = await client.request(method, url, params=data, **request_kwargs)
                    response.raise_for_status()
                    return response
        
        # Create tasks for concurrent execution
        tasks = [make_request(data) for data in data_list]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return benchmark.stop()


class LoadTestBenchmark:
    """Load testing benchmark for sustained performance testing."""
    
    @staticmethod
    async def run_load_test(
        test_func: Callable[[], Any],
        duration_seconds: int = 60,
        concurrent_users: int = 10,
        ramp_up_seconds: int = 10,
        name: str = "Load Test"
    ) -> BenchmarkResult:
        """Run a load test with gradual user ramp-up."""
        benchmark = PerformanceBenchmark(name).start()
        
        # Calculate ramp-up parameters
        users_per_second = concurrent_users / ramp_up_seconds if ramp_up_seconds > 0 else concurrent_users
        
        async def user_session(user_id: int, start_delay: float):
            """Simulate a single user session."""
            await asyncio.sleep(start_delay)
            
            session_end = time.time() + duration_seconds
            
            while time.time() < session_end:
                try:
                    async with benchmark.measure_async():
                        await test_func()
                except Exception:
                    # Error already recorded by measure_async
                    pass
                
                # Small delay between requests to simulate real user behavior
                await asyncio.sleep(0.1)
        
        # Create user sessions with staggered start times
        tasks = []
        for user_id in range(concurrent_users):
            start_delay = (user_id / users_per_second) if ramp_up_seconds > 0 else 0
            task = asyncio.create_task(user_session(user_id, start_delay))
            tasks.append(task)
        
        # Wait for all user sessions to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return benchmark.stop()


class MemoryBenchmark:
    """Memory usage benchmarking utilities."""
    
    @staticmethod
    async def benchmark_memory_usage(
        operation_func: Callable[[], Any],
        iterations: int = 100,
        name: str = "Memory Usage"
    ) -> BenchmarkResult:
        """Benchmark memory usage of operations."""
        benchmark = PerformanceBenchmark(name).start()
        
        for i in range(iterations):
            try:
                async with benchmark.measure_async():
                    result = await operation_func() if asyncio.iscoroutinefunction(operation_func) else operation_func()
            except Exception:
                # Error already recorded by measure_async
                continue
        
        return benchmark.stop()


def compare_benchmarks(benchmark1: BenchmarkResult, benchmark2: BenchmarkResult) -> Dict[str, Any]:
    """Compare two benchmark results and return performance differences."""
    comparison = {
        "benchmark1": benchmark1.name,
        "benchmark2": benchmark2.name,
        "performance_change": {},
        "summary": ""
    }
    
    # Compare response times
    if benchmark1.mean_response_time > 0 and benchmark2.mean_response_time > 0:
        mean_change = ((benchmark2.mean_response_time - benchmark1.mean_response_time) / benchmark1.mean_response_time) * 100
        p95_change = ((benchmark2.p95_response_time - benchmark1.p95_response_time) / benchmark1.p95_response_time) * 100 if benchmark1.p95_response_time > 0 else 0
        
        comparison["performance_change"]["mean_response_time_percent"] = mean_change
        comparison["performance_change"]["p95_response_time_percent"] = p95_change
    
    # Compare throughput
    if benchmark1.requests_per_second > 0 and benchmark2.requests_per_second > 0:
        throughput_change = ((benchmark2.requests_per_second - benchmark1.requests_per_second) / benchmark1.requests_per_second) * 100
        comparison["performance_change"]["throughput_percent"] = throughput_change
    
    # Compare memory usage
    if benchmark1.peak_memory_mb > 0 and benchmark2.peak_memory_mb > 0:
        memory_change = ((benchmark2.peak_memory_mb - benchmark1.peak_memory_mb) / benchmark1.peak_memory_mb) * 100
        comparison["performance_change"]["memory_usage_percent"] = memory_change
    
    # Generate summary
    changes = []
    for metric, change in comparison["performance_change"].items():
        direction = "improved" if change < 0 else "degraded"
        changes.append(f"{metric}: {abs(change):.1f}% {direction}")
    
    comparison["summary"] = "; ".join(changes) if changes else "No significant changes detected"
    
    return comparison


def save_benchmark_results(results: List[BenchmarkResult], filename: str = None) -> str:
    """Save benchmark results to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "results": [result.to_dict() for result in results]
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename