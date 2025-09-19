#!/usr/bin/env python3
"""
Fixed FastAPI main application with absolute imports
Course Generation Platform API - Fixed version for testing
"""

import sys
import os
from pathlib import Path

# Add src to Python path for absolute imports
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Course Generation Platform API",
    description="AI-powered course creation and management platform",
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

try:
    engine = create_engine(DATABASE_URL)
    logger.info("✅ Database engine created successfully")
except Exception as e:
    logger.error(f"❌ Database engine creation failed: {e}")
    raise

# Try to import and include API routes
try:
    # Import with absolute imports from src
    from database.session import get_db
    from api import api_v1_router
    
    # Include the API v1 router
    app.include_router(api_v1_router)
    logger.info("✅ API v1 router included successfully")
    
except ImportError as e:
    logger.warning(f"⚠️ Could not import full API router: {e}")
    logger.info("📝 Falling back to basic endpoints only")
    
    # Fallback basic endpoints
    @app.get("/api/v1/health")
    async def api_health():
        return {"status": "healthy", "message": "Basic API only - import issues detected"}

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Course Generation Platform API (Fixed Version)",
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
            "db_version": db_version[:50] + "..." if len(db_version) > 50 else db_version,
            "api_status": "full" if "api_v1_router" in globals() else "basic"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "course-platform-api", 
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Course Generation Platform API...")
    uvicorn.run("main_fixed:app", host="0.0.0.0", port=8082, reload=True)