"""
Unit tests for the course generation service.

Tests all core functionality including course creation, chapter generation,
quality validation, and error handling scenarios.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.course_generation_service import (
    CourseGenerationService,
    CourseGenerationRequest,
    GenerationMode,
    GenerationStrategy,
    create_course_generation_service
)
from src.models.course import CourseCreate, TargetAudience, QualityMetrics
from src.models.enums import ProficiencyLevel, LearningPreference
from src.integrations.ai_client import (
    CourseStructureResponse,
    ChapterContentResponse,
    ContentQualityResponse
)


class TestCourseGenerationService:
    """Test cases for CourseGenerationService."""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client for testing."""
        client = AsyncMock()
        
        # Mock course structure response
        client.generate_course_structure.return_value = CourseStructureResponse(
            chapters=[
                {
                    "sequence_number": 1,
                    "title": "Introduction to Testing",
                    "learning_objectives": ["Understand testing basics", "Learn test types"],
                    "estimated_duration": "PT2H",
                    "complexity_level": 2.0,
                    "prerequisites": [],
                    "content_outline": "Basic testing concepts"
                },
                {
                    "sequence_number": 2,
                    "title": "Advanced Testing",
                    "learning_objectives": ["Master testing frameworks", "Create test suites"],
                    "estimated_duration": "PT3H",
                    "complexity_level": 3.0,
                    "prerequisites": ["testing basics"],
                    "content_outline": "Advanced testing concepts"
                }
            ],
            estimated_total_duration=5.0,
            difficulty_progression=[2.0, 3.0],
            suggested_prerequisites=["Programming basics"],
            learning_path_rationale="Progressive complexity",
            quality_indicators={"progression_smoothness": 0.9, "objective_coverage": 1.0}
        )
        
        # Mock chapter content response
        client.generate_chapter_content.return_value = ChapterContentResponse(
            content_blocks=[
                {
                    "type": "text",
                    "content": "Chapter content goes here...",
                    "order": 1
                }
            ],
            key_concepts=["Testing", "Quality Assurance"],
            examples=[
                {
                    "title": "Unit Test Example",
                    "description": "Basic unit test",
                    "code_or_content": "def test_example(): assert True"
                }
            ],
            exercises=[
                {
                    "title": "Write a Test",
                    "description": "Create your first test",
                    "difficulty": "easy",
                    "estimated_time": 15
                }
            ],
            summary="Chapter summary",
            estimated_reading_time=30,
            complexity_score=2.5
        )
        
        # Mock quality validation response
        client.comprehensive_quality_check.return_value = {
            "ai_quality_assessment": {
                "overall_score": 0.85,
                "pedagogical_alignment": 0.9,
                "objective_coverage": 0.95,
                "content_accuracy": 0.88
            },
            "readability_analysis": {
                "flesch_reading_ease": 75.0,
                "meets_target_level": True
            },
            "bias_detection": {
                "overall_bias_score": 0.1,
                "severity_level": "low"
            },
            "overall_quality_score": 0.86,
            "meets_quality_standards": True
        }
        
        return client
    
    @pytest.fixture
    def mock_vector_client(self):
        """Mock vector client for testing."""
        client = AsyncMock()
        client.connect.return_value = None
        client.disconnect.return_value = None
        client.store_course_embeddings.return_value = True
        return client
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def sample_course_data(self):
        """Sample course creation data for testing."""
        return CourseCreate(
            title="Test Course",
            description="A comprehensive test course",
            subject_domain="Software Testing",
            target_audience=TargetAudience(
                proficiency_level=ProficiencyLevel.INTERMEDIATE,
                prerequisites=["Basic programming"],
                learning_preferences=[LearningPreference.VISUAL]
            ),
            learning_objectives=[
                "Learn testing fundamentals",
                "Master test automation",
                "Understand quality assurance"
            ],
            estimated_duration="PT20H",
            difficulty_score=3.0,
            language="en",
            version="1.0.0"
        )
    
    @pytest.fixture
    def service(self, mock_ai_client, mock_vector_client, mock_db_session):
        """Course generation service instance for testing."""
        return CourseGenerationService(
            ai_client=mock_ai_client,
            vector_client=mock_vector_client,
            db_session=mock_db_session
        )
    
    @pytest.mark.asyncio
    async def test_create_course_success(self, service, sample_course_data):
        """Test successful course creation."""
        request = CourseGenerationRequest(
            course_data=sample_course_data,
            generation_mode=GenerationMode.BALANCED,
            generation_strategy=GenerationStrategy.PARALLEL
        )
        
        result = await service.create_course(request)
        
        assert result.status.value == "ready"
        assert len(result.chapters) == 2
        assert result.vector_embeddings_stored > 0
        assert result.quality_metrics.readability_score >= 70.0
        assert result.generation_metadata["generation_mode"] == GenerationMode.BALANCED
        
        # Verify AI client was called
        service.ai_client.generate_course_structure.assert_called_once()
        assert service.ai_client.generate_chapter_content.call_count == 2
        service.ai_client.comprehensive_quality_check.assert_called_once()
        
        # Verify vector client was called
        service.vector_client.connect.assert_called_once()
        service.vector_client.store_course_embeddings.assert_called_once()
        service.vector_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_course_structure(self, service, sample_course_data):
        """Test course structure generation."""
        course_id = uuid4()
        
        structure = await service.generate_course_structure(
            course_id=course_id,
            course_data=sample_course_data,
            mode=GenerationMode.BALANCED
        )
        
        assert "chapters" in structure
        assert len(structure["chapters"]) == 2
        assert structure["chapters"][0]["sequence_number"] == 1
        assert structure["chapters"][1]["sequence_number"] == 2
        
        # Verify AI client was called with correct parameters
        service.ai_client.generate_course_structure.assert_called_once()
        call_args = service.ai_client.generate_course_structure.call_args[0][0]
        assert call_args.title == sample_course_data.title
        assert call_args.target_level == sample_course_data.target_audience.proficiency_level
    
    @pytest.mark.asyncio
    async def test_generate_chapters_parallel(self, service, sample_course_data):
        """Test parallel chapter generation."""
        course_id = uuid4()
        chapter_structure = [
            {
                "sequence_number": 1,
                "title": "Chapter 1",
                "learning_objectives": ["Objective 1"],
                "estimated_duration": "PT2H",
                "complexity_level": 2.0
            },
            {
                "sequence_number": 2,
                "title": "Chapter 2",
                "learning_objectives": ["Objective 2"],
                "estimated_duration": "PT2H",
                "complexity_level": 2.5
            }
        ]
        
        chapters = await service.generate_chapters(
            course_id=course_id,
            course_data=sample_course_data,
            chapter_structure=chapter_structure,
            strategy=GenerationStrategy.PARALLEL,
            mode=GenerationMode.BALANCED
        )
        
        assert len(chapters) == 2
        assert chapters[0].sequence_number == 1
        assert chapters[1].sequence_number == 2
        assert all(chapter.course_id == course_id for chapter in chapters)
        
        # Verify AI client was called for each chapter
        assert service.ai_client.generate_chapter_content.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_chapters_sequential(self, service, sample_course_data):
        """Test sequential chapter generation."""
        course_id = uuid4()
        chapter_structure = [
            {
                "sequence_number": 1,
                "title": "Chapter 1",
                "learning_objectives": ["Objective 1"],
                "estimated_duration": "PT2H",
                "complexity_level": 2.0
            }
        ]
        
        chapters = await service.generate_chapters(
            course_id=course_id,
            course_data=sample_course_data,
            chapter_structure=chapter_structure,
            strategy=GenerationStrategy.SEQUENTIAL,
            mode=GenerationMode.BALANCED
        )
        
        assert len(chapters) == 1
        assert chapters[0].sequence_number == 1
        
        # Verify sequential processing
        service.ai_client.generate_chapter_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_chapters_hybrid(self, service, sample_course_data):
        """Test hybrid chapter generation strategy."""
        course_id = uuid4()
        chapter_structure = [
            {
                "sequence_number": i,
                "title": f"Chapter {i}",
                "learning_objectives": [f"Objective {i}"],
                "estimated_duration": "PT2H",
                "complexity_level": 2.0
            }
            for i in range(1, 6)  # 5 chapters
        ]
        
        chapters = await service.generate_chapters(
            course_id=course_id,
            course_data=sample_course_data,
            chapter_structure=chapter_structure,
            strategy=GenerationStrategy.HYBRID,
            mode=GenerationMode.BALANCED
        )
        
        assert len(chapters) == 5
        assert all(chapter.course_id == course_id for chapter in chapters)
        
        # Verify all chapters were generated
        assert service.ai_client.generate_chapter_content.call_count == 5
    
    @pytest.mark.asyncio
    async def test_create_assessments(self, service, sample_course_data):
        """Test assessment creation."""
        course_id = uuid4()
        chapters = []  # Mock chapters list
        
        assessments = await service.create_assessments(
            course_id=course_id,
            course_data=sample_course_data,
            chapters=chapters
        )
        
        assert "chapter_quizzes" in assessments
        assert "final_assessment" in assessments
        assert "practice_exercises" in assessments
        assert assessments["final_assessment"]["course_id"] == str(course_id)
    
    @pytest.mark.asyncio
    async def test_validate_content_quality(self, service, sample_course_data):
        """Test content quality validation."""
        course_id = uuid4()
        chapters = []  # Mock chapters list
        quality_thresholds = {
            "readability_score": 70.0,
            "pedagogical_alignment": 0.8,
            "content_accuracy": 0.85,
            "bias_detection_score": 0.9
        }
        
        quality_metrics = await service.validate_content_quality(
            course_id=course_id,
            course_data=sample_course_data,
            chapters=chapters,
            quality_thresholds=quality_thresholds
        )
        
        assert isinstance(quality_metrics, QualityMetrics)
        assert quality_metrics.readability_score >= 70.0
        assert quality_metrics.pedagogical_alignment >= 0.8
        assert quality_metrics.content_accuracy >= 0.8
        
        # Verify AI client was called for quality check
        service.ai_client.comprehensive_quality_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_course(self, service, sample_course_data, mock_db_session):
        """Test course saving to database."""
        course_id = uuid4()
        chapters = []  # Mock chapters list
        quality_metrics = QualityMetrics(
            readability_score=85.0,
            pedagogical_alignment=0.9,
            objective_coverage=0.95,
            content_accuracy=0.88,
            bias_detection_score=0.95,
            generation_timestamp=datetime.utcnow()
        )
        
        course = await service.save_course(
            course_id=course_id,
            course_data=sample_course_data,
            chapters=chapters,
            quality_metrics=quality_metrics,
            db=mock_db_session
        )
        
        assert course.id == course_id
        assert course.title == sample_course_data.title
        assert course.status.value == "ready"
        assert course.quality_metrics == quality_metrics
    
    @pytest.mark.asyncio
    async def test_chapter_generation_performance(self, service, sample_course_data):
        """Test that chapter generation meets performance requirements (<2 minutes)."""
        course_id = uuid4()
        chapter_info = {
            "sequence_number": 1,
            "title": "Performance Test Chapter",
            "learning_objectives": ["Learn performance testing"],
            "estimated_duration": "PT2H",
            "complexity_level": 2.0
        }
        
        start_time = datetime.utcnow()
        
        chapter = await service._generate_single_chapter(
            course_id=course_id,
            course_data=sample_course_data,
            chapter_info=chapter_info,
            mode=GenerationMode.FAST,
            previous_concepts=[]
        )
        
        generation_time = datetime.utcnow() - start_time
        
        # Verify performance requirement (<2 minutes)
        assert generation_time.total_seconds() < 120
        assert chapter.sequence_number == 1
        assert chapter.title == "Performance Test Chapter"
    
    @pytest.mark.asyncio
    async def test_error_handling_ai_failure(self, service, sample_course_data):
        """Test error handling when AI service fails."""
        # Make AI client fail
        service.ai_client.generate_course_structure.side_effect = Exception("AI service unavailable")
        
        request = CourseGenerationRequest(
            course_data=sample_course_data,
            generation_mode=GenerationMode.BALANCED
        )
        
        with pytest.raises(RuntimeError, match="Course generation failed"):
            await service.create_course(request)
    
    @pytest.mark.asyncio
    async def test_error_handling_vector_failure(self, service, sample_course_data):
        """Test error handling when vector database fails."""
        # Make vector client fail
        service.vector_client.store_course_embeddings.side_effect = Exception("Vector DB unavailable")
        
        request = CourseGenerationRequest(
            course_data=sample_course_data,
            generation_mode=GenerationMode.BALANCED
        )
        
        # Should continue despite vector storage failure
        result = await service.create_course(request)
        assert result.vector_embeddings_stored == 0  # Failed storage
    
    @pytest.mark.asyncio
    async def test_chapter_fallback_creation(self, service):
        """Test fallback chapter creation when AI generation fails."""
        course_id = uuid4()
        chapter_info = {
            "title": "Failed Chapter",
            "learning_objectives": ["Fallback objective"],
            "estimated_duration": "PT1H",
            "complexity_level": 2.0,
            "sequence_number": 1
        }
        
        fallback_chapter = await service._create_fallback_chapter(
            course_id=course_id,
            chapter_info=chapter_info,
            sequence_number=1
        )
        
        assert fallback_chapter.title == "Failed Chapter"
        assert fallback_chapter.course_id == course_id
        assert fallback_chapter.sequence_number == 1
        assert len(fallback_chapter.subchapters) == 1
        assert fallback_chapter.subchapters[0].title == "Introduction"
    
    @pytest.mark.asyncio
    async def test_quality_threshold_validation(self, service):
        """Test quality threshold validation."""
        quality_metrics = QualityMetrics(
            readability_score=65.0,  # Below threshold
            pedagogical_alignment=0.75,  # Below threshold
            objective_coverage=0.95,
            content_accuracy=0.88,
            bias_detection_score=0.95,
            generation_timestamp=datetime.utcnow()
        )
        
        thresholds = {
            "readability_score": 70.0,
            "pedagogical_alignment": 0.8,
            "content_accuracy": 0.85,
            "bias_detection_score": 0.9
        }
        
        # Should log warnings but not raise exceptions
        service._validate_quality_thresholds(quality_metrics, thresholds)
    
    @pytest.mark.asyncio
    async def test_async_course_creation(self, service, sample_course_data):
        """Test asynchronous course creation with background tasks."""
        request = CourseGenerationRequest(
            course_data=sample_course_data,
            generation_mode=GenerationMode.BALANCED
        )
        
        with patch('src.services.course_generation_service.generate_course_task') as mock_task:
            mock_task.delay.return_value.id = "test-task-id"
            
            task_id = await service.create_course_async(request)
            
            assert task_id == "test-task-id"
            mock_task.delay.assert_called_once_with(
                course_data=sample_course_data.dict(),
                user_preferences=None
            )
    
    def test_duration_parsing(self, service):
        """Test duration parsing utilities."""
        # Test hours parsing
        assert service._parse_duration_to_hours("PT5H") == 5.0
        assert service._parse_duration_to_hours("PT120M") == 2.0
        assert service._parse_duration_to_hours("invalid") == 1.0  # Default
        
        # Test minutes parsing
        assert service._parse_duration_to_minutes("PT2H") == 120
        assert service._parse_duration_to_minutes("PT30M") == 30
    
    def test_service_factory(self):
        """Test service factory function."""
        service = create_course_generation_service()
        
        assert isinstance(service, CourseGenerationService)
        assert service.ai_client is not None
        assert service.vector_client is not None


