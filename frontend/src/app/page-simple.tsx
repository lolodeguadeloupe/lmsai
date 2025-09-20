'use client';

import Link from 'next/link';
import { 
  SparklesIcon,
  AcademicCapIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="flex items-center space-x-2">
                <SparklesIcon className="h-8 w-8 text-blue-600" />
                <span className="text-xl font-bold text-gray-900">CourseGen AI</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/auth/signin" className="text-gray-600 hover:text-gray-900">
                Se connecter
              </Link>
              <Link href="/auth/signup" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                Commencer
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              Créez des cours exceptionnels
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                avec l'IA
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Transformez vos idées en cours complets et engageants en quelques minutes. 
              Notre IA génère du contenu pédagogique de qualité professionnelle.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/courses/create" className="bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors">
                Créer mon premier cours
              </Link>
              <Link href="/courses" className="border border-gray-300 text-gray-700 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-50 transition-colors">
                Voir les exemples
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Pourquoi choisir CourseGen AI ?
            </h2>
            <p className="text-xl text-gray-600">
              Une plateforme complète pour créer, gérer et diffuser vos formations
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <SparklesIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Génération IA Avancée</h3>
              <p className="text-gray-600">
                Transformez vos idées en cours complets grâce à l'intelligence artificielle avancée
              </p>
            </div>
            
            <div className="text-center p-6">
              <AcademicCapIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Qualité Pédagogique</h3>
              <p className="text-gray-600">
                Contenu optimisé pour l'apprentissage avec validation automatique de la qualité
              </p>
            </div>
            
            <div className="text-center p-6">
              <BookOpenIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Export Multi-format</h3>
              <p className="text-gray-600">
                Exportez vos cours en SCORM, xAPI, PDF ou HTML selon vos besoins
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}