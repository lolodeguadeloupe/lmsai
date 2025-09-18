"""
Contract test for DELETE /api/v1/courses/{courseId} endpoint.
This test MUST FAIL until the endpoint is implemented.
"""
from fastapi import status


class TestDeleteCourse:
    """Contract tests for course deletion endpoint."""

    def test_delete_course_success(self, client, sample_course_id):
        """Test successful course deletion."""
        response = client.delete(f"/api/v1/courses/{sample_course_id}")

        # Contract assertions - these WILL FAIL until implementation
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify course is actually deleted
        get_response = client.get(f"/api/v1/courses/{sample_course_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_course_not_found(self, client):
        """Test course deletion with non-existent ID."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/courses/{non_existent_id}")

        # Contract assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_course_invalid_uuid(self, client):
        """Test course deletion with invalid UUID format."""
        invalid_id = "not-a-uuid"
        response = client.delete(f"/api/v1/courses/{invalid_id}")

        # Contract assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_course_in_generation(self, client, sample_course_id):
        """Test deletion of course that is currently being generated."""
        # This should either prevent deletion or handle gracefully
        response = client.delete(f"/api/v1/courses/{sample_course_id}")

        # Should either succeed or return conflict
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_409_CONFLICT,
        ]

    def test_delete_course_cascade(self, client, sample_course_id):
        """Test that deleting course also deletes related entities."""
        response = client.delete(f"/api/v1/courses/{sample_course_id}")

        # Contract assertion
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Related entities should also be deleted (chapters, quizzes, etc.)
        chapters_response = client.get(f"/api/v1/courses/{sample_course_id}/chapters")
        assert chapters_response.status_code == status.HTTP_404_NOT_FOUND
