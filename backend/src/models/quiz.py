"""
Quiz model implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Quiz entity.
Note: Question and Flashcard entities moved to separate files.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base
from .enums import CognitiveLevel, QuizType


class QuizTable(Base):
    """SQLAlchemy model for Quiz entity."""

    __tablename__ = "quizzes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    title = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # QuizType enum
    passing_score = Column(Float, nullable=False)  # 0.0-1.0
    time_limit = Column(String(50), nullable=True)  # ISO 8601 duration
    attempts_allowed = Column(Integer, nullable=False, default=3)
    randomize_questions = Column(Boolean, nullable=False, default=False)
    randomize_answers = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Foreign keys for relationships
    course_id = Column(
        PGUUID(as_uuid=True), ForeignKey("courses.id"), nullable=True, index=True
    )
    chapter_id = Column(
        PGUUID(as_uuid=True), ForeignKey("chapters.id"), nullable=True, index=True
    )

    # Relationships
    # questions = relationship("QuestionTable", back_populates="quiz")
    # course = relationship("CourseTable", back_populates="final_assessment")
    # chapter = relationship("ChapterTable", back_populates="chapter_quiz")


class QuizBase(BaseModel):
    """Base schema for Quiz operations."""

    title: str = Field(..., min_length=3, max_length=200)
    type: QuizType
    passing_score: float = Field(
        ..., ge=0.6, le=0.85, description="Minimum 60%, maximum 85%"
    )
    time_limit: Optional[str] = Field(None, description="ISO 8601 duration format")
    attempts_allowed: int = Field(3, ge=1, le=10)
    randomize_questions: bool = False
    randomize_answers: bool = False

    @validator("time_limit")
    def validate_time_limit(cls, v):
        if v is not None and not v.startswith("PT"):
            raise ValueError("Time limit must be in ISO 8601 format (e.g., PT30M)")
        return v

    @validator("passing_score")
    def validate_passing_score_range(cls, v):
        """Validate passing score follows assessment best practices."""
        if v < 0.6:
            raise ValueError("Passing score should be at least 60% for effective assessment")
        if v > 0.85:
            raise ValueError("Passing score above 85% may be too restrictive")
        return v


class QuizCreate(QuizBase):
    """Schema for creating a new quiz."""

    course_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None

    @validator("course_id", "chapter_id")
    def validate_parent_relationship(cls, v, values):
        """Ensure quiz belongs to either a course or chapter, not both."""
        course_id = values.get("course_id")
        chapter_id = values.get("chapter_id")

        if not course_id and not chapter_id:
            raise ValueError("Quiz must belong to either a course or chapter")
        if course_id and chapter_id:
            raise ValueError("Quiz cannot belong to both course and chapter")
        return v


class QuizUpdate(BaseModel):
    """Schema for updating an existing quiz."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    passing_score: Optional[float] = Field(None, ge=0.6, le=0.85)
    time_limit: Optional[str] = Field(None, description="ISO 8601 duration format")
    attempts_allowed: Optional[int] = Field(None, ge=1, le=10)
    randomize_questions: Optional[bool] = None
    randomize_answers: Optional[bool] = None


class Quiz(QuizBase):
    """Complete Quiz model with all fields."""

    id: UUID
    course_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    # Note: questions relationship handled through question.py imports

    class Config:
        from_attributes = True

    @property
    def parent_type(self) -> str:
        """Get the type of parent entity (course or chapter)."""
        if self.course_id:
            return "course"
        elif self.chapter_id:
            return "chapter"
        return "unknown"

    @property
    def parent_id(self) -> Optional[UUID]:
        """Get the parent entity ID."""
        return self.course_id or self.chapter_id


class QuizListResponse(BaseModel):
    """Schema for quiz list responses."""

    quizzes: List[Quiz]
    total_count: int
    parent_id: Optional[UUID] = None
    parent_type: Optional[str] = None


class QuizAttempt(BaseModel):
    """Schema for quiz attempt tracking."""

    attempt_id: UUID = Field(default_factory=uuid4)
    quiz_id: UUID
    user_id: Optional[UUID] = None  # For future user system integration
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    passed: Optional[bool] = None
    time_taken_seconds: Optional[int] = Field(None, ge=0)
    attempt_number: int = Field(..., ge=1)

    @validator("completed_at")
    def validate_completion_time(cls, v, values):
        """Ensure completion time is after start time."""
        if v is not None and "started_at" in values:
            if v <= values["started_at"]:
                raise ValueError("Completion time must be after start time")
        return v

    @validator("passed")
    def validate_passed_status(cls, v, values):
        """Determine passed status based on score if not explicitly set."""
        if v is None and "score" in values and values["score"] is not None:
            # This would need the quiz's passing_score to determine
            # For now, we'll allow explicit setting
            pass
        return v

    @property
    def is_completed(self) -> bool:
        """Check if attempt is completed."""
        return self.completed_at is not None

    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate attempt duration in minutes."""
        if self.time_taken_seconds is not None:
            return round(self.time_taken_seconds / 60, 1)
        return None


class QuizAnalytics(BaseModel):
    """Schema for quiz performance analytics."""

    quiz_id: UUID
    total_attempts: int = 0
    completed_attempts: int = 0
    average_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    pass_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    average_completion_time_minutes: Optional[float] = None
    difficulty_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)

    @property
    def completion_rate(self) -> Optional[float]:
        """Calculate completion rate percentage."""
        if self.total_attempts == 0:
            return None
        return round((self.completed_attempts / self.total_attempts) * 100, 1)

    @validator("pass_rate", "average_score")
    def validate_rates(cls, v):
        """Ensure rates are within valid ranges."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Rates must be between 0.0 and 1.0")
        return v

    @validator("difficulty_rating")
    def validate_difficulty_rating(cls, v):
        """Validate difficulty rating."""
        if v is not None and (v < 1.0 or v > 5.0):
            raise ValueError("Difficulty rating must be between 1.0 and 5.0")
        return v