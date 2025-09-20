import { create } from 'zustand';
import { Course, FilterState, PaginationState } from '@/types';

interface CoursesState {
  courses: Course[];
  selectedCourse: Course | null;
  filters: FilterState;
  pagination: PaginationState;
  isLoading: boolean;
  error: string | null;
  setCourses: (courses: Course[]) => void;
  addCourse: (course: Course) => void;
  updateCourse: (courseId: string, updates: Partial<Course>) => void;
  deleteCourse: (courseId: string) => void;
  setSelectedCourse: (course: Course | null) => void;
  setFilters: (filters: Partial<FilterState>) => void;
  setPagination: (pagination: Partial<PaginationState>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  resetFilters: () => void;
}

const initialFilters: FilterState = {
  search: '',
  category: '',
  sortBy: 'createdAt',
  sortOrder: 'desc',
};

const initialPagination: PaginationState = {
  page: 1,
  limit: 12,
  total: 0,
  totalPages: 0,
};

export const useCoursesStore = create<CoursesState>((set, get) => ({
  courses: [],
  selectedCourse: null,
  filters: initialFilters,
  pagination: initialPagination,
  isLoading: false,
  error: null,
  
  setCourses: (courses) => set({ courses }),
  
  addCourse: (course) =>
    set((state) => ({
      courses: [course, ...state.courses],
    })),
  
  updateCourse: (courseId, updates) =>
    set((state) => ({
      courses: state.courses.map((course) =>
        course.id === courseId ? { ...course, ...updates } : course
      ),
      selectedCourse:
        state.selectedCourse?.id === courseId
          ? { ...state.selectedCourse, ...updates }
          : state.selectedCourse,
    })),
  
  deleteCourse: (courseId) =>
    set((state) => ({
      courses: state.courses.filter((course) => course.id !== courseId),
      selectedCourse:
        state.selectedCourse?.id === courseId ? null : state.selectedCourse,
    })),
  
  setSelectedCourse: (course) => set({ selectedCourse: course }),
  
  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
      pagination: { ...state.pagination, page: 1 }, // Reset to first page when filtering
    })),
  
  setPagination: (pagination) =>
    set((state) => ({
      pagination: { ...state.pagination, ...pagination },
    })),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  resetFilters: () =>
    set({
      filters: initialFilters,
      pagination: initialPagination,
    }),
}));