class TestCourseGenerationModels:
    """Test cases for course generation request/response models."""
    
    def test_course_generation_request_validation(self):
        """Test request model validation."""
        course_data = CourseCreate(
            title="Test Course",
            subject_domain="Testing",
            target_audience=TargetAudience(
                proficiency_level=ProficiencyLevel.BEGINNER
            ),
            learning_objectives=["Learn", "Understand", "Apply"],
            estimated_duration="PT10H",
            difficulty_score=2.0
        )
        
        # Valid request
        request = CourseGenerationRequest(
            course_data=course_data,
            generation_mode=GenerationMode.BALANCED,
            generation_strategy=GenerationStrategy.PARALLEL
        )
        
        assert request.generation_mode == GenerationMode.BALANCED
        assert request.generation_strategy == GenerationStrategy.PARALLEL
    
    def test_quality_thresholds_validation(self):
        """Test quality thresholds validation."""
        course_data = CourseCreate(
            title="Test Course",
            subject_domain="Testing",
            target_audience=TargetAudience(
                proficiency_level=ProficiencyLevel.BEGINNER
            ),
            learning_objectives=["Learn", "Understand", "Apply"],
            estimated_duration="PT10H",
            difficulty_score=2.0
        )
        
        # Valid thresholds
        valid_request = CourseGenerationRequest(
            course_data=course_data,
            quality_thresholds={
                "readability_score": 0.8,
                "pedagogical_alignment": 0.9
            }
        )
        assert valid_request.quality_thresholds["readability_score"] == 0.8
        
        # Invalid threshold values
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            CourseGenerationRequest(
                course_data=course_data,
                quality_thresholds={"readability_score": 1.5}  # Invalid
            )
        
        # Invalid threshold keys
        with pytest.raises(ValueError, match="Invalid quality threshold key"):
            CourseGenerationRequest(
                course_data=course_data,
                quality_thresholds={"invalid_key": 0.8}  # Invalid key
            )


