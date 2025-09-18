from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from ...database.session import get_db
from ...services.quality_validation_service import QualityValidationService
from ...models.course import Course
from ...models.enums import CourseStatus, QualityScore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["quality"])

# Pydantic models for request/response
from pydantic import BaseModel, Field
from datetime import datetime

class QualityMetricsResponse(BaseModel):
    course_id: UUID
    overall_score: float = Field(..., ge=0.0, le=10.0)
    quality_grade: QualityScore
    last_updated: datetime
    
    # Detailed metrics
    content_quality: Dict[str, Any]
    structure_quality: Dict[str, Any]
    assessment_quality: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    accessibility_score: Dict[str, Any]
    
    # Recommendations
    improvement_suggestions: List[str]
    quality_issues: List[Dict[str, Any]]
    
class QualityDetailResponse(BaseModel):
    metric_name: str
    score: float
    max_score: float
    description: str
    weight: float
    contributing_factors: List[str]
    improvement_tips: List[str]
    
class QualityAnalysisRequest(BaseModel):
    analyze_content: bool = Field(True, description="Analyze content quality")
    analyze_structure: bool = Field(True, description="Analyze course structure")
    analyze_assessments: bool = Field(True, description="Analyze assessment quality")
    analyze_engagement: bool = Field(True, description="Analyze engagement factors")
    analyze_accessibility: bool = Field(True, description="Check accessibility compliance")
    detailed_feedback: bool = Field(False, description="Include detailed improvement suggestions")

