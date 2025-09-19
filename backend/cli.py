#!/usr/bin/env python3
"""
Main CLI entry point for the course generation platform.

Provides access to all CLI commands including database management.
"""

import sys
from pathlib import Path

import click

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from cli.db import db_cli

try:
    from cli.ai import ai
    _ai_available = True
except ImportError:
    _ai_available = False


@click.group()
@click.version_option(version="1.0.0", prog_name="Course Generation Platform CLI")
def main():
    """Course Generation Platform CLI.
    
    Comprehensive command-line interface for managing the course generation platform,
    including database operations, data seeding, and system maintenance.
    """
    pass


# Add command groups
main.add_command(db_cli)

if _ai_available:
    main.add_command(ai)


if __name__ == "__main__":
    main()