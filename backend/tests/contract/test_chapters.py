"""
Contract test for GET /api/v1/courses/{courseId}/chapters endpoint.
"""
from fastapi import status


class TestCourseChapters:
    """Contract tests for course chapters endpoint."""

    def test_get_chapters_success(self, client, sample_course_id):
        """Test successful chapters retrieval."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/chapters")

        # Contract assertions - WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "chapters" in data
        assert isinstance(data["chapters"], list)

        # Verify chapter structure
        if data["chapters"]:
            chapter = data["chapters"][0]
            assert "id" in chapter
            assert "sequence_number" in chapter
            assert "title" in chapter
            assert "learning_objectives" in chapter
            assert "estimated_duration" in chapter
            assert "complexity_level" in chapter

    def test_get_chapters_with_content(self, client, sample_course_id):
        """Test chapters with full content included."""
        response = client.get(
            f"/api/v1/courses/{sample_course_id}/chapters?include_content=true"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if data["chapters"]:
            chapter = data["chapters"][0]
            assert "subchapters" in chapter
            assert "chapter_quiz" in chapter
