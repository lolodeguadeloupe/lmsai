"""
Unit tests for AI client wrapper.

Tests T038: OpenAI/Anthropic AI client wrapper functionality.
Covers all key methods and error handling scenarios.
"""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import AsyncGenerator

from src.integrations.ai_client import (
    AIClient,
    OpenAIProvider,
    AnthropicProvider,
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
    ReadabilityAnalyzer,
    BiasDetector,
    RateLimiter,
    create_ai_client
)
from src.models.enums import ProficiencyLevel


class TestAIClient:
    """Test cases for unified AI client wrapper."""
    
    @pytest.fixture
    def mock_openai_provider(self):
        """Mock OpenAI provider."""
        provider = Mock(spec=OpenAIProvider)
        provider.generate_course_structure = AsyncMock()
        provider.generate_chapter_content = AsyncMock()
        provider.generate_chapter_content_stream = AsyncMock()
        provider.validate_content_quality = AsyncMock()
        return provider
    
    @pytest.fixture
    def mock_anthropic_provider(self):
        """Mock Anthropic provider."""
        provider = Mock(spec=AnthropicProvider)
        provider.generate_course_structure = AsyncMock()
        provider.generate_chapter_content = AsyncMock()
        provider.generate_chapter_content_stream = AsyncMock()
        provider.validate_content_quality = AsyncMock()
        return provider
    
    @pytest.fixture
    def ai_client(self, mock_openai_provider, mock_anthropic_provider):
        """AI client with mocked providers."""
        client = AIClient.__new__(AIClient)
        client.providers = {
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider
        }
        client.preferred_provider = "openai"
        client.fallback_enabled = True
        return client
    
    @pytest.fixture
    def sample_course_request(self):
        """Sample course structure request."""
        return CourseStructureRequest(
            title="Introduction to Python Programming",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=20.0,
            learning_objectives=[
                "Understand Python syntax and basic programming concepts",
                "Write simple Python programs with variables and functions",
                "Use Python data structures like lists and dictionaries"
            ],
            prerequisites=["Basic computer literacy"],
            preferred_language="en"
        )
    
    @pytest.fixture
    def sample_chapter_request(self):
        """Sample chapter content request."""
        return ChapterContentRequest(
            chapter_title="Variables and Data Types",
            learning_objectives=[
                "Define variables in Python",
                "Understand different data types"
            ],
            target_level=ProficiencyLevel.BEGINNER,
            sequence_number=1,
            estimated_duration_minutes=45,
            include_examples=True,
            include_exercises=True
        )
    
    @pytest.fixture
    def sample_validation_request(self):
        """Sample content validation request."""
        return ContentValidationRequest(
            content="Python is a programming language. Variables store data.",
            target_level=ProficiencyLevel.BEGINNER,
            learning_objectives=["Understand variables"],
            subject_domain="Computer Science"
        )
    
    def test_ai_client_initialization_with_both_providers(self):
        """Test AI client initialization with both providers."""
        client = AIClient(
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            preferred_provider="openai"
        )
        
        assert "openai" in client.providers
        assert "anthropic" in client.providers
        assert client.preferred_provider == "openai"
        assert client.fallback_enabled is True
    
    def test_ai_client_initialization_single_provider(self):
        """Test AI client initialization with single provider."""
        client = AIClient(openai_api_key="test-openai-key")
        
        assert "openai" in client.providers
        assert "anthropic" not in client.providers
        assert client.preferred_provider == "openai"
    
    def test_ai_client_initialization_no_providers_raises_error(self):
        """Test AI client initialization fails without providers."""
        with pytest.raises(ValueError, match="At least one AI provider API key"):
            AIClient()
    
    def test_ai_client_initialization_invalid_preferred_provider(self):
        """Test AI client falls back when preferred provider not available."""
        client = AIClient(
            openai_api_key="test-openai-key",
            preferred_provider="anthropic"  # Not configured
        )
        
        assert client.preferred_provider == "openai"  # Falls back to available
    
    @pytest.mark.asyncio
    async def test_generate_course_structure_success(self, ai_client, sample_course_request):
        """Test successful course structure generation."""
        expected_response = CourseStructureResponse(
            chapters=[{
                "sequence_number": 1,
                "title": "Introduction",
                "learning_objectives": ["Understand basics"],
                "estimated_duration": 2.0,
                "complexity_level": 1.0,
                "prerequisites": [],
                "content_outline": "Basic introduction"
            }],
            estimated_total_duration=20.0,
            difficulty_progression=[1.0, 1.5, 2.0],
            suggested_prerequisites=["Basic computer literacy"],
            learning_path_rationale="Progressive learning approach",
            quality_indicators={"progression_smoothness": 0.9, "objective_coverage": 1.0}
        )
        
        ai_client.providers["openai"].generate_course_structure.return_value = expected_response
        
        result = await ai_client.generate_course_structure(sample_course_request)
        
        assert result == expected_response
        ai_client.providers["openai"].generate_course_structure.assert_called_once_with(
            sample_course_request
        )
    
    @pytest.mark.asyncio
    async def test_generate_course_structure_fallback(self, ai_client, sample_course_request):
        """Test course structure generation with fallback to secondary provider."""
        expected_response = CourseStructureResponse(
            chapters=[],
            estimated_total_duration=20.0,
            difficulty_progression=[],
            suggested_prerequisites=[],
            learning_path_rationale="Fallback response",
            quality_indicators={}
        )
        
        # Primary provider fails
        ai_client.providers["openai"].generate_course_structure.side_effect = Exception("API Error")
        # Fallback provider succeeds
        ai_client.providers["anthropic"].generate_course_structure.return_value = expected_response
        
        result = await ai_client.generate_course_structure(sample_course_request)
        
        assert result == expected_response
        ai_client.providers["openai"].generate_course_structure.assert_called_once()
        ai_client.providers["anthropic"].generate_course_structure.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content_success(self, ai_client, sample_chapter_request):
        """Test successful chapter content generation."""
        expected_response = ChapterContentResponse(
            content_blocks=[{
                "type": "text",
                "content": "Chapter content here",
                "order": 1
            }],
            key_concepts=["variables", "data types"],
            examples=[{
                "title": "Variable Example",
                "description": "How to create variables",
                "code_or_content": "x = 5"
            }],
            exercises=[{
                "title": "Practice Exercise",
                "description": "Create your own variable",
                "difficulty": "easy",
                "estimated_time": 10
            }],
            summary="Chapter covers variables and data types",
            estimated_reading_time=45,
            complexity_score=1.5
        )
        
        ai_client.providers["openai"].generate_chapter_content.return_value = expected_response
        
        result = await ai_client.generate_chapter_content(sample_chapter_request)
        
        assert result == expected_response
        ai_client.providers["openai"].generate_chapter_content.assert_called_once_with(
            sample_chapter_request
        )
    
    @pytest.mark.asyncio
    async def test_generate_chapter_content_stream(self, ai_client, sample_chapter_request):
        """Test streaming chapter content generation."""
        async def mock_stream():
            chunks = ["First chunk", " second chunk", " final chunk"]
            for chunk in chunks:
                yield chunk
        
        ai_client.providers["openai"].generate_chapter_content_stream.return_value = mock_stream()
        
        chunks = []
        async for chunk in ai_client.generate_chapter_content_stream(sample_chapter_request):
            chunks.append(chunk)
        
        assert chunks == ["First chunk", " second chunk", " final chunk"]
    
    @pytest.mark.asyncio
    async def test_validate_content_quality_success(self, ai_client, sample_validation_request):
        """Test successful content quality validation."""
        expected_response = ContentQualityResponse(
            overall_score=0.85,
            readability_score=75.0,
            pedagogical_alignment=0.9,
            objective_coverage=0.95,
            content_accuracy=0.9,
            recommendations=["Add more examples"],
            issues_found=[{
                "type": "readability",
                "severity": "low",
                "description": "Some complex sentences",
                "location": "paragraph 2"
            }]
        )
        
        ai_client.providers["openai"].validate_content_quality.return_value = expected_response
        
        result = await ai_client.validate_content_quality(sample_validation_request)
        
        assert result == expected_response
        ai_client.providers["openai"].validate_content_quality.assert_called_once_with(
            sample_validation_request
        )
    
    @pytest.mark.asyncio
    async def test_analyze_readability(self, ai_client):
        """Test readability analysis."""
        request = ReadabilityAnalysisRequest(
            content="This is a simple test sentence for readability analysis.",
            target_level=ProficiencyLevel.BEGINNER
        )
        
        with patch.object(ReadabilityAnalyzer, 'analyze_readability') as mock_analyze:
            expected_response = ReadabilityAnalysisResponse(
                flesch_kincaid_score=8.5,
                flesch_reading_ease=75.0,
                coleman_liau_index=9.0,
                automated_readability_index=8.0,
                grade_level="Grade 8.5",
                meets_target_level=True,
                recommendations=[]
            )
            mock_analyze.return_value = expected_response
            
            result = await ai_client.analyze_readability(request)
            
            assert result == expected_response
            mock_analyze.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_check_bias_detection(self, ai_client):
        """Test bias detection analysis."""
        request = BiasDetectionRequest(
            content="This content should be checked for potential bias in language and examples."
        )
        
        with patch.object(BiasDetector, 'detect_bias') as mock_detect:
            expected_response = BiasDetectionResponse(
                overall_bias_score=0.1,
                category_scores={"gender": 0.0, "cultural": 0.2},
                detected_issues=[],
                severity_level="low",
                recommendations=["Review content for inclusive language"]
            )
            mock_detect.return_value = expected_response
            
            result = await ai_client.check_bias_detection(request)
            
            assert result == expected_response
            mock_detect.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_comprehensive_quality_check(self, ai_client):
        """Test comprehensive quality analysis combining all methods."""
        content = "Test content for comprehensive quality analysis."
        target_level = ProficiencyLevel.BEGINNER
        objectives = ["Test objective"]
        subject = "Computer Science"
        
        # Mock individual methods
        ai_client.validate_content_quality = AsyncMock(return_value=ContentQualityResponse(
            overall_score=0.8,
            readability_score=75.0,
            pedagogical_alignment=0.9,
            objective_coverage=0.95,
            content_accuracy=0.9,
            recommendations=[],
            issues_found=[]
        ))
        
        ai_client.analyze_readability = AsyncMock(return_value=ReadabilityAnalysisResponse(
            flesch_kincaid_score=8.5,
            flesch_reading_ease=75.0,
            coleman_liau_index=9.0,
            automated_readability_index=8.0,
            grade_level="Grade 8.5",
            meets_target_level=True,
            recommendations=[]
        ))
        
        ai_client.check_bias_detection = AsyncMock(return_value=BiasDetectionResponse(
            overall_bias_score=0.1,
            category_scores={},
            detected_issues=[],
            severity_level="low",
            recommendations=[]
        ))
        
        result = await ai_client.comprehensive_quality_check(
            content, target_level, objectives, subject
        )
        
        assert "ai_quality_assessment" in result
        assert "readability_analysis" in result
        assert "bias_detection" in result
        assert "overall_quality_score" in result
        assert "meets_quality_standards" in result
        assert result["meets_quality_standards"] is True
    
    def test_switch_provider(self, ai_client):
        """Test switching between providers."""
        assert ai_client.preferred_provider == "openai"
        
        ai_client.switch_provider("anthropic")
        assert ai_client.preferred_provider == "anthropic"
        
        with pytest.raises(ValueError, match="Provider unknown not configured"):
            ai_client.switch_provider("unknown")
    
    def test_get_provider_status(self, ai_client):
        """Test getting provider status."""
        status = ai_client.get_provider_status()
        
        assert status == {"openai": True, "anthropic": True}


