#!/usr/bin/env python3
"""
Version simplifiée de l'API pour tests - évite les imports relatifs complexes
"""

import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../.env")

# Create FastAPI application
app = FastAPI(
    title="Course Generation Platform API",
    description="AI-powered course creation and management platform (Test Version)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://course_user:course_password@localhost:5432/course_platform')
engine = create_engine(DATABASE_URL)

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Course Generation Platform API (Test Version)",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": "/api/v1",
        "database": "connected"
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with database connectivity"""
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            db_version = result.fetchone()[0]
            
        return {
            "status": "healthy", 
            "service": "course-platform-api",
            "database": "connected",
            "db_version": db_version[:50] + "..." if len(db_version) > 50 else db_version
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "course-platform-api", 
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Course Generation Platform API",
        "version": "1.0.0",
        "description": "AI-powered course creation and management platform",
        "status": "test_version",
        "endpoints": {
            "courses": "Course management (Basic test version)",
            "health": "Health check with database connectivity",
            "info": "API information"
        },
        "documentation": "/docs"
    }

@app.get("/api/v1/health")
async def api_v1_health():
    """API v1 health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "v1"
    }

@app.get("/api/v1/courses")
async def list_courses():
    """Simple courses endpoint for testing database connectivity"""
    try:
        with engine.connect() as conn:
            # Count courses
            result = conn.execute(text("SELECT COUNT(*) FROM courses"))
            course_count = result.fetchone()[0]
            
            # Get course list (simple query)
            result = conn.execute(text("SELECT id, title, created_at FROM courses ORDER BY created_at DESC LIMIT 10"))
            courses = []
            for row in result.fetchall():
                courses.append({
                    "id": str(row[0]),
                    "title": row[1],
                    "created_at": row[2].isoformat() if row[2] else None
                })
            
        return {
            "courses": courses,
            "total": course_count,
            "page": 1,
            "limit": 10,
            "message": "Database connection successful"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/v1/courses")
async def create_course_simple():
    """Simple course creation endpoint for testing"""
    return {
        "message": "Course creation endpoint (test version)",
        "note": "Full implementation requires complete model imports",
        "status": "placeholder"
    }

@app.get("/test/database")
async def test_database():
    """Test database connectivity and show table info"""
    try:
        with engine.connect() as conn:
            # Get table list
            result = conn.execute(text("""
                SELECT table_name, 
                       (SELECT COUNT(*) FROM information_schema.columns 
                        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            tables = []
            for row in result.fetchall():
                table_name = row[0]
                column_count = row[1]
                
                # Get row count for each table
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.fetchone()[0]
                
                tables.append({
                    "name": table_name,
                    "columns": column_count,
                    "rows": row_count
                })
            
        return {
            "database_status": "connected",
            "tables": tables,
            "total_tables": len(tables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8001, reload=True)