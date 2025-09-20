'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  SparklesIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  BookOpenIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { coursesApi } from '@/lib/api';
import { GenerationStatus } from '@/lib/api';
import CoursePreview from '@/components/CoursePreview';

export default function CourseGenerationPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = searchParams.get('task_id');
  
  const [status, setStatus] = useState<GenerationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pollGenerationStatus = useCallback(async (): Promise<void> => {
    try {
      const statusData = await coursesApi.getGenerationStatus(params.id);
      setStatus(statusData);
      setError(null);

      // If generation is complete, stop polling
      if (statusData.status === 'completed' || statusData.status === 'failed') {
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Error fetching generation status:', err);
      setError('Erreur lors de la récupération du statut');
    }
  }, [params.id]);

  useEffect(() => {
    if (!params.id) return () => {};

    // Initial fetch
    pollGenerationStatus();

    // Poll every 2 seconds while generation is in progress
    const interval = setInterval(() => {
      if (status?.status === 'pending' || status?.status === 'in_progress') {
        pollGenerationStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [params.id, status?.status, pollGenerationStatus]);

  const getStatusColor = (currentStatus: string) => {
    switch (currentStatus) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'in_progress':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (currentStatus: string) => {
    switch (currentStatus) {
      case 'completed':
        return <CheckIcon className="w-5 h-5" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-5 h-5" />;
      case 'in_progress':
        return <SparklesIcon className="w-5 h-5 animate-spin" />;
      default:
        return <ClockIcon className="w-5 h-5" />;
    }
  };

  const getStatusMessage = (currentStatus: string) => {
    switch (currentStatus) {
      case 'pending':
        return 'En attente de traitement...';
      case 'in_progress':
        return 'Génération en cours...';
      case 'completed':
        return 'Génération terminée avec succès !';
      case 'failed':
        return 'Échec de la génération';
      default:
        return 'Statut inconnu';
    }
  };

  if (error && !status) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8 max-w-md w-full text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Erreur</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link href="/courses">
            <Button>Retour aux cours</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Génération de votre cours
          </h1>
          <p className="text-gray-600">
            Notre IA travaille pour créer votre contenu personnalisé
          </p>
        </div>

        {/* Generation Status Card */}
        <Card className="p-8 mb-8">
          <div className="text-center">
            {/* Status Icon */}
            <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
              status ? getStatusColor(status.status) : 'text-gray-600 bg-gray-100'
            }`}>
              {status ? getStatusIcon(status.status) : <ClockIcon className="w-8 h-8" />}
            </div>

            {/* Status Message */}
            <h2 className="text-2xl font-semibold mb-2">
              {status ? getStatusMessage(status.status) : 'Chargement...'}
            </h2>

            {/* Current Phase */}
            {status?.current_phase && (
              <p className="text-gray-600 mb-4">
                Phase actuelle : <span className="font-medium">{status.current_phase}</span>
              </p>
            )}

            {/* Progress Bar */}
            {status && status.status !== 'failed' && (
              <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Progression</span>
                  <span>{status.progress_percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-500 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${status.progress_percentage}%` }}
                  />
                </div>
              </div>
            )}

            {/* Estimated Time */}
            {status?.estimated_time_remaining && status.status === 'in_progress' && (
              <p className="text-sm text-gray-500 mb-4">
                Temps estimé restant : {status.estimated_time_remaining}
              </p>
            )}

            {/* Error Message */}
            {status?.error_message && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-red-800">{status.error_message}</p>
              </div>
            )}

            {/* Task ID */}
            {taskId && (
              <p className="text-xs text-gray-400 mb-4">
                ID de tâche : {taskId}
              </p>
            )}
          </div>
        </Card>

        {/* Generation Steps */}
        <Card className="p-6 mb-8">
          <h3 className="text-lg font-semibold mb-4">Étapes de génération</h3>
          <div className="space-y-4">
            {[
              { name: 'Analyse du prompt', description: 'Compréhension de vos exigences' },
              { name: 'Structure du cours', description: 'Création de l\'architecture pédagogique' },
              { name: 'Génération du contenu', description: 'Rédaction des chapitres et exercices' },
              { name: 'Validation qualité', description: 'Vérification de la cohérence pédagogique' },
              { name: 'Finalisation', description: 'Préparation pour l\'exportation' },
            ].map((step, index) => {
              const isCompleted = status && status.progress_percentage > (index + 1) * 20;
              const isCurrent = status && 
                status.progress_percentage >= index * 20 && 
                status.progress_percentage < (index + 1) * 20;

              return (
                <div key={index} className="flex items-center space-x-4">
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    isCompleted 
                      ? 'bg-green-100 text-green-600'
                      : isCurrent 
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-400'
                  }`}>
                    {isCompleted ? (
                      <CheckIcon className="w-4 h-4" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`font-medium ${
                      isCompleted ? 'text-green-800' : isCurrent ? 'text-blue-800' : 'text-gray-600'
                    }`}>
                      {step.name}
                    </p>
                    <p className="text-sm text-gray-500">{step.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Real-time Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <CoursePreview 
            courseId={params.id}
            generationStatus={status}
            onRefresh={pollGenerationStatus}
          />
        </div>

        {/* Actions */}
        <div className="text-center space-y-4">
          {status?.status === 'completed' && (
            <div className="space-y-4">
              <Link href={`/courses/${params.id}`}>
                <Button size="lg" className="bg-green-600 hover:bg-green-700">
                  <BookOpenIcon className="w-5 h-5 mr-2" />
                  Voir le cours généré
                  <ArrowRightIcon className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          )}

          {status?.status === 'failed' && (
            <div className="space-y-4">
              <Link href="/courses/create">
                <Button variant="outline">
                  Essayer à nouveau
                </Button>
              </Link>
            </div>
          )}

          {(status?.status === 'pending' || status?.status === 'in_progress') && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Vous pouvez fermer cette page en toute sécurité. Vous recevrez une notification 
                lorsque la génération sera terminée.
              </p>
            </div>
          )}

          <Link href="/courses">
            <Button variant="outline">
              Retour aux cours
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}