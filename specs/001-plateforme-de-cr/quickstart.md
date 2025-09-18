# Quickstart Guide: Course Generation Platform

**Phase 1 Output** | **Date**: 2025-09-16 | **Feature**: 001-plateforme-de-cr

## Test Scenario Validation

This quickstart guide validates the primary user story from the feature specification through API integration tests.

### Prerequisites

- Python 3.11+ environment
- Docker and docker compose installed
- API server running on localhost:8000
- Test data seed files available

### Setup Instructions

```bash
# 1. Clone and setup environment
git clone <repository>
cd lms/creationcours
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Start infrastructure services
docker compose up -d postgres redis vector-db

# 3. Initialize database
python -m src.cli.db init-schema
python -m src.cli.db seed-test-data

# 4. Start API server
python -m src.main --port 8000

# 5. Verify services
curl http://localhost:8000/health
```

### Primary User Story Test

**Story**: An educator creates a comprehensive ML course for beginners

#### Step 1: Create Course Request
```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
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
      "include_practical_examples": true,
      "theory_to_practice_ratio": 0.6
    }
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating",
  "generation_task_id": "task-12345",
  "estimated_completion_time": "2025-09-16T18:30:00Z"
}
```

#### Step 2: Monitor Generation Progress
```bash
# Poll generation status every 30 seconds
curl http://localhost:8000/api/v1/courses/550e8400-e29b-41d4-a716-446655440000/generation-status \
  -H "X-API-Key: test-api-key"
```

**Expected Response Progression**:
```json
// Initial
{
  "task_id": "task-12345",
  "status": "in_progress",
  "progress_percentage": 25.0,
  "current_phase": "structure",
  "estimated_time_remaining": "PT5M"
}

// Mid-generation
{
  "task_id": "task-12345", 
  "status": "in_progress",
  "progress_percentage": 70.0,
  "current_phase": "content",
  "estimated_time_remaining": "PT2M"
}

// Completed
{
  "task_id": "task-12345",
  "status": "completed", 
  "progress_percentage": 100.0,
  "current_phase": "export",
  "estimated_time_remaining": "PT0S"
}
```

#### Step 3: Retrieve Generated Course
```bash
curl http://localhost:8000/api/v1/courses/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: test-api-key"
```

**Validation Criteria**:
- Course status: "ready"
- Chapters: 3-5 chapters (beginner level per FR-001)
- Learning objectives: Specific and measurable
- Content complexity: Appropriate vocabulary for beginners
- Assessment: Proper cognitive distribution (60% memory, 30% understanding, 10% application)

#### Step 4: Validate Quality Metrics
```bash
curl http://localhost:8000/api/v1/courses/550e8400-e29b-41d4-a716-446655440000/quality-metrics \
  -H "X-API-Key: test-api-key"
```

**Expected Thresholds**:
```json
{
  "readability_score": 75.0,        // ≥70 for beginner (FR-011)
  "pedagogical_alignment": 0.90,    // ≥0.8 expected
  "objective_coverage": 1.0,        // 100% required (FR-012)
  "content_accuracy": 0.95,         // ≥0.9 expected
  "bias_detection_score": 0.05,     // ≤0.1 acceptable
  "generation_timestamp": "2025-09-16T18:25:00Z"
}
```

#### Step 5: Test Export Functionality
```bash
curl -X POST http://localhost:8000/api/v1/courses/550e8400-e29b-41d4-a716-446655440000/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "format": "scorm2004",
    "include_assessments": true,
    "include_multimedia": true
  }'
```

**Expected Response**:
```json
{
  "download_url": "https://api.courseplatform.com/downloads/course-export-123.zip",
  "expires_at": "2025-09-17T18:25:00Z",
  "file_size": 2457600,
  "checksum": "sha256:abcd1234..."
}
```

### Integration Test Scenarios

#### Test Case 1: Performance Requirements
```bash
# Measure chapter generation time
time curl -X POST http://localhost:8000/api/v1/courses/550e8400-e29b-41d4-a716-446655440000/regenerate-chapter \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{"chapter_id": "chapter-1", "regeneration_reason": "Performance test"}'

# Validation: Must complete within 2 minutes (FR-020)
```

#### Test Case 2: Concurrent Generation
```bash
# Launch 5 concurrent course generations
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/courses \
    -H "Content-Type: application/json" \
    -H "X-API-Key: test-api-key" \
    -d "{\"title\": \"Test Course $i\", \"subject_domain\": \"Test\", \"target_audience\": {\"proficiency_level\": \"beginner\"}}" &
done

# Validation: All should succeed without timeout (FR-022)
```

#### Test Case 3: Content Regeneration
```bash
# Regenerate specific chapter that doesn't meet requirements
curl -X POST http://localhost:8000/api/v1/courses/550e8400-e29b-41d4-a716-446655440000/regenerate-chapter \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
    "regeneration_reason": "Content too advanced for beginner level"
  }'

# Validation: New content should improve quality metrics
```

### Error Handling Tests

#### Test Case 4: Invalid Request Handling
```bash
# Test invalid audience level
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "title": "Test Course",
    "subject_domain": "Test", 
    "target_audience": {
      "proficiency_level": "invalid_level"
    }
  }'

# Expected: 400 Bad Request with validation error
```

#### Test Case 5: Generation Failure Recovery
```bash
# Test system behavior during AI service failure
# (Requires mock failure scenario)
curl http://localhost:8000/api/v1/courses/failed-generation-id/generation-status

# Expected: Graceful error response with retry options
```

### Performance Benchmarks

#### API Response Times
- Course list: ≤200ms (95th percentile)
- Course creation: ≤500ms (request acceptance)
- Status check: ≤100ms
- Export initiation: ≤300ms

#### Generation Performance
- Chapter generation: ≤2 minutes per chapter
- Full course (5 chapters): ≤10 minutes
- Quality validation: ≤30 seconds
- Export preparation: ≤1 minute

### Success Criteria Checklist

- [ ] Course structure matches target level (3-5 chapters for beginner)
- [ ] Content vocabulary appropriate for audience level  
- [ ] All learning objectives covered in generated content
- [ ] Quality metrics meet specified thresholds
- [ ] Assessment questions follow cognitive distribution rules
- [ ] Export formats comply with SCORM/xAPI standards
- [ ] API response times within performance targets
- [ ] Generation completes within time constraints
- [ ] Error scenarios handled gracefully
- [ ] Concurrent operations supported

### Troubleshooting

#### Common Issues
1. **Generation timeout**: Check AI service availability and rate limits
2. **Quality metrics below threshold**: Review content generation parameters
3. **Export format errors**: Validate SCORM package structure
4. **Database connection errors**: Verify PostgreSQL service status
5. **Vector search failures**: Check vector database connectivity

#### Debug Commands
```bash
# Check service health
curl http://localhost:8000/health

# View generation logs
docker compose logs api-server | grep generation

# Database connectivity test
python -m src.cli.db test-connection

# AI service test
python -m src.cli.ai test-providers
```

---
*Quickstart guide complete - Ready for task generation phase*