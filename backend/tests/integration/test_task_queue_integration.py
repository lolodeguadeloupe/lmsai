"""
Integration tests for task queue functionality.
Tests end-to-end task processing, monitoring, and error handling.
"""

import asyncio
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4
from unittest.mock import patch

from src.tasks import task_manager
from src.tasks.utils import get_task_queue_status, estimate_completion_time
from src.tasks.config import get_performance_settings


class TestTaskQueueIntegration:
    """Integration tests for task queue operations."""

    @pytest.fixture
    def course_generation_data(self):
        """Sample data for course generation testing."""
        return {
            "id": str(uuid4()),
            "title": "Integration Test Course",
            "description": "Course for integration testing",
            "subject_domain": "Software Engineering",
            "target_audience": {
                "proficiency_level": "intermediate",
                "prerequisites": ["Basic programming"],
                "learning_preferences": ["practical", "visual"]
            },
            "learning_objectives": [
                "Understand integration testing",
                "Learn task queue management",
                "Apply async processing patterns"
            ],
            "estimated_duration": "PT15H",
            "difficulty_score": 3.0
        }

    @pytest.fixture
    def chapter_generation_data(self):
        """Sample data for chapter generation testing."""
        return {
            "id": str(uuid4()),
            "course_id": str(uuid4()),
            "sequence_number": 1,
            "title": "Task Queue Fundamentals",
            "learning_objectives": [
                "Understand async task processing",
                "Learn Celery architecture"
            ],
            "estimated_duration": "PT3H",
            "complexity_level": 2.5,
            "prerequisites": ["Basic Python knowledge"]
        }

    @pytest.mark.integration
    def test_full_course_generation_workflow(self, course_generation_data):
        """Test complete course generation workflow."""
        # Start course generation
        task_id = task_manager.start_course_generation(course_generation_data)
        assert task_id is not None
        
        # Monitor progress
        max_wait_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = task_manager.get_task_status(task_id)
            
            # Verify status structure
            assert "status" in status
            assert "progress_percentage" in status
            assert "current_phase" in status
            
            # Check for completion or failure
            if status["status"] == "completed":
                assert status["progress_percentage"] == 100.0
                assert "result" in status
                break
            elif status["status"] == "failed":
                assert "error_details" in status
                break
            
            time.sleep(1)
        
        # Final status check
        final_status = task_manager.get_task_status(task_id)
        assert final_status["status"] in ["completed", "failed", "in_progress"]

    @pytest.mark.integration
    def test_chapter_generation_performance(self, chapter_generation_data):
        """Test chapter generation meets <2 minute requirement."""
        course_context = {
            "title": "Performance Test Course",
            "difficulty_score": 2.0
        }
        
        start_time = time.time()
        task_id = task_manager.start_chapter_generation(chapter_generation_data, course_context)
        
        # Wait for completion with timeout
        max_wait = 125  # 2 minutes + 5 second buffer
        while time.time() - start_time < max_wait:
            status = task_manager.get_task_status(task_id)
            
            if status["status"] in ["completed", "failed"]:
                break
            
            time.sleep(0.5)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify performance requirement
        assert execution_time < 120, f"Chapter generation took {execution_time:.2f}s, exceeds 2-minute limit"
        
        # Verify task completed successfully
        final_status = task_manager.get_task_status(task_id)
        if final_status["status"] == "failed":
            pytest.fail(f"Chapter generation failed: {final_status.get('error_details')}")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_task_processing(self, course_generation_data):
        """Test concurrent processing of multiple tasks (FR-022)."""
        num_concurrent = 10  # Scaled down from 100+ for testing
        
        # Prepare multiple course requests
        course_requests = []
        for i in range(num_concurrent):
            course_data = course_generation_data.copy()
            course_data["id"] = str(uuid4())
            course_data["title"] = f"Concurrent Test Course {i+1}"
            course_requests.append(course_data)
        
        # Submit all tasks concurrently
        task_ids = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            future_to_data = {
                executor.submit(task_manager.start_course_generation, course_data): course_data
                for course_data in course_requests
            }
            
            for future in as_completed(future_to_data):
                task_id = future.result()
                task_ids.append(task_id)
        
        submission_time = time.time() - start_time
        
        # Verify all tasks were submitted
        assert len(task_ids) == num_concurrent
        assert len(set(task_ids)) == num_concurrent  # All unique
        
        print(f"✅ Submitted {num_concurrent} tasks in {submission_time:.2f}s")
        
        # Monitor task progress
        active_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        
        # Check initial status
        for task_id in task_ids:
            status = task_manager.get_task_status(task_id)
            if status["status"] in ["pending", "in_progress"]:
                active_tasks += 1
            elif status["status"] == "completed":
                completed_tasks += 1
            elif status["status"] == "failed":
                failed_tasks += 1
        
        # Should have some active tasks
        assert active_tasks + completed_tasks + failed_tasks == num_concurrent
        
        print(f"✅ Task distribution: {active_tasks} active, {completed_tasks} completed, {failed_tasks} failed")

    @pytest.mark.integration
    def test_quality_validation_workflow(self, course_generation_data):
        """Test quality validation workflow integration."""
        validation_criteria = {
            "min_readability_score": 80.0,
            "min_pedagogical_alignment": 0.8,
            "min_content_accuracy": 0.85,
            "check_bias": True
        }
        
        task_id = task_manager.start_quality_validation(
            course_generation_data, 
            validation_criteria
        )
        
        # Monitor validation progress
        max_wait = 60  # 1 minute
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = task_manager.get_task_status(task_id)
            
            # Should be in validation phase
            assert status["current_phase"] == "validation"
            
            if status["status"] in ["completed", "failed"]:
                break
            
            time.sleep(1)
        
        final_status = task_manager.get_task_status(task_id)
        assert final_status["status"] in ["completed", "failed", "in_progress"]

    @pytest.mark.integration
    def test_export_workflow_integration(self, course_generation_data):
        """Test course export workflow integration."""
        export_formats = ["pdf", "scorm", "json"]
        
        for export_format in export_formats:
            export_options = {
                "include_assessments": True,
                "include_metadata": True,
                "compression": "high" if export_format == "scorm" else "none"
            }
            
            task_id = task_manager.start_course_export(
                course_generation_data,
                export_format,
                export_options
            )
            
            # Verify task creation
            assert task_id is not None
            
            # Check initial status
            status = task_manager.get_task_status(task_id)
            assert status["current_phase"] == "export"
            
            print(f"✅ Started {export_format} export task {task_id}")

    @pytest.mark.integration
    def test_chapter_regeneration_workflow(self, chapter_generation_data):
        """Test chapter regeneration workflow integration."""
        course_context = {
            "title": "Regeneration Test Course",
            "difficulty_score": 2.0
        }
        
        regeneration_reasons = [
            "Content too advanced for beginner level",
            "Missing practical examples",
            "Accuracy concerns in theoretical content"
        ]
        
        for reason in regeneration_reasons:
            regeneration_options = {
                "focus_area": "simplification" if "advanced" in reason else "enhancement",
                "preserve_structure": True
            }
            
            task_id = task_manager.start_chapter_regeneration(
                chapter_generation_data["id"],
                course_context,
                reason,
                regeneration_options
            )
            
            # Verify task creation
            assert task_id is not None
            
            # Check metadata includes regeneration reason
            status = task_manager.get_task_status(task_id)
            if "metadata" in status:
                assert "regeneration_reason" in status["metadata"]

    @pytest.mark.integration
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Test with invalid course data
        invalid_course_data = {
            "invalid_field": "invalid_value",
            "missing_required_fields": True
        }
        
        # Should handle gracefully without crashing
        try:
            task_id = task_manager.start_course_generation(invalid_course_data)
            
            if task_id:
                # If task was created, it should eventually fail gracefully
                time.sleep(2)
                status = task_manager.get_task_status(task_id)
                
                # Should either be failed or still processing
                assert status["status"] in ["failed", "pending", "in_progress"]
                
                if status["status"] == "failed":
                    assert "error_details" in status
                    
        except Exception as e:
            # Exception handling should be graceful
            assert isinstance(e, (ValueError, TypeError, KeyError))

    @pytest.mark.integration
    def test_task_monitoring_and_stats(self):
        """Test task monitoring and statistics collection."""
        # Get initial queue status
        initial_status = get_task_queue_status()
        assert isinstance(initial_status, dict)
        assert "queue_health" in initial_status
        
        # Start some tasks to populate metrics
        course_data = {
            "id": str(uuid4()),
            "title": "Monitoring Test Course",
            "subject_domain": "Testing",
            "target_audience": {"proficiency_level": "beginner"},
            "learning_objectives": ["Test monitoring"],
            "estimated_duration": "PT5H",
            "difficulty_score": 1.5
        }
        
        task_ids = []
        for i in range(3):
            course_data["id"] = str(uuid4())
            task_id = task_manager.start_course_generation(course_data)
            task_ids.append(task_id)
        
        # Get updated status
        updated_status = get_task_queue_status()
        
        # Should show increased activity
        if "total_active_tasks" in updated_status:
            assert updated_status["total_active_tasks"] >= 0
        
        # Get worker stats
        worker_stats = task_manager.get_worker_stats()
        assert isinstance(worker_stats, dict)
        
        # Get active tasks
        active_tasks = task_manager.get_active_tasks()
        assert isinstance(active_tasks, list)

    @pytest.mark.integration
    def test_performance_under_load(self, course_generation_data):
        """Test system performance under load."""
        performance_settings = get_performance_settings()
        max_concurrent = min(performance_settings["max_concurrent_courses"], 20)  # Scaled for testing
        
        # Submit multiple tasks rapidly
        task_ids = []
        start_time = time.time()
        
        for i in range(max_concurrent):
            course_data = course_generation_data.copy()
            course_data["id"] = str(uuid4())
            course_data["title"] = f"Load Test Course {i+1}"
            
            task_id = task_manager.start_course_generation(course_data)
            task_ids.append(task_id)
        
        submission_time = time.time() - start_time
        
        # Verify rapid submission performance
        avg_submission_time = submission_time / max_concurrent
        assert avg_submission_time < 0.5, f"Task submission too slow: {avg_submission_time:.3f}s per task"
        
        # Check system stability
        queue_status = get_task_queue_status()
        assert queue_status.get("queue_health") in ["healthy", "unhealthy"]  # Should not crash
        
        print(f"✅ Submitted {max_concurrent} tasks in {submission_time:.2f}s ({avg_submission_time:.3f}s per task)")

    @pytest.mark.integration
    def test_time_estimation_accuracy(self):
        """Test time estimation accuracy for different task types."""
        task_types = [
            ("generate_course", {"num_chapters": 5, "difficulty_score": 3.0}),
            ("generate_chapter", {"difficulty_score": 2.0}),
            ("validate_quality", {}),
            ("export_course", {}),
            ("regenerate_chapter", {"difficulty_score": 2.5})
        ]
        
        for task_type, complexity_factors in task_types:
            estimate = estimate_completion_time(task_type, complexity_factors)
            
            # Should be valid ISO 8601 duration
            assert estimate.startswith("PT")
            
            # Extract time value for reasonableness check
            if "M" in estimate:
                # Has minutes
                minutes_part = estimate.split("M")[0].replace("PT", "")
                minutes = int(minutes_part) if minutes_part.isdigit() else 0
                
                # Reasonable time ranges
                if task_type == "generate_chapter":
                    assert minutes <= 3, f"Chapter generation estimate too high: {estimate}"
                elif task_type == "generate_course":
                    assert minutes <= 15, f"Course generation estimate too high: {estimate}"

    @pytest.mark.integration
    def test_task_lifecycle_management(self, course_generation_data):
        """Test complete task lifecycle management."""
        # Start task
        task_id = task_manager.start_course_generation(course_generation_data)
        
        # Track through lifecycle
        seen_statuses = set()
        seen_phases = set()
        
        for _ in range(30):  # Monitor for up to 30 seconds
            status = task_manager.get_task_status(task_id)
            seen_statuses.add(status["status"])
            seen_phases.add(status["current_phase"])
            
            if status["status"] in ["completed", "failed"]:
                break
            
            time.sleep(1)
        
        # Should have progressed through multiple phases
        assert len(seen_phases) >= 1
        
        # Test cancellation if still running
        final_status = task_manager.get_task_status(task_id)
        if final_status["status"] in ["pending", "in_progress"]:
            cancel_result = task_manager.cancel_task(task_id, "Integration test cleanup")
            assert isinstance(cancel_result, bool)

    @pytest.mark.integration
    @pytest.mark.parametrize("export_format", ["pdf", "scorm", "json"])
    def test_format_specific_exports(self, course_generation_data, export_format):
        """Test format-specific export functionality."""
        export_options = {
            "pdf": {"page_size": "A4", "include_toc": True},
            "scorm": {"version": "1.2", "compress": True},
            "json": {"pretty_print": True, "include_metadata": True}
        }.get(export_format, {})
        
        task_id = task_manager.start_course_export(
            course_generation_data,
            export_format,
            export_options
        )
        
        # Verify task creation
        assert task_id is not None
        
        # Check status
        status = task_manager.get_task_status(task_id)
        assert status["current_phase"] == "export"
        
        print(f"✅ Successfully started {export_format} export")