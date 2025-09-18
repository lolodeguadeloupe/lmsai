"""
Contract test for GET /api/v1/courses/{courseId} endpoint.
This test MUST FAIL until the endpoint is implemented.
"""
from fastapi import status


class TestGetCourse:
    """Contract tests for course retrieval endpoint."""

    def test_get_course_success(self, client, sample_course_id):
        """Test successful course retrieval."""
        response = client.get(f"/api/v1/courses/{sample_course_id}")

        # Contract assertions - these WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Verify complete course structure matches data model
        assert "id" in data
        assert "title" in data
        assert "description" in data
        assert "subject_domain" in data
        assert "target_audience" in data
        assert "learning_objectives" in data
        assert "estimated_duration" in data
        assert "difficulty_score" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "chapters" in data
        assert "quality_metrics" in data

        # Verify data types
        assert isinstance(data["chapters"], list)
        assert isinstance(data["learning_objectives"], list)
        assert isinstance(data["difficulty_score"], (int, float))

    def test_get_course_not_found(self, client):
        """Test course retrieval with non-existent ID."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/courses/{non_existent_id}")

        # Contract assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "detail" in data

    def test_get_course_invalid_uuid(self, client):
        """Test course retrieval with invalid UUID format."""
        invalid_id = "not-a-uuid"
        response = client.get(f"/api/v1/courses/{invalid_id}")

        # Contract assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_course_include_chapters(self, client, sample_course_id):
        """Test course retrieval with chapters included."""
        response = client.get(
            f"/api/v1/courses/{sample_course_id}?include_chapters=true"
        )

        # Contract assertions
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "chapters" in data
        # Each chapter should have full structure
        if data["chapters"]:
            chapter = data["chapters"][0]
            assert "id" in chapter
            assert "title" in chapter
            assert "sequence_number" in chapter
            assert "subchapters" in chapter
