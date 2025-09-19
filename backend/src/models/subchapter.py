"""
Subchapter model implementation with SQLAlchemy and Pydantic.

Based on data-model.md specifications for Subchapter entity.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base
from .enums import ContentType
from .value_objects import ContentBlock, Example, Resource


class SubchapterTable(Base):
    """SQLAlchemy model for Subchapter entity."""

    __tablename__ = "subchapters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    chapter_id = Column(
        PGUUID(as_uuid=True), ForeignKey("chapters.id"), nullable=False, index=True
    )
    sequence_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content_type = Column(String(20), nullable=False)  # ContentType enum
    content_blocks = Column(JSON, nullable=False)  # List[ContentBlock]
    key_concepts = Column(JSON, nullable=False)  # List[str]
    examples = Column(JSON, nullable=True)  # List[Example]
    summary = Column(Text, nullable=True)
    additional_resources = Column(JSON, nullable=True)  # List[Resource]
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    # chapter = relationship("ChapterTable", back_populates="subchapters")


class SubchapterBase(BaseModel):
    """Base schema for Subchapter operations."""

    title: str = Field(..., min_length=3, max_length=200)
    content_type: ContentType
    content_blocks: List[ContentBlock] = Field(..., min_items=1)
    key_concepts: List[str] = Field(..., min_items=1)
    examples: List[Example] = Field(default_factory=list)
    summary: Optional[str] = Field(None, max_length=1000)
    additional_resources: List[Resource] = Field(default_factory=list)

    @validator("content_blocks")
    def validate_content_blocks_order(cls, v):
        """Ensure content blocks have sequential order starting from 1."""
        if not v:
            raise ValueError("At least one content block is required")
        
        orders = [block.order for block in v]
        expected_orders = list(range(1, len(v) + 1))
        if sorted(orders) != expected_orders:
            raise ValueError(
                "Content blocks must have sequential order starting from 1"
            )
        return v

    @validator("key_concepts")
    def validate_key_concepts(cls, v):
        """Validate key concepts are not empty and unique."""
        if not v:
            raise ValueError("At least one key concept is required")
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Key concepts must be unique")
        
        # Check each concept is meaningful
        for concept in v:
            if len(concept.strip()) < 2:
                raise ValueError("Each key concept must be at least 2 characters")
        
        return v

    @validator("summary")
    def validate_summary(cls, v):
        """Validate summary content if provided."""
        if v is not None and len(v.strip()) < 10:
            raise ValueError("Summary must be at least 10 characters if provided")
        return v


class SubchapterCreate(SubchapterBase):
    """Schema for creating a new subchapter."""

    chapter_id: UUID
    sequence_number: int = Field(..., ge=1)

    @validator("sequence_number")
    def validate_sequence_number(cls, v):
        """Ensure sequence number is positive."""
        if v < 1:
            raise ValueError("Sequence number must start from 1")
        return v


class SubchapterUpdate(BaseModel):
    """Schema for updating an existing subchapter."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content_type: Optional[ContentType] = None
    content_blocks: Optional[List[ContentBlock]] = Field(None, min_items=1)
    key_concepts: Optional[List[str]] = Field(None, min_items=1)
    examples: Optional[List[Example]] = None
    summary: Optional[str] = Field(None, max_length=1000)
    additional_resources: Optional[List[Resource]] = None

    @validator("content_blocks")
    def validate_content_blocks_order(cls, v):
        """Ensure content blocks have sequential order starting from 1."""
        if v is not None:
            orders = [block.order for block in v]
            expected_orders = list(range(1, len(v) + 1))
            if sorted(orders) != expected_orders:
                raise ValueError(
                    "Content blocks must have sequential order starting from 1"
                )
        return v


class Subchapter(SubchapterBase):
    """Complete Subchapter model with all fields."""

    id: UUID
    chapter_id: UUID
    sequence_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator("content_type")
    def validate_content_type_consistency(cls, v, values):
        """Ensure content type matches content blocks."""
        if "content_blocks" in values and values["content_blocks"]:
            blocks = values["content_blocks"]
            
            # Basic consistency checks
            if v == ContentType.THEORY:
                # Theory should primarily be text and diagrams
                non_theory_types = ["video", "code"]
                theory_blocks = [b for b in blocks if b.type.value not in non_theory_types]
                if len(theory_blocks) / len(blocks) < 0.7:
                    raise ValueError(
                        "Theory content should be primarily text and diagrams"
                    )
            elif v == ContentType.PRACTICAL:
                # Practical should have code examples or interactive elements
                practical_types = ["code", "video"]
                practical_blocks = [b for b in blocks if b.type.value in practical_types]
                if len(practical_blocks) == 0:
                    raise ValueError(
                        "Practical content should include code or video blocks"
                    )
        
        return v


class SubchapterListResponse(BaseModel):
    """Schema for subchapter list responses."""

    subchapters: List[Subchapter]
    total_count: int
    chapter_id: UUID
