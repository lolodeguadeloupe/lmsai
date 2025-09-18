"""
Course model implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Course entity.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base
from .enums import CourseStatus, LearningPreference, ProficiencyLevel


class CourseTable(Base):
    """SQLAlchemy model for Course entity."""

    __tablename__ = "courses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    subject_domain = Column(String(100), nullable=False, index=True)
    learning_objectives = Column(JSON, nullable=False)  # List[str]
    estimated_duration = Column(String(50), nullable=False)  # ISO 8601 duration
    difficulty_score = Column(Float, nullable=False)
    language = Column(String(2), nullable=False, default="en")  # ISO 639-1
    version = Column(String(20), nullable=False, default="1.0.0")
    status = Column(SQLEnum(CourseStatus), nullable=False, default=CourseStatus.DRAFT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # JSON fields for complex objects
    target_audience = Column(JSON, nullable=False)  # TargetAudience object
    quality_metrics = Column(JSON, nullable=True)  # QualityMetrics object

    # Relationships (to be implemented with other models)
    # chapters = relationship("ChapterTable", back_populates="course")
    # final_assessment = relationship("QuizTable", back_populates="course")


class TargetAudience(BaseModel):
    """Value object for target audience specification."""

    proficiency_level: ProficiencyLevel
    prerequisites: List[str] = Field(default_factory=list)
    age_range: Optional[dict] = None  # {"min_age": int, "max_age": int}
    professional_context: Optional[str] = None
    learning_preferences: List[LearningPreference] = Field(default_factory=list)

    @validator("age_range")
    def validate_age_range(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("age_range must be a dictionary")
            if "min_age" in v and "max_age" in v:
                if v["min_age"] > v["max_age"]:
                    raise ValueError("min_age cannot be greater than max_age")
                if v["min_age"] < 5 or v["max_age"] > 100:
                    raise ValueError("Age range must be between 5 and 100")
        return v


class QualityMetrics(BaseModel):
    """Value object for course quality metrics."""

    readability_score: float = Field(ge=0.0, le=100.0)
    pedagogical_alignment: float = Field(ge=0.0, le=1.0)
    objective_coverage: float = Field(ge=0.0, le=1.0)
    content_accuracy: float = Field(ge=0.0, le=1.0)
    bias_detection_score: float = Field(ge=0.0, le=1.0)
    user_satisfaction_score: Optional[float] = Field(None, ge=0.0, le=5.0)
    generation_timestamp: datetime


class CourseBase(BaseModel):
    """Base schema for Course operations."""

    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    subject_domain: str = Field(..., max_length=100)
    target_audience: TargetAudience
    learning_objectives: List[str] = Field(..., min_items=3, max_items=12)
    estimated_duration: str = Field(..., description="ISO 8601 duration format")
    difficulty_score: float = Field(..., ge=1.0, le=5.0)
    language: str = Field("en", pattern=r"^[a-z]{2}$")
    version: str = Field("1.0.0", pattern=r"^\d+\.\d+\.\d+$")

    @validator("learning_objectives")
    def validate_learning_objectives(cls, v):
        if not v:
            raise ValueError("At least 3 learning objectives are required")
        for obj in v:
            if len(obj.strip()) < 5:
                raise ValueError(
                    "Each learning objective must be at least 5 characters"
                )
        return v

    @validator("estimated_duration")
    def validate_duration(cls, v):
        # Basic validation for ISO 8601 duration format
        if not v.startswith("PT"):
            raise ValueError("Duration must be in ISO 8601 format (e.g., PT20H)")
        return v


class CourseCreate(CourseBase):
    """Schema for creating a new course."""

    pass


class CourseUpdate(BaseModel):
    """Schema for updating an existing course."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    learning_objectives: Optional[List[str]] = Field(None, min_items=3, max_items=12)
    status: Optional[CourseStatus] = None


class Course(CourseBase):
    """Complete Course model with all fields."""

    id: UUID
    status: CourseStatus = CourseStatus.DRAFT
    created_at: datetime
    updated_at: datetime
    quality_metrics: Optional[QualityMetrics] = None

    class Config:
        from_attributes = True

    @validator("difficulty_score")
    def validate_difficulty_with_audience(cls, v, values):
        """Ensure difficulty aligns with target audience proficiency level."""
        if "target_audience" in values:
            audience = values["target_audience"]
            proficiency = audience.proficiency_level

            # Validation rules from data-model.md
            if proficiency == ProficiencyLevel.BEGINNER and v > 2.5:
                raise ValueError("Beginner courses should have difficulty ≤ 2.5")
            elif proficiency == ProficiencyLevel.INTERMEDIATE and (v < 2.0 or v > 4.0):
                raise ValueError("Intermediate courses should have difficulty 2.0-4.0")
            elif proficiency == ProficiencyLevel.ADVANCED and v < 3.0:
                raise ValueError("Advanced courses should have difficulty ≥ 3.0")
            elif proficiency == ProficiencyLevel.EXPERT and v < 4.0:
                raise ValueError("Expert courses should have difficulty ≥ 4.0")

        return v


class CourseListResponse(BaseModel):
    """Schema for course list responses."""

    courses: List[Course]
    total_count: int
    limit: int
    offset: int
