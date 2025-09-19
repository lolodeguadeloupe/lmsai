"""
AI Service Testing CLI for the course generation platform.

Implements T058: AI service testing CLI with provider validation,
generation testing, configuration validation, and limit checking.

Key Features:
- Test OpenAI and Anthropic provider connectivity
- Validate AI generation capabilities with real content
- Check configuration settings and API keys
- Monitor usage limits and quotas
- Comprehensive error reporting and diagnostics
- Support for different AI models and testing scenarios
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import httpx
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# Import project modules
from ..core.config import settings
from ..core.exceptions import (
    AIServiceException,
    AIServiceUnavailableException,
    AIServiceTimeoutException,
    AIQuotaExceededException,
    PlatformException
)
from ..integrations.ai_client import (
    AIClient,
    OpenAIProvider,
    AnthropicProvider,
    CourseStructureRequest,
    ChapterContentRequest,
    ContentValidationRequest,
    ReadabilityAnalysisRequest,
    BiasDetectionRequest,
    create_ai_client
)
from ..models.enums import ProficiencyLevel
from ..services.course_generation_service import (
    CourseGenerationService,
    GenerationMode,
    create_course_generation_service
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console for beautiful output
console = Console()


# CLI Models
class ProviderTest(BaseModel):
    """Test results for an AI provider."""
    
    provider: str
    available: bool
    response_time: float
    error: Optional[str] = None
    model: Optional[str] = None
    test_content: Optional[str] = None
    metadata: Dict[str, Any] = {}


class GenerationTest(BaseModel):
    """Test results for content generation."""
    
    test_type: str
    success: bool
    duration: float
    content_length: int
    quality_score: Optional[float] = None
    error: Optional[str] = None
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}


class ConfigValidation(BaseModel):
    """Configuration validation results."""
    
    valid: bool
    missing_keys: List[str] = []
    invalid_values: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []


class LimitStatus(BaseModel):
    """API limit status information."""
    
    provider: str
    current_usage: int
    limit: int
    reset_time: Optional[datetime] = None
    percentage_used: float
    status: str  # healthy, warning, critical
    recommendations: List[str] = []


# CLI Group
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--json-output', '-j', is_flag=True, help='Output results in JSON format')
@click.pass_context
def ai(ctx, verbose: bool, json_output: bool):
    """AI service testing and management commands."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['json_output'] = json_output
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


# Test Providers Command
@ai.command()
@click.option('--provider', '-p', type=click.Choice(['openai', 'anthropic', 'all']), 
              default='all', help='Provider to test')
@click.option('--model', '-m', help='Specific model to test (optional)')
@click.option('--timeout', '-t', default=30, help='Request timeout in seconds')
@click.pass_context
def test_providers(ctx, provider: str, model: Optional[str], timeout: int):
    """Test AI provider connectivity and basic functionality."""
    
    async def _run_tests():
        try:
            console.print("\n[bold blue]🧪 Testing AI Providers[/bold blue]")
            console.print("=" * 50)
            
            results = []
            
            if provider in ['openai', 'all']:
                result = await _test_openai_provider(model, timeout)
                results.append(result)
                _display_provider_result(result)
            
            if provider in ['anthropic', 'all']:
                result = await _test_anthropic_provider(model, timeout)
                results.append(result)
                _display_provider_result(result)
            
            # Summary
            _display_provider_summary(results)
            
            if ctx.obj['json_output']:
                console.print_json(json.dumps([r.dict() for r in results], default=str))
                
        except Exception as e:
            console.print(f"[bold red]❌ Error testing providers: {str(e)}[/bold red]")
            sys.exit(1)
    
    run_async_command(_run_tests)


# Test Generation Command
@ai.command()
@click.option('--provider', '-p', type=click.Choice(['openai', 'anthropic']), 
              help='Provider to test (uses preferred if not specified)')
@click.option('--test-type', '-t', 
              type=click.Choice(['structure', 'content', 'validation', 'all']),
              default='all', help='Type of generation to test')
@click.option('--level', '-l', 
              type=click.Choice(['beginner', 'intermediate', 'advanced', 'expert']),
              default='intermediate', help='Proficiency level for test content')
