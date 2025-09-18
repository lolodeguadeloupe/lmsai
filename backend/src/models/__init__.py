"""
Models module for the course generation platform.

Exports all models and schemas for easy importing.
"""

from .base import Base
from .chapter import (
    Chapter,
    ChapterBase,
    ChapterCreate,
    ChapterTable,
    ChapterUpdate,
    ContentBlock,
    Example,
    Resource,
    Subchapter,
    SubchapterBase,
    SubchapterCreate,
    SubchapterTable,
)
from .course import (
    Course,
    CourseBase,
    CourseCreate,
    CourseListResponse,
    CourseTable,
    CourseUpdate,
    QualityMetrics,
    TargetAudience,
)
from .enums import (
    BlockType,
    CognitiveLevel,
    ContentType,
    CourseStatus,
    DifficultyLevel,
    LearningPreference,
    ProficiencyLevel,
    QuestionType,
    QuizType,
)
from .quiz import (
    Flashcard,
    FlashcardBase,
    FlashcardCreate,
    FlashcardTable,
    Question,
    QuestionBase,
    QuestionCreate,
    QuestionTable,
    Quiz,
    QuizBase,
    QuizCreate,
    QuizTable,
    SpacedRepetitionData,
)

__all__ = [
    # Base
    "Base",
    # Enums
    "CourseStatus",
    "ContentType",
    "BlockType",
    "QuizType",
    "QuestionType",
    "ProficiencyLevel",
    "CognitiveLevel",
    "DifficultyLevel",
    "LearningPreference",
    # SQLAlchemy Tables
    "CourseTable",
    "ChapterTable",
    "SubchapterTable",
    "QuizTable",
    "QuestionTable",
    "FlashcardTable",
    # Value Objects
    "TargetAudience",
    "QualityMetrics",
    "ContentBlock",
    "Resource",
    "Example",
    "SpacedRepetitionData",
    # Base Schemas
    "CourseBase",
    "ChapterBase",
    "SubchapterBase",
    "QuizBase",
    "QuestionBase",
    "FlashcardBase",
    # Create Schemas
    "CourseCreate",
    "ChapterCreate",
    "SubchapterCreate",
    "QuizCreate",
    "QuestionCreate",
    "FlashcardCreate",
    # Update Schemas
    "CourseUpdate",
    "ChapterUpdate",
    # Complete Models
    "Course",
    "Chapter",
    "Subchapter",
    "Quiz",
    "Question",
    "Flashcard",
    # Response Schemas
    "CourseListResponse",
]
