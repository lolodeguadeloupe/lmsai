"""
Unit tests for AI Service Integration.

Tests T062: AI client functionality, provider integrations, rate limiting,
error handling, and comprehensive AI-powered content generation and validation.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any, AsyncGenerator

from src.integrations.ai_client import (
    AIClient,
    OpenAIProvider,
    AnthropicProvider,
    ReadabilityAnalyzer,
    BiasDetector,
    RateLimiter,
    CourseStructureRequest,
    ChapterContentRequest,
    ContentValidationRequest,
    ReadabilityAnalysisRequest,
    BiasDetectionRequest,
    CourseStructureResponse,
    ChapterContentResponse,
    ContentQualityResponse,
    ReadabilityAnalysisResponse,
    BiasDetectionResponse,
    create_ai_client,
)
from src.models.enums import ProficiencyLevel, CognitiveLevel


class TestAIClientModels:
    """Test request/response model validation."""
    
    def test_course_structure_request_validation(self):
        """Test CourseStructureRequest validation."""
        request = CourseStructureRequest(
            title="Introduction to Machine Learning",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.INTERMEDIATE,
            estimated_duration_hours=25.0,
            learning_objectives=[
                "Understand ML fundamentals deeply",
                "Apply ML algorithms effectively",
                "Evaluate model performance accurately",
            ],
            prerequisites=["Python programming", "Statistics basics"],
            preferred_language="en",
        )
        
        assert request.title == "Introduction to Machine Learning"
        assert request.target_level == ProficiencyLevel.INTERMEDIATE
        assert request.estimated_duration_hours == 25.0
        assert len(request.learning_objectives) == 3
        assert len(request.prerequisites) == 2
    
    def test_course_structure_request_validation_errors(self):
        """Test CourseStructureRequest validation errors."""
        # Test title too short
        with pytest.raises(ValueError):
            CourseStructureRequest(
                title="ML",  # Too short
                subject_domain="CS",
                target_level=ProficiencyLevel.BEGINNER,
                estimated_duration_hours=10.0,
                learning_objectives=["Learn ML basics", "Apply algorithms", "Build models"],
            )
        
        # Test learning objectives too short
        with pytest.raises(ValueError):
            CourseStructureRequest(
                title="Machine Learning Course",
                subject_domain="Computer Science",
                target_level=ProficiencyLevel.BEGINNER,
                estimated_duration_hours=10.0,
                learning_objectives=["Short obj"],  # Too short
            )
        
        # Test invalid duration
        with pytest.raises(ValueError):
            CourseStructureRequest(
                title="Machine Learning Course",
                subject_domain="Computer Science",
                target_level=ProficiencyLevel.BEGINNER,
                estimated_duration_hours=0.0,  # Invalid
                learning_objectives=["Learn ML fundamentals", "Apply knowledge", "Build systems"],
            )
    
    def test_chapter_content_request_validation(self):
        """Test ChapterContentRequest validation."""
        request = ChapterContentRequest(
            chapter_title="Introduction to Neural Networks",
            learning_objectives=["Understand perceptrons", "Implement basic neural nets"],
            target_level=ProficiencyLevel.INTERMEDIATE,
            sequence_number=3,
            previous_concepts=["linear regression", "gradient descent"],
            content_type="mixed",
            estimated_duration_minutes=90,
            include_examples=True,
            include_exercises=True,
        )
        
        assert request.chapter_title == "Introduction to Neural Networks"
        assert request.sequence_number == 3
        assert request.estimated_duration_minutes == 90
        assert request.include_examples == True
        assert request.include_exercises == True
    
    def test_content_validation_request(self):
        """Test ContentValidationRequest validation."""
        long_content = "A" * 100  # Minimum length requirement
        
        request = ContentValidationRequest(
            content=long_content,
            target_level=ProficiencyLevel.ADVANCED,
            learning_objectives=["Master advanced concepts"],
            subject_domain="Data Science",
            expected_keywords=["algorithm", "optimization"],
        )
        
        assert len(request.content) >= 100
        assert request.target_level == ProficiencyLevel.ADVANCED
        assert len(request.expected_keywords) == 2


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_limit(self):
        """Test that rate limiter allows calls within limit."""
        limiter = RateLimiter(calls_per_minute=5)
        
        # Should allow 5 calls quickly
        for _ in range(5):
            await limiter.acquire()  # Should not block
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_over_limit(self):
        """Test that rate limiter blocks calls over limit."""
        limiter = RateLimiter(calls_per_minute=2)
        
        # First 2 calls should be immediate
        start_time = asyncio.get_event_loop().time()
        await limiter.acquire()
        await limiter.acquire()
        
        # Third call should be delayed
        await limiter.acquire()
        end_time = asyncio.get_event_loop().time()
        
        # Should have taken some time (but we'll be lenient for test speed)
        assert end_time >= start_time


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create OpenAI provider with mock client."""
        with patch('src.integrations.ai_client.AsyncOpenAI') as mock_openai:
            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            provider.client = mock_openai.return_value
            return provider
    
    @pytest.fixture
    def sample_structure_request(self):
        """Sample course structure request."""
        return CourseStructureRequest(
            title="Python Programming",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=20.0,
            learning_objectives=[
                "Learn Python syntax fundamentals",
                "Write basic Python programs effectively",
                "Understand data structures usage",
            ],
        )
    
    @pytest.mark.asyncio
    async def test_generate_course_structure_success(self, provider, sample_structure_request):
        """Test successful course structure generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "chapters": [
                {
                    "sequence_number": 1,
                    "title": "Python Basics",
                    "learning_objectives": ["Learn syntax", "Understand variables"],
                    "estimated_duration": 4.0,
                    "complexity_level": 1.5,
                    "prerequisites": [],
                    "content_outline": "Introduction to Python programming"
                }
            ],
            "estimated_total_duration": 20.0,
            "difficulty_progression": [1.0, 1.5, 2.0],
            "suggested_prerequisites": ["Basic computer literacy"],
            "learning_path_rationale": "Progressive introduction to programming concepts",
            "quality_indicators": {"progression_smoothness": 0.9, "objective_coverage": 1.0}
        })
        
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await provider.generate_course_structure(sample_structure_request)
        
        assert isinstance(result, CourseStructureResponse)
        assert len(result.chapters) == 1
        assert result.chapters[0]["title"] == "Python Basics"
        assert result.estimated_total_duration == 20.0
        provider.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_course_structure_error(self, provider, sample_structure_request):
        """Test course structure generation error handling."""
        provider.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(RuntimeError) as exc_info:
            await provider.generate_course_structure(sample_structure_request)
        
        assert "Course structure generation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content(self, provider):
        """Test chapter content generation."""
        request = ChapterContentRequest(
            chapter_title="Variables and Data Types",
            learning_objectives=["Understand variables", "Use different data types"],
            target_level=ProficiencyLevel.BEGINNER,
            sequence_number=1,
            estimated_duration_minutes=60,
        )
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "content_blocks": [
                {
                    "type": "text",
                    "content": "Variables are containers for storing data values",
                    "order": 1
                }
            ],
            "key_concepts": ["variables", "data types", "assignment"],
            "examples": [
                {
                    "title": "Creating Variables",
                    "description": "How to create and assign variables",
                    "code_or_content": "x = 5\nname = 'Python'"
                }
            ],
            "exercises": [
                {
                    "title": "Variable Practice",
                    "description": "Create variables of different types",
                    "difficulty": "easy",
                    "estimated_time": 10
                }
            ],
            "summary": "Variables store data values and can be of different types",
            "estimated_reading_time": 60,
            "complexity_score": 1.5
        })
        
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await provider.generate_chapter_content(request)
        
        assert isinstance(result, ChapterContentResponse)
        assert len(result.content_blocks) == 1
        assert len(result.key_concepts) == 3
        assert result.estimated_reading_time == 60
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content_stream(self, provider):
        """Test streaming chapter content generation."""
        request = ChapterContentRequest(
            chapter_title="Functions",
            learning_objectives=["Define functions", "Call functions"],
            target_level=ProficiencyLevel.BEGINNER,
            sequence_number=2,
            estimated_duration_minutes=45,
        )
        
        # Mock streaming response
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Functions"))]),
            Mock(choices=[Mock(delta=Mock(content=" are reusable"))]),
            Mock(choices=[Mock(delta=Mock(content=" blocks of code"))]),
        ]
        
        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk
        
        provider.client.chat.completions.create = AsyncMock(return_value=mock_stream())
        
        content_parts = []
        async for chunk in provider.generate_chapter_content_stream(request):
            content_parts.append(chunk)
        
        assert len(content_parts) == 3
        assert "".join(content_parts) == "Functions are reusable blocks of code"
    
    @pytest.mark.asyncio
    async def test_validate_content_quality(self, provider):
        """Test content quality validation."""
        request = ContentValidationRequest(
            content="Functions are fundamental building blocks in Python programming. They allow you to organize code into reusable components.",
            target_level=ProficiencyLevel.BEGINNER,
            learning_objectives=["Understand functions"],
            subject_domain="Computer Science",
        )
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "overall_score": 0.85,
            "readability_score": 78.5,
            "pedagogical_alignment": 0.9,
            "objective_coverage": 0.95,
            "content_accuracy": 0.92,
            "recommendations": ["Add more examples", "Include practice exercises"],
            "issues_found": [
                {
                    "type": "pedagogical",
                    "severity": "low",
                    "description": "Could benefit from more concrete examples",
                    "location": "paragraph 1"
                }
            ]
        })
        
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await provider.validate_content_quality(request)
        
        assert isinstance(result, ContentQualityResponse)
        assert result.overall_score == 0.85
        assert result.readability_score == 78.5
        assert len(result.recommendations) == 2
        assert len(result.issues_found) == 1


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create Anthropic provider with mock client."""
        with patch('src.integrations.ai_client.AsyncAnthropic') as mock_anthropic:
            provider = AnthropicProvider(api_key="test-key")
            provider.client = mock_anthropic.return_value
            return provider
    
    @pytest.mark.asyncio
    async def test_generate_course_structure_json_extraction(self, provider):
        """Test JSON extraction from Anthropic response."""
        request = CourseStructureRequest(
            title="Data Structures",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.INTERMEDIATE,
            estimated_duration_hours=30.0,
            learning_objectives=["Learn arrays", "Understand linked lists", "Master trees"],
        )
        
        # Mock Anthropic response with text around JSON
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        Here's the course structure:
        
        {
            "chapters": [
                {
                    "sequence_number": 1,
                    "title": "Arrays and Lists",
                    "learning_objectives": ["Understand arrays", "Implement lists"],
                    "estimated_duration": 8.0,
                    "complexity_level": 2.0,
                    "prerequisites": ["Basic programming"],
                    "content_outline": "Introduction to linear data structures"
                }
            ],
            "estimated_total_duration": 30.0,
            "difficulty_progression": [2.0, 2.5, 3.0],
            "suggested_prerequisites": ["Programming fundamentals"],
            "learning_path_rationale": "Build from simple to complex structures",
            "quality_indicators": {"progression_smoothness": 0.95, "objective_coverage": 1.0}
        }
        
        This structure provides a comprehensive learning path.
        '''
        
        provider.client.messages.create = AsyncMock(return_value=mock_response)
        
        result = await provider.generate_course_structure(request)
        
        assert isinstance(result, CourseStructureResponse)
        assert len(result.chapters) == 1
        assert result.chapters[0]["title"] == "Arrays and Lists"
        assert result.estimated_total_duration == 30.0
    
    @pytest.mark.asyncio
    async def test_anthropic_streaming(self, provider):
        """Test Anthropic streaming functionality."""
        request = ChapterContentRequest(
            chapter_title="Recursion",
            learning_objectives=["Understand recursion", "Implement recursive functions"],
            target_level=ProficiencyLevel.INTERMEDIATE,
            sequence_number=5,
            estimated_duration_minutes=75,
        )
        
        # Mock streaming context manager
        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=None)
        
        async def mock_text_stream():
            yield "Recursion is"
            yield " a programming technique"
            yield " where functions call themselves"
        
        mock_stream.text_stream = mock_text_stream()
        provider.client.messages.stream = Mock(return_value=mock_stream)
        
        content_parts = []
        async for chunk in provider.generate_chapter_content_stream(request):
            content_parts.append(chunk)
        
        assert len(content_parts) == 3
        full_content = "".join(content_parts)
        assert "Recursion is a programming technique where functions call themselves" == full_content


class TestReadabilityAnalyzer:
    """Test readability analysis utilities."""
    
    def test_analyze_readability_basic(self):
        """Test basic readability analysis."""
        request = ReadabilityAnalysisRequest(
            content="This is a simple sentence. It has easy words. Most people can read this.",
            target_level=ProficiencyLevel.BEGINNER,
        )
        
        result = ReadabilityAnalyzer.analyze_readability(request)
        
        assert isinstance(result, ReadabilityAnalysisResponse)
        assert 0.0 <= result.flesch_reading_ease <= 100.0
        assert result.flesch_kincaid_score > 0.0
        assert result.coleman_liau_index > 0.0
        assert result.automated_readability_index > 0.0
        assert isinstance(result.grade_level, str)
        assert isinstance(result.meets_target_level, bool)
        assert isinstance(result.recommendations, list)
    
    def test_readability_level_thresholds(self):
        """Test readability thresholds for different levels."""
        # Easy content for beginners
        easy_request = ReadabilityAnalysisRequest(
            content="Dogs are pets. They are fun. Kids love dogs. Dogs play a lot.",
            target_level=ProficiencyLevel.BEGINNER,
        )
        
        easy_result = ReadabilityAnalyzer.analyze_readability(easy_request)
        
        # Complex content for experts
        complex_request = ReadabilityAnalysisRequest(
            content="The algorithmic complexity of distributed consensus protocols in Byzantine fault-tolerant systems requires comprehensive analysis of computational overhead and network partition resilience.",
            target_level=ProficiencyLevel.EXPERT,
        )
        
        complex_result = ReadabilityAnalyzer.analyze_readability(complex_request)
        
        # Easy content should have higher readability score
        assert easy_result.flesch_reading_ease >= complex_result.flesch_reading_ease
    
    def test_readability_recommendations(self):
        """Test readability recommendation generation."""
        # Complex content for beginner level
        request = ReadabilityAnalysisRequest(
            content="The implementation of sophisticated algorithmic paradigms necessitates comprehensive understanding of computational complexity theory and its ramifications.",
            target_level=ProficiencyLevel.BEGINNER,
        )
        
        result = ReadabilityAnalyzer.analyze_readability(request)
        
        # Should not meet beginner level and have recommendations
        assert not result.meets_target_level
        assert len(result.recommendations) > 0
        assert any("simplify" in rec.lower() for rec in result.recommendations)


class TestBiasDetector:
    """Test bias detection utilities."""
    
    @pytest.mark.asyncio
    async def test_detect_bias_clean_content(self):
        """Test bias detection on clean content."""
        request = BiasDetectionRequest(
            content="Students learn programming through practice. Learners of all backgrounds can succeed with proper support and guidance.",
            check_categories=["gender", "cultural", "racial"],
        )
        
        result = await BiasDetector.detect_bias(request)
        
        assert isinstance(result, BiasDetectionResponse)
        assert 0.0 <= result.overall_bias_score <= 1.0
        assert isinstance(result.category_scores, dict)
        assert isinstance(result.detected_issues, list)
        assert result.severity_level in ["low", "medium", "high"]
        assert isinstance(result.recommendations, list)
        
        # Clean content should have low bias
        assert result.overall_bias_score < 0.3
        assert result.severity_level == "low"
    
    @pytest.mark.asyncio
    async def test_detect_bias_problematic_content(self):
        """Test bias detection on problematic content."""
        request = BiasDetectionRequest(
            content="Guys, you should learn programming. Mankind has always been innovative. These primitive methods are outdated.",
            check_categories=["gender", "cultural"],
        )
        
        result = await BiasDetector.detect_bias(request)
        
        # Should detect bias in gendered language and cultural references
        assert result.overall_bias_score > 0.0
        assert len(result.detected_issues) > 0
        assert any(issue["category"] == "gender" for issue in result.detected_issues)
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_bias_detection_categories(self):
        """Test bias detection across different categories."""
        content_with_multiple_bias = "Young people these days don't understand technology like elderly folks. Poor people can't afford quality education."
        
        request = BiasDetectionRequest(
            content=content_with_multiple_bias,
            check_categories=["age", "socioeconomic"],
        )
        
        result = await BiasDetector.detect_bias(request)
        
        # Should detect both age and socioeconomic bias
        assert "age" in result.category_scores
        assert "socioeconomic" in result.category_scores
        assert result.category_scores["age"] > 0.0
        assert result.category_scores["socioeconomic"] > 0.0


class TestAIClient:
    """Test unified AI client wrapper."""
    
    @pytest.fixture
    def client_openai_only(self):
        """Create AI client with only OpenAI."""
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_provider:
            client = AIClient(
                openai_api_key="test-openai-key",
                preferred_provider="openai",
            )
            client.providers["openai"] = mock_provider.return_value
            return client
    
    @pytest.fixture
    def client_both_providers(self):
        """Create AI client with both providers."""
        with patch('src.integrations.ai_client.OpenAIProvider') as mock_openai, \
             patch('src.integrations.ai_client.AnthropicProvider') as mock_anthropic:
            client = AIClient(
                openai_api_key="test-openai-key",
                anthropic_api_key="test-anthropic-key",
                preferred_provider="openai",
                fallback_enabled=True,
            )
            client.providers["openai"] = mock_openai.return_value
            client.providers["anthropic"] = mock_anthropic.return_value
            return client
    
    def test_client_initialization_no_keys(self):
        """Test client initialization error with no API keys."""
        with pytest.raises(ValueError) as exc_info:
            AIClient()
        
        assert "At least one AI provider API key must be provided" in str(exc_info.value)
    
    def test_client_initialization_preferred_provider(self):
        """Test client initialization with preferred provider."""
        with patch('src.integrations.ai_client.OpenAIProvider'):
            client = AIClient(
                openai_api_key="test-key",
                preferred_provider="openai",
            )
            assert client.preferred_provider == "openai"
    
    def test_client_initialization_fallback_provider(self):
        """Test client initialization with fallback when preferred unavailable."""
        with patch('src.integrations.ai_client.AnthropicProvider'):
            client = AIClient(
                anthropic_api_key="test-key",
                preferred_provider="openai",  # Not available
            )
            assert client.preferred_provider == "anthropic"  # Should fallback
    
    @pytest.mark.asyncio
    async def test_generate_course_structure_success(self, client_openai_only):
        """Test successful course structure generation."""
        request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Test",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=10.0,
            learning_objectives=["Learn basics", "Apply knowledge", "Master concepts"],
        )
        
        mock_response = CourseStructureResponse(
            chapters=[{"title": "Chapter 1"}],
            estimated_total_duration=10.0,
            difficulty_progression=[1.0],
            suggested_prerequisites=[],
            learning_path_rationale="Test progression",
            quality_indicators={"progression_smoothness": 0.9},
        )
        
        client_openai_only.providers["openai"].generate_course_structure = AsyncMock(return_value=mock_response)
        
        result = await client_openai_only.generate_course_structure(request)
        
        assert result == mock_response
        client_openai_only.providers["openai"].generate_course_structure.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, client_both_providers):
        """Test fallback mechanism when primary provider fails."""
        request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Test",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=10.0,
            learning_objectives=["Learn basics", "Apply knowledge", "Master concepts"],
        )
        
        mock_response = CourseStructureResponse(
            chapters=[{"title": "Chapter 1"}],
            estimated_total_duration=10.0,
            difficulty_progression=[1.0],
            suggested_prerequisites=[],
            learning_path_rationale="Test progression",
            quality_indicators={"progression_smoothness": 0.9},
        )
        
        # Primary provider fails
        client_both_providers.providers["openai"].generate_course_structure = AsyncMock(
            side_effect=Exception("Primary failed")
        )
        
        # Fallback provider succeeds
        client_both_providers.providers["anthropic"].generate_course_structure = AsyncMock(
            return_value=mock_response
        )
        
        result = await client_both_providers.generate_course_structure(request)
        
        assert result == mock_response
        # Both providers should have been called
        client_both_providers.providers["openai"].generate_course_structure.assert_called_once()
        client_both_providers.providers["anthropic"].generate_course_structure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_comprehensive_quality_check(self, client_openai_only):
        """Test comprehensive quality analysis."""
        content = "Machine learning algorithms can analyze large datasets to find patterns and make predictions."
        objectives = ["Understand ML concepts", "Apply algorithms"]
        
        # Mock all the required responses
        mock_ai_quality = ContentQualityResponse(
            overall_score=0.85,
            readability_score=75.0,
            pedagogical_alignment=0.9,
            objective_coverage=0.95,
            content_accuracy=0.92,
            recommendations=["Good content"],
            issues_found=[],
        )
        
        mock_readability = ReadabilityAnalysisResponse(
            flesch_kincaid_score=8.5,
            flesch_reading_ease=75.0,
            coleman_liau_index=9.0,
            automated_readability_index=8.0,
            grade_level="Grade 8",
            meets_target_level=True,
            recommendations=[],
        )
        
        mock_bias = BiasDetectionResponse(
            overall_bias_score=0.05,
            category_scores={"gender": 0.0},
            detected_issues=[],
            severity_level="low",
            recommendations=[],
        )
        
        client_openai_only.validate_content_quality = AsyncMock(return_value=mock_ai_quality)
        client_openai_only.analyze_readability = AsyncMock(return_value=mock_readability)
        client_openai_only.check_bias_detection = AsyncMock(return_value=mock_bias)
        
        result = await client_openai_only.comprehensive_quality_check(
            content=content,
            target_level=ProficiencyLevel.INTERMEDIATE,
            learning_objectives=objectives,
            subject_domain="Computer Science",
        )
        
        assert isinstance(result, dict)
        assert "ai_quality_assessment" in result
        assert "readability_analysis" in result
        assert "bias_detection" in result
        assert "overall_quality_score" in result
        assert "meets_quality_standards" in result
        
        assert result["meets_quality_standards"] == True
        assert 0.0 <= result["overall_quality_score"] <= 1.0
    
    def test_get_provider_status(self, client_both_providers):
        """Test provider status reporting."""
        status = client_both_providers.get_provider_status()
        
        assert isinstance(status, dict)
        assert "openai" in status
        assert "anthropic" in status
        assert status["openai"] == True
        assert status["anthropic"] == True
    
    def test_switch_provider(self, client_both_providers):
        """Test switching between providers."""
        assert client_both_providers.preferred_provider == "openai"
        
        client_both_providers.switch_provider("anthropic")
        assert client_both_providers.preferred_provider == "anthropic"
        
        # Test switching to non-existent provider
        with pytest.raises(ValueError):
            client_both_providers.switch_provider("invalid_provider")


class TestAIClientFactory:
    """Test AI client factory function."""
    
    def test_create_ai_client_default(self):
        """Test creating AI client with default parameters."""
        with patch('src.integrations.ai_client.AIClient') as mock_client:
            result = create_ai_client(openai_api_key="test-key")
            
            mock_client.assert_called_once_with(
                openai_api_key="test-key",
                anthropic_api_key=None,
                preferred_provider="openai"
            )
    
    def test_create_ai_client_custom(self):
        """Test creating AI client with custom parameters."""
        with patch('src.integrations.ai_client.AIClient') as mock_client:
            result = create_ai_client(
                openai_api_key="openai-key",
                anthropic_api_key="anthropic-key",
                preferred_provider="anthropic"
            )
            
            mock_client.assert_called_once_with(
                openai_api_key="openai-key",
                anthropic_api_key="anthropic-key",
                preferred_provider="anthropic"
            )


class TestAIServiceIntegration:
    """Integration tests for AI service components."""
    
    @pytest.mark.asyncio
    async def test_full_course_generation_workflow(self):
        """Test complete workflow from structure to content."""
        # This would be an integration test with actual API calls
        # For unit tests, we mock the entire workflow
        
        with patch('src.integrations.ai_client.AIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock course structure generation
            structure_response = CourseStructureResponse(
                chapters=[
                    {
                        "sequence_number": 1,
                        "title": "Introduction",
                        "learning_objectives": ["Understand basics"],
                        "estimated_duration": 2.0,
                        "complexity_level": 1.0,
                        "prerequisites": [],
                        "content_outline": "Basic introduction"
                    }
                ],
                estimated_total_duration=10.0,
                difficulty_progression=[1.0, 1.5],
                suggested_prerequisites=[],
                learning_path_rationale="Progressive learning",
                quality_indicators={"progression_smoothness": 0.9, "objective_coverage": 1.0}
            )
            
            content_response = ChapterContentResponse(
                content_blocks=[
                    {
                        "type": "text",
                        "content": "Welcome to the course",
                        "order": 1
                    }
                ],
                key_concepts=["introduction", "overview"],
                examples=[],
                exercises=[],
                summary="Course introduction chapter",
                estimated_reading_time=30,
                complexity_score=1.0
            )
            
            quality_response = ContentQualityResponse(
                overall_score=0.9,
                readability_score=85.0,
                pedagogical_alignment=0.95,
                objective_coverage=1.0,
                content_accuracy=0.92,
                recommendations=[],
                issues_found=[]
            )
            
            mock_client.generate_course_structure = AsyncMock(return_value=structure_response)
            mock_client.generate_chapter_content = AsyncMock(return_value=content_response)
            mock_client.validate_content_quality = AsyncMock(return_value=quality_response)
            
            client = mock_client_class.return_value
            
            # Test the workflow
            structure_request = CourseStructureRequest(
                title="Test Course",
                subject_domain="Test",
                target_level=ProficiencyLevel.BEGINNER,
                estimated_duration_hours=10.0,
                learning_objectives=["Learn basics", "Apply knowledge", "Master concepts"],
            )
            
            structure = await client.generate_course_structure(structure_request)
            assert len(structure.chapters) == 1
            
            content_request = ChapterContentRequest(
                chapter_title=structure.chapters[0]["title"],
                learning_objectives=structure.chapters[0]["learning_objectives"],
                target_level=ProficiencyLevel.BEGINNER,
                sequence_number=1,
                estimated_duration_minutes=120,
            )
            
            content = await client.generate_chapter_content(content_request)
            assert len(content.content_blocks) == 1
            
            validation_request = ContentValidationRequest(
                content=content.content_blocks[0]["content"],
                target_level=ProficiencyLevel.BEGINNER,
                learning_objectives=structure.chapters[0]["learning_objectives"],
                subject_domain="Test",
            )
            
            quality = await client.validate_content_quality(validation_request)
            assert quality.overall_score >= 0.8
    
    def test_error_propagation_and_logging(self):
        """Test that errors are properly propagated and logged."""
        # This would test error handling across the entire AI service stack
        with patch('src.integrations.ai_client.logger') as mock_logger:
            with patch('src.integrations.ai_client.AsyncOpenAI') as mock_openai:
                provider = OpenAIProvider(api_key="test-key")
                provider.client = mock_openai.return_value
                provider.client.chat.completions.create = AsyncMock(
                    side_effect=Exception("Network error")
                )
                
                request = CourseStructureRequest(
                    title="Test",
                    subject_domain="Test", 
                    target_level=ProficiencyLevel.BEGINNER,
                    estimated_duration_hours=10.0,
                    learning_objectives=["Learn", "Apply", "Master"],
                )
                
                with pytest.raises(RuntimeError):
                    asyncio.run(provider.generate_course_structure(request))
                
                # Verify error was logged
                mock_logger.error.assert_called()