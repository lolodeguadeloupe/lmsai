"""
OpenAI/Anthropic AI client wrapper for course generation platform.

Implements T038: Unified AI client supporting both OpenAI and Anthropic APIs
with methods for course content generation, quality validation, and analysis.

Key Features:
- Unified interface for multiple AI providers
- Async support with streaming responses
- Rate limiting and error handling
- Pydantic models for request/response validation
- Content quality assessment and bias detection
- Readability analysis with level-specific thresholds
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import openai
import anthropic
import httpx
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    # Fallback textstat implementation for basic functionality
    class MockTextstat:
        @staticmethod
        def flesch_kincaid_grade(text):
            # Simple approximation based on sentence and word length
            sentences = text.count('.') + text.count('!') + text.count('?')
            words = len(text.split())
            if sentences == 0:
                return 8.0
            return max(1.0, min(20.0, (words / sentences) * 0.5))
        
        @staticmethod
        def flesch_reading_ease(text):
            # Simple approximation - inversely related to complexity
            grade = MockTextstat.flesch_kincaid_grade(text)
            return max(0, min(100, 100 - (grade * 5)))
        
        @staticmethod
        def coleman_liau_index(text):
            return MockTextstat.flesch_kincaid_grade(text) + 1.0
        
        @staticmethod
        def automated_readability_index(text):
            return MockTextstat.flesch_kincaid_grade(text) - 0.5
    
    textstat = MockTextstat()
from pydantic import BaseModel, Field, validator
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from ..models.enums import ProficiencyLevel, CognitiveLevel, DifficultyLevel
try:
    from ..core.config import settings
except ImportError:
    # Fallback for testing without full app context
    class MockSettings:
        OPENAI_API_KEY: Optional[str] = None
        ANTHROPIC_API_KEY: Optional[str] = None
    settings = MockSettings()

# Configure logging
logger = logging.getLogger(__name__)


# Request/Response Models
class CourseStructureRequest(BaseModel):
    """Request model for course structure generation."""
    
    title: str = Field(..., min_length=3, max_length=200)
    subject_domain: str = Field(..., min_length=2, max_length=100)
    target_level: ProficiencyLevel
    estimated_duration_hours: float = Field(..., gt=0, le=200)
    learning_objectives: List[str] = Field(..., min_items=3, max_items=12)
    prerequisites: List[str] = Field(default_factory=list)
    preferred_language: str = Field(default="en", max_length=5)
    
    @validator('learning_objectives')
    def validate_objectives_format(cls, v):
        """Ensure learning objectives follow SMART format."""
        for obj in v:
            if len(obj) < 10:
                raise ValueError("Learning objectives must be descriptive (min 10 chars)")
        return v


class ChapterContentRequest(BaseModel):
    """Request model for chapter content generation."""
    
    chapter_title: str = Field(..., min_length=3, max_length=150)
    learning_objectives: List[str] = Field(..., min_items=1, max_items=5)
    target_level: ProficiencyLevel
    sequence_number: int = Field(..., ge=1)
    previous_concepts: List[str] = Field(default_factory=list)
    content_type: str = Field(default="mixed")  # theory, practical, mixed
    estimated_duration_minutes: int = Field(..., gt=0, le=480)
    include_examples: bool = Field(default=True)
    include_exercises: bool = Field(default=True)
    
    
class ContentValidationRequest(BaseModel):
    """Request model for content quality validation."""
    
    content: str = Field(..., min_length=100)
    target_level: ProficiencyLevel
    learning_objectives: List[str] = Field(..., min_items=1)
    subject_domain: str
    expected_keywords: List[str] = Field(default_factory=list)


class ReadabilityAnalysisRequest(BaseModel):
    """Request model for readability analysis."""
    
    content: str = Field(..., min_length=50)
    target_level: ProficiencyLevel
    content_type: str = Field(default="educational")


class BiasDetectionRequest(BaseModel):
    """Request model for bias detection analysis."""
    
    content: str = Field(..., min_length=100)
    check_categories: List[str] = Field(
        default_factory=lambda: ["gender", "cultural", "racial", "age", "socioeconomic"]
    )


class CourseStructureResponse(BaseModel):
    """Response model for course structure generation."""
    
    chapters: List[Dict[str, Any]]
    estimated_total_duration: float
    difficulty_progression: List[float]
    suggested_prerequisites: List[str]
    learning_path_rationale: str
    quality_indicators: Dict[str, float]


class ChapterContentResponse(BaseModel):
    """Response model for chapter content generation."""
    
    content_blocks: List[Dict[str, Any]]
    key_concepts: List[str]
    examples: List[Dict[str, Any]]
    exercises: List[Dict[str, Any]]
    summary: str
    estimated_reading_time: int
    complexity_score: float


class ContentQualityResponse(BaseModel):
    """Response model for content quality validation."""
    
    overall_score: float = Field(..., ge=0, le=1)
    readability_score: float = Field(..., ge=0, le=100)
    pedagogical_alignment: float = Field(..., ge=0, le=1)
    objective_coverage: float = Field(..., ge=0, le=1)
    content_accuracy: float = Field(..., ge=0, le=1)
    recommendations: List[str]
    issues_found: List[Dict[str, Any]]


class ReadabilityAnalysisResponse(BaseModel):
    """Response model for readability analysis."""
    
    flesch_kincaid_score: float
    flesch_reading_ease: float
    coleman_liau_index: float
    automated_readability_index: float
    grade_level: str
    meets_target_level: bool
    recommendations: List[str]


class BiasDetectionResponse(BaseModel):
    """Response model for bias detection."""
    
    overall_bias_score: float = Field(..., ge=0, le=1)
    category_scores: Dict[str, float]
    detected_issues: List[Dict[str, Any]]
    severity_level: str  # low, medium, high
    recommendations: List[str]


# Rate Limiting
class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def acquire(self):
        """Acquire permission to make an API call."""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.calls.append(now)


# Base AI Provider Interface
class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_course_structure(
        self, request: CourseStructureRequest
    ) -> CourseStructureResponse:
        """Generate course structure with chapters and learning progression."""
        pass
    
    @abstractmethod
    async def generate_chapter_content(
        self, request: ChapterContentRequest
    ) -> ChapterContentResponse:
        """Generate detailed content for a specific chapter."""
        pass
    
    @abstractmethod
    async def generate_chapter_content_stream(
        self, request: ChapterContentRequest
    ) -> AsyncGenerator[str, None]:
        """Generate chapter content with streaming response."""
        pass
    
    @abstractmethod
    async def validate_content_quality(
        self, request: ContentValidationRequest
    ) -> ContentQualityResponse:
        """Validate content quality against pedagogical standards."""
        pass


# OpenAI Provider Implementation
class OpenAIProvider(AIProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", rate_limit: int = 60):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.rate_limiter = RateLimiter(rate_limit)
        
    async def generate_course_structure(
        self, request: CourseStructureRequest
    ) -> CourseStructureResponse:
        """Generate course structure using OpenAI GPT."""
        await self.rate_limiter.acquire()
        
        # Calculate chapter count based on level and duration
        level_multipliers = {
            ProficiencyLevel.BEGINNER: 0.3,
            ProficiencyLevel.INTERMEDIATE: 0.4,
            ProficiencyLevel.ADVANCED: 0.5,
            ProficiencyLevel.EXPERT: 0.6,
        }
        
        estimated_chapters = max(3, min(15, int(
            request.estimated_duration_hours * level_multipliers[request.target_level]
        )))
        
        prompt = self._build_structure_prompt(request, estimated_chapters)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_structure_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result_data = json.loads(content)
            
            return CourseStructureResponse(**result_data)
            
        except Exception as e:
            logger.error(f"OpenAI course structure generation failed: {e}")
            raise RuntimeError(f"Course structure generation failed: {str(e)}")
    
    async def generate_chapter_content(
        self, request: ChapterContentRequest
    ) -> ChapterContentResponse:
        """Generate chapter content using OpenAI GPT."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_content_prompt(request)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_content_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result_data = json.loads(content)
            
            return ChapterContentResponse(**result_data)
            
        except Exception as e:
            logger.error(f"OpenAI chapter content generation failed: {e}")
            raise RuntimeError(f"Chapter content generation failed: {str(e)}")
    
    async def generate_chapter_content_stream(
        self, request: ChapterContentRequest
    ) -> AsyncGenerator[str, None]:
        """Generate chapter content with streaming response."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_content_prompt(request)
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_content_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=4000,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming content generation failed: {e}")
            raise RuntimeError(f"Streaming content generation failed: {str(e)}")
    
    async def validate_content_quality(
        self, request: ContentValidationRequest
    ) -> ContentQualityResponse:
        """Validate content quality using OpenAI GPT."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_validation_prompt(request)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_validation_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result_data = json.loads(content)
            
            return ContentQualityResponse(**result_data)
            
        except Exception as e:
            logger.error(f"OpenAI content validation failed: {e}")
            raise RuntimeError(f"Content validation failed: {str(e)}")
    
    def _get_structure_system_prompt(self) -> str:
        """Get system prompt for course structure generation."""
        return """You are an expert educational designer. Generate well-structured course outlines 
        that follow pedagogical best practices. Ensure progressive difficulty, clear learning objectives,
        and appropriate content distribution. Return valid JSON only."""
    
    def _get_content_system_prompt(self) -> str:
        """Get system prompt for chapter content generation."""
        return """You are an expert content creator for educational materials. Create engaging,
        clear, and pedagogically sound content appropriate for the target audience level.
        Include practical examples and exercises. Return valid JSON only."""
    
    def _get_validation_system_prompt(self) -> str:
        """Get system prompt for content validation."""
        return """You are an expert educational quality assessor. Evaluate content for pedagogical
        effectiveness, clarity, accuracy, and appropriateness for the target level.
        Provide specific, actionable feedback. Return valid JSON only."""
    
    def _build_structure_prompt(self, request: CourseStructureRequest, chapter_count: int) -> str:
        """Build prompt for course structure generation."""
        return f"""
        Create a course structure for:
        Title: {request.title}
        Subject: {request.subject_domain}
        Target Level: {request.target_level.value}
        Duration: {request.estimated_duration_hours} hours
        Learning Objectives: {', '.join(request.learning_objectives)}
        Prerequisites: {', '.join(request.prerequisites) if request.prerequisites else 'None'}
        
        Generate approximately {chapter_count} chapters with progressive difficulty.
        
        Return JSON with the following structure:
        {{
            "chapters": [
                {{
                    "sequence_number": 1,
                    "title": "Chapter Title",
                    "learning_objectives": ["objective1", "objective2"],
                    "estimated_duration": 2.5,
                    "complexity_level": 2.0,
                    "prerequisites": ["concept1"],
                    "content_outline": "Brief outline"
                }}
            ],
            "estimated_total_duration": {request.estimated_duration_hours},
            "difficulty_progression": [1.0, 1.5, 2.0],
            "suggested_prerequisites": ["prereq1"],
            "learning_path_rationale": "Explanation of the learning progression",
            "quality_indicators": {{"progression_smoothness": 0.9, "objective_coverage": 1.0}}
        }}
        """
    
    def _build_content_prompt(self, request: ChapterContentRequest) -> str:
        """Build prompt for chapter content generation."""
        return f"""
        Create detailed content for:
        Chapter: {request.chapter_title}
        Learning Objectives: {', '.join(request.learning_objectives)}
        Target Level: {request.target_level.value}
        Duration: {request.estimated_duration_minutes} minutes
        Content Type: {request.content_type}
        Previous Concepts: {', '.join(request.previous_concepts) if request.previous_concepts else 'None'}
        
        Include {'examples' if request.include_examples else 'no examples'} and {'exercises' if request.include_exercises else 'no exercises'}.
        
        Return JSON with the following structure:
        {{
            "content_blocks": [
                {{
                    "type": "text",
                    "content": "Main content text",
                    "order": 1
                }}
            ],
            "key_concepts": ["concept1", "concept2"],
            "examples": [
                {{
                    "title": "Example Title",
                    "description": "Example description",
                    "code_or_content": "Example content"
                }}
            ],
            "exercises": [
                {{
                    "title": "Exercise Title",
                    "description": "Exercise description",
                    "difficulty": "easy",
                    "estimated_time": 10
                }}
            ],
            "summary": "Chapter summary",
            "estimated_reading_time": {request.estimated_duration_minutes},
            "complexity_score": 2.5
        }}
        """
    
    def _build_validation_prompt(self, request: ContentValidationRequest) -> str:
        """Build prompt for content validation."""
        return f"""
        Evaluate this educational content:
        Target Level: {request.target_level.value}
        Subject: {request.subject_domain}
        Learning Objectives: {', '.join(request.learning_objectives)}
        Expected Keywords: {', '.join(request.expected_keywords) if request.expected_keywords else 'None'}
        
        Content to evaluate:
        {request.content[:2000]}...
        
        Return JSON with the following structure:
        {{
            "overall_score": 0.85,
            "readability_score": 75.0,
            "pedagogical_alignment": 0.9,
            "objective_coverage": 0.95,
            "content_accuracy": 0.9,
            "recommendations": ["recommendation1", "recommendation2"],
            "issues_found": [
                {{
                    "type": "readability",
                    "severity": "medium",
                    "description": "Issue description",
                    "location": "paragraph 3"
                }}
            ]
        }}
        """


