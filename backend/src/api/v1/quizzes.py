from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from ...database.session import get_db
from ...models.quiz import Quiz
from ...models.chapter import Chapter
from ...models.enums import QuizType, DifficultyLevel, GenerationStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quizzes", tags=["quizzes"])

# Pydantic models for request/response
from pydantic import BaseModel, Field
from datetime import datetime

class QuestionOptionResponse(BaseModel):
    id: str
    text: str
    is_correct: Optional[bool] = None  # Only included for solutions
    explanation: Optional[str] = None
    
class QuestionResponse(BaseModel):
    id: UUID
    question_text: str
    question_type: str  # multiple_choice, true_false, short_answer, etc.
    difficulty_level: DifficultyLevel
    points: int
    options: List[QuestionOptionResponse]
    explanation: Optional[str]
    hints: List[str]
    
class QuizResponse(BaseModel):
    id: UUID
    chapter_id: UUID
    title: str
    description: str
    quiz_type: QuizType
    difficulty_level: DifficultyLevel
    estimated_duration_minutes: int
    total_points: int
    passing_score: int
    status: GenerationStatus
    created_at: datetime
    updated_at: datetime
    
    # Questions
    questions: List[QuestionResponse]
    
    # Configuration
    allow_multiple_attempts: bool
    shuffle_questions: bool
    show_correct_answers: bool
    time_limit_minutes: Optional[int]
    
    # Metadata
    learning_objectives: List[str]
    tags: List[str]
    
class QuizAttemptRequest(BaseModel):
    answers: Dict[str, Any]  # question_id -> answer
    time_spent_minutes: Optional[int]
    
class QuizAttemptResponse(BaseModel):
    attempt_id: UUID
    quiz_id: UUID
    score: float
    max_score: int
    percentage: float
    passed: bool
    time_spent_minutes: int
    submitted_at: datetime
    
    # Detailed feedback
    question_results: List[Dict[str, Any]]
    feedback: str
    improvement_suggestions: List[str]
    
class QuizSummaryResponse(BaseModel):
    id: UUID
    title: str
    quiz_type: QuizType
    difficulty_level: DifficultyLevel
    question_count: int
    estimated_duration_minutes: int
    total_points: int
    status: GenerationStatus
    
