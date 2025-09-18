"""
Contract test for GET /api/v1/courses/{courseId}/flashcards endpoint.
"""
from fastapi import status


class TestCourseFlashcards:
    """Contract tests for course flashcards endpoint."""

    def test_get_flashcards_success(self, client, sample_course_id):
        """Test successful flashcards retrieval."""
        response = client.get(f"/api/v1/courses/{sample_course_id}/flashcards")

        # Contract assertions - WILL FAIL until implementation
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "flashcards" in data
        assert "total" in data
        assert isinstance(data["flashcards"], list)

        # Verify flashcard structure
        if data["flashcards"]:
            card = data["flashcards"][0]
            assert "id" in card
            assert "front_content" in card
            assert "back_content" in card
            assert "difficulty_rating" in card
            assert "importance_rating" in card
            assert "spaced_repetition_metadata" in card

    def test_get_flashcards_by_chapter(self, client, sample_course_id):
        """Test flashcards filtered by chapter."""
        chapter_id = "550e8400-e29b-41d4-a716-446655440001"
        response = client.get(
            f"/api/v1/courses/{sample_course_id}/flashcards?chapter_id={chapter_id}"
        )

        assert response.status_code == status.HTTP_200_OK
