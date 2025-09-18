"""
Enumerations for the course generation platform.

Based on data-model.md specifications.
"""

from enum import Enum


class CourseStatus(str, Enum):
    """Course lifecycle status."""

    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentType(str, Enum):
    """Type of content in subchapters."""

    THEORY = "theory"
    PRACTICAL = "practical"
    MIXED = "mixed"


class BlockType(str, Enum):
    """Type of content blocks."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CODE = "code"
    DIAGRAM = "diagram"


class QuizType(str, Enum):
    """Type of quiz assessments."""

    CHAPTER = "chapter"
    FINAL = "final"
    PRACTICE = "practice"


class QuestionType(str, Enum):
    """Type of quiz questions."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    PRACTICAL = "practical"


class ProficiencyLevel(str, Enum):
    """Target audience proficiency levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CognitiveLevel(str, Enum):
    """Bloom's taxonomy cognitive levels."""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class LearningPreference(str, Enum):
    """Learning style preferences."""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
