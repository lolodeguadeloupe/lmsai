"""
Test configuration and fixtures.
Common setup for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import will fail until implementation - this is expected for TDD
try:
    from src.database import Base, get_db
    from src.main import app
except ImportError:
    # Expected during TDD phase - tests should fail until implementation
    app = None
    get_db = None
    Base = None

# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def test_engine():
    """Create test database engine."""
    if Base is None:
        pytest.skip("Database models not implemented yet")

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_db_session(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_db_session):
    """Create test client with dependency override."""
    if app is None:
        pytest.skip("FastAPI app not implemented yet")

    def override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_course_request():
    """Sample course creation request data."""
    return {
        "title": "Introduction to Machine Learning",
        "description": "Comprehensive ML course for beginners",
        "subject_domain": "Computer Science",
        "target_audience": {
            "proficiency_level": "beginner",
            "prerequisites": ["Basic mathematics", "Python programming"],
            "learning_preferences": ["visual", "practical"],
        },
        "estimated_duration": "PT20H",
        "content_preferences": {
            "include_practical_examples": True,
            "theory_to_practice_ratio": 0.6,
        },
    }


@pytest.fixture
def sample_course_id():
    """Sample course UUID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"