class TestOpenAIProvider:
    """Test cases for OpenAI provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """OpenAI provider instance."""
        return OpenAIProvider(api_key="test-key", model="gpt-4")
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "chapters": [],
            "estimated_total_duration": 20.0,
            "difficulty_progression": [],
            "suggested_prerequisites": [],
            "learning_path_rationale": "Test rationale",
            "quality_indicators": {}
        })
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        return mock_client
    
    @pytest.mark.asyncio
    async def test_openai_generate_course_structure(self, provider, mock_openai_client):
        """Test OpenAI course structure generation."""
        provider.client = mock_openai_client
        
        request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=20.0,
            learning_objectives=["Learn programming", "Write code", "Debug programs"]
        )
        
        # Mock rate limiter
        provider.rate_limiter.acquire = AsyncMock()
        
        result = await provider.generate_course_structure(request)
        
        assert isinstance(result, CourseStructureResponse)
        assert result.estimated_total_duration == 20.0
        provider.rate_limiter.acquire.assert_called_once()
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openai_api_error_handling(self, provider, mock_openai_client):
        """Test OpenAI API error handling."""
        provider.client = mock_openai_client
        provider.rate_limiter.acquire = AsyncMock()
        
        # Mock API error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Computer Science", 
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=20.0,
            learning_objectives=["Test objective"]
        )
        
        with pytest.raises(RuntimeError, match="Course structure generation failed"):
            await provider.generate_course_structure(request)


class TestAnthropicProvider:
    """Test cases for Anthropic provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Anthropic provider instance."""
        return AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "chapters": [],
            "estimated_total_duration": 20.0,
            "difficulty_progression": [],
            "suggested_prerequisites": [],
            "learning_path_rationale": "Test rationale",
            "quality_indicators": {}
        })
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        return mock_client
    
    @pytest.mark.asyncio
    async def test_anthropic_generate_course_structure(self, provider, mock_anthropic_client):
        """Test Anthropic course structure generation."""
        provider.client = mock_anthropic_client
        provider.rate_limiter.acquire = AsyncMock()
        
        request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=20.0,
            learning_objectives=["Learn programming", "Write code", "Debug programs"]
        )
        
        result = await provider.generate_course_structure(request)
        
        assert isinstance(result, CourseStructureResponse)
        assert result.estimated_total_duration == 20.0
        provider.rate_limiter.acquire.assert_called_once()
        mock_anthropic_client.messages.create.assert_called_once()


class TestRateLimiter:
    """Test cases for rate limiter."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_calls_under_limit(self):
        """Test rate limiter allows calls under the limit."""
        limiter = RateLimiter(calls_per_minute=60)
        
        # Should allow multiple calls under limit
        for _ in range(5):
            await limiter.acquire()  # Should not block
        
        assert len(limiter.calls) == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_over_limit(self):
        """Test rate limiter blocks when over limit."""
        limiter = RateLimiter(calls_per_minute=2)
        
        # First 2 calls should be immediate
        await limiter.acquire()
        await limiter.acquire()
        
        # Mock time to avoid actual delay in tests
        with patch('time.time') as mock_time:
            mock_time.return_value = 0
            limiter.calls = [0, 0]  # Two calls at time 0
            
            with patch('asyncio.sleep') as mock_sleep:
                await limiter.acquire()
                mock_sleep.assert_called_once()


