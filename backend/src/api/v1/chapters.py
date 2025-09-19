from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from database.session import get_db
from models.chapter import Chapter
from models.course import Course
from models.enums import GenerationStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chapters", tags=["chapters"])

# Pydantic models for request/response
from pydantic import BaseModel, Field
from datetime import datetime

class SubchapterResponse(BaseModel):
    id: UUID
    title: str
    order_index: int
    content: str
    estimated_reading_time_minutes: int
    created_at: datetime
    updated_at: datetime
    
class ChapterResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str
    order_index: int
    learning_objectives: List[str]
    estimated_duration_minutes: int
    status: GenerationStatus
    created_at: datetime
    updated_at: datetime
    
    # Content sections
    subchapters: List[SubchapterResponse]
    
    # Progress and metadata
    completion_percentage: Optional[int]
    word_count: Optional[int]
    reading_level: Optional[str]
    key_concepts: List[str]
    
class ChapterContentResponse(BaseModel):
    chapter: ChapterResponse
    navigation: Dict[str, Any]  # Previous/next chapter info
    course_context: Dict[str, Any]  # Course title, progress, etc.
    
class ChapterSummaryResponse(BaseModel):
    id: UUID
    title: str
    order_index: int
    status: GenerationStatus
    estimated_duration_minutes: int
    completion_percentage: Optional[int]
    subchapter_count: int
    
