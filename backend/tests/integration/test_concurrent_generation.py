"""
Integration test for concurrent generation handling.
Tests FR-022: Support 100+ simultaneous operations.
"""
import concurrent.futures

import pytest
from fastapi import status


class TestConcurrentGeneration:
    """Integration tests for concurrent course generation."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_course_generation(self, client):
        """Test concurrent generation of multiple courses (FR-022)."""
        # Create multiple course requests simultaneously
        base_request = {
            "title": "Concurrent Test Course",
            "description": "Course for testing concurrent generation",
            "subject_domain": "Computer Science",
            "target_audience": {
                "proficiency_level": "beginner",
                "prerequisites": [],
                "learning_preferences": ["visual"],
            },
        }

        # Test with 10 concurrent requests (scaled down for testing)
        # In production, should handle 100+ as per FR-022
        num_concurrent = 10
        concurrent_requests = []

        for i in range(num_concurrent):
            request_data = base_request.copy()
            request_data["title"] = f"Concurrent Test Course {i+1}"
            concurrent_requests.append(request_data)

        # Submit all requests concurrently
        responses = []
        course_ids = []

        def create_course(request_data):
            return client.post("/api/v1/courses", json=request_data)

        # Use ThreadPoolExecutor to simulate concurrent requests
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_concurrent
        ) as executor:
            future_to_request = {
                executor.submit(create_course, req): req for req in concurrent_requests
            }

            for future in concurrent.futures.as_completed(future_to_request):
                response = future.result()
                responses.append(response)

                # All requests should be accepted
                assert response.status_code == status.HTTP_201_CREATED

                response_data = response.json()
                course_ids.append(response_data["id"])

                # Verify response structure
                assert "id" in response_data
                assert "status" in response_data
                assert "generation_task_id" in response_data
                assert response_data["status"] == "generating"

        # Verify all courses were created successfully
        assert len(responses) == num_concurrent
        assert len(course_ids) == num_concurrent
        assert len(set(course_ids)) == num_concurrent  # All IDs should be unique

        # Monitor generation progress for all courses
        generation_tasks = set()
        for course_id in course_ids:
            status_response = client.get(
                f"/api/v1/courses/{course_id}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()
            generation_tasks.add(status_data["task_id"])

        # All generation tasks should be unique
        assert len(generation_tasks) == num_concurrent

        print(f"✅ Successfully started {num_concurrent} concurrent course generations")

    @pytest.mark.integration
    def test_concurrent_generation_resource_management(self, client):
        """Test that concurrent generation doesn't exhaust system resources."""
        # Create multiple courses and monitor system behavior
        base_request = {
            "title": "Resource Test Course",
            "description": "Course for testing resource management",
            "subject_domain": "Computer Science",
            "target_audience": {
                "proficiency_level": "intermediate",
                "prerequisites": [],
                "learning_preferences": ["practical"],
            },
        }

        course_ids = []

        # Create 5 courses rapidly
        for i in range(5):
            request_data = base_request.copy()
            request_data["title"] = f"Resource Test Course {i+1}"

            response = client.post("/api/v1/courses", json=request_data)

            # Should not fail due to resource exhaustion
            assert response.status_code == status.HTTP_201_CREATED
            course_ids.append(response.json()["id"])

        # Check that all generations are progressing
        active_generations = 0
        for course_id in course_ids:
            status_response = client.get(
                f"/api/v1/courses/{course_id}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()
            if status_data["status"] in ["pending", "in_progress"]:
                active_generations += 1

        # Should have multiple active generations
        assert active_generations > 0

        print(f"✅ {active_generations} generations active without resource issues")

    @pytest.mark.integration
    def test_concurrent_generation_queue_management(self, client):
        """Test generation queue management under load."""
        # Create more courses than can be processed immediately
        base_request = {
            "title": "Queue Test Course",
            "description": "Course for testing queue management",
            "subject_domain": "Mathematics",
            "target_audience": {
                "proficiency_level": "beginner",
                "prerequisites": [],
                "learning_preferences": ["visual"],
            },
        }

        # Submit requests rapidly
        course_data = []
        for i in range(8):
            request_data = base_request.copy()
            request_data["title"] = f"Queue Test Course {i+1}"

            response = client.post("/api/v1/courses", json=request_data)
            assert response.status_code == status.HTTP_201_CREATED

            course_data.append(
                {
                    "id": response.json()["id"],
                    "task_id": response.json()["generation_task_id"],
                }
            )

        # Check generation status distribution
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}

        for course_info in course_data:
            status_response = client.get(
                f"/api/v1/courses/{course_info['id']}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()
            status_counts[status_data["status"]] += 1

        # Should have some pending and some in progress (queue management)
        total_active = status_counts["pending"] + status_counts["in_progress"]
        assert total_active > 0

        # No failures should occur from concurrent load
        assert status_counts["failed"] == 0

        print(f"✅ Queue management working: {status_counts}")

    @pytest.mark.integration
    def test_concurrent_different_complexity_levels(self, client):
        """Test concurrent generation with different complexity levels."""
        levels = ["beginner", "intermediate", "advanced", "expert"]

        course_ids_by_level = {}

        # Create one course for each level simultaneously
        for level in levels:
            request_data = {
                "title": f"Complexity Test - {level.title()}",
                "description": f"Course for testing {level} level concurrent generation",
                "subject_domain": "Computer Science",
                "target_audience": {
                    "proficiency_level": level,
                    "prerequisites": [],
                    "learning_preferences": ["visual"],
                },
            }

            response = client.post("/api/v1/courses", json=request_data)
            assert response.status_code == status.HTTP_201_CREATED

            course_ids_by_level[level] = response.json()["id"]

        # Verify all levels are being processed
        for level, course_id in course_ids_by_level.items():
            status_response = client.get(
                f"/api/v1/courses/{course_id}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()
            assert status_data["status"] in ["pending", "in_progress", "completed"]

        print(f"✅ Concurrent generation working for all complexity levels")

    @pytest.mark.integration
    def test_generation_failure_isolation(self, client):
        """Test that failure in one generation doesn't affect others."""
        # Create a mix of valid and potentially problematic requests
        requests = [
            {
                "title": "Valid Course 1",
                "description": "Normal course",
                "subject_domain": "Computer Science",
                "target_audience": {
                    "proficiency_level": "beginner",
                    "prerequisites": [],
                    "learning_preferences": ["visual"],
                },
            },
            {
                "title": "Valid Course 2",
                "description": "Another normal course",
                "subject_domain": "Mathematics",
                "target_audience": {
                    "proficiency_level": "intermediate",
                    "prerequisites": ["Basic algebra"],
                    "learning_preferences": ["practical"],
                },
            },
            # This request might cause issues due to complexity mismatch
            {
                "title": "Potentially Problematic Course",
                "description": "Very advanced quantum mechanics for absolute beginners",
                "subject_domain": "Physics",
                "target_audience": {
                    "proficiency_level": "beginner",
                    "prerequisites": [],
                    "learning_preferences": ["theoretical"],
                },
            },
        ]

        course_ids = []
        for request_data in requests:
            response = client.post("/api/v1/courses", json=request_data)
            assert response.status_code == status.HTTP_201_CREATED
            course_ids.append(response.json()["id"])

        # Check that all generations are isolated
        successful_generations = 0
        for course_id in course_ids:
            status_response = client.get(
                f"/api/v1/courses/{course_id}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()
            if status_data["status"] in ["pending", "in_progress", "completed"]:
                successful_generations += 1

        # Most generations should proceed normally
        assert successful_generations >= 2

        print(
            f"✅ Generation isolation working: {successful_generations}/{len(course_ids)} proceeding normally"
        )
