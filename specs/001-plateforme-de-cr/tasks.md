# Tasks: Plateforme de Création de Cours IA

**Input**: Design documents from `/home/laurent/mesprojets/lms/creationcours/specs/001-plateforme-de-cr/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/api.yaml ✓, quickstart.md ✓

## 📊 CURRENT PROGRESS STATUS (2025-09-18 Updated)

**✅ COMPLETED**: 56/67 tasks (84% complete)
- **Phase 3.1** Setup: T001-T006 ✓ DONE
- **Phase 3.2** Tests: T007-T022 ✓ DONE (All contract & integration tests written)
- **Phase 3.3** Models: T023-T033 ✓ DONE (Entity models & database layer)
- **Phase 3.4** Business Logic: T034-T040 ✓ DONE (All services & integrations implemented)
- **Phase 3.5** API Endpoints: T041-T051 ✓ DONE (All FastAPI endpoints implemented)
- **Phase 3.6** Infrastructure: T052-T056 ✓ DONE (Middleware & security layer complete)

**🚧 NEXT PRIORITY**: Phase 3.7 CLI Tools & Utilities (T057-T059)
- 3 CLI tool tasks that can run in parallel
- Database management, AI testing, course management
- **Target**: Complete CLI tooling next

**⏳ REMAINING**: 11 tasks (16%)
- Phase 3.7: CLI Tools (3 tasks) - NEXT UP
- Phase 3.8: Polish & Testing (8 tasks)

## 🎯 IMMEDIATE ACTION PLAN

**START NOW - Phase 3.7 CLI Tools & Utilities (T057-T059)**:
```bash
# Launch T057-T059 together (CLI tools - all can run in parallel):
Task: "Database CLI commands (init, seed, migrate) in backend/src/cli/db.py"
Task: "AI service testing CLI in backend/src/cli/ai.py"
Task: "Course management CLI in backend/src/cli/courses.py"
```

**RECOMMENDED ORDER**:
1. Implement all 3 CLI tools in parallel (T057-T059)
2. Test CLI integration with existing services
3. Move to final polish phase (T060-T067)

**INFRASTRUCTURE COMPLETED ✅**:
- ✅ T052: Request/response logging middleware
- ✅ T053: CORS and security headers middleware  
- ✅ T054: Rate limiting middleware
- ✅ T055: Error handling and exception mapping
- ✅ T056: API key authentication

## Execution Flow (Generated)
```
1. ✓ Loaded plan.md - Web application (backend + frontend), Python 3.11+, FastAPI
2. ✓ Loaded data model - 7 core entities, 6 enums, state transitions
3. ✓ Loaded contracts - 11 API endpoints across 4 resource groups
4. ✓ Loaded quickstart - Primary user story and 5 test scenarios
5. ✓ Generated 67 tasks across 5 phases with TDD approach
6. ✓ Applied parallelization rules - 31 [P] tasks, dependency ordering
7. ✓ Validated completeness - All contracts, entities, and stories covered
8. ✓ Updated with current implementation status (33/67 complete)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths for each task

## Path Conventions
**Web application structure** (from plan.md):
- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Infrastructure**: `docker-compose.yml` at repository root

