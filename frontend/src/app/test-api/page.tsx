'use client';

import { useState } from 'react';
import { coursesApi, CreateCourseRequest } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { toast } from 'react-hot-toast';

export default function TestApiPage() {
  const [loading, setLoading] = useState(false);
  const [courses, setCourses] = useState<any[]>([]);
  const [response, setResponse] = useState<string>('');

  const testConnection = async () => {
    setLoading(true);
    try {
      // Test de santé de l'API
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setResponse(JSON.stringify(data, null, 2));
      toast.success('Connexion API réussie !');
    } catch (error) {
      console.error('Erreur de connexion:', error);
      setResponse(`Erreur: ${error}`);
      toast.error('Erreur de connexion à l\'API');
    } finally {
      setLoading(false);
    }
  };

  const testGetCourses = async () => {
    setLoading(true);
    try {
      const data = await coursesApi.getAll();
      setCourses(data.data || []);
      setResponse(JSON.stringify(data, null, 2));
      toast.success('Récupération des cours réussie !');
    } catch (error) {
      console.error('Erreur:', error);
      setResponse(`Erreur: ${error}`);
      toast.error('Erreur lors de la récupération des cours');
    } finally {
      setLoading(false);
    }
  };

  const testCreateCourse = async () => {
    setLoading(true);
    try {
      const courseData: CreateCourseRequest = {
        title: "Test Course Frontend",
        description: "Cours de test créé depuis le frontend Next.js",
        difficulty: "beginner",
        categoryId: "1",
        tags: ["test", "frontend"],
        targetAudience: "Développeurs frontend",
        estimatedDuration: 120,
        aiPrompt: "Créez un cours simple sur les bases du développement frontend avec React et Next.js"
      };

      const result = await coursesApi.create(courseData);
      setResponse(JSON.stringify(result, null, 2));
      toast.success('Cours créé avec succès !');
      
      // Refresh courses list
      await testGetCourses();
    } catch (error) {
      console.error('Erreur:', error);
      setResponse(`Erreur: ${error}`);
      toast.error('Erreur lors de la création du cours');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Test API Integration
          </h1>
          <p className="text-gray-600">
            Test de l'intégration entre le frontend Next.js et l'API backend FastAPI
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Panel de contrôle */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">Tests API</h2>
            
            <div className="space-y-4">
              <Button
                onClick={testConnection}
                disabled={loading}
                className="w-full"
                variant="outline"
              >
                {loading ? 'Test en cours...' : 'Test Connexion API'}
              </Button>

              <Button
                onClick={testGetCourses}
                disabled={loading}
                className="w-full"
                variant="outline"
              >
                {loading ? 'Chargement...' : 'Récupérer les Cours'}
              </Button>

              <Button
                onClick={testCreateCourse}
                disabled={loading}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white"
              >
                {loading ? 'Création...' : 'Créer un Cours Test'}
              </Button>
            </div>

            {/* Liste des cours */}
            {courses.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-medium mb-3">Cours récupérés ({courses.length})</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {courses.map((course, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded border">
                      <div className="font-medium">{course.title}</div>
                      <div className="text-sm text-gray-600">{course.description}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        ID: {course.id} | Status: {course.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Réponse API */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">Réponse API</h2>
            
            {response ? (
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-96">
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  {response}
                </pre>
              </div>
            ) : (
              <div className="bg-gray-100 p-8 rounded-lg text-center text-gray-500">
                Aucune réponse pour le moment.
                <br />
                Exécutez un test pour voir la réponse API.
              </div>
            )}
          </Card>
        </div>

        {/* Informations de configuration */}
        <Card className="p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">Configuration</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <strong>URL API:</strong> {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
            </div>
            <div>
              <strong>Version API:</strong> {process.env.NEXT_PUBLIC_API_VERSION || 'v1'}
            </div>
            <div>
              <strong>Clé API:</strong> {process.env.NEXT_PUBLIC_API_KEY || 'test-api-key'}
            </div>
            <div>
              <strong>Environment:</strong> {process.env.NODE_ENV}
            </div>
          </div>
        </Card>

        {/* Instructions */}
        <Card className="p-6 mt-8 bg-blue-50 border-blue-200">
          <h2 className="text-xl font-semibold mb-4 text-blue-900">Instructions</h2>
          <div className="text-blue-800 space-y-2">
            <p>1. <strong>Démarrez le backend</strong> : <code className="bg-blue-100 px-2 py-1 rounded">cd backend && python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000</code></p>
            <p>2. <strong>Testez la connexion</strong> : Cliquez sur "Test Connexion API" pour vérifier que l'API est accessible</p>
            <p>3. <strong>Récupérez les cours</strong> : Testez l'endpoint GET /courses</p>
            <p>4. <strong>Créez un cours</strong> : Testez l'endpoint POST /courses avec génération IA</p>
          </div>
        </Card>
      </div>
    </div>
  );
}