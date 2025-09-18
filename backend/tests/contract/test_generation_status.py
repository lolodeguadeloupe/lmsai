"""
Contract test for GET /api/v1/courses/{courseId}/generation-status endpoint.
This test MUST FAIL until the endpoint is implemented.
"""
from fastapi import status


class TestGenerationStatus:
    """Contract tests for generation status endpoint."""

    def test_generation_status_in_progress(self, client, sample_course_id):
        """Test generation status for course in progress."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/generation-status")

        # Contract assertions - these WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "progress_percentage" in data
        assert "current_phase" in data
        assert "estimated_time_remaining" in data

        # Verify enum values
        assert data["status"] in ["pending", "in_progress", "completed", "failed"]
        assert 0 <= data["progress_percentage"] <= 100
        assert data["current_phase"] in [
            "structure",
            "content",
            "assessment",
            "validation",
            "export",
        ]

    def test_generation_status_completed(self, client, sample_course_id):
        """Test generation status for completed course."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/generation-status")

        # Contract assertions
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if data["status"] == "completed":
            assert data["progress_percentage"] == 100.0
            assert data["estimated_time_remaining"] == "PT0S"

    def test_generation_status_failed(self, client, sample_course_id):
        """Test generation status for failed course generation."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/generation-status")

        # Contract assertions
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if data["status"] == "failed":
            assert "error_details" in data
            assert "retry_count" in data

    def test_generation_status_not_found(self, client):
        """Test generation status for non-existent course."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/courses/{non_existent_id}/generation-status")

        # Contract assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
