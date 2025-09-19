#!/usr/bin/env python3
"""
API vraiment simulée - Tout en mémoire, aucune persistance
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage
courses_memory: Dict[str, Dict] = {}

# FastAPI app
app = FastAPI(
    title="Course Platform API - Simulation Pure",
    description="API complètement simulée - Données en mémoire uniquement",
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

# Pydantic models
class CourseCreationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    subject_domain: str = Field(..., min_length=1)
    target_audience: str = Field(..., min_length=1)
    difficulty_level: str = Field(..., pattern="^(Débutant|Intermédiaire|Avancé)$")
    estimated_duration_hours: int = Field(..., ge=1, le=1000)
    learning_objectives: Optional[List[str]] = Field(default_factory=list)

class CourseResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    subject_domain: str
    target_audience: List[str]
    difficulty_level: str
    estimated_duration_hours: int
    learning_objectives: List[str]
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

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Course Platform API - SIMULATION PURE",
        "version": "1.0.0",
        "storage": "IN MEMORY ONLY - No persistence",
        "total_courses": len(courses_memory),
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "course-platform-api-simulation",
        "storage": "memory_only", 
        "persistence": False,
        "total_courses": len(courses_memory),
        "warning": "All data will be lost on restart"
    }

@app.post("/api/v1/courses", response_model=CourseCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_course_memory(request: CourseCreationRequest):
    """Créer un cours en mémoire uniquement (simulation)"""
    try:
        course_id = str(uuid4())
        current_time = datetime.utcnow()
        
        # Store in memory
        course_data = {
            "id": course_id,
            "title": request.title,
            "description": request.description or "",
            "subject_domain": request.subject_domain,
            "target_audience": [request.target_audience],
            "difficulty_level": request.difficulty_level,
            "estimated_duration_hours": request.estimated_duration_hours,
            "learning_objectives": request.learning_objectives or [],
            "status": "DRAFT",
            "created_at": current_time,
            "updated_at": current_time
        }
        
        courses_memory[course_id] = course_data
        
        logger.info(f"📝 Cours simulé créé: {course_id} - {request.title} (Total: {len(courses_memory)})")
        
        return CourseCreationResponse(
            message="Course created in memory (simulation)",
            course_id=course_id,
            status="created"
        )
    except Exception as e:
        logger.error(f"❌ Erreur création cours simulé: {e}")
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")

@app.get("/api/v1/courses", response_model=CourseListResponse)
async def list_courses_memory(
    page: int = 1,
    limit: int = 10,
    status_filter: Optional[str] = None
):
    """Lister tous les cours depuis la mémoire"""
    try:
        # Get all courses from memory
        all_courses = list(courses_memory.values())
        
        # Apply status filter if provided
        if status_filter:
            all_courses = [c for c in all_courses if c["status"] == status_filter]
        
        # Sort by creation date (newest first)
        all_courses.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        total_count = len(all_courses)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_courses = all_courses[start_idx:end_idx]
        
        # Convert to response format
        course_responses = []
        for course in paginated_courses:
            course_responses.append(CourseResponse(
                id=course["id"],
                title=course["title"],
                description=course["description"],
                subject_domain=course["subject_domain"],
                target_audience=course["target_audience"],
                difficulty_level=course["difficulty_level"],
                estimated_duration_hours=course["estimated_duration_hours"],
                learning_objectives=course["learning_objectives"],
                status=course["status"],
                created_at=course["created_at"],
                updated_at=course["updated_at"]
            ))
        
        logger.info(f"📋 Liste cours simulés: {len(course_responses)}/{total_count}")
        
        return CourseListResponse(
            courses=course_responses,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit if total_count > 0 else 0
            }
        )
    except Exception as e:
        logger.error(f"❌ Erreur listing cours simulés: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve courses: {str(e)}")

@app.get("/api/v1/courses/{course_id}", response_model=CourseResponse)
async def get_course_memory(course_id: str):
    """Récupérer un cours spécifique depuis la mémoire"""
    if course_id not in courses_memory:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = courses_memory[course_id]
    return CourseResponse(
        id=course["id"],
        title=course["title"],
        description=course["description"],
        subject_domain=course["subject_domain"],
        target_audience=course["target_audience"],
        difficulty_level=course["difficulty_level"],
        estimated_duration_hours=course["estimated_duration_hours"],
        learning_objectives=course["learning_objectives"],
        status=course["status"],
        created_at=course["created_at"],
        updated_at=course["updated_at"]
    )

@app.delete("/api/v1/courses/{course_id}")
async def delete_course_memory(course_id: str):
    """Supprimer un cours de la mémoire"""
    if course_id not in courses_memory:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course_title = courses_memory[course_id]["title"]
    del courses_memory[course_id]
    
    logger.info(f"🗑️ Cours simulé supprimé: {course_id} - {course_title}")
    return {"message": f"Course {course_id} deleted from memory"}

@app.post("/api/v1/reset")
async def reset_memory():
    """Vider toute la mémoire (reset complet)"""
    courses_memory.clear()
    logger.info("🔄 Mémoire vidée - tous les cours simulés supprimés")
    return {"message": "All courses cleared from memory", "total_courses": 0}

@app.get("/api/v1/memory-stats")
async def memory_stats():
    """Statistiques de la mémoire"""
    return {
        "total_courses": len(courses_memory),
        "course_ids": list(courses_memory.keys()),
        "storage_type": "in_memory_only",
        "persistence": False,
        "warning": "Data will be lost on server restart"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🎭 Starting PURE SIMULATION Course API (Memory Only)...")
    uvicorn.run("api_vraiment_simulee:app", host="0.0.0.0", port=8086, reload=True)