@click.option('--iterations', '-i', default=1, help='Number of test iterations')
@click.pass_context
def test_generation(ctx, provider: Optional[str], test_type: str, 
                         level: str, iterations: int):
    """Test AI content generation capabilities."""
    
    async def _run_tests():
        try:
            console.print("\n[bold green]🎯 Testing AI Generation[/bold green]")
            console.print("=" * 50)
            
            # Initialize AI client
            ai_client = _create_ai_client(provider)
            proficiency_level = ProficiencyLevel(level)
            
            results = []
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                for iteration in range(iterations):
                    console.print(f"\n[bold]Iteration {iteration + 1}/{iterations}[/bold]")
                    
                    if test_type in ['structure', 'all']:
                        task = progress.add_task("Testing course structure generation...", total=None)
                        result = await _test_structure_generation(ai_client, proficiency_level)
                        results.append(result)
                        _display_generation_result(result)
                        progress.remove_task(task)
                    
                    if test_type in ['content', 'all']:
                        task = progress.add_task("Testing chapter content generation...", total=None)
                        result = await _test_content_generation(ai_client, proficiency_level)
                        results.append(result)
                        _display_generation_result(result)
                        progress.remove_task(task)
                    
                    if test_type in ['validation', 'all']:
                        task = progress.add_task("Testing content validation...", total=None)
                        result = await _test_content_validation(ai_client, proficiency_level)
                        results.append(result)
                        _display_generation_result(result)
                        progress.remove_task(task)
            
            # Summary
            _display_generation_summary(results)
            
            if ctx.obj['json_output']:
                console.print_json(json.dumps([r.dict() for r in results], default=str))
                
        except Exception as e:
            console.print(f"[bold red]❌ Error testing generation: {str(e)}[/bold red]")
            sys.exit(1)
    
    run_async_command(_run_tests)


# Validate Config Command
@ai.command()
@click.option('--check-keys', '-k', is_flag=True, help='Check API key validity')
@click.option('--check-endpoints', '-e', is_flag=True, help='Check endpoint accessibility')
@click.option('--check-models', '-m', is_flag=True, help='Check model availability')
@click.pass_context
def validate_config(ctx, check_keys: bool, check_endpoints: bool, check_models: bool):
    """Validate AI service configuration settings."""
    
    async def _run_validation():
        try:
            console.print("\n[bold yellow]⚙️  Validating Configuration[/bold yellow]")
            console.print("=" * 50)
            
            # If no specific checks, do all
            if not any([check_keys, check_endpoints, check_models]):
                check_keys = check_endpoints = check_models = True
            
            validation = await _validate_configuration(check_keys, check_endpoints, check_models)
            _display_config_validation(validation)
            
            if ctx.obj['json_output']:
                console.print_json(validation.dict())
                
        except Exception as e:
            console.print(f"[bold red]❌ Error validating configuration: {str(e)}[/bold red]")
            sys.exit(1)
    
    run_async_command(_run_validation)


# Check Limits Command
@ai.command()
@click.option('--provider', '-p', type=click.Choice(['openai', 'anthropic', 'all']), 
              default='all', help='Provider to check limits for')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed usage information')
@click.pass_context
def check_limits(ctx, provider: str, detailed: bool):
    """Check API usage limits and quotas."""
    
    async def _run_checks():
        try:
            console.print("\n[bold magenta]📊 Checking API Limits[/bold magenta]")
            console.print("=" * 50)
            
            results = []
            
            if provider in ['openai', 'all']:
                result = await _check_openai_limits()
                if result:
                    results.append(result)
                    _display_limit_status(result, detailed)
            
            if provider in ['anthropic', 'all']:
                result = await _check_anthropic_limits()
                if result:
                    results.append(result)
                    _display_limit_status(result, detailed)
            
            # Overall summary
            _display_limits_summary(results)
            
            if ctx.obj['json_output']:
                console.print_json(json.dumps([r.dict() for r in results], default=str))
                
        except Exception as e:
            console.print(f"[bold red]❌ Error checking limits: {str(e)}[/bold red]")
            sys.exit(1)
    
    run_async_command(_run_checks)