@pytest.mark.integration
class TestCourseGenerationIntegration:
    """Integration tests for course generation service."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_course_generation(self):
        """Test complete end-to-end course generation."""
        # This would be an integration test with real AI and vector clients
        # For now, we'll use mocks but structure for real integration
        
        with patch('src.services.course_generation_service.create_ai_client') as mock_ai:
            with patch('src.services.course_generation_service.VectorDatabaseClient') as mock_vector:
                service = create_course_generation_service()
                
                course_data = CourseCreate(
                    title="Integration Test Course",
                    subject_domain="Integration Testing",
                    target_audience=TargetAudience(
                        proficiency_level=ProficiencyLevel.INTERMEDIATE
                    ),
                    learning_objectives=[
                        "Learn integration testing",
                        "Understand system interactions",
                        "Master testing strategies"
                    ],
                    estimated_duration="PT15H",
                    difficulty_score=3.0
                )
                
                request = CourseGenerationRequest(
                    course_data=course_data,
                    generation_mode=GenerationMode.PREMIUM,
                    generation_strategy=GenerationStrategy.HYBRID
                )
                
                # Would call real service in actual integration test
                # result = await service.create_course(request)
                # assert result.status == CourseStatus.READY
                # assert len(result.chapters) > 0
                
                # For now, just verify the service is properly configured
                assert service is not None
                assert hasattr(service, 'ai_client')
                assert hasattr(service, 'vector_client')