// User and Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'instructor' | 'student';
  createdAt: string;
  updatedAt: string;
}

export interface AuthSession {
  user: User;
  accessToken: string;
  refreshToken: string;
}

// Course Types
export interface Course {
  id: string;
  title: string;
  description: string;
  thumbnailUrl?: string;
  status: 'draft' | 'published' | 'archived';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: number; // in minutes
  price: number;
  currency: string;
  tags: string[];
  instructorId: string;
  instructor: User;
  categoryId: string;
  category: Category;
  chapters: Chapter[];
  enrollments: Enrollment[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateCourseRequest {
  title: string;
  description: string;
  difficulty: Course['difficulty'];
  categoryId: string;
  tags: string[];
  aiPrompt?: string;
}

export interface UpdateCourseRequest extends Partial<CreateCourseRequest> {
  status?: Course['status'];
  price?: number;
  currency?: string;
}

// Chapter Types
export interface Chapter {
  id: string;
  title: string;
  description: string;
  content: string;
  videoUrl?: string;
  order: number;
  duration: number;
  courseId: string;
  lessons: Lesson[];
  quiz?: Quiz;
  createdAt: string;
  updatedAt: string;
}

export interface CreateChapterRequest {
  title: string;
  description: string;
  content: string;
  order: number;
  courseId: string;
}

// Lesson Types
export interface Lesson {
  id: string;
  title: string;
  content: string;
  videoUrl?: string;
  order: number;
  duration: number;
  chapterId: string;
  createdAt: string;
  updatedAt: string;
}

// Quiz Types
export interface Quiz {
  id: string;
  title: string;
  description: string;
  questions: Question[];
  timeLimit?: number; // in minutes
  attempts: number;
  passingScore: number;
  chapterId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Question {
  id: string;
  question: string;
  type: 'multiple_choice' | 'true_false' | 'short_answer';
  options?: string[];
  correctAnswer: string | string[];
  explanation?: string;
  points: number;
  order: number;
  quizId: string;
}

// Category Types
export interface Category {
  id: string;
  name: string;
  description: string;
  slug: string;
  parentId?: string;
  children?: Category[];
  courseCount: number;
  createdAt: string;
  updatedAt: string;
}

// Enrollment Types
export interface Enrollment {
  id: string;
  userId: string;
  user: User;
  courseId: string;
  course: Course;
  status: 'active' | 'completed' | 'cancelled';
  progress: number; // percentage
  startedAt: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

// Progress Tracking
export interface LessonProgress {
  id: string;
  userId: string;
  lessonId: string;
  completed: boolean;
  timeSpent: number; // in seconds
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface QuizAttempt {
  id: string;
  userId: string;
  quizId: string;
  answers: Record<string, string | string[]>;
  score: number;
  passed: boolean;
  startedAt: string;
  completedAt?: string;
  timeSpent: number; // in seconds
}

// AI Generation Types
export interface GenerationRequest {
  type: 'course' | 'chapter' | 'lesson' | 'quiz';
  prompt: string;
  context?: {
    courseId?: string;
    chapterId?: string;
    difficulty?: Course['difficulty'];
    duration?: number;
  };
}

export interface GenerationResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  type: GenerationRequest['type'];
  prompt: string;
  result?: any;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  error?: string;
}

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface FilterState {
  search?: string;
  category?: string;
  difficulty?: Course['difficulty'];
  status?: Course['status'];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// Form Types
export interface FormErrors {
  [key: string]: string | undefined;
}

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

// API Response Types
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}