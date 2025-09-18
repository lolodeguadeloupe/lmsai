"""
Contract test for PUT /api/v1/courses/{courseId} endpoint.
This test MUST FAIL until the endpoint is implemented.
"""
from fastapi import status


class TestUpdateCourse:
    """Contract tests for course update endpoint."""

    def test_update_course_success(self, client, sample_course_id):
        """Test successful course update."""
        update_data = {
            "title": "Updated Course Title",
            "description": "Updated description",
            "difficulty_score": 3.5,
        }

        response = client.put(f"/api/v1/courses/{sample_course_id}", json=update_data)

        # Contract assertions - these WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["title"] == "Updated Course Title"
        assert data["description"] == "Updated description"
        assert data["difficulty_score"] == 3.5
        assert "updated_at" in data

    def test_update_course_not_found(self, client):
        """Test course update with non-existent ID."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"title": "New Title"}

        response = client.put(f"/api/v1/courses/{non_existent_id}", json=update_data)

        # Contract assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_course_invalid_data(self, client, sample_course_id):
        """Test course update with invalid data."""
        invalid_data = {
            "difficulty_score": "invalid",  # Should be numeric
            "target_audience": {"proficiency_level": "invalid_level"},
        }

        response = client.put(f"/api/v1/courses/{sample_course_id}", json=invalid_data)

        # Contract assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_course_readonly_fields(self, client, sample_course_id):
        """Test that readonly fields cannot be updated."""
        readonly_update = {
            "id": "new-id",
            "created_at": "2023-01-01T00:00:00Z",
            "status": "published",  # Status changes should be separate endpoint
        }

        response = client.put(
            f"/api/v1/courses/{sample_course_id}", json=readonly_update
        )

        # Should either ignore readonly fields or return error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
