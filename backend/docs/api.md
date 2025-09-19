# Course Generation Platform API Reference

## Overview

The Course Generation Platform API provides AI-powered course creation and management capabilities. This RESTful API enables developers to create, manage, and export educational courses with automated content generation.

**Base URL**: `https://api.courseplatform.com/v1`  
**Development URL**: `http://localhost:8000/api/v1`

## Authentication

All API requests require authentication using API keys passed in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your-api-key-here" \
     -H "Content-Type: application/json" \
     https://api.courseplatform.com/v1/courses
```

## Rate Limiting

- **Default**: 100 requests per minute per API key
- **Burst limit**: 20 requests per 10 seconds
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Total requests allowed per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit window resets

## API Endpoints

### Courses

#### Create Course
Create a new course with AI-generated content.

```http
POST /courses
```

**Request Body:**
```json
{
  "title": "Introduction to Machine Learning",
  "description": "Comprehensive ML course for beginners",
  "subject_domain": "Computer Science",
  "target_audience": {
    "proficiency_level": "beginner",
    "prerequisites": ["Basic mathematics", "Python programming"],
    "age_range": {"min_age": 18, "max_age": 65},
    "professional_context": "Software development",
    "learning_preferences": ["visual", "practical"]
  },
  "estimated_duration": "PT20H",
  "content_preferences": {
    "include_practical_examples": true,
    "theory_to_practice_ratio": 0.6
  }
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating",
  "generation_task_id": "task-12345",
  "estimated_completion_time": "2025-09-19T18:30:00Z"
}
```

#### List Courses
Retrieve a list of courses with optional filtering.

```http
GET /courses?status=ready&limit=20&offset=0
```

**Query Parameters:**
- `status` (optional): Filter by course status (`draft`, `generating`, `ready`, `published`, `archived`)
- `subject_domain` (optional): Filter by subject domain
- `limit` (optional): Number of results (1-100, default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response (200 OK):**
```json
{
  "courses": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Introduction to Machine Learning",
      "description": "Comprehensive ML course for beginners",
      "subject_domain": "Computer Science",
      "status": "ready",
      "created_at": "2025-09-19T15:30:00Z",
      "estimated_duration": "PT20H",
      "difficulty_score": 2.5
    }
  ],
  "total_count": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Course Details
Retrieve detailed information about a specific course.

```http
GET /courses/{courseId}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Introduction to Machine Learning",
  "description": "Comprehensive ML course for beginners",
  "subject_domain": "Computer Science",
  "target_audience": {
    "proficiency_level": "beginner",
    "prerequisites": ["Basic mathematics", "Python programming"],
    "learning_preferences": ["visual", "practical"]
  },
  "learning_objectives": [
    "Understand fundamental ML concepts",
    "Implement basic ML algorithms",
    "Evaluate model performance"
  ],
  "estimated_duration": "PT20H",
  "difficulty_score": 2.5,
  "language": "en",
  "version": "1.0.0",
  "status": "ready",
  "created_at": "2025-09-19T15:30:00Z",
  "updated_at": "2025-09-19T16:15:00Z",
  "chapters": [
    {
      "id": "chapter-1",
      "sequence_number": 1,
      "title": "Introduction to ML",
      "estimated_duration": "PT4H"
    }
  ],
  "quality_metrics": {
    "readability_score": 78.5,
    "pedagogical_alignment": 0.92,
    "objective_coverage": 1.0
  }
}
```

#### Update Course
Update an existing course's metadata.

```http
PUT /courses/{courseId}
```

**Request Body:**
```json
{
  "title": "Advanced Machine Learning",
  "description": "Updated course description",
  "learning_objectives": [
    "Master advanced ML techniques",
    "Deploy ML models in production"
  ]
}
```

**Response (200 OK):** Returns updated course object.

#### Delete Course
Delete a course and all associated content.

```http
DELETE /courses/{courseId}
```

**Response (204 No Content):** Empty response body.

### Generation Status

#### Get Generation Status
Monitor the progress of course generation.

```http
GET /courses/{courseId}/generation-status
```

**Response (200 OK):**
```json
{
  "task_id": "task-12345",
  "status": "in_progress",
  "progress_percentage": 75.0,
  "current_phase": "content",
  "estimated_time_remaining": "PT2M",
  "error_message": null
}
```

**Generation Phases:**
- `structure`: Creating course outline and chapter structure
- `content`: Generating chapter content and materials
- `assessment`: Creating quizzes and assessments
- `validation`: Quality checking and validation
- `export`: Finalizing and preparing content

#### Regenerate Chapter
Regenerate content for a specific chapter.

```http
POST /courses/{courseId}/regenerate-chapter
```

**Request Body:**
```json
{
  "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
  "regeneration_reason": "Content too advanced for beginner level"
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "regen-task-456",
  "estimated_completion_time": "2025-09-19T17:00:00Z"
}
```

### Export

#### Export Course
Export a course in various formats for different LMS platforms.

```http
POST /courses/{courseId}/export
```

**Request Body:**
```json
{
  "format": "scorm2004",
  "include_assessments": true,
  "include_multimedia": true
}
```

**Supported Formats:**
- `scorm2004`: SCORM 2004 package
- `xapi`: Tin Can API/xAPI package
- `qti21`: QTI 2.1 assessment package
- `pdf`: PDF document
- `html`: HTML package

