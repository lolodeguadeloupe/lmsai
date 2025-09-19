"""
Value objects for the course generation platform.

Based on data-model.md specifications for shared value objects.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .enums import BlockType, LearningPreference, ProficiencyLevel


class TargetAudience(BaseModel):
    """Value object for target audience specification."""

    proficiency_level: ProficiencyLevel
    prerequisites: List[str] = Field(default_factory=list)
    age_range: Optional[Dict[str, int]] = None  # {"min_age": int, "max_age": int}
    professional_context: Optional[str] = None
    learning_preferences: List[LearningPreference] = Field(default_factory=list)

    @validator("prerequisites")
    def validate_prerequisites(cls, v):
        """Validate prerequisites are meaningful."""
        if v:
            for prereq in v:
                if len(prereq.strip()) < 3:
                    raise ValueError("Each prerequisite must be at least 3 characters")
        return [prereq.strip() for prereq in v if prereq.strip()]

    @validator("age_range")
    def validate_age_range(cls, v):
        """Validate age range structure and values."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("age_range must be a dictionary")
            
            required_keys = {"min_age", "max_age"}
            if not all(key in v for key in required_keys):
                raise ValueError("age_range must contain 'min_age' and 'max_age'")
            
            min_age, max_age = v["min_age"], v["max_age"]
            
            if not isinstance(min_age, int) or not isinstance(max_age, int):
                raise ValueError("Age values must be integers")
            
            if min_age > max_age:
                raise ValueError("min_age cannot be greater than max_age")
            
            if min_age < 5 or max_age > 100:
                raise ValueError("Age range must be between 5 and 100")
            
            if max_age - min_age > 50:
                raise ValueError("Age range cannot span more than 50 years")
        
        return v

    @validator("professional_context")
    def validate_professional_context(cls, v):
        """Validate professional context."""
        if v is not None:
            v = v.strip()
            if len(v) < 3:
                raise ValueError("Professional context must be at least 3 characters")
            if len(v) > 100:
                raise ValueError("Professional context must be at most 100 characters")
        return v

    @validator("learning_preferences")
    def validate_learning_preferences(cls, v):
        """Ensure learning preferences are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Learning preferences must be unique")
        return v


class QualityMetrics(BaseModel):
    """Value object for course quality metrics."""

    readability_score: float = Field(..., ge=0.0, le=100.0)
    pedagogical_alignment: float = Field(..., ge=0.0, le=1.0)
    objective_coverage: float = Field(..., ge=0.0, le=1.0)
    content_accuracy: float = Field(..., ge=0.0, le=1.0)
    bias_detection_score: float = Field(..., ge=0.0, le=1.0)
    user_satisfaction_score: Optional[float] = Field(None, ge=0.0, le=5.0)
    generation_timestamp: datetime

    @validator("readability_score")
    def validate_readability_score(cls, v):
        """Validate readability score based on common scales."""
        # Most readability scores are 0-100, with higher being more readable
        if v < 0 or v > 100:
            raise ValueError("Readability score must be between 0 and 100")
        return round(v, 1)

    @validator("pedagogical_alignment")
    def validate_pedagogical_alignment(cls, v):
        """Validate pedagogical alignment score."""
        # This measures alignment with educational best practices (Bloom's taxonomy, etc.)
        if v < 0 or v > 1:
            raise ValueError("Pedagogical alignment must be between 0.0 and 1.0")
        return round(v, 3)

    @validator("objective_coverage")
    def validate_objective_coverage(cls, v):
        """Validate objective coverage percentage."""
        # Should achieve 100% coverage for complete courses
        if v < 0 or v > 1:
            raise ValueError("Objective coverage must be between 0.0 and 1.0")
        if v < 0.8:  # Warn for low coverage
            # In production, this might log a warning rather than raise
            pass
        return round(v, 3)

    @validator("content_accuracy")
    def validate_content_accuracy(cls, v):
        """Validate content accuracy score."""
        if v < 0 or v > 1:
            raise ValueError("Content accuracy must be between 0.0 and 1.0")
        return round(v, 3)

    @validator("bias_detection_score")
    def validate_bias_detection_score(cls, v):
        """Validate bias detection score (0 = no bias, 1 = high bias)."""
        if v < 0 or v > 1:
            raise ValueError("Bias detection score must be between 0.0 and 1.0")
        return round(v, 3)

    @validator("user_satisfaction_score")
    def validate_user_satisfaction_score(cls, v):
        """Validate user satisfaction score."""
        if v is not None:
            if v < 0 or v > 5:
                raise ValueError("User satisfaction score must be between 0.0 and 5.0")
            return round(v, 1)
        return v

    @property
    def overall_quality_score(self) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            "pedagogical_alignment": 0.25,
            "objective_coverage": 0.25,
            "content_accuracy": 0.25,
            "bias_detection_score": 0.15,  # Inverted (lower is better)
            "readability_score": 0.10,
        }
        
        # Normalize readability score to 0-1 range
        normalized_readability = self.readability_score / 100
        
        # Calculate weighted score (bias score is inverted)
        score = (
            weights["pedagogical_alignment"] * self.pedagogical_alignment +
            weights["objective_coverage"] * self.objective_coverage +
            weights["content_accuracy"] * self.content_accuracy +
            weights["bias_detection_score"] * (1 - self.bias_detection_score) +
            weights["readability_score"] * normalized_readability
        )
        
        return round(score, 3)


class ContentBlock(BaseModel):
    """Value object for content blocks within subchapters."""

    type: BlockType
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    order: int = Field(..., ge=1)

    @validator("content")
    def validate_content_by_type(cls, v, values):
        """Validate content based on block type."""
        v = v.strip()
        if not v:
            raise ValueError("Content cannot be empty")
        
        if "type" in values:
            block_type = values["type"]
            
            if block_type == BlockType.TEXT:
                if len(v) < 10:
                    raise ValueError("Text blocks must have at least 10 characters")
                    
            elif block_type == BlockType.CODE:
                if len(v) < 5:
                    raise ValueError("Code blocks must have at least 5 characters")
                # Basic code validation
                if not any(char in v for char in ["{", "}", "(", ")", ";", "="]):
                    # Very loose check - allow various code formats
                    pass
                    
            elif block_type == BlockType.IMAGE:
                # For images, content might be URL or description
                if len(v) < 5:
                    raise ValueError("Image blocks must have description or URL")
                    
            elif block_type == BlockType.VIDEO:
                # For videos, content might be URL or description
                if len(v) < 5:
                    raise ValueError("Video blocks must have description or URL")
                    
            elif block_type == BlockType.DIAGRAM:
                if len(v) < 10:
                    raise ValueError("Diagram blocks must have description")
        
        return v

    @validator("metadata")
    def validate_metadata_by_type(cls, v, values):
        """Validate metadata based on block type."""
        if "type" in values:
            block_type = values["type"]
            
            if block_type == BlockType.CODE:
                # Code blocks should specify language
                if "language" not in v:
                    raise ValueError("Code blocks must specify programming language in metadata")
                    
            elif block_type == BlockType.IMAGE:
                # Image blocks should have alt text
                if "alt_text" not in v:
                    raise ValueError("Image blocks must have alt_text in metadata for accessibility")
                    
            elif block_type == BlockType.VIDEO:
                # Video blocks should have duration or transcript info
                if "duration" not in v and "transcript_available" not in v:
                    raise ValueError("Video blocks should specify duration or transcript availability")
        
        return v

    @validator("order")
    def validate_order(cls, v):
        """Validate order is positive."""
        if v < 1:
            raise ValueError("Order must be a positive integer starting from 1")
        return v


class Resource(BaseModel):
    """Value object for additional learning resources."""

    title: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., pattern=r"^https?://.+")
    type: str = Field(..., description="Type of resource (article, video, book, etc.)")
    description: Optional[str] = Field(None, max_length=500)
    estimated_time: Optional[str] = Field(None, description="Estimated time to consume resource")
    difficulty_level: Optional[str] = Field(None, pattern=r"^(beginner|intermediate|advanced)$")

    @validator("title")
    def validate_title(cls, v):
        """Validate resource title."""
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Resource title cannot be empty")
        return v

    @validator("url")
    def validate_url(cls, v):
        """Validate resource URL format."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        
        # Basic domain validation
        if "." not in v:
            raise ValueError("URL must contain a valid domain")
        
        return v

    @validator("type")
    def validate_type(cls, v):
        """Validate resource type."""
        v = v.strip().lower()
        allowed_types = {
            "article", "video", "book", "paper", "tutorial", "documentation", 
            "course", "podcast", "blog", "tool", "exercise", "reference"
        }
        
        if v not in allowed_types:
            raise ValueError(f"Resource type must be one of: {', '.join(sorted(allowed_types))}")
        
        return v

    @validator("description")
    def validate_description(cls, v):
        """Validate resource description."""
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError("Resource description should be at least 10 characters if provided")
        return v

    @validator("estimated_time")
    def validate_estimated_time(cls, v):
        """Validate estimated time format."""
        if v is not None:
            v = v.strip()
            # Accept formats like "5 min", "2 hours", "30 minutes"
            time_patterns = ["min", "minute", "hour", "day"]
            if not any(pattern in v.lower() for pattern in time_patterns):
                raise ValueError("Estimated time should include time units (min, hours, etc.)")
        return v


