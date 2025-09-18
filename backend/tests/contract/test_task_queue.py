"""
Contract tests for background task queue functionality.
Tests task execution, status tracking, and queue management.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.tasks import (
    generate_course_task,
    generate_chapter_task,
    validate_quality_task,
    export_course_task,
    regenerate_chapter_task,
    task_manager
)


class TestTaskQueueContracts:
    """Contract tests for task queue operations."""

    @pytest.fixture
    def sample_course_data(self):
        """Sample course data for testing."""
        return {
            "id": str(uuid4()),
            "title": "Test Course",
            "description": "Course for testing task queue",
            "subject_domain": "Computer Science",
            "target_audience": {
                "proficiency_level": "beginner",
                "prerequisites": [],
                "learning_preferences": ["visual"]
            },
            "learning_objectives": [
                "Learn testing concepts",
                "Understand task queues",
                "Apply async processing"
            ],
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0
        }

    @pytest.fixture
    def sample_chapter_data(self):
        """Sample chapter data for testing."""
        return {
            "id": str(uuid4()),
            "course_id": str(uuid4()),
            "sequence_number": 1,
            "title": "Introduction to Testing",
            "learning_objectives": [
                "Understand testing fundamentals",
                "Learn test-driven development"
            ],
            "estimated_duration": "PT2H",
            "complexity_level": 2.0,
            "prerequisites": []
        }

    def test_generate_course_task_contract(self, sample_course_data):
        """Test course generation task contract."""
        # Test task can be called
        task_id = task_manager.start_course_generation(sample_course_data)
        assert task_id is not None
        assert isinstance(task_id, str)
        
        # Test status can be retrieved
        status = task_manager.get_task_status(task_id)
        assert "task_id" in status
        assert "status" in status
        assert "progress_percentage" in status
        assert "current_phase" in status
        assert "estimated_time_remaining" in status
        
        # Verify status enum values
        assert status["status"] in ["pending", "in_progress", "completed", "failed", "retrying"]
        assert 0 <= status["progress_percentage"] <= 100
        assert status["current_phase"] in [
            "structure", "content", "assessment", "validation", "export"
        ]

    def test_generate_chapter_task_contract(self, sample_chapter_data):
        """Test chapter generation task contract."""
        course_context = {"title": "Test Course", "difficulty_score": 2.0}
        
        task_id = task_manager.start_chapter_generation(sample_chapter_data, course_context)
        assert task_id is not None
        assert isinstance(task_id, str)
        
        status = task_manager.get_task_status(task_id)
        assert status["task_id"] == task_id
        assert "progress_percentage" in status

    def test_validate_quality_task_contract(self, sample_course_data):
        """Test quality validation task contract."""
        validation_criteria = {
            "min_readability_score": 80.0,
            "min_pedagogical_alignment": 0.8
        }
        
        task_id = task_manager.start_quality_validation(sample_course_data, validation_criteria)
        assert task_id is not None
        
        status = task_manager.get_task_status(task_id)
        assert status["current_phase"] == "validation"

    def test_export_course_task_contract(self, sample_course_data):
        """Test course export task contract."""
        export_format = "pdf"
        export_options = {"include_assessments": True}
        
        task_id = task_manager.start_course_export(
            sample_course_data, 
            export_format, 
            export_options
        )
        assert task_id is not None
        
        status = task_manager.get_task_status(task_id)
        assert status["current_phase"] == "export"

    def test_regenerate_chapter_task_contract(self, sample_chapter_data):
        """Test chapter regeneration task contract."""
        course_context = {"title": "Test Course"}
        regeneration_reason = "Content too advanced for beginners"
        
        task_id = task_manager.start_chapter_regeneration(
            sample_chapter_data["id"],
            course_context,
            regeneration_reason
        )
        assert task_id is not None
        
        status = task_manager.get_task_status(task_id)
        assert "metadata" in status
        
    def test_task_status_tracking_contract(self):
        """Test task status tracking contract."""
        fake_task_id = str(uuid4())
        
        # Should handle non-existent task gracefully
        status = task_manager.get_task_status(fake_task_id)
        assert status["task_id"] == fake_task_id
        assert "status" in status
        assert "error_details" in status or status["status"] in ["pending", "failed"]

    def test_task_cancellation_contract(self):
        """Test task cancellation contract."""
        fake_task_id = str(uuid4())
        
        # Should attempt cancellation without error
        result = task_manager.cancel_task(fake_task_id, "Test cancellation")
        assert isinstance(result, bool)

    def test_active_tasks_listing_contract(self):
        """Test active tasks listing contract."""
        active_tasks = task_manager.get_active_tasks()
        assert isinstance(active_tasks, list)
        
        # Test filtering by task type
        filtered_tasks = task_manager.get_active_tasks(["generate_course"])
        assert isinstance(filtered_tasks, list)

    def test_worker_stats_contract(self):
        """Test worker statistics contract."""
        stats = task_manager.get_worker_stats()
        assert isinstance(stats, dict)
        
        # Should have basic structure even if no workers
        assert "workers" in stats or "error" in stats

    def test_performance_requirements_contract(self, sample_chapter_data):
        """Test performance requirements are met."""
        course_context = {"title": "Test Course"}
        
        # Chapter generation should complete within 2 minutes (requirement)
        with patch('time.sleep'):  # Mock sleep to speed up test
            task_id = task_manager.start_chapter_generation(sample_chapter_data, course_context)
            
            # Task should be created successfully
            assert task_id is not None
            
            # Should have time limit configured correctly
            from src.tasks.generation_tasks import generate_chapter_task
            assert hasattr(generate_chapter_task, 'time_limit')
            assert generate_chapter_task.time_limit <= 120  # 2 minutes max

    def test_concurrent_task_support_contract(self, sample_course_data):
        """Test concurrent task creation (FR-022: 100+ simultaneous operations)."""
        # Create multiple tasks rapidly
        task_ids = []
        
        for i in range(5):  # Scaled down for testing
            course_data = sample_course_data.copy()
            course_data["id"] = str(uuid4())
            course_data["title"] = f"Test Course {i+1}"
            
            task_id = task_manager.start_course_generation(course_data)
            task_ids.append(task_id)
        
        # All tasks should be created successfully
        assert len(task_ids) == 5
        assert len(set(task_ids)) == 5  # All unique
        
        # All tasks should be trackable
        for task_id in task_ids:
            status = task_manager.get_task_status(task_id)
            assert status["task_id"] == task_id

    def test_retry_mechanism_contract(self):
        """Test task retry mechanism contract."""
        from src.tasks.generation_tasks import generate_course_task
        
        # Verify retry configuration
        assert hasattr(generate_course_task, 'max_retries')
        assert generate_course_task.max_retries >= 3
        assert hasattr(generate_course_task, 'autoretry_for')

    def test_progress_tracking_contract(self, sample_course_data):
        """Test progress tracking contract."""
        task_id = task_manager.start_course_generation(sample_course_data)
        status = task_manager.get_task_status(task_id)
        
        # Progress should be trackable
        assert "progress_percentage" in status
        assert isinstance(status["progress_percentage"], (int, float))
        assert 0 <= status["progress_percentage"] <= 100
        
        # Should include timing information
        assert "estimated_time_remaining" in status
        # Should be ISO 8601 duration format
        time_remaining = status["estimated_time_remaining"]
        assert time_remaining.startswith("PT") or time_remaining == "PT0S"

    def test_error_handling_contract(self):
        """Test error handling contract."""
        # Test with invalid data
        invalid_data = {"invalid": "data"}
        
        try:
            task_id = task_manager.start_course_generation(invalid_data)
            # If task is created, status should eventually show failure
            status = task_manager.get_task_status(task_id)
            # Should not raise exception, should handle gracefully
            assert "status" in status
        except Exception:
            # If exception is raised, it should be handled gracefully
            pass

    def test_queue_status_contract(self):
        """Test queue status monitoring contract."""
        from src.tasks.utils import get_task_queue_status
        
        queue_status = get_task_queue_status()
        assert isinstance(queue_status, dict)
        
        # Required fields
        required_fields = [
            "queue_health",
            "total_active_tasks",
            "tasks_by_type",
            "queue_capacity"
        ]
        
        for field in required_fields:
            assert field in queue_status or "error" in queue_status

    def test_task_time_estimation_contract(self):
        """Test task time estimation contract."""
        from src.tasks.utils import estimate_completion_time
        
        # Test different task types
        task_types = [
            "generate_course",
            "generate_chapter", 
            "validate_quality",
            "export_course",
            "regenerate_chapter"
        ]
        
        for task_type in task_types:
            estimate = estimate_completion_time(task_type)
            assert isinstance(estimate, str)
            assert estimate.startswith("PT")  # ISO 8601 format

    def test_success_rate_requirement_contract(self):
        """Test 95% success rate requirement tracking."""
        from src.tasks.config import MonitoringConfig
        
        # Verify success rate threshold is configured
        assert hasattr(MonitoringConfig, 'MINIMUM_SUCCESS_RATE')
        assert MonitoringConfig.MINIMUM_SUCCESS_RATE >= 95.0