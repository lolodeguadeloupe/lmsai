"""
Contract test for POST /api/v1/courses/{courseId}/regenerate-chapter endpoint.
"""
from fastapi import status


class TestRegenerateChapter:
    """Contract tests for chapter regeneration endpoint."""

    def test_regenerate_chapter_success(self, client, sample_course_id):
        """Test successful chapter regeneration."""
        request_data = {
            "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
            "regeneration_reason": "Content too advanced for beginner level",
        }

        response = client.post(
            f"/api/v1/courses/{sample_course_id}/regenerate-chapter", json=request_data
        )

        # Contract assertions - WILL FAIL until implementation
        assert response.status_code == status.HTTP_202_ACCEPTED

        data = response.json()
        assert "task_id" in data
        assert "estimated_completion_time" in data

    def test_regenerate_chapter_not_found(self, client, sample_course_id):
        """Test regeneration of non-existent chapter."""
        request_data = {
            "chapter_id": "00000000-0000-0000-0000-000000000000",
            "regeneration_reason": "Test",
        }

        response = client.post(
            f"/api/v1/courses/{sample_course_id}/regenerate-chapter", json=request_data
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
