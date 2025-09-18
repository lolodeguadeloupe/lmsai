# Rapport d'Analyse des Exigences - Plateforme de Génération de Cours IA

**Date**: 2025-09-17  
**Projet**: Plateforme de Création de Cours IA  
**Branch**: 001-plateforme-de-cr  

## 1. ENTITÉS PRINCIPALES À IMPLÉMENTER

### Entités Core (Modèles de données)

#### Course (Aggregate Root)
- **Propriétés clés**:
  - id: UUID, title: str, description: str, subject_domain: str
  - target_audience: TargetAudience, learning_objectives: List[str]
  - estimated_duration: timedelta, difficulty_score: float (1.0-5.0)
  - status: CourseStatus, language: str, version: str
- **Relations**: chapters: List[Chapter], final_assessment: Quiz, quality_metrics: QualityMetrics
- **États**: DRAFT → GENERATING → READY → PUBLISHED → ARCHIVED

#### Chapter (Entity)
- **Propriétés clés**:
  - id: UUID, course_id: UUID, sequence_number: int, title: str
  - learning_objectives: List[str], estimated_duration: timedelta
  - complexity_level: float, prerequisites: List[str]
- **Relations**: subchapters: List[Subchapter], chapter_quiz: Quiz

#### Subchapter (Entity)
- **Propriétés clés**:
  - id: UUID, chapter_id: UUID, sequence_number: int, title: str
  - content_type: ContentType, content_blocks: List[ContentBlock]
  - key_concepts: List[str], examples: List[Example]

#### Quiz (Entity)
- **Propriétés clés**:
  - id: UUID, title: str, type: QuizType
  - questions: List[Question], passing_score: float
  - time_limit: Optional[timedelta], attempts_allowed: int

#### Question (Entity)
- **Propriétés clés**:
  - id: UUID, quiz_id: UUID, type: QuestionType
  - question_text: str, difficulty_level: DifficultyLevel
  - cognitive_level: CognitiveLevel, correct_answers: List[str]

#### Value Objects
- **TargetAudience**: proficiency_level, prerequisites, age_range, learning_preferences
- **QualityMetrics**: readability_score, pedagogical_alignment, objective_coverage
- **ContentBlock**: type, content, metadata, order

## 2. ENDPOINTS API À IMPLÉMENTER

### Groupe Courses (/courses)
1. **POST /courses** - Création de cours
   - Input: CourseCreationRequest
   - Output: 201 CourseCreationResponse (avec task_id)
   - Logique: Initie génération asynchrone

2. **GET /courses** - Liste des cours
   - Params: status, subject_domain, limit, offset
   - Output: 200 CourseListResponse
   - Fonctionnalités: Filtrage et pagination

3. **GET /courses/{courseId}** - Détails du cours
   - Output: 200 Course (avec chapters, final_assessment)
   - Errors: 404 Course not found

4. **PUT /courses/{courseId}** - Mise à jour cours
   - Input: CourseUpdateRequest
   - Output: 200 Course updated

5. **DELETE /courses/{courseId}** - Suppression cours
   - Output: 204 Course deleted

### Groupe Generation (/courses/{courseId}/)
6. **GET /generation-status** - Statut de génération
   - Output: 200 GenerationStatus (progress, current_phase, ETA)

7. **POST /regenerate-chapter** - Régénération chapitre
   - Input: RegenerateChapterRequest (chapter_id, reason)
   - Output: 202 GenerationTaskResponse

### Groupe Export (/courses/{courseId}/)
8. **POST /export** - Export de cours
   - Input: ExportRequest (format: scorm2004, xapi, qti21, pdf, html)
   - Output: 200 ExportResponse (download_url, expires_at)

### Groupe Quality (/courses/{courseId}/)
9. **GET /quality-metrics** - Métriques qualité
   - Output: 200 QualityMetrics (scores de qualité)

### Groupe Chapters & Assessments
10. **GET /chapters/{chapterId}** - Détails chapitre
11. **GET /quizzes/{quizId}** - Détails quiz

## 3. DÉPENDANCES TECHNIQUES REQUISES

### Stack Backend (Python 3.11+)
- **Framework**: FastAPI (REST API, validation automatique)
- **Validation**: Pydantic (modèles de données, sérialisation)
- **Base de données**: PostgreSQL (données relationnelles)
- **ORM**: SQLAlchemy ou tortoise-orm
- **Migrations**: Alembic

### IA et Contenu
- **Providers IA**: OpenAI SDK, Anthropic SDK
- **Vector DB**: Pinecone (prod) / Chroma (dev) pour embeddings
- **Qualité**: textstat (readability), spacy (NLP)

### Performance et Scaling
- **Cache**: Redis (sessions, cache génération)
- **Queue**: Celery avec Redis backend
- **Background tasks**: Celery workers
- **WebSockets**: FastAPI WebSocket (real-time status)

### Export et Conformité
- **SCORM**: py-scorm ou custom XML serialization
- **xAPI**: Tin Can API compatible
- **QTI**: Custom QTI 2.1 serialization
- **PDF**: ReportLab ou WeasyPrint

