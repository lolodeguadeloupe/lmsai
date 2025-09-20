'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import { useCourses } from '@/lib/hooks/useCourses';
import { 
  PlusIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  BookOpenIcon,
  ClockIcon,
  UsersIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { Course } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

export default function CoursesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<Course['status'] | 'all'>('all');
  const [filterDifficulty, setFilterDifficulty] = useState<Course['difficulty'] | 'all'>('all');
  
  const { 
    data: courses, 
    isLoading, 
    error 
  } = useCourses({
    search: searchTerm,
    ...(filterStatus !== 'all' && { status: filterStatus }),
    ...(filterDifficulty !== 'all' && { difficulty: filterDifficulty }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loading size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-8 text-center">
          <h2 className="text-lg font-semibold text-red-600 mb-2">Erreur</h2>
          <p className="text-gray-600">Impossible de charger les cours.</p>
          <Button 
            className="mt-4" 
            onClick={() => window.location.reload()}
          >
            Réessayer
          </Button>
        </Card>
      </div>
    );
  }

  const getDifficultyColor = (difficulty: Course['difficulty']) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: Course['status']) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'archived': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyLabel = (difficulty: Course['difficulty']) => {
    switch (difficulty) {
      case 'beginner': return 'Débutant';
      case 'intermediate': return 'Intermédiaire';
      case 'advanced': return 'Avancé';
      default: return difficulty;
    }
  };

  const getStatusLabel = (status: Course['status']) => {
    switch (status) {
      case 'published': return 'Publié';
      case 'draft': return 'Brouillon';
      case 'archived': return 'Archivé';
      default: return status;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Mes Cours</h1>
            <p className="text-gray-600 mt-2">
              Gérez et créez vos cours avec l'IA
            </p>
          </div>
          <Link href="/courses/create">
            <Button className="mt-4 sm:mt-0 bg-blue-600 hover:bg-blue-700">
              <PlusIcon className="w-4 h-4 mr-2" />
              Créer un cours
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <Card className="p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher un cours..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Status Filter */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as Course['status'] | 'all')}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Tous les statuts</option>
              <option value="draft">Brouillon</option>
              <option value="published">Publié</option>
              <option value="archived">Archivé</option>
            </select>

            {/* Difficulty Filter */}
            <select
              value={filterDifficulty}
              onChange={(e) => setFilterDifficulty(e.target.value as Course['difficulty'] | 'all')}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Tous les niveaux</option>
              <option value="beginner">Débutant</option>
              <option value="intermediate">Intermédiaire</option>
              <option value="advanced">Avancé</option>
            </select>
          </div>
        </Card>

        {/* Courses Grid */}
        {courses && courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <Card key={course.id} className="group hover:shadow-lg transition-shadow duration-200">
                <div className="p-6">
                  {/* Course Image Placeholder */}
                  <div className="w-full h-40 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg mb-4 flex items-center justify-center">
                    <BookOpenIcon className="w-12 h-12 text-white" />
                  </div>

                  {/* Course Info */}
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors">
                        {course.title}
                      </h3>
                    </div>

                    <p className="text-gray-600 text-sm line-clamp-2">
                      {course.description}
                    </p>

                    {/* Badges */}
                    <div className="flex flex-wrap gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(course.difficulty)}`}>
                        {getDifficultyLabel(course.difficulty)}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(course.status)}`}>
                        {getStatusLabel(course.status)}
                      </span>
                    </div>

                    {/* Course Stats */}
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <div className="flex items-center">
                        <ClockIcon className="w-4 h-4 mr-1" />
                        {Math.floor(course.duration / 60)}h {course.duration % 60}min
                      </div>
                      <div className="flex items-center">
                        <UsersIcon className="w-4 h-4 mr-1" />
                        {course.enrollments?.length || 0} étudiants
                      </div>
                    </div>

                    {/* Last Updated */}
                    <p className="text-xs text-gray-400">
                      Mis à jour {formatDistanceToNow(new Date(course.updatedAt), { 
                        addSuffix: true, 
                        locale: fr 
                      })}
                    </p>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <Link href={`/courses/${course.id}`} className="flex-1">
                        <Button variant="outline" size="sm" className="w-full">
                          <PlayIcon className="w-4 h-4 mr-2" />
                          Voir
                        </Button>
                      </Link>
                      <Link href={`/courses/${course.id}/edit`}>
                        <Button variant="outline" size="sm">
                          Éditer
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-12 text-center">
            <BookOpenIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Aucun cours trouvé
            </h3>
            <p className="text-gray-600 mb-6">
              Commencez par créer votre premier cours avec l'IA.
            </p>
            <Link href="/courses/create">
              <Button>
                <PlusIcon className="w-4 h-4 mr-2" />
                Créer mon premier cours
              </Button>
            </Link>
          </Card>
        )}
      </div>
    </div>
  );
}