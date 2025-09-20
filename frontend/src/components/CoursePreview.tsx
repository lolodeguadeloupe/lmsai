'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  BookOpenIcon,
  SparklesIcon,
  ClockIcon,
  PlayIcon,
  CheckIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Course, GenerationStatus } from '@/lib/api';

interface CoursePreviewProps {
  courseId: string;
  generationStatus?: GenerationStatus;
  onRefresh?: () => void;
}

export default function CoursePreview({ courseId, generationStatus, onRefresh }: CoursePreviewProps) {
  const [previewData, setPreviewData] = useState({
    outline: null,
    chapters: [],
    currentChapter: null,
  });

  useEffect(() => {
    // Simulate receiving preview data during generation
    if (generationStatus?.status === 'in_progress') {
      const progress = generationStatus.progress_percentage;
      
      // Generate preview content based on progress
      if (progress >= 20) {
        setPreviewData(prev => ({
          ...prev,
          outline: {
            title: 'Aperçu de la structure',
            chapters: [
              'Introduction et concepts de base',
              'Méthodologie et bonnes pratiques',
              'Cas pratiques et exercices',
              'Projet final et évaluation'
            ]
          }
        }));
      }

      if (progress >= 40) {
        setPreviewData(prev => ({
          ...prev,
          chapters: [
            {
              id: '1',
              title: 'Introduction et concepts de base',
              status: 'generated',
              duration: 45,
              content: 'Ce chapitre introduit les concepts fondamentaux...'
            }
          ]
        }));
      }

      if (progress >= 60) {
        setPreviewData(prev => ({
          ...prev,
          chapters: [
            ...prev.chapters,
            {
              id: '2',
              title: 'Méthodologie et bonnes pratiques',
              status: 'generating',
              duration: 60,
              content: 'Génération en cours...'
            }
          ]
        }));
      }
    }
  }, [generationStatus]);

  const getChapterStatusIcon = (status: string) => {
    switch (status) {
      case 'generated':
        return <CheckIcon className="w-4 h-4 text-green-500" />;
      case 'generating':
        return <SparklesIcon className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Aperçu en temps réel</h3>
        {onRefresh && (
          <Button variant="outline" size="sm" onClick={onRefresh}>
            Actualiser
          </Button>
        )}
      </div>

      {/* Generation Status */}
      {generationStatus && (
        <Card className="p-4">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              generationStatus.status === 'in_progress' ? 'bg-blue-500 animate-pulse' :
              generationStatus.status === 'completed' ? 'bg-green-500' :
              generationStatus.status === 'failed' ? 'bg-red-500' : 'bg-gray-400'
            }`} />
            <div className="flex-1">
              <p className="font-medium">
                {generationStatus.current_phase || 'Génération en cours...'}
              </p>
              <div className="flex items-center space-x-2 mt-1">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${generationStatus.progress_percentage}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600">
                  {generationStatus.progress_percentage}%
                </span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Course Outline Preview */}
      {previewData.outline && (
        <Card className="p-6">
          <div className="flex items-center mb-4">
            <BookOpenIcon className="w-5 h-5 text-blue-500 mr-2" />
            <h4 className="font-semibold">{previewData.outline.title}</h4>
          </div>
          <ul className="space-y-2">
            {previewData.outline.chapters.map((chapter, index) => (
              <li key={index} className="flex items-center text-gray-700">
                <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full text-xs flex items-center justify-center mr-3">
                  {index + 1}
                </span>
                {chapter}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Generated Chapters */}
      {previewData.chapters.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-semibold">Chapitres générés</h4>
          {previewData.chapters.map((chapter: any) => (
            <Card key={chapter.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    {getChapterStatusIcon(chapter.status)}
                    <h5 className="font-medium">{chapter.title}</h5>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {chapter.content}
                  </p>
                  <div className="flex items-center text-xs text-gray-500">
                    <ClockIcon className="w-4 h-4 mr-1" />
                    {chapter.duration} minutes
                  </div>
                </div>
                {chapter.status === 'generated' && (
                  <Button variant="outline" size="sm">
                    <PlayIcon className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!previewData.outline && !previewData.chapters.length && (
        <Card className="p-8 text-center">
          <SparklesIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h4 className="font-medium text-gray-900 mb-2">
            Génération en attente
          </h4>
          <p className="text-gray-600 text-sm">
            L'aperçu apparaîtra ici au fur et à mesure de la génération du contenu.
          </p>
        </Card>
      )}
    </div>
  );
}