## Phase 3.1: Setup (T001-T006)
- [x] **T001** Create project structure per implementation plan (backend/, frontend/, docker-compose.yml)
- [x] **T002** Initialize Python backend with FastAPI, Pydantic, pytest dependencies in backend/requirements.txt
- [x] **T003** [P] Configure pre-commit hooks and linting tools in backend/.pre-commit-config.yaml
- [x] **T004** [P] Setup Docker services for PostgreSQL, Redis, Vector DB in docker-compose.yml
- [x] **T005** [P] Initialize database schema and migrations in backend/src/database/
- [x] **T006** [P] Configure environment variables and settings in backend/src/core/config.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [x] **T007** [P] Contract test POST /courses in backend/tests/contract/test_courses_post.py
- [x] **T008** [P] Contract test GET /courses in backend/tests/contract/test_courses_list.py
- [x] **T009** [P] Contract test GET /courses/{courseId} in backend/tests/contract/test_courses_get.py
- [x] **T010** [P] Contract test PUT /courses/{courseId} in backend/tests/contract/test_courses_update.py
- [x] **T011** [P] Contract test DELETE /courses/{courseId} in backend/tests/contract/test_courses_delete.py
- [x] **T012** [P] Contract test GET /courses/{courseId}/generation-status in backend/tests/contract/test_generation_status.py
- [x] **T013** [P] Contract test POST /courses/{courseId}/regenerate-chapter in backend/tests/contract/test_regenerate_chapter.py
- [x] **T014** [P] Contract test POST /courses/{courseId}/export in backend/tests/contract/test_export.py
- [x] **T015** [P] Contract test GET /courses/{courseId}/quality-metrics in backend/tests/contract/test_quality_metrics.py
- [x] **T016** [P] Contract test GET /chapters/{chapterId} in backend/tests/contract/test_chapters_get.py
- [x] **T017** [P] Contract test GET /quizzes/{quizId} in backend/tests/contract/test_quizzes_get.py

### Integration Tests (User Stories)
- [x] **T018** [P] Integration test course creation workflow in backend/tests/integration/test_course_creation.py
- [x] **T019** [P] Integration test generation monitoring in backend/tests/integration/test_generation_monitoring.py
- [x] **T020** [P] Integration test quality validation in backend/tests/integration/test_quality_validation.py
- [x] **T021** [P] Integration test export functionality in backend/tests/integration/test_export_functionality.py
- [x] **T022** [P] Integration test concurrent generation in backend/tests/integration/test_concurrent_generation.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Entity Models
- [x] **T023** [P] Course entity model in backend/src/models/course.py
- [x] **T024** [P] Chapter entity model in backend/src/models/chapter.py
- [x] **T025** [P] Subchapter entity model in backend/src/models/subchapter.py
- [x] **T026** [P] Quiz entity model in backend/src/models/quiz.py
- [x] **T027** [P] Question entity model in backend/src/models/question.py
- [x] **T028** [P] Flashcard entity model in backend/src/models/flashcard.py
- [x] **T029** [P] Value objects (TargetAudience, QualityMetrics, etc.) in backend/src/models/value_objects.py

### Database Layer
- [x] **T030** [P] Course repository pattern in backend/src/repositories/course_repository.py
- [x] **T031** [P] Chapter repository pattern in backend/src/repositories/chapter_repository.py
- [x] **T032** [P] Quiz repository pattern in backend/src/repositories/quiz_repository.py
- [x] **T033** Database session management and connection pooling in backend/src/database/session.py

## Phase 3.4: Business Logic (Services) ✅ COMPLETED

### Core Services
- [x] **T034** Course generation service with AI integration in backend/src/services/course_generation_service.py
- [x] **T035** Content quality validation service in backend/src/services/quality_validation_service.py
- [x] **T036** Export service for SCORM/xAPI formats in backend/src/services/export_service.py
- [x] **T037** Chapter regeneration service in backend/src/services/chapter_service.py

### External Integrations
- [x] **T038** [P] OpenAI/Anthropic AI client wrapper in backend/src/integrations/ai_client.py
- [x] **T039** [P] Vector database client (Pinecone/Chroma) in backend/src/integrations/vector_client.py
- [x] **T040** [P] Background task queue with Celery in backend/src/tasks/generation_tasks.py

## Phase 3.5: API Layer (Endpoints) ✅ COMPLETED

### Course Management Endpoints
- [x] **T041** POST /courses endpoint in backend/src/api/v1/courses.py
- [x] **T042** GET /courses (list) endpoint in backend/src/api/v1/courses.py
- [x] **T043** GET /courses/{courseId} endpoint in backend/src/api/v1/courses.py
- [x] **T044** PUT /courses/{courseId} endpoint in backend/src/api/v1/courses.py
- [x] **T045** DELETE /courses/{courseId} endpoint in backend/src/api/v1/courses.py

