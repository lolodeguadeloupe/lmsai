"""
Database session management and connection pooling.

Provides SQLAlchemy engine, session factory, and database utilities.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

# Database configuration from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://course_user:course_password@localhost:5432/course_platform",
)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",  # SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import shared base from models
try:
    from models.base import Base
except ImportError:
    Base = declarative_base()

# Metadata for schema operations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        from fastapi import Depends

        def get_courses(db: Session = Depends(get_db)):
            return db.query(CourseTable).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        with get_db_session() as db:
            course = db.query(CourseTable).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        from models import (
            ChapterTable,
            CourseTable,
            FlashcardTable,
            QuestionTable,
            QuizTable,
            SubchapterTable,
        )  # noqa: F401
    except ImportError:
        # Fallback for different import contexts
        import os
        import sys

        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from models import (
            ChapterTable,
            CourseTable,
            FlashcardTable,
            QuestionTable,
            QuizTable,
            SubchapterTable,
        )  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)


def reset_database():
    """Drop and recreate all tables (development only)."""
    drop_tables()
    create_tables()


class DatabaseManager:
    """Database management utilities."""

    @staticmethod
    def init_db():
        """Initialize database with tables and basic data."""
        create_tables()
        print("Database tables created successfully")

    @staticmethod
    def test_connection() -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            from sqlalchemy import text

            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    @staticmethod
    def get_engine_info() -> dict:
        """
        Get database engine information.

        Returns:
            dict: Engine configuration details
        """
        return {
            "url": str(engine.url).replace(f":{engine.url.password}@", ":***@"),
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "checked_in": engine.pool.checkedin(),
        }


# Database health check function
def health_check() -> dict:
    """
    Perform database health check.

    Returns:
        dict: Health check results
    """
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            if result == 1:
                return {
                    "status": "healthy",
                    "database": "postgresql",
                    "connection": "ok",
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "postgresql",
            "connection": "failed",
            "error": str(e),
        }

    return {"status": "unknown", "database": "postgresql", "connection": "unknown"}
