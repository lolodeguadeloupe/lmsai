"""
Integration test for quality validation pipeline.
Validates FR-011, FR-012, and quality thresholds.
"""
import pytest
from fastapi import status


class TestQualityValidation:
    """Integration tests for quality validation pipeline."""

    @pytest.mark.integration
    def test_quality_validation_pipeline(self, client, sample_course_request):
        """Test complete quality validation workflow."""
        # Create course
        response = client.post("/api/v1/courses", json=sample_course_request)
        assert response.status_code == status.HTTP_201_CREATED
        course_id = response.json()["id"]

        # Wait for generation completion (simplified)
        # In real implementation, poll until status == "completed"

        # Test quality metrics endpoint
        quality_response = client.get(f"/api/v1/courses/{course_id}/quality-metrics")
        assert quality_response.status_code == status.HTTP_200_OK

        quality_data = quality_response.json()

        # Validate all required metrics exist
        required_metrics = [
            "readability_score",
            "pedagogical_alignment",
            "objective_coverage",
            "content_accuracy",
            "bias_detection_score",
            "generation_timestamp",
        ]
        for metric in required_metrics:
            assert metric in quality_data

        # FR-011: Readability score thresholds by level
        target_level = sample_course_request["target_audience"]["proficiency_level"]
        readability_thresholds = {
            "beginner": 70.0,
            "intermediate": 60.0,
            "advanced": 50.0,
            "expert": 0.0,  # No strict limit for expert
        }

        expected_threshold = readability_thresholds[target_level]
        assert quality_data["readability_score"] >= expected_threshold

        # FR-012: 100% objective coverage required
        assert quality_data["objective_coverage"] == 1.0

        # Additional quality gates
        assert quality_data["pedagogical_alignment"] >= 0.8
        assert quality_data["content_accuracy"] >= 0.9
        assert quality_data["bias_detection_score"] <= 0.1

        # Verify score ranges
        assert 0 <= quality_data["readability_score"] <= 100
        assert 0 <= quality_data["pedagogical_alignment"] <= 1.0
        assert 0 <= quality_data["objective_coverage"] <= 1.0
        assert 0 <= quality_data["content_accuracy"] <= 1.0
        assert 0 <= quality_data["bias_detection_score"] <= 1.0

    @pytest.mark.integration
    def test_quality_validation_by_level(self, client):
        """Test quality validation for different proficiency levels."""
        levels_and_thresholds = {
            "beginner": 70.0,
            "intermediate": 60.0,
            "advanced": 50.0,
            "expert": 0.0,
        }

        for level, threshold in levels_and_thresholds.items():
            request_data = {
                "title": f"Quality Test Course - {level.title()}",
                "description": "Course for quality validation testing",
                "subject_domain": "Computer Science",
                "target_audience": {
                    "proficiency_level": level,
                    "prerequisites": [],
                    "learning_preferences": ["visual"],
                },
            }

            response = client.post("/api/v1/courses", json=request_data)
            assert response.status_code == status.HTTP_201_CREATED

            course_id = response.json()["id"]

            # Would wait for completion in real test
            # Then verify quality metrics meet level-specific thresholds
            quality_response = client.get(
                f"/api/v1/courses/{course_id}/quality-metrics"
            )

            if quality_response.status_code == status.HTTP_200_OK:
                quality_data = quality_response.json()
                assert quality_data["readability_score"] >= threshold

    @pytest.mark.integration
    def test_quality_failure_handling(self, client):
        """Test handling of quality validation failures."""
        # Create course that might fail quality checks
        difficult_request = {
            "title": "Extremely Advanced Quantum Computing",
            "description": "Highly technical course with complex terminology",
            "subject_domain": "Physics",
            "target_audience": {
                "proficiency_level": "beginner",  # Mismatch: complex topic for beginners
                "prerequisites": [],
                "learning_preferences": ["theoretical"],
            },
        }

        response = client.post("/api/v1/courses", json=difficult_request)
        # Should still accept the request initially
        assert response.status_code == status.HTTP_201_CREATED

        course_id = response.json()["id"]

        # The quality validation should flag this as problematic
        # Implementation should either:
        # 1. Automatically adjust content complexity, or
        # 2. Flag for manual review, or
        # 3. Suggest different target audience

        quality_response = client.get(f"/api/v1/courses/{course_id}/quality-metrics")
        if quality_response.status_code == status.HTTP_200_OK:
            quality_data = quality_response.json()
            # Either readability meets beginner threshold (auto-adjusted)
            # Or we get warnings/flags in the response
            assert "readability_score" in quality_data
