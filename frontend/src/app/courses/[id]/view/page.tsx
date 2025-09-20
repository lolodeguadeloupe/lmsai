'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import ChapterViewer from '@/components/ChapterViewer';
import { 
  ArrowLeftIcon,
  BookOpenIcon,
  ClockIcon,
  UsersIcon,
  CheckCircleIcon,
  PlayCircleIcon,
  ListBulletIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useCourse } from '@/lib/hooks/useCourses';

export default function CourseViewPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;
  
  const { data: course, isLoading, error } = useCourse(courseId);
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [completedChapters, setCompletedChapters] = useState<Set<string>>(new Set());
  const [showSidebar, setShowSidebar] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleChapterComplete = (chapterId: string) => {
    setCompletedChapters(prev => new Set([...prev, chapterId]));
  };

  const handleChapterChange = (index: number) => {
    setCurrentChapterIndex(index);
  };

  const totalChapters = course?.chapters?.length || 0;
  const completionPercentage = totalChapters > 0 ? (completedChapters.size / totalChapters) * 100 : 0;

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowLeft' && currentChapterIndex > 0) {
        setCurrentChapterIndex(currentChapterIndex - 1);
      } else if (event.key === 'ArrowRight' && currentChapterIndex < totalChapters - 1) {
        setCurrentChapterIndex(currentChapterIndex + 1);
      } else if (event.key === 'Escape') {
        setIsFullscreen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentChapterIndex, totalChapters]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loading size="lg" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-8 text-center">
          <h2 className="text-lg font-semibold text-red-600 mb-2">Cours introuvable</h2>
          <p className="text-gray-600 mb-4">Le cours demandé n'existe pas ou n'est plus disponible.</p>
          <Link href="/courses">
            <Button>Retour aux cours</Button>
          </Link>
        </Card>
      </div>
    );
  }

  if (!course.chapters || course.chapters.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-8 text-center">
          <BookOpenIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Aucun contenu disponible</h2>
          <p className="text-gray-600 mb-4">Ce cours n'a pas encore de contenu à afficher.</p>
          <Link href={`/courses/${courseId}`}>
            <Button>Retour au cours</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-50 ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      <div className="flex h-screen">
        {/* Sidebar */}
        {showSidebar && (
          <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <Link href={`/courses/${courseId}`}>
                  <Button variant="outline" size="sm">
                    <ArrowLeftIcon className="w-4 h-4 mr-2" />
                    Retour
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSidebar(false)}
                  className="lg:hidden"
                >
                  <XMarkIcon className="w-4 h-4" />
                </Button>
              </div>
              
              <h1 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                {course.title}
              </h1>
              
              {/* Progress */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Progression</span>
                  <span>{Math.round(completionPercentage)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${completionPercentage}%` }}
                  />
                </div>
              </div>

              {/* Course Stats */}
              <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                <div className="text-center">
                  <BookOpenIcon className="w-4 h-4 mx-auto mb-1" />
                  <div>{totalChapters} chapitres</div>
                </div>
                <div className="text-center">
                  <ClockIcon className="w-4 h-4 mx-auto mb-1" />
                  <div>{course.duration} min</div>
                </div>
                <div className="text-center">
                  <CheckCircleIcon className="w-4 h-4 mx-auto mb-1" />
                  <div>{completedChapters.size} terminés</div>
                </div>
              </div>
            </div>

            {/* Chapter List */}
            <div className="flex-1 overflow-y-auto">
              <div className="p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
                  <ListBulletIcon className="w-4 h-4 mr-2" />
                  Sommaire
                </h3>
                <div className="space-y-2">
                  {course.chapters
                    .sort((a, b) => a.order - b.order)
                    .map((chapter, index) => (
                    <button
                      key={chapter.id}
                      onClick={() => setCurrentChapterIndex(index)}
                      className={`w-full text-left p-3 rounded-lg transition-colors ${
                        currentChapterIndex === index
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                          completedChapters.has(chapter.id)
                            ? 'bg-green-100 text-green-600'
                            : currentChapterIndex === index
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-600'
                        }`}>
                          {completedChapters.has(chapter.id) ? (
                            <CheckCircleIcon className="w-4 h-4" />
                          ) : (
                            index + 1
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className={`text-sm font-medium line-clamp-2 ${
                            currentChapterIndex === index ? 'text-blue-900' : 'text-gray-900'
                          }`}>
                            {chapter.title}
                          </h4>
                          <div className="flex items-center mt-1 text-xs text-gray-500">
                            <ClockIcon className="w-3 h-3 mr-1" />
                            {chapter.duration} min
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-gray-200">
              <div className="space-y-2">
                <Button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  variant="outline"
                  size="sm"
                  className="w-full"
                >
                  <PlayCircleIcon className="w-4 h-4 mr-2" />
                  {isFullscreen ? 'Quitter plein écran' : 'Mode plein écran'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Mobile Header */}
          {!showSidebar && (
            <div className="lg:hidden bg-white border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSidebar(true)}
                >
                  <Bars3Icon className="w-4 h-4 mr-2" />
                  Sommaire
                </Button>
                <h1 className="text-lg font-semibold text-gray-900 truncate mx-4">
                  {course.chapters[currentChapterIndex]?.title}
                </h1>
                <Link href={`/courses/${courseId}`}>
                  <Button variant="outline" size="sm">
                    <ArrowLeftIcon className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {/* Chapter Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto p-6">
              <ChapterViewer
                chapters={course.chapters}
                currentChapterIndex={currentChapterIndex}
                onChapterChange={handleChapterChange}
                onComplete={handleChapterComplete}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Help */}
      {!isFullscreen && (
        <div className="fixed bottom-4 right-4 z-40">
          <Card className="p-3 bg-gray-900 text-white text-xs">
            <div className="space-y-1">
              <div>← → : Navigation</div>
              <div>Échap : Quitter plein écran</div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}