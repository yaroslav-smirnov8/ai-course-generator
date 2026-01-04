// src/types/lessonPlan.ts
export interface TeachingMethod {
  id: string;
  name: string;
  description: string;
  features: string[];
  applicableLanguages?: string[];
}

export interface LessonPlanFormData {
  language: string;
  level: string;
  topic: string;
  duration: number;
  methodologies: {
    mainMethod: string;
    supportMethods: string[];
  };
  teachingMethodology: string;
  objectives: string[];
  materials: string[];
  assessment: 'formative' | 'summative' | 'none';
  format: 'online' | 'offline' | 'hybrid';
  culturalElements: boolean;
}

export interface ValidationResult {
  errors: string[];
  warnings: string[];
}