**Response (200 OK):**
```json
{
  "download_url": "https://api.courseplatform.com/downloads/course-export-123.zip",
  "expires_at": "2025-09-20T18:25:00Z",
  "file_size": 2457600,
  "checksum": "sha256:abcd1234ef567890..."
}
```

### Quality Metrics

#### Get Quality Metrics
Retrieve quality assessment metrics for a course.

```http
GET /courses/{courseId}/quality-metrics
```

**Response (200 OK):**
```json
{
  "readability_score": 78.5,
  "pedagogical_alignment": 0.92,
  "objective_coverage": 1.0,
  "content_accuracy": 0.95,
  "bias_detection_score": 0.03,
  "user_satisfaction_score": 4.2,
  "generation_timestamp": "2025-09-19T16:15:00Z"
}
```

**Quality Metrics Explained:**
- `readability_score`: Flesch reading ease score (0-100, higher is better)
- `pedagogical_alignment`: How well content aligns with learning objectives (0-1)
- `objective_coverage`: Percentage of learning objectives covered (0-1)
- `content_accuracy`: Factual accuracy assessment (0-1)
- `bias_detection_score`: Potential bias detected (0-1, lower is better)
- `user_satisfaction_score`: Average user rating (1-5)

### Chapters

#### Get Chapter Details
Retrieve detailed information about a specific chapter.

```http
GET /chapters/{chapterId}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "course_id": "550e8400-e29b-41d4-a716-446655440000",
  "sequence_number": 1,
  "title": "Introduction to Machine Learning",
  "learning_objectives": [
    "Define machine learning and its applications",
    "Distinguish between supervised and unsupervised learning"
  ],
  "estimated_duration": "PT4H",
  "complexity_level": 2.0,
  "prerequisites": ["Basic programming knowledge"],
  "content_outline": "Chapter covers ML fundamentals...",
  "subchapters": [
    {
      "id": "subchapter-1",
      "sequence_number": 1,
      "title": "What is Machine Learning?",
      "content_type": "theory",
      "key_concepts": ["Definition", "Applications", "Types"]
    }
  ],
  "chapter_quiz": {
    "id": "quiz-1",
    "title": "Chapter 1 Quiz",
    "questions_count": 5
  }
}
```

### Assessments

#### Get Quiz Details
Retrieve detailed information about a quiz or assessment.

```http
GET /quizzes/{quizId}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "title": "Chapter 1: Introduction to ML Quiz",
  "type": "chapter",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question_text": "What is machine learning?",
      "difficulty_level": "easy",
      "cognitive_level": "remember",
      "correct_answers": ["A method for computers to learn from data"],
      "incorrect_answers": [
        "A type of computer hardware",
        "A programming language",
        "A database system"
      ],
      "explanation": "Machine learning is a method...",
      "points": 1
    }
  ],
  "passing_score": 0.7,
  "time_limit": "PT15M",
  "attempts_allowed": 3,
  "randomize_questions": false,
  "randomize_answers": true
}
```

## Response Codes

### Success Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for processing
- `204 No Content`: Request successful, no response body

### Error Codes
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate title)
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: Upstream service error
- `503 Service Unavailable`: Service temporarily unavailable

## Error Response Format

All error responses follow a consistent format:

```json
{
  "error": "ValidationError",
  "message": "Invalid request parameters",
  "details": {
    "field": "title",
    "issue": "Title must be between 3 and 200 characters"
  },
  "timestamp": "2025-09-19T16:30:00Z"
}
```

## Data Types and Enums

### Course Status
- `draft`: Course is being edited
- `generating`: AI is generating content
- `ready`: Course is complete and ready
- `published`: Course is live and accessible
- `archived`: Course is archived

### Target Audience Proficiency Levels
- `beginner`: New to the subject
- `intermediate`: Some experience
- `advanced`: Significant experience
- `expert`: Deep expertise

### Content Types
- `theory`: Theoretical content
- `practical`: Hands-on exercises
- `mixed`: Combination of theory and practice

### Question Types
- `multiple_choice`: Multiple choice questions
- `true_false`: True/false questions
- `fill_blank`: Fill in the blank
- `short_answer`: Short text responses
- `practical`: Hands-on exercises

### Cognitive Levels (Bloom's Taxonomy)
- `remember`: Recall information
- `understand`: Explain concepts
- `apply`: Use knowledge in new situations
- `analyze`: Break down information
- `evaluate`: Make judgments
- `create`: Produce original work

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```http
GET /courses?limit=10&offset=20
```

Response includes pagination metadata:
```json
{
  "courses": [...],
  "total_count": 150,
  "limit": 10,
  "offset": 20
}
```

## Versioning

The API uses URL versioning. Current version is `v1`. Future versions will be available as `v2`, `v3`, etc.

```
https://api.courseplatform.com/v1/courses
https://api.courseplatform.com/v2/courses  (future)
```

## SDKs and Libraries

Official SDKs are available for:
- **Python**: `pip install courseplatform-sdk`
- **JavaScript/Node.js**: `npm install courseplatform-sdk`
- **PHP**: `composer require courseplatform/sdk`

Community SDKs:
- **Java**: Available on Maven Central
- **C#**: Available on NuGet
- **Go**: Available on GitHub

## Support

- **Documentation**: https://docs.courseplatform.com
- **API Status**: https://status.courseplatform.com
- **Support**: support@courseplatform.com
- **GitHub**: https://github.com/courseplatform/api