# Project Context for Qwen Code

## Project Overview

This is an AI-powered course creation platform that automatically generates comprehensive educational content adapted to the target audience's level. The platform creates courses with chapters, assessments (quizzes and flashcards), and study materials, all generated based on a specified subject and difficulty level.

### Key Features
- Automatic course structure generation with appropriate number of chapters based on difficulty level
- Adaptive content generation with vocabulary complexity matching the target audience
- Assessment generation with cognitive level distribution appropriate to the audience
- Content quality validation with readability scores and pedagogical alignment
- Multi-format export (SCORM, xAPI, QTI, PDF, HTML)
- Performance optimization for <2 minute generation time per chapter

### Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **AI Providers**: OpenAI GPT-4, Anthropic Claude
- **Vector Database**: ChromaDB/Pinecone
- **Cache**: Redis
- **Task Queue**: Celery
- **Testing**: pytest, httpx

## Project Structure

```
├── backend/                 # Python FastAPI backend
│   ├── src/                 # Source code
│   │   ├── api/             # API endpoints
│   │   ├── cli/             # Command-line interface tools
│   │   ├── core/            # Core application logic
│   │   ├── database/        # Database configuration and utilities
│   │   ├── integrations/    # External service integrations (AI, vector DB)
│   │   ├── middleware/      # Application middleware
│   │   ├── models/          # Data models and schemas
│   │   ├── repositories/    # Data access layer (planned)
│   │   ├── services/        # Business logic services
│   │   ├── tasks/           # Background tasks
│   │   └── main.py          # Application entry point
│   ├── tests/               # Automated tests
│   │   ├── contract/        # API contract tests
│   │   ├── integration/     # Integration tests
│   │   ├── performance/     # Performance tests
│   │   └── unit/            # Unit tests
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile.dev       # Development Docker configuration
├── frontend/                # React frontend
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API service clients
│   │   └── utils/           # Utility functions
│   ├── package.json         # Node.js dependencies and scripts
│   └── Dockerfile.dev       # Development Docker configuration
├── specs/                   # Project specifications
│   └── 001-plateforme-de-cr/ # Course platform feature
│       ├── contracts/       # API contracts
│       ├── data-model.md    # Data model specification
│       ├── plan.md          # Implementation plan
│       ├── quickstart.md    # Quickstart guide
│       ├── research.md      # Technical research
│       ├── spec.md          # Feature specification
│       └── tasks.md         # Implementation tasks
├── docker-compose.yml       # Docker services configuration
├── README.md                # Project documentation
└── database-connection.md   # Database connection information
```

## Current Development Status

The project is currently in Phase 3.4 of implementation, with 33/67 tasks completed (49%). The current focus is on implementing business logic services and external integrations.

### Completed Phases:
- **Phase 3.1**: Setup (project structure, dependencies, Docker configuration)
- **Phase 3.2**: Tests (contract and integration tests written and failing as expected)
- **Phase 3.3**: Core Implementation (entity models and database layer)

### Current Priority:
- **Phase 3.4**: Business Logic (T034-T040) - Services and external integrations

## Development Conventions

### Code Organization
- Follow Domain-Driven Design principles with clear separation of concerns
- Use Repository Pattern for data access (planned implementation)
- Implement services for business logic
- Apply Test-Driven Development (TDD) approach with failing tests first
- Maintain clear API contracts with OpenAPI specifications

### Testing Approach
- Contract tests for API endpoints (failing until implementation)
- Integration tests for user scenarios
- Unit tests for individual components
- Performance tests for response times and concurrent operations
- All tests should be written before implementation begins (TDD)

### Data Model
The core entities include:
- **Course**: Aggregate root with metadata and relationships
- **Chapter**: Learning units within a course
- **Subchapter**: Detailed content sections
- **Quiz**: Assessments with questions
- **Question**: Individual assessment items
- **Flashcard**: Study materials with spaced repetition
- **TargetAudience**: Learner characteristics
- **QualityMetrics**: Content quality measurements

### API Design
RESTful API following OpenAPI 3.0 specification with endpoints for:
- Course management (create, list, get, update, delete)
- Generation status monitoring
- Content regeneration
- Export functionality
- Quality metrics retrieval
- Chapter and quiz retrieval

## Building and Running

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and docker compose
- Git

### Quick Setup
1. Clone the repository
2. Configure environment variables in `.env` files
3. Start services with Docker: `docker compose up -d postgres redis chromadb`
4. Install backend dependencies: `cd backend && pip install -r requirements.txt`
5. Install frontend dependencies: `cd frontend && npm install`

### Running the Application
- **Backend**: `cd backend && python -m src.main`
- **Frontend**: `cd frontend && npm run dev`
- **Tests**: `cd backend && pytest` or `cd frontend && npm test`

### Development URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Current Implementation Tasks

The immediate priority tasks are:
1. T038: OpenAI/Anthropic AI client wrapper in backend/src/integrations/ai_client.py
2. T039: Vector database client (Pinecone/Chroma) in backend/src/integrations/vector_client.py
3. T040: Background task queue with Celery in backend/src/tasks/generation_tasks.py

These integrations can be implemented in parallel, followed by the core course generation service (T034).

## Testing and Quality Assurance

- All contract tests are written and should fail until implementation is complete
- Integration tests validate user scenarios and workflows
- Performance targets include <200ms API response time (95th percentile)
- Generation performance target is <2 minutes per chapter
- Quality metrics validation includes readability scores and pedagogical alignment

## Database Connection

PostgreSQL database with the following parameters:
- Host: localhost
- Port: 5432
- Database: course_platform
- Username: course_user
- Password: course_password

Additional tools for database management:
- DBeaver for GUI access
- pgAdmin Web UI at http://localhost:5050
- CLI psql access via Docker

## Deployment Architecture

The application uses a microservices-like architecture with:
- PostgreSQL for relational data storage
- Redis for caching and task queue management
- ChromaDB for vector embeddings and semantic search
- Celery for background task processing
- Flower for task monitoring
- Docker containers for service isolation

Services are orchestrated using Docker Compose with health checks and proper dependency management.