#!/usr/bin/env python3
"""
Celery worker startup script.

Provides worker configuration and startup for the course generation task queue.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from .celery_app import celery_app
from .config import get_celery_config, get_performance_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_worker():
    """Configure the Celery worker for course generation."""
    environment = os.getenv("ENVIRONMENT", "development")
    config = get_celery_config(environment)
    
    # Apply configuration to Celery app
    celery_app.conf.update(config)
    
    logger.info(f"Configured Celery worker for {environment} environment")
    return celery_app


def start_worker():
    """Start the Celery worker with optimized settings."""
    app = configure_worker()
    
    # Get performance settings
    perf_settings = get_performance_settings()
    
    # Worker arguments
    worker_args = [
        "worker",
        "--loglevel=INFO",
        f"--concurrency={perf_settings['worker_pool_size']}",
        f"--prefetch-multiplier={perf_settings['prefetch_multiplier']}",
        f"--max-tasks-per-child={perf_settings['max_tasks_per_child']}",
        "--time-limit=660",  # 11 minutes (allows for course generation)
        "--soft-time-limit=600",  # 10 minutes soft limit
    ]
    
    # Queue configuration
    queues = [
        "course_generation",
        "chapter_generation", 
        "quality_validation",
        "export",
        "default"
    ]
    worker_args.extend([f"--queues={','.join(queues)}"])
    
    # Performance optimizations
    worker_args.extend([
        "--optimization=fair",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat"
    ])
    
    logger.info(f"Starting Celery worker with args: {' '.join(worker_args)}")
    
    # Start worker
    app.worker_main(worker_args)


def start_beat():
    """Start Celery beat for periodic tasks."""
    app = configure_worker()
    
    beat_args = [
        "beat",
        "--loglevel=INFO",
        "--schedule-filename=/tmp/celerybeat-schedule"
    ]
    
    logger.info("Starting Celery beat scheduler")
    app.start(beat_args)


def start_flower():
    """Start Flower monitoring dashboard."""
    from celery.bin import flower
    
    flower_args = [
        "--port=5555",
        "--address=0.0.0.0",
        "--broker=redis://localhost:6379/0"
    ]
    
    logger.info("Starting Flower monitoring dashboard on http://0.0.0.0:5555")
    flower.flower(flower_args)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Celery worker management")
    parser.add_argument(
        "command",
        choices=["worker", "beat", "flower", "monitor"],
        help="Command to run"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "testing", "production"],
        default="development",
        help="Environment configuration"
    )
    parser.add_argument(
        "--queues",
        default="course_generation,chapter_generation,quality_validation,export,default",
        help="Comma-separated list of queues to process"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Number of concurrent worker processes"
    )
    parser.add_argument(
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Set environment
    os.environ["ENVIRONMENT"] = args.environment
    
    if args.command == "worker":
        # Override worker settings if specified
        if args.concurrency:
            os.environ["CELERY_WORKER_CONCURRENCY"] = str(args.concurrency)
        
        start_worker()
        
    elif args.command == "beat":
        start_beat()
        
    elif args.command == "flower":
        start_flower()
        
    elif args.command == "monitor":
        # Simple monitoring command
        app = configure_worker()
        inspect = app.control.inspect()
        
        print("=== Celery Worker Status ===")
        
        # Check active workers
        stats = inspect.stats()
        if stats:
            print(f"Active workers: {len(stats)}")
            for worker, stat in stats.items():
                print(f"  {worker}: {stat.get('total', 'Unknown')} total tasks")
        else:
            print("No active workers found")
        
        # Check active tasks
        active = inspect.active()
        if active:
            total_active = sum(len(tasks) for tasks in active.values())
            print(f"Active tasks: {total_active}")
        else:
            print("No active tasks")
        
        # Check reserved tasks
        reserved = inspect.reserved()
        if reserved:
            total_reserved = sum(len(tasks) for tasks in reserved.values())
            print(f"Reserved tasks: {total_reserved}")
        else:
            print("No reserved tasks")
        
        print("=== End Status ===")
    
    else:
        parser.print_help()