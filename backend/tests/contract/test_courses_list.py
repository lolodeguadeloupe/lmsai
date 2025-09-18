"""
Contract test for GET /api/v1/courses endpoint.
This test MUST FAIL until the endpoint is implemented.
"""
from fastapi import status


class TestListCourses:
    """Contract tests for course listing endpoint."""

    def test_list_courses_empty(self, client):
        """Test listing courses when none exist."""
        response = client.get("/api/v1/courses")

        # Contract assertions - these WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "courses" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert isinstance(data["courses"], list)
        assert data["total"] == 0
        assert len(data["courses"]) == 0

    def test_list_courses_with_filters(self, client):
        """Test listing courses with query filters."""
        params = {
            "status": "published",
            "subject_domain": "Computer Science",
            "limit": 10,
            "offset": 0,
        }

        response = client.get("/api/v1/courses", params=params)

        # Contract assertions
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "courses" in data
        assert "total" in data
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_list_courses_pagination(self, client):
        """Test course listing pagination."""
        response = client.get("/api/v1/courses?limit=5&offset=10")

        # Contract assertions
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10

    def test_list_courses_invalid_params(self, client):
        """Test listing with invalid parameters."""
        response = client.get("/api/v1/courses?limit=invalid")

        # Should handle invalid params gracefully
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