class TestReadabilityAnalyzer:
    """Test cases for readability analyzer."""
    
    def test_analyze_readability_beginner_level(self):
        """Test readability analysis for beginner level content."""
        request = ReadabilityAnalysisRequest(
            content="This is a simple sentence. It has easy words. Everyone can read it.",
            target_level=ProficiencyLevel.BEGINNER
        )
        
        with patch('textstat.flesch_kincaid') as mock_fk, \
             patch('textstat.flesch_reading_ease') as mock_fre, \
             patch('textstat.coleman_liau_index') as mock_cli, \
             patch('textstat.automated_readability_index') as mock_ari:
            
            mock_fk.return_value = Mock(grade=6.0)
            mock_fre.return_value = 80.0
            mock_cli.return_value = 5.0
            mock_ari.return_value = 4.0
            
            result = ReadabilityAnalyzer.analyze_readability(request)
            
            assert result.flesch_reading_ease == 80.0
            assert result.meets_target_level is True  # 80.0 >= 70.0 threshold
            assert "Grade" in result.grade_level
    
    def test_analyze_readability_advanced_level(self):
        """Test readability analysis for advanced level content."""
        request = ReadabilityAnalysisRequest(
            content="This sophisticated exposition demonstrates complex syntactic structures.",
            target_level=ProficiencyLevel.ADVANCED
        )
        
        with patch('textstat.flesch_kincaid') as mock_fk, \
             patch('textstat.flesch_reading_ease') as mock_fre, \
             patch('textstat.coleman_liau_index') as mock_cli, \
             patch('textstat.automated_readability_index') as mock_ari:
            
            mock_fk.return_value = Mock(grade=12.0)
            mock_fre.return_value = 45.0
            mock_cli.return_value = 14.0
            mock_ari.return_value = 13.0
            
            result = ReadabilityAnalyzer.analyze_readability(request)
            
            assert result.flesch_reading_ease == 45.0
            assert result.meets_target_level is False  # 45.0 < 50.0 threshold
            assert len(result.recommendations) > 0