### Generation & Export Endpoints
- [x] **T046** GET /courses/{courseId}/generation-status endpoint in backend/src/api/v1/generation.py
- [x] **T047** POST /courses/{courseId}/regenerate-chapter endpoint in backend/src/api/v1/generation.py
- [x] **T048** POST /courses/{courseId}/export endpoint in backend/src/api/v1/export.py
- [x] **T049** GET /courses/{courseId}/quality-metrics endpoint in backend/src/api/v1/quality.py

### Chapter & Assessment Endpoints
- [x] **T050** GET /chapters/{chapterId} endpoint in backend/src/api/v1/chapters.py
- [x] **T051** GET /quizzes/{quizId} endpoint in backend/src/api/v1/quizzes.py

## Phase 3.6: Infrastructure & Middleware ✅ COMPLETED

- [x] **T052** Request/response logging middleware in backend/src/middleware/logging.py
- [x] **T053** CORS and security headers middleware in backend/src/middleware/security.py
- [x] **T054** Rate limiting middleware in backend/src/middleware/rate_limiting.py
- [x] **T055** Error handling and exception mapping in backend/src/core/exceptions.py
- [x] **T056** API key authentication in backend/src/auth/api_key_auth.py

## Phase 3.7: CLI Tools & Utilities ⚠️ CAN BE DONE IN PARALLEL

- [ ] **T057** [P] Database CLI commands (init, seed, migrate) in backend/src/cli/db.py
- [ ] **T058** [P] AI service testing CLI in backend/src/cli/ai.py
- [ ] **T059** [P] Course management CLI in backend/src/cli/courses.py

## Phase 3.8: Polish & Optimization ⚠️ FINAL PHASE

### Unit Tests
- [ ] **T060** [P] Unit tests for course models in backend/tests/unit/test_course_model.py
- [ ] **T061** [P] Unit tests for validation logic in backend/tests/unit/test_validation.py
- [ ] **T062** [P] Unit tests for AI service integration in backend/tests/unit/test_ai_service.py

### Performance & Documentation
- [ ] **T063** [P] Performance tests (<200ms API response) in backend/tests/performance/test_api_performance.py
- [ ] **T064** [P] Load testing for concurrent generation in backend/tests/performance/test_load.py
- [ ] **T065** [P] Update API documentation in backend/docs/api.md
- [ ] **T066** Code quality checks and remove duplication across backend/src/
- [ ] **T067** Execute quickstart.md validation scenarios

## Dependencies

### Critical Path Dependencies
```
Setup (T001-T006) → Tests (T007-T022) → Models (T023-T033) → Services (T034-T040) → Endpoints (T041-T051) → Infrastructure (T052-T056) → Polish (T060-T067)
```

### Blocking Dependencies
- T033 (DB session) blocks T030-T032 (repositories)
- T030-T032 (repositories) block T034-T037 (services)
- T034-T037 (services) block T041-T051 (endpoints)
- T038-T040 (integrations) must complete before T034 (generation service)
- T055 (error handling) must complete before T041-T051 (endpoints)
- All implementation (T023-T056) blocked by failing tests (T007-T022)

### Parallel Execution Groups

**Group 1: Contract Tests (After T006)**
```bash
# Launch T007-T017 together:
Task: "Contract test POST /courses in backend/tests/contract/test_courses_post.py"
Task: "Contract test GET /courses in backend/tests/contract/test_courses_list.py"
Task: "Contract test GET /courses/{courseId} in backend/tests/contract/test_courses_get.py"
Task: "Contract test PUT /courses/{courseId} in backend/tests/contract/test_courses_update.py"
Task: "Contract test DELETE /courses/{courseId} in backend/tests/contract/test_courses_delete.py"
Task: "Contract test GET /courses/{courseId}/generation-status in backend/tests/contract/test_generation_status.py"
Task: "Contract test POST /courses/{courseId}/regenerate-chapter in backend/tests/contract/test_regenerate_chapter.py"
Task: "Contract test POST /courses/{courseId}/export in backend/tests/contract/test_export.py"
Task: "Contract test GET /courses/{courseId}/quality-metrics in backend/tests/contract/test_quality_metrics.py"
Task: "Contract test GET /chapters/{chapterId} in backend/tests/contract/test_chapters_get.py"
Task: "Contract test GET /quizzes/{quizId} in backend/tests/contract/test_quizzes_get.py"
```

