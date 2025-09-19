#!/usr/bin/env python3
"""
API complète avec persistance réelle en base de données PostgreSQL
"""

import sys
import os
from pathlib import Path

# Add src to Python path for absolute imports
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import enum

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://course_user:course_password@localhost:5432/course_platform')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class DifficultyLevel(str, enum.Enum):
    BEGINNER = "Débutant"
    INTERMEDIATE = "Intermédiaire"
    ADVANCED = "Avancé"

class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    PUBLISHED = "published"

# Database Models
class CourseTable(Base):
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    subject_domain = Column(String(100), nullable=False)
    target_audience = Column(String(100), nullable=False)
    difficulty_level = Column(String(50), nullable=False)
    estimated_duration_hours = Column(Integer, nullable=False)
    status = Column(String(50), default=CourseStatus.DRAFT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Course Generation Platform API",
    description="AI-powered course creation and management platform - With Database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class CourseCreationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    subject_domain: str = Field(..., min_length=1, max_length=100)
    target_audience: str = Field(..., min_length=1, max_length=100)
    difficulty_level: str = Field(..., pattern="^(Débutant|Intermédiaire|Avancé)$")
    estimated_duration_hours: int = Field(..., ge=1, le=1000)

class CourseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    subject_domain: str
    target_audience: str
    difficulty_level: str
    estimated_duration_hours: int
    status: str
    created_at: datetime
    updated_at: datetime

class CourseCreationResponse(BaseModel):
    message: str
    course_id: str
    status: str = "created"

class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    pagination: Dict[str, Any]

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "Course Generation Platform API - With Real Database",
        "version": "1.0.0",
        "documentation": "/docs",
        "database": "PostgreSQL with real persistence"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        result = db.execute(text("SELECT version()"))
        db_version = result.fetchone()[0]
        
        # Count courses
        course_count = db.execute(text("SELECT COUNT(*) FROM courses")).fetchone()[0]
        
        return {
            "status": "healthy",
            "service": "course-platform-api",
            "database": "connected",
            "db_version": db_version[:50] + "..." if len(db_version) > 50 else db_version,
            "total_courses": course_count
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "course-platform-api",
            "database": "disconnected",
            "error": str(e)
        }

@app.post("/api/v1/courses", response_model=CourseCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_course(request: CourseCreationRequest, db: Session = Depends(get_db)):
    """Créer un nouveau cours avec persistance en base de données"""
    try:
        # Create new course in database
        new_course = CourseTable(
            id=str(uuid4()),
            title=request.title,
            description=request.description,
            subject_domain=request.subject_domain,
            target_audience=request.target_audience,
            difficulty_level=request.difficulty_level,
            estimated_duration_hours=request.estimated_duration_hours,
            status=CourseStatus.DRAFT.value
        )
        
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        
        logger.info(f"✅ Cours créé en base: {new_course.id} - {new_course.title}")
        
        return CourseCreationResponse(
            message="Course created and saved to database successfully",
            course_id=new_course.id,
            status="created"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur création cours: {e}")
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")

@app.get("/api/v1/courses", response_model=CourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lister tous les cours depuis la base de données"""
    try:
        # Base query
        query = db.query(CourseTable)
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(CourseTable.status == status_filter)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        courses = query.order_by(CourseTable.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        course_responses = []
        for course in courses:
            course_responses.append(CourseResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                subject_domain=course.subject_domain,
                target_audience=course.target_audience,
                difficulty_level=course.difficulty_level,
                estimated_duration_hours=course.estimated_duration_hours,
                status=course.status,
                created_at=course.created_at,
                updated_at=course.updated_at
            ))
        
        return CourseListResponse(
            courses=course_responses,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        )
    except Exception as e:
        logger.error(f"❌ Erreur listing cours: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve courses: {str(e)}")

@app.get("/api/v1/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str, db: Session = Depends(get_db)):
    """Récupérer un cours spécifique par ID"""
    try:
        course = db.query(CourseTable).filter(CourseTable.id == course_id).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            subject_domain=course.subject_domain,
            target_audience=course.target_audience,
            difficulty_level=course.difficulty_level,
            estimated_duration_hours=course.estimated_duration_hours,
            status=course.status,
            created_at=course.created_at,
            updated_at=course.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération cours: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve course: {str(e)}")

@app.delete("/api/v1/courses/{course_id}")
async def delete_course(course_id: str, db: Session = Depends(get_db)):
    """Supprimer un cours"""
    try:
        course = db.query(CourseTable).filter(CourseTable.id == course_id).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        db.delete(course)
        db.commit()
        
        return {"message": f"Course {course_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur suppression cours: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete course: {str(e)}")

@app.get("/api/v1/courses/{course_id}/generation-status")
async def get_generation_status(course_id: str, db: Session = Depends(get_db)):
    """Status de génération d'un cours"""
    # Verify course exists
    course = db.query(CourseTable).filter(CourseTable.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {
        "course_id": course_id,
        "status": "completed",
        "progress": 100,
        "current_step": "finished",
        "estimated_completion": None,
        "chapters_generated": 5,
        "total_chapters": 5
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Course Generation Platform API with Database...")
    uvicorn.run("api_with_database:app", host="0.0.0.0", port=8084, reload=True)