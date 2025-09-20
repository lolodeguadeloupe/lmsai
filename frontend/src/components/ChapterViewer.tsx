'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  PlayIcon,
  PauseIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  BookOpenIcon,
  ClockIcon,
  CheckCircleIcon,
  QuestionMarkCircleIcon,
  DocumentTextIcon,
  AcademicCapIcon,
} from '@heroicons/react/24/outline';
import { Chapter } from '@/lib/api';

interface ChapterViewerProps {
  chapters: Chapter[];
  currentChapterIndex: number;
  onChapterChange: (index: number) => void;
  onComplete?: (chapterId: string) => void;
  isPreviewMode?: boolean;
}

export default function ChapterViewer({ 
  chapters, 
  currentChapterIndex, 
  onChapterChange, 
  onComplete,
  isPreviewMode = false 
}: ChapterViewerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [completedSections, setCompletedSections] = useState<Set<string>>(new Set());
  const [showQuiz, setShowQuiz] = useState(false);

  const currentChapter = chapters[currentChapterIndex];

  const handlePrevious = useCallback(() => {
    if (currentChapterIndex > 0) {
      onChapterChange(currentChapterIndex - 1);
      setShowQuiz(false);
    }
  }, [currentChapterIndex, onChapterChange]);

  const handleNext = useCallback(() => {
    if (currentChapterIndex < chapters.length - 1) {
      onChapterChange(currentChapterIndex + 1);
      setShowQuiz(false);
    }
  }, [currentChapterIndex, chapters.length, onChapterChange]);

  const togglePlayPause = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const markSectionComplete = useCallback((sectionId: string) => {
    setCompletedSections(prev => new Set([...prev, sectionId]));
  }, []);

  const markChapterComplete = useCallback(() => {
    if (onComplete && currentChapter) {
      onComplete(currentChapter.id);
    }
  }, [onComplete, currentChapter]);

  if (!currentChapter) {
    return (
      <Card className="p-8 text-center">
        <BookOpenIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun chapitre sélectionné</h3>
        <p className="text-gray-600">Sélectionnez un chapitre pour commencer la lecture.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Chapter Header */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="flex-shrink-0 w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-medium">
              {currentChapterIndex + 1}
            </span>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{currentChapter.title}</h1>
              <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                <span className="flex items-center">
                  <ClockIcon className="w-4 h-4 mr-1" />
                  {currentChapter.duration} min
                </span>
                <span className="flex items-center">
                  <DocumentTextIcon className="w-4 h-4 mr-1" />
                  {currentChapter.lessons?.length || 0} leçons
                </span>
                {currentChapter.quiz && (
                  <span className="flex items-center">
                    <QuestionMarkCircleIcon className="w-4 h-4 mr-1" />
                    Quiz inclus
                  </span>
                )}
              </div>
            </div>
          </div>

          {!isPreviewMode && (
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={togglePlayPause}
                className="flex items-center"
              >
                {isPlaying ? (
                  <PauseIcon className="w-4 h-4 mr-2" />
                ) : (
                  <PlayIcon className="w-4 h-4 mr-2" />
                )}
                {isPlaying ? 'Pause' : 'Lire'}
              </Button>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progression du chapitre</span>
            <span>{Math.round((completedSections.size / (currentChapter.lessons?.length || 1)) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ 
                width: `${(completedSections.size / (currentChapter.lessons?.length || 1)) * 100}%` 
              }}
            />
          </div>
        </div>

        {/* Chapter Objectives */}
        {currentChapter.objectives && currentChapter.objectives.length > 0 && (
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3 flex items-center">
              <AcademicCapIcon className="w-5 h-5 mr-2 text-blue-600" />
              Objectifs d'apprentissage
            </h3>
            <ul className="space-y-2">
              {currentChapter.objectives.map((objective, index) => (
                <li key={index} className="flex items-start space-x-3">
                  <CheckCircleIcon className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{objective}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>

      {/* Chapter Content */}
      <Card className="p-6">
        <div className="prose prose-lg max-w-none">
          {currentChapter.content ? (
            <div dangerouslySetInnerHTML={{ __html: currentChapter.content }} />
          ) : (
            <div className="text-center py-8">
              <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">Contenu en cours de chargement...</p>
            </div>
          )}
        </div>
      </Card>

      {/* Lessons */}
      {currentChapter.lessons && currentChapter.lessons.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Leçons du chapitre</h3>
          <div className="space-y-3">
            {currentChapter.lessons
              .sort((a, b) => a.order - b.order)
              .map((lesson, index) => (
              <div 
                key={lesson.id}
                className={`p-4 border rounded-lg transition-colors ${
                  completedSections.has(lesson.id) 
                    ? 'bg-green-50 border-green-200' 
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      completedSections.has(lesson.id)
                        ? 'bg-green-100 text-green-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {completedSections.has(lesson.id) ? (
                        <CheckCircleIcon className="w-5 h-5" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{lesson.title}</h4>
                      {lesson.description && (
                        <p className="text-sm text-gray-600">{lesson.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-500 flex items-center">
                      <ClockIcon className="w-4 h-4 mr-1" />
                      {lesson.duration} min
                    </span>
                    {!completedSections.has(lesson.id) && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => markSectionComplete(lesson.id)}
                      >
                        Marquer comme terminé
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Chapter Quiz */}
      {currentChapter.quiz && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center">
              <QuestionMarkCircleIcon className="w-6 h-6 mr-2 text-blue-600" />
              Quiz du chapitre
            </h3>
            <Button
              onClick={() => setShowQuiz(!showQuiz)}
              variant={showQuiz ? "secondary" : "default"}
            >
              {showQuiz ? 'Masquer le quiz' : 'Commencer le quiz'}
            </Button>
          </div>

          {showQuiz ? (
            <div className="bg-blue-50 p-6 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">{currentChapter.quiz.title}</h4>
              <div className="grid grid-cols-2 gap-4 text-sm text-blue-800 mb-4">
                <div>Questions: {currentChapter.quiz.questions?.length || 0}</div>
                <div>Note minimale: {currentChapter.quiz.passingScore}%</div>
                <div>Temps limite: {currentChapter.quiz.timeLimit || 'Illimité'}</div>
                <div>Tentatives: {currentChapter.quiz.attemptsAllowed || 'Illimitées'}</div>
              </div>
              <Button className="w-full">
                Démarrer le quiz
              </Button>
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-gray-600 mb-2">
                Testez vos connaissances avec le quiz de ce chapitre
              </p>
              <p className="text-sm text-gray-500">
                {currentChapter.quiz.questions?.length || 0} questions • 
                Note minimale: {currentChapter.quiz.passingScore}%
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-6">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentChapterIndex === 0}
          className="flex items-center"
        >
          <ChevronLeftIcon className="w-4 h-4 mr-2" />
          Chapitre précédent
        </Button>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            {currentChapterIndex + 1} sur {chapters.length}
          </span>
        </div>

        <Button
          onClick={handleNext}
          disabled={currentChapterIndex === chapters.length - 1}
          className="flex items-center"
        >
          Chapitre suivant
          <ChevronRightIcon className="w-4 h-4 ml-2" />
        </Button>
      </div>

      {/* Complete Chapter Button */}
      {!isPreviewMode && (
        <div className="text-center pt-4">
          <Button
            onClick={markChapterComplete}
            className="bg-green-600 hover:bg-green-700"
            disabled={completedSections.size < (currentChapter.lessons?.length || 0)}
          >
            <CheckCircleIcon className="w-4 h-4 mr-2" />
            Marquer le chapitre comme terminé
          </Button>
        </div>
      )}
    </div>
  );
}