### Testing et Infrastructure
- **Tests**: pytest, httpx (API testing), factories
- **Conteneurisation**: Docker, docker compose
- **Monitoring**: Logging structuré, métriques

## 4. SCÉNARIOS DE TEST À AUTOMATISER

### Test Scenario Principal (Quickstart)
**US001**: Création cours ML pour débutants
- **Setup**: Services up, DB initialized, API running
- **Steps**:
  1. POST /courses (ML course for beginners)
  2. Poll GET /generation-status (until completed)
  3. GET /courses/{id} (validate structure)
  4. GET /quality-metrics (validate thresholds)
  5. POST /export (SCORM format test)

### Tests de Performance
- **Génération**: <2min par chapitre (FR-020)
- **API Response**: <200ms P95 pour lectures
- **Concurrence**: 100 générations simultanées
- **Success Rate**: 95% de taux de succès

### Tests d'Intégration
1. **Course Lifecycle**: DRAFT → GENERATING → READY → PUBLISHED
2. **Quality Validation**: Métriques dans les seuils requis
3. **Export Formats**: SCORM, xAPI, QTI, PDF, HTML
4. **Error Recovery**: Gestion échecs IA, timeouts
5. **Content Regeneration**: Amélioration qualité itérative

### Tests de Validation Métier
- **Content Quality**: Readability ≥70 pour débutants (FR-011)
- **Objective Coverage**: 100% couverture objectifs (FR-012)
- **Cognitive Distribution**: 60% memory, 30% understanding, 10% application
- **Assessment Rules**: Questions appropriées par niveau

## 5. ARCHITECTURE RECOMMANDÉE

### Structure Projet (Web Application)
```
backend/
├── src/
│   ├── models/          # Entités Pydantic + SQLAlchemy
│   ├── services/        # Business logic (generation, quality, export)
│   ├── api/             # FastAPI routers et endpoints
│   ├── repositories/    # Data access layer
│   ├── workers/         # Celery tasks (generation async)
│   ├── integrations/    # AI providers, vector DB, export
│   └── cli/             # Commands de setup/maintenance
└── tests/
    ├── contract/        # Tests API contracts (OpenAPI)
    ├── integration/     # Tests end-to-end scenarios
    └── unit/           # Tests unitaires services

frontend/
├── src/
│   ├── components/     # UI React/Vue components
│   ├── pages/          # Route pages
│   └── services/       # API clients
└── tests/
```

### Services Architecture
- **Generation Service**: Orchestration IA, workflow async
- **Quality Service**: Validation pédagogique, métriques
- **Export Service**: Multi-format serialization
- **Course Service**: CRUD operations, business rules
- **Repository Layer**: Data persistence abstraction

## 6. POINTS CRITIQUES POUR GÉNÉRATION TÂCHES

### Priorités TDD (Test-First)
1. **Contract Tests**: Un test par endpoint (doivent échouer initialement)
2. **Model Tests**: Validation rules, state transitions
3. **Integration Tests**: User stories end-to-end
4. **Service Tests**: Business logic units

### Dépendances d'Implémentation
1. **Base Models** → Services → API Endpoints
2. **Database Schema** → Repositories → Services
3. **AI Integration** → Generation Service → Workers
4. **Quality Metrics** → Validation Service → Content Pipeline

### Tasks Parallélisables [P]
- **Model Creation**: Tous les modèles independants
- **Repository Layer**: Un repository par entité
- **Contract Tests**: Un test par endpoint
- **Service Units**: Services sans dépendances croisées

### Contraintes de Performance
- **Generation Time**: <2min/chapitre - optimisation critique
- **API Latency**: <200ms P95 - indexation, caching
- **Concurrency**: 100 générations - scaling workers
- **Quality Gates**: Validation temps réel sans blocage UX

### Risques Techniques
- **AI Rate Limits**: Circuit breaker, fallback providers
- **Vector DB Scale**: Partition strategy, index optimization
- **Export Compliance**: SCORM/xAPI standard validation
- **Content Quality**: Pedagogical validation automatique

---

## RÉSUMÉ POUR GÉNÉRATION DE TÂCHES

**Entités Core**: 7 entités principales (Course, Chapter, Subchapter, Quiz, Question + Value Objects)  
**Endpoints API**: 11 endpoints principaux avec validation OpenAPI  
**Stack Technique**: FastAPI + PostgreSQL + Redis + Celery + AI Providers  
**Tests Critiques**: Generation workflow, quality validation, export formats  
**Architecture**: Web app backend/frontend avec services orientés domaine  

**Points d'Attention**:
- Génération asynchrone obligatoire (>2min processing)
- Validation qualité automatique avec métriques mesurables
- Export multi-format avec conformité standards
- Performance critique sur generation time et API response
- TDD strict avec contract tests failing initialement

**Estimation**: 25-30 tâches ordonnées avec marqueurs [P] pour parallélisation