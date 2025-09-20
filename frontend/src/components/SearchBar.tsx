'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  MagnifyingGlassIcon,
  XMarkIcon,
  ClockIcon,
  BookOpenIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';

interface SearchResult {
  id: string;
  title: string;
  type: 'course' | 'instructor' | 'category';
  description?: string;
  instructor?: string;
  url: string;
}

interface SearchBarProps {
  placeholder?: string;
  className?: string;
  showQuickResults?: boolean;
  onSearch?: (query: string) => void;
}

export default function SearchBar({ 
  placeholder = "Rechercher des cours, instructeurs, ou sujets...",
  className = "",
  showQuickResults = true,
  onSearch 
}: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const searchRef = useRef<HTMLDivElement>(null);

  // Mock search results
  const mockResults: SearchResult[] = [
    {
      id: '1',
      title: 'Introduction au React',
      type: 'course',
      description: 'Apprenez les bases de React et créez vos premières applications web modernes.',
      instructor: 'Marie Dubois',
      url: '/courses/1'
    },
    {
      id: '2',
      title: 'JavaScript Avancé',
      type: 'course',
      description: 'Maîtrisez les concepts avancés de JavaScript pour devenir un développeur expert.',
      instructor: 'Pierre Martin',
      url: '/courses/2'
    },
    {
      id: '3',
      title: 'Marie Dubois',
      type: 'instructor',
      description: 'Développeuse Senior spécialisée en React et JavaScript',
      url: '/instructors/marie-dubois'
    },
    {
      id: '4',
      title: 'Développement Web',
      type: 'category',
      description: '24 cours disponibles',
      url: '/categories/web-development'
    },
    {
      id: '5',
      title: 'Python pour Débutants',
      type: 'course',
      description: 'Découvrez la programmation avec Python, le langage idéal pour commencer.',
      instructor: 'Sophie Laurent',
      url: '/courses/3'
    },
  ];

  // Popular searches
  const popularSearches = [
    'React',
    'JavaScript',
    'Python',
    'Machine Learning',
    'Design Systems',
    'DevOps'
  ];

  // Handle search input change
  const handleInputChange = (value: string) => {
    setQuery(value);
    
    if (value.length > 0) {
      // Filter results based on query
      const filtered = mockResults.filter(result =>
        result.title.toLowerCase().includes(value.toLowerCase()) ||
        (result.description && result.description.toLowerCase().includes(value.toLowerCase()))
      );
      setResults(filtered.slice(0, 5)); // Limit to 5 results
      setIsOpen(true);
    } else {
      setResults([]);
      setIsOpen(false);
    }
  };

  // Handle search submission
  const handleSearch = (searchQuery: string = query) => {
    if (searchQuery.trim()) {
      // Add to recent searches
      setRecentSearches(prev => {
        const updated = [searchQuery, ...prev.filter(s => s !== searchQuery)];
        return updated.slice(0, 5); // Keep only 5 recent searches
      });
      
      setIsOpen(false);
      onSearch?.(searchQuery);
      
      // Navigate to search page
      window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setQuery('');
    }
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'course':
        return <BookOpenIcon className="w-4 h-4 text-blue-500" />;
      case 'instructor':
        return <UserIcon className="w-4 h-4 text-green-500" />;
      case 'category':
        return <div className="w-4 h-4 bg-purple-500 rounded"></div>;
      default:
        return <MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  const getResultTypeLabel = (type: string) => {
    switch (type) {
      case 'course':
        return 'Cours';
      case 'instructor':
        return 'Instructeur';
      case 'category':
        return 'Catégorie';
      default:
        return '';
    }
  };

  return (
    <div ref={searchRef} className={`relative ${className}`}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsOpen(true)}
          className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
        {query && (
          <button
            onClick={() => {
              setQuery('');
              setResults([]);
              setIsOpen(false);
            }}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && showQuickResults && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {query.length === 0 ? (
            // Show recent searches and popular searches when no query
            <div className="p-4">
              {recentSearches.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                    <ClockIcon className="w-4 h-4 mr-2" />
                    Recherches récentes
                  </h4>
                  <div className="space-y-1">
                    {recentSearches.map((search, index) => (
                      <button
                        key={index}
                        onClick={() => handleSearch(search)}
                        className="block w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                      >
                        {search}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Recherches populaires</h4>
                <div className="flex flex-wrap gap-2">
                  {popularSearches.map((search) => (
                    <button
                      key={search}
                      onClick={() => handleSearch(search)}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      {search}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            // Show search results
            <>
              {results.length > 0 ? (
                <div className="py-2">
                  {results.map((result) => (
                    <Link
                      key={result.id}
                      href={result.url}
                      className="block px-4 py-3 hover:bg-gray-50 cursor-pointer"
                      onClick={() => setIsOpen(false)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 mt-1">
                          {getResultIcon(result.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {result.title}
                            </p>
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {getResultTypeLabel(result.type)}
                            </span>
                          </div>
                          {result.description && (
                            <p className="text-sm text-gray-600 truncate mt-1">
                              {result.description}
                            </p>
                          )}
                          {result.instructor && (
                            <p className="text-xs text-gray-500 mt-1">
                              par {result.instructor}
                            </p>
                          )}
                        </div>
                      </div>
                    </Link>
                  ))}
                  
                  {/* Show all results link */}
                  <div className="border-t border-gray-100 px-4 py-3">
                    <button
                      onClick={() => handleSearch()}
                      className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Voir tous les résultats pour "{query}"
                    </button>
                  </div>
                </div>
              ) : (
                <div className="px-4 py-6 text-center">
                  <MagnifyingGlassIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Aucun résultat trouvé</p>
                  <button
                    onClick={() => handleSearch()}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium mt-2"
                  >
                    Rechercher "{query}" dans tous les cours
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}