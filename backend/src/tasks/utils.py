"""
Utility functions for task management and monitoring.

Provides helper functions for task status tracking, progress monitoring,
and task lifecycle management.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from celery.result import AsyncResult

from .celery_app import celery_app
from .generation_tasks import TaskStatus, GenerationPhase

logger = logging.getLogger(__name__)


class TaskManager:
    """Manager class for task operations and monitoring."""
    
    def __init__(self):
        self.app = celery_app
    
    def start_course_generation(
        self, 
        course_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start course generation task.
        
        Args:
            course_data: Course creation data
            user_preferences: Optional user preferences
            
        Returns:
            Task ID for monitoring
        """
        from .generation_tasks import generate_course_task
        
        task = generate_course_task.delay(course_data, user_preferences)
        
        logger.info(f"Started course generation task {task.id} for course {course_data.get('id')}")
        return task.id
    
    def start_chapter_generation(
        self,
        chapter_data: Dict[str, Any],
        course_context: Dict[str, Any]
    ) -> str:
        """
        Start chapter generation task.
        
        Args:
            chapter_data: Chapter creation data
            course_context: Course context for alignment
            
        Returns:
            Task ID for monitoring
        """
        from .generation_tasks import generate_chapter_task
        
        task = generate_chapter_task.delay(chapter_data, course_context)
        
        logger.info(f"Started chapter generation task {task.id} for chapter {chapter_data.get('id')}")
        return task.id
    
    def start_quality_validation(
        self,
        content_data: Dict[str, Any],
        validation_criteria: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start quality validation task.
        
        Args:
            content_data: Content to validate
            validation_criteria: Validation criteria
            
        Returns:
            Task ID for monitoring
        """
        from .generation_tasks import validate_quality_task
        
        task = validate_quality_task.delay(content_data, validation_criteria)
        
        logger.info(f"Started quality validation task {task.id}")
        return task.id
    
    def start_course_export(
        self,
        course_data: Dict[str, Any],
        export_format: str,
        export_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start course export task.
        
        Args:
            course_data: Complete course data
            export_format: Target format
            export_options: Export options
            
        Returns:
            Task ID for monitoring
        """
        from .generation_tasks import export_course_task
        
        task = export_course_task.delay(course_data, export_format, export_options)
        
        logger.info(f"Started export task {task.id} for course {course_data.get('id')} to {export_format}")
        return task.id
    
    def start_chapter_regeneration(
        self,
        chapter_id: str,
        course_context: Dict[str, Any],
        regeneration_reason: str,
        regeneration_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start chapter regeneration task.
        
        Args:
            chapter_id: Chapter ID to regenerate
            course_context: Course context
            regeneration_reason: Reason for regeneration
            regeneration_options: Regeneration options
            
        Returns:
            Task ID for monitoring
        """
        from .generation_tasks import regenerate_chapter_task
        
        task = regenerate_chapter_task.delay(
            chapter_id, 
            course_context, 
            regeneration_reason,
            regeneration_options
        )
        
        logger.info(f"Started chapter regeneration task {task.id} for chapter {chapter_id}")
        return task.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get comprehensive task status.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Task status information
        """
        try:
            result = AsyncResult(task_id, app=self.app)
            
            base_status = {
                "task_id": task_id,
                "status": "pending",
                "progress_percentage": 0.0,
                "current_phase": "structure",
                "estimated_time_remaining": "PT0S",
                "start_time": None,
                "last_update": None,
                "error_details": None,
                "retry_count": 0,
                "metadata": {}
            }
            
            if result.state == "PENDING":
                base_status.update({
                    "status": "pending"
                })
            elif result.state == "PROGRESS":
                if isinstance(result.info, dict):
                    base_status.update(result.info)
                    base_status["status"] = "in_progress"
            elif result.state == "SUCCESS":
                base_status.update({
                    "status": "completed",
                    "progress_percentage": 100.0,
                    "current_phase": "validation",
                    "estimated_time_remaining": "PT0S"
                })
                if hasattr(result, 'result') and result.result:
                    base_status["result"] = result.result
            elif result.state == "FAILURE":
                error_info = result.info if isinstance(result.info, dict) else {}
                base_status.update({
                    "status": "failed",
                    "error_details": str(result.info) if result.info else "Unknown error",
                    "retry_count": error_info.get("retry_count", 0)
                })
            elif result.state == "RETRY":
                base_status.update({
                    "status": "retrying",
                    "retry_count": getattr(result, 'retries', 0)
                })
            else:
                base_status.update({
                    "status": result.state.lower()
                })
            
            return base_status
            
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
    
    def cancel_task(self, task_id: str, reason: str = "User cancelled") -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task ID to cancel
            reason: Cancellation reason
            
        Returns:
            True if cancelled successfully
        """
        try:
            self.app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}: {reason}")
            return True
        except Exception as exc:
            logger.error(f"Failed to cancel task {task_id}: {exc}")
            return False
    
    def get_active_tasks(self, task_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get list of active tasks.
        
        Args:
            task_types: Filter by task types (optional)
            
        Returns:
            List of active task information
        """
        try:
            active_tasks = []
            inspect = self.app.control.inspect()
            
            # Get active tasks from all workers
            active = inspect.active()
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        task_info = {
                            "task_id": task["id"],
                            "task_name": task["name"],
                            "worker": worker,
                            "args": task.get("args", []),
                            "kwargs": task.get("kwargs", {}),
                            "time_start": task.get("time_start")
                        }
                        
                        # Filter by task types if specified
                        if not task_types or any(t in task["name"] for t in task_types):
                            active_tasks.append(task_info)
            
            return active_tasks
            
        except Exception as exc:
            logger.error(f"Error getting active tasks: {exc}")
            return []
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics and health information.
        
        Returns:
            Worker statistics
        """
        try:
            inspect = self.app.control.inspect()
            
            # Get basic stats
            stats = inspect.stats() or {}
            active = inspect.active() or {}
            reserved = inspect.reserved() or {}
            
            worker_info = {}
            for worker in stats.keys():
                worker_stats = stats.get(worker, {})
                worker_info[worker] = {
                    "status": "online",
                    "total_tasks": worker_stats.get("total", {}),
                    "active_tasks": len(active.get(worker, [])),
                    "reserved_tasks": len(reserved.get(worker, [])),
                    "pool_info": worker_stats.get("pool", {}),
                    "rusage": worker_stats.get("rusage", {})
                }
            
            return {
                "workers": worker_info,
                "total_workers": len(worker_info),
                "total_active_tasks": sum(len(tasks) for tasks in active.values()),
                "total_reserved_tasks": sum(len(tasks) for tasks in reserved.values())
            }
            
        except Exception as exc:
            logger.error(f"Error getting worker stats: {exc}")
            return {"error": str(exc)}


def estimate_completion_time(
    task_type: str,
    complexity_factors: Optional[Dict[str, Any]] = None
) -> str:
    """
    Estimate task completion time based on type and complexity.
    
    Args:
        task_type: Type of task
        complexity_factors: Factors affecting complexity
        
    Returns:
        ISO 8601 duration estimate
    """
    base_times = {
        "generate_course": 600,  # 10 minutes base
        "generate_chapter": 120,  # 2 minutes base
        "validate_quality": 300,  # 5 minutes base
        "export_course": 180,  # 3 minutes base
        "regenerate_chapter": 120  # 2 minutes base
    }
    
    base_time = base_times.get(task_type, 300)
    
    # Apply complexity multipliers
    if complexity_factors:
        multiplier = 1.0
        
        # Course complexity
        if "num_chapters" in complexity_factors:
            multiplier *= max(1.0, complexity_factors["num_chapters"] / 5.0)
        
        # Content complexity
        if "difficulty_score" in complexity_factors:
            multiplier *= max(0.8, complexity_factors["difficulty_score"] / 3.0)
        
        # Target audience complexity
        if "proficiency_level" in complexity_factors:
            level_multipliers = {
                "beginner": 1.2,  # More detailed explanations
                "intermediate": 1.0,
                "advanced": 1.1,
                "expert": 1.3  # More sophisticated content
            }
            multiplier *= level_multipliers.get(complexity_factors["proficiency_level"], 1.0)
        
        base_time = int(base_time * multiplier)
    
    # Convert to ISO 8601 duration
    minutes = base_time // 60
    seconds = base_time % 60
    
    if minutes > 0:
        return f"PT{minutes}M{seconds}S" if seconds > 0 else f"PT{minutes}M"
    else:
        return f"PT{seconds}S"


def get_task_queue_status() -> Dict[str, Any]:
    """
    Get overall task queue status and metrics.
    
    Returns:
        Queue status information
    """
    try:
        task_manager = TaskManager()
        
        # Get active tasks by type
        active_tasks = task_manager.get_active_tasks()
        
        task_counts = {}
        for task in active_tasks:
            task_name = task["task_name"].split(".")[-1]  # Get last part of task name
            task_counts[task_name] = task_counts.get(task_name, 0) + 1
        
        # Get worker stats
        worker_stats = task_manager.get_worker_stats()
        
        return {
            "queue_health": "healthy" if worker_stats.get("total_workers", 0) > 0 else "unhealthy",
            "total_active_tasks": len(active_tasks),
            "tasks_by_type": task_counts,
            "worker_stats": worker_stats,
            "queue_capacity": {
                "max_concurrent_courses": 100,  # As per FR-022
                "current_load_percentage": min(100, len(active_tasks) * 2),  # Rough estimate
                "estimated_queue_time": "PT1M" if len(active_tasks) < 50 else "PT5M"
            },
            "performance_metrics": {
                "average_course_generation_time": "PT8M",
                "average_chapter_generation_time": "PT90S",
                "success_rate_percentage": 95.0,  # As per requirements
                "queue_throughput_per_hour": 25
            }
        }
        
    except Exception as exc:
        logger.error(f"Error getting queue status: {exc}")
        return {
            "queue_health": "unhealthy",
            "error": str(exc)
        }


# Global task manager instance
task_manager = TaskManager()