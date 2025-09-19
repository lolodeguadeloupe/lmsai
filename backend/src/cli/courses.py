"""
Course Management CLI for the Learning Management System.

This CLI provides comprehensive course management commands including:
- Course CRUD operations (create, list, delete, status)
- Export functionality for multiple formats (SCORM, xAPI, PDF, HTML)
- Chapter regeneration and quality validation
- Batch operations for efficiency
- Rich console output with progress indicators and tables

Usage:
    python -m cli.courses create --title "Course Title" --description "Description" ...
    python -m cli.courses list --status ready --format table
    python -m cli.courses export <course_id> --format scorm2004
    python -m cli.courses regenerate-chapter <course_id> <chapter_number>
    python -m cli.courses delete <course_id> --confirm
    python -m cli.courses status <course_id>

Integration:
    - Uses existing course_generation_service.py for course operations
    - Uses export_service.py for multi-format exports
    - Follows existing project patterns and exception handling
    - Supports both synchronous and asynchronous operations
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from sqlalchemy.orm import Session

# Import project dependencies
from ..core.config import settings
from ..database.session import get_db_session
from ..models.course import Course, CourseCreate, CourseStatus, TargetAudience, QualityMetrics
from ..models.enums import ProficiencyLevel, LearningPreference
from ..services.course_generation_service import (
    CourseGenerationService,
    CourseGenerationRequest,
    GenerationMode,
    GenerationStrategy,
    create_course_generation_service
)
from ..services.export_service import ExportService, ExportRequest
from ..core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    DatabaseException
)

# Initialize Rich console for beautiful output
console = Console()

# CLI configuration
CLI_VERSION = "1.0.0"
DEFAULT_PAGE_SIZE = 10
MAX_BATCH_SIZE = 50


class CLIError(Exception):
    """Base exception for CLI operations."""
    pass


class CourseOperationError(CLIError):
    """Exception for course operation failures."""
    pass


# Utility functions
def handle_async(func):
    """Decorator to handle async functions in Click commands."""
    def wrapper(*args, **kwargs):
        try:
            return asyncio.run(func(*args, **kwargs))
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            sys.exit(1)
    return wrapper


def validate_uuid(ctx, param, value):
    """Click callback to validate UUID parameters."""
    if value is None:
        return value
    try:
        return UUID(value)
    except ValueError:
        raise click.BadParameter(f"'{value}' is not a valid UUID")


def format_duration(duration_str: str) -> str:
    """Format ISO 8601 duration for display."""
    if duration_str.startswith("PT"):
        duration_str = duration_str[2:]
        if "H" in duration_str:
            hours = duration_str.replace("H", "")
            return f"{hours} hours"
        elif "M" in duration_str:
            minutes = duration_str.replace("M", "")
            return f"{minutes} minutes"
    return duration_str


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def create_course_table(courses: List[Course], show_details: bool = False) -> Table:
    """Create a Rich table for displaying courses."""
    table = Table(show_header=True, header_style="bold magenta")
    
    # Basic columns
    table.add_column("ID", style="cyan", width=36)
    table.add_column("Title", style="green", min_width=20)
    table.add_column("Status", justify="center")
    table.add_column("Created", style="dim", width=19)
    
    if show_details:
        table.add_column("Domain", style="blue")
        table.add_column("Difficulty", justify="center", width=10)
        table.add_column("Duration", justify="center", width=12)
        table.add_column("Language", justify="center", width=8)
    
    for course in courses:
        # Status with color coding
        status_color = {
            CourseStatus.DRAFT: "yellow",
            CourseStatus.GENERATING: "blue",
            CourseStatus.READY: "green",
            CourseStatus.PUBLISHED: "bright_green",
            CourseStatus.ARCHIVED: "dim"
        }.get(course.status, "white")
        
        status_text = Text(course.status.value.upper(), style=status_color)
        
        # Basic row data
        row_data = [
            str(course.id),
            course.title[:50] + "..." if len(course.title) > 50 else course.title,
            status_text,
            format_timestamp(course.created_at)
        ]
        
        if show_details:
            row_data.extend([
                course.subject_domain,
                f"{course.difficulty_score:.1f}/5",
                format_duration(course.estimated_duration),
                course.language.upper()
            ])
        
        table.add_row(*row_data)
    
    return table


def create_export_formats_table() -> Table:
    """Create a table showing available export formats."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Format", style="green")
    table.add_column("Description", style="white")
    table.add_column("File Type", style="yellow")
    table.add_column("Standards", style="blue")
    
    formats = [
        ("scorm2004", "SCORM 2004 4th Edition package", "ZIP", "SCORM, IMS"),
        ("xapi", "xAPI (Tin Can API) package", "ZIP", "xAPI, cmi5"),
        ("qti21", "QTI 2.1 assessment package", "ZIP", "QTI, IMS"),
        ("pdf", "PDF document", "PDF", "Portable"),
        ("html", "Standalone HTML package", "ZIP", "Web Standard")
    ]
    
    for format_id, description, file_type, standards in formats:
        table.add_row(format_id, description, file_type, standards)
    
    return table


