"""
Unit tests for Course models.

Tests T060: Course entity model validation, business rules, and data integrity.
Covers CourseBase, CourseCreate, CourseUpdate, Course schemas and validation logic.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import ValidationError

from src.models.course import (
    CourseBase,
    CourseCreate, 
    CourseUpdate,
    Course,
    CourseListResponse,
)
from src.models.value_objects import TargetAudience, QualityMetrics
from src.models.enums import (
    CourseStatus,
    ProficiencyLevel,
    LearningPreference,
    CognitiveLevel,
)


class TestCourseBase:
    """Test CourseBase schema validation and business rules."""
    
    def test_valid_course_base_creation(self):
        """Test creating valid CourseBase with all required fields."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=["Basic math"],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        course_data = {
            "title": "Introduction to Python",
            "description": "Learn Python programming from scratch",
            "subject_domain": "Computer Science", 
            "target_audience": target_audience,
            "learning_objectives": [
                "Understand Python syntax",
                "Write basic Python programs",
                "Use Python data structures",
            ],
            "estimated_duration": "PT20H",
            "difficulty_score": 2.0,
            "language": "en",
            "version": "1.0.0",
        }
        
        course = CourseBase(**course_data)
        
        assert course.title == "Introduction to Python"
        assert course.description == "Learn Python programming from scratch"
        assert course.subject_domain == "Computer Science"
        assert course.target_audience == target_audience
        assert len(course.learning_objectives) == 3
        assert course.estimated_duration == "PT20H"
        assert course.difficulty_score == 2.0
        assert course.language == "en"
        assert course.version == "1.0.0"
    
    def test_title_validation(self):
        """Test title field validation rules."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        base_data = {
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0,
        }
        
        # Test minimum length
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(title="AB", **base_data)
        assert "at least 3 characters" in str(exc_info.value)
        
        # Test maximum length
        long_title = "A" * 201
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(title=long_title, **base_data)
        assert "at most 200 characters" in str(exc_info.value)
        
        # Test valid lengths
        CourseBase(title="ABC", **base_data)  # Minimum valid
        CourseBase(title="A" * 200, **base_data)  # Maximum valid
    
    def test_learning_objectives_validation(self):
        """Test learning objectives validation rules."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        base_data = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0,
        }
        
        # Test minimum count
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(learning_objectives=["Only one", "Only two"], **base_data)
        assert "at least 3 items" in str(exc_info.value)
        
        # Test maximum count
        too_many_objectives = [f"Objective {i}" for i in range(13)]
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(learning_objectives=too_many_objectives, **base_data)
        assert "at most 12 items" in str(exc_info.value)
        
        # Test objective content validation
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(learning_objectives=["Good objective", "Bad", "Another good objective"], **base_data)
        assert "at least 5 characters" in str(exc_info.value)
        
        # Test valid objectives
        valid_objectives = [
            "Understand basic concepts",
            "Apply knowledge in practice",
            "Analyze complex problems",
        ]
        course = CourseBase(learning_objectives=valid_objectives, **base_data)
        assert len(course.learning_objectives) == 3
    
    def test_difficulty_score_validation(self):
        """Test difficulty score validation range."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        base_data = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
        }
        
        # Test below minimum
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(difficulty_score=0.5, **base_data)
        assert "greater than or equal to 1" in str(exc_info.value)
        
        # Test above maximum
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(difficulty_score=5.5, **base_data)
        assert "less than or equal to 5" in str(exc_info.value)
        
        # Test valid range
        for score in [1.0, 2.5, 5.0]:
            course = CourseBase(difficulty_score=score, **base_data)
            assert course.difficulty_score == score
    
    def test_duration_format_validation(self):
        """Test ISO 8601 duration format validation."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        base_data = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "difficulty_score": 2.0,
        }
        
        # Test invalid format
        with pytest.raises(ValidationError) as exc_info:
            CourseBase(estimated_duration="20 hours", **base_data)
        assert "ISO 8601 format" in str(exc_info.value)
        
        # Test valid formats
        valid_durations = ["PT20H", "PT30M", "PT2H30M", "PT45M"]
        for duration in valid_durations:
            course = CourseBase(estimated_duration=duration, **base_data)
            assert course.estimated_duration == duration
    
    def test_language_code_validation(self):
        """Test ISO 639-1 language code validation."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        base_data = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0,
        }
        
        # Test invalid format
        with pytest.raises(ValidationError):
            CourseBase(language="english", **base_data)
        
        with pytest.raises(ValidationError):
            CourseBase(language="e", **base_data)
        
        # Test valid codes
        valid_codes = ["en", "fr", "es", "de", "it"]
        for code in valid_codes:
            course = CourseBase(language=code, **base_data)
            assert course.language == code
    
    def test_version_format_validation(self):
        """Test semantic version format validation."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        base_data = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0,
        }
        
        # Test invalid format
        with pytest.raises(ValidationError):
            CourseBase(version="v1.0", **base_data)
        
        with pytest.raises(ValidationError):
            CourseBase(version="1.0", **base_data)
        
        # Test valid formats
        valid_versions = ["1.0.0", "2.1.3", "10.0.1"]
        for version in valid_versions:
            course = CourseBase(version=version, **base_data)
            assert course.version == version