# Anthropic Provider Implementation
class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", rate_limit: int = 60):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.rate_limiter = RateLimiter(rate_limit)
    
    async def generate_course_structure(
        self, request: CourseStructureRequest
    ) -> CourseStructureResponse:
        """Generate course structure using Anthropic Claude."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_structure_prompt(request)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=self._get_structure_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            # Claude doesn't enforce JSON mode, so we need to extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_content = content[json_start:json_end]
            
            result_data = json.loads(json_content)
            return CourseStructureResponse(**result_data)
            
        except Exception as e:
            logger.error(f"Anthropic course structure generation failed: {e}")
            raise RuntimeError(f"Course structure generation failed: {str(e)}")
    
    async def generate_chapter_content(
        self, request: ChapterContentRequest
    ) -> ChapterContentResponse:
        """Generate chapter content using Anthropic Claude."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_content_prompt(request)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.6,
                system=self._get_content_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_content = content[json_start:json_end]
            
            result_data = json.loads(json_content)
            return ChapterContentResponse(**result_data)
            
        except Exception as e:
            logger.error(f"Anthropic chapter content generation failed: {e}")
            raise RuntimeError(f"Chapter content generation failed: {str(e)}")
    
    async def generate_chapter_content_stream(
        self, request: ChapterContentRequest
    ) -> AsyncGenerator[str, None]:
        """Generate chapter content with streaming response."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_content_prompt(request)
        
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4000,
                temperature=0.6,
                system=self._get_content_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming content generation failed: {e}")
            raise RuntimeError(f"Streaming content generation failed: {str(e)}")
    
    async def validate_content_quality(
        self, request: ContentValidationRequest
    ) -> ContentQualityResponse:
        """Validate content quality using Anthropic Claude."""
        await self.rate_limiter.acquire()
        
        prompt = self._build_validation_prompt(request)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                system=self._get_validation_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_content = content[json_start:json_end]
            
            result_data = json.loads(json_content)
            return ContentQualityResponse(**result_data)
            
        except Exception as e:
            logger.error(f"Anthropic content validation failed: {e}")
            raise RuntimeError(f"Content validation failed: {str(e)}")
    
    def _get_structure_system_prompt(self) -> str:
        """Get system prompt for course structure generation."""
        return """You are an expert educational designer with deep knowledge of learning science 
        and instructional design. Create comprehensive course structures that follow evidence-based 
        pedagogical principles. Always return valid JSON in the exact format requested."""
    
    def _get_content_system_prompt(self) -> str:
        """Get system prompt for chapter content generation."""
        return """You are an expert educational content creator. Generate clear, engaging, and 
        pedagogically effective content that matches the target audience level. Include practical 
        applications and scaffolded learning. Always return valid JSON in the exact format requested."""
    
    def _get_validation_system_prompt(self) -> str:
        """Get system prompt for content validation."""
        return """You are an expert educational quality assessor with expertise in learning 
        sciences, content evaluation, and pedagogical effectiveness. Provide thorough, objective 
        assessments with specific recommendations. Always return valid JSON in the exact format requested."""
    
    def _build_structure_prompt(self, request: CourseStructureRequest) -> str:
        """Build prompt for course structure generation."""
        level_guidelines = {
            ProficiencyLevel.BEGINNER: "3-5 chapters, simple concepts, lots of examples",
            ProficiencyLevel.INTERMEDIATE: "5-8 chapters, moderate complexity, practical applications",
            ProficiencyLevel.ADVANCED: "8-12 chapters, complex concepts, deep analysis",
            ProficiencyLevel.EXPERT: "10-15 chapters, cutting-edge topics, research-level content"
        }
        
        return f"""Create a comprehensive course structure for "{request.title}" in {request.subject_domain}.

