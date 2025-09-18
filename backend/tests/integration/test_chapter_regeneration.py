"""
Integration tests for chapter regeneration service.

Tests the complete chapter regeneration workflow including:
- AI integration for content improvement
- Quality validation and analysis
- Database operations and consistency
- Error handling and recovery
- Performance under various scenarios
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from sqlalchemy.orm import Session

from src.services.chapter_service import (
    ChapterRegenerationService,
    ChapterRegenerationRequest,
    RegenerationScope,
    RegenerationReason,
    QualityAnalysisResult,
    create_chapter_service
)
from src.models.chapter import (
    Chapter,
    ChapterTable,
    Subchapter,
    SubchapterTable,
    ContentBlock
)
from src.models.course import CourseTable, TargetAudience
from src.models.enums import ProficiencyLevel, ContentType, BlockType, CourseStatus
from src.integrations.ai_client import (
    AIClient,
    ChapterContentResponse,
    ContentQualityResponse,
    ReadabilityAnalysisResponse,
    BiasDetectionResponse
)


class TestChapterRegenerationIntegration:
    """Integration tests for chapter regeneration service."""
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client with realistic responses."""
        ai_client = Mock(spec=AIClient)
        ai_client.preferred_provider = "openai"
        
        # Mock chapter content generation
        ai_client.generate_chapter_content = AsyncMock(return_value=ChapterContentResponse(
            content_blocks=[
                {
                    "type": "text",
                    "content": "Improved content with better explanations and examples.",
                    "order": 1
                },
                {
                    "type": "code",
                    "content": "# Example code with clear comments\nprint('Hello, World!')",
                    "order": 2
                }
            ],
            key_concepts=["improved concept 1", "enhanced concept 2"],
            examples=[
                {
                    "title": "Practical Example",
                    "description": "Clear demonstration of concept",
                    "code_or_content": "example code"
                }
            ],
            exercises=[
                {
                    "title": "Practice Exercise",
                    "description": "Hands-on practice",
                    "difficulty": "medium",
                    "estimated_time": 15
                }
            ],
            summary="Comprehensive summary of improved chapter content",
            estimated_reading_time=45,
            complexity_score=2.5
        ))
        
        # Mock comprehensive quality check
        ai_client.comprehensive_quality_check = AsyncMock(return_value={
            "ai_quality_assessment": {
                "overall_score": 0.85,
                "pedagogical_alignment": 0.9,
                "objective_coverage": 0.95,
                "content_accuracy": 0.9,
                "recommendations": ["Great improvement in clarity"]
            },
            "readability_analysis": {
                "flesch_reading_ease": 75.0,
                "meets_target_level": True,
                "recommendations": []
            },
            "bias_detection": {
                "overall_bias_score": 0.1,
                "severity_level": "low",
                "recommendations": []
            },
            "overall_quality_score": 0.85,
            "meets_quality_standards": True
        })
        
        return ai_client
    
    @pytest.fixture
    def sample_course(self, db_session: Session):
        """Create a sample course for testing."""
        course = CourseTable(
            id=uuid4(),
            title="Test Course",
            subject_domain="Programming",
            learning_objectives=["Learn programming basics", "Understand syntax"],
            estimated_duration="PT20H",
            difficulty_score=2.0,
            target_audience={
                "proficiency_level": "beginner",
                "prerequisites": [],
                "learning_preferences": ["visual"]
            },
            status=CourseStatus.DRAFT
        )
        db_session.add(course)
        db_session.commit()
        return course
    
    @pytest.fixture
    def sample_chapter(self, db_session: Session, sample_course):
        """Create a sample chapter for testing."""
        chapter = ChapterTable(
            id=uuid4(),
            course_id=sample_course.id,
            sequence_number=1,
            title="Introduction to Programming",
            learning_objectives=["Understand basic concepts", "Write first program"],
            estimated_duration="PT2H",
            complexity_level=2.0,
            prerequisites=["Basic computer knowledge"],
            content_outline="Basic introduction to programming concepts and syntax"
        )
        db_session.add(chapter)
        
        # Add subchapters
        subchapter = SubchapterTable(
            id=uuid4(),
            chapter_id=chapter.id,
            sequence_number=1,
            title="What is Programming?",
            content_type=ContentType.THEORY,
            content_blocks=[
                {
                    "type": "text",
                    "content": "Programming is the process of creating instructions for computers.",
                    "order": 1,
                    "metadata": {}
                }
            ],
            key_concepts=["programming", "instructions", "computers"],
            summary="Introduction to the concept of programming"
        )
        db_session.add(subchapter)
        db_session.commit()
        return chapter
    
    @pytest.fixture
    def regeneration_service(self, mock_ai_client):
        """Create chapter regeneration service with mocked AI client."""
        return ChapterRegenerationService(ai_client=mock_ai_client)
    
    @pytest.mark.asyncio
    async def test_complete_chapter_regeneration_workflow(
        self,
        regeneration_service,
        sample_chapter,
        db_session: Session
    ):
        """Test complete chapter regeneration workflow from request to completion."""
        # Create regeneration request
        request = ChapterRegenerationRequest(
            chapter_id=sample_chapter.id,
            regeneration_reason="Content is too advanced for beginner level students",
            scope=RegenerationScope(
                regenerate_full_chapter=True,
                preserve_structure=True,
                preserve_examples=True
            ),
            target_quality_score=0.85,
            user_feedback="Students are struggling with technical terms"
        )
        
        # Execute regeneration
        response = await regeneration_service.regenerate_chapter(request, db_session)
        
        # Verify response structure
        assert response.task_id is not None
        assert response.chapter_id == sample_chapter.id
        assert response.current_status == "completed"
        assert response.quality_target == 0.85
        assert isinstance(response.estimated_completion_time, datetime)
        
        # Verify chapter was updated in database
        updated_chapter = db_session.query(ChapterTable).filter(
            ChapterTable.id == sample_chapter.id
        ).first()
        assert updated_chapter.updated_at > sample_chapter.updated_at
        
        # Verify regeneration history was recorded
        history = await regeneration_service.get_regeneration_history(sample_chapter.id)
        assert len(history) == 1
        assert history[0].chapter_id == sample_chapter.id
        assert history[0].quality_improvement > 0
    
    @pytest.mark.asyncio
    async def test_analyze_regeneration_need_categorization(self, regeneration_service):
        """Test regeneration need analysis and categorization."""
        # Test different types of regeneration reasons
        test_cases = [
            {
                "reason": "Content is too difficult for beginners",
                "expected_category": "difficulty",
                "expected_severity": "medium"
            },
            {
                "reason": "Explanations are unclear and confusing",
                "expected_category": "clarity", 
                "expected_severity": "medium"
            },
            {
                "reason": "There are factual errors in the examples",
                "expected_category": "accuracy",
                "expected_severity": "high"
            },
            {
                "reason": "Content contains biased language",
                "expected_category": "bias",
                "expected_severity": "high"
            }
        ]
        
        for case in test_cases:
            # Create mock chapter
            chapter = Chapter(
                id=uuid4(),
                course_id=uuid4(),
                sequence_number=1,
                title="Test Chapter",
                learning_objectives=["Test objective"],
                estimated_duration="PT1H",
                complexity_level=2.0,
                prerequisites=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Analyze regeneration need
            result = await regeneration_service.analyze_regeneration_need(
                chapter, case["reason"]
            )
            
            # Verify categorization
            assert result.category == case["expected_category"]
            assert result.severity == case["expected_severity"]
            assert len(result.specific_issues) > 0
            assert len(result.target_improvements) > 0
    
    @pytest.mark.asyncio
    async def test_partial_chapter_regeneration(
        self,
        regeneration_service,
        sample_chapter,
        db_session: Session
    ):
        """Test partial chapter regeneration targeting specific subchapters."""
        # Get subchapter ID
        subchapter = db_session.query(SubchapterTable).filter(
            SubchapterTable.chapter_id == sample_chapter.id
        ).first()
        
        # Create request for partial regeneration
        request = ChapterRegenerationRequest(
            chapter_id=sample_chapter.id,
            regeneration_reason="First section needs more examples",
            scope=RegenerationScope(
                regenerate_full_chapter=False,
                target_subchapters=[subchapter.id],
                preserve_structure=True,
                preserve_examples=False
            )
        )
        
        # Execute regeneration
        response = await regeneration_service.regenerate_chapter(request, db_session)
        
        # Verify partial regeneration was applied
        assert response.regeneration_scope.regenerate_full_chapter == False
        assert len(response.regeneration_scope.target_subchapters) == 1
        assert response.current_status == "completed"
    
    @pytest.mark.asyncio
    async def test_quality_validation_comprehensive(self, regeneration_service):
        """Test comprehensive quality validation of regenerated content."""
        # Create test content
        content = {
            "title": "Advanced Programming Concepts",
            "content": "This chapter covers complex algorithmic thinking and data structures.",
            "subchapters": [
                {
                    "title": "Algorithms",
                    "content_blocks": [
                        {
                            "type": "text",
                            "content": "An algorithm is a step-by-step procedure for solving problems."
                        }
                    ],
                    "summary": "Introduction to algorithmic thinking"
                }
            ]
        }
        
        # Create target audience
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=["Basic programming knowledge"],
            learning_preferences=["visual"]
        )
        
        learning_objectives = ["Understand algorithms", "Apply problem-solving techniques"]
        
        # Validate content quality
        result = await regeneration_service.validate_regenerated_content(
            content, target_audience, learning_objectives
        )
        
        # Verify quality analysis
        assert isinstance(result, QualityAnalysisResult)
        assert 0.0 <= result.overall_score <= 1.0
        assert 0.0 <= result.readability_score <= 100.0
        assert 0.0 <= result.pedagogical_alignment <= 1.0
        assert 0.0 <= result.objective_coverage <= 1.0
        assert 0.0 <= result.content_accuracy <= 1.0
        assert 0.0 <= result.bias_score <= 1.0
        assert isinstance(result.meets_quality_standards, bool)
        assert isinstance(result.improvement_recommendations, list)
        assert isinstance(result.critical_issues, list)
    
    @pytest.mark.asyncio
    async def test_preserve_chapter_structure(self, regeneration_service):
        """Test structure preservation during regeneration."""
        # Create original chapter
        original_chapter = Chapter(
            id=uuid4(),
            course_id=uuid4(),
            sequence_number=3,
            title="Original Title",
            learning_objectives=["Original objective 1", "Original objective 2"],
            estimated_duration="PT2H",
            complexity_level=3.0,
            prerequisites=["Original prereq"],
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Create new content
        new_content = {
            "title": "New Title",
            "learning_objectives": ["New objective"],
            "complexity_level": 4.5,
            "content_outline": "New outline"
        }
        
        # Preserve structure
        preserved_content = await regeneration_service.preserve_chapter_structure(
            original_chapter, new_content
        )
        
        # Verify preservation
        assert preserved_content["learning_objectives"] == original_chapter.learning_objectives
        assert preserved_content["sequence_number"] == original_chapter.sequence_number
        assert preserved_content["id"] == original_chapter.id
        assert preserved_content["course_id"] == original_chapter.course_id
        assert preserved_content["created_at"] == original_chapter.created_at
        
        # Verify complexity level is clamped
        assert 1.0 <= preserved_content["complexity_level"] <= 5.0
    
    @pytest.mark.asyncio
    async def test_regeneration_history_tracking(self, regeneration_service):
        """Test regeneration history tracking and retrieval."""
        chapter_id = uuid4()
        
        # Create regeneration reason
        reason = RegenerationReason(
            category="clarity",
            description="Content needs clearer explanations",
            severity="medium",
            specific_issues=["Complex terminology"],
            target_improvements=["Simplify language"]
        )
        
        # Create scope
        scope = RegenerationScope(regenerate_full_chapter=True)
        
        # Track history
        with patch('src.services.chapter_service.Session') as mock_session:
            history_record = await regeneration_service.track_regeneration_history(
                chapter_id=chapter_id,
                regeneration_reason=reason,
                scope=scope,
                original_quality=0.6,
                new_quality=0.85,
                processing_time=45.0,
                db=mock_session
            )
        
        # Verify history record
        assert history_record.chapter_id == chapter_id
        assert history_record.regeneration_reason.category == "clarity"
        assert history_record.quality_improvement == 0.25
        assert history_record.processing_time_seconds == 45.0
        assert history_record.ai_provider_used == "openai"
        
        # Test history retrieval
        retrieved_history = await regeneration_service.get_regeneration_history(chapter_id)
        assert len(retrieved_history) == 1
        assert retrieved_history[0].chapter_id == chapter_id
        
        # Test global history retrieval
        all_history = await regeneration_service.get_regeneration_history()
        assert len(all_history) >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling_chapter_not_found(
        self,
        regeneration_service,
        db_session: Session
    ):
        """Test error handling when chapter is not found."""
        non_existent_id = uuid4()
        
        request = ChapterRegenerationRequest(
            chapter_id=non_existent_id,
            regeneration_reason="Test reason"
        )
        
        # Should raise error for non-existent chapter
        with pytest.raises(RuntimeError, match="Chapter regeneration failed"):
            await regeneration_service.regenerate_chapter(request, db_session)
    
    @pytest.mark.asyncio
    async def test_error_handling_ai_client_failure(
        self,
        sample_chapter,
        db_session: Session
    ):
        """Test error handling when AI client fails."""
        # Create service with failing AI client
        failing_ai_client = Mock(spec=AIClient)
        failing_ai_client.generate_chapter_content = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )
        failing_ai_client.comprehensive_quality_check = AsyncMock(
            side_effect=Exception("Quality check failed")
        )
        
        failing_service = ChapterRegenerationService(ai_client=failing_ai_client)
        
        request = ChapterRegenerationRequest(
            chapter_id=sample_chapter.id,
            regeneration_reason="Test reason"
        )
        
        # Should handle AI failure gracefully
        with pytest.raises(RuntimeError):
            await regeneration_service.regenerate_chapter(request, db_session)
    
    @pytest.mark.asyncio
    async def test_concurrent_regeneration_requests(
        self,
        regeneration_service,
        sample_chapter,
        db_session: Session
    ):
        """Test handling of concurrent regeneration requests."""
        # Create multiple requests
        requests = [
            ChapterRegenerationRequest(
                chapter_id=sample_chapter.id,
                regeneration_reason=f"Reason {i}",
                priority="medium"
            )
            for i in range(3)
        ]
        
        # Execute concurrently
        tasks = [
            regeneration_service.regenerate_chapter(request, db_session)
            for request in requests
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all completed successfully or handled gracefully
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 1  # At least one should succeed
        
        # Check that history records multiple regenerations
        history = await regeneration_service.get_regeneration_history(sample_chapter.id)
        assert len(history) >= 1
    
    @pytest.mark.asyncio
    async def test_quality_threshold_enforcement(self, regeneration_service):
        """Test that quality thresholds are properly enforced."""
        # Mock AI client to return low quality content
        low_quality_ai = Mock(spec=AIClient)
        low_quality_ai.comprehensive_quality_check = AsyncMock(return_value={
            "ai_quality_assessment": {
                "overall_score": 0.4,  # Below threshold
                "pedagogical_alignment": 0.5,
                "objective_coverage": 0.6,
                "content_accuracy": 0.3,
                "recommendations": ["Significant improvement needed"]
            },
            "readability_analysis": {
                "flesch_reading_ease": 30.0,  # Poor readability
                "meets_target_level": False,
                "recommendations": ["Simplify language"]
            },
            "bias_detection": {
                "overall_bias_score": 0.5,  # High bias
                "severity_level": "high",
                "recommendations": ["Remove biased content"]
            },
            "overall_quality_score": 0.4,
            "meets_quality_standards": False
        })
        
        low_quality_service = ChapterRegenerationService(ai_client=low_quality_ai)
        
        # Test quality validation
        content = {"content": "Low quality content with bias and errors"}
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[]
        )
        
        result = await low_quality_service.validate_regenerated_content(
            content, target_audience, ["Test objective"]
        )
        
        # Verify quality issues are detected
        assert result.overall_score < 0.8  # Below quality threshold
        assert not result.meets_quality_standards
        assert len(result.critical_issues) > 0
        assert len(result.improvement_recommendations) > 0
    
    def test_service_factory_creation(self):
        """Test factory function for creating chapter service."""
        service = create_chapter_service()
        assert isinstance(service, ChapterRegenerationService)
        assert service.ai_client is not None
        assert service.quality_threshold == 0.8
        
        # Test with custom AI client
        custom_ai = Mock(spec=AIClient)
        custom_service = create_chapter_service(custom_ai)
        assert custom_service.ai_client == custom_ai


