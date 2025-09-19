# Course Platform Backend

## Purpose
AI-powered course creation and management platform with FastAPI backend, PostgreSQL database, and Alembic migrations.

## Tech Stack
- **Framework**: FastAPI (async web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Language**: Python 3.11+
- **Containerization**: Docker for PostgreSQL

## Architecture
- `src/models/` - SQLAlchemy database models
- `src/api/v1/` - FastAPI endpoint routers
- `src/database/` - Database session management
- `src/services/` - Business logic layer
- `alembic/` - Database migration files