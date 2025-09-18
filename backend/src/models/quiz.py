"""
Quiz and Question models implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Quiz and Question entities.
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
from .enums import CognitiveLevel, DifficultyLevel, QuestionType, QuizType


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


class QuestionTable(Base):
    """SQLAlchemy model for Question entity."""

    __tablename__ = "questions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    quiz_id = Column(
        PGUUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False, index=True
    )
    type = Column(String(20), nullable=False)  # QuestionType enum
    question_text = Column(Text, nullable=False)
    difficulty_level = Column(String(10), nullable=False)  # DifficultyLevel enum
    cognitive_level = Column(String(15), nullable=False)  # CognitiveLevel enum
    correct_answers = Column(JSON, nullable=False)  # List[str]
    incorrect_answers = Column(JSON, nullable=True)  # List[str] for multiple choice
    explanation = Column(Text, nullable=True)
    hints = Column(JSON, nullable=True)  # List[str]
    points = Column(Integer, nullable=False, default=1)
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # quiz = relationship("QuizTable", back_populates="questions")


class FlashcardTable(Base):
    """SQLAlchemy model for Flashcard entity."""

    __tablename__ = "flashcards"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    course_id = Column(
        PGUUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    front_content = Column(Text, nullable=False)
    back_content = Column(Text, nullable=False)
    difficulty_rating = Column(Float, nullable=False, default=3.0)  # 1.0-5.0
    importance_rating = Column(Float, nullable=False, default=3.0)  # 1.0-5.0
    spaced_repetition_metadata = Column(JSON, nullable=True)
    related_concepts = Column(JSON, nullable=False)  # List[str]
    tags = Column(JSON, nullable=False)  # List[str]
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SpacedRepetitionData(BaseModel):
    """Value object for spaced repetition algorithm data."""

    ease_factor: float = Field(2.5, ge=1.3, le=5.0)
    interval: int = Field(1, ge=1)  # Days
    repetitions: int = Field(0, ge=0)
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    quality_responses: List[int] = Field(default_factory=list)  # 0-5 scale


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


class QuestionBase(BaseModel):
    """Base schema for Question operations."""

    type: QuestionType
    question_text: str = Field(..., min_length=10)
    difficulty_level: DifficultyLevel
    cognitive_level: CognitiveLevel
    correct_answers: List[str] = Field(..., min_items=1)
    incorrect_answers: Optional[List[str]] = Field(None)
    explanation: Optional[str] = Field(None, max_length=1000)
    hints: Optional[List[str]] = Field(None, max_items=3)
    points: int = Field(1, ge=1, le=10)

    @validator("incorrect_answers")
    def validate_incorrect_answers_for_multiple_choice(cls, v, values):
        """Ensure multiple choice questions have incorrect answers."""
        if "type" in values and values["type"] == QuestionType.MULTIPLE_CHOICE:
            if not v or len(v) < 2:
                raise ValueError(
                    "Multiple choice questions need at least 2 incorrect answers"
                )
            if len(v) > 4:
                raise ValueError(
                    "Multiple choice questions should have at most 4 incorrect answers"
                )
        return v

    @validator("correct_answers")
    def validate_correct_answers_by_type(cls, v, values):
        """Validate correct answers based on question type."""
        if "type" in values:
            question_type = values["type"]
            if question_type == QuestionType.TRUE_FALSE and len(v) != 1:
                raise ValueError(
                    "True/False questions must have exactly one correct answer"
                )
            elif question_type == QuestionType.TRUE_FALSE and v[0].lower() not in [
                "true",
                "false",
            ]:
                raise ValueError("True/False answers must be 'true' or 'false'")
            elif question_type == QuestionType.MULTIPLE_CHOICE and len(v) != 1:
                raise ValueError(
                    "Multiple choice questions must have exactly one correct answer"
                )
        return v


class FlashcardBase(BaseModel):
    """Base schema for Flashcard operations."""

    front_content: str = Field(..., min_length=5, max_length=500)
    back_content: str = Field(..., min_length=5, max_length=1000)
    difficulty_rating: float = Field(3.0, ge=1.0, le=5.0)
    importance_rating: float = Field(3.0, ge=1.0, le=5.0)
    related_concepts: List[str] = Field(..., min_items=1)
    tags: List[str] = Field(..., min_items=1)
    spaced_repetition_metadata: Optional[SpacedRepetitionData] = None


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


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""

    quiz_id: UUID
    sequence_number: int = Field(..., ge=1)


class FlashcardCreate(FlashcardBase):
    """Schema for creating a new flashcard."""

    course_id: UUID


class Question(QuestionBase):
    """Complete Question model with all fields."""

    id: UUID
    quiz_id: UUID
    sequence_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Quiz(QuizBase):
    """Complete Quiz model with all fields."""

    id: UUID
    course_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    questions: List[Question] = Field(default_factory=list)

    class Config:
        from_attributes = True

    @validator("questions")
    def validate_question_distribution(cls, v):
        """Validate cognitive level distribution based on audience level."""
        if not v:
            return v

        # Count questions by cognitive level
        cognitive_counts = {}
        for question in v:
            level = question.cognitive_level
            cognitive_counts[level] = cognitive_counts.get(level, 0) + 1

        total_questions = len(v)

        # Basic validation for cognitive distribution
        if total_questions >= 5:
            remember_pct = (
                cognitive_counts.get(CognitiveLevel.REMEMBER, 0) / total_questions
            )
            understand_pct = (
                cognitive_counts.get(CognitiveLevel.UNDERSTAND, 0) / total_questions
            )

            # Ensure some balance (can be refined based on target audience)
            if remember_pct > 0.7:  # Max 70% memory questions
                raise ValueError("Too many memory-based questions")
            if understand_pct < 0.2 and total_questions >= 10:  # Min 20% understanding
                raise ValueError("Need more understanding-level questions")

        return v


class Flashcard(FlashcardBase):
    """Complete Flashcard model with all fields."""

    id: UUID
    course_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
