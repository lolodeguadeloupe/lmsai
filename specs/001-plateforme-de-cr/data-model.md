# Data Model: Plateforme de Création de Cours IA

**Phase 1 Output** | **Date**: 2025-09-16 | **Feature**: 001-plateforme-de-cr

## Core Entities

### Course (Aggregate Root)
```python
class Course:
    id: UUID
    title: str                    # e.g., "Introduction to Machine Learning"
    description: str              # Course overview and objectives
    subject_domain: str           # e.g., "Computer Science", "Mathematics"
    target_audience: TargetAudience
    learning_objectives: List[str] # Specific, measurable objectives
    estimated_duration: timedelta # Total course time
    difficulty_score: float       # 1.0-5.0 scale
    language: str                 # ISO 639-1 code
    version: str                  # Semantic version (1.0.0)
    status: CourseStatus          # DRAFT, GENERATING, READY, PUBLISHED
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    chapters: List[Chapter]       # Ordered sequence
    final_assessment: Quiz       # Optional course-level assessment
    quality_metrics: QualityMetrics
```

### Chapter (Entity)
```python
class Chapter:
    id: UUID
    course_id: UUID              # Foreign key
    sequence_number: int         # 1, 2, 3...
    title: str                   # Chapter name
    learning_objectives: List[str] # Chapter-specific objectives
    estimated_duration: timedelta # Chapter completion time
    complexity_level: float      # 1.0-5.0 relative to course
    prerequisites: List[str]     # Concept dependencies
    content_outline: str         # High-level structure
    
    # Relationships
    subchapters: List[Subchapter] # Ordered content sections
    chapter_quiz: Quiz           # Chapter assessment
```

### Subchapter (Entity)
```python
class Subchapter:
    id: UUID
    chapter_id: UUID             # Foreign key
    sequence_number: int         # 1, 2, 3...
    title: str                   # Section name
    content_type: ContentType    # THEORY, PRACTICAL, MIXED
    content_blocks: List[ContentBlock] # Structured content
    key_concepts: List[str]      # Important terms/ideas
    examples: List[Example]      # Practical demonstrations
    summary: str                 # Section recap
    additional_resources: List[Resource] # External links, readings
```

### ContentBlock (Value Object)
```python
class ContentBlock:
    type: BlockType              # TEXT, IMAGE, VIDEO, CODE, DIAGRAM
    content: str                 # Main content
    metadata: Dict[str, Any]     # Type-specific properties
    order: int                   # Display sequence
```

### Quiz (Entity)
```python
class Quiz:
    id: UUID
    title: str
    type: QuizType               # CHAPTER, FINAL, PRACTICE
    questions: List[Question]    # Assessment items
    passing_score: float         # Minimum score (0.0-1.0)
    time_limit: Optional[timedelta] # Max completion time
    attempts_allowed: int        # Number of retries
    randomize_questions: bool    # Shuffle order
    randomize_answers: bool      # Shuffle multiple choice
```

### Question (Entity)
```python
class Question:
    id: UUID
    quiz_id: UUID               # Foreign key
    type: QuestionType          # MULTIPLE_CHOICE, TRUE_FALSE, FILL_BLANK, SHORT_ANSWER, PRACTICAL
    question_text: str          # Question prompt
    difficulty_level: DifficultyLevel # EASY, MEDIUM, HARD
    cognitive_level: CognitiveLevel # REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE
    correct_answers: List[str]  # Accepted answers
    incorrect_answers: List[str] # Distractors (multiple choice)
    explanation: str            # Answer explanation
    hints: List[str]           # Progressive hints
    points: int                # Score weight
```

### Flashcard (Entity)
```python
class Flashcard:
    id: UUID
    course_id: UUID             # Foreign key
    front_content: str          # Question/prompt side
    back_content: str           # Answer/explanation side
    difficulty_rating: float    # User-perceived difficulty
    importance_rating: float    # Pedagogical importance
    spaced_repetition_metadata: SpacedRepetitionData
    related_concepts: List[str] # Concept relationships
    tags: List[str]            # Classification tags
```

### TargetAudience (Value Object)
```python
class TargetAudience:
    proficiency_level: ProficiencyLevel # BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    prerequisites: List[str]     # Required prior knowledge
    age_range: Optional[AgeRange] # Target age group
    professional_context: Optional[str] # Industry/domain
    learning_preferences: List[LearningPreference] # VISUAL, AUDITORY, KINESTHETIC
```

### QualityMetrics (Value Object)
```python
class QualityMetrics:
    readability_score: float     # Flesch-Kincaid or similar
    pedagogical_alignment: float # Bloom's taxonomy compliance
    objective_coverage: float    # % of objectives covered
    content_accuracy: float      # Fact-checking score
    bias_detection_score: float  # Content bias assessment
    user_satisfaction_score: Optional[float] # Feedback rating
    generation_timestamp: datetime
```

## Enumerations

```python
class CourseStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ContentType(str, Enum):
    THEORY = "theory"
    PRACTICAL = "practical"
    MIXED = "mixed"

class BlockType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CODE = "code"
    DIAGRAM = "diagram"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    PRACTICAL = "practical"

class ProficiencyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class CognitiveLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"
```

## State Transitions

### Course Lifecycle
```
DRAFT → GENERATING → READY → PUBLISHED
  ↓         ↓         ↓
ARCHIVED ← ARCHIVED ← ARCHIVED
```

### Generation Process States
```
1. Course structure generation
2. Chapter content generation (parallel)
3. Assessment generation
4. Quality validation
5. Export preparation
6. Final review
```

## Validation Rules

### Course Level
- Title: 3-200 characters, no profanity
- Learning objectives: 3-12 items, SMART format
- Difficulty score: 1.0-5.0, must align with target audience
- Estimated duration: 30min-40hours based on proficiency level

### Chapter Level  
- Sequence numbers: Must be consecutive starting from 1
- Prerequisites: Must reference valid concepts from previous chapters
- Complexity level: Cannot exceed course difficulty + 0.5

### Content Quality
- Readability score: Must meet level-specific thresholds (FR-011)
- Objective coverage: Must achieve 100% coverage (FR-012)
- Cognitive distribution: Must follow level-appropriate percentages

### Assessment Rules
- Question distribution: Follow cognitive level requirements per audience
- Passing score: 60% minimum, 85% maximum
- Time limits: Appropriate for question count and complexity

---
*Data model complete - Ready for contract generation*