class Example(BaseModel):
    """Value object for practical examples."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    code_snippet: Optional[str] = None
    expected_output: Optional[str] = None
    difficulty: str = Field("medium", pattern=r"^(easy|medium|hard)$")
    language: Optional[str] = Field(None, description="Programming language if code example")
    explanation: Optional[str] = Field(None, max_length=1000)

    @validator("title")
    def validate_title(cls, v):
        """Validate example title."""
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Example title cannot be empty")
        return v

    @validator("description")
    def validate_description(cls, v):
        """Validate example description."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Example description must be at least 10 characters")
        return v

    @validator("code_snippet")
    def validate_code_snippet(cls, v, values):
        """Validate code snippet if provided."""
        if v is not None:
            v = v.strip()
            if len(v) < 5:
                raise ValueError("Code snippet must be at least 5 characters if provided")
            
            # If code is provided, language should be specified
            if "language" not in values or not values["language"]:
                # Don't enforce this strictly, but could log a warning
                pass
        
        return v

    @validator("expected_output")
    def validate_expected_output(cls, v):
        """Validate expected output."""
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError("Expected output cannot be empty if provided")
        return v

    @validator("language")
    def validate_language(cls, v):
        """Validate programming language."""
        if v is not None:
            v = v.strip().lower()
            # Common programming languages
            common_languages = {
                "python", "javascript", "java", "c++", "c#", "c", "go", "rust", 
                "php", "ruby", "swift", "kotlin", "typescript", "sql", "html", 
                "css", "bash", "shell", "r", "matlab", "scala", "perl"
            }
            
            if v not in common_languages:
                # Don't enforce strictly - allow other languages
                pass
        
        return v


