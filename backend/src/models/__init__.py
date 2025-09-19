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
)
from .course import (
    Course,
    CourseBase,
    CourseCreate,
    CourseListResponse,
    CourseTable,
    CourseUpdate,
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
from .flashcard import (
    Flashcard,
    FlashcardBase,
    FlashcardCreate,
    FlashcardListResponse,
    FlashcardReview,
    FlashcardSession,
    FlashcardTable,
    FlashcardUpdate,
)
from .question import (
    Question,
    QuestionAnalytics,
    QuestionBase,
    QuestionCreate,
    QuestionListResponse,
    QuestionTable,
    QuestionUpdate,
)
from .quiz import (
    Quiz,
    QuizAnalytics,
    QuizAttempt,
    QuizBase,
    QuizCreate,
    QuizListResponse,
    QuizTable,
    QuizUpdate,
)
from .subchapter import (
    Subchapter,
    SubchapterBase,
    SubchapterCreate,
    SubchapterListResponse,
    SubchapterTable,
    SubchapterUpdate,
)
from .value_objects import (
    ContentBlock,
    Example,
    QualityMetrics,
    Resource,
    SpacedRepetitionData,
    TargetAudience,
)

# Import API key models from auth module
try:
    from ..auth.api_key_auth import APIKeyTable, APIKeyUsageLog
    _auth_models_available = True
except ImportError:
    _auth_models_available = False

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
    "SubchapterUpdate",
    "QuizUpdate",
    "QuestionUpdate",
    "FlashcardUpdate",
    # Complete Models
    "Course",
    "Chapter",
    "Subchapter",
    "Quiz",
    "Question",
    "Flashcard",
    # Response Schemas
    "CourseListResponse",
    "SubchapterListResponse",
    "QuizListResponse",
    "QuestionListResponse",
    "FlashcardListResponse",
    # Analytics and Tracking
    "QuizAttempt",
    "QuizAnalytics",
    "QuestionAnalytics",
    "FlashcardReview",
    "FlashcardSession",
]

# Add auth models to exports if available
if _auth_models_available:
    __all__.extend(["APIKeyTable", "APIKeyUsageLog"])