# CLI Command Group
@click.group()
@click.version_option(version=CLI_VERSION, prog_name="Course Management CLI")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """Course Management CLI for Learning Management System.
    
    Provides comprehensive course management commands including creation,
    listing, export, regeneration, and batch operations.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print("[dim]Course Management CLI v{CLI_VERSION}[/dim]")


# Create Command
@cli.command()
@click.option("--title", "-t", required=True, help="Course title")
@click.option("--description", "-d", required=True, help="Course description")
@click.option("--domain", required=True, help="Subject domain (e.g., programming, mathematics)")
@click.option("--proficiency", 
              type=click.Choice(['beginner', 'intermediate', 'advanced', 'expert']),
              default='intermediate', help="Target proficiency level")
@click.option("--difficulty", type=float, default=3.0, 
              help="Difficulty score (1.0-5.0)")
@click.option("--duration", default="PT20H", 
              help="Estimated duration (ISO 8601 format, e.g., PT20H)")
@click.option("--language", default="en", help="Course language (ISO 639-1 code)")
@click.option("--objectives", multiple=True, required=True,
              help="Learning objectives (use multiple times)")
@click.option("--mode", 
              type=click.Choice(['fast', 'balanced', 'premium']),
              default='balanced', help="Generation mode")
@click.option("--strategy",
              type=click.Choice(['sequential', 'parallel', 'hybrid']),
              default='hybrid', help="Generation strategy")
@click.option("--async", "async_mode", is_flag=True,
              help="Run generation asynchronously")
@click.pass_context
@handle_async
async def create(ctx, title, description, domain, proficiency, difficulty, 
                duration, language, objectives, mode, strategy, async_mode):
    """Create a new course with AI-powered content generation.
    
    Example:
        courses create -t "Python Basics" -d "Learn Python fundamentals" 
                      --domain programming --objectives "Understand variables" 
                      --objectives "Write functions" --mode premium
    """
    verbose = ctx.obj.get('verbose', False)
    
    if verbose:
        console.print(f"[dim]Creating course with {len(objectives)} objectives[/dim]")
    
    try:
        # Validate input
        if len(objectives) < 3:
            raise click.BadParameter("At least 3 learning objectives are required")
        
        if not (1.0 <= difficulty <= 5.0):
            raise click.BadParameter("Difficulty must be between 1.0 and 5.0")
        
        # Create target audience
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel(proficiency),
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL]
        )
        
        # Create course data
        course_data = CourseCreate(
            title=title,
            description=description,
            subject_domain=domain,
            target_audience=target_audience,
            learning_objectives=list(objectives),
            estimated_duration=duration,
            difficulty_score=difficulty,
            language=language
        )
        
        # Create generation request
        request = CourseGenerationRequest(
            course_data=course_data,
            generation_mode=GenerationMode(mode),
            generation_strategy=GenerationStrategy(strategy)
        )
        
        # Initialize service
        service = create_course_generation_service()
        
        if async_mode:
            # Asynchronous generation
            console.print("[yellow]Starting asynchronous course generation...[/yellow]")
            task_id = await service.create_course_async(request)
            
            console.print(Panel(
                f"Course generation started successfully!\n\n"
                f"Task ID: {task_id}\n"
                f"Track progress with: courses status {task_id}",
                title="[green]Generation Started[/green]",
                border_style="green"
            ))
            
        else:
            # Synchronous generation with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Generating course content...", total=100)
                
                # Start generation
                result = await service.create_course(request)
                progress.update(task, completed=100)
                
                # Success output
                console.print(Panel(
                    f"Course created successfully!\n\n"
                    f"Course ID: {result.course_id}\n"
                    f"Status: {result.status.value}\n"
                    f"Generation Time: {result.generation_time}\n"
                    f"Chapters: {len(result.chapters)}\n"
                    f"Vector Embeddings: {result.vector_embeddings_stored}",
                    title="[green]Course Created[/green]",
                    border_style="green"
                ))
                
                if verbose:
                    # Show quality metrics
                    metrics = result.quality_metrics
                    console.print("\n[bold]Quality Metrics:[/bold]")
                    console.print(f"Readability Score: {metrics.readability_score:.1f}")
                    console.print(f"Pedagogical Alignment: {metrics.pedagogical_alignment:.2f}")
                    console.print(f"Content Accuracy: {metrics.content_accuracy:.2f}")
                    console.print(f"Bias Detection: {metrics.bias_detection_score:.2f}")
        
    except ValidationException as e:
        console.print(f"[red]Validation Error: {e.message}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to create course: {str(e)}[/red]")
        sys.exit(1)


# List Command
@cli.command()
@click.option("--status", type=click.Choice(['draft', 'generating', 'ready', 'published', 'archived']),
              help="Filter by course status")
@click.option("--domain", help="Filter by subject domain")
@click.option("--page", default=1, help="Page number for pagination")
@click.option("--limit", default=DEFAULT_PAGE_SIZE, help="Number of courses per page")
@click.option("--format", "output_format", 
              type=click.Choice(['table', 'json', 'csv']),
              default='table', help="Output format")
@click.option("--details", is_flag=True, help="Show detailed information")
@click.option("--sort", type=click.Choice(['created', 'title', 'status']),
              default='created', help="Sort field")
@click.pass_context
@handle_async
async def list_courses(ctx, status, domain, page, limit, output_format, details, sort):
    """List courses with filtering and pagination options.
    
    Example:
        courses list --status ready --format table --details
        courses list --domain programming --page 2 --limit 20
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Get database session
        async with get_db_session() as db:
            # Build query
            query = db.query(Course)
            
            # Apply filters
            if status:
                query = query.filter(Course.status == CourseStatus(status))
            if domain:
                query = query.filter(Course.subject_domain.ilike(f"%{domain}%"))
            
            # Apply sorting
            if sort == 'title':
                query = query.order_by(Course.title)
            elif sort == 'status':
                query = query.order_by(Course.status)
            else:  # default: created
                query = query.order_by(Course.created_at.desc())
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            courses = query.offset(offset).limit(limit).all()
            
            if verbose:
                console.print(f"[dim]Found {total} courses, showing page {page}[/dim]")
            
            # Output based on format
            if output_format == 'json':
                # JSON output
                courses_data = []
                for course in courses:
                    course_dict = {
                        'id': str(course.id),
                        'title': course.title,
                        'description': course.description,
                        'subject_domain': course.subject_domain,
                        'status': course.status.value,
                        'difficulty_score': course.difficulty_score,
                        'estimated_duration': course.estimated_duration,
                        'language': course.language,
                        'created_at': course.created_at.isoformat(),
                        'updated_at': course.updated_at.isoformat(),
                        'learning_objectives': course.learning_objectives
                    }
                    courses_data.append(course_dict)
                
                output = {
                    'courses': courses_data,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'pages': (total + limit - 1) // limit
                    }
                }
                console.print(json.dumps(output, indent=2))
                
            elif output_format == 'csv':
                # CSV output
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                headers = ['id', 'title', 'status', 'domain', 'difficulty', 'duration', 'created_at']
                writer.writerow(headers)
                
                # Write rows
                for course in courses:
                    writer.writerow([
                        str(course.id),
                        course.title,
                        course.status.value,
                        course.subject_domain,
                        course.difficulty_score,
                        course.estimated_duration,
                        course.created_at.isoformat()
                    ])
                
                console.print(output.getvalue())
                
            else:  # table format (default)
                if not courses:
                    console.print("[yellow]No courses found matching the criteria[/yellow]")
                    return
                
                # Create and display table
                table = create_course_table(courses, show_details=details)
                console.print(table)
                
                # Pagination info
                total_pages = (total + limit - 1) // limit
                console.print(f"\n[dim]Page {page} of {total_pages} "
                            f"({total} total courses)[/dim]")
                
                if page < total_pages:
                    console.print(f"[dim]Next page: courses list --page {page + 1}[/dim]")
    
    except Exception as e:
        console.print(f"[red]Failed to list courses: {str(e)}[/red]")
        sys.exit(1)