Target audience: {request.target_level.value} level learners
Duration: {request.estimated_duration_hours} hours
Prerequisites: {', '.join(request.prerequisites) if request.prerequisites else 'None'}

Learning Objectives:
{chr(10).join(f"- {obj}" for obj in request.learning_objectives)}

Guidelines for {request.target_level.value} level: {level_guidelines[request.target_level]}

Please provide a JSON response with the exact structure:
{{
    "chapters": [array of chapter objects with sequence_number, title, learning_objectives, estimated_duration, complexity_level, prerequisites, content_outline],
    "estimated_total_duration": float,
    "difficulty_progression": [array of float values],
    "suggested_prerequisites": [array of strings],
    "learning_path_rationale": "string explaining the progression logic",
    "quality_indicators": {{"progression_smoothness": float, "objective_coverage": float}}
}}"""
    
    def _build_content_prompt(self, request: ChapterContentRequest) -> str:
        """Build prompt for chapter content generation."""
        return f"""Create detailed educational content for Chapter {request.sequence_number}: "{request.chapter_title}"

Target Level: {request.target_level.value}
Duration: {request.estimated_duration_minutes} minutes
Content Type: {request.content_type}

Learning Objectives:
{chr(10).join(f"- {obj}" for obj in request.learning_objectives)}

