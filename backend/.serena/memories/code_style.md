# Code Style and Conventions

## Python Style
- **Formatter**: Black (line length 88)
- **Import sorting**: isort with black profile
- **Linting**: flake8
- **Type hints**: mypy with strict settings

## Naming Conventions
- **Functions/variables**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Files**: snake_case.py

## Code Organization
- Use type hints for all function signatures
- Async functions for FastAPI endpoints
- SQLAlchemy declarative models
- Pydantic models for request/response validation