"""
Export service for multiple educational content formats.

Implements T036: Export service for SCORM/xAPI formats with support for:
- SCORM 2004 4th Edition packages  
- xAPI (Tin Can API) content
- QTI 2.1 assessment format
- PDF document generation
- HTML standalone format

Based on educational standards compliance and LMS interoperability requirements.
"""

import hashlib
import json
import tempfile
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, Field, validator
from weasyprint import HTML

from ..models.course import Course
from ..models.chapter import Chapter  
from ..models.quiz import Quiz
from ..models.enums import CourseStatus


class ExportRequest(BaseModel):
    """Export request validation schema."""
    
    format: str = Field(..., description="Export format")
    include_assessments: bool = Field(True, description="Include quizzes and assessments")
    include_multimedia: bool = Field(True, description="Include images, videos, diagrams")
    scorm_version: Optional[str] = Field("2004_4th_edition", description="SCORM version for SCORM exports")
    xapi_profile: Optional[str] = Field("cmi5", description="xAPI profile for xAPI exports")
    
    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["scorm2004", "xapi", "qti21", "pdf", "html"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of: {', '.join(valid_formats)}")
        return v


class ExportResponse(BaseModel):
    """Export response schema."""
    
    download_url: str = Field(..., description="Temporary download URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")
    file_size: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="MD5 checksum of exported file")
    scorm_metadata: Optional[Dict] = Field(None, description="SCORM-specific metadata")
    xapi_metadata: Optional[Dict] = Field(None, description="xAPI-specific metadata")


class SCORMPackage:
    """SCORM 2004 package structure and metadata."""
    
    def __init__(self, course: Course):
        self.course = course
        self.identifier = f"course_{course.id}"
        self.version = "2004 4th Edition"
        
    def generate_manifest(self) -> str:
        """Generate imsmanifest.xml for SCORM package."""
        manifest_template = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{{ identifier }}" version="1.3"
    xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
    xmlns:adlcp="http://www.adlcp.org/xsd/adlcp_v1p3"
    xmlns:adlseq="http://www.adlcp.org/xsd/adlseq_v1p3"
    xmlns:adlnav="http://www.adlcp.org/xsd/adlnav_v1p3"
    xmlns:imsss="http://www.imsglobal.org/xsd/imsss"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imscp_v1p1 imscp_v1p1.xsd
                        http://www.adlcp.org/xsd/adlcp_v1p3 adlcp_v1p3.xsd
                        http://www.adlcp.org/xsd/adlseq_v1p3 adlseq_v1p3.xsd
                        http://www.adlcp.org/xsd/adlnav_v1p3 adlnav_v1p3.xsd
                        http://www.imsglobal.org/xsd/imsss imsss_v1p0.xsd">
    
    <metadata>
        <schema>ADL SCORM</schema>
        <schemaversion>2004 4th Edition</schemaversion>
        <adlcp:location>metadata.xml</adlcp:location>
    </metadata>
    
    <organizations default="default_org">
        <organization identifier="default_org">
            <title>{{ course.title }}</title>
            <item identifier="course_item" identifierref="course_resource">
                <title>{{ course.title }}</title>
                <adlcp:masteryscore>{{ mastery_score }}</adlcp:masteryscore>
                {% for chapter in chapters %}
                <item identifier="chapter_{{ chapter.sequence_number }}" identifierref="chapter_{{ chapter.sequence_number }}_resource">
                    <title>{{ chapter.title }}</title>
                </item>
                {% endfor %}
            </item>
        </organization>
    </organizations>
    
    <resources>
        <resource identifier="course_resource" type="webcontent" adlcp:scormType="sco" href="index.html">
            <file href="index.html"/>
            <file href="course_content.html"/>
            {% for file in resource_files %}
            <file href="{{ file }}"/>
            {% endfor %}
        </resource>
        {% for chapter in chapters %}
        <resource identifier="chapter_{{ chapter.sequence_number }}_resource" type="webcontent" href="chapter_{{ chapter.sequence_number }}.html">
            <file href="chapter_{{ chapter.sequence_number }}.html"/>
        </resource>
        {% endfor %}
    </resources>
