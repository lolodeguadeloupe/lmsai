"""
Chapter model implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Chapter entity.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base
from .enums import ContentType
from .value_objects import ContentBlock, Example, Resource


class ChapterTable(Base):
    """SQLAlchemy model for Chapter entity."""

    __tablename__ = "chapters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    course_id = Column(
        PGUUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    sequence_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    learning_objectives = Column(JSON, nullable=False)  # List[str]
    estimated_duration = Column(String(50), nullable=False)  # ISO 8601 duration
    complexity_level = Column(Float, nullable=False)
    prerequisites = Column(JSON, nullable=False)  # List[str]
    content_outline = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # course = relationship("CourseTable", back_populates="chapters")
    # subchapters = relationship("SubchapterTable", back_populates="chapter")
    # chapter_quiz = relationship("QuizTable", back_populates="chapter")


# Subchapter entity moved to subchapter.py


# ContentBlock moved to value_objects.py


# Resource moved to value_objects.py


# Example moved to value_objects.py


class ChapterBase(BaseModel):
    """Base schema for Chapter operations."""

    title: str = Field(..., min_length=3, max_length=200)
    learning_objectives: List[str] = Field(..., min_items=1, max_items=8)
    estimated_duration: str = Field(..., description="ISO 8601 duration format")
    complexity_level: float = Field(..., ge=1.0, le=5.0)
    prerequisites: List[str] = Field(default_factory=list)
    content_outline: Optional[str] = Field(None, max_length=2000)

    @validator("learning_objectives")
    def validate_objectives(cls, v):
        for obj in v:
            if len(obj.strip()) < 5:
                raise ValueError(
                    "Each learning objective must be at least 5 characters"
                )
        return v

    @validator("estimated_duration")
    def validate_duration(cls, v):
        if not v.startswith("PT"):
            raise ValueError("Duration must be in ISO 8601 format (e.g., PT30M)")
        return v


# Subchapter schemas moved to subchapter.py


class ChapterCreate(ChapterBase):
    """Schema for creating a new chapter."""

    course_id: UUID
    sequence_number: int = Field(..., ge=1)


# SubchapterCreate moved to subchapter.py


class ChapterUpdate(BaseModel):
    """Schema for updating an existing chapter."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    learning_objectives: Optional[List[str]] = Field(None, min_items=1, max_items=8)
    content_outline: Optional[str] = Field(None, max_length=2000)


# Subchapter moved to subchapter.py


class Chapter(ChapterBase):
    """Complete Chapter model with all fields."""

    id: UUID
    course_id: UUID
    sequence_number: int
    created_at: datetime
    updated_at: datetime
    subchapters: List[Subchapter] = Field(default_factory=list)

    class Config:
        from_attributes = True

    @validator("complexity_level")
    def validate_complexity_relative_to_course(cls, v, values):
        """Ensure chapter complexity doesn't exceed course difficulty + 0.5."""
        # Note: This validation would need course context in practice
        # For now, we'll implement basic validation
        if v > 5.0:
            raise ValueError("Chapter complexity cannot exceed 5.0")
        return v

    @validator("sequence_number")
    def validate_sequence_number(cls, v):
        """Ensure sequence number is positive."""
        if v < 1:
            raise ValueError("Sequence number must start from 1")
        return v
