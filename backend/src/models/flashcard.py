"""
Flashcard model implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Flashcard entity with spaced repetition.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base
from .value_objects import SpacedRepetitionData


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

    # Relationships
    # course = relationship("CourseTable", back_populates="flashcards")


class FlashcardBase(BaseModel):
    """Base schema for Flashcard operations."""

    front_content: str = Field(..., min_length=5, max_length=500)
    back_content: str = Field(..., min_length=5, max_length=1000)
    difficulty_rating: float = Field(3.0, ge=1.0, le=5.0)
    importance_rating: float = Field(3.0, ge=1.0, le=5.0)
    related_concepts: List[str] = Field(..., min_items=1)
    tags: List[str] = Field(..., min_items=1)
    spaced_repetition_metadata: Optional[SpacedRepetitionData] = None

    @validator("front_content")
    def validate_front_content(cls, v):
        """Validate front content format and quality."""
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Front content must be at least 5 characters")
        
        # Check for question format or key term
        if not (v.endswith("?") or v.endswith(":") or 
                any(keyword in v.lower() for keyword in 
                    ["what", "how", "why", "when", "where", "define", "explain"])):
            # Allow non-question format but ensure it's a clear prompt
            if len(v.split()) < 2:
                raise ValueError(
                    "Front content should be a clear question or prompt with multiple words"
                )
        
        return v

    @validator("back_content")
    def validate_back_content(cls, v):
        """Validate back content is comprehensive."""
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Back content must be at least 5 characters")
        
        # Ensure answer is meaningful
        if len(v.split()) < 3:
            raise ValueError("Back content should be a comprehensive answer with at least 3 words")
        
        return v

    @validator("related_concepts")
    def validate_related_concepts(cls, v):
        """Validate related concepts are meaningful and unique."""
        if not v:
            raise ValueError("At least one related concept is required")
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Related concepts must be unique")
        
        # Validate each concept
        for concept in v:
            if len(concept.strip()) < 2:
                raise ValueError("Each related concept must be at least 2 characters")
            if concept.strip() != concept:
                raise ValueError("Related concepts should not have leading/trailing whitespace")
        
        return [concept.strip() for concept in v]

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags are meaningful and unique."""
        if not v:
            raise ValueError("At least one tag is required")
        
        # Check for duplicates (case-insensitive)
        lower_tags = [tag.lower() for tag in v]
        if len(lower_tags) != len(set(lower_tags)):
            raise ValueError("Tags must be unique (case-insensitive)")
        
        # Validate each tag
        for tag in v:
            tag_cleaned = tag.strip()
            if len(tag_cleaned) < 2:
                raise ValueError("Each tag must be at least 2 characters")
            if len(tag_cleaned) > 30:
                raise ValueError("Each tag must be at most 30 characters")
            if not tag_cleaned.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Tags should only contain letters, numbers, hyphens, and underscores")
        
        return [tag.strip().lower() for tag in v]

    @validator("difficulty_rating", "importance_rating")
    def validate_ratings(cls, v):
        """Ensure ratings are within valid ranges."""
        if v < 1.0 or v > 5.0:
            raise ValueError("Ratings must be between 1.0 and 5.0")
        return round(v, 1)  # Round to 1 decimal place


class FlashcardCreate(FlashcardBase):
    """Schema for creating a new flashcard."""

    course_id: UUID

    @validator("spaced_repetition_metadata")
    def set_default_spaced_repetition(cls, v):
        """Set default spaced repetition data for new flashcards."""
        if v is None:
            return SpacedRepetitionData()
        return v


class FlashcardUpdate(BaseModel):
    """Schema for updating an existing flashcard."""

    front_content: Optional[str] = Field(None, min_length=5, max_length=500)
    back_content: Optional[str] = Field(None, min_length=5, max_length=1000)
    difficulty_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    importance_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    related_concepts: Optional[List[str]] = Field(None, min_items=1)
    tags: Optional[List[str]] = Field(None, min_items=1)
    spaced_repetition_metadata: Optional[SpacedRepetitionData] = None


