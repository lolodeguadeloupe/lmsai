#!/usr/bin/env python3
"""
Example CLI Usage for Course Management.

This script demonstrates how to use the course management CLI
with practical examples and common operations.

Run this script to see example CLI commands and their output.
"""

import subprocess
import sys
from pathlib import Path

def run_cli_command(command, description=""):
    """Run a CLI command and display the result."""
    print(f"\n{'='*60}")
    if description:
        print(f"EXAMPLE: {description}")
    print(f"COMMAND: {command}")
    print(f"{'='*60}")
    
    try:
        # Note: In a real environment, these would actually execute
        # For demonstration, we'll show what the commands would do
        print(f"[DEMO] Would execute: {command}")
        print("[DEMO] This is a demonstration - actual CLI requires database setup")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Demonstrate CLI usage with examples."""
    
    print("Course Management CLI - Usage Examples")
    print("=====================================")
    print("This demonstrates the course management CLI functionality.")
    print("Note: Actual execution requires database setup and configuration.")
    
    # Basic CLI help
    run_cli_command(
        "python -m cli.courses --help",
        "Show available course management commands"
    )
    
    # Create a course
    run_cli_command(
        'python -m cli.courses create '
        '--title "Introduction to Python Programming" '
        '--description "Learn Python fundamentals step by step" '
        '--domain programming '
        '--proficiency beginner '
        '--difficulty 2.0 '
        '--duration PT25H '
        '--objectives "Understand Python syntax" '
        '--objectives "Write simple programs" '
        '--objectives "Use variables and functions" '
        '--mode balanced',
        "Create a new Python programming course"
    )
    
    # List courses
    run_cli_command(
        "python -m cli.courses list --status ready --format table --details",
        "List all ready courses with detailed information"
    )
    
    # Check course status
    run_cli_command(
        "python -m cli.courses status 123e4567-e89b-12d3-a456-426614174000",
        "Check the status of a specific course"
    )
    
    # Export to different formats
    run_cli_command(
        "python -m cli.courses export 123e4567-e89b-12d3-a456-426614174000 --format scorm2004",
        "Export course as SCORM 2004 package"
    )
    
    run_cli_command(
        "python -m cli.courses export 123e4567-e89b-12d3-a456-426614174000 --format pdf",
        "Export course as PDF document"
    )
    
    # Show export formats
    run_cli_command(
        "python -m cli.courses export-formats",
        "Show all available export formats"
    )
    
    # Regenerate a chapter
    run_cli_command(
        "python -m cli.courses regenerate-chapter 123e4567-e89b-12d3-a456-426614174000 3 --mode premium",
        "Regenerate chapter 3 with premium quality"
    )
    
    # Batch operations
    run_cli_command(
        "python -m cli.courses batch delete --status draft --older-than 30 --dry-run",
        "Show what draft courses older than 30 days would be deleted (dry run)"
    )
    
    run_cli_command(
        "python -m cli.courses batch export --status ready --format pdf --output-dir ./exports",
        "Batch export all ready courses to PDF format"
    )
    
    # Advanced filtering
    run_cli_command(
        "python -m cli.courses list --domain programming --format json --page 2 --limit 5",
        "List programming courses in JSON format with pagination"
    )
    
    # Watch mode
    run_cli_command(
        "python -m cli.courses status 123e4567-e89b-12d3-a456-426614174000 --watch",
        "Watch course status changes in real-time"
    )
    
    print(f"\n{'='*60}")
    print("CLI FEATURES SUMMARY")
    print(f"{'='*60}")
    
    features = [
        "✓ Course creation with AI-powered content generation",
        "✓ Comprehensive course listing with filtering and pagination",
        "✓ Multiple export formats (SCORM, xAPI, QTI, PDF, HTML)",
        "✓ Real-time status monitoring with watch mode",
        "✓ Chapter regeneration for content improvement",
        "✓ Batch operations for efficiency",
        "✓ Rich console output with tables and progress bars",
        "✓ JSON and CSV output formats for automation",
        "✓ Safety features with confirmation prompts",
        "✓ Comprehensive error handling and validation"
    ]
    
    for feature in features:
        print(feature)
    
    print(f"\n{'='*60}")
    print("GETTING STARTED")
    print(f"{'='*60}")
    print("1. Ensure database is set up and configured")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Set environment variables for database connection")
    print("4. Run: python -m cli.courses --help")
    print("5. Create your first course with the 'create' command")
    
    print(f"\n{'='*60}")
    print("INTEGRATION WITH EXISTING SERVICES")
    print(f"{'='*60}")
    print("• Uses CourseGenerationService for AI-powered content creation")
    print("• Integrates with ExportService for multi-format exports")
    print("• Follows existing project patterns and exception handling")
    print("• Supports both synchronous and asynchronous operations")
    print("• Works with the existing database models and schema")


if __name__ == "__main__":
    main()