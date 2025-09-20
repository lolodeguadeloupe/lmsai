'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import { 
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  CloudArrowDownIcon,
  CogIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  DocumentTextIcon,
  FilmIcon,
  PhotoIcon,
  ArchiveBoxIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useCourse } from '@/lib/hooks/useCourses';
import { coursesApi } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface ExportOptions {
  format: 'scorm2004' | 'xapi' | 'pdf' | 'html';
  includeAssessments: boolean;
  includeMultimedia: boolean;
  includeInteractivity: boolean;
  compression: 'none' | 'zip' | 'gzip';
  language: string;
}

const EXPORT_FORMATS = [
  {
    id: 'scorm2004' as const,
    name: 'SCORM 2004',
    description: 'Standard pour LMS compatibles SCORM',
    icon: ArchiveBoxIcon,
    features: ['Tracking des progrès', 'Compatible LMS', 'Interactivité complète'],
    fileSize: '~15-25 MB',
    recommended: true,
  },
  {
    id: 'xapi' as const,
    name: 'xAPI (Tin Can)',
    description: 'Format moderne pour analytics avancés',
    icon: CloudArrowDownIcon,
    features: ['Analytics détaillés', 'Expériences mobiles', 'Hors ligne possible'],
    fileSize: '~10-20 MB',
    recommended: false,
  },
  {
    id: 'pdf' as const,
    name: 'PDF',
    description: 'Document statique pour impression',
    icon: DocumentTextIcon,
    features: ['Portable', 'Imprimable', 'Lecture hors ligne'],
    fileSize: '~2-5 MB',
    recommended: false,
  },
  {
    id: 'html' as const,
    name: 'HTML/Web',
    description: 'Site web autonome',
    icon: DocumentArrowDownIcon,
    features: ['Compatible navigateurs', 'Responsive', 'Hébergement simple'],
    fileSize: '~5-10 MB',
    recommended: false,
  },
];