class TestBiasDetector:
    """Test cases for bias detector."""
    
    @pytest.mark.asyncio
    async def test_detect_bias_no_issues(self):
        """Test bias detection with clean content."""
        request = BiasDetectionRequest(
            content="This educational content uses inclusive language and diverse examples for all learners.",
            check_categories=["gender", "cultural"]
        )
        
        result = await BiasDetector.detect_bias(request)
        
        assert result.overall_bias_score == 0.0
        assert result.severity_level == "low"
        assert len(result.detected_issues) == 0
    
    @pytest.mark.asyncio
    async def test_detect_bias_with_issues(self):
        """Test bias detection with problematic content."""
        request = BiasDetectionRequest(
            content="Guys, this is how primitive cultures do things in the third world.",
            check_categories=["gender", "cultural"]
        )
        
        result = await BiasDetector.detect_bias(request)
        
        assert result.overall_bias_score > 0.0
        assert result.severity_level in ["medium", "high"]
        assert len(result.detected_issues) > 0
        assert any(issue["category"] == "gender" for issue in result.detected_issues)
        assert any(issue["category"] == "cultural" for issue in result.detected_issues)


class TestValidationModels:
    """Test cases for request/response validation models."""
    
    def test_course_structure_request_validation(self):
        """Test course structure request validation."""
        # Valid request
        valid_request = CourseStructureRequest(
            title="Introduction to Python",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=20.0,
            learning_objectives=[
                "Understand Python syntax",
                "Write basic programs", 
                "Debug simple errors"
            ]
        )
        assert valid_request.title == "Introduction to Python"
        assert len(valid_request.learning_objectives) == 3
        
        # Invalid request - title too short
        with pytest.raises(ValueError):
            CourseStructureRequest(
                title="Hi",  # Too short
                subject_domain="Computer Science",
                target_level=ProficiencyLevel.BEGINNER,
                estimated_duration_hours=20.0,
                learning_objectives=["Learn", "Code", "Debug"]
            )
        
        # Invalid request - too few objectives
        with pytest.raises(ValueError):
            CourseStructureRequest(
                title="Introduction to Python",
                subject_domain="Computer Science", 
                target_level=ProficiencyLevel.BEGINNER,
                estimated_duration_hours=20.0,
                learning_objectives=["Learn", "Code"]  # Less than 3
            )
    
    def test_chapter_content_request_validation(self):
        """Test chapter content request validation."""
        # Valid request
        valid_request = ChapterContentRequest(
            chapter_title="Variables and Data Types",
            learning_objectives=["Define variables"],
            target_level=ProficiencyLevel.BEGINNER,
            sequence_number=1,
            estimated_duration_minutes=45
        )
        assert valid_request.sequence_number == 1
        assert valid_request.estimated_duration_minutes == 45
        
        # Invalid request - sequence number too low
        with pytest.raises(ValueError):
            ChapterContentRequest(
                chapter_title="Variables and Data Types",
                learning_objectives=["Define variables"],
                target_level=ProficiencyLevel.BEGINNER,
                sequence_number=0,  # Must be >= 1
                estimated_duration_minutes=45
            )
    
    def test_content_validation_request_validation(self):
        """Test content validation request validation."""
        # Valid request
        valid_request = ContentValidationRequest(
            content="This is a comprehensive explanation of Python variables and how they work in programming.",
            target_level=ProficiencyLevel.BEGINNER,
            learning_objectives=["Understand variables"],
            subject_domain="Computer Science"
        )
        assert len(valid_request.content) >= 100
        
        # Invalid request - content too short
        with pytest.raises(ValueError):
            ContentValidationRequest(
                content="Short content",  # Less than 100 chars
                target_level=ProficiencyLevel.BEGINNER,
                learning_objectives=["Understand variables"],
                subject_domain="Computer Science"
            )


class TestFactoryFunction:
    """Test cases for factory function."""
    
    def test_create_ai_client_with_keys(self):
        """Test factory function with explicit API keys."""
        client = create_ai_client(
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            preferred_provider="anthropic"
        )
        
        assert isinstance(client, AIClient)
        assert client.preferred_provider == "anthropic"
        assert "openai" in client.providers
        assert "anthropic" in client.providers
    
    def test_create_ai_client_with_settings(self):
        """Test factory function using settings defaults."""
        with patch('src.integrations.ai_client.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "settings-openai-key"
            mock_settings.ANTHROPIC_API_KEY = None
            
            client = create_ai_client()
            
            assert isinstance(client, AIClient)
            assert "openai" in client.providers