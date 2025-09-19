# Suggested Commands

## Development
```bash
# Start development server
cd src && python main.py
# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start PostgreSQL
docker compose up -d postgres
```

## Database
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check migration status
alembic current
```

## Testing
```bash
# Run all tests
python test_final.py

# Test database only
python test_database.py

# Test API
python test_api_simple.py
```

## Code Quality
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/

# Type checking
mypy src/
```