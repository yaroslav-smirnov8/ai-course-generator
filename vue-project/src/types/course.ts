// src/types/course.ts

export interface CourseFormData {
  courseName: string;
  language: string;
  level: string;
  startLevel: string;
  targetAudience: string;
  lessonsCount: number;
  lessonDuration: number;
  mainTopics: string;
  grammarFocus: string;
  vocabularyFocus: string;
  includeSpeaking: boolean;
  includeListening: boolean;
  includeReading: boolean;
  includeWriting: boolean;
  includeGames: boolean;
  format: string;
  examPrep?: string;
  methodology: string;
  age?: string;
  interests?: string;
  goals?: string;
  commonMistakes?: string;
  customExam?: string;
  examPrepLessons?: number;
}

export interface Activity {
  id: number;
  name: string;
  type: string;
  duration: number;
  description: string;
  materials?: string[];
  objectives?: string[];
}

export interface Homework {
  description: string;
  tasks?: string[];
  estimatedTime?: number;
}

export interface Lesson {
  id: number;
  title: string;
  duration: number;
  objectives: string[];
  grammar: string[];
  vocabulary: string[];
  activities: Activity[];
  materials: string[];
  homework: Homework;
  order: number;
  isCompleted?: boolean;
}

export interface CourseStructure {
  id: number;
  name: string;
  language: string;
  level: string;
  startLevel?: string;
  targetAudience: string;
  format: string;
  totalDuration: number;
  lessons: Lesson[];
  examPrep?: string;
  progress?: number;
  completedLessons?: number;
  createdAt?: string;
  updatedAt?: string;
  description?: string;
  prerequisites?: string[];
  learningOutcomes?: string[];
  methodology?: string;
  studentAge?: string;
  studentInterests?: string;
  studentGoals?: string;
  commonMistakes?: string;
  customExam?: string;
  examPrepLessons?: number;
}

export interface LessonTemplate {
  id: number;
  name: string;
  type: string;
  structure: any;
  isDefault: boolean;
}

export interface MaterialsGenerationRequest {
  lessonId: number;
  types: string[];
  parameters?: {
    difficulty?: string;
    count?: number;
    topics?: string[];
    [key: string]: any;
  };
}

export interface ExportOptions {
  format: 'pdf' | 'docx';
  includeMaterials: boolean;
  includeAnswers: boolean;
  customization?: {
    logo?: string;
    color?: string;
    template?: string;
  };
}

export type CourseLevel = 'beginner' | 'elementary' | 'intermediate' | 'upper-intermediate' | 'advanced';

export type CourseFormat = 'online' | 'offline' | 'hybrid';

export type TargetAudience = 'children' | 'teens' | 'adults' | 'business';

// Интерфейс для ответа генерации упражнений
export interface GeneratedExercisesResponse {
  exercises_content: string;
}

// Интерфейс для ответа генерации игры (теперь содержит Markdown)
export interface GeneratedGameResponse {
  game_content: string;
  game_type?: string; // Тип игры может опционально возвращаться
}

export class CourseFormData {
}
