#!/usr/bin/env python3
"""
Main CLI entry point for the course generation platform.

Usage:
    python cli_runner.py ai test-providers
    python cli_runner.py ai test-generation
    python cli_runner.py ai validate-config
    python cli_runner.py ai check-limits
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import click
from src.cli.ai import ai


@click.group()
def cli():
    """Course Generation Platform CLI."""
    pass


# Register command groups
cli.add_command(ai)


if __name__ == "__main__":
    cli()