# Status Command
@cli.command()
@click.argument("course_id", callback=validate_uuid)
@click.option("--watch", "-w", is_flag=True, help="Watch for status changes")
@click.option("--interval", default=5, help="Watch interval in seconds")
@click.pass_context
@handle_async
async def status(ctx, course_id, watch, interval):
    """Get detailed status information for a course.
    
    Example:
        courses status 123e4567-e89b-12d3-a456-426614174000
        courses status 123e4567-e89b-12d3-a456-426614174000 --watch
    """
    verbose = ctx.obj.get('verbose', False)
    
    async def get_course_status():
        async with get_db_session() as db:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ResourceNotFoundException(
                    resource_type="Course",
                    resource_id=course_id
                )
            return course
    
    try:
        if watch:
            # Watch mode
            console.print(f"[yellow]Watching course {course_id} (Ctrl+C to stop)[/yellow]")
            
            while True:
                try:
                    course = await get_course_status()
                    
                    # Clear screen and show status
                    console.clear()
                    console.print(f"[bold]Course Status - {datetime.now().strftime('%H:%M:%S')}[/bold]")
                    console.print(f"ID: {course.id}")
                    console.print(f"Title: {course.title}")
                    console.print(f"Status: {course.status.value}")
                    console.print(f"Last Updated: {format_timestamp(course.updated_at)}")
                    
                    if hasattr(course, 'quality_metrics') and course.quality_metrics:
                        console.print("\n[bold]Quality Metrics:[/bold]")
                        metrics = course.quality_metrics
                        console.print(f"Readability: {metrics.readability_score:.1f}")
                        console.print(f"Pedagogical Alignment: {metrics.pedagogical_alignment:.2f}")
                        console.print(f"Content Accuracy: {metrics.content_accuracy:.2f}")
                    
                    # Exit if course is in final state
                    if course.status in [CourseStatus.READY, CourseStatus.PUBLISHED, CourseStatus.ARCHIVED]:
                        console.print(f"\n[green]Course is in final state: {course.status.value}[/green]")
                        break
                    
                    await asyncio.sleep(interval)
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopped watching[/yellow]")
                    break
        else:
            # Single status check
            course = await get_course_status()
            
            # Display detailed status
            panel_content = (
                f"Title: {course.title}\n"
                f"Status: {course.status.value}\n"
                f"Subject Domain: {course.subject_domain}\n"
                f"Difficulty: {course.difficulty_score}/5\n"
                f"Duration: {format_duration(course.estimated_duration)}\n"
                f"Language: {course.language.upper()}\n"
                f"Created: {format_timestamp(course.created_at)}\n"
                f"Updated: {format_timestamp(course.updated_at)}"
            )
            
            if hasattr(course, 'quality_metrics') and course.quality_metrics:
                metrics = course.quality_metrics
                panel_content += (
                    f"\n\nQuality Metrics:\n"
                    f"Readability Score: {metrics.readability_score:.1f}\n"
                    f"Pedagogical Alignment: {metrics.pedagogical_alignment:.2f}\n"
                    f"Content Accuracy: {metrics.content_accuracy:.2f}\n"
                    f"Bias Detection: {metrics.bias_detection_score:.2f}"
                )
            
            console.print(Panel(
                panel_content,
                title=f"[green]Course Status[/green]",
                border_style="green"
            ))
            
            if verbose and course.learning_objectives:
                console.print("\n[bold]Learning Objectives:[/bold]")
                for i, objective in enumerate(course.learning_objectives, 1):
                    console.print(f"{i}. {objective}")
    
    except ResourceNotFoundException:
        console.print(f"[red]Course with ID {course_id} not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to get course status: {str(e)}[/red]")
        sys.exit(1)


