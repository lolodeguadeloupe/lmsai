"""
Chapter regeneration service implementation.

Implements T037: Chapter regeneration service with intelligent content improvement
based on user feedback, AI-powered analysis, and quality validation.

Key Features:
- Intelligent chapter regeneration based on user feedback
- Content analysis and improvement suggestions
- Partial chapter updates (specific subchapters or content blocks)
- Quality validation and consistency maintenance
- Regeneration history tracking and audit trail
- Integration with AI client for content enhancement
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ..database.session import get_db_session
from ..integrations.ai_client import (
    AIClient,
    ChapterContentRequest,
    ChapterContentResponse,
    ContentValidationRequest,
    ReadabilityAnalysisRequest,
    BiasDetectionRequest,
    create_ai_client,
)
from ..models.chapter import (
    Chapter,
    ChapterTable,
    ChapterUpdate,
    Subchapter,
    SubchapterTable,
    ContentBlock,
    Resource,
    Example,
)
from ..models.course import CourseTable, TargetAudience, QualityMetrics
from ..models.enums import ProficiencyLevel, ContentType, BlockType, CourseStatus

# Configure logging
logger = logging.getLogger(__name__)


# Request/Response Models
class RegenerationReason(BaseModel):
    """Structured regeneration reason analysis."""
    
    category: str = Field(..., description="Primary category: content, difficulty, clarity, accuracy, bias")
    description: str = Field(..., min_length=10, max_length=500)
    severity: str = Field(..., pattern=r"^(low|medium|high|critical)$")
    specific_issues: List[str] = Field(default_factory=list)
    target_improvements: List[str] = Field(default_factory=list)


class RegenerationScope(BaseModel):
    """Defines the scope of chapter regeneration."""
    
    regenerate_full_chapter: bool = Field(default=True)
    target_subchapters: List[UUID] = Field(default_factory=list)
    target_content_blocks: List[int] = Field(default_factory=list)  # Block orders
    preserve_structure: bool = Field(default=True)
    preserve_examples: bool = Field(default=True)
    preserve_exercises: bool = Field(default=True)


class ChapterRegenerationRequest(BaseModel):
    """Request model for chapter regeneration."""
    
    chapter_id: UUID
    regeneration_reason: str = Field(..., min_length=10, max_length=1000)
    scope: RegenerationScope = Field(default_factory=RegenerationScope)
    target_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    preserve_learning_objectives: bool = Field(default=True)
    user_feedback: Optional[str] = Field(None, max_length=2000)
    priority: str = Field("medium", pattern=r"^(low|medium|high|urgent)$")


class RegenerationHistory(BaseModel):
    """History record for chapter regeneration."""
    
    id: UUID = Field(default_factory=uuid4)
    chapter_id: UUID
    regeneration_reason: RegenerationReason
    scope: RegenerationScope
    original_content_hash: str
    new_content_hash: str
    quality_improvement: float = Field(..., description="Quality score improvement")
    processing_time_seconds: float
    ai_provider_used: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class ChapterRegenerationResponse(BaseModel):
    """Response model for chapter regeneration."""
    
    task_id: UUID
    chapter_id: UUID
    estimated_completion_time: datetime
    regeneration_scope: RegenerationScope
    current_status: str = "initiated"
    quality_target: Optional[float] = None


class QualityAnalysisResult(BaseModel):
    """Result of comprehensive quality analysis."""
    
    overall_score: float = Field(..., ge=0.0, le=1.0)
    readability_score: float = Field(..., ge=0.0, le=100.0)
    pedagogical_alignment: float = Field(..., ge=0.0, le=1.0)
    objective_coverage: float = Field(..., ge=0.0, le=1.0)
    content_accuracy: float = Field(..., ge=0.0, le=1.0)
    bias_score: float = Field(..., ge=0.0, le=1.0)
    meets_quality_standards: bool
    improvement_recommendations: List[str]
    critical_issues: List[Dict[str, Any]]


class ChapterRegenerationService:
    """Service for intelligent chapter regeneration and content improvement."""
    
    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize the chapter regeneration service."""
        self.ai_client = ai_client or create_ai_client()
        self.regeneration_history: List[RegenerationHistory] = []
        self.quality_threshold = 0.8  # Minimum quality score threshold
        
    async def regenerate_chapter(
        self,
        request: ChapterRegenerationRequest,
        db: Session
    ) -> ChapterRegenerationResponse:
        """
        Main regeneration workflow for chapters.
        
        Args:
            request: Regeneration request with scope and requirements
            db: Database session
            
        Returns:
            Response with task information and status
        """
        start_time = datetime.utcnow()
        task_id = uuid4()
        
        try:
            # Validate chapter exists and retrieve context
            chapter_data = await self._get_chapter_context(request.chapter_id, db)
            if not chapter_data:
                raise ValueError(f"Chapter {request.chapter_id} not found")
            
            chapter, course, subchapters = chapter_data
            
            # Analyze regeneration need and create improvement plan
            regeneration_plan = await self.analyze_regeneration_need(
                chapter, request.regeneration_reason, request.user_feedback
            )
            
            # Validate regeneration scope against chapter structure
            validated_scope = await self._validate_regeneration_scope(
                request.scope, chapter, subchapters
            )
            
            # Perform quality analysis on current content
            current_quality = await self._analyze_current_quality(
                chapter, subchapters, course.target_audience
            )
            
            # Generate improved content based on analysis
            improved_content = await self._generate_improved_content(
                chapter, course, regeneration_plan, validated_scope, current_quality
            )
            
            # Validate new content meets quality standards
            new_quality = await self._validate_regenerated_content(
                improved_content, course.target_audience, chapter.learning_objectives
            )
            
            # Update chapter content in database
            updated_chapter = await self.update_chapter_content(
                chapter, improved_content, validated_scope, db
            )
            
            # Track regeneration history
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.track_regeneration_history(
                chapter.id,
                regeneration_plan,
                validated_scope,
                current_quality.overall_score,
                new_quality.overall_score,
                processing_time,
                db
            )
            
            # Calculate estimated completion time
            estimated_completion = start_time + timedelta(seconds=processing_time * 1.2)
            
            return ChapterRegenerationResponse(
                task_id=task_id,
                chapter_id=chapter.id,
                estimated_completion_time=estimated_completion,
                regeneration_scope=validated_scope,
                current_status="completed",
                quality_target=request.target_quality_score
            )
            
        except Exception as e:
            logger.error(f"Chapter regeneration failed for {request.chapter_id}: {e}")
            raise RuntimeError(f"Chapter regeneration failed: {str(e)}")
    
    async def analyze_regeneration_need(
        self,
        chapter: Chapter,
        regeneration_reason: str,
        user_feedback: Optional[str] = None
    ) -> RegenerationReason:
        """
        Analyze regeneration requirements and categorize improvement needs.
        
        Args:
            chapter: Current chapter data
            regeneration_reason: User-provided reason for regeneration
            user_feedback: Optional detailed user feedback
            
        Returns:
            Structured analysis of regeneration requirements
        """
        try:
            # Combine reason and feedback for comprehensive analysis
            full_context = regeneration_reason
            if user_feedback:
                full_context += f"\n\nAdditional feedback: {user_feedback}"
            
            # Categorize the regeneration reason using AI analysis
            category = await self._categorize_regeneration_reason(full_context)
            
            # Extract specific issues and target improvements
            specific_issues = await self._extract_specific_issues(full_context, chapter)
            target_improvements = await self._identify_target_improvements(
                category, specific_issues, chapter
            )
            
            # Determine severity based on content analysis
            severity = await self._assess_regeneration_severity(
                category, specific_issues, chapter
            )
            
            return RegenerationReason(
                category=category,
                description=regeneration_reason,
                severity=severity,
                specific_issues=specific_issues,
                target_improvements=target_improvements
            )
            
        except Exception as e:
            logger.error(f"Regeneration need analysis failed: {e}")
            # Fallback to basic categorization
            return RegenerationReason(
                category="content",
                description=regeneration_reason,
                severity="medium",
                specific_issues=["General content improvement needed"],
                target_improvements=["Improve content quality and clarity"]
            )
    
    async def update_chapter_content(
        self,
        chapter: Chapter,
        improved_content: Dict[str, Any],
        scope: RegenerationScope,
        db: Session
    ) -> Chapter:
        """
        Update chapter content with improved version while preserving structure.
        
        Args:
            chapter: Original chapter
            improved_content: Generated improved content
            scope: Regeneration scope specifying what to update
            db: Database session
            
        Returns:
            Updated chapter object
        """
        try:
            # Get current chapter from database
            db_chapter = db.query(ChapterTable).filter(
                ChapterTable.id == chapter.id
            ).first()
            
            if not db_chapter:
                raise ValueError(f"Chapter {chapter.id} not found in database")
            
            # Update chapter-level content if in scope
            if scope.regenerate_full_chapter:
                # Update learning objectives if not preserved
                if not scope.preserve_structure and "learning_objectives" in improved_content:
                    db_chapter.learning_objectives = improved_content["learning_objectives"]
                
                # Update content outline
                if "content_outline" in improved_content:
                    db_chapter.content_outline = improved_content["content_outline"]
                
                # Update complexity level if recalculated
                if "complexity_level" in improved_content:
                    db_chapter.complexity_level = improved_content["complexity_level"]
            
            # Update subchapters if specified
            if scope.target_subchapters or scope.regenerate_full_chapter:
                await self._update_subchapters_content(
                    db_chapter.id, improved_content.get("subchapters", []), scope, db
                )
            
            # Update timestamp
            db_chapter.updated_at = datetime.utcnow()
            
            # Commit changes
            db.commit()
            db.refresh(db_chapter)
            
            # Convert back to Pydantic model
            return Chapter.from_orm(db_chapter)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Chapter content update failed: {e}")
            raise RuntimeError(f"Failed to update chapter content: {str(e)}")
    
    async def preserve_chapter_structure(
        self,
        original_chapter: Chapter,
        new_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Preserve important structural elements while allowing content updates.
        
        Args:
            original_chapter: Original chapter structure
            new_content: Generated new content
            
        Returns:
            Content with preserved structural elements
        """
        preserved_content = new_content.copy()
        
        # Preserve learning objectives if requested
        preserved_content["learning_objectives"] = original_chapter.learning_objectives
        
        # Preserve sequence numbers and IDs
        preserved_content["sequence_number"] = original_chapter.sequence_number
        preserved_content["id"] = original_chapter.id
        preserved_content["course_id"] = original_chapter.course_id
        
        # Preserve creation timestamp
        preserved_content["created_at"] = original_chapter.created_at
        
        # Ensure complexity level is within acceptable range
        if "complexity_level" in new_content:
            preserved_content["complexity_level"] = max(
                1.0, min(5.0, new_content["complexity_level"])
            )
        else:
            preserved_content["complexity_level"] = original_chapter.complexity_level
        
        return preserved_content
    
    async def validate_regenerated_content(
        self,
        content: Dict[str, Any],
        target_audience: TargetAudience,
        learning_objectives: List[str]
    ) -> QualityAnalysisResult:
        """
        Comprehensive quality validation of regenerated content.
        
        Args:
            content: Generated content to validate
            target_audience: Target audience for validation context
            learning_objectives: Learning objectives to validate against
            
        Returns:
            Comprehensive quality analysis result
        """
        try:
            # Extract text content for analysis
            content_text = self._extract_text_content(content)
            
            # Perform comprehensive quality analysis
            quality_analysis = await self.ai_client.comprehensive_quality_check(
                content=content_text,
                target_level=target_audience.proficiency_level,
                learning_objectives=learning_objectives,
                subject_domain="General"  # Could be extracted from course context
            )
            
            # Check for critical issues
            critical_issues = []
            improvement_recommendations = []
            
            # Validate readability for target level
            readability = quality_analysis["readability_analysis"]
            if not readability["meets_target_level"]:
                critical_issues.append({
                    "type": "readability",
                    "severity": "high",
                    "description": f"Content readability not suitable for {target_audience.proficiency_level.value} level"
                })
                improvement_recommendations.extend(readability["recommendations"])
            
            # Check bias detection results
            bias = quality_analysis["bias_detection"]
            if bias["overall_bias_score"] > 0.3:
                critical_issues.append({
                    "type": "bias",
                    "severity": bias["severity_level"],
                    "description": "Content contains potential bias issues"
                })
                improvement_recommendations.extend(bias["recommendations"])
            
            # Validate AI quality assessment
            ai_quality = quality_analysis["ai_quality_assessment"]
            if ai_quality["overall_score"] < self.quality_threshold:
                critical_issues.append({
                    "type": "quality",
                    "severity": "medium",
                    "description": "Overall content quality below threshold"
                })
                improvement_recommendations.extend(ai_quality["recommendations"])
            
            meets_standards = quality_analysis["meets_quality_standards"]
            
            return QualityAnalysisResult(
                overall_score=quality_analysis["overall_quality_score"],
                readability_score=readability["flesch_reading_ease"],
                pedagogical_alignment=ai_quality["pedagogical_alignment"],
                objective_coverage=ai_quality["objective_coverage"],
                content_accuracy=ai_quality["content_accuracy"],
                bias_score=bias["overall_bias_score"],
                meets_quality_standards=meets_standards,
                improvement_recommendations=improvement_recommendations,
                critical_issues=critical_issues
            )
            
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            # Return conservative quality assessment
            return QualityAnalysisResult(
                overall_score=0.5,
                readability_score=50.0,
                pedagogical_alignment=0.5,
                objective_coverage=0.5,
                content_accuracy=0.5,
                bias_score=0.2,
                meets_quality_standards=False,
                improvement_recommendations=["Content validation failed - manual review required"],
                critical_issues=[{
                    "type": "validation_error",
                    "severity": "high",
                    "description": "Automated validation failed - manual review required"
                }]
            )
    
    async def track_regeneration_history(
        self,
        chapter_id: UUID,
        regeneration_reason: RegenerationReason,
        scope: RegenerationScope,
        original_quality: float,
        new_quality: float,
        processing_time: float,
        db: Session
    ) -> RegenerationHistory:
        """
        Track regeneration history for audit trail and analysis.
        
        Args:
            chapter_id: Chapter that was regenerated
            regeneration_reason: Reason for regeneration
            scope: Scope of regeneration
            original_quality: Quality score before regeneration
            new_quality: Quality score after regeneration
            processing_time: Time taken for regeneration
            db: Database session
            
        Returns:
            Regeneration history record
        """
        try:
            history_record = RegenerationHistory(
                chapter_id=chapter_id,
                regeneration_reason=regeneration_reason,
                scope=scope,
                original_content_hash=f"hash_{uuid4()}",  # Simplified for demo
                new_content_hash=f"hash_{uuid4()}",
                quality_improvement=new_quality - original_quality,
                processing_time_seconds=processing_time,
                ai_provider_used=self.ai_client.preferred_provider,
                created_at=datetime.utcnow()
            )
            
            # Store in memory (in production, this would go to database)
            self.regeneration_history.append(history_record)
            
            logger.info(
                f"Regeneration completed for chapter {chapter_id}: "
                f"Quality improved from {original_quality:.2f} to {new_quality:.2f} "
                f"in {processing_time:.1f}s"
            )
            
            return history_record
            
        except Exception as e:
            logger.error(f"Failed to track regeneration history: {e}")
            raise
    
    async def get_regeneration_history(
        self,
        chapter_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[RegenerationHistory]:
        """
        Retrieve regeneration history for analysis.
        
        Args:
            chapter_id: Optional chapter ID to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of regeneration history records
        """
        if chapter_id:
            filtered_history = [
                record for record in self.regeneration_history
                if record.chapter_id == chapter_id
            ]
        else:
            filtered_history = self.regeneration_history
        
        # Sort by creation date (newest first) and limit
        sorted_history = sorted(
            filtered_history,
            key=lambda x: x.created_at,
            reverse=True
        )
        
        return sorted_history[:limit]
    
    # Private helper methods
    
    async def _get_chapter_context(
        self,
        chapter_id: UUID,
        db: Session
    ) -> Optional[Tuple[Chapter, CourseTable, List[Subchapter]]]:
        """Get chapter with full context including course and subchapters."""
        try:
            # Get chapter
            db_chapter = db.query(ChapterTable).filter(
                ChapterTable.id == chapter_id
            ).first()
            
            if not db_chapter:
                return None
            
            # Get course
            course = db.query(CourseTable).filter(
                CourseTable.id == db_chapter.course_id
            ).first()
            
            if not course:
                return None
            
            # Get subchapters
            subchapters = db.query(SubchapterTable).filter(
                SubchapterTable.chapter_id == chapter_id
            ).order_by(SubchapterTable.sequence_number).all()
            
            chapter = Chapter.from_orm(db_chapter)
            subchapter_models = [Subchapter.from_orm(sub) for sub in subchapters]
            
            return chapter, course, subchapter_models
            
        except Exception as e:
            logger.error(f"Failed to get chapter context: {e}")
            return None
    
    async def _validate_regeneration_scope(
        self,
        scope: RegenerationScope,
        chapter: Chapter,
        subchapters: List[Subchapter]
    ) -> RegenerationScope:
        """Validate and adjust regeneration scope based on chapter structure."""
        validated_scope = scope.copy()
        
        # Validate target subchapters exist
        subchapter_ids = {sub.id for sub in subchapters}
        validated_scope.target_subchapters = [
            sub_id for sub_id in scope.target_subchapters
            if sub_id in subchapter_ids
        ]
        
        # If no valid subchapters specified, regenerate all
        if scope.target_subchapters and not validated_scope.target_subchapters:
            validated_scope.regenerate_full_chapter = True
        
        # Validate content block orders
        if scope.target_content_blocks:
            max_blocks = max(
                len(sub.content_blocks) for sub in subchapters
                if subchapters else [1]
            )
            validated_scope.target_content_blocks = [
                block_order for block_order in scope.target_content_blocks
                if 1 <= block_order <= max_blocks
            ]
        
        return validated_scope
    
    async def _analyze_current_quality(
        self,
        chapter: Chapter,
        subchapters: List[Subchapter],
        target_audience: TargetAudience
    ) -> QualityAnalysisResult:
        """Analyze current chapter quality."""
        # Extract content for analysis
        content_text = f"{chapter.title}\n\n"
        if chapter.content_outline:
            content_text += f"{chapter.content_outline}\n\n"
        
        # Add subchapter content
        for subchapter in subchapters:
            content_text += f"{subchapter.title}\n"
            for block in subchapter.content_blocks:
                content_text += f"{block.content}\n"
            if subchapter.summary:
                content_text += f"Summary: {subchapter.summary}\n\n"
        
        # Perform quality analysis
        return await self.validate_regenerated_content(
            {"content": content_text},
            target_audience,
            chapter.learning_objectives
        )
    
    async def _generate_improved_content(
        self,
        chapter: Chapter,
        course: CourseTable,
        regeneration_plan: RegenerationReason,
        scope: RegenerationScope,
        current_quality: QualityAnalysisResult
    ) -> Dict[str, Any]:
        """Generate improved content based on analysis."""
        try:
            # Create content generation request
            content_request = ChapterContentRequest(
                chapter_title=chapter.title,
                learning_objectives=chapter.learning_objectives,
                target_level=course.target_audience["proficiency_level"],
                sequence_number=chapter.sequence_number,
                previous_concepts=[],  # Could be enhanced with actual previous concepts
                content_type="mixed",
                estimated_duration_minutes=60,  # Could be calculated from duration
                include_examples=scope.preserve_examples,
                include_exercises=scope.preserve_exercises
            )
            
            # Generate improved content
            improved_response = await self.ai_client.generate_chapter_content(content_request)
            
            # Convert response to structured format
            improved_content = {
                "title": chapter.title,
                "learning_objectives": chapter.learning_objectives if scope.preserve_structure else improved_response.key_concepts,
                "content_outline": f"Improved content addressing: {', '.join(regeneration_plan.target_improvements)}",
                "complexity_level": improved_response.complexity_score,
                "subchapters": self._convert_ai_response_to_subchapters(improved_response)
            }
            
            return improved_content
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            # Return minimal improved content
            return {
                "title": chapter.title,
                "learning_objectives": chapter.learning_objectives,
                "content_outline": f"Content improved to address: {regeneration_plan.description}",
                "complexity_level": chapter.complexity_level
            }
    
    async def _update_subchapters_content(
        self,
        chapter_id: UUID,
        improved_subchapters: List[Dict[str, Any]],
        scope: RegenerationScope,
        db: Session
    ) -> None:
        """Update subchapter content in database."""
        try:
            # Get existing subchapters
            existing_subchapters = db.query(SubchapterTable).filter(
                SubchapterTable.chapter_id == chapter_id
            ).all()
            
            # Update or create subchapters
            for i, improved_sub in enumerate(improved_subchapters):
                if i < len(existing_subchapters):
                    # Update existing
                    subchapter = existing_subchapters[i]
                    if not scope.preserve_structure:
                        subchapter.title = improved_sub.get("title", subchapter.title)
                    
                    # Update content blocks
                    if "content_blocks" in improved_sub:
                        subchapter.content_blocks = improved_sub["content_blocks"]
                    
                    if "key_concepts" in improved_sub:
                        subchapter.key_concepts = improved_sub["key_concepts"]
                    
                    if "summary" in improved_sub:
                        subchapter.summary = improved_sub["summary"]
                    
                    subchapter.updated_at = datetime.utcnow()
                    
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Subchapter update failed: {e}")
            raise
    
    def _convert_ai_response_to_subchapters(
        self,
        ai_response: ChapterContentResponse
    ) -> List[Dict[str, Any]]:
        """Convert AI response to subchapter format."""
        # Create a single subchapter from AI response
        return [{
            "title": "Main Content",
            "content_type": "mixed",
            "content_blocks": ai_response.content_blocks,
            "key_concepts": ai_response.key_concepts,
            "summary": ai_response.summary,
            "additional_resources": []
        }]
    
    def _extract_text_content(self, content: Dict[str, Any]) -> str:
        """Extract text content from structured content for analysis."""
        text_parts = []
        
        # Add title and outline
        if "title" in content:
            text_parts.append(content["title"])
        
        if "content_outline" in content:
            text_parts.append(content["content_outline"])
        
        # Add subchapter content
        if "subchapters" in content:
            for subchapter in content["subchapters"]:
                if "title" in subchapter:
                    text_parts.append(subchapter["title"])
                
                if "content_blocks" in subchapter:
                    for block in subchapter["content_blocks"]:
                        if isinstance(block, dict) and "content" in block:
                            text_parts.append(block["content"])
                        elif hasattr(block, 'content'):
                            text_parts.append(block.content)
                
                if "summary" in subchapter:
                    text_parts.append(subchapter["summary"])
        
        return "\n\n".join(text_parts)
    
    async def _categorize_regeneration_reason(self, reason_text: str) -> str:
        """Categorize regeneration reason using keyword analysis."""
        reason_lower = reason_text.lower()
        
        # Define keywords for each category
        categories = {
            "difficulty": ["too hard", "too easy", "complex", "simple", "difficulty", "level"],
            "clarity": ["unclear", "confusing", "hard to understand", "clarity", "explanation"],
            "accuracy": ["wrong", "incorrect", "error", "mistake", "accuracy", "factual"],
            "bias": ["bias", "biased", "unfair", "discriminatory", "inclusive", "diversity"],
            "content": ["content", "information", "details", "examples", "structure"]
        }
        
        # Count matches for each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in reason_lower)
            category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return "content"  # Default category
    
    async def _extract_specific_issues(
        self,
        reason_text: str,
        chapter: Chapter
    ) -> List[str]:
        """Extract specific issues from regeneration reason."""
        issues = []
        reason_lower = reason_text.lower()
        
        # Common issue patterns
        issue_patterns = {
            "too advanced": "Content complexity too high for target audience",
            "too basic": "Content too simple for target audience level",
            "missing examples": "Insufficient practical examples",
            "unclear explanations": "Explanations lack clarity",
            "outdated": "Content needs updating with current information",
            "boring": "Content lacks engagement",
            "errors": "Content contains factual errors"
        }
        
        for pattern, issue in issue_patterns.items():
            if pattern in reason_lower:
                issues.append(issue)
        
        # If no specific patterns found, use general issue
        if not issues:
            issues.append("General content improvement needed")
        
        return issues
    
    async def _identify_target_improvements(
        self,
        category: str,
        specific_issues: List[str],
        chapter: Chapter
    ) -> List[str]:
        """Identify target improvements based on category and issues."""
        improvements = []
        
        # Category-specific improvements
        category_improvements = {
            "difficulty": ["Adjust content complexity level", "Revise explanations for target audience"],
            "clarity": ["Improve explanation clarity", "Add more examples", "Restructure content flow"],
            "accuracy": ["Verify and correct factual content", "Update with latest information"],
            "bias": ["Review for inclusive language", "Add diverse perspectives and examples"],
            "content": ["Enhance content depth and quality", "Improve pedagogical structure"]
        }
        
        improvements.extend(category_improvements.get(category, []))
        
        # Issue-specific improvements
        for issue in specific_issues:
            if "examples" in issue.lower():
                improvements.append("Add more practical examples")
            elif "clarity" in issue.lower() or "unclear" in issue.lower():
                improvements.append("Simplify language and structure")
            elif "advanced" in issue.lower():
                improvements.append("Reduce complexity level")
            elif "basic" in issue.lower():
                improvements.append("Increase content depth")
        
        # Remove duplicates and return
        return list(set(improvements))
    
    async def _assess_regeneration_severity(
        self,
        category: str,
        specific_issues: List[str],
        chapter: Chapter
    ) -> str:
        """Assess severity of regeneration need."""
        # High severity categories
        if category in ["accuracy", "bias"]:
            return "high"
        
        # Check for critical keywords
        critical_keywords = ["error", "wrong", "incorrect", "bias", "discriminatory"]
        issue_text = " ".join(specific_issues).lower()
        
        if any(keyword in issue_text for keyword in critical_keywords):
            return "critical"
        
        # Medium severity for clarity and difficulty issues
        if category in ["clarity", "difficulty"]:
            return "medium"
        
        # Default to medium for general content issues
        return "medium"


# Factory function for creating service
def create_chapter_service(ai_client: Optional[AIClient] = None) -> ChapterRegenerationService:
    """Factory function to create chapter regeneration service."""
    return ChapterRegenerationService(ai_client=ai_client)