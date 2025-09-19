#!/usr/bin/env python3
"""
Database CLI commands for the course generation platform.

Provides comprehensive database management capabilities including schema initialization,
data seeding, migrations, and connection testing.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

import click
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

try:
    # Try to import configuration, but provide fallback
    try:
        from core.config import settings
        DATABASE_URL = settings.DATABASE_URL
    except Exception as e:
        # Fallback to environment variable if config fails
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://course_user:course_password@localhost:5432/course_platform")
        click.echo(f"Warning: Could not load config, using fallback DATABASE_URL: {e}", err=True)
    
    from database.session import SessionLocal, Base, DatabaseManager
    from models import (
        CourseTable,
        ChapterTable, 
        SubchapterTable,
        QuizTable,
        QuestionTable,
        FlashcardTable,
        CourseStatus,
        QuizType,
        QuestionType,
        DifficultyLevel,
        ProficiencyLevel,
        LearningPreference,
    )
    
    # Create our own engine for CLI operations
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    )
    
except ImportError as e:
    click.echo(f"Error importing modules: {e}", err=True)
    click.echo("Make sure you're running from the correct directory and all dependencies are installed", err=True)
    sys.exit(1)


class DatabaseCLI:
    """Database management CLI operations."""
    
    def __init__(self):
        """Initialize database CLI with configuration."""
        self.database_url = DATABASE_URL
        self.engine = engine
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test database connection and return status.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT version()")).scalar()
                if result:
                    return True, f"Connected successfully. PostgreSQL version: {result.split(',')[0]}"
                return False, "Connection test failed - no response"
        except SQLAlchemyError as e:
            return False, f"Database connection failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get current database schema information.
        
        Returns:
            dict: Schema information including tables and columns
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            schema_info = {
                "database_url": str(self.engine.url).replace(f":{self.engine.url.password}@", ":***@"),
                "total_tables": len(tables),
                "tables": {}
            }
            
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                schema_info["tables"][table_name] = {
                    "columns": len(columns),
                    "column_details": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"],
                            "primary_key": col.get("primary_key", False)
                        }
                        for col in columns
                    ],
                    "indexes": len(indexes),
                    "foreign_keys": len(foreign_keys)
                }
            
            return schema_info
        except Exception as e:
            return {"error": f"Failed to get schema info: {str(e)}"}
    
    def create_schema(self, drop_existing: bool = False) -> tuple[bool, str]:
        """
        Create database schema from SQLAlchemy models.
        
        Args:
            drop_existing: Whether to drop existing tables first
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if drop_existing:
                click.echo("Dropping existing tables...")
                Base.metadata.drop_all(bind=self.engine)
                click.echo("Existing tables dropped.")
            
            click.echo("Creating database schema...")
            Base.metadata.create_all(bind=self.engine)
            
            # Verify tables were created
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            expected_tables = {
                "courses", "chapters", "subchapters", 
                "quizzes", "questions", "flashcards"
            }
            created_tables = set(tables)
            
            if expected_tables.issubset(created_tables):
                return True, f"Schema created successfully. Tables: {', '.join(sorted(created_tables))}"
            else:
                missing = expected_tables - created_tables
                return False, f"Schema creation incomplete. Missing tables: {', '.join(missing)}"
                
        except SQLAlchemyError as e:
            return False, f"Schema creation failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error during schema creation: {str(e)}"
    
    def seed_test_data(self) -> tuple[bool, str]:
        """
        Seed database with test data for development.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            with SessionLocal() as db:
                # Check if data already exists
                existing_courses = db.query(CourseTable).count()
                if existing_courses > 0:
                    return False, f"Database already contains {existing_courses} courses. Use --force to overwrite."
                
                # Create sample course
                sample_course = CourseTable(
                    title="Introduction to Python Programming",
                    description="A comprehensive introduction to Python programming for beginners",
                    subject_domain="Programming",
                    learning_objectives=[
                        "Understand Python syntax and basic programming concepts",
                        "Write simple Python programs",
                        "Use variables, data types, and control structures",
                        "Work with functions and modules"
                    ],
                    estimated_duration="PT40H",  # ISO 8601: 40 hours
                    difficulty_score=3.5,
                    language="en",
                    version="1.0.0",
                    status=CourseStatus.PUBLISHED,
                    target_audience={
                        "proficiency_level": ProficiencyLevel.BEGINNER.value,
                        "learning_preferences": [LearningPreference.VISUAL.value, LearningPreference.HANDS_ON.value],
                        "prerequisites": ["Basic computer literacy"],
                        "time_commitment": "5-10 hours per week"
                    },
                    quality_metrics={
                        "content_depth": 85.0,
                        "engagement_level": 78.0,
                        "difficulty_balance": 82.0,
                        "learning_progression": 88.0
                    }
                )
                
                db.add(sample_course)
                db.flush()  # Get the course ID
                
                # Create sample chapter
                sample_chapter = ChapterTable(
                    course_id=sample_course.id,
                    title="Getting Started with Python",
                    description="Learn the basics of Python programming",
                    chapter_number=1,
                    learning_objectives=[
                        "Install Python and set up development environment",
                        "Write your first Python program",
                        "Understand Python REPL"
                    ],
                    estimated_duration="PT4H",
                    content_blocks=[
                        {
                            "type": "text",
                            "content": "Python is a high-level, interpreted programming language...",
                            "metadata": {"word_count": 150}
                        },
                        {
                            "type": "code",
                            "content": "print('Hello, World!')",
                            "metadata": {"language": "python", "executable": True}
                        }
                    ],
                    resources=[
                        {
                            "title": "Python Official Documentation",
                            "url": "https://docs.python.org/3/",
                            "type": "documentation"
                        }
                    ],
                    examples=[
                        {
                            "title": "Hello World Example",
                            "code": "print('Hello, World!')",
                            "explanation": "This is the traditional first program in Python"
                        }
                    ]
                )
                
                db.add(sample_chapter)
                db.flush()
                
                # Create sample quiz
                sample_quiz = QuizTable(
                    chapter_id=sample_chapter.id,
                    title="Python Basics Quiz",
                    description="Test your understanding of Python basics",
                    quiz_type=QuizType.KNOWLEDGE_CHECK,
                    time_limit_minutes=15,
                    passing_score=70.0,
                    randomize_questions=True,
                    max_attempts=3
                )
                
                db.add(sample_quiz)
                db.flush()
                
                # Create sample questions
                sample_questions = [
                    QuestionTable(
                        quiz_id=sample_quiz.id,
                        question_text="What does the print() function do in Python?",
                        question_type=QuestionType.MULTIPLE_CHOICE,
                        correct_answer="Outputs text to the console",
                        options=[
                            "Outputs text to the console",
                            "Reads input from the user",
                            "Performs mathematical calculations",
                            "Creates a new variable"
                        ],
                        explanation="The print() function outputs text or other values to the console/terminal.",
                        difficulty_level=DifficultyLevel.BEGINNER,
                        points=5
                    ),
                    QuestionTable(
                        quiz_id=sample_quiz.id,
                        question_text="Which of the following is a valid Python variable name?",
                        question_type=QuestionType.MULTIPLE_CHOICE,
                        correct_answer="my_variable",
                        options=[
                            "2variable",
                            "my-variable",
                            "my_variable",
                            "my variable"
                        ],
                        explanation="Python variable names must start with a letter or underscore, and can contain letters, numbers, and underscores.",
                        difficulty_level=DifficultyLevel.BEGINNER,
                        points=5
                    )
                ]
                
                for question in sample_questions:
                    db.add(question)
                
                # Create sample flashcard
                sample_flashcard = FlashcardTable(
                    chapter_id=sample_chapter.id,
                    front="What is Python?",
                    back="Python is a high-level, interpreted programming language known for its simplicity and readability.",
                    difficulty_level=DifficultyLevel.BEGINNER,
                    tags=["python", "basics", "programming"],
                    spaced_repetition_data={
                        "ease_factor": 2.5,
                        "interval_days": 1,
                        "repetitions": 0,
                        "next_review": (datetime.utcnow() + timedelta(days=1)).isoformat()
                    }
                )
                
                db.add(sample_flashcard)
                db.commit()
                
                # Count created records
                courses_count = db.query(CourseTable).count()
                chapters_count = db.query(ChapterTable).count()
                quizzes_count = db.query(QuizTable).count()
                questions_count = db.query(QuestionTable).count()
                flashcards_count = db.query(FlashcardTable).count()
                
                return True, (
                    f"Test data seeded successfully!\n"
                    f"Created: {courses_count} courses, {chapters_count} chapters, "
                    f"{quizzes_count} quizzes, {questions_count} questions, {flashcards_count} flashcards"
                )
                
        except SQLAlchemyError as e:
            return False, f"Failed to seed test data: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error during seeding: {str(e)}"
    
    def run_migrations(self, direction: str = "upgrade") -> tuple[bool, str]:
        """
        Run Alembic database migrations.
        
        Args:
            direction: Migration direction ("upgrade" or "downgrade")
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Change to backend directory for alembic commands
            backend_dir = Path(__file__).parent.parent.parent
            
            if direction == "upgrade":
                cmd = ["alembic", "upgrade", "head"]
            elif direction == "downgrade":
                cmd = ["alembic", "downgrade", "-1"]
            else:
                return False, f"Invalid direction: {direction}. Use 'upgrade' or 'downgrade'."
            
            result = subprocess.run(
                cmd,
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Migration {direction} completed successfully.\n{result.stdout}"
            else:
                return False, f"Migration {direction} failed.\nError: {result.stderr}"
                
        except FileNotFoundError:
            return False, "Alembic not found. Make sure it's installed and in PATH."
        except Exception as e:
            return False, f"Unexpected error during migration: {str(e)}"


# CLI Group and Commands
@click.group(name="db")
@click.pass_context
def db_cli(ctx):
    """Database management commands."""
    ctx.ensure_object(dict)
    ctx.obj['db_manager'] = DatabaseCLI()


@db_cli.command()
@click.option('--force', is_flag=True, help='Drop existing tables before creating schema')
@click.pass_context
def init_schema(ctx, force):
    """Initialize database schema from SQLAlchemy models."""
    db_manager = ctx.obj['db_manager']
    
    click.echo("Initializing database schema...")
    
    # Test connection first
    success, message = db_manager.test_connection()
    if not success:
        click.echo(f"❌ {message}", err=True)
        sys.exit(1)
    
    # Create schema
    success, message = db_manager.create_schema(drop_existing=force)
    
    if success:
        click.echo(f"✅ {message}")
    else:
        click.echo(f"❌ {message}", err=True)
        sys.exit(1)


@db_cli.command()
@click.option('--force', is_flag=True, help='Overwrite existing test data')
@click.pass_context
def seed_test_data(ctx, force):
    """Seed database with test data for development."""
    db_manager = ctx.obj['db_manager']
    
    click.echo("Seeding test data...")
    
    # Test connection first
    success, message = db_manager.test_connection()
    if not success:
        click.echo(f"❌ {message}", err=True)
        sys.exit(1)
    
    # Clear existing data if force flag is used
    if force:
        try:
            with SessionLocal() as db:
                # Delete in reverse order of dependencies
                db.query(FlashcardTable).delete()
                db.query(QuestionTable).delete()
                db.query(QuizTable).delete()
                db.query(SubchapterTable).delete()
                db.query(ChapterTable).delete()
                db.query(CourseTable).delete()
                db.commit()
                click.echo("Existing test data cleared.")
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not clear existing data: {e}")
    
    # Seed data
    success, message = db_manager.seed_test_data()
    
    if success:
        click.echo(f"✅ {message}")
    else:
        click.echo(f"❌ {message}", err=True)
        if not force:
            click.echo("Tip: Use --force to overwrite existing data")
        sys.exit(1)


@db_cli.command()
@click.option('--direction', type=click.Choice(['upgrade', 'downgrade']), default='upgrade',
              help='Migration direction (default: upgrade)')
@click.pass_context
def migrate(ctx, direction):
    """Run database migrations using Alembic."""
    db_manager = ctx.obj['db_manager']
    
    click.echo(f"Running migration {direction}...")
    
    success, message = db_manager.run_migrations(direction)
    
    if success:
        click.echo(f"✅ {message}")
    else:
        click.echo(f"❌ {message}", err=True)
        sys.exit(1)


@db_cli.command()
@click.option('--verbose', is_flag=True, help='Show detailed connection information')
@click.pass_context
def test_connection(ctx, verbose):
    """Test database connection and show status."""
    db_manager = ctx.obj['db_manager']
    
    click.echo("Testing database connection...")
    
    success, message = db_manager.test_connection()
    
    if success:
        click.echo(f"✅ {message}")
        
        if verbose:
            try:
                # Show additional connection details
                engine_info = DatabaseManager.get_engine_info()
                click.echo("\n📊 Connection Details:")
                click.echo(f"   Database URL: {engine_info['url']}")
                click.echo(f"   Pool Size: {engine_info['pool_size']}")
                click.echo(f"   Checked Out: {engine_info['checked_out']}")
                click.echo(f"   Checked In: {engine_info['checked_in']}")
                click.echo(f"   Overflow: {engine_info['overflow']}")
                
                # Show schema information
                schema_info = db_manager.get_schema_info()
                if "error" not in schema_info:
                    click.echo(f"\n📋 Schema Information:")
                    click.echo(f"   Total Tables: {schema_info['total_tables']}")
                    for table_name, table_info in schema_info['tables'].items():
                        click.echo(f"   • {table_name}: {table_info['columns']} columns, "
                                 f"{table_info['indexes']} indexes, {table_info['foreign_keys']} foreign keys")
                
            except Exception as e:
                click.echo(f"⚠️  Could not fetch detailed information: {e}")
    else:
        click.echo(f"❌ {message}", err=True)
        sys.exit(1)


@db_cli.command()
@click.pass_context
def status(ctx):
    """Show database status and schema information."""
    db_manager = ctx.obj['db_manager']
    
    # Test connection
    success, message = db_manager.test_connection()
    click.echo(f"Connection: {'✅' if success else '❌'} {message}")
    
    if not success:
        sys.exit(1)
    
    # Show schema information
    schema_info = db_manager.get_schema_info()
    
    if "error" in schema_info:
        click.echo(f"❌ {schema_info['error']}", err=True)
        sys.exit(1)
    
    click.echo(f"\n📋 Database Status:")
    click.echo(f"   Database URL: {schema_info['database_url']}")
    click.echo(f"   Total Tables: {schema_info['total_tables']}")
    
    if schema_info['tables']:
        click.echo("\n📊 Tables:")
        for table_name, table_info in schema_info['tables'].items():
            click.echo(f"   • {table_name}")
            click.echo(f"     - Columns: {table_info['columns']}")
            click.echo(f"     - Indexes: {table_info['indexes']}")
            click.echo(f"     - Foreign Keys: {table_info['foreign_keys']}")
    else:
        click.echo("   No tables found. Run 'db init-schema' to create schema.")


if __name__ == "__main__":
    db_cli()