class TestCourseCreate:
    """Test CourseCreate schema for new course creation."""
    
    def test_course_create_inherits_validation(self):
        """Test that CourseCreate inherits all CourseBase validation."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.INTERMEDIATE,
            prerequisites=["Python basics"],
            learning_preferences=[LearningPreference.PRACTICAL],
        )
        
        course_data = {
            "title": "Advanced Python Programming",
            "description": "Deep dive into Python advanced concepts",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": [
                "Master decorators and metaclasses",
                "Implement design patterns",
                "Optimize code performance",
            ],
            "estimated_duration": "PT40H",
            "difficulty_score": 4.0,
            "language": "en",
            "version": "1.0.0",
        }
        
        course = CourseCreate(**course_data)
        assert isinstance(course, CourseCreate)
        assert course.title == "Advanced Python Programming"
        assert course.difficulty_score == 4.0


class TestCourseUpdate:
    """Test CourseUpdate schema for partial course updates."""
    
    def test_all_fields_optional(self):
        """Test that all fields in CourseUpdate are optional."""
        # Should be able to create with no fields
        update = CourseUpdate()
        assert update.title is None
        assert update.description is None
        assert update.learning_objectives is None
        assert update.status is None
    
    def test_partial_update_validation(self):
        """Test partial update with some fields."""
        update_data = {
            "title": "Updated Course Title",
            "status": CourseStatus.PUBLISHED,
        }
        
        update = CourseUpdate(**update_data)
        assert update.title == "Updated Course Title"
        assert update.status == CourseStatus.PUBLISHED
        assert update.description is None
        assert update.learning_objectives is None
    
    def test_update_validation_rules_applied(self):
        """Test that validation rules still apply to provided fields."""
        # Test title validation
        with pytest.raises(ValidationError):
            CourseUpdate(title="AB")  # Too short
        
        # Test learning objectives validation
        with pytest.raises(ValidationError):
            CourseUpdate(learning_objectives=["Too", "Few"])  # Less than 3
        
        # Valid updates should work
        update = CourseUpdate(
            title="Valid Title",
            learning_objectives=["Good objective one", "Good objective two", "Good objective three"]
        )
        assert update.title == "Valid Title"
        assert len(update.learning_objectives) == 3


class TestCourse:
    """Test complete Course model with all fields."""
    
    def test_course_with_all_fields(self):
        """Test Course model with all fields populated."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.ADVANCED,
            prerequisites=["Calculus", "Linear Algebra"],
            learning_preferences=[LearningPreference.THEORETICAL],
        )
        
        quality_metrics = QualityMetrics(
            readability_score=85.0,
            pedagogical_alignment=0.9,
            objective_coverage=1.0,
            content_accuracy=0.95,
            bias_detection_score=0.05,
            user_satisfaction_score=4.5,
            generation_timestamp=datetime.utcnow(),
        )
        
        course_id = uuid4()
        now = datetime.utcnow()
        
        course_data = {
            "id": course_id,
            "title": "Machine Learning Theory",
            "description": "Theoretical foundations of machine learning",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": [
                "Understand statistical learning theory",
                "Analyze algorithm complexity",
                "Prove convergence theorems",
            ],
            "estimated_duration": "PT60H",
            "difficulty_score": 4.5,
            "language": "en",
            "version": "2.0.0",
            "status": CourseStatus.PUBLISHED,
            "created_at": now,
            "updated_at": now,
            "quality_metrics": quality_metrics,
        }
        
        course = Course(**course_data)
        
        assert course.id == course_id
        assert course.title == "Machine Learning Theory"
        assert course.status == CourseStatus.PUBLISHED
        assert course.quality_metrics == quality_metrics
        assert course.created_at == now
        assert course.updated_at == now
    
    def test_difficulty_audience_alignment_validation(self):
        """Test difficulty score alignment with target audience proficiency."""
        base_data = {
            "id": uuid4(),
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
            "language": "en",
            "version": "1.0.0",
            "status": CourseStatus.DRAFT,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        # Test beginner level with too high difficulty
        beginner_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        with pytest.raises(ValidationError) as exc_info:
            Course(
                target_audience=beginner_audience,
                difficulty_score=3.0,  # Too high for beginner
                **base_data
            )
        assert "Beginner courses should have difficulty ≤ 2.5" in str(exc_info.value)
        
        # Test intermediate level with appropriate difficulty
        intermediate_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.INTERMEDIATE,
            prerequisites=["Basic knowledge"],
            learning_preferences=[LearningPreference.PRACTICAL],
        )
        
        course = Course(
            target_audience=intermediate_audience,
            difficulty_score=3.0,  # Valid for intermediate
            **base_data
        )
        assert course.difficulty_score == 3.0
        
        # Test intermediate with invalid difficulty
        with pytest.raises(ValidationError) as exc_info:
            Course(
                target_audience=intermediate_audience,
                difficulty_score=1.5,  # Too low for intermediate
                **base_data
            )
        assert "Intermediate courses should have difficulty 2.0-4.0" in str(exc_info.value)
        
        # Test advanced level validation
        advanced_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.ADVANCED,
            prerequisites=["Extensive background"],
            learning_preferences=[LearningPreference.THEORETICAL],
        )
        
        with pytest.raises(ValidationError) as exc_info:
            Course(
                target_audience=advanced_audience,
                difficulty_score=2.5,  # Too low for advanced
                **base_data
            )
        assert "Advanced courses should have difficulty ≥ 3.0" in str(exc_info.value)
        
        # Test expert level validation
        expert_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.EXPERT,
            prerequisites=["PhD level knowledge"],
            learning_preferences=[LearningPreference.RESEARCH],
        )
        
        with pytest.raises(ValidationError) as exc_info:
            Course(
                target_audience=expert_audience,
                difficulty_score=3.5,  # Too low for expert
                **base_data
            )
        assert "Expert courses should have difficulty ≥ 4.0" in str(exc_info.value)
        
        # Valid expert course
        course = Course(
            target_audience=expert_audience,
            difficulty_score=4.8,
            **base_data
        )
        assert course.difficulty_score == 4.8
    
    def test_course_defaults(self):
        """Test Course model default values."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        minimal_data = {
            "id": uuid4(),
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        course = Course(**minimal_data)
        
        # Check defaults
        assert course.status == CourseStatus.DRAFT
        assert course.language == "en"
        assert course.version == "1.0.0"
        assert course.quality_metrics is None
        assert course.description is None


class TestCourseListResponse:
    """Test CourseListResponse for API list endpoints."""
    
    def test_course_list_response_structure(self):
        """Test CourseListResponse with multiple courses."""
        # Create sample courses
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        course_data = {
            "title": "Test Course",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": ["Learn basics", "Apply knowledge", "Master concepts"],
            "estimated_duration": "PT10H",
            "difficulty_score": 2.0,
        }
        
        courses = []
        for i in range(3):
            course = Course(
                id=uuid4(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                **course_data
            )
            courses.append(course)
        
        response = CourseListResponse(
            courses=courses,
            total_count=10,
            limit=3,
            offset=0,
        )
        
        assert len(response.courses) == 3
        assert response.total_count == 10
        assert response.limit == 3
        assert response.offset == 0
        assert all(isinstance(course, Course) for course in response.courses)
    
    def test_empty_course_list(self):
        """Test CourseListResponse with empty course list."""
        response = CourseListResponse(
            courses=[],
            total_count=0,
            limit=10,
            offset=0,
        )
        
        assert len(response.courses) == 0
        assert response.total_count == 0
        assert response.limit == 10
        assert response.offset == 0


class TestCourseModelIntegration:
    """Integration tests for Course model business logic."""
    
    def test_course_lifecycle_transitions(self):
        """Test valid course status transitions."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.INTERMEDIATE,
            prerequisites=["Basic knowledge"],
            learning_preferences=[LearningPreference.PRACTICAL],
        )
        
        course_data = {
            "id": uuid4(),
            "title": "Software Engineering",
            "subject_domain": "Computer Science",
            "target_audience": target_audience,
            "learning_objectives": [
                "Design software systems",
                "Implement best practices",
                "Test and maintain code",
            ],
            "estimated_duration": "PT30H",
            "difficulty_score": 3.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        # Test progression through statuses
        statuses = [
            CourseStatus.DRAFT,
            CourseStatus.UNDER_REVIEW,
            CourseStatus.PUBLISHED,
            CourseStatus.ARCHIVED,
        ]
        
        for status in statuses:
            course = Course(status=status, **course_data)
            assert course.status == status
    
    def test_course_quality_metrics_integration(self):
        """Test Course with QualityMetrics integration."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.ADVANCED,
            prerequisites=["Strong foundation"],
            learning_preferences=[LearningPreference.THEORETICAL],
        )
        
        # High quality metrics
        high_quality = QualityMetrics(
            readability_score=95.0,
            pedagogical_alignment=0.98,
            objective_coverage=1.0,
            content_accuracy=0.99,
            bias_detection_score=0.02,
            user_satisfaction_score=4.8,
            generation_timestamp=datetime.utcnow(),
        )
        
        course = Course(
            id=uuid4(),
            title="High Quality Course",
            subject_domain="Computer Science",
            target_audience=target_audience,
            learning_objectives=[
                "Master advanced concepts",
                "Apply theoretical knowledge",
                "Conduct original research",
            ],
            estimated_duration="PT50H",
            difficulty_score=4.5,
            status=CourseStatus.PUBLISHED,
            quality_metrics=high_quality,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        assert course.quality_metrics.readability_score == 95.0
        assert course.quality_metrics.pedagogical_alignment == 0.98
        assert course.quality_metrics.objective_coverage == 1.0
        assert course.status == CourseStatus.PUBLISHED
    
    def test_course_serialization(self):
        """Test Course model serialization for API responses."""
        target_audience = TargetAudience(
            proficiency_level=ProficiencyLevel.BEGINNER,
            prerequisites=[],
            learning_preferences=[LearningPreference.VISUAL],
        )
        
        course = Course(
            id=uuid4(),
            title="API Serialization Test",
            subject_domain="Computer Science",
            target_audience=target_audience,
            learning_objectives=[
                "Learn serialization",
                "Understand JSON",
                "Master API design",
            ],
            estimated_duration="PT15H",
            difficulty_score=2.0,
            status=CourseStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Test dict conversion
        course_dict = course.dict()
        assert "id" in course_dict
        assert "title" in course_dict
        assert "target_audience" in course_dict
        assert "learning_objectives" in course_dict
        assert "status" in course_dict
        assert "created_at" in course_dict
        assert "updated_at" in course_dict
        
        # Test JSON serialization
        course_json = course.json()
        assert isinstance(course_json, str)
        assert "API Serialization Test" in course_json