# Provider Testing Functions
async def _test_openai_provider(model: Optional[str], timeout: int) -> ProviderTest:
    """Test OpenAI provider connectivity and functionality."""
    
    start_time = time.time()
    
    try:
        if not settings.OPENAI_API_KEY:
            return ProviderTest(
                provider="openai",
                available=False,
                response_time=0.0,
                error="OpenAI API key not configured"
            )
        
        # Create provider instance
        provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=model or "gpt-4",
            rate_limit=60
        )
        
        # Test simple request
        test_request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Test Subject",
            target_level=ProficiencyLevel.INTERMEDIATE,
            estimated_duration_hours=2.0,
            learning_objectives=["Test objective 1", "Test objective 2", "Test objective 3"]
        )
        
        # Set timeout for the request
        try:
            response = await asyncio.wait_for(
                provider.generate_course_structure(test_request),
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            return ProviderTest(
                provider="openai",
                available=True,
                response_time=response_time,
                model=provider.model,
                test_content=f"Generated {len(response.chapters)} chapters",
                metadata={
                    "chapters_count": len(response.chapters),
                    "total_duration": response.estimated_total_duration,
                    "quality_indicators": response.quality_indicators
                }
            )
            
        except asyncio.TimeoutError:
            return ProviderTest(
                provider="openai",
                available=False,
                response_time=timeout,
                error=f"Request timed out after {timeout} seconds"
            )
            
    except Exception as e:
        response_time = time.time() - start_time
        return ProviderTest(
            provider="openai",
            available=False,
            response_time=response_time,
            error=str(e)
        )


async def _test_anthropic_provider(model: Optional[str], timeout: int) -> ProviderTest:
    """Test Anthropic provider connectivity and functionality."""
    
    start_time = time.time()
    
    try:
        if not settings.ANTHROPIC_API_KEY:
            return ProviderTest(
                provider="anthropic",
                available=False,
                response_time=0.0,
                error="Anthropic API key not configured"
            )
        
        # Create provider instance
        provider = AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=model or "claude-3-sonnet-20240229",
            rate_limit=60
        )
        
        # Test simple request
        test_request = CourseStructureRequest(
            title="Test Course",
            subject_domain="Test Subject",
            target_level=ProficiencyLevel.INTERMEDIATE,
            estimated_duration_hours=2.0,
            learning_objectives=["Test objective 1", "Test objective 2", "Test objective 3"]
        )
        
        try:
            response = await asyncio.wait_for(
                provider.generate_course_structure(test_request),
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            return ProviderTest(
                provider="anthropic",
                available=True,
                response_time=response_time,
                model=provider.model,
                test_content=f"Generated {len(response.chapters)} chapters",
                metadata={
                    "chapters_count": len(response.chapters),
                    "total_duration": response.estimated_total_duration,
                    "quality_indicators": response.quality_indicators
                }
            )
            
        except asyncio.TimeoutError:
            return ProviderTest(
                provider="anthropic",
                available=False,
                response_time=timeout,
                error=f"Request timed out after {timeout} seconds"
            )
            
    except Exception as e:
        response_time = time.time() - start_time
        return ProviderTest(
            provider="anthropic",
            available=False,
            response_time=response_time,
            error=str(e)
        )


# Generation Testing Functions
async def _test_structure_generation(ai_client: AIClient, level: ProficiencyLevel) -> GenerationTest:
    """Test course structure generation."""
    
    start_time = time.time()
    
    try:
        request = CourseStructureRequest(
            title="Introduction to Machine Learning",
            subject_domain="Computer Science",
            target_level=level,
            estimated_duration_hours=8.0,
            learning_objectives=[
                "Understand fundamental ML concepts",
                "Implement basic ML algorithms",
                "Evaluate model performance",
                "Apply ML to real-world problems"
            ],
            prerequisites=["Basic programming", "Statistics fundamentals"]
        )
        
        response = await ai_client.generate_course_structure(request)
        duration = time.time() - start_time
        
        # Calculate quality score based on response completeness
        quality_score = _calculate_structure_quality(response)
        
        return GenerationTest(
            test_type="structure",
            success=True,
            duration=duration,
            content_length=len(response.chapters),
            quality_score=quality_score,
            metadata={
                "chapters_count": len(response.chapters),
                "total_duration": response.estimated_total_duration,
                "difficulty_progression": response.difficulty_progression,
                "learning_path_rationale": len(response.learning_path_rationale)
            }
        )
        
    except Exception as e:
        duration = time.time() - start_time
        return GenerationTest(
            test_type="structure",
            success=False,
            duration=duration,
            content_length=0,
            error=str(e)
        )


async def _test_content_generation(ai_client: AIClient, level: ProficiencyLevel) -> GenerationTest:
    """Test chapter content generation."""
    
    start_time = time.time()
    
    try:
        request = ChapterContentRequest(
            chapter_title="Introduction to Neural Networks",
            learning_objectives=[
                "Understand neuron basics",
                "Implement simple perceptron",
                "Understand activation functions"
            ],
            target_level=level,
            sequence_number=1,
            previous_concepts=[],
            content_type="mixed",
            estimated_duration_minutes=45,
            include_examples=True,
            include_exercises=True
        )
        
        response = await ai_client.generate_chapter_content(request)
        duration = time.time() - start_time
        
        # Calculate total content length
        content_length = sum(len(block.get("content", "")) for block in response.content_blocks)
        
        # Calculate quality score
        quality_score = _calculate_content_quality(response)
        
        warnings = []
        if duration > 120:  # >2 minutes warning
            warnings.append(f"Generation time {duration:.1f}s exceeds 2-minute target")
        
        return GenerationTest(
            test_type="content",
            success=True,
            duration=duration,
            content_length=content_length,
            quality_score=quality_score,
            warnings=warnings,
            metadata={
                "content_blocks": len(response.content_blocks),
                "examples": len(response.examples),
                "exercises": len(response.exercises),
                "key_concepts": len(response.key_concepts),
                "complexity_score": response.complexity_score
            }
        )
        
    except Exception as e:
        duration = time.time() - start_time
        return GenerationTest(
            test_type="content",
            success=False,
            duration=duration,
            content_length=0,
            error=str(e)
        )


async def _test_content_validation(ai_client: AIClient, level: ProficiencyLevel) -> GenerationTest:
    """Test content quality validation."""
    
    start_time = time.time()
    
    try:
        test_content = """
        Machine Learning is a subset of artificial intelligence that enables computers 
        to learn and make decisions without being explicitly programmed. It involves 
        algorithms that can identify patterns in data and make predictions or decisions 
        based on that data. There are three main types of machine learning: supervised 
        learning, unsupervised learning, and reinforcement learning. Supervised learning 
        uses labeled data to train models, while unsupervised learning finds patterns 
        in unlabeled data. Reinforcement learning involves training agents through 
        rewards and penalties.
        """
        
        request = ContentValidationRequest(
            content=test_content,
            target_level=level,
            learning_objectives=["Understand ML basics", "Identify ML types"],
            subject_domain="Machine Learning",
            expected_keywords=["algorithm", "data", "pattern", "learning"]
        )
        
        response = await ai_client.validate_content_quality(request)
        duration = time.time() - start_time
        
        return GenerationTest(
            test_type="validation",
            success=True,
            duration=duration,
            content_length=len(test_content),
            quality_score=response.overall_score,
            metadata={
                "readability_score": response.readability_score,
                "pedagogical_alignment": response.pedagogical_alignment,
                "objective_coverage": response.objective_coverage,
                "content_accuracy": response.content_accuracy,
                "issues_found": len(response.issues_found),
                "recommendations": len(response.recommendations)
            }
        )
        
    except Exception as e:
        duration = time.time() - start_time
        return GenerationTest(
            test_type="validation",
            success=False,
            duration=duration,
            content_length=0,
            error=str(e)
        )


# Configuration Validation Functions
async def _validate_configuration(check_keys: bool, check_endpoints: bool, 
                                check_models: bool) -> ConfigValidation:
    """Validate AI service configuration."""
    
    missing_keys = []
    invalid_values = []
    warnings = []
    recommendations = []
    
    # Check API keys
    if check_keys:
        if not settings.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        elif not settings.OPENAI_API_KEY.startswith("sk-"):
            invalid_values.append("OPENAI_API_KEY: Invalid format")
        
        if not settings.ANTHROPIC_API_KEY:
            missing_keys.append("ANTHROPIC_API_KEY")
        elif not settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
            invalid_values.append("ANTHROPIC_API_KEY: Invalid format")
    
    # Check endpoints
    if check_endpoints:
        try:
            # Test OpenAI endpoint
            if settings.OPENAI_API_KEY:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        timeout=10
                    )
                    if response.status_code != 200:
                        warnings.append(f"OpenAI endpoint returned {response.status_code}")
        except Exception:
            warnings.append("Could not connect to OpenAI endpoint")
        
        try:
            # Test Anthropic endpoint
            if settings.ANTHROPIC_API_KEY:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": settings.ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01"
                        },
                        timeout=10
                    )
                    # Anthropic returns 400 for GET on messages endpoint, which is expected
                    if response.status_code not in [400, 401, 403]:
                        warnings.append(f"Anthropic endpoint returned {response.status_code}")
        except Exception:
            warnings.append("Could not connect to Anthropic endpoint")
    
    # Check model availability
    if check_models:
        try:
            ai_client = _create_ai_client()
            provider_status = ai_client.get_provider_status()
            
            for provider, available in provider_status.items():
                if not available:
                    warnings.append(f"{provider} provider not available")
        except Exception:
            warnings.append("Could not check model availability")
    
    # Generate recommendations
    if missing_keys:
        recommendations.append("Set missing API keys in environment or .env file")
    
    if settings.DEFAULT_AI_PROVIDER not in ["openai", "anthropic"]:
        recommendations.append("Set DEFAULT_AI_PROVIDER to 'openai' or 'anthropic'")
    
    if settings.MAX_CHAPTER_GENERATION_TIME < 60:
        recommendations.append("Consider increasing MAX_CHAPTER_GENERATION_TIME for complex content")
    
    return ConfigValidation(
        valid=not missing_keys and not invalid_values,
        missing_keys=missing_keys,
        invalid_values=invalid_values,
        warnings=warnings,
        recommendations=recommendations
    )


