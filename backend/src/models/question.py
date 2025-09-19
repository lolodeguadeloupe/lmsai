"""
Question model implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Question entity.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base
from .enums import CognitiveLevel, DifficultyLevel, QuestionType


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


class QuestionBase(BaseModel):
    """Base schema for Question operations."""

    type: QuestionType
    question_text: str = Field(..., min_length=10, max_length=2000)
    difficulty_level: DifficultyLevel
    cognitive_level: CognitiveLevel
    correct_answers: List[str] = Field(..., min_items=1)
    incorrect_answers: Optional[List[str]] = Field(None)
    explanation: Optional[str] = Field(None, max_length=1000)
    hints: Optional[List[str]] = Field(None, max_items=3)
    points: int = Field(1, ge=1, le=10)

    @validator("question_text")
    def validate_question_text(cls, v):
        """Validate question text content and format."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Question text must be at least 10 characters")
        
        # Check for question mark or imperative form
        if not (v.endswith("?") or any(word in v.lower() for word in 
                ["complete", "fill", "choose", "select", "identify", "explain", "describe"])):
            raise ValueError("Question text should be in question or imperative form")
        
        return v

    @validator("incorrect_answers")
    def validate_incorrect_answers_for_multiple_choice(cls, v, values):
        """Ensure multiple choice questions have appropriate incorrect answers."""
        if "type" in values and values["type"] == QuestionType.MULTIPLE_CHOICE:
            if not v or len(v) < 2:
                raise ValueError(
                    "Multiple choice questions need at least 2 incorrect answers"
                )
            if len(v) > 4:
                raise ValueError(
                    "Multiple choice questions should have at most 4 incorrect answers"
                )
            
            # Check for duplicate answers
            if len(set(v)) != len(v):
                raise ValueError("Incorrect answers must be unique")
                
        elif "type" in values and values["type"] in [
            QuestionType.TRUE_FALSE, 
            QuestionType.FILL_BLANK, 
            QuestionType.SHORT_ANSWER,
            QuestionType.PRACTICAL
        ]:
            # These question types don't need incorrect answers
            if v is not None and len(v) > 0:
                raise ValueError(f"{values['type'].value} questions should not have incorrect answers")
        
        return v

    @validator("correct_answers")
    def validate_correct_answers_by_type(cls, v, values):
        """Validate correct answers based on question type."""
        if not v:
            raise ValueError("At least one correct answer is required")
            
        if "type" in values:
            question_type = values["type"]
            
            if question_type == QuestionType.TRUE_FALSE:
                if len(v) != 1:
                    raise ValueError(
                        "True/False questions must have exactly one correct answer"
                    )
                if v[0].lower() not in ["true", "false"]:
                    raise ValueError("True/False answers must be 'true' or 'false'")
                    
            elif question_type == QuestionType.MULTIPLE_CHOICE:
                if len(v) != 1:
                    raise ValueError(
                        "Multiple choice questions must have exactly one correct answer"
                    )
                    
            elif question_type == QuestionType.FILL_BLANK:
                # Can have multiple acceptable answers
                for answer in v:
                    if len(answer.strip()) < 1:
                        raise ValueError("Fill-in-the-blank answers cannot be empty")
                        
            elif question_type == QuestionType.SHORT_ANSWER:
                # Can have multiple acceptable answers, check they're meaningful
                for answer in v:
                    if len(answer.strip()) < 2:
                        raise ValueError("Short answer responses must be at least 2 characters")
                        
            elif question_type == QuestionType.PRACTICAL:
                # Practical questions can have various answer formats
                for answer in v:
                    if len(answer.strip()) < 5:
                        raise ValueError("Practical answers must be at least 5 characters")
        
        return v

    @validator("hints")
    def validate_hints(cls, v):
        """Validate hints are meaningful and progressive."""
        if v is not None:
            if len(v) > 3:
                raise ValueError("Maximum 3 hints allowed per question")
            
            for i, hint in enumerate(v):
                if len(hint.strip()) < 5:
                    raise ValueError(f"Hint {i+1} must be at least 5 characters")
                    
            # Check hints are not identical
            if len(set(v)) != len(v):
                raise ValueError("Hints must be unique")
        
        return v

    @validator("points")
    def validate_points_by_difficulty(cls, v, values):
        """Ensure points align with difficulty level."""
        if "difficulty_level" in values:
            difficulty = values["difficulty_level"]
            
            # Suggest point ranges based on difficulty
            if difficulty == DifficultyLevel.EASY and v > 3:
                raise ValueError("Easy questions should typically have 1-3 points")
            elif difficulty == DifficultyLevel.MEDIUM and (v < 2 or v > 6):
                raise ValueError("Medium questions should typically have 2-6 points")
            elif difficulty == DifficultyLevel.HARD and v < 3:
                raise ValueError("Hard questions should typically have 3+ points")
        
        return v


class QuestionCreate(QuestionBase):
    """Schema for creating a new question."""

    quiz_id: UUID
    sequence_number: int = Field(..., ge=1)

    @validator("sequence_number")
    def validate_sequence_number(cls, v):
        """Ensure sequence number is positive."""
        if v < 1:
            raise ValueError("Sequence number must start from 1")
        return v


class QuestionUpdate(BaseModel):
    """Schema for updating an existing question."""

    type: Optional[QuestionType] = None
    question_text: Optional[str] = Field(None, min_length=10, max_length=2000)
    difficulty_level: Optional[DifficultyLevel] = None
    cognitive_level: Optional[CognitiveLevel] = None
    correct_answers: Optional[List[str]] = Field(None, min_items=1)
    incorrect_answers: Optional[List[str]] = None
    explanation: Optional[str] = Field(None, max_length=1000)
    hints: Optional[List[str]] = Field(None, max_items=3)
    points: Optional[int] = Field(None, ge=1, le=10)


class Question(QuestionBase):
    """Complete Question model with all fields."""

    id: UUID
    quiz_id: UUID
    sequence_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator("cognitive_level")
    def validate_cognitive_alignment_with_difficulty(cls, v, values):
        """Ensure cognitive level aligns appropriately with difficulty."""
        if "difficulty_level" in values:
            difficulty = values["difficulty_level"]
            
            # Basic alignment rules (can be refined)
            if difficulty == DifficultyLevel.EASY:
                if v not in [CognitiveLevel.REMEMBER, CognitiveLevel.UNDERSTAND]:
                    raise ValueError(
                        "Easy questions should focus on Remember or Understand levels"
                    )
            elif difficulty == DifficultyLevel.HARD:
                if v in [CognitiveLevel.REMEMBER]:
                    raise ValueError(
                        "Hard questions should go beyond simple recall"
                    )
        
        return v


class QuestionListResponse(BaseModel):
    """Schema for question list responses."""

    questions: List[Question]
    total_count: int
    quiz_id: UUID


class QuestionAnalytics(BaseModel):
    """Schema for question performance analytics."""

    question_id: UUID
    total_attempts: int = 0
    correct_attempts: int = 0
    average_time_seconds: Optional[float] = None
    hint_usage_rate: float = 0.0
    difficulty_rating: float = 0.0  # User-perceived difficulty
    last_analyzed: datetime

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.correct_attempts / self.total_attempts) * 100

    @validator("hint_usage_rate", "difficulty_rating")
    def validate_rates(cls, v):
        """Ensure rates are within valid ranges."""
        if v < 0.0 or v > 5.0:
            raise ValueError("Rates must be between 0.0 and 5.0")
        return v
