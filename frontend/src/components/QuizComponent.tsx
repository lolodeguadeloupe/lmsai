'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  CheckIcon,
  XMarkIcon,
  ClockIcon,
  QuestionMarkCircleIcon,
  LightBulbIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  FlagIcon,
  PlayIcon,
  PauseIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

interface QuizQuestion {
  id: string;
  type: 'multiple_choice' | 'true_false' | 'fill_blank' | 'short_answer';
  question: string;
  options?: string[];
  correctAnswers: string[];
  explanation: string;
  hints?: string[];
  points: number;
  difficulty: 'easy' | 'medium' | 'hard';
}

interface QuizAttempt {
  questionId: string;
  selectedAnswers: string[];
  isCorrect: boolean;
  timeSpent: number;
  hintsUsed: number;
}

interface QuizComponentProps {
  quizId: string;
  title: string;
  description?: string;
  questions: QuizQuestion[];
  timeLimit?: number; // in minutes
  passingScore: number; // percentage
  attemptsAllowed?: number;
  onComplete: (results: QuizResults) => void;
  onExit?: () => void;
}

interface QuizResults {
  score: number;
  percentage: number;
  timeSpent: number;
  attempts: QuizAttempt[];
  passed: boolean;
}

export default function QuizComponent({
  quizId,
  title,
  description,
  questions,
  timeLimit,
  passingScore,
  attemptsAllowed = 1,
  onComplete,
  onExit,
}: QuizComponentProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(
    timeLimit ? timeLimit * 60 : null
  );
  const [quizStartTime] = useState(Date.now());
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [isStarted, setIsStarted] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [showHints, setShowHints] = useState<Record<string, number>>({});
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState<QuizResults | null>(null);
  const [flaggedQuestions, setFlaggedQuestions] = useState<Set<string>>(new Set());

  const currentQuestion = questions[currentQuestionIndex];

  // Timer effect
  useEffect(() => {
    if (!isStarted || isCompleted || timeRemaining === null) return;

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev === null) return null;
        if (prev <= 1) {
          handleQuizComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isStarted, isCompleted, timeRemaining]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const startQuiz = () => {
    setIsStarted(true);
    setQuestionStartTime(Date.now());
  };

  const handleAnswerSelect = (questionId: string, answer: string) => {
    const question = questions.find(q => q.id === questionId);
    if (!question) return;

    setAnswers(prev => {
      const currentAnswers = prev[questionId] || [];
      
      if (question.type === 'multiple_choice' && question.correctAnswers.length > 1) {
        // Multiple selection
        const newAnswers = currentAnswers.includes(answer)
          ? currentAnswers.filter(a => a !== answer)
          : [...currentAnswers, answer];
        return { ...prev, [questionId]: newAnswers };
      } else {
        // Single selection
        return { ...prev, [questionId]: [answer] };
      }
    });
  };

  const handleTextAnswer = (questionId: string, text: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: [text] }));
  };

  const showHint = (questionId: string) => {
    setShowHints(prev => ({
      ...prev,
      [questionId]: (prev[questionId] || 0) + 1
    }));
  };

  const toggleFlag = (questionId: string) => {
    setFlaggedQuestions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const goToQuestion = (index: number) => {
    if (index >= 0 && index < questions.length) {
      recordQuestionTime();
      setCurrentQuestionIndex(index);
      setQuestionStartTime(Date.now());
    }
  };

  const recordQuestionTime = () => {
    const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);
    const questionId = currentQuestion.id;
    const selectedAnswers = answers[questionId] || [];
    const isCorrect = checkAnswer(currentQuestion, selectedAnswers);
    const hintsUsed = showHints[questionId] || 0;

    setAttempts(prev => {
      const existing = prev.find(a => a.questionId === questionId);
      const attempt: QuizAttempt = {
        questionId,
        selectedAnswers,
        isCorrect,
        timeSpent,
        hintsUsed,
      };

      return existing 
        ? prev.map(a => a.questionId === questionId ? attempt : a)
        : [...prev, attempt];
    });
  };

  const checkAnswer = (question: QuizQuestion, selectedAnswers: string[]): boolean => {
    if (question.type === 'true_false' || question.type === 'multiple_choice') {
      return question.correctAnswers.length === selectedAnswers.length &&
             question.correctAnswers.every(answer => selectedAnswers.includes(answer));
    } else if (question.type === 'short_answer' || question.type === 'fill_blank') {
      return selectedAnswers.some(answer => 
        question.correctAnswers.some(correct => 
          answer.toLowerCase().trim() === correct.toLowerCase().trim()
        )
      );
    }
    return false;
  };

  const handleQuizComplete = useCallback(() => {
    if (isCompleted) return;

    recordQuestionTime();
    
    const totalTimeSpent = Math.floor((Date.now() - quizStartTime) / 1000);
    const finalAttempts = [...attempts];
    
    // Add current question if not already recorded
    const currentQuestionId = currentQuestion.id;
    if (!finalAttempts.find(a => a.questionId === currentQuestionId)) {
      const selectedAnswers = answers[currentQuestionId] || [];
      const isCorrect = checkAnswer(currentQuestion, selectedAnswers);
      const hintsUsed = showHints[currentQuestionId] || 0;
      
      finalAttempts.push({
        questionId: currentQuestionId,
        selectedAnswers,
        isCorrect,
        timeSpent: Math.floor((Date.now() - questionStartTime) / 1000),
        hintsUsed,
      });
    }

    const correctAnswers = finalAttempts.filter(a => a.isCorrect).length;
    const totalPoints = questions.reduce((sum, q) => sum + q.points, 0);
    const earnedPoints = finalAttempts
      .filter(a => a.isCorrect)
      .reduce((sum, a) => {
        const question = questions.find(q => q.id === a.questionId);
        return sum + (question?.points || 0);
      }, 0);
    
    const percentage = (earnedPoints / totalPoints) * 100;
    const passed = percentage >= passingScore;

    const quizResults: QuizResults = {
      score: earnedPoints,
      percentage,
      timeSpent: totalTimeSpent,
      attempts: finalAttempts,
      passed,
    };

    setResults(quizResults);
    setIsCompleted(true);
    setShowResults(true);
    onComplete(quizResults);
  }, [attempts, answers, currentQuestion, quizStartTime, questionStartTime, showHints, questions, passingScore, onComplete, isCompleted]);

  if (!isStarted) {
    return (
      <Card className="p-8 max-w-2xl mx-auto">
        <div className="text-center">
          <QuestionMarkCircleIcon className="w-16 h-16 text-blue-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>
          {description && (
            <p className="text-gray-600 mb-6">{description}</p>
          )}
          
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-900">Questions: </span>
                <span className="text-gray-600">{questions.length}</span>
              </div>
              <div>
                <span className="font-medium text-gray-900">Note minimale: </span>
                <span className="text-gray-600">{passingScore}%</span>
              </div>
              {timeLimit && (
                <div>
                  <span className="font-medium text-gray-900">Temps limite: </span>
                  <span className="text-gray-600">{timeLimit} minutes</span>
                </div>
              )}
              <div>
                <span className="font-medium text-gray-900">Tentatives: </span>
                <span className="text-gray-600">
                  {attemptsAllowed === 1 ? '1 seule' : `${attemptsAllowed} maximum`}
                </span>
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            {onExit && (
              <Button variant="outline" onClick={onExit}>
                Retour
              </Button>
            )}
            <Button onClick={startQuiz} className="bg-blue-600 hover:bg-blue-700">
              <PlayIcon className="w-4 h-4 mr-2" />
              Commencer le quiz
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  if (showResults && results) {
    return (
      <Card className="p-8 max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <div className={`w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center ${
            results.passed ? 'bg-green-100' : 'bg-red-100'
          }`}>
            {results.passed ? (
              <CheckCircleIcon className="w-12 h-12 text-green-600" />
            ) : (
              <ExclamationTriangleIcon className="w-12 h-12 text-red-600" />
            )}
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {results.passed ? 'Quiz réussi !' : 'Quiz non réussi'}
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">{results.score}</div>
              <div className="text-sm text-gray-600">Points obtenus</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">{Math.round(results.percentage)}%</div>
              <div className="text-sm text-gray-600">Score</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">{formatTime(results.timeSpent)}</div>
              <div className="text-sm text-gray-600">Temps passé</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {results.attempts.filter(a => a.isCorrect).length}/{questions.length}
              </div>
              <div className="text-sm text-gray-600">Bonnes réponses</div>
            </div>
          </div>
        </div>

        <div className="space-y-4 mb-8">
          <h3 className="text-lg font-semibold">Détail des réponses</h3>
          {questions.map((question, index) => {
            const attempt = results.attempts.find(a => a.questionId === question.id);
            return (
              <Card key={question.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-gray-900">
                    {index + 1}. {question.question}
                  </h4>
                  <div className={`px-2 py-1 rounded text-sm ${
                    attempt?.isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {attempt?.isCorrect ? 'Correct' : 'Incorrect'}
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 mb-2">
                  Votre réponse: {attempt?.selectedAnswers.join(', ') || 'Aucune réponse'}
                </div>
                
                <div className="text-sm text-green-700">
                  Bonne(s) réponse(s): {question.correctAnswers.join(', ')}
                </div>
                
                {question.explanation && (
                  <div className="mt-2 p-3 bg-blue-50 rounded text-sm text-blue-800">
                    <strong>Explication:</strong> {question.explanation}
                  </div>
                )}
              </Card>
            );
          })}
        </div>

        <div className="flex justify-center space-x-4">
          {!results.passed && attemptsAllowed > 1 && (
            <Button onClick={() => window.location.reload()}>
              Recommencer
            </Button>
          )}
          {onExit && (
            <Button variant="outline" onClick={onExit}>
              Retour au cours
            </Button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Quiz Header */}
      <Card className="p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <p className="text-sm text-gray-600">
              Question {currentQuestionIndex + 1} sur {questions.length}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {timeRemaining !== null && (
              <div className="flex items-center text-sm">
                <ClockIcon className="w-4 h-4 mr-1 text-gray-500" />
                <span className={timeRemaining < 300 ? 'text-red-600 font-bold' : 'text-gray-700'}>
                  {formatTime(timeRemaining)}
                </span>
              </div>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleFlag(currentQuestion.id)}
              className={flaggedQuestions.has(currentQuestion.id) ? 'text-orange-600' : ''}
            >
              <FlagIcon className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>
      </Card>

      {/* Question */}
      <Card className="p-6 mb-6">
        <div className="flex items-start justify-between mb-6">
          <h3 className="text-xl font-medium text-gray-900 flex-1">
            {currentQuestion.question}
          </h3>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            currentQuestion.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
            currentQuestion.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {currentQuestion.difficulty === 'easy' ? 'Facile' :
             currentQuestion.difficulty === 'medium' ? 'Moyen' : 'Difficile'}
          </span>
        </div>

        <QuestionContent
          question={currentQuestion}
          selectedAnswers={answers[currentQuestion.id] || []}
          onAnswerSelect={handleAnswerSelect}
          onTextAnswer={handleTextAnswer}
        />

        {/* Hints */}
        {currentQuestion.hints && currentQuestion.hints.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-700">Indices disponibles</span>
              {(showHints[currentQuestion.id] || 0) < currentQuestion.hints.length && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => showHint(currentQuestion.id)}
                >
                  <LightBulbIcon className="w-4 h-4 mr-2" />
                  Afficher un indice
                </Button>
              )}
            </div>
            
            {Array.from({ length: showHints[currentQuestion.id] || 0 }, (_, i) => (
              <div key={i} className="mb-2 p-3 bg-yellow-50 border border-yellow-200 rounded">
                <div className="flex items-start">
                  <LightBulbIcon className="w-4 h-4 text-yellow-600 mr-2 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-yellow-800">{currentQuestion.hints![i]}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Navigation */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => goToQuestion(currentQuestionIndex - 1)}
            disabled={currentQuestionIndex === 0}
          >
            <ArrowLeftIcon className="w-4 h-4 mr-2" />
            Précédent
          </Button>

          <div className="flex space-x-2">
            {questions.map((_, index) => (
              <button
                key={index}
                onClick={() => goToQuestion(index)}
                className={`w-8 h-8 rounded text-sm font-medium transition-colors ${
                  index === currentQuestionIndex
                    ? 'bg-blue-600 text-white'
                    : answers[questions[index].id]
                      ? 'bg-green-100 text-green-800'
                      : flaggedQuestions.has(questions[index].id)
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>

          {currentQuestionIndex === questions.length - 1 ? (
            <Button onClick={handleQuizComplete} className="bg-green-600 hover:bg-green-700">
              Terminer le quiz
            </Button>
          ) : (
            <Button onClick={() => goToQuestion(currentQuestionIndex + 1)}>
              Suivant
              <ArrowRightIcon className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

// Question Content Component
interface QuestionContentProps {
  question: QuizQuestion;
  selectedAnswers: string[];
  onAnswerSelect: (questionId: string, answer: string) => void;
  onTextAnswer: (questionId: string, text: string) => void;
}

function QuestionContent({ question, selectedAnswers, onAnswerSelect, onTextAnswer }: QuestionContentProps) {
  if (question.type === 'multiple_choice') {
    const isMultiSelect = question.correctAnswers.length > 1;
    
    return (
      <div className="space-y-3">
        {isMultiSelect && (
          <p className="text-sm text-blue-600 mb-4">
            ℹ️ Plusieurs réponses possibles
          </p>
        )}
        {question.options?.map((option, index) => (
          <label
            key={index}
            className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedAnswers.includes(option)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input
              type={isMultiSelect ? 'checkbox' : 'radio'}
              name={`question-${question.id}`}
              value={option}
              checked={selectedAnswers.includes(option)}
              onChange={() => onAnswerSelect(question.id, option)}
              className="mr-3"
            />
            <span className="text-gray-900">{option}</span>
          </label>
        ))}
      </div>
    );
  }

  if (question.type === 'true_false') {
    return (
      <div className="space-y-3">
        {['Vrai', 'Faux'].map((option) => (
          <label
            key={option}
            className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedAnswers.includes(option)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input
              type="radio"
              name={`question-${question.id}`}
              value={option}
              checked={selectedAnswers.includes(option)}
              onChange={() => onAnswerSelect(question.id, option)}
              className="mr-3"
            />
            <span className="text-gray-900">{option}</span>
          </label>
        ))}
      </div>
    );
  }

  if (question.type === 'short_answer' || question.type === 'fill_blank') {
    return (
      <div>
        <textarea
          rows={3}
          value={selectedAnswers[0] || ''}
          onChange={(e) => onTextAnswer(question.id, e.target.value)}
          placeholder="Tapez votre réponse ici..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
    );
  }

  return null;
}