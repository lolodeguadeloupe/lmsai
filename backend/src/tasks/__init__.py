"""
Background task processing with Celery.

This module implements the task queue system for asynchronous course generation
and processing operations.
"""

from .celery_app import celery_app
from .generation_tasks import (
    export_course_task,
    generate_chapter_task,
    generate_course_task,
    regenerate_chapter_task,
    validate_quality_task,
)
from .utils import task_manager

__all__ = [
    "celery_app",
    "generate_course_task",
    "generate_chapter_task",
    "validate_quality_task",
    "export_course_task",
    "regenerate_chapter_task",
    "task_manager",
]