export default function CourseExportPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;
  
  const { data: course, isLoading, error } = useCourse(courseId);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'scorm2004',
    includeAssessments: true,
    includeMultimedia: true,
    includeInteractivity: true,
    compression: 'zip',
    language: 'fr',
  });
  
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const handleFormatChange = (format: ExportOptions['format']) => {
    setExportOptions(prev => ({ ...prev, format }));
  };

  const handleOptionChange = (key: keyof ExportOptions, value: any) => {
    setExportOptions(prev => ({ ...prev, [key]: value }));
  };

  const startExport = async () => {
    if (!course) return;

    setIsExporting(true);
    setExportProgress(0);
    setDownloadUrl(null);

    try {
      // Simuler le progrès d'export
      const progressInterval = setInterval(() => {
        setExportProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + Math.random() * 10;
        });
      }, 500);

      // Appel API pour export
      const response = await coursesApi.exportCourse(courseId, exportOptions.format);
      
      clearInterval(progressInterval);
      setExportProgress(100);
      setDownloadUrl(response.download_url);
      
      toast.success('Export terminé avec succès !');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Erreur lors de l\'export du cours');
    } finally {
      setIsExporting(false);
    }
  };

  const getEstimatedSize = () => {
    const selectedFormat = EXPORT_FORMATS.find(f => f.id === exportOptions.format);
    return selectedFormat?.fileSize || '~5-10 MB';
  };

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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Link href={`/courses/${courseId}`}>
              <Button variant="outline" size="sm" className="mr-4">
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Retour
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Exporter le cours</h1>
              <p className="text-gray-600 mt-2">
                {course.title}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Export Configuration */}
          <div className="lg:col-span-2 space-y-6">
            {/* Format Selection */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <CogIcon className="w-6 h-6 mr-2 text-blue-600" />
                Choisir le format
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {EXPORT_FORMATS.map((format) => (
                  <label key={format.id} className="cursor-pointer">
                    <input
                      type="radio"
                      name="format"
                      value={format.id}
                      checked={exportOptions.format === format.id}
                      onChange={() => handleFormatChange(format.id)}
                      className="sr-only"
                    />
                    <div className={`p-4 border-2 rounded-lg transition-all relative ${
                      exportOptions.format === format.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}>
                      {format.recommended && (
                        <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                          Recommandé
                        </span>
                      )}
                      <div className="flex items-center justify-center mb-3">
                        <format.icon className={`w-8 h-8 ${
                          exportOptions.format === format.id ? 'text-blue-600' : 'text-gray-400'
                        }`} />
                      </div>
                      <h3 className="font-semibold text-center mb-2">{format.name}</h3>
                      <p className="text-sm text-gray-600 text-center mb-3">{format.description}</p>
                      <ul className="text-xs text-gray-500 space-y-1">
                        {format.features.map((feature, index) => (
                          <li key={index} className="flex items-center">
                            <CheckIcon className="w-3 h-3 mr-1 text-green-500" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                      <div className="text-xs text-gray-500 mt-2 text-center">
                        Taille: {format.fileSize}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </Card>

            {/* Export Options */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">Options d'export</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900">Inclure les évaluations</label>
                    <p className="text-sm text-gray-600">Quiz et exercices interactifs</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeAssessments}
                      onChange={(e) => handleOptionChange('includeAssessments', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900">Inclure le multimédia</label>
                    <p className="text-sm text-gray-600">Images, vidéos et autres médias</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeMultimedia}
                      onChange={(e) => handleOptionChange('includeMultimedia', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900">Interactivité complète</label>
                    <p className="text-sm text-gray-600">Suivi des progrès et interactions</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeInteractivity}
                      onChange={(e) => handleOptionChange('includeInteractivity', e.target.checked)}
                      className="sr-only peer"
                      disabled={exportOptions.format === 'pdf'}
                    />
                    <div className={`w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 ${
                      exportOptions.format === 'pdf' ? 'opacity-50 cursor-not-allowed' : ''
                    }`}></div>
                  </label>
                </div>

                <div>
                  <label className="block font-medium text-gray-900 mb-2">Compression</label>
                  <select
                    value={exportOptions.compression}
                    onChange={(e) => handleOptionChange('compression', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="zip">ZIP (recommandé)</option>
                    <option value="gzip">GZIP</option>
                    <option value="none">Aucune compression</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-gray-900 mb-2">Langue</label>
                  <select
                    value={exportOptions.language}
                    onChange={(e) => handleOptionChange('language', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="fr">Français</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="de">Deutsch</option>
                  </select>
                </div>
              </div>
            </Card>

            {/* Export Progress */}
            {isExporting && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Export en cours...</h2>
                <div className="space-y-4">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Progression</span>
                    <span>{Math.round(exportProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${exportProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600">
                    Génération du package d'export...
                  </p>
                </div>
              </Card>
            )}

            {/* Download Ready */}
            {downloadUrl && (
              <Card className="p-6 bg-green-50 border-green-200">
                <div className="flex items-center mb-4">
                  <CheckIcon className="w-6 h-6 text-green-600 mr-2" />
                  <h2 className="text-xl font-semibold text-green-900">Export terminé !</h2>
                </div>
                <p className="text-green-800 mb-4">
                  Votre cours a été exporté avec succès. Le téléchargement va commencer automatiquement.
                </p>
                <div className="flex space-x-3">
                  <a
                    href={downloadUrl}
                    download
                    className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                    Télécharger maintenant
                  </a>
                  <Button variant="outline" onClick={() => setDownloadUrl(null)}>
                    Nouvel export
                  </Button>
                </div>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Export Summary */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Résumé de l'export</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Format</span>
                  <span className="font-medium">
                    {EXPORT_FORMATS.find(f => f.id === exportOptions.format)?.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Taille estimée</span>
                  <span className="font-medium">{getEstimatedSize()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Chapitres</span>
                  <span className="font-medium">{course.chapters?.length || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Évaluations</span>
                  <span className="font-medium">
                    {exportOptions.includeAssessments ? 'Incluses' : 'Exclues'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Multimédia</span>
                  <span className="font-medium">
                    {exportOptions.includeMultimedia ? 'Inclus' : 'Exclu'}
                  </span>
                </div>
              </div>
            </Card>

            {/* Help & Info */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center">
                <InformationCircleIcon className="w-5 h-5 mr-2 text-blue-600" />
                Aide & informations
              </h3>
              <div className="space-y-3 text-sm text-gray-600">
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">SCORM 2004</h4>
                  <p>Compatible avec la plupart des LMS (Moodle, Canvas, Blackboard)</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">xAPI</h4>
                  <p>Pour des analytics avancés et expériences modernes</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">PDF</h4>
                  <p>Document statique pour impression ou lecture hors ligne</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">HTML</h4>
                  <p>Site web autonome hébergeable sur n'importe quel serveur</p>
                </div>
              </div>
            </Card>

            {/* Action Button */}
            <Card className="p-6">
              <Button
                onClick={startExport}
                disabled={isExporting}
                className="w-full bg-blue-600 hover:bg-blue-700"
                size="lg"
              >
                {isExporting ? (
                  <>
                    <Loading size="sm" className="mr-2" />
                    Export en cours...
                  </>
                ) : (
                  <>
                    <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
                    Démarrer l'export
                  </>
                )}
              </Button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}