@pytest.mark.integration
class TestChapterRegenerationPerformance:
    """Performance tests for chapter regeneration service."""
    
    @pytest.mark.asyncio
    async def test_regeneration_performance_large_chapter(
        self,
        regeneration_service,
        db_session: Session
    ):
        """Test regeneration performance with large chapter content."""
        # Create large chapter with multiple subchapters
        course = CourseTable(
            id=uuid4(),
            title="Large Course",
            subject_domain="Computer Science", 
            learning_objectives=["Comprehensive understanding"],
            estimated_duration="PT40H",
            difficulty_score=3.0,
            target_audience={
                "proficiency_level": "intermediate",
                "prerequisites": [],
                "learning_preferences": ["visual", "kinesthetic"]
            },
            status=CourseStatus.DRAFT
        )
        db_session.add(course)
        
        chapter = ChapterTable(
            id=uuid4(),
            course_id=course.id,
            sequence_number=1,
            title="Large Chapter",
            learning_objectives=["Multiple objectives"] * 5,
            estimated_duration="PT4H",
            complexity_level=3.0,
            prerequisites=[],
            content_outline="Large chapter with extensive content"
        )
        db_session.add(chapter)
        
        # Add multiple subchapters
        for i in range(10):  # 10 subchapters
            subchapter = SubchapterTable(
                id=uuid4(),
                chapter_id=chapter.id,
                sequence_number=i + 1,
                title=f"Subchapter {i + 1}",
                content_type=ContentType.MIXED,
                content_blocks=[{
                    "type": "text",
                    "content": f"Large content block {j} with detailed explanation " * 20,
                    "order": j + 1,
                    "metadata": {}
                } for j in range(5)],  # 5 content blocks per subchapter
                key_concepts=[f"concept_{i}_{j}" for j in range(10)],
                summary=f"Summary for subchapter {i + 1} with comprehensive overview"
            )
            db_session.add(subchapter)
        
        db_session.commit()
        
        # Measure regeneration performance
        start_time = datetime.utcnow()
        
        request = ChapterRegenerationRequest(
            chapter_id=chapter.id,
            regeneration_reason="Large chapter needs optimization for better learning flow"
        )
        
        response = await regeneration_service.regenerate_chapter(request, db_session)
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify performance is reasonable (should complete within 2 minutes for testing)
        assert processing_time < 120  # 2 minutes
        assert response.current_status == "completed"
        
        # Verify all subchapters were processed
        history = await regeneration_service.get_regeneration_history(chapter.id)
        assert len(history) == 1
        assert history[0].processing_time_seconds < 120
    
    @pytest.mark.asyncio
    async def test_memory_usage_multiple_regenerations(
        self,
        regeneration_service,
        sample_chapter,
        db_session: Session
    ):
        """Test memory usage doesn't grow excessively with multiple regenerations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple regenerations
        for i in range(5):
            request = ChapterRegenerationRequest(
                chapter_id=sample_chapter.id,
                regeneration_reason=f"Iteration {i} improvement"
            )
            
            await regeneration_service.regenerate_chapter(request, db_session)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for test)
        assert memory_increase < 100
        
        # Verify history is properly managed
        history = await regeneration_service.get_regeneration_history(sample_chapter.id)
        assert len(history) == 5  # All regenerations tracked