# T051: GET /quizzes/{quizId} endpoint
@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: UUID,
    include_solutions: bool = Query(False, description="Include correct answers and explanations"),
    shuffle_questions: bool = Query(False, description="Randomize question order"),
    db: Session = Depends(get_db)
) -> QuizResponse:
    """
    Get complete quiz content with questions and configuration.
    
    Returns:
    - Full quiz details with all questions
    - Question options (with or without correct answers)
    - Quiz configuration and metadata
    - Learning objectives and tags
    
    Parameters:
    - include_solutions: Whether to include correct answers (for review mode)
    - shuffle_questions: Whether to randomize question order (for taking quiz)
    """
    try:
        logger.info(f"Fetching quiz content for ID: {quiz_id}")
        
        # Get the quiz with all related data
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Check if quiz content is available
        if quiz.status == GenerationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quiz content is still being generated"
            )
        
        if quiz.status == GenerationStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quiz generation failed. Content may be incomplete."
            )
        
        # Get chapter for context
        chapter = db.query(Chapter).filter(Chapter.id == quiz.chapter_id).first()
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent chapter not found"
            )
        
        # Build questions response
        questions = quiz.questions or []
        
        # Shuffle questions if requested
        if shuffle_questions:
            import random
            questions = questions.copy()
            random.shuffle(questions)
        
        questions_response = []
        for question in questions:
            # Build options
            options_response = []
            for option in question.options:
                option_resp = QuestionOptionResponse(
                    id=option['id'],
                    text=option['text']
                )
                
                # Include correct answer and explanation only if requested
                if include_solutions:
                    option_resp.is_correct = option.get('is_correct', False)
                    option_resp.explanation = option.get('explanation')
                
                options_response.append(option_resp)
            
            question_resp = QuestionResponse(
                id=question.id,
                question_text=question.question_text,
                question_type=question.question_type,
                difficulty_level=question.difficulty_level,
                points=question.points,
                options=options_response,
                explanation=question.explanation if include_solutions else None,
                hints=question.hints or []
            )
            
            questions_response.append(question_resp)
        
        return QuizResponse(
            id=quiz.id,
            chapter_id=quiz.chapter_id,
            title=quiz.title,
            description=quiz.description,
            quiz_type=quiz.quiz_type,
            difficulty_level=quiz.difficulty_level,
            estimated_duration_minutes=quiz.estimated_duration_minutes,
            total_points=quiz.total_points,
            passing_score=quiz.passing_score,
            status=quiz.status,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
            questions=questions_response,
            allow_multiple_attempts=quiz.allow_multiple_attempts,
            shuffle_questions=quiz.shuffle_questions,
            show_correct_answers=quiz.show_correct_answers,
            time_limit_minutes=quiz.time_limit_minutes,
            learning_objectives=quiz.learning_objectives or [],
            tags=quiz.tags or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz {quiz_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz content"
        )

# Get quiz summary (lightweight version)
@router.get("/{quiz_id}/summary", response_model=QuizSummaryResponse)
async def get_quiz_summary(
    quiz_id: UUID,
    db: Session = Depends(get_db)
) -> QuizSummaryResponse:
    """
    Get a lightweight summary of quiz information.
    
    Useful for course navigation and quiz selection.
    Does not include full questions to improve performance.
    """
    try:
        logger.info(f"Fetching quiz summary for ID: {quiz_id}")
        
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Count questions
        question_count = len(quiz.questions) if quiz.questions else 0
        
        return QuizSummaryResponse(
            id=quiz.id,
            title=quiz.title,
            quiz_type=quiz.quiz_type,
            difficulty_level=quiz.difficulty_level,
            question_count=question_count,
            estimated_duration_minutes=quiz.estimated_duration_minutes,
            total_points=quiz.total_points,
            status=quiz.status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz summary {quiz_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz summary"
        )

# Submit quiz attempt
@router.post("/{quiz_id}/attempt", response_model=QuizAttemptResponse)
async def submit_quiz_attempt(
    quiz_id: UUID,
    request: QuizAttemptRequest,
    user_id: Optional[UUID] = Query(None, description="User ID for attempt tracking"),
    db: Session = Depends(get_db)
) -> QuizAttemptResponse:
    """
    Submit a quiz attempt and get results with feedback.
    
    This endpoint:
    1. Validates the submitted answers
    2. Calculates the score and feedback
    3. Stores the attempt (if user_id provided)
    4. Returns detailed results and improvement suggestions
    
    Note: Full user management will be implemented in future versions.
    """
    try:
        logger.info(f"Processing quiz attempt for quiz {quiz_id}")
        
        # Get the quiz
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        if quiz.status != GenerationStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quiz is not available for attempts"
            )
        
        # Validate answers format
        if not request.answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No answers provided"
            )
        
        # Calculate score and generate feedback
        from uuid import uuid4
        import uuid
        
        attempt_id = uuid4()
        total_score = 0
        max_score = quiz.total_points
        question_results = []
        
        questions = quiz.questions or []
        
        for question in questions:
            question_id = str(question.id)
            submitted_answer = request.answers.get(question_id)
            
            # Score the question
            is_correct = False
            points_earned = 0
            feedback = ""
            
            if submitted_answer is not None:
                # Simple scoring logic (this would be more sophisticated in production)
                correct_options = [opt for opt in question.options if opt.get('is_correct', False)]
                
                if question.question_type == 'multiple_choice':
                    correct_option_ids = [opt['id'] for opt in correct_options]
                    is_correct = submitted_answer in correct_option_ids
                    points_earned = question.points if is_correct else 0
                    
                elif question.question_type == 'true_false':
                    correct_answer = correct_options[0]['id'] if correct_options else None
                    is_correct = submitted_answer == correct_answer
                    points_earned = question.points if is_correct else 0
                
                # Generate feedback
                if is_correct:
                    feedback = "Correct! " + (question.explanation or "")
                else:
                    feedback = "Incorrect. " + (question.explanation or "")
                    if correct_options:
                        feedback += f" The correct answer is: {correct_options[0]['text']}"
            else:
                feedback = "No answer provided."
            
            total_score += points_earned
            
            question_results.append({
                "question_id": question_id,
                "submitted_answer": submitted_answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "max_points": question.points,
                "feedback": feedback
            })
        
        # Calculate percentage and pass/fail
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= quiz.passing_score
        
        # Generate overall feedback
        overall_feedback = f"You scored {total_score} out of {max_score} points ({percentage:.1f}%)."
        if passed:
            overall_feedback += " Congratulations, you passed!"
        else:
            overall_feedback += f" You need {quiz.passing_score}% to pass. Keep studying!"
        
        # Generate improvement suggestions
        improvement_suggestions = []
        incorrect_questions = [r for r in question_results if not r['is_correct']]
        
        if incorrect_questions:
            improvement_suggestions.append(f"Review the topics covered in {len(incorrect_questions)} questions you missed.")
            
        if percentage < 70:
            improvement_suggestions.append("Consider reviewing the chapter content before retaking the quiz.")
        elif percentage < 85:
            improvement_suggestions.append("You're doing well! Focus on the specific areas where you had difficulty.")
        
        # TODO: Store attempt in database when user management is implemented
        
        return QuizAttemptResponse(
            attempt_id=attempt_id,
            quiz_id=quiz_id,
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            passed=passed,
            time_spent_minutes=request.time_spent_minutes or 0,
            submitted_at=datetime.utcnow(),
            question_results=question_results,
            feedback=overall_feedback,
            improvement_suggestions=improvement_suggestions
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in quiz attempt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing quiz attempt {quiz_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process quiz attempt"
        )

# Get quiz statistics
@router.get("/{quiz_id}/statistics")
async def get_quiz_statistics(
    quiz_id: UUID,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get quiz statistics and analytics.
    
    Note: This is a placeholder for future analytics implementation.
    Currently returns basic quiz metadata.
    """
    try:
        logger.info(f"Fetching quiz statistics for ID: {quiz_id}")
        
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found"
            )
        
        # Basic quiz analytics (placeholder for future implementation)
        questions = quiz.questions or []
        
        difficulty_distribution = {}
        question_types = {}
        
        for question in questions:
            # Count by difficulty
            diff = question.difficulty_level.value if hasattr(question.difficulty_level, 'value') else str(question.difficulty_level)
            difficulty_distribution[diff] = difficulty_distribution.get(diff, 0) + 1
            
            # Count by type
            q_type = question.question_type
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        return {
            "quiz_id": quiz_id,
            "basic_stats": {
                "total_questions": len(questions),
                "total_points": quiz.total_points,
                "estimated_duration_minutes": quiz.estimated_duration_minutes,
                "passing_score": quiz.passing_score
            },
            "question_distribution": {
                "by_difficulty": difficulty_distribution,
                "by_type": question_types
            },
            "engagement_metrics": {
                "note": "User engagement metrics will be implemented with full user management",
                "total_attempts": 0,  # Placeholder
                "average_score": 0,   # Placeholder
                "completion_rate": 0  # Placeholder
            },
            "performance_analytics": {
                "note": "Performance analytics will be available with user attempt tracking",
                "difficult_questions": [],  # Placeholder
                "common_mistakes": [],     # Placeholder
                "time_analytics": {}       # Placeholder
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz statistics {quiz_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quiz statistics"
        )