class SpacedRepetitionData(BaseModel):
    """Value object for spaced repetition algorithm data."""

    ease_factor: float = Field(2.5, ge=1.3, le=5.0)
    interval: int = Field(1, ge=1)  # Days
    repetitions: int = Field(0, ge=0)
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    quality_responses: List[int] = Field(default_factory=list)  # 0-5 scale

    @validator("ease_factor")
    def validate_ease_factor(cls, v):
        """Validate ease factor according to SuperMemo algorithm."""
        if v < 1.3 or v > 5.0:
            raise ValueError("Ease factor must be between 1.3 and 5.0")
        return round(v, 2)

    @validator("interval")
    def validate_interval(cls, v):
        """Validate interval is reasonable."""
        if v < 1:
            raise ValueError("Interval must be at least 1 day")
        if v > 365:  # More than a year seems excessive
            raise ValueError("Interval cannot exceed 365 days")
        return v

    @validator("quality_responses")
    def validate_quality_responses(cls, v):
        """Validate quality responses follow SuperMemo scale."""
        if v:
            for response in v:
                if response < 0 or response > 5:
                    raise ValueError("Quality responses must be between 0 and 5")
            
            # Keep only last 10 responses for performance
            if len(v) > 10:
                v = v[-10:]
        
        return v

    @validator("next_review")
    def validate_next_review(cls, v, values):
        """Validate next review date is logical."""
        if v is not None and "last_reviewed" in values and values["last_reviewed"]:
            if v <= values["last_reviewed"]:
                raise ValueError("Next review must be after last reviewed date")
        
        return v

    @property
    def average_quality(self) -> Optional[float]:
        """Calculate average quality from recent responses."""
        if not self.quality_responses:
            return None
        return round(sum(self.quality_responses) / len(self.quality_responses), 2)

    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate (quality >= 3) from recent responses."""
        if not self.quality_responses:
            return None
        
        successful = sum(1 for q in self.quality_responses if q >= 3)
        return round(successful / len(self.quality_responses), 2)