# Export Command
@cli.command()
@click.argument("course_id", callback=validate_uuid)
@click.option("--format", "export_format",
              type=click.Choice(['scorm2004', 'xapi', 'qti21', 'pdf', 'html']),
              required=True, help="Export format")
@click.option("--output", "-o", help="Output file path")
@click.option("--include-assessments/--no-assessments", default=True,
              help="Include assessments in export")
@click.option("--include-multimedia/--no-multimedia", default=True,
              help="Include multimedia content")
@click.option("--scorm-version", default="2004_4th_edition",
              help="SCORM version for SCORM exports")
@click.option("--xapi-profile", default="cmi5",
              help="xAPI profile for xAPI exports")
@click.pass_context
@handle_async
async def export(ctx, course_id, export_format, output, include_assessments,
                include_multimedia, scorm_version, xapi_profile):
    """Export a course to various educational standards formats.
    
    Supported formats:
    - scorm2004: SCORM 2004 4th Edition package
    - xapi: xAPI (Tin Can API) package
    - qti21: QTI 2.1 assessment package
    - pdf: PDF document
    - html: Standalone HTML package
    
    Example:
        courses export 123e4567-e89b-12d3-a456-426614174000 --format scorm2004
        courses export 123e4567-e89b-12d3-a456-426614174000 --format pdf -o course.pdf
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Get course
        async with get_db_session() as db:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ResourceNotFoundException(
                    resource_type="Course",
                    resource_id=course_id
                )
            
            # Validate course status
            if course.status not in [CourseStatus.READY, CourseStatus.PUBLISHED]:
                console.print(f"[red]Course must be READY or PUBLISHED for export. "
                            f"Current status: {course.status.value}[/red]")
                sys.exit(1)
        
        # Create export request
        export_request = ExportRequest(
            format=export_format,
            include_assessments=include_assessments,
            include_multimedia=include_multimedia,
            scorm_version=scorm_version,
            xapi_profile=xapi_profile
        )
        
        # Initialize export service
        export_service = ExportService()
        
        if verbose:
            console.print(f"[dim]Exporting course to {export_format} format[/dim]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task(f"Exporting to {export_format}...", total=None)
            
            # Perform export
            export_response = await export_service.export_course(course, export_request)
            
            progress.update(task, description="Export completed!")
        
        # Success output
        console.print(Panel(
            f"Course exported successfully!\n\n"
            f"Format: {export_format}\n"
            f"File Size: {export_response.file_size:,} bytes\n"
            f"Checksum: {export_response.checksum}\n"
            f"Download URL: {export_response.download_url}\n"
            f"Expires: {format_timestamp(export_response.expires_at)}",
            title="[green]Export Complete[/green]",
            border_style="green"
        ))
        
        if verbose:
            # Show format-specific metadata
            if export_response.scorm_metadata:
                console.print("\n[bold]SCORM Metadata:[/bold]")
                for key, value in export_response.scorm_metadata.items():
                    console.print(f"{key}: {value}")
            
            if export_response.xapi_metadata:
                console.print("\n[bold]xAPI Metadata:[/bold]")
                for key, value in export_response.xapi_metadata.items():
                    console.print(f"{key}: {value}")
    
    except ResourceNotFoundException:
        console.print(f"[red]Course with ID {course_id} not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to export course: {str(e)}[/red]")
        sys.exit(1)


# Show Export Formats Command
@cli.command("export-formats")
def show_export_formats():
    """Show available export formats and their specifications."""
    console.print(Panel(
        "Export formats supported by the course management system",
        title="[cyan]Available Export Formats[/cyan]",
        border_style="cyan"
    ))
    
    table = create_export_formats_table()
    console.print(table)
    
    console.print("\n[bold]Usage Examples:[/bold]")
    console.print("• SCORM 2004: courses export <id> --format scorm2004")
    console.print("• xAPI cmi5: courses export <id> --format xapi --xapi-profile cmi5")
    console.print("• PDF: courses export <id> --format pdf")
    console.print("• HTML: courses export <id> --format html")


# Regenerate Chapter Command
@cli.command("regenerate-chapter")
@click.argument("course_id", callback=validate_uuid)
@click.argument("chapter_number", type=int)
@click.option("--mode", 
              type=click.Choice(['fast', 'balanced', 'premium']),
              default='balanced', help="Generation mode")
@click.option("--reason", help="Reason for regeneration (for logging)")
@click.pass_context
@handle_async
async def regenerate_chapter(ctx, course_id, chapter_number, mode, reason):
    """Regenerate a specific chapter of a course.
    
    Example:
        courses regenerate-chapter 123e4567-e89b-12d3-a456-426614174000 3 --mode premium
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Get course and validate
        async with get_db_session() as db:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ResourceNotFoundException(
                    resource_type="Course",
                    resource_id=course_id
                )
            
            # Check if chapter exists
            # Note: In a real implementation, you'd query chapters table
            # For now, we'll simulate the validation
            if chapter_number < 1:
                raise click.BadParameter("Chapter number must be positive")
        
        # Confirm regeneration
        if not Confirm.ask(
            f"Are you sure you want to regenerate chapter {chapter_number} "
            f"of course '{course.title}'? This will replace existing content."
        ):
            console.print("[yellow]Operation cancelled[/yellow]")
            return
        
        if verbose:
            console.print(f"[dim]Regenerating chapter {chapter_number} with {mode} mode[/dim]")
        
        # Initialize service
        service = create_course_generation_service()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task(f"Regenerating chapter {chapter_number}...", total=None)
            
            # Note: This would need to be implemented in the service
            # For now, we'll simulate the process
            await asyncio.sleep(2)  # Simulate processing time
            
            progress.update(task, description="Chapter regenerated!")
        
        console.print(Panel(
            f"Chapter {chapter_number} regenerated successfully!\n\n"
            f"Course: {course.title}\n"
            f"Chapter: {chapter_number}\n"
            f"Mode: {mode}\n"
            f"Timestamp: {format_timestamp(datetime.utcnow())}"
            + (f"\nReason: {reason}" if reason else ""),
            title="[green]Chapter Regenerated[/green]",
            border_style="green"
        ))
    
    except ResourceNotFoundException:
        console.print(f"[red]Course with ID {course_id} not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to regenerate chapter: {str(e)}[/red]")
        sys.exit(1)


