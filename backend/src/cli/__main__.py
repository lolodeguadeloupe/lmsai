"""
Main entry point for CLI modules.

This script provides a unified entry point for all CLI tools in the system.
It allows running CLI commands directly with python -m cli.

Usage:
    python -m cli courses create --title "My Course" ...
    python -m cli courses list --status ready
    python -m cli db init
    python -m cli ai test-providers

The script automatically routes commands to the appropriate CLI module.
"""

import sys
import click
from pathlib import Path

# Add the src directory to Python path for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from cli.courses import cli as courses_cli
from cli import CLI_MODULES, __version__


@click.group()
@click.version_option(version=__version__, prog_name="LMS CLI")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx, verbose):
    """Learning Management System CLI Tools.
    
    Provides command-line interfaces for course management, database operations,
    and AI service testing.
    
    Available modules:
    - courses: Course management operations
    - db: Database management and migration  
    - ai: AI service testing and validation
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


# Add CLI modules as subcommands
main.add_command(courses_cli, name='courses')

# Note: db and ai CLI modules would be added here when implemented
# main.add_command(db_cli, name='db')
# main.add_command(ai_cli, name='ai')


@main.command()
def modules():
    """List available CLI modules and their descriptions."""
    click.echo("Available CLI modules:\n")
    for module, description in CLI_MODULES.items():
        click.echo(f"  {module:<12} {description}")
    
    click.echo("\nUsage:")
    click.echo("  python -m cli <module> <command> [options]")
    click.echo("  python -m cli courses --help")


if __name__ == "__main__":
    main()