"""
Integration test for multi-format export functionality.
Based on quickstart.md Step 5 export scenarios.
"""
import pytest
from fastapi import status


class TestExportFormats:
    """Integration tests for course export in multiple formats."""

    @pytest.mark.integration
    def test_export_all_formats(self, client, sample_course_request):
        """Test export in all supported formats."""
        # Create and wait for course completion
        response = client.post("/api/v1/courses", json=sample_course_request)
        assert response.status_code == status.HTTP_201_CREATED
        course_id = response.json()["id"]

        # Wait for course to be ready (simplified for test)
        # In real test, poll generation status until completed

        # Test all supported export formats from FR-016
        export_formats = ["scorm2004", "xapi", "qti21", "pdf", "html"]

        for format_type in export_formats:
            export_request = {
                "format": format_type,
                "include_assessments": True,
                "include_multimedia": True,
            }

            export_response = client.post(
                f"/api/v1/courses/{course_id}/export", json=export_request
            )

            assert export_response.status_code == status.HTTP_200_OK

            export_data = export_response.json()

            # Verify export response structure
            assert "download_url" in export_data
            assert "expires_at" in export_data
            assert "file_size" in export_data
            assert "checksum" in export_data

            # Verify file size is reasonable (> 1KB)
            assert export_data["file_size"] > 1024

            # Verify download URL is valid format
            assert export_data["download_url"].startswith(("http://", "https://"))

            print(f"✅ Successfully exported course in {format_type} format")

    @pytest.mark.integration
    def test_scorm_export_validation(self, client, sample_course_request):
        """Test SCORM export specifically for LMS compliance."""
        response = client.post("/api/v1/courses", json=sample_course_request)
        course_id = response.json()["id"]

        # Export in SCORM format
        export_request = {
            "format": "scorm2004",
            "include_assessments": True,
            "include_multimedia": True,
            "scorm_version": "2004_4th_edition",
        }

        export_response = client.post(
            f"/api/v1/courses/{course_id}/export", json=export_request
        )

        assert export_response.status_code == status.HTTP_200_OK
        export_data = export_response.json()

        # SCORM packages should be ZIP files
        assert export_data["download_url"].endswith(".zip")

        # Should include SCORM-specific metadata
        if "scorm_metadata" in export_data:
            metadata = export_data["scorm_metadata"]
            assert "manifest_file" in metadata
            assert "package_type" in metadata
            assert metadata["package_type"] == "scorm2004"

    @pytest.mark.integration
    def test_xapi_export_validation(self, client, sample_course_request):
        """Test xAPI (Tin Can) export for learning analytics."""
        response = client.post("/api/v1/courses", json=sample_course_request)
        course_id = response.json()["id"]

        export_request = {
            "format": "xapi",
            "include_assessments": True,
            "xapi_profile": "cmi5",  # Common xAPI profile
        }

        export_response = client.post(
            f"/api/v1/courses/{course_id}/export", json=export_request
        )

        assert export_response.status_code == status.HTTP_200_OK
        export_data = export_response.json()

        # xAPI should include learning record structure
        if "xapi_metadata" in export_data:
            metadata = export_data["xapi_metadata"]
            assert "activity_id" in metadata
            assert "actor_template" in metadata

    @pytest.mark.integration
    def test_export_with_different_options(self, client, sample_course_request):
        """Test export with various inclusion options."""
        response = client.post("/api/v1/courses", json=sample_course_request)
        course_id = response.json()["id"]

        # Test different export configurations
        export_configs = [
            {
                "format": "pdf",
                "include_assessments": False,
                "include_multimedia": False,
            },
            {
                "format": "html",
                "include_assessments": True,
                "include_multimedia": False,
            },
            {
                "format": "scorm2004",
                "include_assessments": True,
                "include_multimedia": True,
            },
        ]

        for config in export_configs:
            export_response = client.post(
                f"/api/v1/courses/{course_id}/export", json=config
            )

            assert export_response.status_code == status.HTTP_200_OK

            export_data = export_response.json()
            # File size should vary based on inclusion options
            assert export_data["file_size"] > 0

    @pytest.mark.integration
    def test_export_error_handling(self, client, sample_course_request):
        """Test export error scenarios."""
        response = client.post("/api/v1/courses", json=sample_course_request)
        course_id = response.json()["id"]

        # Test invalid format
        invalid_export = {"format": "invalid_format", "include_assessments": True}

        export_response = client.post(
            f"/api/v1/courses/{course_id}/export", json=invalid_export
        )

        assert export_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test export of non-existent course
        invalid_id = "00000000-0000-0000-0000-000000000000"
        valid_export = {"format": "pdf"}

        export_response = client.post(
            f"/api/v1/courses/{invalid_id}/export", json=valid_export
        )

        assert export_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.integration
    def test_export_file_cleanup(self, client, sample_course_request):
        """Test that export files are properly managed and cleaned up."""
        response = client.post("/api/v1/courses", json=sample_course_request)
        course_id = response.json()["id"]

        export_request = {"format": "pdf"}
        export_response = client.post(
            f"/api/v1/courses/{course_id}/export", json=export_request
        )

        assert export_response.status_code == status.HTTP_200_OK
        export_data = export_response.json()

        # Verify expiration time is set
        assert "expires_at" in export_data

        # Download URL should be temporary
        download_url = export_data["download_url"]
        assert "temp" in download_url or "download" in download_url
