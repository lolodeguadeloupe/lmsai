"""
Course generation tasks for background processing.

Implements async tasks for course creation, chapter generation, quality validation,
and export operations with proper error handling and progress tracking.
"""

import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from celery import Task
from celery.exceptions import Retry
from pydantic import BaseModel, Field

from .celery_app import celery_app

# Setup logging
logger = logging.getLogger(__name__)


# Task status and progress models

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class GenerationPhase(str, Enum):
    """Course generation phases."""
    STRUCTURE = "structure"
    CONTENT = "content"
    ASSESSMENT = "assessment"
    VALIDATION = "validation"
    EXPORT = "export"


class TaskProgress(BaseModel):
    """Task progress tracking model."""
    task_id: str
    status: TaskStatus
    progress_percentage: float = Field(ge=0.0, le=100.0)
    current_phase: GenerationPhase
    estimated_time_remaining: str  # ISO 8601 duration
    start_time: datetime
    last_update: datetime
    error_details: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseGenerationTask(Task):
    """Base class for generation tasks with common functionality."""
    
    def __init__(self):
        self.progress_data = {}
    
    def update_progress(
        self,
        task_id: str,
        progress_percentage: float,
        phase: GenerationPhase,
        estimated_remaining: str = "PT0S",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update task progress and store in result backend."""
        progress = TaskProgress(
            task_id=task_id,
            status=TaskStatus.IN_PROGRESS,
            progress_percentage=progress_percentage,
            current_phase=phase,
            estimated_time_remaining=estimated_remaining,
            start_time=self.progress_data.get("start_time", datetime.utcnow()),
            last_update=datetime.utcnow(),
            retry_count=self.request.retries,
            metadata=metadata or {}
        )
        
        # Store progress in Redis for monitoring
        self.update_state(
            state="PROGRESS",
            meta=progress.dict()
        )
        
        logger.info(f"Task {task_id} progress: {progress_percentage}% - {phase}")
    
    def handle_error(self, task_id: str, error: Exception) -> None:
        """Handle task errors with proper logging and progress updates."""
        error_msg = str(error)
        error_trace = traceback.format_exc()
        
        logger.error(f"Task {task_id} failed: {error_msg}\n{error_trace}")
        
        # Update progress with error state
        progress = TaskProgress(
            task_id=task_id,
            status=TaskStatus.FAILED,
            progress_percentage=0.0,
            current_phase=GenerationPhase.STRUCTURE,
            estimated_time_remaining="PT0S",
            start_time=self.progress_data.get("start_time", datetime.utcnow()),
            last_update=datetime.utcnow(),
            error_details=error_msg,
            retry_count=self.request.retries
        )
        
        self.update_state(
            state="FAILURE",
            meta=progress.dict()
        )


@celery_app.task(
    bind=True,
    base=BaseGenerationTask,
    name="src.tasks.generation_tasks.generate_course_task",
    max_retries=3,
    soft_time_limit=600,  # 10 minutes for full course
    time_limit=660,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True
)
def generate_course_task(
    self,
    course_data: Dict[str, Any],
    user_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a complete course with chapters and content.
    
    Args:
        course_data: Course creation data following CourseCreate schema
        user_preferences: Optional user preferences for generation
        
    Returns:
        Generated course data with chapters and metadata
        
    Raises:
        Exception: If generation fails after all retries
    """
    task_id = self.request.id
    course_id = course_data.get("id") or str(uuid4())
    
    try:
        # Initialize progress tracking
        self.progress_data["start_time"] = datetime.utcnow()
        self.update_progress(
            task_id=task_id,
            progress_percentage=0.0,
            phase=GenerationPhase.STRUCTURE,
            estimated_remaining="PT10M"
        )
        
        logger.info(f"Starting course generation for course {course_id}")
        
        # Phase 1: Generate course structure (20%)
        self.update_progress(task_id, 10.0, GenerationPhase.STRUCTURE, "PT8M")
        
        # Simulate structure generation
        num_chapters = 5  # Based on course complexity
        chapter_structure = []
        for i in range(num_chapters):
            chapter_structure.append({
                "id": str(uuid4()),
                "sequence_number": i + 1,
                "title": f"Chapter {i + 1}: {course_data.get('title', 'Unknown')} - Part {i + 1}",
                "estimated_duration": "PT2H",
                "complexity_level": 2.0 + (i * 0.5),
                "learning_objectives": [
                    f"Understand concepts in chapter {i + 1}",
                    f"Apply knowledge from chapter {i + 1}"
                ]
            })
        
        self.update_progress(task_id, 20.0, GenerationPhase.STRUCTURE, "PT7M")
        
        # Phase 2: Generate content for each chapter (60%)
        self.update_progress(task_id, 25.0, GenerationPhase.CONTENT, "PT6M")
        
        generated_chapters = []
        for idx, chapter in enumerate(chapter_structure):
            # Generate chapter content
            chapter_progress = 25.0 + ((idx + 1) / num_chapters) * 55.0
            self.update_progress(
                task_id, 
                chapter_progress, 
                GenerationPhase.CONTENT,
                f"PT{max(1, 6 - idx)}M"
            )
            
            # Simulate chapter generation time
            time.sleep(2)  # Simulated AI processing
            
            # Generate chapter content
            chapter_content = {
                **chapter,
                "content_outline": f"Detailed content for {chapter['title']}",
                "subchapters": [
                    {
                        "id": str(uuid4()),
                        "sequence_number": 1,
                        "title": f"{chapter['title']} - Introduction",
                        "content_type": "theory",
                        "content_blocks": [
                            {
                                "type": "text",
                                "content": f"Introduction to {chapter['title']}...",
                                "order": 1,
                                "metadata": {}
                            }
                        ],
                        "key_concepts": ["Key concept 1", "Key concept 2"]
                    }
                ]
            }
            generated_chapters.append(chapter_content)
        
        # Phase 3: Generate assessments (15%)
        self.update_progress(task_id, 80.0, GenerationPhase.ASSESSMENT, "PT2M")
        
        # Generate final assessment
        final_assessment = {
            "id": str(uuid4()),
            "type": "final",
            "title": f"Final Assessment - {course_data.get('title', 'Course')}",
            "questions": [
                {
                    "id": str(uuid4()),
                    "type": "multiple_choice",
                    "question": "Which concept is fundamental to this course?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "difficulty": "medium"
                }
            ]
        }
        
        self.update_progress(task_id, 90.0, GenerationPhase.ASSESSMENT, "PT1M")
        
        # Phase 4: Final validation (10%)
        self.update_progress(task_id, 95.0, GenerationPhase.VALIDATION, "PT30S")
        
        # Validate generated content
        quality_metrics = {
            "readability_score": 85.5,
            "pedagogical_alignment": 0.92,
            "objective_coverage": 0.95,
            "content_accuracy": 0.88,
            "bias_detection_score": 0.97,
            "generation_timestamp": datetime.utcnow().isoformat()
        }
        
        # Complete course data
        complete_course = {
            "id": course_id,
            "status": "ready",
            "chapters": generated_chapters,
            "final_assessment": final_assessment,
            "quality_metrics": quality_metrics,
            "generation_metadata": {
                "task_id": task_id,
                "generation_time": datetime.utcnow().isoformat(),
                "total_duration": str(datetime.utcnow() - self.progress_data["start_time"]),
                "retry_count": self.request.retries
            },
            **course_data
        }
        
        # Complete task
        self.update_progress(task_id, 100.0, GenerationPhase.VALIDATION, "PT0S")
        
        logger.info(f"Course generation completed for course {course_id}")
        return complete_course
        
    except Exception as exc:
        self.handle_error(task_id, exc)
        
        # Retry if under limit
        if self.request.retries < self.max_retries:
            logger.warning(f"Retrying course generation for course {course_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(
    bind=True,
    base=BaseGenerationTask,
    name="src.tasks.generation_tasks.generate_chapter_task",
    max_retries=3,
    soft_time_limit=110,  # <2 min as per requirements
    time_limit=120,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def generate_chapter_task(
    self,
    chapter_data: Dict[str, Any],
    course_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate content for a single chapter.
    
    Args:
        chapter_data: Chapter creation data
        course_context: Course context for alignment
        
    Returns:
        Generated chapter with subchapters and content
    """
    task_id = self.request.id
    chapter_id = chapter_data.get("id") or str(uuid4())
    
    try:
        self.progress_data["start_time"] = datetime.utcnow()
        self.update_progress(
            task_id=task_id,
            progress_percentage=0.0,
            phase=GenerationPhase.CONTENT,
            estimated_remaining="PT2M"
        )
        
        logger.info(f"Starting chapter generation for chapter {chapter_id}")
        
        # Generate subchapters (50%)
        self.update_progress(task_id, 25.0, GenerationPhase.CONTENT, "PT90S")
        
        num_subchapters = 3
        subchapters = []
        
        for i in range(num_subchapters):
            subchapter = {
                "id": str(uuid4()),
                "sequence_number": i + 1,
                "title": f"{chapter_data.get('title', 'Chapter')} - Section {i + 1}",
                "content_type": "mixed" if i % 2 == 0 else "theory",
                "content_blocks": [
                    {
                        "type": "text",
                        "content": f"Content for section {i + 1} of the chapter...",
                        "order": 1,
                        "metadata": {"word_count": 250}
                    }
                ],
                "key_concepts": [f"Concept {i + 1}.1", f"Concept {i + 1}.2"],
                "summary": f"Summary of section {i + 1}"
            }
            subchapters.append(subchapter)
            
            progress = 25.0 + ((i + 1) / num_subchapters) * 50.0
            self.update_progress(task_id, progress, GenerationPhase.CONTENT, "PT60S")
        
        # Generate chapter quiz (25%)
        self.update_progress(task_id, 75.0, GenerationPhase.ASSESSMENT, "PT30S")
        
        chapter_quiz = {
            "id": str(uuid4()),
            "type": "chapter",
            "title": f"Quiz - {chapter_data.get('title', 'Chapter')}",
            "questions": [
                {
                    "id": str(uuid4()),
                    "type": "multiple_choice",
                    "question": f"What is the main concept in {chapter_data.get('title', 'this chapter')}?",
                    "options": ["Option A", "Option B", "Option C"],
                    "correct_answer": "Option A",
                    "difficulty": "medium"
                }
            ]
        }
        
        # Final assembly (25%)
        self.update_progress(task_id, 90.0, GenerationPhase.VALIDATION, "PT10S")
        
        complete_chapter = {
            "id": chapter_id,
            "subchapters": subchapters,
            "chapter_quiz": chapter_quiz,
            "generation_metadata": {
                "task_id": task_id,
                "generation_time": datetime.utcnow().isoformat(),
                "total_duration": str(datetime.utcnow() - self.progress_data["start_time"])
            },
            **chapter_data
        }
        
        self.update_progress(task_id, 100.0, GenerationPhase.VALIDATION, "PT0S")
        
        logger.info(f"Chapter generation completed for chapter {chapter_id}")
        return complete_chapter
        
    except Exception as exc:
        self.handle_error(task_id, exc)
        
        if self.request.retries < self.max_retries:
            logger.warning(f"Retrying chapter generation for chapter {chapter_id}")
            raise self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        
        raise exc


@celery_app.task(
    bind=True,
    base=BaseGenerationTask,
    name="src.tasks.generation_tasks.validate_quality_task",
    max_retries=2,
    soft_time_limit=300,  # 5 minutes for quality validation
    time_limit=360
)
def validate_quality_task(
    self,
    content_data: Dict[str, Any],
    validation_criteria: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate content quality and generate quality metrics.
    
    Args:
        content_data: Content to validate (course or chapter)
        validation_criteria: Specific validation criteria
        
    Returns:
        Quality metrics and validation results
    """
    task_id = self.request.id
    content_id = content_data.get("id", "unknown")
    
    try:
        self.progress_data["start_time"] = datetime.utcnow()
        self.update_progress(
            task_id=task_id,
            progress_percentage=0.0,
            phase=GenerationPhase.VALIDATION,
            estimated_remaining="PT5M"
        )
        
        logger.info(f"Starting quality validation for content {content_id}")
        
        # Readability analysis (25%)
        self.update_progress(task_id, 10.0, GenerationPhase.VALIDATION, "PT4M")
        time.sleep(1)  # Simulate processing
        
        readability_score = 85.5  # Simulated analysis
        self.update_progress(task_id, 25.0, GenerationPhase.VALIDATION, "PT3M")
        
        # Pedagogical alignment check (25%)
        pedagogical_alignment = 0.92
        self.update_progress(task_id, 50.0, GenerationPhase.VALIDATION, "PT2M")
        
        # Content accuracy validation (25%)
        content_accuracy = 0.88
        self.update_progress(task_id, 75.0, GenerationPhase.VALIDATION, "PT1M")
        
        # Bias detection (25%)
        bias_score = 0.97
        self.update_progress(task_id, 90.0, GenerationPhase.VALIDATION, "PT30S")
        
        # Generate final metrics
        quality_metrics = {
            "readability_score": readability_score,
            "pedagogical_alignment": pedagogical_alignment,
            "objective_coverage": 0.95,
            "content_accuracy": content_accuracy,
            "bias_detection_score": bias_score,
            "user_satisfaction_score": None,  # Will be updated after user feedback
            "generation_timestamp": datetime.utcnow().isoformat(),
            "validation_criteria": validation_criteria or {},
            "validation_metadata": {
                "task_id": task_id,
                "validation_time": datetime.utcnow().isoformat(),
                "content_id": content_id
            }
        }
        
        self.update_progress(task_id, 100.0, GenerationPhase.VALIDATION, "PT0S")
        
        logger.info(f"Quality validation completed for content {content_id}")
        return quality_metrics
        
    except Exception as exc:
        self.handle_error(task_id, exc)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        
        raise exc


@celery_app.task(
    bind=True,
    base=BaseGenerationTask,
    name="src.tasks.generation_tasks.export_course_task",
    max_retries=2,
    soft_time_limit=180,  # 3 minutes for export
    time_limit=240
)
def export_course_task(
    self,
    course_data: Dict[str, Any],
    export_format: str,
    export_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Export course to specified format (PDF, SCORM, etc.).
    
    Args:
        course_data: Complete course data
        export_format: Target format (pdf, scorm, json, etc.)
        export_options: Format-specific options
        
    Returns:
        Export results with file URLs and metadata
    """
    task_id = self.request.id
    course_id = course_data.get("id", "unknown")
    
    try:
        self.progress_data["start_time"] = datetime.utcnow()
        self.update_progress(
            task_id=task_id,
            progress_percentage=0.0,
            phase=GenerationPhase.EXPORT,
            estimated_remaining="PT3M"
        )
        
        logger.info(f"Starting export for course {course_id} to format {export_format}")
        
        # Prepare content (30%)
        self.update_progress(task_id, 15.0, GenerationPhase.EXPORT, "PT2M30S")
        time.sleep(1)  # Simulate content preparation
        
        # Generate export files (60%)
        self.update_progress(task_id, 30.0, GenerationPhase.EXPORT, "PT2M")
        
        # Simulate format-specific processing
        if export_format.lower() == "pdf":
            # PDF generation simulation
            time.sleep(2)
            export_files = [
                {
                    "filename": f"course_{course_id}.pdf",
                    "url": f"/exports/pdf/course_{course_id}.pdf",
                    "size_bytes": 2048576,  # ~2MB
                    "type": "application/pdf"
                }
            ]
        elif export_format.lower() == "scorm":
            # SCORM package generation
            time.sleep(3)
            export_files = [
                {
                    "filename": f"course_{course_id}_scorm.zip",
                    "url": f"/exports/scorm/course_{course_id}_scorm.zip",
                    "size_bytes": 5242880,  # ~5MB
                    "type": "application/zip"
                }
            ]
        else:
            # JSON or other formats
            export_files = [
                {
                    "filename": f"course_{course_id}.json",
                    "url": f"/exports/json/course_{course_id}.json",
                    "size_bytes": 1048576,  # ~1MB
                    "type": "application/json"
                }
            ]
        
        self.update_progress(task_id, 90.0, GenerationPhase.EXPORT, "PT30S")
        
        # Finalize export
        export_result = {
            "course_id": course_id,
            "export_format": export_format,
            "files": export_files,
            "export_metadata": {
                "task_id": task_id,
                "export_time": datetime.utcnow().isoformat(),
                "total_duration": str(datetime.utcnow() - self.progress_data["start_time"]),
                "options": export_options or {}
            },
            "download_expires": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        self.update_progress(task_id, 100.0, GenerationPhase.EXPORT, "PT0S")
        
        logger.info(f"Export completed for course {course_id}")
        return export_result
        
    except Exception as exc:
        self.handle_error(task_id, exc)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        
        raise exc


@celery_app.task(
    bind=True,
    base=BaseGenerationTask,
    name="src.tasks.generation_tasks.regenerate_chapter_task",
    max_retries=3,
    soft_time_limit=110,  # <2 min like generate_chapter_task
    time_limit=120
)
def regenerate_chapter_task(
    self,
    chapter_id: str,
    course_context: Dict[str, Any],
    regeneration_reason: str,
    regeneration_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Regenerate a specific chapter with improvements.
    
    Args:
        chapter_id: ID of chapter to regenerate
        course_context: Course context for alignment
        regeneration_reason: Reason for regeneration
        regeneration_options: Specific regeneration parameters
        
    Returns:
        Regenerated chapter data
    """
    task_id = self.request.id
    
    try:
        self.progress_data["start_time"] = datetime.utcnow()
        self.update_progress(
            task_id=task_id,
            progress_percentage=0.0,
            phase=GenerationPhase.CONTENT,
            estimated_remaining="PT2M",
            metadata={"regeneration_reason": regeneration_reason}
        )
        
        logger.info(f"Starting chapter regeneration for chapter {chapter_id}: {regeneration_reason}")
        
        # Analyze regeneration requirements (20%)
        self.update_progress(task_id, 10.0, GenerationPhase.CONTENT, "PT90S")
        time.sleep(1)
        
        # Apply regeneration improvements based on reason
        improvement_focus = "general"
        if "too advanced" in regeneration_reason.lower():
            improvement_focus = "simplify"
        elif "too basic" in regeneration_reason.lower():
            improvement_focus = "deepen"
        elif "accuracy" in regeneration_reason.lower():
            improvement_focus = "accuracy"
        
        self.update_progress(
            task_id, 
            20.0, 
            GenerationPhase.CONTENT, 
            "PT80S",
            metadata={"improvement_focus": improvement_focus}
        )
        
        # Generate improved content (60%)
        regenerated_chapter = {
            "id": chapter_id,
            "title": f"Improved Chapter - {course_context.get('title', 'Course')}",
            "learning_objectives": [
                "Improved learning objective 1",
                "Enhanced learning objective 2"
            ],
            "content_outline": f"Regenerated content outline based on: {regeneration_reason}",
            "subchapters": [
                {
                    "id": str(uuid4()),
                    "sequence_number": 1,
                    "title": "Improved Introduction",
                    "content_type": "mixed",
                    "content_blocks": [
                        {
                            "type": "text",
                            "content": f"Improved content addressing: {regeneration_reason}",
                            "order": 1,
                            "metadata": {"improvement_focus": improvement_focus}
                        }
                    ],
                    "key_concepts": ["Improved concept 1", "Enhanced concept 2"]
                }
            ],
            "regeneration_metadata": {
                "task_id": task_id,
                "original_chapter_id": chapter_id,
                "regeneration_reason": regeneration_reason,
                "improvement_focus": improvement_focus,
                "regeneration_time": datetime.utcnow().isoformat(),
                "options": regeneration_options or {}
            }
        }
        
        # Progress through regeneration
        for progress in [40.0, 60.0, 80.0]:
            self.update_progress(task_id, progress, GenerationPhase.CONTENT, "PT60S")
            time.sleep(0.5)
        
        # Final validation (20%)
        self.update_progress(task_id, 90.0, GenerationPhase.VALIDATION, "PT10S")
        
        # Add quality improvements
        regenerated_chapter["quality_improvements"] = {
            "readability_improvement": 15.0,
            "pedagogical_alignment_improvement": 0.08,
            "content_accuracy_improvement": 0.12
        }
        
        self.update_progress(task_id, 100.0, GenerationPhase.VALIDATION, "PT0S")
        
        logger.info(f"Chapter regeneration completed for chapter {chapter_id}")
        return regenerated_chapter
        
    except Exception as exc:
        self.handle_error(task_id, exc)
        
        if self.request.retries < self.max_retries:
            logger.warning(f"Retrying chapter regeneration for chapter {chapter_id}")
            raise self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        
        raise exc


# Task status monitoring utilities
@celery_app.task(name="src.tasks.generation_tasks.get_task_status")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get task status and progress information.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status and progress data
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        if result.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "progress_percentage": 0.0,
                "current_phase": "structure",
                "estimated_time_remaining": "PT0S"
            }
        elif result.state == "PROGRESS":
            return result.info
        elif result.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "completed",
                "progress_percentage": 100.0,
                "current_phase": "validation",
                "estimated_time_remaining": "PT0S",
                "result": result.result
            }
        elif result.state == "FAILURE":
            error_info = result.info or {}
            return {
                "task_id": task_id,
                "status": "failed",
                "progress_percentage": 0.0,
                "current_phase": "structure",
                "estimated_time_remaining": "PT0S",
                "error_details": str(result.info) if result.info else "Unknown error",
                "retry_count": error_info.get("retry_count", 0)
            }
        else:
            return {
                "task_id": task_id,
                "status": result.state.lower(),
                "progress_percentage": 0.0,
                "current_phase": "structure",
                "estimated_time_remaining": "PT0S"
            }
            
    except Exception as exc:
        logger.error(f"Error getting task status for {task_id}: {exc}")
        return {
            "task_id": task_id,
            "status": "failed",
            "progress_percentage": 0.0,
            "current_phase": "structure",
            "estimated_time_remaining": "PT0S",
            "error_details": f"Status check failed: {exc}"
        }