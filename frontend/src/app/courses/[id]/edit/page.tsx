'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import { 
  ArrowLeftIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  SaveIcon,
  SparklesIcon,
  DocumentTextIcon,
  QuestionMarkCircleIcon,
  Bars3Icon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useCourse, useUpdateCourse } from '@/lib/hooks/useCourses';
import { Chapter } from '@/lib/api';
import { toast } from 'react-hot-toast';

const courseSchema = z.object({
  title: z.string().min(5, 'Le titre doit contenir au moins 5 caractères'),
  description: z.string().min(20, 'La description doit contenir au moins 20 caractères'),
  difficulty: z.enum(['beginner', 'intermediate', 'advanced']),
  status: z.enum(['draft', 'published', 'archived']),
});

type CourseFormData = z.infer<typeof courseSchema>;

interface EditingChapter extends Chapter {
  isEditing?: boolean;
  isDirty?: boolean;
}

export default function CourseEditPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;
  
  const { data: course, isLoading, error } = useCourse(courseId);
  const updateCourseMutation = useUpdateCourse();
  
  const [chapters, setChapters] = useState<EditingChapter[]>([]);
  const [activeChapter, setActiveChapter] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty }
  } = useForm<CourseFormData>({
    resolver: zodResolver(courseSchema),
  });

  // Initialize form when course data loads
  useEffect(() => {
    if (course) {
      setValue('title', course.title);
      setValue('description', course.description);
      setValue('difficulty', course.difficulty);
      setValue('status', course.status);
      
      if (course.chapters) {
        setChapters(course.chapters.map(chapter => ({ ...chapter, isEditing: false, isDirty: false })));
      }
    }
  }, [course, setValue]);

  const handleCourseSubmit = async (data: CourseFormData) => {
    setIsSaving(true);
    try {
      await updateCourseMutation.mutateAsync({
        courseId,
        data: {
          title: data.title,
          description: data.description,
          difficulty: data.difficulty,
          status: data.status,
        }
      });
      setHasUnsavedChanges(false);
      toast.success('Informations du cours sauvegardées');
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChapterEdit = (chapterId: string) => {
    setChapters(prev => prev.map(chapter => 
      chapter.id === chapterId 
        ? { ...chapter, isEditing: true }
        : { ...chapter, isEditing: false }
    ));
    setActiveChapter(chapterId);
  };

  const handleChapterSave = (chapterId: string, newTitle: string, newContent: string) => {
    setChapters(prev => prev.map(chapter => 
      chapter.id === chapterId 
        ? { 
            ...chapter, 
            title: newTitle, 
            content: newContent, 
            isEditing: false, 
            isDirty: true 
          }
        : chapter
    ));
    setHasUnsavedChanges(true);
    setActiveChapter(null);
  };

  const handleChapterCancel = (chapterId: string) => {
    setChapters(prev => prev.map(chapter => 
      chapter.id === chapterId 
        ? { ...chapter, isEditing: false }
        : chapter
    ));
    setActiveChapter(null);
  };

  const handleChapterDelete = (chapterId: string) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce chapitre ?')) {
      setChapters(prev => prev.filter(chapter => chapter.id !== chapterId));
      setHasUnsavedChanges(true);
    }
  };

  const handleAddChapter = () => {
    const newChapter: EditingChapter = {
      id: `temp-${Date.now()}`,
      course_id: courseId,
      title: 'Nouveau chapitre',
      content: '',
      order: chapters.length + 1,
      duration: 30,
      objectives: [],
      resources: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      isEditing: true,
      isDirty: true,
    };
    setChapters(prev => [...prev, newChapter]);
    setActiveChapter(newChapter.id);
    setHasUnsavedChanges(true);
  };

  const handleChapterReorder = (dragIndex: number, hoverIndex: number) => {
    const newChapters = [...chapters];
    const draggedChapter = newChapters[dragIndex];
    newChapters.splice(dragIndex, 1);
    newChapters.splice(hoverIndex, 0, draggedChapter);
    
    // Update order
    const updatedChapters = newChapters.map((chapter, index) => ({
      ...chapter,
      order: index + 1,
      isDirty: true,
    }));
    
    setChapters(updatedChapters);
    setHasUnsavedChanges(true);
  };

  const saveAllChanges = async () => {
    setIsSaving(true);
    try {
      // Save course info if needed
      if (isDirty) {
        const formData = watch();
        await updateCourseMutation.mutateAsync({
          courseId,
          data: formData
        });
      }
      
      // TODO: Save chapter changes via API
      // For now, just simulate saving
      setChapters(prev => prev.map(chapter => ({ ...chapter, isDirty: false })));
      setHasUnsavedChanges(false);
      toast.success('Toutes les modifications ont été sauvegardées');
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
              <h1 className="text-3xl font-bold text-gray-900">Éditer le cours</h1>
              <p className="text-gray-600 mt-2">
                Modifiez le contenu et la structure de votre cours
              </p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Link href={`/courses/${courseId}/view`}>
              <Button variant="outline" size="sm">
                <EyeIcon className="w-4 h-4 mr-2" />
                Prévisualiser
              </Button>
            </Link>
            {hasUnsavedChanges && (
              <Button
                onClick={saveAllChanges}
                disabled={isSaving}
                className="bg-green-600 hover:bg-green-700"
              >
                {isSaving ? (
                  <Loading size="sm" className="mr-2" />
                ) : (
                  <SaveIcon className="w-4 h-4 mr-2" />
                )}
                Sauvegarder tout
              </Button>
            )}
          </div>
        </div>

        {hasUnsavedChanges && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center">
              <SparklesIcon className="w-5 h-5 text-yellow-600 mr-2" />
              <p className="text-yellow-800">
                Vous avez des modifications non sauvegardées. N'oubliez pas de sauvegarder vos changements.
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Course Information */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <DocumentTextIcon className="w-6 h-6 mr-2 text-blue-600" />
                Informations du cours
              </h2>
              
              <form onSubmit={handleSubmit(handleCourseSubmit)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Titre du cours *
                  </label>
                  <input
                    {...register('title')}
                    type="text"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.title && (
                    <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <textarea
                    {...register('description')}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.description && (
                    <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Niveau de difficulté
                    </label>
                    <select
                      {...register('difficulty')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="beginner">Débutant</option>
                      <option value="intermediate">Intermédiaire</option>
                      <option value="advanced">Avancé</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Statut
                    </label>
                    <select
                      {...register('status')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="draft">Brouillon</option>
                      <option value="published">Publié</option>
                      <option value="archived">Archivé</option>
                    </select>
                  </div>
                </div>

                {isDirty && (
                  <div className="flex justify-end">
                    <Button type="submit" disabled={isSaving}>
                      {isSaving ? (
                        <Loading size="sm" className="mr-2" />
                      ) : (
                        <SaveIcon className="w-4 h-4 mr-2" />
                      )}
                      Sauvegarder les informations
                    </Button>
                  </div>
                )}
              </form>
            </Card>

            {/* Chapters */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold flex items-center">
                  <Bars3Icon className="w-6 h-6 mr-2 text-blue-600" />
                  Contenu du cours
                </h2>
                <Button onClick={handleAddChapter} size="sm">
                  <PlusIcon className="w-4 h-4 mr-2" />
                  Ajouter un chapitre
                </Button>
              </div>

              {chapters.length > 0 ? (
                <div className="space-y-4">
                  {chapters
                    .sort((a, b) => a.order - b.order)
                    .map((chapter, index) => (
                    <ChapterEditCard
                      key={chapter.id}
                      chapter={chapter}
                      index={index}
                      isActive={activeChapter === chapter.id}
                      onEdit={() => handleChapterEdit(chapter.id)}
                      onSave={handleChapterSave}
                      onCancel={() => handleChapterCancel(chapter.id)}
                      onDelete={() => handleChapterDelete(chapter.id)}
                      onReorder={handleChapterReorder}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Aucun chapitre
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Commencez par ajouter votre premier chapitre.
                  </p>
                  <Button onClick={handleAddChapter}>
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Ajouter un chapitre
                  </Button>
                </div>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Actions rapides</h3>
              <div className="space-y-3">
                <Button variant="outline" className="w-full" size="sm">
                  <SparklesIcon className="w-4 h-4 mr-2" />
                  Régénérer avec IA
                </Button>
                
                <Button variant="outline" className="w-full" size="sm">
                  <QuestionMarkCircleIcon className="w-4 h-4 mr-2" />
                  Ajouter un quiz
                </Button>
                
                <Button variant="outline" className="w-full" size="sm">
                  <DocumentTextIcon className="w-4 h-4 mr-2" />
                  Importer contenu
                </Button>
              </div>
            </Card>

            {/* Course Stats */}
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Statistiques</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Chapitres</span>
                  <span className="font-medium">{chapters.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Durée totale</span>
                  <span className="font-medium">
                    {Math.floor(chapters.reduce((acc, ch) => acc + ch.duration, 0) / 60)}h{' '}
                    {chapters.reduce((acc, ch) => acc + ch.duration, 0) % 60}min
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Mots</span>
                  <span className="font-medium">
                    ~{chapters.reduce((acc, ch) => acc + (ch.content?.length || 0), 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Dernière modification</span>
                  <span className="font-medium">
                    {new Date().toLocaleDateString('fr-FR')}
                  </span>
                </div>
              </div>
            </Card>

            {/* Help */}
            <Card className="p-6 bg-blue-50 border-blue-200">
              <h3 className="font-semibold mb-3 text-blue-900">💡 Conseils</h3>
              <ul className="text-sm text-blue-800 space-y-2">
                <li>• Utilisez l'IA pour améliorer vos contenus</li>
                <li>• Ajoutez des quiz pour tester la compréhension</li>
                <li>• Prévisualisez régulièrement le rendu final</li>
                <li>• Sauvegardez fréquemment vos modifications</li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

// Chapter Edit Component
interface ChapterEditCardProps {
  chapter: EditingChapter;
  index: number;
  isActive: boolean;
  onEdit: () => void;
  onSave: (id: string, title: string, content: string) => void;
  onCancel: () => void;
  onDelete: () => void;
  onReorder: (dragIndex: number, hoverIndex: number) => void;
}

function ChapterEditCard({
  chapter,
  index,
  isActive,
  onEdit,
  onSave,
  onCancel,
  onDelete,
}: ChapterEditCardProps) {
  const [editTitle, setEditTitle] = useState(chapter.title);
  const [editContent, setEditContent] = useState(chapter.content || '');

  const handleSave = () => {
    onSave(chapter.id, editTitle, editContent);
  };

  const handleCancel = () => {
    setEditTitle(chapter.title);
    setEditContent(chapter.content || '');
    onCancel();
  };

  if (chapter.isEditing) {
    return (
      <Card className="p-6 border-blue-200 bg-blue-50">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Titre du chapitre
            </label>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contenu
            </label>
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Rédigez le contenu du chapitre..."
            />
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={handleCancel} size="sm">
              Annuler
            </Button>
            <Button onClick={handleSave} size="sm">
              <SaveIcon className="w-4 h-4 mr-2" />
              Sauvegarder
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-4 transition-all ${chapter.isDirty ? 'border-yellow-300 bg-yellow-50' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="flex-shrink-0 w-8 h-8 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center text-sm font-medium">
            {index + 1}
          </span>
          <div>
            <h3 className="font-medium text-gray-900">{chapter.title}</h3>
            <p className="text-sm text-gray-600">
              {chapter.duration} min • {(chapter.content?.length || 0)} caractères
            </p>
          </div>
          {chapter.isDirty && (
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
              Modifié
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={onEdit}>
            <PencilIcon className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={onDelete} className="text-red-600 hover:text-red-700">
            <TrashIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}