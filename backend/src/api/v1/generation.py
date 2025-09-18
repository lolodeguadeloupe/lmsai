from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from ...database.session import get_db
from ...services.course_generation_service import CourseGenerationService
from ...services.chapter_service import ChapterService
from ...models.course import Course
from ...models.chapter import Chapter
from ...models.enums import CourseStatus, GenerationStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["generation"])

# Pydantic models for request/response
from pydantic import BaseModel, Field
from datetime import datetime

class GenerationStatusResponse(BaseModel):
    course_id: UUID
    status: CourseStatus
    completion_percentage: int = Field(..., ge=0, le=100)
    current_stage: str
    estimated_completion_time: Optional[datetime]
    chapters_generated: int
    total_chapters: int
    last_updated: datetime
    generation_logs: Optional[list] = None
    
class ChapterRegenerationRequest(BaseModel):
    chapter_id: UUID
    regeneration_reason: Optional[str] = Field(None, max_length=500)
    preserve_structure: bool = Field(True, description="Whether to keep the same chapter structure")
    
class ChapterRegenerationResponse(BaseModel):
    chapter_id: UUID
    course_id: UUID
    status: GenerationStatus
    message: str
    estimated_completion_time: Optional[datetime]

# T046: GET /courses/{courseId}/generation-status endpoint
@router.get("/{course_id}/generation-status", response_model=GenerationStatusResponse)
async def get_generation_status(
    course_id: UUID,
    include_logs: bool = False,
    db: Session = Depends(get_db)
) -> GenerationStatusResponse:
    """
    Get the current generation status of a course.
    
    Returns detailed information about:
    - Overall course generation progress
    - Current stage of generation
    - Number of chapters completed
    - Estimated completion time
    - Optional generation logs for debugging
    """
    try:
        logger.info(f"Fetching generation status for course: {course_id}")
        
        # Get the course
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Initialize course generation service
        course_service = CourseGenerationService(db)
        
        # Get detailed generation status
        generation_info = await course_service.get_generation_status(course_id)
        
        # Count chapters
        total_chapters = db.query(Chapter).filter(Chapter.course_id == course_id).count()
        completed_chapters = db.query(Chapter).filter(
            Chapter.course_id == course_id,
            Chapter.status == GenerationStatus.COMPLETED
        ).count()
        
        # Determine current stage
        current_stage = "Initializing"
        if course.status == CourseStatus.GENERATING:
            if total_chapters == 0:
                current_stage = "Planning course structure"
            elif completed_chapters < total_chapters:
                current_stage = f"Generating content ({completed_chapters}/{total_chapters} chapters)"
            else:
                current_stage = "Finalizing course"
        elif course.status == CourseStatus.COMPLETED:
            current_stage = "Generation complete"
        elif course.status == CourseStatus.FAILED:
            current_stage = "Generation failed"
        elif course.status == CourseStatus.DRAFT:
            current_stage = "Ready for generation"
        
        # Get generation logs if requested
        logs = None
        if include_logs:
            logs = generation_info.get('logs', [])
        
        return GenerationStatusResponse(
            course_id=course.id,
            status=course.status,
            completion_percentage=course.completion_percentage or 0,
            current_stage=current_stage,
            estimated_completion_time=course.estimated_completion_time,
            chapters_generated=completed_chapters,
            total_chapters=total_chapters,
            last_updated=course.updated_at,
            generation_logs=logs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching generation status for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch generation status"
        )

# T047: POST /courses/{courseId}/regenerate-chapter endpoint
@router.post("/{course_id}/regenerate-chapter", response_model=ChapterRegenerationResponse)
async def regenerate_chapter(
    course_id: UUID,
    request: ChapterRegenerationRequest,
    db: Session = Depends(get_db)
) -> ChapterRegenerationResponse:
    """
    Regenerate a specific chapter within a course.
    
    This endpoint allows for:
    - Regenerating a single chapter due to quality issues
    - Updating chapter content while preserving course structure
    - Providing feedback for improved generation
    
    The regeneration process:
    1. Validates the chapter exists and belongs to the course
    2. Initiates background regeneration task
    3. Returns status and tracking information
    """
    try:
        logger.info(f"Starting chapter regeneration for course {course_id}, chapter {request.chapter_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Verify chapter exists and belongs to the course
        chapter = db.query(Chapter).filter(
            Chapter.id == request.chapter_id,
            Chapter.course_id == course_id
        ).first()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {request.chapter_id} not found in course {course_id}"
            )
        
        # Check if course is in a state that allows regeneration
        if course.status == CourseStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot regenerate chapter while course generation is in progress"
            )
        
        # Check if chapter is already being regenerated
        if chapter.status == GenerationStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chapter is already being regenerated"
            )
        
        # Initialize chapter service
        chapter_service = ChapterService(db)
        
        # Start the regeneration process
        regeneration_result = await chapter_service.regenerate_chapter(
            chapter_id=request.chapter_id,
            regeneration_reason=request.regeneration_reason,
            preserve_structure=request.preserve_structure
        )
        
        logger.info(f"Chapter regeneration initiated successfully for {request.chapter_id}")
        
        return ChapterRegenerationResponse(
            chapter_id=request.chapter_id,
            course_id=course_id,
            status=GenerationStatus.GENERATING,
            message="Chapter regeneration initiated successfully",
            estimated_completion_time=regeneration_result.get('estimated_completion_time')
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in chapter regeneration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error regenerating chapter {request.chapter_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate chapter regeneration"
        )

# Additional helper endpoint for generation control
@router.post("/{course_id}/cancel-generation")
async def cancel_generation(
    course_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel an ongoing course generation process.
    
    This is a safety endpoint to stop generation if needed.
    """
    try:
        logger.info(f"Cancelling generation for course: {course_id}")
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        if course.status != CourseStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No active generation to cancel"
            )
        
        # Initialize course generation service
        course_service = CourseGenerationService(db)
        
        # Cancel the generation
        await course_service.cancel_generation(course_id)
        
        return {
            "message": "Generation cancelled successfully",
            "course_id": course_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling generation for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel generation"
        )

# Additional helper endpoint for generation restart
@router.post("/{course_id}/restart-generation")
async def restart_generation(
    course_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Restart generation for a failed or cancelled course.
    
    Useful for recovering from generation failures.
    """
    try:
        logger.info(f"Restarting generation for course: {course_id}")
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        if course.status not in [CourseStatus.FAILED, CourseStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Course is not in a state that allows restart"
            )
        
        # Initialize course generation service
        course_service = CourseGenerationService(db)
        
        # Restart the generation
        result = await course_service.restart_generation(course_id)
        
        return {
            "message": "Generation restarted successfully",
            "course_id": course_id,
            "status": "generating",
            "estimated_completion_time": result.get('estimated_completion_time')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting generation for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart generation"
        )
