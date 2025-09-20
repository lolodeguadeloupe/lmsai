'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  AdjustmentsHorizontalIcon,
  ClockIcon,
  StarIcon,
  UserGroupIcon,
  EyeIcon,
  TagIcon,
  AcademicCapIcon,
  CalendarIcon,
  XMarkIcon,
  BookOpenIcon,
  CheckCircleIcon,
  PlayIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';

interface Course {
  id: string;
  title: string;
  description: string;
  instructor: string;
  level: 'Débutant' | 'Intermédiaire' | 'Avancé';
  duration: string;
  rating: number;
  studentsCount: number;
  price: number;
  tags: string[];
  category: string;
  createdAt: string;
  thumbnail: string;
  isCompleted?: boolean;
  progress?: number;
}

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<{
    categories: string[];
    levels: string[];
    duration: string[];
    rating: number | null;
    price: string[];
    tags: string[];
  }>({
    categories: [],
    levels: [],
    duration: [],
    rating: null,
    price: [],
    tags: [],
  });
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('relevance');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Mock course data
  const allCourses: Course[] = [
    {
      id: '1',
      title: 'Introduction au React',
      description: 'Apprenez les bases de React et créez vos premières applications web modernes.',
      instructor: 'Marie Dubois',
      level: 'Débutant',
      duration: '12h',
      rating: 4.8,
      studentsCount: 2847,
      price: 49,
      tags: ['React', 'JavaScript', 'Frontend'],
      category: 'Développement Web',
      createdAt: '2024-01-15',
      thumbnail: '/api/placeholder/300/200',
      progress: 65,
    },
    {
      id: '2',
      title: 'JavaScript Avancé',
      description: 'Maîtrisez les concepts avancés de JavaScript pour devenir un développeur expert.',
      instructor: 'Pierre Martin',
      level: 'Avancé',
      duration: '18h',
      rating: 4.9,
      studentsCount: 1934,
      price: 79,
      tags: ['JavaScript', 'ES6+', 'Async/Await'],
      category: 'Développement Web',
      createdAt: '2024-02-20',
      thumbnail: '/api/placeholder/300/200',
      isCompleted: true,
    },
    {
      id: '3',
      title: 'Python pour Débutants',
      description: 'Découvrez la programmation avec Python, le langage idéal pour commencer.',
      instructor: 'Sophie Laurent',
      level: 'Débutant',
      duration: '15h',
      rating: 4.7,
      studentsCount: 3456,
      price: 39,
      tags: ['Python', 'Programmation', 'Bases'],
      category: 'Programmation',
      createdAt: '2024-03-10',
      thumbnail: '/api/placeholder/300/200',
    },
    {
      id: '4',
      title: 'Design Systems avec Figma',
      description: 'Créez des systèmes de design cohérents et scalables avec Figma.',
      instructor: 'Thomas Bernard',
      level: 'Intermédiaire',
      duration: '8h',
      rating: 4.6,
      studentsCount: 1567,
      price: 59,
      tags: ['Design', 'Figma', 'UI/UX'],
      category: 'Design',
      createdAt: '2024-04-05',
      thumbnail: '/api/placeholder/300/200',
      progress: 30,
    },
    {
      id: '5',
      title: 'Machine Learning avec Python',
      description: 'Introduction pratique au machine learning et à l\'intelligence artificielle.',
      instructor: 'Laura Chen',
      level: 'Avancé',
      duration: '25h',
      rating: 4.9,
      studentsCount: 892,
      price: 99,
      tags: ['Machine Learning', 'Python', 'IA'],
      category: 'Data Science',
      createdAt: '2024-05-12',
      thumbnail: '/api/placeholder/300/200',
    },
    {
      id: '6',
      title: 'DevOps et Docker',
      description: 'Maîtrisez les outils DevOps modernes et la containerisation avec Docker.',
      instructor: 'Antoine Moreau',
      level: 'Intermédiaire',
      duration: '20h',
      rating: 4.5,
      studentsCount: 1234,
      price: 69,
      tags: ['DevOps', 'Docker', 'CI/CD'],
      category: 'DevOps',
      createdAt: '2024-06-18',
      thumbnail: '/api/placeholder/300/200',
    },
  ];

  // Filter options
  const filterOptions = {
    categories: ['Développement Web', 'Programmation', 'Design', 'Data Science', 'DevOps', 'Marketing'],
    levels: ['Débutant', 'Intermédiaire', 'Avancé'],
    duration: ['Moins de 5h', '5-10h', '10-20h', 'Plus de 20h'],
    price: ['Gratuit', 'Moins de 50€', '50-100€', 'Plus de 100€'],
  };

  // Popular tags
  const popularTags = ['React', 'JavaScript', 'Python', 'Design', 'Machine Learning', 'DevOps'];

  // Filter courses based on search and filters
  const filteredCourses = allCourses.filter((course) => {
    // Search query filter
    if (searchQuery && !course.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !course.description.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !course.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))) {
      return false;
    }

    // Category filter
    if (selectedFilters.categories.length > 0 && !selectedFilters.categories.includes(course.category)) {
      return false;
    }

    // Level filter
    if (selectedFilters.levels.length > 0 && !selectedFilters.levels.includes(course.level)) {
      return false;
    }

    // Rating filter
    if (selectedFilters.rating && course.rating < selectedFilters.rating) {
      return false;
    }

    // Tags filter
    if (selectedFilters.tags.length > 0 && !selectedFilters.tags.some(tag => course.tags.includes(tag))) {
      return false;
    }

    return true;
  });

  // Sort courses
  const sortedCourses = [...filteredCourses].sort((a, b) => {
    switch (sortBy) {
      case 'rating':
        return b.rating - a.rating;
      case 'students':
        return b.studentsCount - a.studentsCount;
      case 'price-low':
        return a.price - b.price;
      case 'price-high':
        return b.price - a.price;
      case 'newest':
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      case 'oldest':
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
      default: // relevance
        return 0;
    }
  });

  const toggleFilter = (type: keyof typeof selectedFilters, value: string) => {
    setSelectedFilters(prev => ({
      ...prev,
      [type]: Array.isArray(prev[type]) 
        ? (prev[type] as string[]).includes(value)
          ? (prev[type] as string[]).filter(item => item !== value)
          : [...(prev[type] as string[]), value]
        : prev[type]
    }));
  };

  const clearAllFilters = () => {
    setSelectedFilters({
      categories: [],
      levels: [],
      duration: [],
      rating: null,
      price: [],
      tags: [],
    });
  };

  const activeFiltersCount = 
    selectedFilters.categories.length + 
    selectedFilters.levels.length + 
    selectedFilters.duration.length + 
    selectedFilters.price.length + 
    selectedFilters.tags.length + 
    (selectedFilters.rating ? 1 : 0);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Rechercher des cours</h1>
          <p className="text-gray-600">Trouvez le cours parfait parmi notre collection</p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Rechercher des cours, instructeurs, ou sujets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>
        </div>

        {/* Popular Tags */}
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-3">Tags populaires:</p>
          <div className="flex flex-wrap gap-2">
            {popularTags.map((tag) => (
              <button
                key={tag}
                onClick={() => toggleFilter('tags', tag)}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  selectedFilters.tags.includes(tag)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-8">
          {/* Filters Sidebar */}
          <div className={`${showFilters ? 'block' : 'hidden'} lg:block w-80 flex-shrink-0`}>
            <Card className="p-6 sticky top-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Filtres</h3>
                {activeFiltersCount > 0 && (
                  <button
                    onClick={clearAllFilters}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Effacer tout ({activeFiltersCount})
                  </button>
                )}
              </div>

              <div className="space-y-6">
                {/* Categories */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Catégories</h4>
                  <div className="space-y-2">
                    {filterOptions.categories.map((category) => (
                      <label key={category} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedFilters.categories.includes(category)}
                          onChange={() => toggleFilter('categories', category)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{category}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Levels */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Niveau</h4>
                  <div className="space-y-2">
                    {filterOptions.levels.map((level) => (
                      <label key={level} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedFilters.levels.includes(level)}
                          onChange={() => toggleFilter('levels', level)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{level}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Rating */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Note minimum</h4>
                  <div className="space-y-2">
                    {[4.5, 4.0, 3.5, 3.0].map((rating) => (
                      <label key={rating} className="flex items-center">
                        <input
                          type="radio"
                          name="rating"
                          checked={selectedFilters.rating === rating}
                          onChange={() => setSelectedFilters(prev => ({ ...prev, rating }))}
                          className="border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="ml-2 flex items-center">
                          <div className="flex items-center">
                            {[...Array(Math.floor(rating))].map((_, i) => (
                              <StarIcon key={i} className="w-4 h-4 text-yellow-400 fill-current" />
                            ))}
                            {rating % 1 !== 0 && (
                              <StarIcon className="w-4 h-4 text-yellow-400 fill-current opacity-50" />
                            )}
                          </div>
                          <span className="ml-1 text-sm text-gray-700">{rating}+</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Duration */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Durée</h4>
                  <div className="space-y-2">
                    {filterOptions.duration.map((duration) => (
                      <label key={duration} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedFilters.duration.includes(duration)}
                          onChange={() => toggleFilter('duration', duration)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{duration}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Price */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Prix</h4>
                  <div className="space-y-2">
                    {filterOptions.price.map((price) => (
                      <label key={price} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedFilters.price.includes(price)}
                          onChange={() => toggleFilter('price', price)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{price}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Results */}
          <div className="flex-1">
            {/* Results Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="lg:hidden flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <FunnelIcon className="w-4 h-4 mr-2" />
                  Filtres
                  {activeFiltersCount > 0 && (
                    <span className="ml-2 bg-blue-600 text-white text-xs rounded-full px-2 py-1">
                      {activeFiltersCount}
                    </span>
                  )}
                </button>
                <p className="text-gray-600">
                  {sortedCourses.length} résultat{sortedCourses.length > 1 ? 's' : ''} trouvé{sortedCourses.length > 1 ? 's' : ''}
                </p>
              </div>

              <div className="flex items-center space-x-4">
                {/* Sort */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="relevance">Pertinence</option>
                  <option value="rating">Note</option>
                  <option value="students">Nombre d'étudiants</option>
                  <option value="price-low">Prix croissant</option>
                  <option value="price-high">Prix décroissant</option>
                  <option value="newest">Plus récent</option>
                  <option value="oldest">Plus ancien</option>
                </select>

                {/* View Mode */}
                <div className="flex border border-gray-300 rounded-md">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Course Results */}
            {sortedCourses.length === 0 ? (
              <Card className="p-12 text-center">
                <MagnifyingGlassIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun cours trouvé</h3>
                <p className="text-gray-600 mb-4">
                  Essayez de modifier vos critères de recherche ou vos filtres.
                </p>
                <Button onClick={clearAllFilters} variant="outline">
                  Effacer les filtres
                </Button>
              </Card>
            ) : (
              <div className={viewMode === 'grid' 
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
                : 'space-y-4'
              }>
                {sortedCourses.map((course) => (
                  <Card key={course.id} className={`${viewMode === 'list' ? 'p-6' : 'overflow-hidden'} hover:shadow-lg transition-shadow`}>
                    {viewMode === 'grid' ? (
                      <>
                        <div className="relative">
                          <img
                            src={course.thumbnail}
                            alt={course.title}
                            className="w-full h-48 object-cover"
                          />
                          {course.isCompleted && (
                            <div className="absolute top-2 right-2 bg-green-500 text-white p-1 rounded-full">
                              <CheckCircleIcon className="w-4 h-4" />
                            </div>
                          )}
                          {course.progress && !course.isCompleted && (
                            <div className="absolute bottom-0 left-0 right-0 bg-gray-900 bg-opacity-75 text-white p-2">
                              <div className="flex items-center justify-between text-xs">
                                <span>Progression</span>
                                <span>{course.progress}%</span>
                              </div>
                              <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                                <div 
                                  className="bg-blue-500 h-1 rounded-full" 
                                  style={{ width: `${course.progress}%` }}
                                ></div>
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="p-6">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
                              {course.level}
                            </span>
                            <span className="text-sm font-bold text-gray-900">€{course.price}</span>
                          </div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                            {course.title}
                          </h3>
                          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                            {course.description}
                          </p>
                          <p className="text-sm text-gray-500 mb-3">par {course.instructor}</p>
                          
                          <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                            <div className="flex items-center">
                              <StarIcon className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                              <span>{course.rating}</span>
                            </div>
                            <div className="flex items-center">
                              <UserGroupIcon className="w-4 h-4 mr-1" />
                              <span>{course.studentsCount.toLocaleString()}</span>
                            </div>
                            <div className="flex items-center">
                              <ClockIcon className="w-4 h-4 mr-1" />
                              <span>{course.duration}</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-1 mb-4">
                            {course.tags.slice(0, 3).map((tag) => (
                              <span key={tag} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>

                          <Link href={`/courses/${course.id}`}>
                            <Button className="w-full">
                              {course.isCompleted ? 'Revoir' : course.progress ? 'Continuer' : 'Commencer'}
                            </Button>
                          </Link>
                        </div>
                      </>
                    ) : (
                      <div className="flex space-x-4">
                        <div className="relative flex-shrink-0">
                          <img
                            src={course.thumbnail}
                            alt={course.title}
                            className="w-32 h-24 object-cover rounded"
                          />
                          {course.isCompleted && (
                            <div className="absolute -top-1 -right-1 bg-green-500 text-white p-1 rounded-full">
                              <CheckCircleIcon className="w-3 h-3" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                {course.title}
                              </h3>
                              <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                                {course.description}
                              </p>
                              <p className="text-sm text-gray-500">par {course.instructor}</p>
                            </div>
                            <div className="text-right">
                              <span className="text-lg font-bold text-gray-900">€{course.price}</span>
                              <div className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded mt-1">
                                {course.level}
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <div className="flex items-center">
                                <StarIcon className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                                <span>{course.rating}</span>
                              </div>
                              <div className="flex items-center">
                                <UserGroupIcon className="w-4 h-4 mr-1" />
                                <span>{course.studentsCount.toLocaleString()}</span>
                              </div>
                              <div className="flex items-center">
                                <ClockIcon className="w-4 h-4 mr-1" />
                                <span>{course.duration}</span>
                              </div>
                            </div>
                            
                            <Link href={`/courses/${course.id}`}>
                              <Button size="sm">
                                {course.isCompleted ? 'Revoir' : course.progress ? 'Continuer' : 'Commencer'}
                              </Button>
                            </Link>
                          </div>

                          {course.progress && !course.isCompleted && (
                            <div className="mt-3">
                              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                                <span>Progression</span>
                                <span>{course.progress}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1">
                                <div 
                                  className="bg-blue-500 h-1 rounded-full" 
                                  style={{ width: `${course.progress}%` }}
                                ></div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}