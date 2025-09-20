'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Loading } from '@/components/ui/loading';
import { 
  SparklesIcon,
  BookOpenIcon,
  AcademicCapIcon,
  ClockIcon,
  ArrowLeftIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { CreateCourseRequest } from '@/types';
import { toast } from 'react-hot-toast';
import { coursesApi } from '@/lib/api';

const courseSchema = z.object({
  title: z.string().min(5, 'Le titre doit contenir au moins 5 caractères'),
  description: z.string().min(20, 'La description doit contenir au moins 20 caractères'),
  difficulty: z.enum(['beginner', 'intermediate', 'advanced']),
  categoryId: z.string().min(1, 'Veuillez sélectionner une catégorie'),
  tags: z.array(z.string()).min(1, 'Ajoutez au moins un tag'),
  aiPrompt: z.string().min(10, 'Le prompt IA doit contenir au moins 10 caractères'),
  estimatedDuration: z.number().min(30, 'La durée doit être d\'au moins 30 minutes'),
  targetAudience: z.string().min(5, 'Décrivez l\'audience cible'),
});

type CourseFormData = z.infer<typeof courseSchema>;

const CATEGORIES = [
  { id: '1', name: 'Technologie', slug: 'technology' },
  { id: '2', name: 'Business', slug: 'business' },
  { id: '3', name: 'Design', slug: 'design' },
  { id: '4', name: 'Marketing', slug: 'marketing' },
  { id: '5', name: 'Sciences', slug: 'sciences' },
  { id: '6', name: 'Langues', slug: 'languages' },
];

const POPULAR_TAGS = [
  'JavaScript', 'Python', 'React', 'Machine Learning', 'Design',
  'Marketing Digital', 'Entrepreneuriat', 'Leadership', 'Communication',
  'Gestion de projet', 'Analytics', 'UX/UI'
];

export default function CreateCoursePage() {
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [customTag, setCustomTag] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid }
  } = useForm<CourseFormData>({
    resolver: zodResolver(courseSchema),
    mode: 'onChange',
    defaultValues: {
      difficulty: 'beginner',
      tags: [],
      estimatedDuration: 120,
    }
  });

  const difficulty = watch('difficulty');
  const aiPrompt = watch('aiPrompt');

  const addTag = (tag: string) => {
    if (tag && !selectedTags.includes(tag)) {
      const newTags = [...selectedTags, tag];
      setSelectedTags(newTags);
      setValue('tags', newTags, { shouldValidate: true });
    }
    setCustomTag('');
  };

  const removeTag = (tagToRemove: string) => {
    const newTags = selectedTags.filter(tag => tag !== tagToRemove);
    setSelectedTags(newTags);
    setValue('tags', newTags, { shouldValidate: true });
  };

  const onSubmit = async (data: CourseFormData) => {
    setIsGenerating(true);
    try {
      // Create course via API
      const response = await coursesApi.create({
        title: data.title,
        description: data.description,
        difficulty: data.difficulty,
        categoryId: data.categoryId,
        tags: data.tags,
        targetAudience: data.targetAudience,
        estimatedDuration: data.estimatedDuration,
        aiPrompt: data.aiPrompt
      });

      console.log('Course creation initiated:', response);
      toast.success('Génération du cours initiée !');
      
      // Redirect to course generation status page
      router.push(`/courses/${response.id}/generation?task_id=${response.task_id}`);
    } catch (error) {
      console.error('Error creating course:', error);
      toast.error('Erreur lors de la création du cours');
    } finally {
      setIsGenerating(false);
    }
  };

  const getDifficultyDescription = (level: string) => {
    switch (level) {
      case 'beginner':
        return 'Aucun prérequis. Parfait pour débuter dans le domaine.';
      case 'intermediate':
        return 'Quelques bases requises. Pour approfondir ses connaissances.';
      case 'advanced':
        return 'Solides connaissances requises. Pour les experts.';
      default:
        return '';
    }
  };

  const steps = [
    { 
      number: 1, 
      title: 'Informations de base',
      description: 'Titre, description et niveau du cours'
    },
    { 
      number: 2, 
      title: 'Catégorie et tags',
      description: 'Classification et mots-clés'
    },
    { 
      number: 3, 
      title: 'Génération IA',
      description: 'Prompt et paramètres pour l\'IA'
    },
  ];

  if (isGenerating) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8 max-w-md w-full text-center">
          <div className="animate-spin w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-6"></div>
          <h2 className="text-xl font-semibold mb-2">Génération en cours...</h2>
          <p className="text-gray-600 mb-4">
            Notre IA crée votre cours personnalisé. Cela peut prendre quelques minutes.
          </p>
          <div className="bg-gray-200 rounded-full h-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '75%' }}></div>
          </div>
          <p className="text-sm text-gray-500 mt-2">Génération du contenu...</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Link href="/courses">
            <Button variant="outline" size="sm" className="mr-4">
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Retour
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Créer un nouveau cours</h1>
            <p className="text-gray-600 mt-2">
              Utilisez l'IA pour générer un cours complet en quelques minutes
            </p>
          </div>
        </div>

        {/* Progress Steps */}
        <Card className="p-6 mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  currentStep >= step.number 
                    ? 'bg-blue-500 border-blue-500 text-white' 
                    : 'border-gray-300 text-gray-500'
                }`}>
                  {currentStep > step.number ? (
                    <CheckIcon className="w-5 h-5" />
                  ) : (
                    step.number
                  )}
                </div>
                <div className="ml-3 min-w-0 flex-1">
                  <p className={`text-sm font-medium ${
                    currentStep >= step.number ? 'text-blue-600' : 'text-gray-500'
                  }`}>
                    {step.title}
                  </p>
                  <p className="text-xs text-gray-500">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-0.5 mx-4 ${
                    currentStep > step.number ? 'bg-blue-500' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </Card>

        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <Card className="p-8">
              <div className="space-y-6">
                <div className="flex items-center mb-6">
                  <BookOpenIcon className="w-6 h-6 text-blue-500 mr-2" />
                  <h2 className="text-xl font-semibold">Informations de base</h2>
                </div>

                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Titre du cours *
                  </label>
                  <input
                    {...register('title')}
                    type="text"
                    placeholder="Ex: Introduction au Machine Learning"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.title && (
                    <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
                  )}
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description du cours *
                  </label>
                  <textarea
                    {...register('description')}
                    rows={4}
                    placeholder="Décrivez ce que les étudiants vont apprendre dans ce cours..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.description && (
                    <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
                  )}
                </div>

                {/* Difficulty */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Niveau de difficulté *
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { value: 'beginner', label: 'Débutant', icon: '🌱' },
                      { value: 'intermediate', label: 'Intermédiaire', icon: '🌿' },
                      { value: 'advanced', label: 'Avancé', icon: '🌳' },
                    ].map((level) => (
                      <label key={level.value} className="cursor-pointer">
                        <input
                          {...register('difficulty')}
                          type="radio"
                          value={level.value}
                          className="sr-only"
                        />
                        <div className={`p-4 border-2 rounded-lg transition-all ${
                          difficulty === level.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}>
                          <div className="flex items-center justify-center text-2xl mb-2">
                            {level.icon}
                          </div>
                          <h3 className="font-medium text-center mb-1">{level.label}</h3>
                          <p className="text-sm text-gray-600 text-center">
                            {getDifficultyDescription(level.value)}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Target Audience */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Audience cible *
                  </label>
                  <input
                    {...register('targetAudience')}
                    type="text"
                    placeholder="Ex: Développeurs débutants, étudiants en informatique..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.targetAudience && (
                    <p className="text-red-500 text-sm mt-1">{errors.targetAudience.message}</p>
                  )}
                </div>

                {/* Estimated Duration */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Durée estimée (minutes) *
                  </label>
                  <div className="flex items-center">
                    <ClockIcon className="w-5 h-5 text-gray-400 mr-2" />
                    <input
                      {...register('estimatedDuration', { valueAsNumber: true })}
                      type="number"
                      min="30"
                      step="15"
                      className="w-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <span className="ml-2 text-gray-600">minutes</span>
                  </div>
                  {errors.estimatedDuration && (
                    <p className="text-red-500 text-sm mt-1">{errors.estimatedDuration.message}</p>
                  )}
                </div>

                <div className="flex justify-end">
                  <Button 
                    type="button" 
                    onClick={() => setCurrentStep(2)}
                    disabled={!watch('title') || !watch('description') || !watch('targetAudience')}
                  >
                    Suivant
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Step 2: Category and Tags */}
          {currentStep === 2 && (
            <Card className="p-8">
              <div className="space-y-6">
                <div className="flex items-center mb-6">
                  <AcademicCapIcon className="w-6 h-6 text-blue-500 mr-2" />
                  <h2 className="text-xl font-semibold">Catégorie et mots-clés</h2>
                </div>

                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Catégorie *
                  </label>
                  <select
                    {...register('categoryId')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Sélectionnez une catégorie</option>
                    {CATEGORIES.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                  {errors.categoryId && (
                    <p className="text-red-500 text-sm mt-1">{errors.categoryId.message}</p>
                  )}
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mots-clés *
                  </label>
                  
                  {/* Selected Tags */}
                  {selectedTags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {selectedTags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                        >
                          {tag}
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="ml-2 hover:text-blue-600"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Popular Tags */}
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-2">Tags populaires :</p>
                    <div className="flex flex-wrap gap-2">
                      {POPULAR_TAGS.map((tag) => (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => addTag(tag)}
                          disabled={selectedTags.includes(tag)}
                          className="px-3 py-1 text-sm border border-gray-300 rounded-full hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          + {tag}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Custom Tag Input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customTag}
                      onChange={(e) => setCustomTag(e.target.value)}
                      placeholder="Ajouter un tag personnalisé..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addTag(customTag);
                        }
                      }}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => addTag(customTag)}
                      disabled={!customTag}
                    >
                      Ajouter
                    </Button>
                  </div>

                  {errors.tags && (
                    <p className="text-red-500 text-sm mt-1">{errors.tags.message}</p>
                  )}
                </div>

                <div className="flex justify-between">
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={() => setCurrentStep(1)}
                  >
                    Précédent
                  </Button>
                  <Button 
                    type="button" 
                    onClick={() => setCurrentStep(3)}
                    disabled={!watch('categoryId') || selectedTags.length === 0}
                  >
                    Suivant
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Step 3: AI Generation */}
          {currentStep === 3 && (
            <Card className="p-8">
              <div className="space-y-6">
                <div className="flex items-center mb-6">
                  <SparklesIcon className="w-6 h-6 text-blue-500 mr-2" />
                  <h2 className="text-xl font-semibold">Configuration de l'IA</h2>
                </div>

                {/* AI Prompt */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Instructions pour l'IA *
                  </label>
                  <textarea
                    {...register('aiPrompt')}
                    rows={6}
                    placeholder="Décrivez en détail ce que vous voulez que l'IA génère. Plus vous êtes précis, meilleur sera le résultat.

Exemple : 'Créez un cours complet sur les bases du JavaScript pour débutants. Incluez des exemples pratiques, des exercices interactifs, et des projets concrets comme la création d'une calculatrice et d'un site web simple.'"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.aiPrompt && (
                    <p className="text-red-500 text-sm mt-1">{errors.aiPrompt.message}</p>
                  )}
                  <p className="text-sm text-gray-600 mt-2">
                    💡 Conseil : Mentionnez le style d'apprentissage souhaité, les compétences à acquérir, et les projets pratiques à inclure.
                  </p>
                </div>

                {/* AI Generation Preview */}
                {aiPrompt && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-medium text-blue-900 mb-2">Aperçu de génération</h3>
                    <p className="text-sm text-blue-800">
                      L'IA va créer un cours <strong>{getDifficultyDescription(difficulty).toLowerCase()}</strong> avec :
                    </p>
                    <ul className="list-disc list-inside text-sm text-blue-800 mt-2 space-y-1">
                      <li>Structure complète du cours avec chapitres</li>
                      <li>Contenu pédagogique adapté au niveau</li>
                      <li>Exercices et évaluations</li>
                      <li>Ressources complémentaires</li>
                    </ul>
                  </div>
                )}

                <div className="flex justify-between">
                  <Button 
                    type="button" 
                    variant="outline"
                    onClick={() => setCurrentStep(2)}
                  >
                    Précédent
                  </Button>
                  <Button 
                    type="submit"
                    disabled={!isValid || isGenerating}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {isGenerating ? (
                      <>
                        <Loading size="sm" className="mr-2" />
                        Génération...
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="w-4 h-4 mr-2" />
                        Générer le cours
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </form>
      </div>
    </div>
  );
}