Previous Concepts: {', '.join(request.previous_concepts) if request.previous_concepts else 'This is an introductory chapter'}

Requirements:
- {'Include practical examples' if request.include_examples else 'Focus on theory without examples'}
- {'Include hands-on exercises' if request.include_exercises else 'No exercises needed'}
- Content should be appropriate for {request.target_level.value} level learners
- Clear explanations with logical progression

Please provide a JSON response with the exact structure:
{{
    "content_blocks": [array of content block objects with type, content, order],
    "key_concepts": [array of key terms/concepts],
    "examples": [array of example objects with title, description, code_or_content],
    "exercises": [array of exercise objects with title, description, difficulty, estimated_time],
    "summary": "comprehensive chapter summary",
    "estimated_reading_time": integer (minutes),
    "complexity_score": float (1.0-5.0)
}}"""
    
    def _build_validation_prompt(self, request: ContentValidationRequest) -> str:
        """Build prompt for content validation."""
        return f"""Evaluate this educational content for quality and effectiveness:

Subject Domain: {request.subject_domain}
Target Level: {request.target_level.value}

Learning Objectives to assess against:
{chr(10).join(f"- {obj}" for obj in request.learning_objectives)}

Expected Keywords: {', '.join(request.expected_keywords) if request.expected_keywords else 'None specified'}

