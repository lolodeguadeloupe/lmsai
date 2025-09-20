'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import { 
  ArrowLeftIcon,
  PlayIcon,
  ClockIcon,
  UsersIcon,
  BookOpenIcon,
  PencilIcon,
  ShareIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useCourse } from '@/lib/hooks/useCourses';

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;
  
  const { data: course, isLoading, error } = useCourse(courseId);
  const [expandedChapter, setExpandedChapter] = useState<string | null>(null);

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

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'archived': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'Débutant';
      case 'intermediate': return 'Intermédiaire';
      case 'advanced': return 'Avancé';
      default: return difficulty;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'published': return 'Publié';
      case 'draft': return 'Brouillon';
      case 'archived': return 'Archivé';
      default: return status;
    }
  };

  const totalChapters = course.chapters?.length || 0;
  const totalDuration = course.chapters?.reduce((acc, chapter) => acc + chapter.duration, 0) || 0;
  const enrollmentCount = course.enrollments?.length || 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Link href="/courses">
              <Button variant="outline" size="sm" className="mr-4">
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Retour
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{course.title}</h1>
              <p className="text-gray-600 mt-2">
                Mis à jour récemment
              </p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <ShareIcon className="w-4 h-4 mr-2" />
              Partager
            </Button>
            <Link href={`/courses/${courseId}/export`}>
              <Button variant="outline" size="sm">
                <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                Exporter
              </Button>
            </Link>
            <Link href={`/courses/${courseId}/edit`}>
              <Button size="sm">
                <PencilIcon className="w-4 h-4 mr-2" />
                Éditer
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Course Overview */}
            <Card className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(course.difficulty)}`}>
                      {getDifficultyLabel(course.difficulty)}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(course.status)}`}>
                      {getStatusLabel(course.status)}
                    </span>
                  </div>
                  
                  <p className="text-gray-700 text-lg leading-relaxed mb-6">
                    {course.description}
                  </p>

                  {/* Tags */}
                  {course.tags && course.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {course.tags.map((tag, index) => (
                        <span 
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Course Thumbnail */}
                <div className="ml-6 flex-shrink-0">
                  <div className="w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <BookOpenIcon className="w-16 h-16 text-white" />
                  </div>
                </div>
              </div>
            </Card>

            {/* Course Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="p-4 text-center">
                <BookOpenIcon className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">{totalChapters}</p>
                <p className="text-sm text-gray-600">Chapitres</p>
              </Card>
              
              <Card className="p-4 text-center">
                <ClockIcon className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">
                  {Math.floor(totalDuration / 60)}h {totalDuration % 60}min
                </p>
                <p className="text-sm text-gray-600">Durée totale</p>
              </Card>
              
              <Card className="p-4 text-center">
                <UsersIcon className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">{enrollmentCount}</p>
                <p className="text-sm text-gray-600">Étudiants</p>
              </Card>
              
              <Card className="p-4 text-center">
                <ChartBarIcon className="w-8 h-8 text-orange-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">4.8</p>
                <p className="text-sm text-gray-600">Note moyenne</p>
              </Card>
            </div>

            {/* Chapters */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Contenu du cours</h2>
              
              {course.chapters && course.chapters.length > 0 ? (
                <div className="space-y-3">
                  {course.chapters
                    .sort((a, b) => a.order - b.order)
                    .map((chapter, index) => (
                    <div 
                      key={chapter.id}
                      className="border border-gray-200 rounded-lg"
                    >
                      <button
                        onClick={() => setExpandedChapter(
                          expandedChapter === chapter.id ? null : chapter.id
                        )}
                        className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                              {index + 1}
                            </span>
                            <div>
                              <h3 className="font-medium text-gray-900">{chapter.title}</h3>
                              <p className="text-sm text-gray-600">{chapter.description}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span className="flex items-center">
                              <ClockIcon className="w-4 h-4 mr-1" />
                              {chapter.duration} min
                            </span>
                            <span className="flex items-center">
                              <BookOpenIcon className="w-4 h-4 mr-1" />
                              {chapter.lessons?.length || 0} leçons
                            </span>
                          </div>
                        </div>
                      </button>
                      
                      {expandedChapter === chapter.id && (
                        <div className="px-4 pb-4 border-t border-gray-200 bg-gray-50">
                          <div className="mt-3">
                            <h4 className="font-medium text-gray-900 mb-2">Contenu du chapitre</h4>
                            <div className="prose prose-sm max-w-none text-gray-700">
                              {chapter.content ? (
                                <div dangerouslySetInnerHTML={{ __html: chapter.content }} />
                              ) : (
                                <p className="text-gray-500 italic">Contenu en cours de génération...</p>
                              )}
                            </div>
                            
                            {chapter.lessons && chapter.lessons.length > 0 && (
                              <div className="mt-4">
                                <h5 className="font-medium text-gray-900 mb-2">Leçons</h5>
                                <div className="space-y-2">
                                  {chapter.lessons
                                    .sort((a, b) => a.order - b.order)
                                    .map((lesson, lessonIndex) => (
                                    <div key={lesson.id} className="flex items-center justify-between p-2 bg-white rounded border">
                                      <div className="flex items-center space-x-2">
                                        <span className="w-6 h-6 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center text-xs">
                                          {lessonIndex + 1}
                                        </span>
                                        <span className="text-sm">{lesson.title}</span>
                                      </div>
                                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                                        <ClockIcon className="w-3 h-3" />
                                        {lesson.duration} min
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {chapter.quiz && (
                              <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                                <h5 className="font-medium text-blue-900 mb-1">Quiz du chapitre</h5>
                                <p className="text-sm text-blue-700">{chapter.quiz.title}</p>
                                <p className="text-xs text-blue-600 mt-1">
                                  {chapter.quiz.questions?.length || 0} questions • 
                                  Note minimale: {chapter.quiz.passingScore}%
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BookOpenIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Aucun chapitre
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Ce cours n'a pas encore de contenu.
                  </p>
                  <Button>
                    <PencilIcon className="w-4 h-4 mr-2" />
                    Ajouter du contenu
                  </Button>
                </div>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Actions rapides</h3>
              <div className="space-y-3">
                <Link href={`/courses/${courseId}/view`}>
                  <Button className="w-full" size="sm">
                    <PlayIcon className="w-4 h-4 mr-2" />
                    Lire le cours
                  </Button>
                </Link>
                
                <Link href={`/courses/${courseId}/view`}>
                  <Button variant="outline" className="w-full" size="sm">
                    <EyeIcon className="w-4 h-4 mr-2" />
                    Vue étudiante
                  </Button>
                </Link>
                
                <Link href={`/courses/${courseId}/export`}>
                  <Button variant="outline" className="w-full" size="sm">
                    <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                    Exporter
                  </Button>
                </Link>
                
                <Link href={`/courses/${courseId}/analytics`}>
                  <Button variant="outline" className="w-full" size="sm">
                    <ChartBarIcon className="w-4 h-4 mr-2" />
                    Analytiques
                  </Button>
                </Link>
              </div>
            </Card>

            {/* Course Info */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Informations</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Catégorie</span>
                  <span className="font-medium">{course.category?.name || 'Non définie'}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Instructeur</span>
                  <span className="font-medium">Non défini</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Créé le</span>
                  <span className="font-medium">
                    {new Date().toLocaleDateString('fr-FR')}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-600">Prix</span>
                  <span className="font-medium">
                    Gratuit
                  </span>
                </div>
              </div>
            </Card>

            {/* Recent Activity */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Activité récente</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-gray-900">Cours publié</p>
                    <p className="text-gray-500 text-xs">Il y a 2 heures</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-gray-900">Chapitre 3 ajouté</p>
                    <p className="text-gray-500 text-xs">Il y a 1 jour</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-gray-900">5 nouveaux étudiants</p>
                    <p className="text-gray-500 text-xs">Il y a 2 jours</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}