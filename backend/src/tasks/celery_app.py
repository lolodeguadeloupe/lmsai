"""
Celery application configuration for background task processing.

Supports Redis as message broker and result backend with optimized settings
for course generation workloads.
"""

import os
from typing import Dict, Any

from celery import Celery
from kombu import Queue


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.
    
    Returns:
        Configured Celery application instance
    """
    # Redis configuration from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    app = Celery("course_generation")
    
    # Configuration
    app.conf.update(
        # Broker and backend
        broker_url=redis_url,
        result_backend=redis_url,
        
        # Task routing
        task_routes={
            "src.tasks.generation_tasks.generate_course_task": {"queue": "course_generation"},
            "src.tasks.generation_tasks.generate_chapter_task": {"queue": "chapter_generation"},
            "src.tasks.generation_tasks.validate_quality_task": {"queue": "quality_validation"},
            "src.tasks.generation_tasks.export_course_task": {"queue": "export"},
            "src.tasks.generation_tasks.regenerate_chapter_task": {"queue": "chapter_generation"},
        },
        
        # Queue definitions
        task_default_queue="default",
        task_queues=(
            Queue("course_generation", routing_key="course_generation"),
            Queue("chapter_generation", routing_key="chapter_generation"),
            Queue("quality_validation", routing_key="quality_validation"),
            Queue("export", routing_key="export"),
            Queue("default", routing_key="default"),
        ),
        
        # Concurrency and performance
        worker_concurrency=4,  # Adjustable based on system resources
        worker_prefetch_multiplier=1,  # Prevent overloading workers
        task_acks_late=True,  # Acknowledge after completion
        worker_disable_rate_limits=False,
        
        # Retry configuration
        task_retry_jitter=True,
        task_retry_jitter_max=5.0,
        task_default_retry_delay=60,  # 1 minute default retry delay
        task_max_retries=3,
        
        # Result backend settings
        result_expires=3600 * 24,  # 24 hours
        result_compression="gzip",
        
        # Monitoring and logging
        worker_send_task_events=True,
        task_send_sent_event=True,
        task_track_started=True,
        
        # Task time limits (2min for chapters as per requirements)
        task_soft_time_limit=110,  # 1:50 soft limit
        task_time_limit=120,  # 2:00 hard limit for chapters
        
        # Serialization
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        
        # Security
        worker_hijack_root_logger=False,
        worker_log_color=False,
        
        # Performance tuning for 100+ concurrent courses
        broker_pool_limit=50,
        broker_connection_retry_on_startup=True,
        broker_connection_retry=True,
        broker_connection_max_retries=10,
        
        # Task execution
        task_always_eager=False,  # Set to True for testing
        task_eager_propagates=True,
        task_store_eager_result=True,
    )
    
    return app


# Global Celery instance
celery_app = create_celery_app()


@celery_app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """
    Health check task for monitoring Celery worker status.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "worker_id": self.request.id,
        "timestamp": self.request.utc,
    }


# Auto-discover tasks
celery_app.autodiscover_tasks(["src.tasks"])