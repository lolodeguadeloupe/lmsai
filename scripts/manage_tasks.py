#!/usr/bin/env python3
"""
Task queue management script.

Provides CLI commands for managing the Celery task queue, monitoring
performance, and troubleshooting issues.
"""

import os
import sys
import json
import time
import click
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add backend src to path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from tasks import task_manager
from tasks.utils import get_task_queue_status, estimate_completion_time
from tasks.config import get_performance_settings


@click.group()
def cli():
    """Course Generation Platform Task Queue Management"""
    pass


@cli.command()
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']))
def status(output_format):
    """Show task queue status and worker information."""
    try:
        queue_status = get_task_queue_status()
        worker_stats = task_manager.get_worker_stats()
        active_tasks = task_manager.get_active_tasks()
        
        if output_format == 'json':
            click.echo(json.dumps({
                "queue_status": queue_status,
                "worker_stats": worker_stats,
                "active_tasks": active_tasks
            }, indent=2))
        else:
            # Table format
            click.echo("=== Task Queue Status ===")
            click.echo(f"Queue Health: {queue_status.get('queue_health', 'unknown')}")
            click.echo(f"Total Active Tasks: {queue_status.get('total_active_tasks', 0)}")
            
            if 'tasks_by_type' in queue_status:
                click.echo("\nTasks by Type:")
                for task_type, count in queue_status['tasks_by_type'].items():
                    click.echo(f"  {task_type}: {count}")
            
            click.echo(f"\n=== Worker Information ===")
            if 'workers' in worker_stats:
                click.echo(f"Total Workers: {len(worker_stats['workers'])}")
                for worker, info in worker_stats['workers'].items():
                    click.echo(f"  {worker}: {info.get('active_tasks', 0)} active, {info.get('reserved_tasks', 0)} reserved")
            else:
                click.echo("No workers available")
            
            if active_tasks:
                click.echo(f"\n=== Active Tasks ===")
                for task in active_tasks[:10]:  # Limit to first 10
                    click.echo(f"  {task['task_id']}: {task['task_name']} on {task['worker']}")
                if len(active_tasks) > 10:
                    click.echo(f"  ... and {len(active_tasks) - 10} more")
            
    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']))
