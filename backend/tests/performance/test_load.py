"""
Load testing for the course generation platform.
Tests concurrent operations and sustained performance under load.
"""
import pytest
import asyncio
import time
import uuid
from typing import Dict, Any, List, Callable
from datetime import datetime, timedelta

import httpx

from .benchmarks import LoadTestBenchmark, PerformanceBenchmark, APiBenchmark, BenchmarkResult
from .conftest import run_concurrent_requests, assert_performance_thresholds


class TestConcurrentLoad:
    """Test concurrent user load scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_course_creation(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        load_test_data: Dict[str, Any],
        performance_report
    ):
        """Test concurrent course creation with 100 simultaneous requests."""
        course_requests = load_test_data["course_requests"][:100]
        concurrent_users = min(performance_config["concurrent_users"], 100)
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="POST",
            url="/api/v1/courses/",
            data_list=course_requests,
            concurrent=concurrent_users,
            name="Concurrent Course Creation Load Test"
        )
        
        # Assert performance requirements for concurrent creation
        stats = result.to_dict()["response_time_stats"]
        
        # More lenient thresholds for high concurrency
        concurrent_thresholds = {
            "p95_threshold_ms": 1000,  # 1 second for P95
            "p99_threshold_ms": 2000   # 2 seconds for P99
        }
        assert_performance_thresholds(stats, concurrent_thresholds)
        
        # Assert minimum success rate
        success_rate = result.success_count / (result.success_count + result.error_count)
        assert success_rate >= 0.95, f"Concurrent creation success rate {success_rate:.2%} below 95%"
        
        # Assert reasonable throughput
        assert result.requests_per_second >= 10, f"Throughput {result.requests_per_second:.1f} req/s too low"
        
        performance_report.add_test_result("concurrent_course_creation", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_concurrent_read_operations(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test concurrent read operations (should handle high concurrency well)."""
        concurrent_users = performance_config["concurrent_users"]
        
        # Mix of read operations
        read_operations = [
            lambda: async_client.get("/api/v1/health"),
            lambda: async_client.get("/api/v1/info"),
            lambda: async_client.get("/api/v1/courses/"),
            lambda: async_client.get(f"/api/v1/courses/{sample_course_id}"),
            lambda: async_client.get(f"/api/v1/courses/{sample_course_id}/generation-status"),
            lambda: async_client.get(f"/api/v1/courses/{sample_course_id}/chapters"),
        ] * 50  # 300 total requests
        
        benchmark = PerformanceBenchmark("Concurrent Read Operations").start()
        
        async def execute_operation(operation):
            async with benchmark.measure_async():
                response = await operation()
                response.raise_for_status()
                return response
        
        # Execute all operations concurrently
        results = await run_concurrent_requests(
            async_client, 
            [lambda op=op: execute_operation(op) for op in read_operations],
            max_concurrent=concurrent_users
        )
        
        load_result = benchmark.stop()
        
        # Read operations should be very fast even under high concurrency
        stats = load_result.to_dict()["response_time_stats"]
        read_thresholds = {
            "p95_threshold_ms": 300,  # 300ms for P95
            "p99_threshold_ms": 600   # 600ms for P99
        }
        assert_performance_thresholds(stats, read_thresholds)
        
        # Should handle high throughput for reads
        assert load_result.requests_per_second >= 50, f"Read throughput {load_result.requests_per_second:.1f} req/s too low"
        
        performance_report.add_test_result("concurrent_read_operations", load_result.to_dict())
    
    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        load_test_data: Dict[str, Any],
        performance_report
    ):
        """Test mixed read/write operations under concurrent load."""
        concurrent_users = performance_config["concurrent_users"]
        
        # Create a realistic mix: 70% reads, 30% writes
        operations = []
        
        # Read operations (70%)
        read_ops = [
            lambda: async_client.get("/api/v1/health"),
            lambda: async_client.get("/api/v1/courses/"),
            lambda: async_client.get(f"/api/v1/courses/{sample_course_id}"),
            lambda: async_client.get(f"/api/v1/courses/{sample_course_id}/generation-status"),
        ] * 18  # 72 read operations
        
        # Write operations (30%)
        course_data = load_test_data["course_requests"][:28]
        write_ops = [
            lambda data=data: async_client.post("/api/v1/courses/", json=data)
            for data in course_data
        ]  # 28 write operations
        
        operations = read_ops + write_ops  # Total: 100 operations
        
        benchmark = PerformanceBenchmark("Mixed Concurrent Operations").start()
        
        async def execute_operation(operation):
            async with benchmark.measure_async():
                response = await operation()
                response.raise_for_status()
                return response
        
        # Execute with controlled concurrency
        results = await run_concurrent_requests(
            async_client,
            [lambda op=op: execute_operation(op) for op in operations],
            max_concurrent=concurrent_users // 2  # More conservative for mixed ops
        )
        
        load_result = benchmark.stop()
        
        # Mixed operations should still meet reasonable thresholds
        stats = load_result.to_dict()["response_time_stats"]
        mixed_thresholds = {
            "p95_threshold_ms": 800,   # 800ms for P95
            "p99_threshold_ms": 1500   # 1.5 seconds for P99
        }
        assert_performance_thresholds(stats, mixed_thresholds)
        
        # Assert good success rate
        success_rate = load_result.success_count / (load_result.success_count + load_result.error_count)
        assert success_rate >= 0.95, f"Mixed operations success rate {success_rate:.2%} below 95%"
        
        performance_report.add_test_result("mixed_concurrent_operations", load_result.to_dict())


