"""
Unit tests for Quality Validation Service.

Tests T061: Comprehensive validation logic for content quality assessment.
Covers QualityValidationService methods, pedagogical alignment, objective coverage,
readability analysis, and bias detection functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.services.quality_validation_service import (
    QualityValidationService,
    QualityValidationRequest,
    QualityValidationResult,
    ObjectiveCoverageResult,
    PedagogicalAlignmentResult,
    ContentAccuracyResult,
)
from src.models.enums import ProficiencyLevel, CognitiveLevel
from src.integrations.ai_client import AIClient, ContentValidationRequest


class TestQualityValidationRequest:
    """Test QualityValidationRequest model validation."""
    
    def test_valid_validation_request(self):
        """Test creating valid validation request."""
        request = QualityValidationRequest(
            content="This is a comprehensive educational content piece that covers multiple learning objectives with detailed explanations and examples.",
            learning_objectives=["Understand concepts", "Apply knowledge", "Analyze problems"],
            target_level=ProficiencyLevel.INTERMEDIATE,
            subject_domain="Computer Science",
            expected_keywords=["algorithm", "data structure"],
            chapter_context="Introduction to algorithms chapter",
        )
        
        assert len(request.content) >= 100
        assert len(request.learning_objectives) >= 1
        assert request.target_level == ProficiencyLevel.INTERMEDIATE
        assert request.subject_domain == "Computer Science"
        assert "algorithm" in request.expected_keywords
    
    def test_content_length_validation(self):
        """Test content minimum length validation."""
        with pytest.raises(ValueError) as exc_info:
            QualityValidationRequest(
                content="Too short content",  # Less than 100 characters
                learning_objectives=["Learn something"],
                target_level=ProficiencyLevel.BEGINNER,
                subject_domain="Test",
            )
        assert "at least 100 characters" in str(exc_info.value)
    
    def test_learning_objectives_validation(self):
        """Test learning objectives validation."""
        long_content = "A" * 100  # Minimum content length
        
        with pytest.raises(ValueError) as exc_info:
            QualityValidationRequest(
                content=long_content,
                learning_objectives=[],  # Empty list
                target_level=ProficiencyLevel.BEGINNER,
                subject_domain="Test",
            )
        assert "at least 1 item" in str(exc_info.value)


class TestQualityValidationService:
    """Test QualityValidationService core functionality."""
    
    @pytest.fixture
    def service(self):
        """Create service instance with mock AI client."""
        mock_ai_client = Mock(spec=AIClient)
        return QualityValidationService(ai_client=mock_ai_client)
    
    @pytest.fixture
    def service_no_ai(self):
        """Create service instance without AI client."""
        return QualityValidationService(ai_client=None)
    
    @pytest.fixture
    def sample_request(self):
        """Create sample validation request."""
        return QualityValidationRequest(
            content="""
            This is a comprehensive educational content about machine learning algorithms.
            Machine learning is a subset of artificial intelligence that enables computers
            to learn and make decisions without being explicitly programmed. The main types
            of machine learning include supervised learning, unsupervised learning, and
            reinforcement learning. Supervised learning uses labeled data to train models
            that can make predictions on new data. Common algorithms include linear regression,
            decision trees, and neural networks. Each algorithm has its own strengths and
            weaknesses depending on the problem domain and data characteristics.
            """,
            learning_objectives=[
                "Understand machine learning fundamentals",
                "Identify different types of machine learning",
                "Compare supervised and unsupervised learning",
                "Apply appropriate algorithms to problems",
            ],
            target_level=ProficiencyLevel.INTERMEDIATE,
            subject_domain="Computer Science",
            expected_keywords=["machine learning", "algorithm", "supervised", "unsupervised"],
        )
    
    def test_service_initialization_with_ai(self):
        """Test service initialization with AI client."""
        mock_ai_client = Mock(spec=AIClient)
        service = QualityValidationService(ai_client=mock_ai_client)
        
        assert service.ai_client == mock_ai_client
        assert service.READABILITY_THRESHOLDS[ProficiencyLevel.BEGINNER] == 70.0
        assert service.MIN_QUALITY_THRESHOLDS["overall_score"] == 0.75
    
    def test_service_initialization_without_ai(self):
        """Test service initialization without AI client."""
        service = QualityValidationService(ai_client=None)
        
        assert service.ai_client is None
    
    @pytest.mark.asyncio
    async def test_validate_course_quality_success(self, service, sample_request):
        """Test comprehensive course quality validation success path."""
        # Mock AI client responses
        service.ai_client.validate_content_quality = AsyncMock(return_value=Mock(
            overall_score=0.85,
            content_accuracy=0.90,
            recommendations=["Good quality content"],
            issues_found=[],
        ))
        service.ai_client.analyze_readability = AsyncMock(return_value=Mock(
            flesch_reading_ease=75.0,
            recommendations=[],
        ))
        service.ai_client.check_bias_detection = AsyncMock(return_value=Mock(
            overall_bias_score=0.05,
            recommendations=[],
            dict=lambda: {"overall_bias_score": 0.05},
        ))
        
        result = await service.validate_course_quality(
            course_content=sample_request.content,
            learning_objectives=sample_request.learning_objectives,
            target_level=sample_request.target_level,
            subject_domain=sample_request.subject_domain,
        )
        
        assert isinstance(result, QualityValidationResult)
        assert result.overall_score > 0.0
        assert result.readability_score >= 0.0
        assert result.pedagogical_alignment >= 0.0
        assert result.objective_coverage >= 0.0
        assert result.content_accuracy >= 0.0
        assert result.bias_detection_score >= 0.0
        assert isinstance(result.validation_timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_validate_course_quality_with_errors(self, service, sample_request):
        """Test validation handling of individual method errors."""
        # Mock some methods to fail
        service.ai_client.validate_content_quality = AsyncMock(side_effect=Exception("AI service failed"))
        service.ai_client.analyze_readability = AsyncMock(return_value=Mock(
            flesch_reading_ease=60.0,
            recommendations=[],
        ))
        service.ai_client.check_bias_detection = AsyncMock(return_value=Mock(
            overall_bias_score=0.08,
            recommendations=[],
            dict=lambda: {"overall_bias_score": 0.08},
        ))
        
        result = await service.validate_course_quality(
            course_content=sample_request.content,
            learning_objectives=sample_request.learning_objectives,
            target_level=sample_request.target_level,
            subject_domain=sample_request.subject_domain,
        )
        
        assert isinstance(result, QualityValidationResult)
        assert len(result.validation_errors) > 0
        assert "Accuracy analysis failed" in result.validation_errors[0]
        # Should still have some results from successful methods
        assert result.readability_score > 0
    
    @pytest.mark.asyncio
    async def test_check_readability_score_with_ai(self, service, sample_request):
        """Test readability analysis with AI client."""
        mock_readability_response = Mock()
        mock_readability_response.flesch_reading_ease = 78.5
        mock_readability_response.recommendations = []
        
        service.ai_client.analyze_readability = AsyncMock(return_value=mock_readability_response)
        
        result = await service.check_readability_score(sample_request)
        
        assert result.flesch_reading_ease == 78.5
        assert len(result.recommendations) == 0
        service.ai_client.analyze_readability.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_readability_score_fallback(self, service_no_ai, sample_request):
        """Test readability analysis fallback without AI."""
        result = await service_no_ai.check_readability_score(sample_request)
        
        assert hasattr(result, 'flesch_reading_ease')
        assert result.flesch_reading_ease >= 0
        assert result.flesch_reading_ease <= 100
    
    @pytest.mark.asyncio
    async def test_validate_pedagogical_alignment(self, service, sample_request):
        """Test pedagogical alignment validation."""
        result = await service.validate_pedagogical_alignment(sample_request)
        
        assert isinstance(result, PedagogicalAlignmentResult)
        assert 0.0 <= result.alignment_score <= 1.0
        assert 0.0 <= result.level_appropriateness <= 1.0
        assert 0.0 <= result.bloom_taxonomy_compliance <= 1.0
        assert 0.0 <= result.scaffolding_quality <= 1.0
        assert isinstance(result.cognitive_distribution, dict)
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_assess_objective_coverage(self, service, sample_request):
        """Test learning objective coverage assessment."""
        result = await service.assess_objective_coverage(sample_request)
        
        assert isinstance(result, ObjectiveCoverageResult)
        assert 0.0 <= result.overall_coverage <= 1.0
        assert len(result.objective_scores) == len(sample_request.learning_objectives)
        assert isinstance(result.missing_objectives, list)
        assert isinstance(result.well_covered_objectives, list)
        assert isinstance(result.recommendations, list)
        
        # Check that all objectives are scored
        for objective in sample_request.learning_objectives:
            assert objective in result.objective_scores
            assert 0.0 <= result.objective_scores[objective] <= 1.0
    
    @pytest.mark.asyncio
    async def test_validate_content_accuracy_with_ai(self, service, sample_request):
        """Test content accuracy validation with AI."""
        mock_ai_response = Mock()
        mock_ai_response.content_accuracy = 0.92
        mock_ai_response.overall_score = 0.88
        mock_ai_response.recommendations = ["Content is accurate"]
        mock_ai_response.issues_found = []
        
        service.ai_client.validate_content_quality = AsyncMock(return_value=mock_ai_response)
        
        result = await service.validate_content_accuracy(sample_request)
        
        assert isinstance(result, ContentAccuracyResult)
        assert 0.0 <= result.accuracy_score <= 1.0
        assert 0.0 <= result.factual_consistency <= 1.0
        assert 0.0 <= result.technical_correctness <= 1.0
        assert 0.0 <= result.source_reliability <= 1.0
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_validate_content_accuracy_fallback(self, service_no_ai, sample_request):
        """Test content accuracy validation fallback."""
        result = await service_no_ai.validate_content_accuracy(sample_request)
        
        assert isinstance(result, ContentAccuracyResult)
        assert result.accuracy_score >= 0.5  # Baseline fallback
        assert "Manual fact-checking recommended" in result.recommendations[0]
    
    @pytest.mark.asyncio
    async def test_detect_content_bias_with_ai(self, service, sample_request):
        """Test bias detection with AI client."""
        mock_bias_response = Mock()
        mock_bias_response.overall_bias_score = 0.03
        mock_bias_response.recommendations = []
        mock_bias_response.dict = lambda: {"overall_bias_score": 0.03}
        
        service.ai_client.check_bias_detection = AsyncMock(return_value=mock_bias_response)
        
        result = await service.detect_content_bias(sample_request)
        
        assert hasattr(result, 'overall_bias_score')
        assert 0.0 <= result.overall_bias_score <= 1.0
        service.ai_client.check_bias_detection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_content_bias_fallback(self, service_no_ai, sample_request):
        """Test bias detection fallback without AI."""
        result = await service_no_ai.detect_content_bias(sample_request)
        
        assert hasattr(result, 'overall_bias_score')
        assert 0.0 <= result.overall_bias_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_generate_quality_report(self, service):
        """Test quality report generation."""
        # Create mock validation result
        validation_result = QualityValidationResult(
            overall_score=0.85,
            readability_score=78.0,
            pedagogical_alignment=0.88,
            objective_coverage=0.95,
            content_accuracy=0.92,
            bias_detection_score=0.05,
            meets_quality_standards=True,
            validation_warnings=[],
            validation_errors=[],
        )
        
        report = await service.generate_quality_report(validation_result)
        
        assert isinstance(report, dict)
        assert "executive_summary" in report
        assert "quality_metrics" in report
        assert "meets_standards" in report
        assert "validation_timestamp" in report
        assert "detailed_analysis" in report
        assert "recommendations" in report
        assert "action_items" in report
        assert "quality_gates" in report
        
        assert report["meets_standards"] == True
        assert report["quality_metrics"]["overall_score"] == 0.85


class TestQualityValidationBusinessLogic:
    """Test business logic and validation rules."""
    
    @pytest.fixture
    def service(self):
        return QualityValidationService(ai_client=None)
    
    def test_readability_thresholds_by_level(self, service):
        """Test readability thresholds for different proficiency levels."""
        thresholds = service.READABILITY_THRESHOLDS
        
        assert thresholds[ProficiencyLevel.BEGINNER] == 70.0
        assert thresholds[ProficiencyLevel.INTERMEDIATE] == 60.0
        assert thresholds[ProficiencyLevel.ADVANCED] == 50.0
        assert thresholds[ProficiencyLevel.EXPERT] == 0.0
        
        # Beginner should have highest threshold (easiest to read)
        assert thresholds[ProficiencyLevel.BEGINNER] > thresholds[ProficiencyLevel.INTERMEDIATE]
        assert thresholds[ProficiencyLevel.INTERMEDIATE] > thresholds[ProficiencyLevel.ADVANCED]
    
    def test_cognitive_level_distributions(self, service):
        """Test cognitive level distributions for different proficiency levels."""
        distributions = service.COGNITIVE_DISTRIBUTIONS
        
        # Test that all levels have distributions
        for level in ProficiencyLevel:
            assert level in distributions
            distribution = distributions[level]
            
            # Test that distributions sum to approximately 1.0
            total = sum(distribution.values())
            assert abs(total - 1.0) < 0.01
            
            # Test that all cognitive levels are represented
            for cognitive_level in CognitiveLevel:
                assert cognitive_level in distribution
                assert 0.0 <= distribution[cognitive_level] <= 1.0
        
        # Test progression: beginners should have more remember/understand
        beginner_dist = distributions[ProficiencyLevel.BEGINNER]
        expert_dist = distributions[ProficiencyLevel.EXPERT]
        
        assert beginner_dist[CognitiveLevel.REMEMBER] > expert_dist[CognitiveLevel.REMEMBER]
        assert beginner_dist[CognitiveLevel.UNDERSTAND] > expert_dist[CognitiveLevel.UNDERSTAND]
        assert beginner_dist[CognitiveLevel.CREATE] < expert_dist[CognitiveLevel.CREATE]
    
    def test_quality_thresholds(self, service):
        """Test minimum quality thresholds."""
        thresholds = service.MIN_QUALITY_THRESHOLDS
        
        assert thresholds["overall_score"] == 0.75
        assert thresholds["pedagogical_alignment"] == 0.80
        assert thresholds["objective_coverage"] == 1.0  # 100% required
        assert thresholds["content_accuracy"] == 0.90
        assert thresholds["bias_detection_max"] == 0.10
    
    def test_calculate_overall_score(self, service):
        """Test overall score calculation logic."""
        # Test with perfect scores
        perfect_score = service._calculate_overall_score(
            readability=100.0,
            pedagogical=1.0,
            coverage=1.0,
            accuracy=1.0,
            bias=0.0,
            level=ProficiencyLevel.INTERMEDIATE
        )
        assert perfect_score == 1.0
        
        # Test with mixed scores
        mixed_score = service._calculate_overall_score(
            readability=80.0,  # 0.8 normalized
            pedagogical=0.8,
            coverage=0.9,
            accuracy=0.85,
            bias=0.05,  # 0.95 quality (inverted)
            level=ProficiencyLevel.INTERMEDIATE
        )
        assert 0.7 <= mixed_score <= 0.9
        
        # Test with poor scores
        poor_score = service._calculate_overall_score(
            readability=40.0,  # 0.4 normalized
            pedagogical=0.5,
            coverage=0.6,
            accuracy=0.7,
            bias=0.2,  # 0.8 quality (inverted)
            level=ProficiencyLevel.INTERMEDIATE
        )
        assert poor_score < 0.7
    
    def test_check_quality_standards(self, service):
        """Test quality standards checking."""
        # Test passing all standards
        passes = service._check_quality_standards(
            overall=0.85,
            readability=75.0,
            pedagogical=0.85,
            coverage=1.0,
            accuracy=0.95,
            bias=0.05,
            level=ProficiencyLevel.INTERMEDIATE
        )
        assert passes == True
        
        # Test failing coverage requirement
        fails_coverage = service._check_quality_standards(
            overall=0.85,
            readability=75.0,
            pedagogical=0.85,
            coverage=0.9,  # Less than required 1.0
            accuracy=0.95,
            bias=0.05,
            level=ProficiencyLevel.INTERMEDIATE
        )
        assert fails_coverage == False
        
        # Test failing readability for level
        fails_readability = service._check_quality_standards(
            overall=0.85,
            readability=50.0,  # Below intermediate threshold of 60.0
            pedagogical=0.85,
            coverage=1.0,
            accuracy=0.95,
            bias=0.05,
            level=ProficiencyLevel.INTERMEDIATE
        )
        assert fails_readability == False
    
    def test_generate_quality_warnings(self, service):
        """Test quality warning generation."""
        warnings = service._generate_quality_warnings(
            readability=50.0,  # Below intermediate threshold
            pedagogical=0.70,  # Below threshold
            coverage=0.85,    # Below required 1.0
            accuracy=0.85,    # Below threshold
            bias=0.15,        # Above maximum
            level=ProficiencyLevel.INTERMEDIATE
        )
        
        assert len(warnings) == 5  # Should have warning for each failed metric
        assert any("Readability score" in warning for warning in warnings)
        assert any("Pedagogical alignment" in warning for warning in warnings)
        assert any("Objective coverage" in warning for warning in warnings)
        assert any("Content accuracy" in warning for warning in warnings)
        assert any("Bias detection score" in warning for warning in warnings)


class TestQualityValidationHelpers:
    """Test helper methods and utilities."""
    
    @pytest.fixture
    def service(self):
        return QualityValidationService(ai_client=None)
    
    @pytest.mark.asyncio
    async def test_analyze_cognitive_levels(self, service):
        """Test cognitive level analysis."""
        content = """
        Remember these key concepts: variables, functions, and loops.
        Understand how they work together in programming.
        Apply these concepts to solve real problems.
        Analyze the efficiency of different approaches.
        Evaluate which solution is best.
        Create your own innovative solutions.
        """
        
        distribution = await service._analyze_cognitive_levels(content)
        
        assert isinstance(distribution, dict)
        assert len(distribution) == 6  # All cognitive levels
        
        # Should find examples of each cognitive level
        assert distribution["remember"] > 0
        assert distribution["understand"] > 0
        assert distribution["apply"] > 0
        assert distribution["analyze"] > 0
        assert distribution["evaluate"] > 0
        assert distribution["create"] > 0
        
        # Total should sum to 1.0 (normalized)
        total = sum(distribution.values())
        assert abs(total - 1.0) < 0.01
    
    def test_calculate_distribution_alignment(self, service):
        """Test cognitive distribution alignment calculation."""
        # Perfect alignment
        expected = {
            CognitiveLevel.REMEMBER: 0.3,
            CognitiveLevel.UNDERSTAND: 0.3,
            CognitiveLevel.APPLY: 0.2,
            CognitiveLevel.ANALYZE: 0.1,
            CognitiveLevel.EVALUATE: 0.1,
            CognitiveLevel.CREATE: 0.0,
        }
        
        actual_perfect = {
            "remember": 0.3,
            "understand": 0.3,
            "apply": 0.2,
            "analyze": 0.1,
            "evaluate": 0.1,
            "create": 0.0,
        }
        
        alignment = service._calculate_distribution_alignment(actual_perfect, expected)
        assert alignment == 1.0
        
        # Partial alignment
        actual_partial = {
            "remember": 0.5,  # Higher than expected
            "understand": 0.2,  # Lower than expected
            "apply": 0.2,
            "analyze": 0.1,
            "evaluate": 0.0,   # Lower than expected
            "create": 0.0,
        }
        
        alignment = service._calculate_distribution_alignment(actual_partial, expected)
        assert 0.0 <= alignment < 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_objective_coverage(self, service):
        """Test learning objective coverage analysis."""
        content = """
        This content covers machine learning algorithms including supervised learning
        and unsupervised learning. We will understand the fundamentals of neural networks
        and how to apply them to classification problems.
        """
        
        objective = "Understand machine learning fundamentals"
        subject_domain = "Computer Science"
        
        coverage = await service._analyze_objective_coverage(content, objective, subject_domain)
        
        assert 0.0 <= coverage <= 1.0
        # Should have decent coverage since content mentions machine learning and fundamentals
        assert coverage > 0.3
    
    @pytest.mark.asyncio
    async def test_assess_source_reliability(self, service):
        """Test source reliability assessment."""
        # Content with reliability indicators
        reliable_content = """
        According to research published in Nature, machine learning algorithms
        have shown significant improvements. Studies indicate that peer-reviewed
        methodologies are most effective. The Journal of AI Research demonstrates
        these findings with rigorous experimental validation.
        """
        
        reliability = await service._assess_source_reliability(reliable_content)
        assert 0.5 <= reliability <= 1.0  # Should score well
        
        # Content without reliability indicators
        unreliable_content = """
        I think machine learning is cool and everyone should use it.
        My friend told me that AI will solve everything.
        """
        
        reliability = await service._assess_source_reliability(unreliable_content)
        assert reliability == 0.5  # Baseline minimum
    
    @pytest.mark.asyncio
    async def test_assess_educational_bias(self, service):
        """Test educational bias assessment."""
        # Balanced content
        balanced_content = """
        Students can see visual diagrams, hear audio explanations,
        and practice hands-on exercises to build understanding.
        """
        
        bias = await service._assess_educational_bias(balanced_content, ProficiencyLevel.INTERMEDIATE)
        assert bias < 0.3  # Should be low bias
        
        # Biased content (only visual)
        biased_content = """
        Look at this diagram. See how the chart shows the data.
        Visual learners will understand by looking at these images.
        The visual representation makes everything clear to see.
        """
        
        bias = await service._assess_educational_bias(biased_content, ProficiencyLevel.INTERMEDIATE)
        assert bias > 0.0  # Should detect some bias