CONTENT TO EVALUATE:
{request.content}

Please assess the content on:
1. Overall pedagogical quality (0.0-1.0)
2. Readability for target level (0-100 scale)
3. Alignment with learning objectives (0.0-1.0)
4. Coverage of stated objectives (0.0-1.0)
5. Content accuracy and reliability (0.0-1.0)

Provide specific recommendations for improvement and identify any issues.

Return JSON response with exact structure:
{{
    "overall_score": float,
    "readability_score": float,
    "pedagogical_alignment": float,
    "objective_coverage": float,
    "content_accuracy": float,
    "recommendations": [array of strings],
    "issues_found": [array of issue objects with type, severity, description, location]
}}"""


# Content Analysis Utilities
class ReadabilityAnalyzer:
    """Utility class for content readability analysis."""
    
    @staticmethod
    def analyze_readability(request: ReadabilityAnalysisRequest) -> ReadabilityAnalysisResponse:
        """Analyze text readability using multiple metrics."""
        text = request.content
        
        # Calculate various readability metrics
        flesch_kincaid = textstat.flesch_kincaid_grade(text)
        flesch_ease = textstat.flesch_reading_ease(text)
        coleman_liau = textstat.coleman_liau_index(text)
        ari = textstat.automated_readability_index(text)
        
        # Determine grade level
        avg_grade = (flesch_kincaid + coleman_liau + ari) / 3
        grade_level = f"Grade {avg_grade:.1f}"
        
        # Check if meets target level thresholds
        level_thresholds = {
            ProficiencyLevel.BEGINNER: 70.0,
            ProficiencyLevel.INTERMEDIATE: 60.0,
            ProficiencyLevel.ADVANCED: 50.0,
            ProficiencyLevel.EXPERT: 0.0,  # No minimum for expert
        }
        
        threshold = level_thresholds[request.target_level]
        meets_target = flesch_ease >= threshold
        
        # Generate recommendations
        recommendations = []
        if not meets_target:
            recommendations.append(f"Readability score {flesch_ease:.1f} below target {threshold}")
            recommendations.append("Consider simplifying sentence structure")
            recommendations.append("Use more common vocabulary where possible")
        
        if avg_grade > 12:
            recommendations.append("Content may be too complex for general audience")
        
        return ReadabilityAnalysisResponse(
            flesch_kincaid_score=flesch_kincaid,
            flesch_reading_ease=flesch_ease,
            coleman_liau_index=coleman_liau,
            automated_readability_index=ari,
            grade_level=grade_level,
            meets_target_level=meets_target,
            recommendations=recommendations
        )


class BiasDetector:
    """Utility class for detecting potential bias in educational content."""
    
    BIAS_KEYWORDS = {
        "gender": ["he should", "she should", "guys", "mankind", "manpower"],
        "cultural": ["primitive", "third world", "exotic", "normal family"],
        "racial": ["articulate", "urban", "inner city", "ethnic"],
        "age": ["elderly", "senior moment", "young people these days"],
        "socioeconomic": ["poor people", "welfare", "trailer park", "ghetto"]
    }
    
    @classmethod
    async def detect_bias(cls, request: BiasDetectionRequest) -> BiasDetectionResponse:
        """Detect potential bias in content."""
        content_lower = request.content.lower()
        
        category_scores = {}
        detected_issues = []
        
        for category in request.check_categories:
            if category in cls.BIAS_KEYWORDS:
                keywords = cls.BIAS_KEYWORDS[category]
                found_keywords = [kw for kw in keywords if kw in content_lower]
                
                score = min(len(found_keywords) * 0.2, 1.0)  # Max 1.0
                category_scores[category] = score
                
                for keyword in found_keywords:
                    detected_issues.append({
                        "category": category,
                        "keyword": keyword,
                        "severity": "medium" if score > 0.5 else "low",
                        "suggestion": f"Consider replacing '{keyword}' with more inclusive language"
                    })
            else:
                category_scores[category] = 0.0
        
        overall_score = sum(category_scores.values()) / len(category_scores)
        
        # Determine severity
        if overall_score > 0.7:
            severity = "high"
        elif overall_score > 0.3:
            severity = "medium"
        else:
            severity = "low"
        
        # Generate recommendations
        recommendations = []
        if overall_score > 0.1:
            recommendations.append("Review content for inclusive language")
            recommendations.append("Consider diverse perspectives and examples")
        
        return BiasDetectionResponse(
            overall_bias_score=overall_score,
            category_scores=category_scores,
            detected_issues=detected_issues,
            severity_level=severity,
            recommendations=recommendations
        )


# Main AI Client Wrapper
class AIClient:
    """Unified AI client wrapper supporting multiple providers."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        preferred_provider: str = "openai",
        fallback_enabled: bool = True
    ):
        """Initialize AI client with provider configurations."""
        self.providers = {}
        self.preferred_provider = preferred_provider
        self.fallback_enabled = fallback_enabled
        
        # Initialize providers
        if openai_api_key:
            self.providers["openai"] = OpenAIProvider(openai_api_key)
        
        if anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(anthropic_api_key)
        
        if not self.providers:
            raise ValueError("At least one AI provider API key must be provided")
        
        # Set default provider
        if preferred_provider not in self.providers:
            self.preferred_provider = list(self.providers.keys())[0]
    
    async def generate_course_structure(
        self, request: CourseStructureRequest
    ) -> CourseStructureResponse:
        """Generate course structure using preferred provider with fallback."""
        return await self._execute_with_fallback(
            lambda provider: provider.generate_course_structure(request)
        )
    
    async def generate_chapter_content(
        self, request: ChapterContentRequest
    ) -> ChapterContentResponse:
        """Generate chapter content using preferred provider with fallback."""
        return await self._execute_with_fallback(
            lambda provider: provider.generate_chapter_content(request)
        )
    
    async def generate_chapter_content_stream(
        self, request: ChapterContentRequest
    ) -> AsyncGenerator[str, None]:
        """Generate chapter content with streaming response."""
        provider = self.providers[self.preferred_provider]
        async for chunk in provider.generate_chapter_content_stream(request):
            yield chunk
    
    async def validate_content_quality(
        self, request: ContentValidationRequest
    ) -> ContentQualityResponse:
        """Validate content quality using AI analysis."""
        return await self._execute_with_fallback(
            lambda provider: provider.validate_content_quality(request)
        )
    
    async def analyze_readability(
        self, request: ReadabilityAnalysisRequest
    ) -> ReadabilityAnalysisResponse:
        """Analyze content readability using statistical methods."""
        return ReadabilityAnalyzer.analyze_readability(request)
    
    async def check_bias_detection(
        self, request: BiasDetectionRequest
    ) -> BiasDetectionResponse:
        """Check content for potential bias using keyword analysis."""
        return await BiasDetector.detect_bias(request)
    
    async def comprehensive_quality_check(
        self, content: str, target_level: ProficiencyLevel, learning_objectives: List[str],
        subject_domain: str
    ) -> Dict[str, Any]:
        """Perform comprehensive quality analysis combining all methods."""
        # Run all analyses concurrently
        tasks = [
            self.validate_content_quality(ContentValidationRequest(
                content=content,
                target_level=target_level,
                learning_objectives=learning_objectives,
                subject_domain=subject_domain
            )),
            self.analyze_readability(ReadabilityAnalysisRequest(
                content=content,
                target_level=target_level
            )),
            self.check_bias_detection(BiasDetectionRequest(content=content))
        ]
        
        ai_quality, readability, bias = await asyncio.gather(*tasks)
        
        # Combine results
        return {
            "ai_quality_assessment": ai_quality.dict(),
            "readability_analysis": readability.dict(),
            "bias_detection": bias.dict(),
            "overall_quality_score": (
                ai_quality.overall_score * 0.5 +
                (readability.flesch_reading_ease / 100) * 0.3 +
                (1 - bias.overall_bias_score) * 0.2
            ),
            "meets_quality_standards": (
                ai_quality.overall_score >= 0.8 and
                readability.meets_target_level and
                bias.overall_bias_score <= 0.3
            )
        }
    
    async def _execute_with_fallback(self, operation):
        """Execute operation with primary provider and fallback to secondary if needed."""
        primary_provider = self.providers[self.preferred_provider]
        
        try:
            return await operation(primary_provider)
        except Exception as e:
            logger.warning(f"Primary provider {self.preferred_provider} failed: {e}")
            
            if self.fallback_enabled and len(self.providers) > 1:
                for provider_name, provider in self.providers.items():
                    if provider_name != self.preferred_provider:
                        try:
                            logger.info(f"Attempting fallback to {provider_name}")
                            return await operation(provider)
                        except Exception as fallback_error:
                            logger.warning(f"Fallback provider {provider_name} failed: {fallback_error}")
            
            # If all providers fail, raise the original exception
            raise e
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all configured providers."""
        return {name: True for name in self.providers.keys()}  # Simplified status check
    
    def switch_provider(self, provider_name: str):
        """Switch to a different provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not configured")
        self.preferred_provider = provider_name


# Factory function for creating AI client
def create_ai_client(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    preferred_provider: str = "openai"
) -> AIClient:
    """Factory function to create AI client with environment defaults."""
    return AIClient(
        openai_api_key=openai_api_key or getattr(settings, 'OPENAI_API_KEY', None),
        anthropic_api_key=anthropic_api_key or getattr(settings, 'ANTHROPIC_API_KEY', None),
        preferred_provider=preferred_provider
    )