</manifest>"""
        
        env = Environment(autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string(manifest_template)
        
        return template.render(
            identifier=self.identifier,
            course=self.course,
            chapters=getattr(self.course, 'chapters', []),
            mastery_score=80,  # Default mastery score
            resource_files=[]  # TODO: Add multimedia files
        )


class XAPIPackage:
    """xAPI (Tin Can API) package structure."""
    
    def __init__(self, course: Course, profile: str = "cmi5"):
        self.course = course
        self.profile = profile
        self.activity_id = f"https://example.com/courses/{course.id}"
        
    def generate_activity_definition(self) -> Dict:
        """Generate xAPI activity definition."""
        return {
            "objectType": "Activity",
            "id": self.activity_id,
            "definition": {
                "name": {"en": self.course.title},
                "description": {"en": self.course.description or ""},
                "type": "http://adlnet.gov/expapi/activities/course",
                "extensions": {
                    "https://w3id.org/xapi/cmi5/context/extensions/sessionid": str(uuid.uuid4()),
                    "https://w3id.org/xapi/cmi5/context/extensions/masteryscore": 0.8
                },
                "interactionType": "other"
            }
        }
    
    def generate_cmi5_xml(self) -> str:
        """Generate cmi5.xml for cmi5 profile."""
        cmi5_template = """<?xml version="1.0" encoding="UTF-8"?>
<courseStructure xmlns="https://w3id.org/xapi/profiles/cmi5/v1.0">
    <course id="{{ course_id }}">
        <title>
            <langstring lang="en">{{ course.title }}</langstring>
        </title>
        <description>
            <langstring lang="en">{{ course.description }}</langstring>
        </description>
        <objectives>
            {% for objective in course.learning_objectives %}
            <objective>
                <langstring lang="en">{{ objective }}</langstring>
            </objective>
            {% endfor %}
        </objectives>
        {% for chapter in chapters %}
        <au id="chapter_{{ chapter.sequence_number }}" moveOn="Completed" masteryScore="{{ mastery_score }}">
            <url>chapter_{{ chapter.sequence_number }}.html</url>
            <title>
                <langstring lang="en">{{ chapter.title }}</langstring>
            </title>
        </au>
        {% endfor %}
    </course>
</courseStructure>"""
        
        env = Environment(autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string(cmi5_template)
        
        return template.render(
            course_id=self.activity_id,
            course=self.course,
            chapters=getattr(self.course, 'chapters', []),
            mastery_score=0.8
        )


class QTIPackage:
    """QTI 2.1 assessment package."""
    
    def __init__(self, course: Course):
        self.course = course
        self.identifier = f"qti_course_{course.id}"
        
    def generate_manifest(self) -> str:
        """Generate QTI manifest.xml."""
        manifest_template = """<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_v1p2"
          xmlns:imsqti="http://www.imsglobal.org/xsd/imsqti_v2p1"
          identifier="{{ identifier }}"
          version="1.0">
    
    <metadata>
        <schema>IMS QTI</schema>
        <schemaversion>2.1</schemaversion>
    </metadata>
    
    <organizations>
        <organization identifier="course_org">
            <title>{{ course.title }} - Assessments</title>
            {% for quiz in quizzes %}
            <item identifier="quiz_{{ quiz.id }}" identifierref="quiz_{{ quiz.id }}_resource">
                <title>{{ quiz.title }}</title>
            </item>
            {% endfor %}
        </organization>
    </organizations>
    
    <resources>
        {% for quiz in quizzes %}
        <resource identifier="quiz_{{ quiz.id }}_resource" type="imsqti_test_xmlv2p1" href="quiz_{{ quiz.id }}.xml">
            <file href="quiz_{{ quiz.id }}.xml"/>
        </resource>
        {% endfor %}
    </resources>
