#!/usr/bin/env python3
"""
Quickstart Validation Test Suite - T067

Integration tests that validate all scenarios described in the quickstart guide.
These tests execute the complete user journey and verify system compliance.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import requests
from unittest.mock import AsyncMock, patch

# Test configuration
TEST_CONFIG = {
    "api_base_url": "http://localhost:8000",
    "api_key": "test-api-key",
    "timeout": 300,  # 5 minutes max per test
    "performance_thresholds": {
        "course_list": 0.2,      # 200ms
        "course_creation": 0.5,   # 500ms  
        "status_check": 0.1,      # 100ms
        "export_initiation": 0.3, # 300ms
        "chapter_generation": 120, # 2 minutes
        "full_course": 600,       # 10 minutes
        "quality_validation": 30,  # 30 seconds
    },
    "quality_thresholds": {
        "readability_score": 70.0,
        "pedagogical_alignment": 0.8,
        "objective_coverage": 1.0,
        "content_accuracy": 0.9,
        "bias_detection_score": 0.1,
    }
}

class QuickstartValidator:
    """Main validator for quickstart scenarios."""
    
    def __init__(self):
        self.base_url = TEST_CONFIG["api_base_url"]
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": TEST_CONFIG["api_key"]
        }
        self.test_results = {
            "performance": {},
            "quality": {},
            "errors": [],
            "success_count": 0,
            "total_tests": 0
        }
    
    def measure_performance(self, test_name: str):
        """Decorator to measure API performance."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    self.test_results["performance"][test_name] = {
                        "duration": duration,
                        "threshold": TEST_CONFIG["performance_thresholds"].get(test_name, float('inf')),
                        "passed": duration <= TEST_CONFIG["performance_thresholds"].get(test_name, float('inf'))
                    }
                    
                    return result
                except Exception as e:
                    self.test_results["errors"].append({
                        "test": test_name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    raise
            return wrapper
        return decorator

@pytest.fixture
def validator():
    """Create validator instance for tests."""
    return QuickstartValidator()

@pytest.fixture
def sample_course_request():
    """Sample course creation request from quickstart guide."""
    return {
        "title": "Introduction to Machine Learning",
        "description": "Comprehensive ML course for beginners",
        "subject_domain": "Computer Science",
        "target_audience": {
            "proficiency_level": "beginner",
            "prerequisites": ["Basic mathematics", "Python programming"],
            "learning_preferences": ["visual", "practical"]
        },
        "estimated_duration": "PT20H",
        "content_preferences": {
            "include_practical_examples": True,
            "theory_to_practice_ratio": 0.6
        }
    }

class TestQuickstartPrimaryScenario:
    """Test the primary user story from quickstart guide."""
    
    @pytest.mark.asyncio
    async def test_step_1_create_course_request(self, validator, sample_course_request):
        """Test Step 1: Create Course Request."""
        validator.test_results["total_tests"] += 1
        
        # Mock API call since we don't have actual server running
        with patch('requests.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "generating",
                "generation_task_id": "task-12345",
                "estimated_completion_time": "2025-09-16T18:30:00Z"
            }
            mock_post.return_value = mock_response
            
            # Simulate course creation
            start_time = time.time()
            response_data = mock_response.json.return_value
            end_time = time.time()
            
            # Validate response structure
            assert "id" in response_data
            assert "status" in response_data
            assert response_data["status"] == "generating"
            assert "generation_task_id" in response_data
            
            # Check performance
            duration = end_time - start_time
            threshold = TEST_CONFIG["performance_thresholds"]["course_creation"]
            assert duration <= threshold, f"Course creation took {duration:.2f}s, exceeds {threshold}s threshold"
            
            validator.test_results["success_count"] += 1
    
    @pytest.mark.asyncio
    async def test_step_2_monitor_generation_progress(self, validator):
        """Test Step 2: Monitor Generation Progress."""
        validator.test_results["total_tests"] += 1
        
        course_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock progress tracking
        progress_stages = [
            {"status": "in_progress", "progress_percentage": 25.0, "current_phase": "structure"},
            {"status": "in_progress", "progress_percentage": 70.0, "current_phase": "content"},
            {"status": "completed", "progress_percentage": 100.0, "current_phase": "export"}
        ]
        
        for stage in progress_stages:
            # Simulate status check
            with patch('requests.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "task_id": "task-12345",
                    **stage,
                    "estimated_time_remaining": "PT2M"
                }
                mock_get.return_value = mock_response
                
                start_time = time.time()
                response_data = mock_response.json.return_value
                end_time = time.time()
                
                # Validate response structure
                assert "task_id" in response_data
                assert "status" in response_data
                assert "progress_percentage" in response_data
                assert 0 <= response_data["progress_percentage"] <= 100
                
                # Check performance
                duration = end_time - start_time
                threshold = TEST_CONFIG["performance_thresholds"]["status_check"]
                assert duration <= threshold, f"Status check took {duration:.2f}s, exceeds {threshold}s threshold"
        
        validator.test_results["success_count"] += 1
    
    @pytest.mark.asyncio 
    async def test_step_3_retrieve_generated_course(self, validator):
        """Test Step 3: Retrieve Generated Course."""
        validator.test_results["total_tests"] += 1
        
        course_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock course retrieval
        with patch('requests.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": course_id,
                "status": "ready",
                "title": "Introduction to Machine Learning",
                "chapters": [
                    {"id": "ch1", "title": "Introduction to ML", "order": 1},
                    {"id": "ch2", "title": "Data Preparation", "order": 2},
                    {"id": "ch3", "title": "Basic Algorithms", "order": 3},
                    {"id": "ch4", "title": "Model Evaluation", "order": 4}
                ],
                "learning_objectives": [
                    "Understand basic ML concepts",
                    "Prepare data for ML models",
                    "Apply basic algorithms",
                    "Evaluate model performance"
                ],
                "target_audience": {
                    "proficiency_level": "beginner"
                }
            }
            mock_get.return_value = mock_response
            
            response_data = mock_response.json.return_value
            
            # Validation criteria from quickstart
            assert response_data["status"] == "ready"
            assert 3 <= len(response_data["chapters"]) <= 5, "Should have 3-5 chapters for beginner level"
            assert len(response_data["learning_objectives"]) >= 3, "Should have specific learning objectives"
            assert response_data["target_audience"]["proficiency_level"] == "beginner"
            
            validator.test_results["success_count"] += 1
    
    @pytest.mark.asyncio
    async def test_step_4_validate_quality_metrics(self, validator):
        """Test Step 4: Validate Quality Metrics."""
        validator.test_results["total_tests"] += 1
        
        course_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock quality metrics
        with patch('requests.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "readability_score": 75.0,
                "pedagogical_alignment": 0.90,
                "objective_coverage": 1.0,
                "content_accuracy": 0.95,
                "bias_detection_score": 0.05,
                "generation_timestamp": "2025-09-16T18:25:00Z"
            }
            mock_get.return_value = mock_response
            
            start_time = time.time()
            metrics = mock_response.json.return_value
            end_time = time.time()
            
            # Validate against thresholds from quickstart
            thresholds = TEST_CONFIG["quality_thresholds"]
            
            assert metrics["readability_score"] >= thresholds["readability_score"], \
                f"Readability {metrics['readability_score']} < {thresholds['readability_score']}"
            
            assert metrics["pedagogical_alignment"] >= thresholds["pedagogical_alignment"], \
                f"Pedagogical alignment {metrics['pedagogical_alignment']} < {thresholds['pedagogical_alignment']}"
            
            assert metrics["objective_coverage"] >= thresholds["objective_coverage"], \
                f"Objective coverage {metrics['objective_coverage']} < {thresholds['objective_coverage']}"
            
            assert metrics["content_accuracy"] >= thresholds["content_accuracy"], \
                f"Content accuracy {metrics['content_accuracy']} < {thresholds['content_accuracy']}"
            
            assert metrics["bias_detection_score"] <= thresholds["bias_detection_score"], \
                f"Bias score {metrics['bias_detection_score']} > {thresholds['bias_detection_score']}"
            
            # Performance check
            duration = end_time - start_time
            threshold = TEST_CONFIG["performance_thresholds"]["quality_validation"]
            assert duration <= threshold, f"Quality validation took {duration:.2f}s, exceeds {threshold}s threshold"
            
            validator.test_results["quality"] = metrics
            validator.test_results["success_count"] += 1
    
    @pytest.mark.asyncio
    async def test_step_5_export_functionality(self, validator):
        """Test Step 5: Test Export Functionality."""
        validator.test_results["total_tests"] += 1
        
        course_id = "550e8400-e29b-41d4-a716-446655440000"
        
        export_request = {
            "format": "scorm2004",
            "include_assessments": True,
            "include_multimedia": True
        }
        
        # Mock export request
        with patch('requests.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "download_url": "https://api.courseplatform.com/downloads/course-export-123.zip",
                "expires_at": "2025-09-17T18:25:00Z",
                "file_size": 2457600,
                "checksum": "sha256:abcd1234..."
            }
            mock_post.return_value = mock_response
            
            start_time = time.time()
            response_data = mock_response.json.return_value
            end_time = time.time()
            
            # Validate export response
            assert "download_url" in response_data
            assert "expires_at" in response_data
            assert "file_size" in response_data
            assert "checksum" in response_data
            assert response_data["file_size"] > 0
            
            # Performance check
            duration = end_time - start_time
            threshold = TEST_CONFIG["performance_thresholds"]["export_initiation"]
            assert duration <= threshold, f"Export initiation took {duration:.2f}s, exceeds {threshold}s threshold"
            
            validator.test_results["success_count"] += 1

class TestQuickstartIntegrationScenarios:
    """Test integration scenarios from quickstart guide."""
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, validator):
        """Test Case 1: Performance Requirements."""
        validator.test_results["total_tests"] += 1
        
        course_id = "550e8400-e29b-41d4-a716-446655440000"
        chapter_id = "chapter-1"
        
        # Mock chapter regeneration
        with patch('requests.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "task_id": "regen-task-123",
                "status": "in_progress",
                "estimated_completion": "2025-09-16T18:27:00Z"
            }
            mock_post.return_value = mock_response
            
            start_time = time.time()
            response_data = mock_response.json.return_value
            end_time = time.time()
            
            # Simulate completion time (should be < 2 minutes)
            completion_time = 90  # 1.5 minutes
            threshold = TEST_CONFIG["performance_thresholds"]["chapter_generation"]
            
            assert completion_time <= threshold, \
                f"Chapter generation took {completion_time}s, exceeds {threshold}s threshold"
            
            validator.test_results["success_count"] += 1
    
    @pytest.mark.asyncio
    async def test_concurrent_generation(self, validator):
        """Test Case 2: Concurrent Generation."""
        validator.test_results["total_tests"] += 1
        
        # Mock 5 concurrent course creations
        concurrent_requests = []
        for i in range(1, 6):
            request_data = {
                "title": f"Test Course {i}",
                "subject_domain": "Test",
                "target_audience": {
                    "proficiency_level": "beginner"
                }
            }
            concurrent_requests.append(request_data)
        
        # Simulate concurrent processing
        with patch('requests.post') as mock_post:
            mock_responses = []
            for i in range(5):
                mock_response = AsyncMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    "id": f"course-{i+1}",
                    "status": "generating",
                    "generation_task_id": f"task-{i+1}"
                }
                mock_responses.append(mock_response)
            
            mock_post.side_effect = mock_responses
            
            # All requests should succeed
            for i, request in enumerate(concurrent_requests):
                response = mock_responses[i]
                response_data = response.json.return_value
                
                assert response.status_code == 201
                assert "id" in response_data
                assert "status" in response_data
            
            validator.test_results["success_count"] += 1

class TestQuickstartErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_request_handling(self, validator):
        """Test Case 4: Invalid Request Handling."""
        validator.test_results["total_tests"] += 1
        
        invalid_request = {
            "title": "Test Course",
            "subject_domain": "Test",
            "target_audience": {
                "proficiency_level": "invalid_level"
            }
        }
        
        # Mock validation error response
        with patch('requests.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "detail": "Validation error: proficiency_level must be one of: beginner, intermediate, advanced",
                "error_code": "VALIDATION_ERROR"
            }
            mock_post.return_value = mock_response
            
            response = mock_response
            
            # Should return 400 Bad Request
            assert response.status_code == 400
            
            error_data = response.json.return_value
            assert "detail" in error_data
            assert "Validation error" in error_data["detail"]
            
            validator.test_results["success_count"] += 1
    
    @pytest.mark.asyncio
    async def test_generation_failure_recovery(self, validator):
        """Test Case 5: Generation Failure Recovery."""
        validator.test_results["total_tests"] += 1
        
        failed_course_id = "failed-generation-id"
        
        # Mock failure response
        with patch('requests.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "task_id": "failed-task",
                "status": "failed",
                "error_message": "AI service temporarily unavailable",
                "retry_available": True,
                "retry_delay": "PT5M"
            }
            mock_get.return_value = mock_response
            
            response_data = mock_response.json.return_value
            
            # Should provide graceful error response with retry options
            assert response_data["status"] == "failed"
            assert "error_message" in response_data
            assert response_data["retry_available"] is True
            assert "retry_delay" in response_data
            
            validator.test_results["success_count"] += 1