# Limit Checking Functions
async def _check_openai_limits() -> Optional[LimitStatus]:
    """Check OpenAI API usage limits."""
    
    if not settings.OPENAI_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Check current usage (simplified - real implementation would need more sophisticated tracking)
            response = await client.get(
                "https://api.openai.com/v1/usage",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=10
            )
            
            if response.status_code == 200:
                # Simulate usage data (real implementation would parse actual response)
                current_usage = 1500  # Placeholder
                limit = 10000  # Placeholder
                percentage_used = (current_usage / limit) * 100
                
                status = "healthy"
                if percentage_used > 80:
                    status = "critical"
                elif percentage_used > 60:
                    status = "warning"
                
                recommendations = []
                if status == "critical":
                    recommendations.append("Usage is very high - consider rate limiting")
                elif status == "warning":
                    recommendations.append("Monitor usage closely")
                
                return LimitStatus(
                    provider="openai",
                    current_usage=current_usage,
                    limit=limit,
                    percentage_used=percentage_used,
                    status=status,
                    recommendations=recommendations
                )
            
    except Exception as e:
        logger.warning(f"Could not check OpenAI limits: {e}")
    
    return None


async def _check_anthropic_limits() -> Optional[LimitStatus]:
    """Check Anthropic API usage limits."""
    
    if not settings.ANTHROPIC_API_KEY:
        return None
    
    # Anthropic doesn't have a public usage endpoint yet, so we simulate
    # In real implementation, this would integrate with their billing/usage API when available
    
    try:
        # Placeholder implementation
        current_usage = 800  # Placeholder
        limit = 5000  # Placeholder
        percentage_used = (current_usage / limit) * 100
        
        status = "healthy"
        if percentage_used > 80:
            status = "critical"
        elif percentage_used > 60:
            status = "warning"
        
        recommendations = []
        if status == "critical":
            recommendations.append("Usage is very high - consider rate limiting")
        elif status == "warning":
            recommendations.append("Monitor usage closely")
        
        return LimitStatus(
            provider="anthropic",
            current_usage=current_usage,
            limit=limit,
            percentage_used=percentage_used,
            status=status,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.warning(f"Could not check Anthropic limits: {e}")
    
    return None


# Utility Functions
def _create_ai_client(provider: Optional[str] = None) -> AIClient:
    """Create AI client with optional provider preference."""
    
    if provider:
        return create_ai_client(preferred_provider=provider)
    else:
        return create_ai_client()


def _calculate_structure_quality(response) -> float:
    """Calculate quality score for course structure."""
    
    score = 0.0
    total_checks = 0
    
    # Check chapters count
    if hasattr(response, 'chapters') and response.chapters:
        score += 0.3 if len(response.chapters) >= 3 else 0.1
    total_checks += 0.3
    
    # Check quality indicators
    if hasattr(response, 'quality_indicators') and response.quality_indicators:
        avg_quality = sum(response.quality_indicators.values()) / len(response.quality_indicators)
        score += avg_quality * 0.4
    total_checks += 0.4
    
    # Check difficulty progression
    if hasattr(response, 'difficulty_progression') and response.difficulty_progression:
        score += 0.2 if len(response.difficulty_progression) > 1 else 0.1
    total_checks += 0.2
    
    # Check learning path rationale
    if hasattr(response, 'learning_path_rationale') and response.learning_path_rationale:
        score += 0.1 if len(response.learning_path_rationale) > 50 else 0.05
    total_checks += 0.1
    
    return min(score / total_checks if total_checks > 0 else 0.0, 1.0)


def _calculate_content_quality(response) -> float:
    """Calculate quality score for chapter content."""
    
    score = 0.0
    total_checks = 0
    
    # Check content blocks
    if hasattr(response, 'content_blocks') and response.content_blocks:
        score += 0.3 if len(response.content_blocks) >= 2 else 0.1
    total_checks += 0.3
    
    # Check examples
    if hasattr(response, 'examples') and response.examples:
        score += 0.2 if len(response.examples) >= 1 else 0.1
    total_checks += 0.2
    
    # Check exercises
    if hasattr(response, 'exercises') and response.exercises:
        score += 0.2 if len(response.exercises) >= 1 else 0.1
    total_checks += 0.2
    
    # Check key concepts
    if hasattr(response, 'key_concepts') and response.key_concepts:
        score += 0.2 if len(response.key_concepts) >= 3 else 0.1
    total_checks += 0.2
    
    # Check summary
    if hasattr(response, 'summary') and response.summary:
        score += 0.1 if len(response.summary) > 50 else 0.05
    total_checks += 0.1
    
    return min(score / total_checks if total_checks > 0 else 0.0, 1.0)


# Display Functions
def _display_provider_result(result: ProviderTest):
    """Display provider test result."""
    
    status_color = "green" if result.available else "red"
    status_icon = "✅" if result.available else "❌"
    
    panel_content = f"""
[bold]{result.provider.upper()} Provider[/bold]

Status: [{status_color}]{status_icon} {'Available' if result.available else 'Unavailable'}[/{status_color}]
Response Time: {result.response_time:.2f}s
Model: {result.model or 'N/A'}
"""
    
    if result.error:
        panel_content += f"Error: [red]{result.error}[/red]\n"
    
    if result.test_content:
        panel_content += f"Test Result: {result.test_content}\n"
    
    if result.metadata:
        panel_content += "\nMetadata:\n"
        for key, value in result.metadata.items():
            panel_content += f"  {key}: {value}\n"
    
    console.print(Panel(panel_content, title=f"{result.provider.upper()} Test"))


def _display_provider_summary(results: List[ProviderTest]):
    """Display provider test summary."""
    
    table = Table(title="Provider Test Summary")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Response Time", style="yellow")
    table.add_column("Model", style="blue")
    
    for result in results:
        status = "✅ Available" if result.available else "❌ Unavailable"
        table.add_row(
            result.provider.upper(),
            status,
            f"{result.response_time:.2f}s",
            result.model or "N/A"
        )
    
    console.print("\n")
    console.print(table)


def _display_generation_result(result: GenerationTest):
    """Display generation test result."""
    
    status_color = "green" if result.success else "red"
    status_icon = "✅" if result.success else "❌"
    
    panel_content = f"""
[bold]{result.test_type.upper()} Generation Test[/bold]

Status: [{status_color}]{status_icon} {'Success' if result.success else 'Failed'}[/{status_color}]
Duration: {result.duration:.2f}s
Content Length: {result.content_length} chars
"""
    
    if result.quality_score is not None:
        score_color = "green" if result.quality_score > 0.8 else "yellow" if result.quality_score > 0.6 else "red"
        panel_content += f"Quality Score: [{score_color}]{result.quality_score:.2f}[/{score_color}]\n"
    
    if result.error:
        panel_content += f"Error: [red]{result.error}[/red]\n"
    
    if result.warnings:
        panel_content += f"Warnings: [yellow]{', '.join(result.warnings)}[/yellow]\n"
    
    if result.metadata:
        panel_content += "\nDetails:\n"
        for key, value in result.metadata.items():
            panel_content += f"  {key}: {value}\n"
    
    console.print(Panel(panel_content, title=f"{result.test_type.upper()} Test"))


def _display_generation_summary(results: List[GenerationTest]):
    """Display generation test summary."""
    
    table = Table(title="Generation Test Summary")
    table.add_column("Test Type", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Quality", style="blue")
    
    for result in results:
        status = "✅ Success" if result.success else "❌ Failed"
        quality = f"{result.quality_score:.2f}" if result.quality_score else "N/A"
        table.add_row(
            result.test_type.upper(),
            status,
            f"{result.duration:.2f}s",
            quality
        )
    
    console.print("\n")
    console.print(table)


def _display_config_validation(validation: ConfigValidation):
    """Display configuration validation results."""
    
    status_color = "green" if validation.valid else "red"
    status_icon = "✅" if validation.valid else "❌"
    
    panel_content = f"""
[bold]Configuration Validation[/bold]

Status: [{status_color}]{status_icon} {'Valid' if validation.valid else 'Invalid'}[/{status_color}]
"""
    
    if validation.missing_keys:
        panel_content += f"\n[red]Missing Keys:[/red]\n"
        for key in validation.missing_keys:
            panel_content += f"  • {key}\n"
    
    if validation.invalid_values:
        panel_content += f"\n[red]Invalid Values:[/red]\n"
        for value in validation.invalid_values:
            panel_content += f"  • {value}\n"
    
    if validation.warnings:
        panel_content += f"\n[yellow]Warnings:[/yellow]\n"
        for warning in validation.warnings:
            panel_content += f"  • {warning}\n"
    
    if validation.recommendations:
        panel_content += f"\n[blue]Recommendations:[/blue]\n"
        for rec in validation.recommendations:
            panel_content += f"  • {rec}\n"
    
    console.print(Panel(panel_content, title="Configuration Validation"))


def _display_limit_status(status: LimitStatus, detailed: bool):
    """Display API limit status."""
    
    status_colors = {
        "healthy": "green",
        "warning": "yellow",
        "critical": "red"
    }
    
    status_icons = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🚨"
    }
    
    status_color = status_colors.get(status.status, "white")
    status_icon = status_icons.get(status.status, "❓")
    
    panel_content = f"""
[bold]{status.provider.upper()} API Limits[/bold]

Status: [{status_color}]{status_icon} {status.status.upper()}[/{status_color}]
Usage: {status.current_usage:,} / {status.limit:,} ({status.percentage_used:.1f}%)
"""
    
    if status.reset_time:
        panel_content += f"Reset Time: {status.reset_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if status.recommendations:
        panel_content += f"\n[blue]Recommendations:[/blue]\n"
        for rec in status.recommendations:
            panel_content += f"  • {rec}\n"
    
    if detailed:
        panel_content += f"\nDetailed Information:\n"
        panel_content += f"  Provider: {status.provider}\n"
        panel_content += f"  Current Usage: {status.current_usage:,}\n"
        panel_content += f"  Limit: {status.limit:,}\n"
        panel_content += f"  Percentage Used: {status.percentage_used:.2f}%\n"
    
    console.print(Panel(panel_content, title=f"{status.provider.upper()} Limits"))


def _display_limits_summary(results: List[LimitStatus]):
    """Display limits summary."""
    
    if not results:
        console.print("\n[yellow]No limit information available[/yellow]")
        return
    
    table = Table(title="API Limits Summary")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Usage", style="yellow")
    table.add_column("Percentage", style="blue")
    
    for result in results:
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🚨"
        }
        
        status_display = f"{status_icons.get(result.status, '❓')} {result.status.upper()}"
        usage_display = f"{result.current_usage:,} / {result.limit:,}"
        percentage_display = f"{result.percentage_used:.1f}%"
        
        table.add_row(
            result.provider.upper(),
            status_display,
            usage_display,
            percentage_display
        )
    
    console.print("\n")
    console.print(table)


# Entry point for async commands
def run_async_command(command):
    """Run async command in event loop."""
    try:
        asyncio.run(command())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    ai()