</manifest>"""
        
        env = Environment(autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string(manifest_template)
        
        return template.render(
            identifier=self.identifier,
            course=self.course,
            quizzes=getattr(self.course, 'quizzes', [])
        )


class ExportService:
    """Main export service orchestrating multiple format exports."""
    
    def __init__(self, base_url: str = "https://api.example.com", temp_dir: str = "/tmp"):
        self.base_url = base_url
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
    async def export_course(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> ExportResponse:
        """
        Main export orchestration method.
        
        Args:
            course: Course entity to export
            export_request: Export configuration
            
        Returns:
            ExportResponse with download URL and metadata
            
        Raises:
            ValueError: If course is not ready for export
            NotImplementedError: If format not supported
        """
        # Validate course status
        if course.status not in [CourseStatus.READY, CourseStatus.PUBLISHED]:
            raise ValueError(f"Course must be READY or PUBLISHED for export, got {course.status}")
        
        # Route to appropriate export method
        export_method = {
            "scorm2004": self.export_to_scorm,
            "xapi": self.export_to_xapi, 
            "qti21": self.export_to_qti,
            "pdf": self.export_to_pdf,
            "html": self.export_to_html
        }.get(export_request.format)
        
        if not export_method:
            raise NotImplementedError(f"Export format '{export_request.format}' not implemented")
        
        # Generate export package
        export_path, metadata = await export_method(course, export_request)
        
        # Calculate file size and checksum
        file_size = export_path.stat().st_size
        checksum = self._calculate_checksum(export_path)
        
        # Generate temporary download URL
        download_url = self.generate_download_link(export_path)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        return ExportResponse(
            download_url=download_url,
            expires_at=expires_at,
            file_size=file_size,
            checksum=checksum,
            **metadata
        )
    
    async def export_to_scorm(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> Tuple[Path, Dict]:
        """
        Export course as SCORM 2004 package.
        
        Returns:
            Tuple of (export_file_path, scorm_metadata)
        """
        scorm = SCORMPackage(course)
        
        # Create temporary directory for SCORM content
        with tempfile.TemporaryDirectory() as temp_dir:
            scorm_dir = Path(temp_dir) / "scorm_package"
            scorm_dir.mkdir()
            
            # Generate manifest
            manifest_path = scorm_dir / "imsmanifest.xml"
            manifest_path.write_text(scorm.generate_manifest(), encoding='utf-8')
            
            # Generate course content HTML
            await self._generate_html_content(course, scorm_dir, export_request)
            
            # Create SCORM runtime files
            await self._create_scorm_runtime(scorm_dir)
            
            # Create ZIP package
            zip_path = self.temp_dir / f"scorm_{course.id}_{datetime.utcnow().timestamp()}.zip"
            self._create_zip_package(scorm_dir, zip_path)
            
            metadata = {
                "scorm_metadata": {
                    "manifest_file": "imsmanifest.xml",
                    "package_type": "scorm2004",
                    "version": scorm.version,
                    "identifier": scorm.identifier
                }
            }
            
            return zip_path, metadata
    
    async def export_to_xapi(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> Tuple[Path, Dict]:
        """
        Export course as xAPI (Tin Can API) package.
        
        Returns:
            Tuple of (export_file_path, xapi_metadata)
        """
        xapi = XAPIPackage(course, export_request.xapi_profile or "cmi5")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            xapi_dir = Path(temp_dir) / "xapi_package"
            xapi_dir.mkdir()
            
            # Generate activity definition
            activity_def = xapi.generate_activity_definition()
            activity_path = xapi_dir / "activity.json"
            activity_path.write_text(json.dumps(activity_def, indent=2), encoding='utf-8')
            
            # Generate cmi5.xml if using cmi5 profile
            if export_request.xapi_profile == "cmi5":
                cmi5_path = xapi_dir / "cmi5.xml"
                cmi5_path.write_text(xapi.generate_cmi5_xml(), encoding='utf-8')
            
            # Generate HTML content
            await self._generate_html_content(course, xapi_dir, export_request)
            
            # Create xAPI runtime files
            await self._create_xapi_runtime(xapi_dir, xapi)
            
            # Create ZIP package
            zip_path = self.temp_dir / f"xapi_{course.id}_{datetime.utcnow().timestamp()}.zip"
            self._create_zip_package(xapi_dir, zip_path)
            
            metadata = {
                "xapi_metadata": {
                    "activity_id": xapi.activity_id,
                    "profile": export_request.xapi_profile,
                    "actor_template": {
                        "objectType": "Agent",
                        "name": "Student",
                        "mbox": "mailto:student@example.com"
                    }
                }
            }
            
            return zip_path, metadata
    
    async def export_to_qti(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> Tuple[Path, Dict]:
        """
        Export course assessments as QTI 2.1 package.
        
        Returns:
            Tuple of (export_file_path, qti_metadata)
        """
        qti = QTIPackage(course)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            qti_dir = Path(temp_dir) / "qti_package"
            qti_dir.mkdir()
            
            # Generate QTI manifest
            manifest_path = qti_dir / "manifest.xml"
            manifest_path.write_text(qti.generate_manifest(), encoding='utf-8')
            
            # Generate assessment XML files
            await self._generate_qti_assessments(course, qti_dir, export_request)
            
            # Create ZIP package
            zip_path = self.temp_dir / f"qti_{course.id}_{datetime.utcnow().timestamp()}.zip"
            self._create_zip_package(qti_dir, zip_path)
            
            metadata = {
                "qti_metadata": {
                    "manifest_file": "manifest.xml",
                    "version": "2.1",
                    "identifier": qti.identifier
                }
            }
            
            return zip_path, metadata
    
    async def export_to_pdf(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> Tuple[Path, Dict]:
        """
        Export course as PDF document.
        
        Returns:
            Tuple of (export_file_path, pdf_metadata)
        """
        # Generate HTML content for PDF conversion
        html_content = await self._generate_pdf_html(course, export_request)
        
        # Convert to PDF using WeasyPrint
        pdf_path = self.temp_dir / f"course_{course.id}_{datetime.utcnow().timestamp()}.pdf"
        HTML(string=html_content).write_pdf(str(pdf_path))
        
        metadata = {
            "pdf_metadata": {
                "title": course.title,
                "pages": "calculated_dynamically",  # TODO: Count pages
                "includes_assessments": export_request.include_assessments
            }
        }
        
        return pdf_path, metadata
    
    async def export_to_html(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> Tuple[Path, Dict]:
        """
        Export course as standalone HTML package.
        
        Returns:
            Tuple of (export_file_path, html_metadata)
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            html_dir = Path(temp_dir) / "html_package"
            html_dir.mkdir()
            
            # Generate course content
            await self._generate_html_content(course, html_dir, export_request)
            
            # Add standalone navigation and styling
            await self._create_html_standalone(html_dir, course)
            
            # Create ZIP package
            zip_path = self.temp_dir / f"html_{course.id}_{datetime.utcnow().timestamp()}.zip"
            self._create_zip_package(html_dir, zip_path)
            
            metadata = {
                "html_metadata": {
                    "entry_point": "index.html",
                    "includes_assessments": export_request.include_assessments,
                    "includes_multimedia": export_request.include_multimedia
                }
            }
            
            return zip_path, metadata
    
    def generate_download_link(self, file_path: Path) -> str:
        """
        Generate secure temporary download URL.
        
        Args:
            file_path: Path to exported file
            
        Returns:
            Temporary download URL with expiration
        """
        # Generate secure token
        token = hashlib.sha256(f"{file_path.name}{datetime.utcnow().timestamp()}".encode()).hexdigest()[:16]
        
        # Store file mapping (in production, use Redis or database)
        # For now, just return a mock URL
        return urljoin(self.base_url, f"/api/v1/downloads/{token}/{file_path.name}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _create_zip_package(self, source_dir: Path, zip_path: Path) -> None:
        """Create ZIP package from directory."""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
    
    async def _generate_html_content(
        self, 
        course: Course, 
        output_dir: Path, 
        export_request: ExportRequest
    ) -> None:
        """Generate HTML content files for the course."""
        # Create index.html
        index_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ course.title }}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="course-container">
        <header>
            <h1>{{ course.title }}</h1>
            <p class="description">{{ course.description }}</p>
        </header>
        
        <main>
            <section class="course-info">
                <h2>Course Information</h2>
                <ul>
                    <li><strong>Duration:</strong> {{ course.estimated_duration }}</li>
                    <li><strong>Difficulty:</strong> {{ course.difficulty_score }}/5</li>
                    <li><strong>Language:</strong> {{ course.language }}</li>
                </ul>
            </section>
            
            <section class="learning-objectives">
                <h2>Learning Objectives</h2>
                <ul>
                    {% for objective in course.learning_objectives %}
                    <li>{{ objective }}</li>
                    {% endfor %}
                </ul>
            </section>
            
            <section class="chapters">
                <h2>Course Content</h2>
                {% for chapter in chapters %}
                <div class="chapter">
                    <h3><a href="chapter_{{ chapter.sequence_number }}.html">Chapter {{ chapter.sequence_number }}: {{ chapter.title }}</a></h3>
                </div>
                {% endfor %}
            </section>
        </main>
    </div>
