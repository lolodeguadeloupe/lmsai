"""
API performance tests for the course generation platform.
Tests all API endpoints for response time, throughput, and resource usage.
"""
import pytest
import asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime

import httpx

from .benchmarks import APiBenchmark, PerformanceBenchmark, BenchmarkResult
from .conftest import assert_performance_thresholds


class TestAPIPerformance:
    """Comprehensive API performance test suite."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_report
    ):
        """Test health endpoint performance - should be very fast."""
        result = await APiBenchmark.benchmark_endpoint(
            client=async_client,
            method="GET",
            url="/api/v1/health",
            iterations=200,
            concurrent=20,
            name="Health Check Performance"
        )
        
        # Health checks should be extremely fast
        health_thresholds = {
            "p95_threshold_ms": 50,  # Much stricter than normal API
            "p99_threshold_ms": 100
        }
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, health_thresholds)
        
        # Assert high throughput
        assert result.requests_per_second > 100, f"Health endpoint throughput too low: {result.requests_per_second:.1f} req/s"
        
        performance_report.add_test_result("health_endpoint_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_api_info_endpoint_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_report
    ):
        """Test API info endpoint performance."""
        result = await APiBenchmark.benchmark_endpoint(
            client=async_client,
            method="GET",
            url="/api/v1/info",
            iterations=100,
            concurrent=10,
            name="API Info Performance"
        )
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, performance_config)
        
        performance_report.add_test_result("api_info_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_course_creation_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        load_test_data: Dict[str, Any],
        performance_report
    ):
        """Test course creation endpoint performance with various payloads."""
        # Use first 50 course requests for performance testing
        course_requests = load_test_data["course_requests"][:50]
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="POST",
            url="/api/v1/courses/",
            data_list=course_requests,
            concurrent=5,  # Lower concurrency for creation operations
            name="Course Creation Performance"
        )
        
        # Course creation should be within threshold but may be slower
        creation_thresholds = {
            "p95_threshold_ms": 500,  # More lenient for creation
            "p99_threshold_ms": 1000
        }
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, creation_thresholds)
        
        # Assert reasonable success rate
        success_rate = result.success_count / (result.success_count + result.error_count)
        assert success_rate >= 0.95, f"Course creation success rate too low: {success_rate:.2%}"
        
        performance_report.add_test_result("course_creation_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_course_listing_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_report
    ):
        """Test course listing endpoint with various filters."""
        # Test different query parameters
        query_variations = [
            {},  # No filters
            {"page": 1, "limit": 10},
            {"page": 2, "limit": 20},
            {"status": "DRAFT"},
            {"subject_domain": "COMPUTER_SCIENCE"},
            {"status": "COMPLETED", "page": 1, "limit": 5}
        ]
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="GET",
            url="/api/v1/courses/",
            data_list=query_variations,
            concurrent=8,
            name="Course Listing Performance"
        )
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, performance_config)
        
        performance_report.add_test_result("course_listing_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_course_retrieval_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test individual course retrieval performance."""
        result = await APiBenchmark.benchmark_endpoint(
            client=async_client,
            method="GET",
            url=f"/api/v1/courses/{sample_course_id}",
            iterations=100,
            concurrent=15,
            name="Course Retrieval Performance"
        )
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, performance_config)
        
        performance_report.add_test_result("course_retrieval_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_course_update_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test course update endpoint performance."""
        update_data = [
            {
                "title": f"Updated Course Title {i}",
                "description": f"Updated description for performance test iteration {i}"
            }
            for i in range(20)
        ]
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="PUT",
            url=f"/api/v1/courses/{sample_course_id}",
            data_list=update_data,
            concurrent=3,  # Lower concurrency for updates
            name="Course Update Performance"
        )
        
        # Updates may be slower due to validation and database operations
        update_thresholds = {
            "p95_threshold_ms": 300,
            "p99_threshold_ms": 600
        }
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, update_thresholds)
        
        performance_report.add_test_result("course_update_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_generation_status_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test generation status endpoint performance."""
        # Test with and without logs
        query_variations = [
            {},  # No query parameters
            {"include_logs": False},
            {"include_logs": True}
        ]
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="GET",
            url=f"/api/v1/courses/{sample_course_id}/generation-status",
            data_list=query_variations,
            concurrent=10,
            name="Generation Status Performance"
        )
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, performance_config)
        
        performance_report.add_test_result("generation_status_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_chapter_operations_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test chapter-related endpoint performance."""
        chapter_id = str(uuid.uuid4())
        
        # Test chapter listing
        chapter_list_result = await APiBenchmark.benchmark_endpoint(
            client=async_client,
            method="GET",
            url=f"/api/v1/courses/{sample_course_id}/chapters",
            iterations=50,
            concurrent=8,
            name="Chapter Listing Performance"
        )
        
        # Test individual chapter retrieval
        chapter_get_result = await APiBenchmark.benchmark_endpoint(
            client=async_client,
            method="GET",
            url=f"/api/v1/courses/{sample_course_id}/chapters/{chapter_id}",
            iterations=50,
            concurrent=8,
            name="Chapter Retrieval Performance"
        )
        
        # Combine results for reporting
        combined_stats = {
            "chapter_listing": chapter_list_result.to_dict(),
            "chapter_retrieval": chapter_get_result.to_dict()
        }
        
        # Assert thresholds for both operations
        for operation, result in [("listing", chapter_list_result), ("retrieval", chapter_get_result)]:
            stats = result.to_dict()["response_time_stats"]
            assert_performance_thresholds(stats, performance_config)
        
        performance_report.add_test_result("chapter_operations_performance", combined_stats)
    
    @pytest.mark.asyncio
    async def test_quiz_operations_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test quiz-related endpoint performance."""
        quiz_id = str(uuid.uuid4())
        
        # Test quiz listing
        quiz_list_result = await APiBenchmark.benchmark_endpoint(
            client=async_client,
            method="GET",
            url=f"/api/v1/courses/{sample_course_id}/quizzes",
            iterations=50,
            concurrent=8,
            name="Quiz Listing Performance"
        )
        
        # Test quiz attempts
        attempt_data = [
            {
                "answers": [
                    {"question_id": f"q{i}", "selected_options": [f"option{i%4}"]}
                    for i in range(5)
                ]
            }
            for _ in range(20)
        ]
        
        quiz_attempt_result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="POST",
            url=f"/api/v1/courses/{sample_course_id}/quizzes/{quiz_id}/attempts",
            data_list=attempt_data,
            concurrent=5,
            name="Quiz Attempt Performance"
        )
        
        combined_stats = {
            "quiz_listing": quiz_list_result.to_dict(),
            "quiz_attempts": quiz_attempt_result.to_dict()
        }
        
        # Assert thresholds
        for operation, result in [("listing", quiz_list_result), ("attempts", quiz_attempt_result)]:
            stats = result.to_dict()["response_time_stats"]
            # Quiz attempts may be slower due to processing
            thresholds = performance_config if operation == "listing" else {
                "p95_threshold_ms": 400,
                "p99_threshold_ms": 800
            }
            assert_performance_thresholds(stats, thresholds)
        
        performance_report.add_test_result("quiz_operations_performance", combined_stats)
    
    @pytest.mark.asyncio
    async def test_export_operations_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test export endpoint performance with different formats."""
        export_formats = ["pdf", "docx", "html", "scorm"]
        export_requests = [{"format": fmt} for fmt in export_formats]
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="POST",
            url=f"/api/v1/courses/{sample_course_id}/export",
            data_list=export_requests,
            concurrent=2,  # Lower concurrency for exports (resource intensive)
            name="Export Operations Performance"
        )
        
        # Export operations are typically slower
        export_thresholds = {
            "p95_threshold_ms": 2000,  # 2 seconds
            "p99_threshold_ms": 5000   # 5 seconds
        }
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, export_thresholds)
        
        performance_report.add_test_result("export_operations_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_quality_analysis_performance(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test quality analysis endpoint performance."""
        analysis_types = [
            {"analysis_type": "content_quality"},
            {"analysis_type": "readability"},
            {"analysis_type": "engagement"},
            {"analysis_type": "comprehensive"}
        ]
        
        result = await APiBenchmark.benchmark_endpoint_with_data(
            client=async_client,
            method="POST",
            url=f"/api/v1/courses/{sample_course_id}/quality-analysis",
            data_list=analysis_types,
            concurrent=3,
            name="Quality Analysis Performance"
        )
        
        # Quality analysis may take longer
        quality_thresholds = {
            "p95_threshold_ms": 1000,  # 1 second
            "p99_threshold_ms": 2000   # 2 seconds
        }
        
        stats = result.to_dict()["response_time_stats"]
        assert_performance_thresholds(stats, quality_thresholds)
        
        performance_report.add_test_result("quality_analysis_performance", result.to_dict())
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        sample_course_id: str,
        performance_report
    ):
        """Test mixed API operations under concurrent load."""
        benchmark = PerformanceBenchmark("Mixed Operations Load Test").start()
        
        async def mixed_operations():
            """Simulate a mix of realistic API operations."""
            operations = [
                # Read operations (more frequent)
                lambda: async_client.get("/api/v1/health"),
                lambda: async_client.get("/api/v1/courses/"),
                lambda: async_client.get(f"/api/v1/courses/{sample_course_id}"),
                lambda: async_client.get(f"/api/v1/courses/{sample_course_id}/generation-status"),
                lambda: async_client.get(f"/api/v1/courses/{sample_course_id}/chapters"),
                
                # Write operations (less frequent)
                lambda: async_client.put(f"/api/v1/courses/{sample_course_id}", json={
                    "title": f"Updated at {datetime.now().isoformat()}"
                }),
            ]
            
            # Choose operation with weighted probability (80% read, 20% write)
            import random
            operation = random.choices(
                operations, 
                weights=[20, 15, 15, 15, 15, 20], 
                k=1
            )[0]
            
            async with benchmark.measure_async():
                response = await operation()
                response.raise_for_status()
        
        # Run concurrent mixed operations
        tasks = [mixed_operations() for _ in range(200)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        result = benchmark.stop()
        
        # Mixed operations should still meet performance targets
        stats = result.to_dict()["response_time_stats"]
        mixed_thresholds = {
            "p95_threshold_ms": 400,  # Slightly more lenient
            "p99_threshold_ms": 800
        }
        assert_performance_thresholds(stats, mixed_thresholds)
        
        # Assert good success rate
        success_rate = result.success_count / (result.success_count + result.error_count)
        assert success_rate >= 0.95, f"Mixed operations success rate too low: {success_rate:.2%}"
        
        performance_report.add_test_result("concurrent_mixed_operations", result.to_dict())


class TestAPIResourceUsage:
    """Test API resource usage patterns."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_monitor,
        performance_report
    ):
        """Test memory usage during sustained API load."""
        performance_monitor.start_monitoring()
        
        # Generate sustained load
        benchmark = PerformanceBenchmark("Memory Usage Test").start()
        
        async def api_call():
            async with benchmark.measure_async():
                response = await async_client.get("/api/v1/courses/")
                response.raise_for_status()
                performance_monitor.sample_resources()
        
        # Run 500 API calls
        tasks = [api_call() for _ in range(500)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        memory_stats = performance_monitor.stop_monitoring()
        result = benchmark.stop()
        
        # Assert memory usage is reasonable
        memory_limit_mb = performance_config["memory_limit_mb"]
        assert memory_stats["peak_memory_mb"] <= memory_limit_mb, \
            f"Memory usage {memory_stats['peak_memory_mb']:.1f}MB exceeds limit {memory_limit_mb}MB"
        
        # Memory increase should be reasonable
        assert memory_stats["memory_increase_mb"] <= 100, \
            f"Memory increase {memory_stats['memory_increase_mb']:.1f}MB too high"
        
        combined_stats = {
            "api_performance": result.to_dict(),
            "memory_usage": memory_stats
        }
        
        performance_report.add_test_result("memory_usage_under_load", combined_stats)
    
    @pytest.mark.asyncio
    async def test_cpu_usage_patterns(
        self, 
        async_client: httpx.AsyncClient, 
        performance_config: Dict[str, Any],
        performance_monitor,
        performance_report
    ):
        """Test CPU usage patterns during various operations."""
        performance_monitor.start_monitoring()
        
        # Test different operation types
        operations = [
            ("light", lambda: async_client.get("/api/v1/health")),
            ("medium", lambda: async_client.get("/api/v1/courses/")),
            ("heavy", lambda: async_client.post("/api/v1/courses/", json={
                "title": "CPU Test Course",
                "description": "Course for CPU usage testing",
                "subject_domain": "COMPUTER_SCIENCE",
                "target_audience": "BEGINNER", 
                "difficulty_level": "EASY",
                "estimated_duration_hours": 10,
                "learning_objectives": ["Test objective"]
            }))
        ]
        
        results = {}
        
        for op_type, operation in operations:
            benchmark = PerformanceBenchmark(f"CPU Usage - {op_type}").start()
            
            async def monitored_operation():
                async with benchmark.measure_async():
                    response = await operation()
                    response.raise_for_status()
                    performance_monitor.sample_resources()
            
            # Run operation multiple times
            tasks = [monitored_operation() for _ in range(20)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            results[op_type] = benchmark.stop().to_dict()
        
        cpu_stats = performance_monitor.stop_monitoring()
        
        # Assert CPU usage is reasonable
        cpu_limit = performance_config["cpu_limit_percent"]
        assert cpu_stats["max_cpu_percent"] <= cpu_limit, \
            f"Peak CPU usage {cpu_stats['max_cpu_percent']:.1f}% exceeds limit {cpu_limit}%"
        
        combined_stats = {
            "operations": results,
            "cpu_usage": cpu_stats
        }
        
        performance_report.add_test_result("cpu_usage_patterns", combined_stats)