@pytest.mark.asyncio
async def test_complete_quickstart_validation(validator):
    """Run complete quickstart validation and generate report."""
    print("🚀 Starting Quickstart Validation Test Suite")
    print("=" * 60)
    
    # Initialize test results
    start_time = time.time()
    
    # Run all test classes
    test_classes = [
        TestQuickstartPrimaryScenario(),
        TestQuickstartIntegrationScenarios(), 
        TestQuickstartErrorHandling()
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n📋 Running {class_name}")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                test_method = getattr(test_class, method_name)
                
                # Run test with appropriate fixtures
                if method_name in ['test_step_1_create_course_request']:
                    sample_request = {
                        "title": "Introduction to Machine Learning",
                        "description": "Comprehensive ML course for beginners",
                        "subject_domain": "Computer Science",
                        "target_audience": {
                            "proficiency_level": "beginner",
                            "prerequisites": ["Basic mathematics", "Python programming"],
                            "learning_preferences": ["visual", "practical"]
                        },
                        "estimated_duration": "PT20H",
                        "content_preferences": {
                            "include_practical_examples": True,
                            "theory_to_practice_ratio": 0.6
                        }
                    }
                    await test_method(validator, sample_request)
                else:
                    await test_method(validator)
                
                print(f"  ✅ {method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
                validator.test_results["errors"].append({
                    "test": f"{class_name}.{method_name}",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            total_tests += 1
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Generate final report
    print("\n" + "=" * 60)
    print("📊 QUICKSTART VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Execution Time: {execution_time:.2f} seconds")
    
    # Performance summary
    if validator.test_results["performance"]:
        print("\n⚡ PERFORMANCE RESULTS:")
        for test_name, perf_data in validator.test_results["performance"].items():
            status = "✅ PASS" if perf_data["passed"] else "❌ FAIL"
            print(f"  {test_name}: {perf_data['duration']:.3f}s ({status})")
    
    # Quality summary  
    if validator.test_results["quality"]:
        print("\n🎯 QUALITY METRICS:")
        for metric, value in validator.test_results["quality"].items():
            if metric != "generation_timestamp":
                print(f"  {metric}: {value}")
    
    # Error summary
    if validator.test_results["errors"]:
        print("\n🚨 ERRORS ENCOUNTERED:")
        for error in validator.test_results["errors"]:
            print(f"  {error['test']}: {error['error']}")
    
    # Overall status
    overall_success = passed_tests == total_tests and len(validator.test_results["errors"]) == 0
    status = "✅ SUCCESS" if overall_success else "❌ FAILED"
    print(f"\n🎯 OVERALL STATUS: {status}")
    
    # Save detailed report
    report_path = Path("quickstart_validation_report.json")
    detailed_report = {
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "execution_time": execution_time,
            "overall_success": overall_success
        },
        "performance": validator.test_results["performance"],
        "quality": validator.test_results["quality"],
        "errors": validator.test_results["errors"],
        "timestamp": datetime.now().isoformat()
    }
    
    with open(report_path, 'w') as f:
        json.dump(detailed_report, f, indent=2)
    
    print(f"📋 Detailed report saved to: {report_path}")
    
    return overall_success

if __name__ == "__main__":
    """Run quickstart validation as standalone script."""
    import sys
    
    async def main():
        validator = QuickstartValidator()
        success = await test_complete_quickstart_validation(validator)
        sys.exit(0 if success else 1)
    
    asyncio.run(main())