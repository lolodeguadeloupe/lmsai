'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  BookOpenIcon,
  UsersIcon,
  ChartBarIcon,
  PlusIcon,
  SparklesIcon,
  ClockIcon,
  EyeIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useCourses } from '@/lib/hooks/useCourses';

export default function DashboardPage() {
  const { data: courses, isLoading } = useCourses();

  // Mock data for demonstration
  const stats = [
    {
      name: 'Cours créés',
      value: courses?.length || 0,
      icon: BookOpenIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      change: '+12%',
      changeType: 'increase',
    },
    {
      name: 'Étudiants totaux',
      value: '2,847',
      icon: UsersIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      change: '+8%',
      changeType: 'increase',
    },
    {
      name: 'Heures de contenu',
      value: '156h',
      icon: ClockIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      change: '+23%',
      changeType: 'increase',
    },
    {
      name: 'Taux de completion',
      value: '87%',
      icon: ArrowTrendingUpIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      change: '+5%',
      changeType: 'increase',
    },
  ];

  const recentCourses = courses?.slice(0, 5) || [];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-2 text-gray-600">
                Bienvenue dans votre plateforme de création de cours IA
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <Link href="/courses/create">
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <PlusIcon className="w-4 h-4 mr-2" />
                  Créer un nouveau cours
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {stats.map((stat) => (
            <Card key={stat.name} className="p-6">
              <div className="flex items-center">
                <div className={`${stat.bgColor} rounded-lg p-3`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <div className="flex items-baseline">
                    <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                    <p className={`ml-2 text-sm font-medium ${
                      stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Courses */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Cours récents</h2>
                <Link href="/courses">
                  <Button variant="outline" size="sm">
                    Voir tout
                  </Button>
                </Link>
              </div>

              {isLoading ? (
                <div className="space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse flex space-x-4">
                      <div className="w-16 h-16 bg-gray-200 rounded-lg"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : recentCourses.length > 0 ? (
                <div className="space-y-4">
                  {recentCourses.map((course) => (
                    <div key={course.id} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <BookOpenIcon className="w-8 h-8 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {course.title}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">
                          {course.description}
                        </p>
                        <div className="flex items-center mt-2 space-x-4 text-xs text-gray-400">
                          <span className={`px-2 py-1 rounded-full ${
                            course.status === 'published' ? 'bg-green-100 text-green-800' :
                            course.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {course.status === 'published' ? 'Publié' :
                             course.status === 'draft' ? 'Brouillon' : 'Archivé'}
                          </span>
                          <span className="flex items-center">
                            <ClockIcon className="w-3 h-3 mr-1" />
                            {Math.floor(course.duration / 60)}h {course.duration % 60}min
                          </span>
                          <span className="flex items-center">
                            <UsersIcon className="w-3 h-3 mr-1" />
                            {course.enrollments?.length || 0} étudiants
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Link href={`/courses/${course.id}`}>
                          <Button variant="outline" size="sm">
                            <EyeIcon className="w-4 h-4" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BookOpenIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Aucun cours
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Créez votre premier cours avec l'IA pour commencer.
                  </p>
                  <Link href="/courses/create">
                    <Button>
                      <SparklesIcon className="w-4 h-4 mr-2" />
                      Créer un cours
                    </Button>
                  </Link>
                </div>
              )}
            </Card>
          </div>

          {/* Quick Actions & Tips */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h3>
              <div className="space-y-3">
                <Link href="/courses/create">
                  <Button className="w-full justify-start" variant="outline">
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Nouveau cours
                  </Button>
                </Link>
                <Link href="/courses">
                  <Button className="w-full justify-start" variant="outline">
                    <BookOpenIcon className="w-4 h-4 mr-2" />
                    Mes cours
                  </Button>
                </Link>
                <Link href="/analytics">
                  <Button className="w-full justify-start" variant="outline">
                    <ChartBarIcon className="w-4 h-4 mr-2" />
                    Analytiques
                  </Button>
                </Link>
              </div>
            </Card>

            {/* Tips */}
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
              <div className="flex items-center mb-3">
                <SparklesIcon className="w-5 h-5 text-blue-600 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">Conseil IA</h3>
              </div>
              <p className="text-sm text-gray-700 mb-4">
                Pour de meilleurs résultats, soyez précis dans vos prompts. Mentionnez le niveau, 
                les objectifs d'apprentissage et les projets pratiques souhaités.
              </p>
              <Button size="sm" variant="outline" className="border-blue-300 text-blue-700 hover:bg-blue-100">
                En savoir plus
              </Button>
            </Card>

            {/* Recent Activity */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Activité récente</h3>
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-900">Cours "React Avancé" publié</p>
                    <p className="text-xs text-gray-500">Il y a 2 heures</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-900">Nouveau chapitre ajouté</p>
                    <p className="text-xs text-gray-500">Il y a 1 jour</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-900">12 nouveaux étudiants inscrits</p>
                    <p className="text-xs text-gray-500">Il y a 2 jours</p>
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