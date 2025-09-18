"""
Database module for the course generation platform.

Provides database session management and utilities.
"""

from .session import (
    Base,
    DatabaseManager,
    SessionLocal,
    create_tables,
    drop_tables,
    engine,
    get_db,
    get_db_session,
    health_check,
    metadata,
    reset_database,
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "metadata",
    "get_db",
    "get_db_session",
    "create_tables",
    "drop_tables",
    "reset_database",
    "DatabaseManager",
    "health_check",
]