class TestSustainedLoad:
    """Test sustained load over time."""
    
    @pytest.mark.asyncio
    async def test_sustained_api_load(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test sustained API load for specified duration."""
        duration = performance_config["test_duration"]  # 60 seconds
        concurrent_users = performance_config["concurrent_users"] // 4  # 25 users
        ramp_up = performance_config["ramp_up_time"]  # 10 seconds
        
        async def api_workload():
            """Simulate realistic API usage pattern."""
            # Mix of operations with realistic frequency
            operations = [
                # Health checks (frequent)
                (lambda: async_client.get("/api/v1/health"), 0.3),
                # Course listing (frequent)
                (lambda: async_client.get("/api/v1/courses/"), 0.25),
                # Course details (moderate)
                (lambda: async_client.get(f"/api/v1/courses/{sample_course_id}"), 0.2),
                # Generation status (moderate)
                (lambda: async_client.get(f"/api/v1/courses/{sample_course_id}/generation-status"), 0.15),
                # Course updates (infrequent)
                (lambda: async_client.put(f"/api/v1/courses/{sample_course_id}", json={
                    "title": f"Updated at {datetime.now().isoformat()}"
                }), 0.1)
            ]
            
            # Weighted random selection
            import random
            ops, weights = zip(*operations)
            operation = random.choices(ops, weights=weights, k=1)[0]
            
            response = await operation()
            response.raise_for_status()
            return response
        
        result = await LoadTestBenchmark.run_load_test(
            test_func=api_workload,
            duration_seconds=duration,
            concurrent_users=concurrent_users,
            ramp_up_seconds=ramp_up,
            name="Sustained API Load Test"
        )
        
        # Sustained load should maintain good performance
        stats = result.to_dict()["response_time_stats"]
        sustained_thresholds = {
            "p95_threshold_ms": 500,   # 500ms for P95 during sustained load
            "p99_threshold_ms": 1000   # 1 second for P99
        }
        assert_performance_thresholds(stats, sustained_thresholds)
        
        # Assert good overall success rate
        success_rate = result.success_count / (result.success_count + result.error_count)
        assert success_rate >= 0.95, f"Sustained load success rate {success_rate:.2%} below 95%"
        
        # Should maintain reasonable throughput
        assert result.requests_per_second >= 20, f"Sustained throughput {result.requests_per_second:.1f} req/s too low"
        
        performance_report.add_test_result("sustained_api_load", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_course_generation_load(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        load_test_data: Dict[str, Any],
        performance_report
    ):
        """Test sustained course generation load."""
        duration = 30  # Shorter duration for generation tests
        concurrent_users = 10  # Lower concurrency for generation
        
        course_requests = load_test_data["course_requests"]
        
        async def generation_workload():
            """Simulate course generation workload."""
            import random
            
            # 80% status checks, 20% new course creation
            if random.random() < 0.8:
                # Status check operation
                course_id = random.choice(load_test_data["course_ids"])
                response = await async_client.get(f"/api/v1/courses/{course_id}/generation-status")
            else:
                # Course creation operation
                course_data = random.choice(course_requests)
                response = await async_client.post("/api/v1/courses/", json=course_data)
            
            response.raise_for_status()
            return response
        
        result = await LoadTestBenchmark.run_load_test(
            test_func=generation_workload,
            duration_seconds=duration,
            concurrent_users=concurrent_users,
            ramp_up_seconds=5,
            name="Course Generation Load Test"
        )
        
        # Generation operations may be slower
        stats = result.to_dict()["response_time_stats"]
        generation_thresholds = {
            "p95_threshold_ms": 1500,  # 1.5 seconds for P95
            "p99_threshold_ms": 3000   # 3 seconds for P99
        }
        assert_performance_thresholds(stats, generation_thresholds)
        
        # Success rate should still be good
        success_rate = result.success_count / (result.success_count + result.error_count)
        assert success_rate >= 0.90, f"Generation load success rate {success_rate:.2%} below 90%"
        
        performance_report.add_test_result("course_generation_load", result.to_dict())


class TestRampUpBehavior:
    """Test system behavior during user ramp-up scenarios."""
    
    @pytest.mark.asyncio
    async def test_gradual_ramp_up(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_report
    ):
        """Test gradual user ramp-up to detect performance degradation."""
        max_users = performance_config["concurrent_users"]
        ramp_steps = 5
        users_per_step = max_users // ramp_steps
        step_duration = 10  # seconds per step
        
        results = []
        
        for step in range(1, ramp_steps + 1):
            current_users = users_per_step * step
            
            async def api_call():
                response = await async_client.get("/api/v1/courses/")
                response.raise_for_status()
                return response
            
            step_result = await LoadTestBenchmark.run_load_test(
                test_func=api_call,
                duration_seconds=step_duration,
                concurrent_users=current_users,
                ramp_up_seconds=2,
                name=f"Ramp Up Step {step} ({current_users} users)"
            )
            
            results.append({
                "step": step,
                "concurrent_users": current_users,
                "result": step_result.to_dict()
            })
            
            # Brief pause between steps
            await asyncio.sleep(1)
        
        # Analyze performance degradation
        response_times = [r["result"]["response_time_stats"]["p95_ms"] for r in results]
        throughputs = [r["result"]["throughput_stats"]["requests_per_second"] for r in results]
        
        # Response time should not degrade dramatically
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        degradation_ratio = max_response_time / min_response_time if min_response_time > 0 else float('inf')
        
        assert degradation_ratio <= 3.0, f"Response time degraded by {degradation_ratio:.1f}x during ramp-up"
        
        # Throughput should scale reasonably
        max_throughput = max(throughputs)
        min_throughput = min(throughputs)
        scaling_ratio = max_throughput / min_throughput if min_throughput > 0 else float('inf')
        
        assert scaling_ratio >= 1.5, f"Throughput only scaled by {scaling_ratio:.1f}x with {ramp_steps}x users"
        
        ramp_up_summary = {
            "steps": results,
            "analysis": {
                "response_time_degradation": degradation_ratio,
                "throughput_scaling": scaling_ratio,
                "max_p95_response_time_ms": max_response_time,
                "max_throughput_rps": max_throughput
            }
        }
        
        performance_report.add_test_result("gradual_ramp_up", ramp_up_summary)
    
    @pytest.mark.asyncio
    async def test_spike_load_handling(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_report
    ):
        """Test system behavior under sudden load spikes."""
        baseline_users = 5
        spike_users = performance_config["concurrent_users"]
        
        # Baseline measurement
        async def api_call():
            response = await async_client.get("/api/v1/courses/")
            response.raise_for_status()
            return response
        
        baseline_result = await LoadTestBenchmark.run_load_test(
            test_func=api_call,
            duration_seconds=15,
            concurrent_users=baseline_users,
            ramp_up_seconds=2,
            name="Baseline Load"
        )
        
        # Short recovery period
        await asyncio.sleep(5)
        
        # Spike load (no ramp-up)
        spike_result = await LoadTestBenchmark.run_load_test(
            test_func=api_call,
            duration_seconds=15,
            concurrent_users=spike_users,
            ramp_up_seconds=0,  # Immediate spike
            name="Spike Load"
        )
        
        # Recovery measurement
        await asyncio.sleep(5)
        
        recovery_result = await LoadTestBenchmark.run_load_test(
            test_func=api_call,
            duration_seconds=15,
            concurrent_users=baseline_users,
            ramp_up_seconds=2,
            name="Recovery Load"
        )
        
        # Analyze spike handling
        baseline_p95 = baseline_result.to_dict()["response_time_stats"]["p95_ms"]
        spike_p95 = spike_result.to_dict()["response_time_stats"]["p95_ms"]
        recovery_p95 = recovery_result.to_dict()["response_time_stats"]["p95_ms"]
        
        # Spike should not cause extreme degradation
        spike_degradation = spike_p95 / baseline_p95 if baseline_p95 > 0 else float('inf')
        assert spike_degradation <= 5.0, f"Spike caused {spike_degradation:.1f}x response time degradation"
        
        # Recovery should return close to baseline
        recovery_ratio = recovery_p95 / baseline_p95 if baseline_p95 > 0 else float('inf')
        assert recovery_ratio <= 1.5, f"System did not recover after spike (ratio: {recovery_ratio:.1f})"
        
        # Success rates should remain acceptable
        spike_success_rate = spike_result.success_count / (spike_result.success_count + spike_result.error_count)
        assert spike_success_rate >= 0.85, f"Spike success rate {spike_success_rate:.2%} too low"
        
        spike_summary = {
            "baseline": baseline_result.to_dict(),
            "spike": spike_result.to_dict(),
            "recovery": recovery_result.to_dict(),
            "analysis": {
                "spike_degradation_ratio": spike_degradation,
                "recovery_ratio": recovery_ratio,
                "spike_success_rate": spike_success_rate
            }
        }
        
        performance_report.add_test_result("spike_load_handling", spike_summary)


class TestResourceScaling:
    """Test resource usage scaling under load."""
    
    @pytest.mark.asyncio
    async def test_memory_scaling_under_load(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_monitor,
        performance_report
    ):
        """Test memory usage scaling with increasing load."""
        performance_monitor.start_monitoring()
        
        load_levels = [10, 25, 50, 100]  # Different concurrent user levels
        memory_measurements = []
        
        async def api_workload():
            response = await async_client.get("/api/v1/courses/")
            response.raise_for_status()
            performance_monitor.sample_resources()
            return response
        
        for load_level in load_levels:
            # Run load test at this level
            result = await LoadTestBenchmark.run_load_test(
                test_func=api_workload,
                duration_seconds=20,
                concurrent_users=load_level,
                ramp_up_seconds=5,
                name=f"Memory Scaling Test - {load_level} users"
            )
            
            memory_measurements.append({
                "concurrent_users": load_level,
                "throughput_rps": result.requests_per_second,
                "p95_response_time_ms": result.p95_response_time,
                "success_rate": result.success_count / (result.success_count + result.error_count)
            })
            
            # Brief pause between tests
            await asyncio.sleep(5)
        
        final_memory_stats = performance_monitor.stop_monitoring()
        
        # Memory usage should scale reasonably
        memory_limit_mb = performance_config["memory_limit_mb"]
        assert final_memory_stats["peak_memory_mb"] <= memory_limit_mb, \
            f"Memory usage {final_memory_stats['peak_memory_mb']:.1f}MB exceeds limit {memory_limit_mb}MB"
        
        # Memory increase should be reasonable even at max load
        assert final_memory_stats["memory_increase_mb"] <= 200, \
            f"Memory increase {final_memory_stats['memory_increase_mb']:.1f}MB too high under load"
        
        scaling_summary = {
            "load_levels": memory_measurements,
            "memory_stats": final_memory_stats,
            "memory_efficiency": final_memory_stats["peak_memory_mb"] / max(load_levels)  # MB per user
        }
        
        performance_report.add_test_result("memory_scaling_under_load", scaling_summary)