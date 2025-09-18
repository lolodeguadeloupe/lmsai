from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import logging
import io
import tempfile
import os

from ...database.session import get_db
from ...services.export_service import ExportService
from ...models.course import Course
from ...models.enums import CourseStatus, ExportFormat, ExportStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["export"])

# Pydantic models for request/response
from pydantic import BaseModel, Field
from datetime import datetime

class ExportRequest(BaseModel):
    format: ExportFormat = Field(..., description="Export format (SCORM, xAPI, PDF, HTML)")
    include_assessments: bool = Field(True, description="Include quizzes and assessments")
    include_multimedia: bool = Field(True, description="Include images and videos")
    compression_level: Optional[str] = Field("standard", description="Compression level for package")
    custom_styling: Optional[Dict[str, Any]] = Field(None, description="Custom styling options")
    
class ExportResponse(BaseModel):
    export_id: UUID
    course_id: UUID
    format: ExportFormat
    status: ExportStatus
    download_url: Optional[str]
    file_size_bytes: Optional[int]
    created_at: datetime
    expires_at: Optional[datetime]
    error_message: Optional[str]

class ExportStatusResponse(BaseModel):
    export_id: UUID
    status: ExportStatus
    progress_percentage: int = Field(..., ge=0, le=100)
    estimated_completion_time: Optional[datetime]
    file_info: Optional[Dict[str, Any]]
    error_details: Optional[str]

# T048: POST /courses/{courseId}/export endpoint
@router.post("/{course_id}/export", response_model=ExportResponse)
async def export_course(
    course_id: UUID,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ExportResponse:
    """
    Export a course in the specified format.
    
    Supported formats:
    - SCORM: SCORM 1.2 and 2004 packages
    - xAPI: Experience API (Tin Can API) packages
    - PDF: Comprehensive PDF document
    - HTML: Standalone HTML package
    
    The export process:
    1. Validates the course is complete
    2. Initiates background export task
    3. Returns export tracking information
    4. Generates downloadable package
    """
    try:
        logger.info(f"Starting export for course {course_id} in format {request.format}")
        
        # Verify course exists and is complete
        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Check if course is complete enough for export
        if course.status not in [CourseStatus.COMPLETED, CourseStatus.REVIEW]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course must be completed before export. Current status: {course.status}"
            )
        
        # Validate export format
        if request.format not in ExportFormat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {request.format}"
            )
        
        # Initialize export service
        export_service = ExportService(db)
        
        # Create export record and start background task
        export_record = await export_service.create_export(
            course_id=course_id,
            export_format=request.format,
            include_assessments=request.include_assessments,
            include_multimedia=request.include_multimedia,
            compression_level=request.compression_level,
            custom_styling=request.custom_styling
        )
        
        # Add background task for actual export processing
        background_tasks.add_task(
            export_service.process_export,
            export_record.id
        )
        
        logger.info(f"Export initiated successfully with ID: {export_record.id}")
        
        return ExportResponse(
            export_id=export_record.id,
            course_id=course_id,
            format=request.format,
            status=ExportStatus.PENDING,
            download_url=None,  # Will be available once processing is complete
            file_size_bytes=None,
            created_at=export_record.created_at,
            expires_at=export_record.expires_at,
            error_message=None
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in export request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error initiating export for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate course export"
        )

# Get export status
@router.get("/{course_id}/export/{export_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    course_id: UUID,
    export_id: UUID,
    db: Session = Depends(get_db)
) -> ExportStatusResponse:
    """
    Get the status of an ongoing or completed export.
    
    Returns detailed information about:
    - Export progress percentage
    - Estimated completion time
    - File information (size, format details)
    - Error details if export failed
    """
    try:
        logger.info(f"Fetching export status for export {export_id}")
        
        # Initialize export service
        export_service = ExportService(db)
        
        # Get export status
        export_info = await export_service.get_export_status(export_id)
        
        if not export_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export with ID {export_id} not found"
            )
        
        return ExportStatusResponse(
            export_id=export_id,
            status=export_info['status'],
            progress_percentage=export_info['progress_percentage'],
            estimated_completion_time=export_info.get('estimated_completion_time'),
            file_info=export_info.get('file_info'),
            error_details=export_info.get('error_details')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching export status {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch export status"
        )

# Download export file
@router.get("/{course_id}/export/{export_id}/download")
async def download_export(
    course_id: UUID,
    export_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Download the completed export file.
    
    Returns the exported course package as a downloadable file.
    The file format and name depend on the export format chosen.
    """
    try:
        logger.info(f"Processing download request for export {export_id}")
        
        # Initialize export service
        export_service = ExportService(db)
        
        # Get export record and file path
        export_record = await export_service.get_export_record(export_id)
        
        if not export_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export with ID {export_id} not found"
            )
        
        if export_record.status != ExportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Export is not ready for download. Status: {export_record.status}"
            )
        
        if not export_record.file_path or not os.path.exists(export_record.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found or has expired"
            )
        
        # Determine content type and filename based on format
        content_type_map = {
            ExportFormat.SCORM: "application/zip",
            ExportFormat.XAPI: "application/zip",
            ExportFormat.PDF: "application/pdf",
            ExportFormat.HTML: "application/zip"
        }
        
        filename_map = {
            ExportFormat.SCORM: f"course_{course_id}_scorm.zip",
            ExportFormat.XAPI: f"course_{course_id}_xapi.zip",
            ExportFormat.PDF: f"course_{course_id}.pdf",
            ExportFormat.HTML: f"course_{course_id}_html.zip"
        }
        
        content_type = content_type_map.get(export_record.format, "application/octet-stream")
        filename = filename_map.get(export_record.format, f"course_{course_id}_export")
        
        # Return file response
        return FileResponse(
            path=export_record.file_path,
            media_type=content_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(os.path.getsize(export_record.file_path))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download export file"
        )

# List all exports for a course
@router.get("/{course_id}/exports")
async def list_course_exports(
    course_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all export records for a specific course.
    
    Useful for tracking export history and managing storage.
    """
    try:
        logger.info(f"Listing exports for course {course_id}")
        
        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        
        # Initialize export service
        export_service = ExportService(db)
        
        # Get all exports for the course
        exports = await export_service.list_course_exports(course_id)
        
        return {
            "course_id": course_id,
            "exports": exports,
            "total_exports": len(exports)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing exports for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list course exports"
        )

# Delete an export
@router.delete("/{course_id}/export/{export_id}")
async def delete_export(
    course_id: UUID,
    export_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete an export record and associated files.
    
    Useful for cleaning up storage space.
    """
    try:
        logger.info(f"Deleting export {export_id} for course {course_id}")
        
        # Initialize export service
        export_service = ExportService(db)
        
        # Delete the export
        await export_service.delete_export(export_id)
        
        return {
            "message": "Export deleted successfully",
            "export_id": str(export_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export {export_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete export"
        )