# T050: GET /chapters/{chapterId} endpoint
@router.get("/{chapter_id}", response_model=ChapterContentResponse)
async def get_chapter(
    chapter_id: UUID,
    include_navigation: bool = Query(True, description="Include navigation to adjacent chapters"),
    include_course_context: bool = Query(True, description="Include course context information"),
    db: Session = Depends(get_db)
) -> ChapterContentResponse:
    """
    Get complete chapter content with subchapters and navigation.
    
    Returns:
    - Full chapter details including all subchapters
    - Navigation information (previous/next chapters)
    - Course context for breadcrumb navigation
    - Progress and metadata information
    
    This endpoint is designed for the main content viewing experience.
    """
    try:
        logger.info(f"Fetching chapter content for ID: {chapter_id}")
        
        # Get the chapter with all related data
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {chapter_id} not found"
            )
        
        # Check if chapter content is available
        if chapter.status == GenerationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chapter content is still being generated"
            )
        
        if chapter.status == GenerationStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Chapter generation failed. Content may be incomplete."
            )
        
        # Get course for context
        course = db.query(Course).filter(Course.id == chapter.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent course not found"
            )
        
        # Build subchapters response
        subchapters_response = [
            SubchapterResponse(
                id=sub.id,
                title=sub.title,
                order_index=sub.order_index,
                content=sub.content,
                estimated_reading_time_minutes=sub.estimated_reading_time_minutes,
                created_at=sub.created_at,
                updated_at=sub.updated_at
            )
            for sub in sorted(chapter.subchapters, key=lambda x: x.order_index)
        ]
        
        # Build main chapter response
        chapter_response = ChapterResponse(
            id=chapter.id,
            course_id=chapter.course_id,
            title=chapter.title,
            description=chapter.description,
            order_index=chapter.order_index,
            learning_objectives=chapter.learning_objectives,
            estimated_duration_minutes=chapter.estimated_duration_minutes,
            status=chapter.status,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
            subchapters=subchapters_response,
            completion_percentage=chapter.completion_percentage,
            word_count=chapter.word_count,
            reading_level=chapter.reading_level,
            key_concepts=chapter.key_concepts or []
        )
        
        # Build navigation context
        navigation = {}
        if include_navigation:
            # Get previous chapter
            prev_chapter = db.query(Chapter).filter(
                Chapter.course_id == chapter.course_id,
                Chapter.order_index < chapter.order_index
            ).order_by(Chapter.order_index.desc()).first()
            
            # Get next chapter
            next_chapter = db.query(Chapter).filter(
                Chapter.course_id == chapter.course_id,
                Chapter.order_index > chapter.order_index
            ).order_by(Chapter.order_index.asc()).first()
            
            navigation = {
                "previous_chapter": {
                    "id": prev_chapter.id,
                    "title": prev_chapter.title,
                    "order_index": prev_chapter.order_index
                } if prev_chapter else None,
                "next_chapter": {
                    "id": next_chapter.id,
                    "title": next_chapter.title,
                    "order_index": next_chapter.order_index
                } if next_chapter else None,
                "total_chapters": db.query(Chapter).filter(Chapter.course_id == chapter.course_id).count()
            }
        
        # Build course context
        course_context = {}
        if include_course_context:
            course_context = {
                "course_id": course.id,
                "course_title": course.title,
                "course_status": course.status,
                "current_chapter_position": chapter.order_index,
                "total_chapters": db.query(Chapter).filter(Chapter.course_id == chapter.course_id).count(),
                "course_completion_percentage": course.completion_percentage
            }
        
        return ChapterContentResponse(
            chapter=chapter_response,
            navigation=navigation,
            course_context=course_context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chapter {chapter_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chapter content"
        )

# Get chapter summary (lightweight version)
@router.get("/{chapter_id}/summary", response_model=ChapterSummaryResponse)
async def get_chapter_summary(
    chapter_id: UUID,
    db: Session = Depends(get_db)
) -> ChapterSummaryResponse:
    """
    Get a lightweight summary of chapter information.
    
    Useful for course navigation, progress tracking, and table of contents.
    Does not include full content to improve performance.
    """
    try:
        logger.info(f"Fetching chapter summary for ID: {chapter_id}")
        
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {chapter_id} not found"
            )
        
        # Count subchapters
        subchapter_count = len(chapter.subchapters) if chapter.subchapters else 0
        
        return ChapterSummaryResponse(
            id=chapter.id,
            title=chapter.title,
            order_index=chapter.order_index,
            status=chapter.status,
            estimated_duration_minutes=chapter.estimated_duration_minutes,
            completion_percentage=chapter.completion_percentage,
            subchapter_count=subchapter_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chapter summary {chapter_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chapter summary"
        )

# Get chapter outline (structure without content)
@router.get("/{chapter_id}/outline")
async def get_chapter_outline(
    chapter_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the structural outline of a chapter without full content.
    
    Useful for:
    - Course planning and review
    - Content structure analysis
    - Quick navigation
    """
    try:
        logger.info(f"Fetching chapter outline for ID: {chapter_id}")
        
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {chapter_id} not found"
            )
        
        # Build outline structure
        subchapter_outline = [
            {
                "id": sub.id,
                "title": sub.title,
                "order_index": sub.order_index,
                "estimated_reading_time_minutes": sub.estimated_reading_time_minutes,
                "content_preview": sub.content[:200] + "..." if sub.content and len(sub.content) > 200 else sub.content
            }
            for sub in sorted(chapter.subchapters, key=lambda x: x.order_index)
        ] if chapter.subchapters else []
        
        return {
            "chapter_id": chapter.id,
            "title": chapter.title,
            "description": chapter.description,
            "learning_objectives": chapter.learning_objectives,
            "estimated_duration_minutes": chapter.estimated_duration_minutes,
            "key_concepts": chapter.key_concepts or [],
            "subchapters": subchapter_outline,
            "structure_summary": {
                "total_subchapters": len(subchapter_outline),
                "total_estimated_time": sum(sub.get('estimated_reading_time_minutes', 0) for sub in subchapter_outline),
                "word_count": chapter.word_count,
                "reading_level": chapter.reading_level
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chapter outline {chapter_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chapter outline"
        )

# Get chapter learning progress
@router.get("/{chapter_id}/progress")
async def get_chapter_progress(
    chapter_id: UUID,
    user_id: Optional[UUID] = Query(None, description="User ID for progress tracking"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get learning progress for a specific chapter.
    
    Note: This is a placeholder for future user progress tracking.
    Currently returns chapter completion status and metrics.
    """
    try:
        logger.info(f"Fetching chapter progress for ID: {chapter_id}")
        
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter with ID {chapter_id} not found"
            )
        
        # For now, return chapter-level progress information
        # Future: Integrate with user progress tracking system
        
        return {
            "chapter_id": chapter.id,
            "generation_progress": {
                "status": chapter.status,
                "completion_percentage": chapter.completion_percentage or 0,
                "last_updated": chapter.updated_at
            },
            "content_metrics": {
                "word_count": chapter.word_count,
                "estimated_duration_minutes": chapter.estimated_duration_minutes,
                "subchapter_count": len(chapter.subchapters) if chapter.subchapters else 0,
                "reading_level": chapter.reading_level
            },
            "learning_analytics": {
                "key_concepts_count": len(chapter.key_concepts) if chapter.key_concepts else 0,
                "learning_objectives_count": len(chapter.learning_objectives) if chapter.learning_objectives else 0
            },
            "user_progress": {
                "note": "User-specific progress tracking will be implemented in future versions",
                "user_id": user_id,
                "reading_progress": None,
                "time_spent": None,
                "completed_subchapters": None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chapter progress {chapter_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chapter progress"
        )
