# Database CLI Guide

Comprehensive database management commands for the course generation platform.

## Installation & Setup

1. **Activate virtual environment:**
   ```bash
   cd backend
   source .venv/bin/activate
   ```

2. **Set database URL (optional):**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
   ```

## Available Commands

### Main CLI
```bash
python cli.py --help
```

### Database Commands
```bash
python cli.py db --help
```

## Command Reference

### 1. Test Database Connection
Test if the database is accessible and show PostgreSQL version:

```bash
python cli.py db test-connection
```

**With verbose details:**
```bash
python cli.py db test-connection --verbose
```

### 2. Initialize Database Schema
Create all database tables from SQLAlchemy models:

```bash
python cli.py db init-schema
```

**Drop existing tables first (caution!):**
```bash
python cli.py db init-schema --force
```

### 3. Seed Test Data
Populate database with sample data for development:

```bash
python cli.py db seed-test-data
```

**Overwrite existing data:**
```bash
python cli.py db seed-test-data --force
```

### 4. Run Migrations
Execute Alembic database migrations:

**Upgrade to latest:**
```bash
python cli.py db migrate
```

**Downgrade one version:**
```bash
python cli.py db migrate --direction=downgrade
```

### 5. Database Status
Show comprehensive database and schema information:

```bash
python cli.py db status
```

## Typical Workflows

### Development Setup
1. Test connection: `python cli.py db test-connection`
2. Initialize schema: `python cli.py db init-schema`
3. Seed test data: `python cli.py db seed-test-data`

### Production Deployment
1. Test connection: `python cli.py db test-connection`
2. Run migrations: `python cli.py db migrate`
3. Verify status: `python cli.py db status`

### Schema Updates
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review migration file in `alembic/versions/`
3. Apply migration: `python cli.py db migrate`

## Configuration

The CLI uses the following configuration priority:

1. **Environment variable:** `DATABASE_URL`
2. **Config file:** `src/core/config.py` (if available)
3. **Default fallback:** `postgresql://course_user:course_password@localhost:5432/course_platform`

## Error Handling

The CLI provides:
- ✅ Success indicators with green checkmarks
- ❌ Error indicators with red X marks
- ⚠️ Warning messages for non-critical issues
- Detailed error messages with troubleshooting hints
- Proper exit codes for scripting

## Test Data Details

The `seed-test-data` command creates:
- **1 Course:** "Introduction to Python Programming"
- **1 Chapter:** "Getting Started with Python"
- **1 Quiz:** "Python Basics Quiz" with 2 questions
- **1 Flashcard:** Python definition with spaced repetition data
- **Complete relationships** between all entities

## Migration Management

The CLI integrates with Alembic for schema versioning:
- Migrations stored in: `alembic/versions/`
- Configuration: `alembic.ini`
- Environment setup: `alembic/env.py`

## Troubleshooting

### Connection Issues
- Verify PostgreSQL is running
- Check `DATABASE_URL` format
- Ensure database exists
- Verify credentials

### Import Errors
- Activate virtual environment
- Run from `backend/` directory
- Check all dependencies installed

### Migration Failures
- Review migration files
- Check for conflicting schema changes
- Use `--direction=downgrade` to rollback

## Security Notes

- Database credentials are masked in output
- CLI falls back gracefully on configuration errors
- Connection pooling optimized for CLI usage
- No sensitive data in error messages

## Integration

The CLI can be integrated into:
- **Docker containers:** Add to Dockerfile
- **CI/CD pipelines:** Use exit codes for success/failure
- **Development scripts:** Chain commands with `&&`
- **Production deployments:** Automated migration workflows