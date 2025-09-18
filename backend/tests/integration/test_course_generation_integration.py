"""
Integration tests for the course generation service.

Tests real integration with AI client, vector database, and background tasks
to ensure the complete workflow functions correctly.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from src.services.course_generation_service import (
    CourseGenerationService,
    CourseGenerationRequest,
    GenerationMode,
    GenerationStrategy,
    create_course_generation_service
)
from src.models.course import CourseCreate, TargetAudience
from src.models.enums import ProficiencyLevel, LearningPreference
from src.integrations.ai_client import create_ai_client
from src.integrations.vector_client import (
    create_vector_client,
    VectorConfig,
    VectorBackend
)


@pytest.mark.integration
class TestCourseGenerationIntegration:
    """Integration tests for course generation service."""
    
    @pytest.fixture
    def sample_course_data(self):
        """Sample course data for integration testing."""
        return CourseCreate(
            title="Integration Test Course: Python Programming",
            description="A comprehensive course for learning Python programming",
            subject_domain="Programming",
            target_audience=TargetAudience(
                proficiency_level=ProficiencyLevel.BEGINNER,
                prerequisites=["Basic computer skills"],
                learning_preferences=[LearningPreference.VISUAL, LearningPreference.KINESTHETIC]
            ),
            learning_objectives=[
                "Understand Python syntax and basic concepts",
                "Learn to write simple Python programs",
                "Master basic data structures and control flow",
                "Apply Python to solve real-world problems"
            ],
            estimated_duration="PT25H",
            difficulty_score=2.0,
            language="en",
            version="1.0.0"
        )
    
    @pytest.fixture
    async def real_ai_client(self):
        """Real AI client for integration testing."""
        # Note: This would use real API keys in actual integration tests
        # For CI/CD, we might use mock keys or skip these tests
        return create_ai_client(
            openai_api_key="test-key",  # Would be real key in integration env
            preferred_provider="openai"
        )
    
    @pytest.fixture
    async def real_vector_client(self):
        """Real vector client for integration testing."""
        # Using Chroma for integration tests (easier to set up)
        vector_client = create_vector_client(
            backend="chroma",
            chroma_host="localhost",
            chroma_port=8000
        )
        await vector_client.connect()
        yield vector_client
        await vector_client.disconnect()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_course_generation_workflow(self, sample_course_data):
        """Test the complete course generation workflow with mocked external services."""
        # Mock external services for reliable testing
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_openai:
            with patch('src.integrations.vector_client.ChromaVectorClient') as mock_chroma:
                
                # Configure mocks to simulate successful responses
                mock_ai_instance = mock_openai.return_value
                mock_ai_instance.generate_course_structure.return_value = {
                    "chapters": [
                        {
                            "sequence_number": 1,
                            "title": "Python Basics",
                            "learning_objectives": ["Learn Python syntax", "Understand variables"],
                            "estimated_duration": "PT5H",
                            "complexity_level": 1.5,
                            "prerequisites": [],
                            "content_outline": "Introduction to Python programming"
                        },
                        {
                            "sequence_number": 2,
                            "title": "Data Structures",
                            "learning_objectives": ["Master lists and dictionaries", "Use data structures"],
                            "estimated_duration": "PT8H",
                            "complexity_level": 2.0,
                            "prerequisites": ["Python syntax"],
                            "content_outline": "Working with Python data structures"
                        },
                        {
                            "sequence_number": 3,
                            "title": "Control Flow",
                            "learning_objectives": ["Understand conditionals", "Master loops"],
                            "estimated_duration": "PT6H",
                            "complexity_level": 2.5,
                            "prerequisites": ["Data structures"],
                            "content_outline": "Control flow in Python"
                        }
                    ],
                    "estimated_total_duration": 19.0,
                    "difficulty_progression": [1.5, 2.0, 2.5],
                    "suggested_prerequisites": ["Basic computer skills"],
                    "learning_path_rationale": "Progressive complexity from basics to advanced concepts",
                    "quality_indicators": {"progression_smoothness": 0.95, "objective_coverage": 1.0}
                }
                
                mock_ai_instance.generate_chapter_content.return_value = {
                    "content_blocks": [
                        {
                            "type": "text",
                            "content": "This chapter introduces Python programming fundamentals...",
                            "order": 1
                        },
                        {
                            "type": "code",
                            "content": "print('Hello, World!')",
                            "order": 2
                        }
                    ],
                    "key_concepts": ["Variables", "Data Types", "Print Function"],
                    "examples": [
                        {
                            "title": "Hello World Example",
                            "description": "Your first Python program",
                            "code_or_content": "print('Hello, World!')"
                        }
                    ],
                    "exercises": [
                        {
                            "title": "Variable Assignment",
                            "description": "Create variables and assign values",
                            "difficulty": "easy",
                            "estimated_time": 10
                        }
                    ],
                    "summary": "Introduction to Python basics including syntax and variables",
                    "estimated_reading_time": 45,
                    "complexity_score": 1.5
                }
                
                mock_ai_instance.comprehensive_quality_check.return_value = {
                    "ai_quality_assessment": {
                        "overall_score": 0.88,
                        "pedagogical_alignment": 0.92,
                        "objective_coverage": 0.95,
                        "content_accuracy": 0.89
                    },
                    "readability_analysis": {
                        "flesch_reading_ease": 78.5,
                        "meets_target_level": True
                    },
                    "bias_detection": {
                        "overall_bias_score": 0.05,
                        "severity_level": "low"
                    },
                    "overall_quality_score": 0.87,
                    "meets_quality_standards": True
                }
                
                # Configure vector client mock
                mock_vector_instance = mock_chroma.return_value
                mock_vector_instance.connect.return_value = None
                mock_vector_instance.disconnect.return_value = None
                mock_vector_instance.store_course_embeddings.return_value = True
                
                # Create service and test
                service = create_course_generation_service()
                
                request = CourseGenerationRequest(
                    course_data=sample_course_data,
                    generation_mode=GenerationMode.BALANCED,
                    generation_strategy=GenerationStrategy.HYBRID,
                    quality_thresholds={
                        "readability_score": 70.0,
                        "pedagogical_alignment": 0.85,
                        "content_accuracy": 0.80,
                        "bias_detection_score": 0.90
                    }
                )
                
                # Execute course generation
                start_time = datetime.utcnow()
                result = await service.create_course(request)
                generation_time = datetime.utcnow() - start_time
                
                # Verify results
                assert result.status.value == "ready"
                assert len(result.chapters) == 3
                assert result.quality_metrics.readability_score >= 70.0
                assert result.quality_metrics.pedagogical_alignment >= 0.85
                assert result.vector_embeddings_stored > 0
                
                # Verify performance requirements
                assert generation_time.total_seconds() < 600  # 10 minutes max for full course
                
                # Verify generation metadata
                metadata = result.generation_metadata
                assert metadata["generation_mode"] == GenerationMode.BALANCED
                assert metadata["generation_strategy"] == GenerationStrategy.HYBRID
                assert metadata["total_chapters"] == 3
                assert "ai_provider" in metadata
                assert "vector_backend" in metadata
                
                # Verify chapters have proper structure
                for i, chapter_data in enumerate(result.chapters):
                    assert chapter_data["sequence_number"] == i + 1
                    assert "title" in chapter_data
                    assert "learning_objectives" in chapter_data
                    assert "subchapters" in chapter_data
                    assert len(chapter_data["subchapters"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_parallel_chapter_generation_performance(self, sample_course_data):
        """Test that parallel chapter generation meets performance requirements."""
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_openai:
            
            # Simulate realistic AI response times
            async def mock_generate_content(*args, **kwargs):
                await asyncio.sleep(0.5)  # Simulate AI processing time
                return {
                    "content_blocks": [{"type": "text", "content": "Content", "order": 1}],
                    "key_concepts": ["Concept"],
                    "examples": [],
                    "exercises": [],
                    "summary": "Summary",
                    "estimated_reading_time": 30,
                    "complexity_score": 2.0
                }
            
            mock_ai_instance = mock_openai.return_value
            mock_ai_instance.generate_chapter_content.side_effect = mock_generate_content
            
            service = create_course_generation_service()
            
            # Create chapter structure for testing
            chapter_structure = [
                {
                    "sequence_number": i,
                    "title": f"Chapter {i}",
                    "learning_objectives": [f"Learn topic {i}"],
                    "estimated_duration": "PT2H",
                    "complexity_level": 2.0
                }
                for i in range(1, 6)  # 5 chapters
            ]
            
            # Test parallel generation
            start_time = datetime.utcnow()
            chapters = await service.generate_chapters(
                course_id=uuid4(),
                course_data=sample_course_data,
                chapter_structure=chapter_structure,
                strategy=GenerationStrategy.PARALLEL,
                mode=GenerationMode.FAST
            )
            parallel_time = datetime.utcnow() - start_time
            
            # Test sequential generation for comparison
            start_time = datetime.utcnow()
            chapters_seq = await service.generate_chapters(
                course_id=uuid4(),
                course_data=sample_course_data,
                chapter_structure=chapter_structure,
                strategy=GenerationStrategy.SEQUENTIAL,
                mode=GenerationMode.FAST
            )
            sequential_time = datetime.utcnow() - start_time
            
            # Verify results
            assert len(chapters) == 5
            assert len(chapters_seq) == 5
            
            # Parallel should be significantly faster
            assert parallel_time.total_seconds() < sequential_time.total_seconds()
            
            # Each chapter should be generated in <2 minutes (requirement)
            average_time_per_chapter = parallel_time.total_seconds() / 5
            assert average_time_per_chapter < 120  # 2 minutes
    
    @pytest.mark.asyncio
    async def test_vector_database_integration(self, sample_course_data):
        """Test integration with vector database for content storage and retrieval."""
        with patch('src.integrations.vector_client.ChromaVectorClient') as mock_chroma:
            
            # Configure vector client mock
            mock_instance = mock_chroma.return_value
            mock_instance.connect.return_value = None
            mock_instance.disconnect.return_value = None
            mock_instance.store_course_embeddings.return_value = True
            mock_instance.search_similar_content.return_value = []
            mock_instance.get_content_by_id.return_value = None
            
            service = create_course_generation_service()
            
            # Test vector storage during course creation
            course_id = uuid4()
            chapters = []  # Mock chapters for testing
            
            embeddings_count = await service._store_course_vectors(course_id, chapters)
            
            # Verify vector client interactions
            mock_instance.connect.assert_called_once()
            mock_instance.store_course_embeddings.assert_called_once()
            
            # Test vector search functionality
            search_results = await service.vector_client.search_similar_content(
                query_text="Python programming basics",
                limit=5
            )
            
            mock_instance.search_similar_content.assert_called()
            assert isinstance(search_results, list)
    
    @pytest.mark.asyncio
    async def test_quality_validation_integration(self, sample_course_data):
        """Test integration of quality validation across all content."""
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_openai:
            
            # Mock quality validation responses
            mock_ai_instance = mock_openai.return_value
            mock_ai_instance.comprehensive_quality_check.return_value = {
                "ai_quality_assessment": {
                    "overall_score": 0.85,
                    "pedagogical_alignment": 0.90,
                    "objective_coverage": 0.95,
                    "content_accuracy": 0.88
                },
                "readability_analysis": {
                    "flesch_reading_ease": 75.0,
                    "grade_level": "Grade 8",
                    "meets_target_level": True
                },
                "bias_detection": {
                    "overall_bias_score": 0.1,
                    "severity_level": "low",
                    "detected_issues": []
                },
                "overall_quality_score": 0.86,
                "meets_quality_standards": True
            }
            
            service = create_course_generation_service()
            
            # Test quality validation
            chapters = []  # Mock chapters
            quality_thresholds = {
                "readability_score": 70.0,
                "pedagogical_alignment": 0.85,
                "content_accuracy": 0.80,
                "bias_detection_score": 0.90
            }
            
            quality_metrics = await service.validate_content_quality(
                course_id=uuid4(),
                course_data=sample_course_data,
                chapters=chapters,
                quality_thresholds=quality_thresholds
            )
            
            # Verify quality metrics
            assert quality_metrics.readability_score == 75.0
            assert quality_metrics.pedagogical_alignment == 0.90
            assert quality_metrics.content_accuracy == 0.88
            assert quality_metrics.bias_detection_score == 0.9  # 1.0 - 0.1
            
            # Verify AI client was called
            mock_ai_instance.comprehensive_quality_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_fallbacks(self, sample_course_data):
        """Test error recovery and fallback mechanisms."""
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_openai:
            
            # Configure AI client to fail on first chapter, succeed on others
            call_count = 0
            
            async def mock_generate_content(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("AI service temporarily unavailable")
                return {
                    "content_blocks": [{"type": "text", "content": "Content", "order": 1}],
                    "key_concepts": ["Concept"],
                    "examples": [],
                    "exercises": [],
                    "summary": "Summary",
                    "estimated_reading_time": 30,
                    "complexity_score": 2.0
                }
            
            mock_ai_instance = mock_openai.return_value
            mock_ai_instance.generate_chapter_content.side_effect = mock_generate_content
            
            service = create_course_generation_service()
            
            # Test chapter generation with failures
            chapter_structure = [
                {
                    "sequence_number": 1,
                    "title": "Chapter 1",
                    "learning_objectives": ["Learn topic 1"],
                    "estimated_duration": "PT2H",
                    "complexity_level": 2.0
                },
                {
                    "sequence_number": 2,
                    "title": "Chapter 2", 
                    "learning_objectives": ["Learn topic 2"],
                    "estimated_duration": "PT2H",
                    "complexity_level": 2.0
                }
            ]
            
            chapters = await service.generate_chapters(
                course_id=uuid4(),
                course_data=sample_course_data,
                chapter_structure=chapter_structure,
                strategy=GenerationStrategy.PARALLEL,
                mode=GenerationMode.BALANCED
            )
            
            # Verify both chapters were created (one fallback, one normal)
            assert len(chapters) == 2
            assert chapters[0].title == "Chapter 1"  # Fallback chapter
            assert chapters[1].title == "Chapter 2"  # Normal chapter
            
            # Verify fallback chapter has basic content
            assert len(chapters[0].subchapters) == 1
            assert chapters[0].subchapters[0].title == "Introduction"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_course_generation(self, sample_course_data):
        """Test concurrent generation of multiple courses."""
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_openai:
            with patch('src.integrations.vector_client.ChromaVectorClient') as mock_chroma:
                
                # Configure mocks for multiple concurrent requests
                mock_ai_instance = mock_openai.return_value
                mock_ai_instance.generate_course_structure.return_value = {
                    "chapters": [
                        {
                            "sequence_number": 1,
                            "title": "Test Chapter",
                            "learning_objectives": ["Learn something"],
                            "estimated_duration": "PT2H",
                            "complexity_level": 2.0,
                            "prerequisites": [],
                            "content_outline": "Test content"
                        }
                    ],
                    "estimated_total_duration": 2.0,
                    "difficulty_progression": [2.0],
                    "suggested_prerequisites": [],
                    "learning_path_rationale": "Simple test",
                    "quality_indicators": {"progression_smoothness": 1.0, "objective_coverage": 1.0}
                }
                
                async def mock_generate_content(*args, **kwargs):
                    await asyncio.sleep(0.1)  # Simulate processing
                    return {
                        "content_blocks": [{"type": "text", "content": "Content", "order": 1}],
                        "key_concepts": ["Concept"],
                        "examples": [],
                        "exercises": [],
                        "summary": "Summary",
                        "estimated_reading_time": 30,
                        "complexity_score": 2.0
                    }
                
                mock_ai_instance.generate_chapter_content.side_effect = mock_generate_content
                mock_ai_instance.comprehensive_quality_check.return_value = {
                    "ai_quality_assessment": {"overall_score": 0.85, "pedagogical_alignment": 0.9, "objective_coverage": 0.95, "content_accuracy": 0.88},
                    "readability_analysis": {"flesch_reading_ease": 75.0, "meets_target_level": True},
                    "bias_detection": {"overall_bias_score": 0.1, "severity_level": "low"},
                    "overall_quality_score": 0.86,
                    "meets_quality_standards": True
                }
                
                # Configure vector client
                mock_vector_instance = mock_chroma.return_value
                mock_vector_instance.connect.return_value = None
                mock_vector_instance.disconnect.return_value = None
                mock_vector_instance.store_course_embeddings.return_value = True
                
                # Create multiple course generation requests
                num_courses = 5
                tasks = []
                
                for i in range(num_courses):
                    course_data = CourseCreate(
                        title=f"Concurrent Test Course {i+1}",
                        subject_domain="Testing",
                        target_audience=TargetAudience(proficiency_level=ProficiencyLevel.BEGINNER),
                        learning_objectives=["Learn", "Understand", "Apply"],
                        estimated_duration="PT5H",
                        difficulty_score=2.0
                    )
                    
                    request = CourseGenerationRequest(
                        course_data=course_data,
                        generation_mode=GenerationMode.FAST,
                        generation_strategy=GenerationStrategy.PARALLEL
                    )
                    
                    service = create_course_generation_service()
                    task = service.create_course(request)
                    tasks.append(task)
                
                # Execute all course generations concurrently
                start_time = datetime.utcnow()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = datetime.utcnow() - start_time
                
                # Verify all courses were generated successfully
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) == num_courses
                
                # Verify concurrent performance
                average_time_per_course = total_time.total_seconds() / num_courses
                assert average_time_per_course < 60  # Should be much faster due to concurrency
                
                # Verify each result
                for result in successful_results:
                    assert result.status.value == "ready"
                    assert len(result.chapters) == 1
                    assert result.quality_metrics.readability_score >= 70.0