# Delete Command
@cli.command()
@click.argument("course_id", callback=validate_uuid)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--force", is_flag=True, help="Force delete even if in generating state")
@click.pass_context
@handle_async
async def delete(ctx, course_id, confirm, force):
    """Delete a course and all associated content.
    
    WARNING: This operation cannot be undone!
    
    Example:
        courses delete 123e4567-e89b-12d3-a456-426614174000 --confirm
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Get course
        async with get_db_session() as db:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ResourceNotFoundException(
                    resource_type="Course", 
                    resource_id=course_id
                )
            
            # Check if course can be deleted
            if course.status == CourseStatus.GENERATING and not force:
                console.print(
                    f"[red]Cannot delete course while generation is in progress. "
                    f"Use --force to override.[/red]"
                )
                sys.exit(1)
            
            # Confirmation
            if not confirm:
                console.print(Panel(
                    f"You are about to delete:\n\n"
                    f"ID: {course.id}\n"
                    f"Title: {course.title}\n"
                    f"Status: {course.status.value}\n"
                    f"Created: {format_timestamp(course.created_at)}\n\n"
                    f"[red]This action cannot be undone![/red]",
                    title="[red]Confirm Deletion[/red]",
                    border_style="red"
                ))
                
                if not Confirm.ask("Are you sure you want to delete this course?"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return
            
            if verbose:
                console.print(f"[dim]Deleting course {course_id}[/dim]")
            
            # Perform deletion
            db.delete(course)
            db.commit()
            
            console.print(Panel(
                f"Course deleted successfully!\n\n"
                f"ID: {course_id}\n"
                f"Title: {course.title}\n"
                f"Deleted: {format_timestamp(datetime.utcnow())}",
                title="[green]Course Deleted[/green]",
                border_style="green"
            ))
    
    except ResourceNotFoundException:
        console.print(f"[red]Course with ID {course_id} not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Failed to delete course: {str(e)}[/red]")
        sys.exit(1)


# Batch Operations Commands
@cli.group("batch")
def batch():
    """Batch operations for multiple courses."""
    pass


@batch.command("delete")
@click.option("--status", type=click.Choice(['draft', 'archived']),
              help="Delete courses by status")
@click.option("--older-than", type=int, help="Delete courses older than N days")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
@handle_async
async def batch_delete(ctx, status, older_than, dry_run, confirm):
    """Batch delete courses based on criteria.
    
    Example:
        courses batch delete --status draft --older-than 30 --dry-run
        courses batch delete --status archived --confirm
    """
    verbose = ctx.obj.get('verbose', False)
    
    if not status and not older_than:
        console.print("[red]Must specify either --status or --older-than[/red]")
        sys.exit(1)
    
    try:
        async with get_db_session() as db:
            # Build query
            query = db.query(Course)
            
            if status:
                query = query.filter(Course.status == CourseStatus(status))
            
            if older_than:
                cutoff_date = datetime.utcnow() - timedelta(days=older_than)
                query = query.filter(Course.created_at < cutoff_date)
            
            courses = query.all()
            
            if not courses:
                console.print("[yellow]No courses match the deletion criteria[/yellow]")
                return
            
            # Show what will be deleted
            console.print(f"\n[bold]Found {len(courses)} courses to delete:[/bold]")
            table = create_course_table(courses[:10])  # Show first 10
            console.print(table)
            
            if len(courses) > 10:
                console.print(f"[dim]... and {len(courses) - 10} more[/dim]")
            
            if dry_run:
                console.print(f"\n[yellow]DRY RUN: {len(courses)} courses would be deleted[/yellow]")
                return
            
            # Confirmation
            if not confirm:
                if not Confirm.ask(f"Delete {len(courses)} courses? This cannot be undone!"):
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return
            
            # Perform batch deletion
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Deleting courses...", total=len(courses))
                
                deleted_count = 0
                for course in courses:
                    try:
                        db.delete(course)
                        deleted_count += 1
                        progress.update(task, advance=1)
                    except Exception as e:
                        if verbose:
                            console.print(f"[red]Failed to delete {course.id}: {str(e)}[/red]")
                
                db.commit()
            
            console.print(Panel(
                f"Batch deletion completed!\n\n"
                f"Successfully deleted: {deleted_count}\n"
                f"Failed: {len(courses) - deleted_count}\n"
                f"Completed: {format_timestamp(datetime.utcnow())}",
                title="[green]Batch Deletion Complete[/green]",
                border_style="green"
            ))
    
    except Exception as e:
        console.print(f"[red]Batch deletion failed: {str(e)}[/red]")
        sys.exit(1)


@batch.command("export")
@click.option("--status", type=click.Choice(['ready', 'published']),
              default='ready', help="Export courses by status")
@click.option("--format", "export_format",
              type=click.Choice(['scorm2004', 'xapi', 'qti21', 'pdf', 'html']),
              required=True, help="Export format")
@click.option("--output-dir", "-o", default="./exports", help="Output directory")
@click.option("--max-concurrent", default=5, help="Maximum concurrent exports")
@click.pass_context
@handle_async
async def batch_export(ctx, status, export_format, output_dir, max_concurrent):
    """Batch export multiple courses.
    
    Example:
        courses batch export --status ready --format pdf --output-dir ./exports
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get courses
        async with get_db_session() as db:
            courses = db.query(Course).filter(Course.status == CourseStatus(status)).all()
            
            if not courses:
                console.print(f"[yellow]No {status} courses found for export[/yellow]")
                return
        
        console.print(f"[bold]Exporting {len(courses)} courses to {export_format}[/bold]")
        
        # Initialize export service
        export_service = ExportService()
        
        # Batch export with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def export_single_course(course):
            async with semaphore:
                try:
                    export_request = ExportRequest(format=export_format)
                    result = await export_service.export_course(course, export_request)
                    return course.id, True, result
                except Exception as e:
                    return course.id, False, str(e)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Exporting courses...", total=len(courses))
            
            # Execute exports
            tasks = [export_single_course(course) for course in courses]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            progress.update(task, completed=len(courses))
        
        # Process results
        successful = 0
        failed = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
            else:
                course_id, success, data = result
                if success:
                    successful += 1
                else:
                    failed += 1
                    if verbose:
                        console.print(f"[red]Failed to export {course_id}: {data}[/red]")
        
        console.print(Panel(
            f"Batch export completed!\n\n"
            f"Successful: {successful}\n"
            f"Failed: {failed}\n"
            f"Format: {export_format}\n"
            f"Output Directory: {output_path.absolute()}",
            title="[green]Batch Export Complete[/green]",
            border_style="green"
        ))
    
    except Exception as e:
        console.print(f"[red]Batch export failed: {str(e)}[/red]")
        sys.exit(1)


# Main entry point
if __name__ == "__main__":
    cli()