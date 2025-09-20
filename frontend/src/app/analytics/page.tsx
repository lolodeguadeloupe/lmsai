'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  ChartBarIcon,
  EyeIcon,
  UserGroupIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
  UsersIcon,
  TrophyIcon,
  BookOpenIcon,
  FunnelIcon,
  DocumentArrowDownIcon,
  AcademicCapIcon,
  StarIcon,
  CurrencyDollarIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  GlobeAltIcon,
  PlayIcon,
  PauseIcon,
  ForwardIcon,
  BackwardIcon,
  ChartPieIcon,
  MapIcon,
  BellIcon,
  CogIcon,
} from '@heroicons/react/24/outline';

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('overview');

  // Enhanced stats with more metrics
  const stats = [
    {
      name: 'Vues totales',
      value: '12,847',
      change: '+12%',
      changeType: 'increase' as const,
      icon: EyeIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Nouveaux étudiants',
      value: '1,247',
      change: '+8%',
      changeType: 'increase' as const,
      icon: UserGroupIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Temps moyen',
      value: '24min',
      change: '-3%',
      changeType: 'decrease' as const,
      icon: ClockIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Taux de completion',
      value: '87%',
      change: '+5%',
      changeType: 'increase' as const,
      icon: ArrowTrendingUpIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      name: 'Revenus',
      value: '€45,230',
      change: '+23%',
      changeType: 'increase' as const,
      icon: CurrencyDollarIcon,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
    },
    {
      name: 'Note moyenne',
      value: '4.8/5',
      change: '+0.2',
      changeType: 'increase' as const,
      icon: StarIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      name: 'Certificats émis',
      value: '892',
      change: '+15%',
      changeType: 'increase' as const,
      icon: AcademicCapIcon,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100',
    },
    {
      name: 'Support demandes',
      value: '23',
      change: '-18%',
      changeType: 'decrease' as const,
      icon: BellIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
  ];

  // Device analytics
  const deviceStats = [
    { name: 'Desktop', percentage: 68, icon: ComputerDesktopIcon, color: 'bg-blue-500' },
    { name: 'Mobile', percentage: 28, icon: DevicePhoneMobileIcon, color: 'bg-green-500' },
    { name: 'Tablette', percentage: 4, icon: GlobeAltIcon, color: 'bg-purple-500' },
  ];

  // Geographic data
  const geoData = [
    { country: 'France', users: 4234, percentage: 45 },
    { country: 'Belgique', users: 1876, percentage: 20 },
    { country: 'Canada', users: 1234, percentage: 13 },
    { country: 'Suisse', users: 987, percentage: 11 },
    { country: 'Autres', users: 1016, percentage: 11 },
  ];

  // Learning path analytics
  const learningPaths = [
    { name: 'Développement Web', completions: 234, avgTime: '6.5h', satisfaction: 4.7 },
    { name: 'Data Science', completions: 189, avgTime: '8.2h', satisfaction: 4.8 },
    { name: 'Mobile Development', completions: 156, avgTime: '5.8h', satisfaction: 4.6 },
    { name: 'Cloud Computing', completions: 123, avgTime: '7.1h', satisfaction: 4.9 },
  ];

  const topCourses = [
    { name: 'Introduction au React', views: 3451, students: 287, completion: 89 },
    { name: 'JavaScript Avancé', views: 2834, students: 231, completion: 84 },
    { name: 'Python pour Débutants', views: 2190, students: 195, completion: 92 },
    { name: 'Design Systems', views: 1876, students: 156, completion: 78 },
    { name: 'Machine Learning 101', views: 1654, students: 134, completion: 85 },
  ];

  const timeRanges = [
    { label: '7 jours', value: '7d' },
    { label: '30 jours', value: '30d' },
    { label: '90 jours', value: '90d' },
    { label: '1 an', value: '1y' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
              <p className="mt-2 text-gray-600">
                Suivez les performances de vos cours et l'engagement des étudiants
              </p>
            </div>
            <div className="mt-4 sm:mt-0 flex items-center space-x-4">
              {/* Time Range Selector */}
              <div className="flex bg-white rounded-lg border border-gray-200 p-1">
                {timeRanges.map((range) => (
                  <button
                    key={range.value}
                    onClick={() => setTimeRange(range.value)}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                      timeRange === range.value
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
              <Button variant="outline" size="sm">
                <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                Exporter
              </Button>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {stats.map((stat) => (
            <Card key={stat.name} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center">
                <div className={`${stat.bgColor} rounded-lg p-3`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <div className="flex items-baseline">
                    <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                    <div className={`ml-2 flex items-center text-sm font-medium ${
                      stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.changeType === 'increase' ? (
                        <ArrowTrendingUpIcon className="h-3 w-3 mr-1" />
                      ) : (
                        <ArrowTrendingDownIcon className="h-3 w-3 mr-1" />
                      )}
                      {stat.change}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Chart Area */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Learning Paths Performance */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Performance des parcours</h2>
                <Button variant="outline" size="sm">
                  <ChartPieIcon className="w-4 h-4 mr-2" />
                  Voir détails
                </Button>
              </div>
              
              <div className="space-y-4">
                {learningPaths.map((path) => (
                  <div key={path.name} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">{path.name}</h3>
                      <div className="flex items-center space-x-2">
                        <StarIcon className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm font-medium">{path.satisfaction}</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Complétions: </span>
                        <span className="font-medium">{path.completions}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Temps moyen: </span>
                        <span className="font-medium">{path.avgTime}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Satisfaction: </span>
                        <span className="font-medium">{path.satisfaction}/5</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Device Analytics */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Appareils utilisés</h2>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <DevicePhoneMobileIcon className="w-4 h-4" />
                  <span>Analyse des plateformes</span>
                </div>
              </div>
              
              <div className="space-y-4">
                {deviceStats.map((device) => (
                  <div key={device.name} className="flex items-center space-x-4">
                    <div className="flex items-center space-x-3 flex-1">
                      <device.icon className="w-5 h-5 text-gray-600" />
                      <span className="text-sm font-medium text-gray-900">{device.name}</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`${device.color} h-2 rounded-full`} 
                          style={{ width: `${device.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium w-8 text-right">{device.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
            {/* Views Chart */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Vues au fil du temps</h2>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <CalendarIcon className="w-4 h-4" />
                  <span>Derniers {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}</span>
                </div>
              </div>
              
              {/* Mock Chart */}
              <div className="h-64 bg-gradient-to-t from-blue-50 to-white rounded-lg border border-gray-200 flex items-end justify-between p-4">
                {[...Array(7)].map((_, i) => (
                  <div 
                    key={i}
                    className="bg-blue-500 rounded-t-md w-8"
                    style={{ height: `${Math.random() * 200 + 50}px` }}
                  />
                ))}
              </div>
              
              <div className="mt-4 flex justify-between text-xs text-gray-500">
                <span>Lun</span>
                <span>Mar</span>
                <span>Mer</span>
                <span>Jeu</span>
                <span>Ven</span>
                <span>Sam</span>
                <span>Dim</span>
              </div>
            </Card>

            {/* Engagement Chart */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Engagement des étudiants</h2>
                <Button variant="outline" size="sm">
                  Voir détails
                </Button>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Taux de completion</span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '87%' }}></div>
                    </div>
                    <span className="text-sm font-medium">87%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Temps moyen par session</span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: '65%' }}></div>
                    </div>
                    <span className="text-sm font-medium">24min</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Taux de rétention</span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div className="bg-purple-500 h-2 rounded-full" style={{ width: '73%' }}></div>
                    </div>
                    <span className="text-sm font-medium">73%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Note moyenne</span>
                  <div className="flex items-center">
                    <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                      <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '96%' }}></div>
                    </div>
                    <span className="text-sm font-medium">4.8/5</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Geographic Analytics */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Répartition géographique</h3>
              <div className="space-y-3">
                {geoData.map((geo) => (
                  <div key={geo.country} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <MapIcon className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-900">{geo.country}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full" 
                          style={{ width: `${geo.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium w-8 text-right">{geo.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t">
                <div className="text-center">
                  <span className="text-sm text-gray-500">Total utilisateurs actifs</span>
                  <p className="text-lg font-semibold text-gray-900">
                    {geoData.reduce((sum, geo) => sum + geo.users, 0).toLocaleString()}
                  </p>
                </div>
              </div>
            </Card>

            {/* Top Courses */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cours les plus populaires</h3>
              <div className="space-y-4">
                {topCourses.map((course, index) => (
                  <div key={course.name} className="flex items-center space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{course.name}</p>
                      <div className="flex items-center text-xs text-gray-500 space-x-3">
                        <span className="flex items-center">
                          <EyeIcon className="w-3 h-3 mr-1" />
                          {course.views.toLocaleString()}
                        </span>
                        <span className="flex items-center">
                          <UserGroupIcon className="w-3 h-3 mr-1" />
                          {course.students}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-medium text-gray-900">{course.completion}%</span>
                      <p className="text-xs text-gray-500">completion</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Traffic Sources */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Sources de trafic</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Recherche directe</span>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: '45%' }}></div>
                    </div>
                    <span className="text-sm font-medium">45%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Réseaux sociaux</span>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '30%' }}></div>
                    </div>
                    <span className="text-sm font-medium">30%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Email</span>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div className="bg-purple-500 h-2 rounded-full" style={{ width: '15%' }}></div>
                    </div>
                    <span className="text-sm font-medium">15%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Référencement</span>
                  <div className="flex items-center">
                    <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                      <div className="bg-orange-500 h-2 rounded-full" style={{ width: '10%' }}></div>
                    </div>
                    <span className="text-sm font-medium">10%</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h3>
              <div className="space-y-3">
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <ChartBarIcon className="w-4 h-4 mr-2" />
                  Rapport détaillé
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                  Exporter données
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <CalendarIcon className="w-4 h-4 mr-2" />
                  Planifier rapport
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <CogIcon className="w-4 h-4 mr-2" />
                  Configurer alertes
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                  Rapport PDF
                </Button>
              </div>
            </Card>
            
            {/* Real-time Activity */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Activité en temps réel</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Utilisateurs actifs</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium">147</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Cours en cours</span>
                  <span className="text-sm font-medium">89</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Quiz complétés (1h)</span>
                  <span className="text-sm font-medium">23</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Nouvelles inscriptions</span>
                  <span className="text-sm font-medium">12</span>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t">
                <Button variant="ghost" className="w-full text-blue-600 hover:text-blue-700">
                  Voir activité détaillée
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}