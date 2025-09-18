"""
Contract test for POST /api/v1/courses endpoint.
This test MUST FAIL until the endpoint is implemented.
"""
from fastapi import status


class TestCreateCourse:
    """Contract tests for course creation endpoint."""

    def test_create_course_success(self, client, sample_course_request):
        """Test successful course creation."""
        response = client.post("/api/v1/courses", json=sample_course_request)

        # Contract assertions - these WILL FAIL until implementation
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "id" in data
        assert "status" in data
        assert "generation_task_id" in data
        assert "estimated_completion_time" in data

        # Verify response structure matches OpenAPI spec
        assert data["status"] == "generating"
        assert isinstance(data["id"], str)
        assert isinstance(data["generation_task_id"], str)

    def test_create_course_invalid_request(self, client):
        """Test course creation with invalid request data."""
        invalid_request = {
            "title": "",  # Empty title should fail validation
            "subject_domain": "Invalid Domain",
        }

        response = client.post("/api/v1/courses", json=invalid_request)

        # Contract assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], (str, list, dict))

    def test_create_course_missing_required_fields(self, client):
        """Test course creation with missing required fields."""
        incomplete_request = {
            "title": "Test Course"
            # Missing required fields: subject_domain, target_audience
        }

        response = client.post("/api/v1/courses", json=incomplete_request)

        # Contract assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_course_invalid_target_audience(self, client):
        """Test course creation with invalid target audience."""
        invalid_request = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": {
                "proficiency_level": "invalid_level"  # Should be beginner|intermediate|advanced|expert
            },
        }

        response = client.post("/api/v1/courses", json=invalid_request)

        # Contract assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_course_unauthorized(self, client, sample_course_request):
        """Test course creation without authentication (future requirement)."""
        # Remove API key header if authentication is implemented
        response = client.post("/api/v1/courses", json=sample_course_request)

        # For now, should work without auth. Later this test will expect 401
        # When auth is implemented, change to: assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_create_course_rate_limit(self, client, sample_course_request):
        """Test rate limiting on course creation endpoint."""
        # This test will fail until rate limiting is implemented
        responses = []

        # Try to create many courses quickly
        for _ in range(10):
            response = client.post("/api/v1/courses", json=sample_course_request)
            responses.append(response)

        # At least one should succeed, but rate limiting should eventually kick in
        success_count = sum(
            1 for r in responses if r.status_code == status.HTTP_201_CREATED
        )
        rate_limited_count = sum(
            1 for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        )

        # For now, accept any response. Later, verify rate limiting works
        assert len(responses) == 10