def get_task(task_id, output_format):
    """Get detailed information about a specific task."""
    try:
        status = task_manager.get_task_status(task_id)
        
        if output_format == 'json':
            click.echo(json.dumps(status, indent=2))
        else:
            click.echo(f"=== Task {task_id} ===")
            click.echo(f"Status: {status.get('status', 'unknown')}")
            click.echo(f"Progress: {status.get('progress_percentage', 0):.1f}%")
            click.echo(f"Phase: {status.get('current_phase', 'unknown')}")
            click.echo(f"Estimated Time Remaining: {status.get('estimated_time_remaining', 'unknown')}")
            
            if status.get('error_details'):
                click.echo(f"Error: {status['error_details']}")
            
            if status.get('retry_count', 0) > 0:
                click.echo(f"Retries: {status['retry_count']}")
            
            if 'metadata' in status and status['metadata']:
                click.echo("\nMetadata:")
                for key, value in status['metadata'].items():
                    click.echo(f"  {key}: {value}")
                    
    except Exception as e:
        click.echo(f"Error getting task info: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.option('--reason', default='Manual cancellation', help='Reason for cancellation')
def cancel(task_id, reason):
    """Cancel a running task."""
    try:
        result = task_manager.cancel_task(task_id, reason)
        if result:
            click.echo(f"Task {task_id} cancelled successfully")
        else:
            click.echo(f"Failed to cancel task {task_id}")
            
    except Exception as e:
        click.echo(f"Error cancelling task: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--count', default=10, help='Number of tasks to show')
@click.option('--task-type', help='Filter by task type')
def active(count, task_type):
    """List active tasks."""
    try:
        filters = [task_type] if task_type else None
        active_tasks = task_manager.get_active_tasks(filters)
        
        if not active_tasks:
            click.echo("No active tasks")
            return
        
        click.echo(f"=== Active Tasks (showing {min(count, len(active_tasks))}) ===")
        for task in active_tasks[:count]:
            click.echo(f"{task['task_id']}: {task['task_name']} on {task['worker']}")
            if task.get('time_start'):
                click.echo(f"  Started: {task['time_start']}")
                
    except Exception as e:
        click.echo(f"Error getting active tasks: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--duration', default=60, help='Monitoring duration in seconds')
@click.option('--interval', default=5, help='Update interval in seconds')
def monitor(duration, interval):
    """Monitor task queue in real-time."""
    try:
        start_time = time.time()
        
        click.echo("=== Real-time Task Queue Monitor ===")
        click.echo("Press Ctrl+C to stop\n")
        
        while time.time() - start_time < duration:
            try:
                # Clear screen (works on most terminals)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Get current status
                queue_status = get_task_queue_status()
                worker_stats = task_manager.get_worker_stats()
                
                # Display header
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                click.echo(f"=== Task Queue Monitor - {timestamp} ===")
                
                # Queue status
                click.echo(f"Queue Health: {queue_status.get('queue_health', 'unknown')}")
                click.echo(f"Active Tasks: {queue_status.get('total_active_tasks', 0)}")
                
                # Worker info
                if 'workers' in worker_stats:
                    click.echo(f"Active Workers: {len(worker_stats['workers'])}")
                    total_active = sum(w.get('active_tasks', 0) for w in worker_stats['workers'].values())
                    total_reserved = sum(w.get('reserved_tasks', 0) for w in worker_stats['workers'].values())
                    click.echo(f"Total Active: {total_active}, Reserved: {total_reserved}")
                
                # Performance metrics
                if 'performance_metrics' in queue_status:
                    metrics = queue_status['performance_metrics']
                    click.echo(f"Success Rate: {metrics.get('success_rate_percentage', 0):.1f}%")
                    click.echo(f"Avg Chapter Time: {metrics.get('average_chapter_generation_time', 'unknown')}")
                
                # Task breakdown
                if 'tasks_by_type' in queue_status:
                    click.echo("\nTasks by Type:")
                    for task_type, count in queue_status['tasks_by_type'].items():
                        click.echo(f"  {task_type}: {count}")
                
                click.echo(f"\nNext update in {interval}s...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                break
                
        click.echo("\nMonitoring stopped.")
        
    except Exception as e:
        click.echo(f"Error during monitoring: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_type', type=click.Choice([
    'generate_course', 'generate_chapter', 'validate_quality', 
    'export_course', 'regenerate_chapter'
]))
@click.option('--complexity', help='JSON string with complexity factors')
def estimate(task_type, complexity):
    """Estimate completion time for a task type."""
    try:
        complexity_factors = None
        if complexity:
            complexity_factors = json.loads(complexity)
        
        estimate_time = estimate_completion_time(task_type, complexity_factors)
        
        click.echo(f"Estimated completion time for {task_type}: {estimate_time}")
        
        if complexity_factors:
            click.echo("Complexity factors considered:")
            for key, value in complexity_factors.items():
                click.echo(f"  {key}: {value}")
                
    except json.JSONDecodeError:
        click.echo("Invalid JSON in complexity factors", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error estimating time: {e}", err=True)
        sys.exit(1)


@cli.command()
def performance():
    """Show performance settings and recommendations."""
    try:
        settings = get_performance_settings()
        
        click.echo("=== Performance Settings ===")
        for key, value in settings.items():
            click.echo(f"{key}: {value}")
        
        click.echo("\n=== Performance Analysis ===")
        
        # Get current metrics
        queue_status = get_task_queue_status()
        
        if 'queue_capacity' in queue_status:
            capacity = queue_status['queue_capacity']
            load_pct = capacity.get('current_load_percentage', 0)
            
            if load_pct > 80:
                click.echo("⚠️  High load detected - consider scaling workers")
            elif load_pct < 20:
                click.echo("✅ Low load - system running efficiently")
            else:
                click.echo(f"📊 Normal load - {load_pct}% capacity")
        
        if 'performance_metrics' in queue_status:
            metrics = queue_status['performance_metrics']
            success_rate = metrics.get('success_rate_percentage', 0)
            
            if success_rate < 95:
                click.echo(f"⚠️  Success rate below target: {success_rate:.1f}% (target: 95%)")
            else:
                click.echo(f"✅ Success rate on target: {success_rate:.1f}%")
        
    except Exception as e:
        click.echo(f"Error getting performance info: {e}", err=True)
        sys.exit(1)


@cli.command()
def test_queue():
    """Test task queue functionality with sample tasks."""
    click.echo("Testing task queue functionality...")
    
    try:
        # Test course generation
        sample_course = {
            "id": "test-course-123",
            "title": "Test Course",
            "subject_domain": "Testing",
            "target_audience": {"proficiency_level": "beginner"},
            "learning_objectives": ["Test the task queue"],
            "estimated_duration": "PT1H",
            "difficulty_score": 1.0
        }
        
        click.echo("1. Testing course generation task...")
        task_id = task_manager.start_course_generation(sample_course)
        click.echo(f"   ✅ Created task: {task_id}")
        
        # Check status
        status = task_manager.get_task_status(task_id)
        click.echo(f"   Status: {status['status']}")
        
        # Test chapter generation
        sample_chapter = {
            "id": "test-chapter-123",
            "course_id": sample_course["id"],
            "title": "Test Chapter",
            "learning_objectives": ["Learn testing"],
            "estimated_duration": "PT30M",
            "complexity_level": 1.0
        }
        
        click.echo("2. Testing chapter generation task...")
        chapter_task_id = task_manager.start_chapter_generation(
            sample_chapter, 
            {"title": "Test Course"}
        )
        click.echo(f"   ✅ Created task: {chapter_task_id}")
        
        # Test queue status
        click.echo("3. Testing queue status...")
        queue_status = get_task_queue_status()
        click.echo(f"   Queue health: {queue_status.get('queue_health', 'unknown')}")
        
        click.echo("\n✅ All tests completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()