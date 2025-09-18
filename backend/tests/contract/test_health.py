"""
Contract test for GET /health endpoint.
"""
from fastapi import status


class TestHealthCheck:
    """Contract tests for health check endpoint."""

    def test_health_check_success(self, client):
        """Test basic health check."""
        response = client.get("/health")

        # Contract assertions - This should PASS as it's already implemented in main.py
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert data["service"] == "course-platform-api"

    def test_health_check_detailed(self, client):
        """Test detailed health check with dependencies."""
        response = client.get("/health?detailed=true")

        # Contract assertion - WILL FAIL until detailed health check implemented
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]
        assert "vector_db" in data["dependencies"]

        # Each dependency should have status
        for dep_name, dep_status in data["dependencies"].items():
            assert "status" in dep_status
            assert "response_time_ms" in dep_status
