from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
import logging

from ...database.session import get_db
from ...services.course_generation_service import CourseGenerationService
from ...models.course import Course
from ...models.enums import CourseStatus, SubjectDomain, TargetAudience, DifficultyLevel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["courses"])

# Pydantic models for request/response
from pydantic import BaseModel, Field
from datetime import datetime

class CourseCreationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    subject_domain: SubjectDomain
    target_audience: TargetAudience
    difficulty_level: DifficultyLevel
    estimated_duration_hours: int = Field(..., ge=1, le=200)
    learning_objectives: List[str] = Field(..., min_items=1, max_items=20)
    
class CourseCreationResponse(BaseModel):
    id: UUID
    title: str
    status: CourseStatus
    created_at: datetime
    estimated_completion_time: Optional[datetime]
    
class CourseResponse(BaseModel):
    id: UUID
    title: str
    description: str
    subject_domain: SubjectDomain
    target_audience: TargetAudience
    difficulty_level: DifficultyLevel
    status: CourseStatus
    estimated_duration_hours: int
    learning_objectives: List[str]
    created_at: datetime
    updated_at: datetime
    completion_percentage: Optional[int]
    
class CourseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    learning_objectives: Optional[List[str]] = Field(None, min_items=1, max_items=20)

class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    total: int
    page: int
    limit: int

# T041: POST /courses endpoint
@router.post("/", response_model=CourseCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    request: CourseCreationRequest,
    db: Session = Depends(get_db)
) -> CourseCreationResponse:
    """
    Create a new course and initiate the AI generation process.
    
    This endpoint:
    1. Creates a course record in the database
    2. Initiates the AI-powered content generation process
    3. Returns the course ID and status for tracking
    """
    try:
        logger.info(f"Creating new course: {request.title}")
        
        # Initialize the course generation service
        course_service = CourseGenerationService(db)
        
        # Create the course and start generation
        course = await course_service.create_course(
            title=request.title,
            description=request.description,
            subject_domain=request.subject_domain,
            target_audience=request.target_audience,
            difficulty_level=request.difficulty_level,
            estimated_duration_hours=request.estimated_duration_hours,
            learning_objectives=request.learning_objectives
        )
        
        logger.info(f"Course created successfully with ID: {course.id}")
        
        return CourseCreationResponse(
            id=course.id,
            title=course.title,
            status=course.status,
            created_at=course.created_at,
            estimated_completion_time=course.estimated_completion_time
        )
        
    except ValueError as e:
        logger.error(f"Validation error creating course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course"
        )

# T042: GET /courses (list) endpoint
@router.get("/", response_model=CourseListResponse)
async def list_courses(
    status_filter: Optional[CourseStatus] = Query(None, alias="status"),
    subject_domain: Optional[SubjectDomain] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> CourseListResponse:
    """
    List courses with optional filtering and pagination.
    
    Supports filtering by:
    - status: Course generation status
    - subject_domain: Domain of the course
    
    Includes pagination with page and limit parameters.
    """
    try:
        logger.info(f"Listing courses with filters: status={status_filter}, domain={subject_domain}")
        
        # Build query with filters
        query = db.query(Course)
        
        if status_filter:
            query = query.filter(Course.status == status_filter)
        if subject_domain:
            query = query.filter(Course.subject_domain == subject_domain)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        courses = query.order_by(Course.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        course_responses = [
            CourseResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                subject_domain=course.subject_domain,
                target_audience=course.target_audience,
                difficulty_level=course.difficulty_level,
                status=course.status,
                estimated_duration_hours=course.estimated_duration_hours,
                learning_objectives=course.learning_objectives,
                created_at=course.created_at,
                updated_at=course.updated_at,
                completion_percentage=course.completion_percentage
            )
            for course in courses
        ]
        
        return CourseListResponse(
            courses=course_responses,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list courses"
        )

# T043: GET /courses/{courseId} endpoint
@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    db: Session = Depends(get_db)
) -> CourseResponse:
    """
    Get detailed information about a specific course.
    
    Returns complete course details including generation status,
    learning objectives, and completion percentage.
    """
    try:
        logger.info(f"Fetching course details for ID: {course_id}")
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            subject_domain=course.subject_domain,
            target_audience=course.target_audience,
            difficulty_level=course.difficulty_level,
            status=course.status,
            estimated_duration_hours=course.estimated_duration_hours,
            learning_objectives=course.learning_objectives,
            created_at=course.created_at,
            updated_at=course.updated_at,
            completion_percentage=course.completion_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch course details"
        )

# T044: PUT /courses/{courseId} endpoint
@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    request: CourseUpdateRequest,
    db: Session = Depends(get_db)
) -> CourseResponse:
    """
    Update course information.
    
    Allows updating:
    - title: Course title
    - description: Course description
    - learning_objectives: List of learning objectives
    
    Note: Some fields like subject_domain and status cannot be updated
    once the course is created to maintain data integrity.
    """
    try:
        logger.info(f"Updating course {course_id}")
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Check if course can be updated (not in certain states)
        if course.status in [CourseStatus.GENERATING, CourseStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot update course while generation is in progress"
            )
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        
        course.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(course)
        
        logger.info(f"Course {course_id} updated successfully")
        
        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            subject_domain=course.subject_domain,
            target_audience=course.target_audience,
            difficulty_level=course.difficulty_level,
            status=course.status,
            estimated_duration_hours=course.estimated_duration_hours,
            learning_objectives=course.learning_objectives,
            created_at=course.created_at,
            updated_at=course.updated_at,
            completion_percentage=course.completion_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating course {course_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course"
        )

# T045: DELETE /courses/{courseId} endpoint
@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a course and all associated content.
    
    This is a hard delete operation that removes:
    - The course record
    - All associated chapters and subchapters
    - All quizzes and questions
    - All flashcards
    
    Warning: This operation cannot be undone.
    """
    try:
        logger.info(f"Deleting course {course_id}")
        
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Check if course can be deleted
        if course.status == CourseStatus.GENERATING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete course while generation is in progress"
            )
        
        # Delete the course (cascading deletes will handle related entities)
        db.delete(course)
        db.commit()
        
        logger.info(f"Course {course_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course"
        )