</body>
</html>"""
        
        env = Environment(autoescape=select_autoescape(['html']))
        template = env.from_string(index_template)
        
        index_html = template.render(
            course=course,
            chapters=getattr(course, 'chapters', [])
        )
        
        (output_dir / "index.html").write_text(index_html, encoding='utf-8')
        
        # Create basic CSS
        css_content = """
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
        .course-container { max-width: 800px; margin: 0 auto; }
        header { border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px; }
        h1 { color: #333; }
        .description { font-style: italic; color: #666; }
        section { margin-bottom: 30px; }
        h2 { color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
        ul { padding-left: 20px; }
        .chapter { margin: 10px 0; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        """
        
        (output_dir / "styles.css").write_text(css_content, encoding='utf-8')
    
    async def _create_scorm_runtime(self, scorm_dir: Path) -> None:
        """Create SCORM runtime API files."""
        # Basic SCORM API wrapper
        api_js = """
        // SCORM 2004 API Wrapper
        var API_1484_11 = {
            Initialize: function(parameter) { return "true"; },
            Terminate: function(parameter) { return "true"; },
            GetValue: function(element) { return ""; },
            SetValue: function(element, value) { return "true"; },
            Commit: function(parameter) { return "true"; },
            GetLastError: function() { return "0"; },
            GetErrorString: function(errorCode) { return ""; },
            GetDiagnostic: function(errorCode) { return ""; }
        };
        """
        
        (scorm_dir / "scorm_api.js").write_text(api_js, encoding='utf-8')
    
    async def _create_xapi_runtime(self, xapi_dir: Path, xapi: XAPIPackage) -> None:
        """Create xAPI runtime files."""
        # Basic xAPI wrapper
        xapi_js = f"""
        // xAPI (Tin Can API) Wrapper
        var xapi = {{
            activityId: "{xapi.activity_id}",
            actor: {{
                "objectType": "Agent",
                "name": "Student",
                "mbox": "mailto:student@example.com"
            }},
            sendStatement: function(verb, object) {{
                // Implementation would send to LRS
                console.log("xAPI Statement:", {{ verb: verb, object: object }});
            }}
        }};
        """
        
        (xapi_dir / "xapi_wrapper.js").write_text(xapi_js, encoding='utf-8')
    
    async def _generate_qti_assessments(
        self, 
        course: Course, 
        qti_dir: Path, 
        export_request: ExportRequest
    ) -> None:
        """Generate QTI XML files for assessments."""
        # TODO: Implement QTI assessment generation
        # This would iterate through course quizzes and generate QTI XML
        placeholder_qti = """<?xml version="1.0" encoding="UTF-8"?>
<assessmentTest xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
                identifier="assessment_placeholder"
                title="Course Assessment">
    <!-- QTI assessment items would be generated here -->
</assessmentTest>"""
        
        (qti_dir / "assessment_placeholder.xml").write_text(placeholder_qti, encoding='utf-8')
    
    async def _generate_pdf_html(
        self, 
        course: Course, 
        export_request: ExportRequest
    ) -> str:
        """Generate HTML content optimized for PDF conversion."""
        pdf_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ course.title }}</title>
    <style>
        @page { margin: 2cm; }
        body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 12pt; line-height: 1.4; }
        h1 { color: #333; page-break-before: auto; }
        h2 { color: #555; margin-top: 30px; }
        .course-meta { background: #f5f5f5; padding: 15px; margin: 20px 0; }
        .chapter { page-break-before: always; }
        .no-break { page-break-inside: avoid; }
    </style>
</head>
<body>
    <div class="title-page">
        <h1>{{ course.title }}</h1>
        <p class="description">{{ course.description }}</p>
        
        <div class="course-meta">
            <p><strong>Duration:</strong> {{ course.estimated_duration }}</p>
            <p><strong>Difficulty Level:</strong> {{ course.difficulty_score }}/5</p>
            <p><strong>Language:</strong> {{ course.language }}</p>
            <p><strong>Version:</strong> {{ course.version }}</p>
        </div>
        
        <div class="learning-objectives no-break">
            <h2>Learning Objectives</h2>
            <ul>
                {% for objective in course.learning_objectives %}
                <li>{{ objective }}</li>
                {% endfor %}
            </ul>
        </div>
    </div>
    
    {% for chapter in chapters %}
    <div class="chapter">
        <h1>Chapter {{ chapter.sequence_number }}: {{ chapter.title }}</h1>
        <!-- Chapter content would be rendered here -->
    </div>
    {% endfor %}
</body>
</html>"""
        
        env = Environment(autoescape=select_autoescape(['html']))
        template = env.from_string(pdf_template)
        
        return template.render(
            course=course,
            chapters=getattr(course, 'chapters', [])
        )
    
    async def _create_html_standalone(self, html_dir: Path, course: Course) -> None:
        """Create standalone HTML navigation and structure."""
        # Enhanced navigation for standalone HTML
        nav_js = """
        // Course Navigation
        document.addEventListener('DOMContentLoaded', function() {
            // Add navigation functionality
            const chapters = document.querySelectorAll('.chapter a');
            chapters.forEach(link => {
                link.addEventListener('click', function(e) {
                    // Track chapter access
                    console.log('Accessed:', this.textContent);
                });
            });
        });
        """
        
        (html_dir / "navigation.js").write_text(nav_js, encoding='utf-8')