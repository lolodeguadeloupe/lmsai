"""
Integration test for generation progress monitoring.
Based on quickstart.md Step 2 monitoring scenarios.
"""
import asyncio

import pytest
from fastapi import status


class TestGenerationMonitoring:
    """Integration tests for generation progress monitoring."""

    @pytest.mark.integration
    async def test_generation_progress_monitoring(self, client, sample_course_request):
        """Test complete generation monitoring workflow."""
        # Start course creation
        response = client.post("/api/v1/courses", json=sample_course_request)
        assert response.status_code == status.HTTP_201_CREATED

        creation_data = response.json()
        course_id = creation_data["id"]
        task_id = creation_data["generation_task_id"]

        # Monitor progress through all phases
        expected_phases = ["structure", "content", "assessment", "validation", "export"]
        seen_phases = set()
        previous_progress = 0

        for _ in range(60):  # Max 5 minutes (60 * 5 seconds)
            status_response = client.get(
                f"/api/v1/courses/{course_id}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()

            # Verify status data structure
            assert status_data["task_id"] == task_id
            assert status_data["status"] in [
                "pending",
                "in_progress",
                "completed",
                "failed",
            ]
            assert 0 <= status_data["progress_percentage"] <= 100
            assert status_data["current_phase"] in expected_phases

            # Progress should be non-decreasing
            assert status_data["progress_percentage"] >= previous_progress
            previous_progress = status_data["progress_percentage"]

            # Track phases
            seen_phases.add(status_data["current_phase"])

            if status_data["status"] == "completed":
                assert status_data["progress_percentage"] == 100.0
                assert status_data["current_phase"] == "export"
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Generation failed: {status_data.get('error_details')}")

            await asyncio.sleep(5)  # Wait 5 seconds between checks
        else:
            pytest.fail("Generation did not complete within timeout")

        # Verify we saw progression through phases
        assert len(seen_phases) >= 2  # Should see at least 2 different phases

    @pytest.mark.integration
    def test_generation_status_persistence(self, client, sample_course_request):
        """Test that generation status persists across API calls."""
        # Create course
        response = client.post("/api/v1/courses", json=sample_course_request)
        course_id = response.json()["id"]

        # Multiple status calls should return consistent data
        for _ in range(5):
            status_response = client.get(
                f"/api/v1/courses/{course_id}/generation-status"
            )
            assert status_response.status_code == status.HTTP_200_OK

            status_data = status_response.json()
            assert "task_id" in status_data
            assert "status" in status_data
            # Task ID should remain consistent
            if hasattr(self, "previous_task_id"):
                assert status_data["task_id"] == self.previous_task_id
            self.previous_task_id = status_data["task_id"]

    @pytest.mark.integration
    def test_generation_error_handling(self, client):
        """Test generation monitoring with invalid scenarios."""
        # Test with non-existent course
        invalid_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/courses/{invalid_id}/generation-status")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test with malformed UUID
        response = client.get("/api/v1/courses/invalid-uuid/generation-status")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