class FlashcardReview(BaseModel):
    """Schema for flashcard review responses."""

    flashcard_id: UUID
    quality_rating: int = Field(..., ge=0, le=5, description="Quality of recall (0=blackout, 5=perfect)")
    response_time_seconds: Optional[float] = Field(None, ge=0)
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, max_length=200)

    @validator("quality_rating")
    def validate_quality_rating(cls, v):
        """Validate quality rating follows SuperMemo scale."""
        # SuperMemo quality scale:
        # 0 - complete blackout
        # 1 - incorrect response; correct answer seemed familiar
        # 2 - incorrect response; correct answer seemed easy to recall
        # 3 - correct response given with serious difficulty
        # 4 - correct response given after hesitation
        # 5 - correct response given with perfect recall
        if v < 0 or v > 5:
            raise ValueError("Quality rating must be between 0 and 5")
        return v

    @validator("response_time_seconds")
    def validate_response_time(cls, v):
        """Validate response time is reasonable."""
        if v is not None:
            if v < 0:
                raise ValueError("Response time cannot be negative")
            if v > 300:  # 5 minutes seems excessive for a flashcard
                raise ValueError("Response time seems unreasonably long (>5 minutes)")
        return v


class Flashcard(FlashcardBase):
    """Complete Flashcard model with all fields."""

    id: UUID
    course_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def is_due_for_review(self) -> bool:
        """Check if flashcard is due for review based on spaced repetition."""
        if not self.spaced_repetition_metadata or not self.spaced_repetition_metadata.next_review:
            return True
        return datetime.utcnow() >= self.spaced_repetition_metadata.next_review

    @property
    def days_until_next_review(self) -> Optional[int]:
        """Calculate days until next review."""
        if not self.spaced_repetition_metadata or not self.spaced_repetition_metadata.next_review:
            return 0
        
        delta = self.spaced_repetition_metadata.next_review - datetime.utcnow()
        return max(0, delta.days)

    def update_spaced_repetition(self, quality_rating: int) -> SpacedRepetitionData:
        """Update spaced repetition data based on review quality."""
        if not self.spaced_repetition_metadata:
            sr_data = SpacedRepetitionData()
        else:
            sr_data = self.spaced_repetition_metadata
        
        # SuperMemo 2 algorithm implementation
        if quality_rating >= 3:
            if sr_data.repetitions == 0:
                sr_data.interval = 1
            elif sr_data.repetitions == 1:
                sr_data.interval = 6
            else:
                sr_data.interval = round(sr_data.interval * sr_data.ease_factor)
            
            sr_data.repetitions += 1
        else:
            sr_data.repetitions = 0
            sr_data.interval = 1
        
        # Update ease factor
        sr_data.ease_factor = max(
            1.3,
            sr_data.ease_factor + (0.1 - (5 - quality_rating) * (0.08 + (5 - quality_rating) * 0.02))
        )
        
        # Set next review date
        sr_data.last_reviewed = datetime.utcnow()
        sr_data.next_review = sr_data.last_reviewed + timedelta(days=sr_data.interval)
        
        # Track quality responses (keep last 10)
        sr_data.quality_responses.append(quality_rating)
        if len(sr_data.quality_responses) > 10:
            sr_data.quality_responses = sr_data.quality_responses[-10:]
        
        return sr_data


class FlashcardListResponse(BaseModel):
    """Schema for flashcard list responses."""

    flashcards: List[Flashcard]
    total_count: int
    due_count: int
    course_id: UUID


class FlashcardSession(BaseModel):
    """Schema for flashcard study session."""

    session_id: UUID = Field(default_factory=uuid4)
    course_id: UUID
    flashcard_ids: List[UUID]
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_cards: int = Field(..., ge=1)
    cards_completed: int = Field(0, ge=0)
    average_quality: Optional[float] = Field(None, ge=0, le=5)
    session_duration_seconds: Optional[int] = Field(None, ge=0)

    @validator("cards_completed")
    def validate_cards_completed(cls, v, values):
        """Ensure cards completed doesn't exceed total cards."""
        if "total_cards" in values and v > values["total_cards"]:
            raise ValueError("Cards completed cannot exceed total cards")
        return v

    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.cards_completed == self.total_cards

    @property
    def progress_percentage(self) -> float:
        """Calculate session progress percentage."""
        if self.total_cards == 0:
            return 0.0
        return (self.cards_completed / self.total_cards) * 100