# T049: GET /courses/{courseId}/quality-metrics endpoint
@router.get("/{course_id}/quality-metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(
    course_id: UUID,
    force_refresh: bool = Query(False, description="Force recalculation of metrics"),
    include_detailed_suggestions: bool = Query(True, description="Include improvement suggestions"),
    db: Session = Depends(get_db)
) -> QualityMetricsResponse:
    """
    Get comprehensive quality metrics for a course.
    
    Returns detailed analysis of:
    - Content quality (clarity, accuracy, completeness)
    - Structure quality (organization, flow, coherence)
    - Assessment quality (validity, reliability, fairness)
    - Engagement metrics (interactivity, multimedia usage)
    - Accessibility compliance (WCAG guidelines)
    
    Quality scoring:
    - 9.0-10.0: Excellent
    - 7.0-8.9: Good
    - 5.0-6.9: Satisfactory
    - 3.0-4.9: Needs Improvement
    - 0.0-2.9: Poor
    """
    try:
        logger.info(f"Fetching quality metrics for course: {course_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Check if course has enough content for quality analysis
        if course.status in [CourseStatus.DRAFT, CourseStatus.GENERATING]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Course must have generated content for quality analysis"
            )
        
        # Initialize quality validation service
        quality_service = QualityValidationService(db)
        
        # Get or calculate quality metrics
        metrics = await quality_service.get_course_quality_metrics(
            course_id=course_id,
            force_refresh=force_refresh,
            include_detailed_suggestions=include_detailed_suggestions
        )
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality metrics not available for this course"
            )
        
        # Convert quality score to enum
        quality_grade = QualityScore.POOR
        if metrics['overall_score'] >= 9.0:
            quality_grade = QualityScore.EXCELLENT
        elif metrics['overall_score'] >= 7.0:
            quality_grade = QualityScore.GOOD
        elif metrics['overall_score'] >= 5.0:
            quality_grade = QualityScore.SATISFACTORY
        elif metrics['overall_score'] >= 3.0:
            quality_grade = QualityScore.NEEDS_IMPROVEMENT
        
        return QualityMetricsResponse(
            course_id=course_id,
            overall_score=metrics['overall_score'],
            quality_grade=quality_grade,
            last_updated=metrics['last_updated'],
            content_quality=metrics['content_quality'],
            structure_quality=metrics['structure_quality'],
            assessment_quality=metrics['assessment_quality'],
            engagement_metrics=metrics['engagement_metrics'],
            accessibility_score=metrics['accessibility_score'],
            improvement_suggestions=metrics.get('improvement_suggestions', []),
            quality_issues=metrics.get('quality_issues', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quality metrics for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quality metrics"
        )

# Get detailed quality analysis for a specific metric
@router.get("/{course_id}/quality-metrics/{metric_name}", response_model=QualityDetailResponse)
async def get_quality_metric_detail(
    course_id: UUID,
    metric_name: str,
    db: Session = Depends(get_db)
) -> QualityDetailResponse:
    """
    Get detailed analysis for a specific quality metric.
    
    Available metrics:
    - content_clarity
    - content_accuracy
    - content_completeness
    - structure_organization
    - structure_flow
    - assessment_validity
    - assessment_reliability
    - engagement_interactivity
    - accessibility_compliance
    """
    try:
        logger.info(f"Fetching detailed quality metric {metric_name} for course {course_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Initialize quality validation service
        quality_service = QualityValidationService(db)
        
        # Get detailed metric analysis
        metric_detail = await quality_service.get_metric_detail(
            course_id=course_id,
            metric_name=metric_name
        )
        
        if not metric_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quality metric '{metric_name}' not found or not available"
            )
        
        return QualityDetailResponse(
            metric_name=metric_name,
            score=metric_detail['score'],
            max_score=metric_detail['max_score'],
            description=metric_detail['description'],
            weight=metric_detail['weight'],
            contributing_factors=metric_detail['contributing_factors'],
            improvement_tips=metric_detail['improvement_tips']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metric detail {metric_name} for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch metric detail"
        )

# Trigger quality analysis
@router.post("/{course_id}/quality-analysis")
async def trigger_quality_analysis(
    course_id: UUID,
    request: QualityAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger a new quality analysis for the course.
    
    This endpoint allows customizing which aspects of quality to analyze.
    Useful for targeted quality improvements.
    """
    try:
        logger.info(f"Triggering quality analysis for course {course_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Check if course has content to analyze
        if course.status in [CourseStatus.DRAFT, CourseStatus.GENERATING]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Course must have generated content for quality analysis"
            )
        
        # Initialize quality validation service
        quality_service = QualityValidationService(db)
        
        # Trigger the analysis
        analysis_result = await quality_service.trigger_quality_analysis(
            course_id=course_id,
            analyze_content=request.analyze_content,
            analyze_structure=request.analyze_structure,
            analyze_assessments=request.analyze_assessments,
            analyze_engagement=request.analyze_engagement,
            analyze_accessibility=request.analyze_accessibility,
            detailed_feedback=request.detailed_feedback
        )
        
        return {
            "message": "Quality analysis initiated successfully",
            "course_id": course_id,
            "analysis_id": analysis_result['analysis_id'],
            "estimated_completion_time": analysis_result.get('estimated_completion_time'),
            "analysis_scope": {
                "content": request.analyze_content,
                "structure": request.analyze_structure,
                "assessments": request.analyze_assessments,
                "engagement": request.analyze_engagement,
                "accessibility": request.analyze_accessibility
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering quality analysis for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger quality analysis"
        )

# Get quality trends over time
@router.get("/{course_id}/quality-history")
async def get_quality_history(
    course_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get quality metrics history for a course.
    
    Useful for tracking quality improvements over time.
    """
    try:
        logger.info(f"Fetching quality history for course {course_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Initialize quality validation service
        quality_service = QualityValidationService(db)
        
        # Get quality history
        history = await quality_service.get_quality_history(
            course_id=course_id,
            days=days
        )
        
        return {
            "course_id": course_id,
            "period_days": days,
            "quality_history": history,
            "trend_analysis": history.get('trend_analysis', {}) if history else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quality history for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quality history"
        )

# Get quality comparison with similar courses
@router.get("/{course_id}/quality-benchmark")
async def get_quality_benchmark(
    course_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare course quality metrics with similar courses.
    
    Provides benchmarking data to understand relative performance.
    """
    try:
        logger.info(f"Fetching quality benchmark for course {course_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Initialize quality validation service
        quality_service = QualityValidationService(db)
        
        # Get benchmark comparison
        benchmark = await quality_service.get_quality_benchmark(
            course_id=course_id
        )
        
        return {
            "course_id": course_id,
            "benchmark_data": benchmark,
            "comparison_summary": benchmark.get('summary', {}) if benchmark else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quality benchmark for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quality benchmark"
        )
