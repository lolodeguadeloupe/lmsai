"""
Contract test for POST /api/v1/courses/{courseId}/export endpoint.
"""
from fastapi import status


class TestExportCourse:
    """Contract tests for course export endpoint."""

    def test_export_scorm(self, client, sample_course_id):
        """Test SCORM export format."""
        request_data = {
            "format": "scorm2004",
            "include_assessments": True,
            "include_multimedia": True,
        }

        response = client.post(
            f"/api/v1/courses/{sample_course_id}/export", json=request_data
        )

        # Contract assertions - WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "download_url" in data
        assert "expires_at" in data
        assert "file_size" in data
        assert "checksum" in data

    def test_export_multiple_formats(self, client, sample_course_id):
        """Test multiple export formats."""
        formats = ["scorm2004", "xapi", "qti21", "pdf", "html"]

        for format_type in formats:
            response = client.post(
                f"/api/v1/courses/{sample_course_id}/export",
                json={"format": format_type},
            )
            assert response.status_code == status.HTTP_200_OK

    def test_export_invalid_format(self, client, sample_course_id):
        """Test export with invalid format."""
        request_data = {"format": "invalid_format"}

        response = client.post(
            f"/api/v1/courses/{sample_course_id}/export", json=request_data
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
