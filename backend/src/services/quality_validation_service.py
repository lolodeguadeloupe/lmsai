"""
Content quality validation service for course generation platform.

Implementation of T035: Comprehensive quality validation following QualityMetrics
from data-model.md with AI-powered pedagogical assessment and bias detection.

Key Features:
- Comprehensive quality validation against learning objectives
- AI-powered pedagogical alignment assessment  
- Readability analysis with level-appropriate thresholds
- Content bias detection and fairness assessment
- Objective coverage validation
- Cognitive level distribution analysis
- Integration with AI client for advanced validation
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator

from ..integrations.ai_client import (
    AIClient,
    BiasDetectionRequest,
    ContentValidationRequest,
    ReadabilityAnalysisRequest,
    create_ai_client,
)
from ..models.course import QualityMetrics
from ..models.enums import CognitiveLevel, ProficiencyLevel

# Configure logging
logger = logging.getLogger(__name__)


class QualityValidationRequest(BaseModel):
    """Request model for quality validation."""
    
    content: str = Field(..., min_length=100, description="Content to validate")
    learning_objectives: List[str] = Field(..., min_items=1, description="Learning objectives to validate against")
    target_level: ProficiencyLevel = Field(..., description="Target proficiency level")
    subject_domain: str = Field(..., min_length=2, description="Subject domain")
    cognitive_levels: Optional[List[CognitiveLevel]] = Field(
        default=None, description="Expected cognitive levels for validation"
    )
    expected_keywords: Optional[List[str]] = Field(
        default_factory=list, description="Keywords that should be present"
    )
    chapter_context: Optional[str] = Field(
        default=None, description="Additional context from chapter/course"
    )


class ObjectiveCoverageResult(BaseModel):
    """Result of objective coverage analysis."""
    
    overall_coverage: float = Field(..., ge=0.0, le=1.0)
    objective_scores: Dict[str, float] = Field(default_factory=dict)
    missing_objectives: List[str] = Field(default_factory=list)
    well_covered_objectives: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class PedagogicalAlignmentResult(BaseModel):
    """Result of pedagogical alignment analysis."""
    
    alignment_score: float = Field(..., ge=0.0, le=1.0)
    cognitive_distribution: Dict[str, float] = Field(default_factory=dict)
    level_appropriateness: float = Field(..., ge=0.0, le=1.0)
    bloom_taxonomy_compliance: float = Field(..., ge=0.0, le=1.0)
    scaffolding_quality: float = Field(..., ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)


class ContentAccuracyResult(BaseModel):
    """Result of content accuracy analysis."""
    
    accuracy_score: float = Field(..., ge=0.0, le=1.0)
    factual_consistency: float = Field(..., ge=0.0, le=1.0)
    technical_correctness: float = Field(..., ge=0.0, le=1.0)
    source_reliability: float = Field(..., ge=0.0, le=1.0)
    issues_found: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class QualityValidationResult(BaseModel):
    """Comprehensive quality validation result."""
    
    overall_score: float = Field(..., ge=0.0, le=1.0)
    readability_score: float = Field(..., ge=0.0, le=100.0)
    pedagogical_alignment: float = Field(..., ge=0.0, le=1.0)
    objective_coverage: float = Field(..., ge=0.0, le=1.0)
    content_accuracy: float = Field(..., ge=0.0, le=1.0)
    bias_detection_score: float = Field(..., ge=0.0, le=1.0)
    
    # Detailed results
    readability_details: Optional[Dict[str, Any]] = None
    pedagogical_details: Optional[PedagogicalAlignmentResult] = None
    coverage_details: Optional[ObjectiveCoverageResult] = None
    accuracy_details: Optional[ContentAccuracyResult] = None
    bias_details: Optional[Dict[str, Any]] = None
    
    # Meta information
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    meets_quality_standards: bool = Field(default=False)
    validation_warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)


class QualityValidationService:
    """Service for comprehensive content quality validation."""
    
    # Quality thresholds by proficiency level (from test requirements)
    READABILITY_THRESHOLDS = {
        ProficiencyLevel.BEGINNER: 70.0,
        ProficiencyLevel.INTERMEDIATE: 60.0,
        ProficiencyLevel.ADVANCED: 50.0,
        ProficiencyLevel.EXPERT: 0.0,  # No strict minimum for expert level
    }
    
    # Cognitive level distribution expectations by proficiency level
    COGNITIVE_DISTRIBUTIONS = {
        ProficiencyLevel.BEGINNER: {
            CognitiveLevel.REMEMBER: 0.35,
            CognitiveLevel.UNDERSTAND: 0.35,
            CognitiveLevel.APPLY: 0.20,
            CognitiveLevel.ANALYZE: 0.10,
            CognitiveLevel.EVALUATE: 0.0,
            CognitiveLevel.CREATE: 0.0,
        },
        ProficiencyLevel.INTERMEDIATE: {
            CognitiveLevel.REMEMBER: 0.20,
            CognitiveLevel.UNDERSTAND: 0.30,
            CognitiveLevel.APPLY: 0.30,
            CognitiveLevel.ANALYZE: 0.15,
            CognitiveLevel.EVALUATE: 0.05,
            CognitiveLevel.CREATE: 0.0,
        },
        ProficiencyLevel.ADVANCED: {
            CognitiveLevel.REMEMBER: 0.10,
            CognitiveLevel.UNDERSTAND: 0.20,
            CognitiveLevel.APPLY: 0.25,
            CognitiveLevel.ANALYZE: 0.25,
            CognitiveLevel.EVALUATE: 0.15,
            CognitiveLevel.CREATE: 0.05,
        },
        ProficiencyLevel.EXPERT: {
            CognitiveLevel.REMEMBER: 0.05,
            CognitiveLevel.UNDERSTAND: 0.15,
            CognitiveLevel.APPLY: 0.20,
            CognitiveLevel.ANALYZE: 0.25,
            CognitiveLevel.EVALUATE: 0.20,
            CognitiveLevel.CREATE: 0.15,
        },
    }
    
    # Minimum quality thresholds
    MIN_QUALITY_THRESHOLDS = {
        "overall_score": 0.75,
        "pedagogical_alignment": 0.80,
        "objective_coverage": 1.0,  # 100% coverage required (FR-012)
        "content_accuracy": 0.90,
        "bias_detection_max": 0.10,  # Low bias tolerance
    }
    
    def __init__(self, ai_client: Optional[AIClient] = None):
        """Initialize quality validation service."""
        self.ai_client = ai_client or create_ai_client()
        if not self.ai_client:
            logger.warning("AI client not available, some validation features will be limited")
    
    async def validate_course_quality(
        self,
        course_content: str,
        learning_objectives: List[str],
        target_level: ProficiencyLevel,
        subject_domain: str,
        **kwargs
    ) -> QualityValidationResult:
        """
        Perform comprehensive course quality validation.
        
        This is the main entry point for quality validation that combines
        all validation methods to provide a complete quality assessment.
        
        Args:
            course_content: Full course content to validate
            learning_objectives: Course learning objectives
            target_level: Target proficiency level
            subject_domain: Subject domain (e.g., "Computer Science")
            **kwargs: Additional validation parameters
            
        Returns:
            QualityValidationResult: Comprehensive validation results
        """
        logger.info(f"Starting comprehensive quality validation for {target_level.value} level course")
        
        request = QualityValidationRequest(
            content=course_content,
            learning_objectives=learning_objectives,
            target_level=target_level,
            subject_domain=subject_domain,
            **kwargs
        )
        
        try:
            # Run all validation methods concurrently
            validation_tasks = [
                self.check_readability_score(request),
                self.validate_pedagogical_alignment(request),
                self.assess_objective_coverage(request),
                self.validate_content_accuracy(request),
                self.detect_content_bias(request),
            ]
            
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            readability_result, pedagogical_result, coverage_result, accuracy_result, bias_result = results
            
            # Handle exceptions in results
            validation_errors = []
            validation_warnings = []
            
            if isinstance(readability_result, Exception):
                validation_errors.append(f"Readability analysis failed: {str(readability_result)}")
                readability_result = None
            
            if isinstance(pedagogical_result, Exception):
                validation_errors.append(f"Pedagogical analysis failed: {str(pedagogical_result)}")
                pedagogical_result = None
            
            if isinstance(coverage_result, Exception):
                validation_errors.append(f"Coverage analysis failed: {str(coverage_result)}")
                coverage_result = None
            
            if isinstance(accuracy_result, Exception):
                validation_errors.append(f"Accuracy analysis failed: {str(accuracy_result)}")
                accuracy_result = None
            
            if isinstance(bias_result, Exception):
                validation_errors.append(f"Bias analysis failed: {str(bias_result)}")
                bias_result = None
            
            # Extract scores with fallbacks
            readability_score = getattr(readability_result, 'flesch_reading_ease', 50.0) if readability_result else 50.0
            pedagogical_score = getattr(pedagogical_result, 'alignment_score', 0.5) if pedagogical_result else 0.5
            coverage_score = getattr(coverage_result, 'overall_coverage', 0.5) if coverage_result else 0.5
            accuracy_score = getattr(accuracy_result, 'accuracy_score', 0.5) if accuracy_result else 0.5
            bias_score = getattr(bias_result, 'overall_bias_score', 0.5) if bias_result else 0.5
            
            # Calculate overall score with weighted average
            overall_score = self._calculate_overall_score(
                readability_score, pedagogical_score, coverage_score, accuracy_score, bias_score, target_level
            )
            
            # Check if meets quality standards
            meets_standards = self._check_quality_standards(
                overall_score, readability_score, pedagogical_score, 
                coverage_score, accuracy_score, bias_score, target_level
            )
            
            # Generate warnings
            if not meets_standards:
                validation_warnings.extend(self._generate_quality_warnings(
                    readability_score, pedagogical_score, coverage_score, 
                    accuracy_score, bias_score, target_level
                ))
            
            return QualityValidationResult(
                overall_score=overall_score,
                readability_score=readability_score,
                pedagogical_alignment=pedagogical_score,
                objective_coverage=coverage_score,
                content_accuracy=accuracy_score,
                bias_detection_score=bias_score,
                readability_details=readability_result.dict() if readability_result else None,
                pedagogical_details=pedagogical_result if pedagogical_result else None,
                coverage_details=coverage_result if coverage_result else None,
                accuracy_details=accuracy_result if accuracy_result else None,
                bias_details=bias_result.dict() if bias_result else None,
                meets_quality_standards=meets_standards,
                validation_warnings=validation_warnings,
                validation_errors=validation_errors,
            )
            
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            raise RuntimeError(f"Quality validation process failed: {str(e)}")
    
    async def check_readability_score(
        self, request: QualityValidationRequest
    ) -> Optional[Any]:
        """
        Analyze content readability and ensure it meets level-appropriate thresholds.
        
        Uses both statistical readability measures and AI-powered analysis
        to assess if content complexity matches the target proficiency level.
        
        Args:
            request: Quality validation request
            
        Returns:
            ReadabilityAnalysisResponse: Detailed readability analysis
        """
        try:
            if not self.ai_client:
                # Fallback to basic analysis without AI
                return await self._basic_readability_analysis(request)
            
            readability_request = ReadabilityAnalysisRequest(
                content=request.content,
                target_level=request.target_level,
                content_type="educational"
            )
            
            result = await self.ai_client.analyze_readability(readability_request)
            
            # Validate against level-specific thresholds
            threshold = self.READABILITY_THRESHOLDS[request.target_level]
            if result.flesch_reading_ease < threshold:
                result.recommendations.append(
                    f"Readability score {result.flesch_reading_ease:.1f} below {request.target_level.value} "
                    f"level threshold of {threshold}. Consider simplifying language and sentence structure."
                )
            
            logger.info(f"Readability analysis completed: {result.flesch_reading_ease:.1f}/100 (target: ≥{threshold})")
            return result
            
        except Exception as e:
            logger.error(f"Readability analysis failed: {e}")
            # Return basic fallback result
            return await self._basic_readability_analysis(request)
    
    async def validate_pedagogical_alignment(
        self, request: QualityValidationRequest
    ) -> PedagogicalAlignmentResult:
        """
        Validate content alignment with Bloom's taxonomy and pedagogical best practices.
        
        Analyzes cognitive level distribution, learning progression scaffolding,
        and appropriateness for the target proficiency level.
        
        Args:
            request: Quality validation request
            
        Returns:
            PedagogicalAlignmentResult: Detailed pedagogical alignment analysis
        """
        try:
            # Analyze cognitive level distribution
            cognitive_distribution = await self._analyze_cognitive_levels(request.content)
            
            # Check alignment with expected distribution for proficiency level
            expected_distribution = self.COGNITIVE_DISTRIBUTIONS[request.target_level]
            level_appropriateness = self._calculate_distribution_alignment(
                cognitive_distribution, expected_distribution
            )
            
            # Analyze Bloom's taxonomy compliance
            bloom_compliance = await self._analyze_bloom_taxonomy_compliance(
                request.content, request.learning_objectives, request.target_level
            )
            
            # Assess scaffolding quality
            scaffolding_quality = await self._assess_scaffolding_quality(
                request.content, request.target_level
            )
            
            # Calculate overall alignment score
            alignment_score = (level_appropriateness * 0.4 + bloom_compliance * 0.4 + scaffolding_quality * 0.2)
            
            # Generate recommendations
            recommendations = []
            if level_appropriateness < 0.8:
                recommendations.append(
                    f"Cognitive level distribution doesn't match {request.target_level.value} expectations"
                )
            if bloom_compliance < 0.8:
                recommendations.append("Content doesn't align well with Bloom's taxonomy progression")
            if scaffolding_quality < 0.8:
                recommendations.append("Learning progression lacks adequate scaffolding")
            
            return PedagogicalAlignmentResult(
                alignment_score=alignment_score,
                cognitive_distribution=cognitive_distribution,
                level_appropriateness=level_appropriateness,
                bloom_taxonomy_compliance=bloom_compliance,
                scaffolding_quality=scaffolding_quality,
                recommendations=recommendations,
            )
            
        except Exception as e:
            logger.error(f"Pedagogical alignment analysis failed: {e}")
            # Return default result with warning
            return PedagogicalAlignmentResult(
                alignment_score=0.5,
                recommendations=[f"Pedagogical analysis failed: {str(e)}"],
            )
    
    async def assess_objective_coverage(
        self, request: QualityValidationRequest
    ) -> ObjectiveCoverageResult:
        """
        Assess how well the content covers the specified learning objectives.
        
        Uses semantic analysis to determine if each learning objective
        is adequately addressed in the content.
        
        Args:
            request: Quality validation request
            
        Returns:
            ObjectiveCoverageResult: Detailed objective coverage analysis
        """
        try:
            objective_scores = {}
            missing_objectives = []
            well_covered_objectives = []
            
            for objective in request.learning_objectives:
                # Analyze coverage of each objective
                coverage_score = await self._analyze_objective_coverage(
                    request.content, objective, request.subject_domain
                )
                
                objective_scores[objective] = coverage_score
                
                if coverage_score >= 0.8:
                    well_covered_objectives.append(objective)
                elif coverage_score < 0.5:
                    missing_objectives.append(objective)
            
            # Calculate overall coverage (FR-012 requires 100%)
            overall_coverage = sum(objective_scores.values()) / len(objective_scores) if objective_scores else 0.0
            
            # Generate recommendations
            recommendations = []
            if overall_coverage < 1.0:
                recommendations.append(
                    f"Overall objective coverage is {overall_coverage:.1%}, but 100% coverage is required (FR-012)"
                )
            
            for missing_obj in missing_objectives:
                recommendations.append(f"Learning objective poorly covered: '{missing_obj}'")
            
            if not well_covered_objectives and request.learning_objectives:
                recommendations.append("No learning objectives are well covered - content needs significant revision")
            
            return ObjectiveCoverageResult(
                overall_coverage=overall_coverage,
                objective_scores=objective_scores,
                missing_objectives=missing_objectives,
                well_covered_objectives=well_covered_objectives,
                recommendations=recommendations,
            )
            
        except Exception as e:
            logger.error(f"Objective coverage analysis failed: {e}")
            return ObjectiveCoverageResult(
                overall_coverage=0.5,
                recommendations=[f"Objective coverage analysis failed: {str(e)}"],
            )
    
    async def validate_content_accuracy(
        self, request: QualityValidationRequest
    ) -> ContentAccuracyResult:
        """
        Validate content accuracy through AI-powered fact-checking and consistency analysis.
        
        Assesses factual consistency, technical correctness, and source reliability
        to ensure content meets educational quality standards.
        
        Args:
            request: Quality validation request
            
        Returns:
            ContentAccuracyResult: Detailed content accuracy analysis
        """
        try:
            if not self.ai_client:
                # Fallback to basic accuracy assessment
                return await self._basic_accuracy_assessment(request)
            
            # Use AI client for comprehensive content validation
            validation_request = ContentValidationRequest(
                content=request.content,
                target_level=request.target_level,
                learning_objectives=request.learning_objectives,
                subject_domain=request.subject_domain,
                expected_keywords=request.expected_keywords,
            )
            
            ai_result = await self.ai_client.validate_content_quality(validation_request)
            
            # Extract accuracy components from AI analysis
            factual_consistency = ai_result.content_accuracy
            technical_correctness = ai_result.overall_score  # AI overall score reflects technical quality
            
            # Assess source reliability (basic heuristic)
            source_reliability = await self._assess_source_reliability(request.content)
            
            # Calculate overall accuracy score
            accuracy_score = (factual_consistency * 0.5 + technical_correctness * 0.3 + source_reliability * 0.2)
            
            # Convert AI issues to our format
            issues_found = []
            for issue in ai_result.issues_found:
                issues_found.append({
                    "type": issue.get("type", "accuracy"),
                    "severity": issue.get("severity", "medium"),
                    "description": issue.get("description", "Content accuracy issue"),
                    "location": issue.get("location", "general"),
                    "suggestion": f"Review and verify: {issue.get('description', 'accuracy concern')}",
                })
            
            recommendations = list(ai_result.recommendations)
            if accuracy_score < 0.9:
                recommendations.append("Content accuracy below required threshold of 90%")
            
            return ContentAccuracyResult(
                accuracy_score=accuracy_score,
                factual_consistency=factual_consistency,
                technical_correctness=technical_correctness,
                source_reliability=source_reliability,
                issues_found=issues_found,
                recommendations=recommendations,
            )
            
        except Exception as e:
            logger.error(f"Content accuracy validation failed: {e}")
            return await self._basic_accuracy_assessment(request)
    
    async def detect_content_bias(
        self, request: QualityValidationRequest
    ) -> Optional[Any]:
        """
        Detect potential bias and ensure content fairness and inclusivity.
        
        Analyzes content for various forms of bias including gender, cultural,
        racial, age, and socioeconomic bias to ensure educational content
        is inclusive and appropriate.
        
        Args:
            request: Quality validation request
            
        Returns:
            BiasDetectionResponse: Detailed bias analysis results
        """
        try:
            if not self.ai_client:
                # Fallback to basic bias detection
                return await self._basic_bias_detection(request)
            
            bias_request = BiasDetectionRequest(
                content=request.content,
                check_categories=["gender", "cultural", "racial", "age", "socioeconomic", "ability"],
            )
            
            result = await self.ai_client.check_bias_detection(bias_request)
            
            # Add educational-specific bias checks
            educational_bias_score = await self._assess_educational_bias(request.content, request.target_level)
            
            # Combine scores
            combined_bias_score = (result.overall_bias_score * 0.8 + educational_bias_score * 0.2)
            result.overall_bias_score = combined_bias_score
            
            if combined_bias_score > 0.1:  # Low tolerance for bias
                result.recommendations.append(
                    "Content shows potential bias - review for inclusive language and diverse perspectives"
                )
            
            logger.info(f"Bias detection completed: {combined_bias_score:.3f} bias score (target: ≤0.1)")
            return result
            
        except Exception as e:
            logger.error(f"Bias detection failed: {e}")
            return await self._basic_bias_detection(request)
    
    async def generate_quality_report(
        self, validation_result: QualityValidationResult
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report from validation results.
        
        Creates a detailed report suitable for educators, content creators,
        and quality assurance teams with actionable insights and recommendations.
        
        Args:
            validation_result: Complete validation results
            
        Returns:
            Dict[str, Any]: Formatted quality report
        """
        report = {
            "executive_summary": self._generate_executive_summary(validation_result),
            "quality_metrics": {
                "overall_score": validation_result.overall_score,
                "readability_score": validation_result.readability_score,
                "pedagogical_alignment": validation_result.pedagogical_alignment,
                "objective_coverage": validation_result.objective_coverage,
                "content_accuracy": validation_result.content_accuracy,
                "bias_detection_score": validation_result.bias_detection_score,
            },
            "meets_standards": validation_result.meets_quality_standards,
            "validation_timestamp": validation_result.validation_timestamp.isoformat(),
            "detailed_analysis": self._format_detailed_analysis(validation_result),
            "recommendations": self._consolidate_recommendations(validation_result),
            "action_items": self._generate_action_items(validation_result),
            "quality_gates": self._assess_quality_gates(validation_result),
        }
        
        if validation_result.validation_errors:
            report["validation_errors"] = validation_result.validation_errors
        
        if validation_result.validation_warnings:
            report["validation_warnings"] = validation_result.validation_warnings
        
        return report
    
    # Private helper methods
    
    async def _basic_readability_analysis(self, request: QualityValidationRequest) -> Any:
        """Fallback readability analysis without AI."""
        # Simple word/sentence analysis
        sentences = len(re.findall(r'[.!?]+', request.content))
        words = len(request.content.split())
        
        if sentences == 0:
            avg_sentence_length = 0
        else:
            avg_sentence_length = words / sentences
        
        # Simplified Flesch Reading Ease approximation
        flesch_score = max(0, min(100, 100 - (avg_sentence_length * 2)))
        
        # Mock readability result structure
        class MockReadabilityResult:
            def __init__(self):
                self.flesch_reading_ease = flesch_score
                self.flesch_kincaid_score = max(1, avg_sentence_length / 2)
                self.meets_target_level = flesch_score >= self.READABILITY_THRESHOLDS.get(request.target_level, 50)
                self.recommendations = []
                if not self.meets_target_level:
                    self.recommendations.append("Consider simplifying language and sentence structure")
            
            def dict(self):
                return {
                    "flesch_reading_ease": self.flesch_reading_ease,
                    "flesch_kincaid_score": self.flesch_kincaid_score,
                    "meets_target_level": self.meets_target_level,
                    "recommendations": self.recommendations,
                }
        
        return MockReadabilityResult()
    
    async def _analyze_cognitive_levels(self, content: str) -> Dict[str, float]:
        """Analyze cognitive level distribution in content."""
        # Simplified cognitive level detection using keywords
        cognitive_keywords = {
            CognitiveLevel.REMEMBER: ["remember", "recall", "list", "define", "identify", "know"],
            CognitiveLevel.UNDERSTAND: ["understand", "explain", "describe", "summarize", "interpret"],
            CognitiveLevel.APPLY: ["apply", "use", "implement", "solve", "demonstrate", "practice"],
            CognitiveLevel.ANALYZE: ["analyze", "compare", "contrast", "examine", "break down"],
            CognitiveLevel.EVALUATE: ["evaluate", "assess", "judge", "critique", "argue", "defend"],
            CognitiveLevel.CREATE: ["create", "design", "build", "develop", "construct", "generate"],
        }
        
        content_lower = content.lower()
        level_counts = {}
        
        for level, keywords in cognitive_keywords.items():
            count = sum(content_lower.count(keyword) for keyword in keywords)
            level_counts[level.value] = count
        
        # Normalize to percentages
        total_count = sum(level_counts.values()) or 1
        return {level: count / total_count for level, count in level_counts.items()}
    
    def _calculate_distribution_alignment(
        self, actual: Dict[str, float], expected: Dict[CognitiveLevel, float]
    ) -> float:
        """Calculate alignment between actual and expected cognitive distributions."""
        total_deviation = 0.0
        for level, expected_ratio in expected.items():
            actual_ratio = actual.get(level.value, 0.0)
            total_deviation += abs(actual_ratio - expected_ratio)
        
        # Convert deviation to alignment score (lower deviation = higher alignment)
        max_possible_deviation = 2.0  # Maximum possible total absolute deviation
        alignment = max(0.0, 1.0 - (total_deviation / max_possible_deviation))
        return alignment
    
    async def _analyze_bloom_taxonomy_compliance(
        self, content: str, objectives: List[str], level: ProficiencyLevel
    ) -> float:
        """Analyze Bloom's taxonomy compliance."""
        # Check if content progression follows Bloom's hierarchy
        # This is a simplified implementation
        
        # Look for progression indicators
        progression_indicators = [
            "first", "then", "next", "finally", "building on", "expanding", "advanced"
        ]
        
        content_lower = content.lower()
        progression_count = sum(content_lower.count(indicator) for indicator in progression_indicators)
        
        # Check objective alignment
        objective_alignment = 0.0
        for objective in objectives:
            # Simple keyword matching between content and objectives
            obj_words = set(objective.lower().split())
            content_words = set(content_lower.split())
            overlap = len(obj_words.intersection(content_words))
            objective_alignment += min(1.0, overlap / max(len(obj_words), 1))
        
        objective_alignment = objective_alignment / max(len(objectives), 1)
        
        # Combine progression and alignment scores
        progression_score = min(1.0, progression_count / 10)
        return (progression_score * 0.4 + objective_alignment * 0.6)
    
    async def _assess_scaffolding_quality(self, content: str, level: ProficiencyLevel) -> float:
        """Assess quality of learning scaffolding in content."""
        # Look for scaffolding indicators
        scaffolding_indicators = [
            "example", "for instance", "let's practice", "try this", "step by step",
            "recap", "summary", "review", "prerequisite", "building block"
        ]
        
        content_lower = content.lower()
        scaffolding_count = sum(content_lower.count(indicator) for indicator in scaffolding_indicators)
        
        # Normalize based on content length
        words = len(content.split())
        scaffolding_density = scaffolding_count / max(words / 100, 1)  # Per 100 words
        
        return min(1.0, scaffolding_density)
    
    async def _analyze_objective_coverage(
        self, content: str, objective: str, subject_domain: str
    ) -> float:
        """Analyze how well content covers a specific learning objective."""
        # Extract key concepts from objective
        objective_words = set(word.lower() for word in objective.split() if len(word) > 3)
        content_words = set(word.lower() for word in content.split())
        
        # Calculate coverage based on keyword overlap
        overlap = len(objective_words.intersection(content_words))
        coverage = overlap / max(len(objective_words), 1)
        
        # Boost score if objective appears directly in content
        if objective.lower() in content.lower():
            coverage = min(1.0, coverage + 0.3)
        
        return coverage
    
    async def _assess_source_reliability(self, content: str) -> float:
        """Assess reliability of sources mentioned in content."""
        # Look for citation patterns and authoritative sources
        reliability_indicators = [
            "research shows", "studies indicate", "according to", "published in",
            "peer-reviewed", "academic", "university", "journal", "doi:"
        ]
        
        content_lower = content.lower()
        reliability_count = sum(content_lower.count(indicator) for indicator in reliability_indicators)
        
        # Normalize and cap at 1.0
        words = len(content.split())
        reliability_score = min(1.0, reliability_count / max(words / 200, 1))
        
        return max(0.5, reliability_score)  # Minimum baseline reliability
    
    async def _basic_accuracy_assessment(self, request: QualityValidationRequest) -> ContentAccuracyResult:
        """Fallback accuracy assessment without AI."""
        # Basic heuristic accuracy assessment
        content_length = len(request.content.split())
        
        # Assume reasonable accuracy for well-structured content
        factual_consistency = 0.8 if content_length > 100 else 0.6
        technical_correctness = 0.85
        source_reliability = await self._assess_source_reliability(request.content)
        
        accuracy_score = (factual_consistency * 0.5 + technical_correctness * 0.3 + source_reliability * 0.2)
        
        return ContentAccuracyResult(
            accuracy_score=accuracy_score,
            factual_consistency=factual_consistency,
            technical_correctness=technical_correctness,
            source_reliability=source_reliability,
            recommendations=["Manual fact-checking recommended - AI validation unavailable"],
        )
    
    async def _basic_bias_detection(self, request: QualityValidationRequest) -> Any:
        """Fallback bias detection without AI."""
        # Simple keyword-based bias detection
        bias_keywords = {
            "gender": ["he should", "she should", "guys", "mankind"],
            "cultural": ["primitive", "third world", "exotic"],
            "age": ["elderly", "old people", "young people"],
        }
        
        content_lower = request.content.lower()
        bias_count = 0
        
        for category, keywords in bias_keywords.items():
            bias_count += sum(content_lower.count(keyword) for keyword in keywords)
        
        bias_score = min(1.0, bias_count / 100)
        
        class MockBiasResult:
            def __init__(self):
                self.overall_bias_score = bias_score
                self.severity_level = "low" if bias_score < 0.3 else "medium"
                self.recommendations = []
                if bias_score > 0.1:
                    self.recommendations.append("Review content for inclusive language")
            
            def dict(self):
                return {
                    "overall_bias_score": self.overall_bias_score,
                    "severity_level": self.severity_level,
                    "recommendations": self.recommendations,
                }
        
        return MockBiasResult()
    
    async def _assess_educational_bias(self, content: str, level: ProficiencyLevel) -> float:
        """Assess educational-specific bias (learning style preferences, etc.)."""
        # Check for over-reliance on single learning modalities
        visual_indicators = ["see", "look", "image", "diagram", "chart", "visual"]
        auditory_indicators = ["hear", "listen", "sound", "audio", "voice", "music"]
        kinesthetic_indicators = ["do", "practice", "hands-on", "build", "touch", "move"]
        
        content_lower = content.lower()
        
        visual_count = sum(content_lower.count(word) for word in visual_indicators)
        auditory_count = sum(content_lower.count(word) for word in auditory_indicators)
        kinesthetic_count = sum(content_lower.count(word) for word in kinesthetic_indicators)
        
        total_modality = visual_count + auditory_count + kinesthetic_count
        
        if total_modality == 0:
            return 0.0
        
        # Calculate balance - bias is high if one modality dominates
        modality_ratios = [visual_count / total_modality, auditory_count / total_modality, kinesthetic_count / total_modality]
        max_ratio = max(modality_ratios)
        
        # High bias if one modality is >70% of total
        bias_score = max(0.0, (max_ratio - 0.7) / 0.3) if max_ratio > 0.7 else 0.0
        
        return bias_score
    
    def _calculate_overall_score(
        self,
        readability: float,
        pedagogical: float,
        coverage: float,
        accuracy: float,
        bias: float,
        level: ProficiencyLevel,
    ) -> float:
        """Calculate weighted overall quality score."""
        # Normalize readability to 0-1 scale
        readability_normalized = readability / 100.0
        
        # Invert bias score (lower bias = higher quality)
        bias_quality = 1.0 - bias
        
        # Weighted average with emphasis on coverage and accuracy
        weights = {
            "readability": 0.15,
            "pedagogical": 0.25,
            "coverage": 0.30,  # Highest weight - FR-012 requirement
            "accuracy": 0.25,   # High weight for content quality
            "bias": 0.05,       # Lower weight but still important
        }
        
        overall = (
            readability_normalized * weights["readability"] +
            pedagogical * weights["pedagogical"] +
            coverage * weights["coverage"] +
            accuracy * weights["accuracy"] +
            bias_quality * weights["bias"]
        )
        
        return min(1.0, max(0.0, overall))
    
    def _check_quality_standards(
        self,
        overall: float,
        readability: float,
        pedagogical: float,
        coverage: float,
        accuracy: float,
        bias: float,
        level: ProficiencyLevel,
    ) -> bool:
        """Check if content meets minimum quality standards."""
        thresholds = self.MIN_QUALITY_THRESHOLDS
        readability_threshold = self.READABILITY_THRESHOLDS[level]
        
        return (
            overall >= thresholds["overall_score"] and
            readability >= readability_threshold and
            pedagogical >= thresholds["pedagogical_alignment"] and
            coverage >= thresholds["objective_coverage"] and
            accuracy >= thresholds["content_accuracy"] and
            bias <= thresholds["bias_detection_max"]
        )
    
    def _generate_quality_warnings(
        self,
        readability: float,
        pedagogical: float,
        coverage: float,
        accuracy: float,
        bias: float,
        level: ProficiencyLevel,
    ) -> List[str]:
        """Generate quality warnings for standards not met."""
        warnings = []
        thresholds = self.MIN_QUALITY_THRESHOLDS
        readability_threshold = self.READABILITY_THRESHOLDS[level]
        
        if readability < readability_threshold:
            warnings.append(f"Readability score {readability:.1f} below {level.value} threshold of {readability_threshold}")
        
        if pedagogical < thresholds["pedagogical_alignment"]:
            warnings.append(f"Pedagogical alignment {pedagogical:.2f} below required {thresholds['pedagogical_alignment']}")
        
        if coverage < thresholds["objective_coverage"]:
            warnings.append(f"Objective coverage {coverage:.2f} below required {thresholds['objective_coverage']} (FR-012)")
        
        if accuracy < thresholds["content_accuracy"]:
            warnings.append(f"Content accuracy {accuracy:.2f} below required {thresholds['content_accuracy']}")
        
        if bias > thresholds["bias_detection_max"]:
            warnings.append(f"Bias detection score {bias:.3f} above maximum {thresholds['bias_detection_max']}")
        
        return warnings
    
    def _generate_executive_summary(self, result: QualityValidationResult) -> str:
        """Generate executive summary of validation results."""
        status = "PASS" if result.meets_quality_standards else "FAIL"
        
        summary = f"Quality Validation: {status} (Score: {result.overall_score:.2f}/1.00)\n\n"
        
        if result.meets_quality_standards:
            summary += "Content meets all quality standards and is ready for publication.\n"
        else:
            summary += "Content requires improvements before publication:\n"
            for warning in result.validation_warnings[:3]:  # Top 3 issues
                summary += f"• {warning}\n"
        
        summary += f"\nKey Metrics:\n"
        summary += f"• Readability: {result.readability_score:.1f}/100\n"
        summary += f"• Pedagogical Alignment: {result.pedagogical_alignment:.2f}/1.00\n"
        summary += f"• Objective Coverage: {result.objective_coverage:.2f}/1.00\n"
        summary += f"• Content Accuracy: {result.content_accuracy:.2f}/1.00\n"
        summary += f"• Bias Score: {result.bias_detection_score:.3f}/1.00 (lower is better)\n"
        
        return summary
    
    def _format_detailed_analysis(self, result: QualityValidationResult) -> Dict[str, Any]:
        """Format detailed analysis section of the report."""
        analysis = {}
        
        if result.readability_details:
            analysis["readability"] = result.readability_details
        
        if result.pedagogical_details:
            analysis["pedagogical"] = result.pedagogical_details.dict()
        
        if result.coverage_details:
            analysis["objective_coverage"] = result.coverage_details.dict()
        
        if result.accuracy_details:
            analysis["content_accuracy"] = result.accuracy_details.dict()
        
        if result.bias_details:
            analysis["bias_detection"] = result.bias_details
        
        return analysis
    
    def _consolidate_recommendations(self, result: QualityValidationResult) -> List[str]:
        """Consolidate all recommendations from different analyses."""
        all_recommendations = []
        
        # Collect recommendations from all analysis components
        if result.readability_details and hasattr(result.readability_details, 'recommendations'):
            all_recommendations.extend(result.readability_details.get('recommendations', []))
        
        if result.pedagogical_details:
            all_recommendations.extend(result.pedagogical_details.recommendations)
        
        if result.coverage_details:
            all_recommendations.extend(result.coverage_details.recommendations)
        
        if result.accuracy_details:
            all_recommendations.extend(result.accuracy_details.recommendations)
        
        if result.bias_details and hasattr(result.bias_details, 'recommendations'):
            all_recommendations.extend(result.bias_details.get('recommendations', []))
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)
        
        return unique_recommendations
    
    def _generate_action_items(self, result: QualityValidationResult) -> List[Dict[str, Any]]:
        """Generate prioritized action items for improvement."""
        action_items = []
        
        # High priority items
        if result.objective_coverage < 1.0:
            action_items.append({
                "priority": "HIGH",
                "category": "Objective Coverage",
                "action": "Ensure all learning objectives are fully addressed",
                "current_score": result.objective_coverage,
                "target_score": 1.0,
            })
        
        if result.content_accuracy < 0.9:
            action_items.append({
                "priority": "HIGH",
                "category": "Content Accuracy",
                "action": "Review and verify factual accuracy of content",
                "current_score": result.content_accuracy,
                "target_score": 0.9,
            })
        
        # Medium priority items
        if result.pedagogical_alignment < 0.8:
            action_items.append({
                "priority": "MEDIUM",
                "category": "Pedagogical Alignment",
                "action": "Improve alignment with Bloom's taxonomy and learning progression",
                "current_score": result.pedagogical_alignment,
                "target_score": 0.8,
            })
        
        # Check readability threshold by level
        target_readability = self.READABILITY_THRESHOLDS.get(ProficiencyLevel.INTERMEDIATE, 60.0)  # Default fallback
        if result.readability_score < target_readability:
            action_items.append({
                "priority": "MEDIUM",
                "category": "Readability",
                "action": "Simplify language and sentence structure for target audience",
                "current_score": result.readability_score,
                "target_score": target_readability,
            })
        
        # Low priority items
        if result.bias_detection_score > 0.1:
            action_items.append({
                "priority": "LOW",
                "category": "Bias Detection",
                "action": "Review content for inclusive language and diverse perspectives",
                "current_score": result.bias_detection_score,
                "target_score": 0.1,
            })
        
        return action_items
    
    def _assess_quality_gates(self, result: QualityValidationResult) -> Dict[str, Any]:
        """Assess which quality gates are passed or failed."""
        gates = {}
        
        # FR-012: 100% objective coverage gate
        gates["objective_coverage_gate"] = {
            "name": "FR-012: Complete Objective Coverage",
            "status": "PASS" if result.objective_coverage >= 1.0 else "FAIL",
            "current": result.objective_coverage,
            "required": 1.0,
            "critical": True,
        }
        
        # Content accuracy gate
        gates["accuracy_gate"] = {
            "name": "Content Accuracy Standard",
            "status": "PASS" if result.content_accuracy >= 0.9 else "FAIL",
            "current": result.content_accuracy,
            "required": 0.9,
            "critical": True,
        }
        
        # Pedagogical alignment gate
        gates["pedagogical_gate"] = {
            "name": "Pedagogical Alignment Standard",
            "status": "PASS" if result.pedagogical_alignment >= 0.8 else "FAIL",
            "current": result.pedagogical_alignment,
            "required": 0.8,
            "critical": False,
        }
        
        # Bias tolerance gate
        gates["bias_gate"] = {
            "name": "Bias Detection Standard",
            "status": "PASS" if result.bias_detection_score <= 0.1 else "FAIL",
            "current": result.bias_detection_score,
            "required": 0.1,
            "critical": False,
        }
        
        # Overall quality gate
        gates["overall_gate"] = {
            "name": "Overall Quality Standard",
            "status": "PASS" if result.overall_score >= 0.75 else "FAIL",
            "current": result.overall_score,
            "required": 0.75,
            "critical": True,
        }
        
        return gates


# Utility function to create QualityMetrics from validation result
def create_quality_metrics_from_validation(result: QualityValidationResult) -> QualityMetrics:
    """Convert validation result to QualityMetrics model for database storage."""
    return QualityMetrics(
        readability_score=result.readability_score,
        pedagogical_alignment=result.pedagogical_alignment,
        objective_coverage=result.objective_coverage,
        content_accuracy=result.content_accuracy,
        bias_detection_score=result.bias_detection_score,
        user_satisfaction_score=None,  # Not available from validation
        generation_timestamp=result.validation_timestamp,
    )