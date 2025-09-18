"""
Integration tests for AI client wrapper.

Tests T038: AI client integration with course generation workflow.
Validates end-to-end functionality with real AI provider simulation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from src.integrations.ai_client import (
    AIClient,
    CourseStructureRequest,
    ChapterContentRequest,
    ContentValidationRequest,
    ReadabilityAnalysisRequest,
    BiasDetectionRequest,
    create_ai_client
)
from src.models.enums import ProficiencyLevel


class TestAIClientIntegration:
    """Integration tests for AI client with course generation workflow."""
    
    @pytest.fixture
    def ai_client(self):
        """AI client with mocked providers for integration testing."""
        return create_ai_client(
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            preferred_provider="openai"
        )
    
    @pytest.fixture
    def course_generation_scenario(self):
        """Complete course generation scenario data."""
        return {
            "course_request": CourseStructureRequest(
                title="Machine Learning Fundamentals",
                subject_domain="Computer Science",
                target_level=ProficiencyLevel.INTERMEDIATE,
                estimated_duration_hours=40.0,
                learning_objectives=[
                    "Understand machine learning concepts and terminology",
                    "Implement basic supervised learning algorithms",
                    "Evaluate model performance using appropriate metrics",
                    "Apply machine learning to real-world problems"
                ],
                prerequisites=["Basic programming", "Statistics fundamentals"],
                preferred_language="en"
            ),
            "expected_chapters": [
                {
                    "sequence_number": 1,
                    "title": "Introduction to Machine Learning",
                    "learning_objectives": ["Define machine learning", "Understand types of learning"],
                    "estimated_duration": 4.0,
                    "complexity_level": 2.0
                },
                {
                    "sequence_number": 2,
                    "title": "Supervised Learning",
                    "learning_objectives": ["Implement classification", "Implement regression"],
                    "estimated_duration": 8.0,
                    "complexity_level": 3.0
                }
            ]
        }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_course_generation_workflow(self, ai_client, course_generation_scenario):
        """Test complete course generation workflow from structure to quality validation."""
        
        # Mock AI provider responses
        with patch.object(ai_client.providers["openai"], 'generate_course_structure') as mock_structure, \
             patch.object(ai_client.providers["openai"], 'generate_chapter_content') as mock_content, \
             patch.object(ai_client.providers["openai"], 'validate_content_quality') as mock_quality:
            
            # Step 1: Generate course structure
            mock_structure.return_value = self._create_mock_structure_response(
                course_generation_scenario["expected_chapters"]
            )
            
            structure_result = await ai_client.generate_course_structure(
                course_generation_scenario["course_request"]
            )
            
            assert len(structure_result.chapters) == 2
            assert structure_result.estimated_total_duration == 40.0
            assert structure_result.difficulty_progression == [2.0, 3.0]
            
            # Step 2: Generate content for each chapter
            chapter_contents = []
            for i, chapter in enumerate(structure_result.chapters):
                mock_content.return_value = self._create_mock_content_response(
                    chapter["title"], i + 1
                )
                
                chapter_request = ChapterContentRequest(
                    chapter_title=chapter["title"],
                    learning_objectives=chapter["learning_objectives"],
                    target_level=course_generation_scenario["course_request"].target_level,
                    sequence_number=chapter["sequence_number"],
                    estimated_duration_minutes=int(chapter["estimated_duration"] * 60),
                    include_examples=True,
                    include_exercises=True
                )
                
                content_result = await ai_client.generate_chapter_content(chapter_request)
                chapter_contents.append(content_result)
                
                assert len(content_result.content_blocks) > 0
                assert len(content_result.key_concepts) > 0
                assert content_result.estimated_reading_time > 0
            
            # Step 3: Validate content quality for all chapters
            mock_quality.return_value = self._create_mock_quality_response()
            
            quality_results = []
            for content in chapter_contents:
                combined_content = " ".join([
                    block["content"] for block in content.content_blocks
                    if block["type"] == "text"
                ])
                
                validation_request = ContentValidationRequest(
                    content=combined_content,
                    target_level=course_generation_scenario["course_request"].target_level,
                    learning_objectives=course_generation_scenario["course_request"].learning_objectives,
                    subject_domain=course_generation_scenario["course_request"].subject_domain
                )
                
                quality_result = await ai_client.validate_content_quality(validation_request)
                quality_results.append(quality_result)
                
                # Validate quality thresholds for intermediate level
                assert quality_result.overall_score >= 0.7
                assert quality_result.readability_score >= 60.0  # Intermediate threshold
                assert quality_result.objective_coverage >= 0.8
            
            # Verify workflow completion
            assert len(chapter_contents) == len(structure_result.chapters)
            assert len(quality_results) == len(chapter_contents)
            assert all(q.overall_score >= 0.7 for q in quality_results)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_level_adaptive_content_generation(self, ai_client):
        """Test that content adapts appropriately to different proficiency levels."""
        
        levels_to_test = [
            ProficiencyLevel.BEGINNER,
            ProficiencyLevel.INTERMEDIATE,
            ProficiencyLevel.ADVANCED,
            ProficiencyLevel.EXPERT
        ]
        
        base_request = {
            "title": "Introduction to Programming",
            "subject_domain": "Computer Science",
            "estimated_duration_hours": 20.0,
            "learning_objectives": [
                "Understand programming concepts",
                "Write basic programs",
                "Debug code effectively"
            ]
        }
        
        results = {}
        
        for level in levels_to_test:
            with patch.object(ai_client.providers["openai"], 'generate_course_structure') as mock_gen:
                # Mock different responses based on level
                expected_chapters = self._get_expected_chapters_for_level(level)
                mock_gen.return_value = self._create_mock_structure_response(expected_chapters)
                
                request = CourseStructureRequest(
                    **base_request,
                    target_level=level
                )
                
                result = await ai_client.generate_course_structure(request)
                results[level] = result
                
                # Verify level-appropriate characteristics
                if level == ProficiencyLevel.BEGINNER:
                    assert len(result.chapters) <= 5  # Fewer chapters for beginners
                    assert max(result.difficulty_progression) <= 2.5
                elif level == ProficiencyLevel.EXPERT:
                    assert len(result.chapters) >= 8  # More chapters for experts
                    assert max(result.difficulty_progression) >= 4.0
        
        # Verify progression complexity increases with level
        beginner_complexity = max(results[ProficiencyLevel.BEGINNER].difficulty_progression)
        expert_complexity = max(results[ProficiencyLevel.EXPERT].difficulty_progression)
        assert expert_complexity > beginner_complexity
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_quality_validation_thresholds_by_level(self, ai_client):
        """Test that quality validation applies appropriate thresholds by proficiency level."""
        
        test_content = "This is educational content that needs to be evaluated for quality and readability."
        
        level_expectations = {
            ProficiencyLevel.BEGINNER: {
                "readability_threshold": 70.0,
                "complexity_expectation": "low"
            },
            ProficiencyLevel.INTERMEDIATE: {
                "readability_threshold": 60.0,
                "complexity_expectation": "medium"
            },
            ProficiencyLevel.ADVANCED: {
                "readability_threshold": 50.0,
                "complexity_expectation": "high"
            },
            ProficiencyLevel.EXPERT: {
                "readability_threshold": 0.0,
                "complexity_expectation": "very_high"
            }
        }
        
        for level, expectations in level_expectations.items():
            # Test readability analysis
            readability_request = ReadabilityAnalysisRequest(
                content=test_content,
                target_level=level
            )
            
            readability_result = await ai_client.analyze_readability(readability_request)
            
            # Verify threshold application
            expected_threshold = expectations["readability_threshold"]
            if expected_threshold > 0:
                # For levels with thresholds, check if meets_target_level is correctly calculated
                meets_target = readability_result.flesch_reading_ease >= expected_threshold
                assert readability_result.meets_target_level == meets_target
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_comprehensive_quality_analysis_integration(self, ai_client):
        """Test comprehensive quality analysis integrating all validation methods."""
        
        test_scenarios = [
            {
                "name": "high_quality_content",
                "content": "Python is a versatile programming language. It has simple syntax. Developers use it for web development, data science, and automation. Variables in Python store data values. You can create a variable by writing: name = 'John'. This assigns the string 'John' to the variable named 'name'.",
                "target_level": ProficiencyLevel.BEGINNER,
                "expected_quality": "high"
            },
            {
                "name": "problematic_content",
                "content": "Guys, programming is really hard for primitive beginners. The syntax is so complex that normal people can't understand it. You need to be really smart like us experts.",
                "target_level": ProficiencyLevel.BEGINNER,
                "expected_quality": "low"
            }
        ]
        
        for scenario in test_scenarios:
            # Mock AI quality validation
            with patch.object(ai_client.providers["openai"], 'validate_content_quality') as mock_quality:
                if scenario["expected_quality"] == "high":
                    mock_quality.return_value = self._create_mock_quality_response(
                        overall_score=0.9,
                        readability_score=80.0,
                        pedagogical_alignment=0.95,
                        objective_coverage=0.9,
                        content_accuracy=0.95
                    )
                else:
                    mock_quality.return_value = self._create_mock_quality_response(
                        overall_score=0.4,
                        readability_score=45.0,
                        pedagogical_alignment=0.3,
                        objective_coverage=0.6,
                        content_accuracy=0.8
                    )
                
                # Run comprehensive analysis
                result = await ai_client.comprehensive_quality_check(
                    content=scenario["content"],
                    target_level=scenario["target_level"],
                    learning_objectives=["Understand programming basics"],
                    subject_domain="Computer Science"
                )
                
                # Verify comprehensive results
                assert "ai_quality_assessment" in result
                assert "readability_analysis" in result
                assert "bias_detection" in result
                assert "overall_quality_score" in result
                assert "meets_quality_standards" in result
                
                if scenario["expected_quality"] == "high":
                    assert result["overall_quality_score"] > 0.7
                    assert result["meets_quality_standards"] is True
                else:
                    assert result["overall_quality_score"] < 0.7
                    # Bias detection should flag problematic language
                    assert result["bias_detection"]["overall_bias_score"] > 0.0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_provider_fallback_mechanism(self, ai_client):
        """Test provider fallback mechanism under failure conditions."""
        
        request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Computer Science",
            target_level=ProficiencyLevel.BEGINNER,
            estimated_duration_hours=10.0,
            learning_objectives=["Learn basic concepts", "Apply knowledge", "Practice skills"]
        )
        
        with patch.object(ai_client.providers["openai"], 'generate_course_structure') as mock_openai, \
             patch.object(ai_client.providers["anthropic"], 'generate_course_structure') as mock_anthropic:
            
            # Simulate OpenAI failure
            mock_openai.side_effect = Exception("OpenAI API Error")
            
            # Anthropic succeeds
            mock_anthropic.return_value = self._create_mock_structure_response([{
                "sequence_number": 1,
                "title": "Fallback Chapter",
                "learning_objectives": ["Learn basics"],
                "estimated_duration": 5.0,
                "complexity_level": 1.0
            }])
            
            # Should fallback to Anthropic
            result = await ai_client.generate_course_structure(request)
            
            assert result.chapters[0]["title"] == "Fallback Chapter"
            mock_openai.assert_called_once()
            mock_anthropic.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_streaming_content_generation(self, ai_client):
        """Test streaming chapter content generation."""
        
        request = ChapterContentRequest(
            chapter_title="Introduction to Variables",
            learning_objectives=["Define variables", "Use variables in programs"],
            target_level=ProficiencyLevel.BEGINNER,
            sequence_number=1,
            estimated_duration_minutes=30
        )
        
        # Mock streaming response
        async def mock_stream():
            chunks = [
                "Variables are ",
                "containers for ",
                "storing data values. ",
                "In Python, you create ",
                "variables by assignment."
            ]
            for chunk in chunks:
                yield chunk
        
        with patch.object(ai_client.providers["openai"], 'generate_chapter_content_stream') as mock_stream_gen:
            mock_stream_gen.return_value = mock_stream()
            
            # Collect streamed content
            streamed_content = []
            async for chunk in ai_client.generate_chapter_content_stream(request):
                streamed_content.append(chunk)
            
            # Verify streaming worked
            assert len(streamed_content) == 5
            full_content = "".join(streamed_content)
            assert "Variables are containers" in full_content
            assert "Python" in full_content
    
    def _create_mock_structure_response(self, chapters):
        """Helper to create mock course structure response."""
        from src.integrations.ai_client import CourseStructureResponse
        
        return CourseStructureResponse(
            chapters=chapters,
            estimated_total_duration=sum(ch.get("estimated_duration", 5.0) for ch in chapters),
            difficulty_progression=[ch.get("complexity_level", 2.0) for ch in chapters],
            suggested_prerequisites=["Basic programming"],
            learning_path_rationale="Progressive learning approach with hands-on practice",
            quality_indicators={
                "progression_smoothness": 0.9,
                "objective_coverage": 1.0,
                "content_balance": 0.85
            }
        )
    
    def _create_mock_content_response(self, chapter_title, sequence_number):
        """Helper to create mock chapter content response."""
        from src.integrations.ai_client import ChapterContentResponse
        
        return ChapterContentResponse(
            content_blocks=[
                {
                    "type": "text",
                    "content": f"This chapter covers {chapter_title.lower()}. You will learn key concepts and apply them through practical exercises.",
                    "order": 1
                },
                {
                    "type": "text", 
                    "content": "Let's start with the fundamental concepts and build understanding step by step.",
                    "order": 2
                }
            ],
            key_concepts=[f"concept_{sequence_number}_1", f"concept_{sequence_number}_2"],
            examples=[
                {
                    "title": f"Example {sequence_number}.1",
                    "description": "Practical demonstration of key concepts",
                    "code_or_content": "# Example code here\nprint('Hello, World!')"
                }
            ],
            exercises=[
                {
                    "title": f"Exercise {sequence_number}.1",
                    "description": "Practice what you've learned",
                    "difficulty": "easy",
                    "estimated_time": 15
                }
            ],
            summary=f"In this chapter, you learned about {chapter_title.lower()} and how to apply the concepts.",
            estimated_reading_time=30,
            complexity_score=2.0 + (sequence_number * 0.5)
        )
    
    def _create_mock_quality_response(self, overall_score=0.85, readability_score=75.0,
                                    pedagogical_alignment=0.9, objective_coverage=0.95,
                                    content_accuracy=0.9):
        """Helper to create mock quality validation response."""
        from src.integrations.ai_client import ContentQualityResponse
        
        return ContentQualityResponse(
            overall_score=overall_score,
            readability_score=readability_score,
            pedagogical_alignment=pedagogical_alignment,
            objective_coverage=objective_coverage,
            content_accuracy=content_accuracy,
            recommendations=[
                "Consider adding more examples for complex concepts",
                "Include interactive exercises to reinforce learning"
            ],
            issues_found=[
                {
                    "type": "clarity",
                    "severity": "low",
                    "description": "Some technical terms could use more explanation",
                    "location": "paragraph 3"
                }
            ]
        )
    
    def _get_expected_chapters_for_level(self, level):
        """Helper to get expected chapter count and complexity for proficiency level."""
        level_configs = {
            ProficiencyLevel.BEGINNER: {
                "count": 4,
                "max_complexity": 2.5,
                "base_duration": 3.0
            },
            ProficiencyLevel.INTERMEDIATE: {
                "count": 6,
                "max_complexity": 3.5,
                "base_duration": 4.0
            },
            ProficiencyLevel.ADVANCED: {
                "count": 8,
                "max_complexity": 4.5,
                "base_duration": 5.0
            },
            ProficiencyLevel.EXPERT: {
                "count": 10,
                "max_complexity": 5.0,
                "base_duration": 6.0
            }
        }
        
        config = level_configs[level]
        chapters = []
        
        for i in range(config["count"]):
            chapters.append({
                "sequence_number": i + 1,
                "title": f"Chapter {i + 1}: {level.value.title()} Topic",
                "learning_objectives": [f"Objective {i + 1}.1", f"Objective {i + 1}.2"],
                "estimated_duration": config["base_duration"],
                "complexity_level": min(1.0 + (i * 0.5), config["max_complexity"]),
                "prerequisites": [] if i == 0 else [f"Chapter {i}"],
                "content_outline": f"Outline for {level.value} level chapter {i + 1}"
            })
        
        return chapters


class TestAIClientPerformance:
    """Performance tests for AI client operations."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_content_generation(self):
        """Test concurrent chapter content generation performance."""
        import asyncio
        import time
        
        ai_client = create_ai_client(
            openai_api_key="test-key",
            preferred_provider="openai"
        )
        
        # Create multiple chapter requests
        requests = [
            ChapterContentRequest(
                chapter_title=f"Chapter {i}: Test Topic",
                learning_objectives=[f"Learn concept {i}"],
                target_level=ProficiencyLevel.BEGINNER,
                sequence_number=i,
                estimated_duration_minutes=30
            )
            for i in range(1, 6)  # 5 chapters
        ]
        
        # Mock the provider to simulate processing time
        with patch.object(ai_client.providers["openai"], 'generate_chapter_content') as mock_gen:
            async def mock_generation(request):
                await asyncio.sleep(0.1)  # Simulate API call time
                return self._create_mock_content_response(request.chapter_title, request.sequence_number)
            
            mock_gen.side_effect = mock_generation
            
            # Test concurrent generation
            start_time = time.time()
            results = await asyncio.gather(*[
                ai_client.generate_chapter_content(req) for req in requests
            ])
            concurrent_time = time.time() - start_time
            
            # Test sequential generation
            start_time = time.time()
            sequential_results = []
            for req in requests:
                result = await ai_client.generate_chapter_content(req)
                sequential_results.append(result)
            sequential_time = time.time() - start_time
            
            # Verify results
            assert len(results) == 5
            assert len(sequential_results) == 5
            
            # Concurrent should be significantly faster
            assert concurrent_time < sequential_time * 0.8  # At least 20% faster
    
    def _create_mock_content_response(self, chapter_title, sequence_number):
        """Helper method for performance tests."""
        from src.integrations.ai_client import ChapterContentResponse
        
        return ChapterContentResponse(
            content_blocks=[{"type": "text", "content": f"Content for {chapter_title}", "order": 1}],
            key_concepts=[f"concept_{sequence_number}"],
            examples=[{"title": "Example", "description": "Test", "code_or_content": "test"}],
            exercises=[{"title": "Exercise", "description": "Test", "difficulty": "easy", "estimated_time": 10}],
            summary=f"Summary for {chapter_title}",
            estimated_reading_time=30,
            complexity_score=2.0
        )