**Group 2: Integration Tests (After T017)**
```bash
# Launch T018-T022 together:
Task: "Integration test course creation workflow in backend/tests/integration/test_course_creation.py"
Task: "Integration test generation monitoring in backend/tests/integration/test_generation_monitoring.py"
Task: "Integration test quality validation in backend/tests/integration/test_quality_validation.py"
Task: "Integration test export functionality in backend/tests/integration/test_export_functionality.py"
Task: "Integration test concurrent generation in backend/tests/integration/test_concurrent_generation.py"
```

**Group 3: Entity Models (After T022)**
```bash
# Launch T023-T029 together:
Task: "Course entity model in backend/src/models/course.py"
Task: "Chapter entity model in backend/src/models/chapter.py"
Task: "Subchapter entity model in backend/src/models/subchapter.py"
Task: "Quiz entity model in backend/src/models/quiz.py"
Task: "Question entity model in backend/src/models/question.py"
Task: "Flashcard entity model in backend/src/models/flashcard.py"
Task: "Value objects (TargetAudience, QualityMetrics, etc.) in backend/src/models/value_objects.py"
```

**Group 4: External Integrations (After T033)**
```bash
# Launch T038-T040 together:
Task: "OpenAI/Anthropic AI client wrapper in backend/src/integrations/ai_client.py"
Task: "Vector database client (Pinecone/Chroma) in backend/src/integrations/vector_client.py"
Task: "Background task queue with Celery in backend/src/tasks/generation_tasks.py"
```

## Task Generation Rules Applied

1. **From Contracts (api.yaml)**:
   - 11 endpoints → 11 contract test tasks [P] (T007-T017)
   - 11 endpoints → 11 implementation tasks (T041-T051)
   
2. **From Data Model**:
   - 7 entities → 7 model creation tasks [P] (T023-T029)
   - Relationships → repository and service layer tasks (T030-T037)
   
3. **From User Stories (quickstart.md)**:
   - 5 test scenarios → 5 integration tests [P] (T018-T022)
   - Performance requirements → performance test tasks (T063-T064)

4. **Ordering Applied**:
   - Setup → Tests → Models → Services → Endpoints → Infrastructure → Polish
   - TDD: All tests (T007-T022) before implementation (T023+)
   - Dependencies prevent inappropriate parallelization

## Validation Checklist ✓

- [x] All 11 contracts have corresponding tests (T007-T017)
- [x] All 7 entities have model tasks (T023-T029)
- [x] All tests (T007-T022) come before implementation (T023+)
- [x] Parallel tasks [P] are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] Backend structure follows web app conventions from plan.md
- [x] Performance requirements (<2min generation, <200ms API) included
- [x] Export formats (SCORM, xAPI) covered
- [x] Quality validation and AI integration included
- [x] CLI tools for debugging and management included

## Notes
- [P] tasks = different files, no dependencies, can run in parallel
- Verify tests fail before implementing (critical for TDD)
- Commit after each task completion
- Use docker compose instead of docker-compose per user preferences
- Backend-first approach; frontend tasks can be added later if needed
- AI service integration requires API keys configuration
- Vector database choice (Pinecone vs Chroma) based on scale requirements from research.md

## Estimated Timeline
- **Phase 3.1**: 1-2 days (setup and infrastructure)
- **Phase 3.2**: 3-4 days (comprehensive test suite)
- **Phase 3.3**: 2-3 days (data models and repositories)
- **Phase 3.4**: 4-5 days (business logic and AI integration)
- **Phase 3.5**: 2-3 days (API endpoints)
- **Phase 3.6**: 1-2 days (middleware and infrastructure)
- **Phase 3.7**: 1 day (CLI tools)
- **Phase 3.8**: 2-3 days (testing, optimization, documentation)

**Total**: 16-23 days for full implementation

---
*Tasks generated successfully - Ready for execution*