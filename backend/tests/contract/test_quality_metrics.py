"""
Contract test for GET /api/v1/courses/{courseId}/quality-metrics endpoint.
"""
from fastapi import status


class TestQualityMetrics:
    """Contract tests for quality metrics endpoint."""

    def test_quality_metrics_success(self, client, sample_course_id):
        """Test successful quality metrics retrieval."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/quality-metrics")

        # Contract assertions - WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "readability_score" in data
        assert "pedagogical_alignment" in data
        assert "objective_coverage" in data
        assert "content_accuracy" in data
        assert "bias_detection_score" in data
        assert "generation_timestamp" in data

        # Verify score ranges
        assert 0 <= data["readability_score"] <= 100
        assert 0 <= data["pedagogical_alignment"] <= 1.0
        assert 0 <= data["objective_coverage"] <= 1.0
        assert 0 <= data["content_accuracy"] <= 1.0
        assert 0 <= data["bias_detection_score"] <= 1.0

    def test_quality_metrics_thresholds(self, client, sample_course_id):
        """Test quality metrics meet requirements thresholds."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/quality-metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # FR-011: Readability thresholds by level
        # For beginner: ≥70, intermediate: ≥60, advanced: ≥50
        assert data["readability_score"] >= 50  # Minimum threshold

        # FR-012: 100% objective coverage required
        assert data["objective_coverage"] == 1.0
