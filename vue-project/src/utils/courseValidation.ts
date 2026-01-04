import type { CourseStructure, Lesson } from '@/types/course';

/**
 * Результат валидации курса
 */
export interface CourseValidationResult {
  isValid: boolean;
  missingFields: string[];
  lessonValidation: {
    validLessons: number;
    invalidLessons: number;
    missingFields: Record<number, string[]>;
  };
  score: number; // 0-100, качество данных
}

/**
 * Проверяет полноту и корректность структуры курса
 * @param course Структура курса для валидации
 * @returns Результат валидации
 */
export function validateCourseStructure(course?: CourseStructure | null): CourseValidationResult {
  if (!course) {
    return {
      isValid: false,
      missingFields: ['Курс отсутствует'],
      lessonValidation: {
        validLessons: 0,
        invalidLessons: 0,
        missingFields: {}
      },
      score: 0
    };
  }

  const result: CourseValidationResult = {
    isValid: true,
    missingFields: [],
    lessonValidation: {
      validLessons: 0,
      invalidLessons: 0,
      missingFields: {}
    },
    score: 100
  };

  // Проверяем обязательные поля курса
  const requiredCourseFields = [
    { field: 'id', name: 'ID курса' },
    { field: 'name', name: 'Название курса' },
    { field: 'language', name: 'Язык' },
    { field: 'level', name: 'Уровень' },
    { field: 'targetAudience', name: 'Целевая аудитория' },
    { field: 'format', name: 'Формат' },
    { field: 'lessons', name: 'Уроки' }
  ];

  // Проверяем каждое обязательное поле
  for (const { field, name } of requiredCourseFields) {
    if (!course[field as keyof CourseStructure]) {
      result.missingFields.push(name);
      result.isValid = false;
      result.score -= 10; // Снижаем оценку за каждое отсутствующее поле
    }
  }

  // Если уроки существуют, проверяем их
  if (course.lessons && Array.isArray(course.lessons)) {
    // Проверяем каждый урок
    course.lessons.forEach((lesson, index) => {
      const lessonValidation = validateLesson(lesson, index);
      
      if (lessonValidation.isValid) {
        result.lessonValidation.validLessons++;
      } else {
        result.lessonValidation.invalidLessons++;
        result.lessonValidation.missingFields[index] = lessonValidation.missingFields;
        
        // Снижаем общую оценку за каждый невалидный урок
        result.score -= 5 * (lessonValidation.missingFields.length / 2);
      }
    });

    // Если все уроки невалидны, снижаем общую валидность
    if (course.lessons.length > 0 && result.lessonValidation.validLessons === 0) {
      result.isValid = false;
      result.score -= 30;
    }
  } else {
    // Если уроков нет вообще
    result.missingFields.push('Уроки (отсутствует массив)');
    result.isValid = false;
    result.score -= 30;
  }

  // Обеспечиваем, что оценка в пределах 0-100
  result.score = Math.max(0, Math.min(100, result.score));

  return result;
}

/**
 * Проверяет полноту и корректность урока
 * @param lesson Урок для валидации
 * @param index Индекс урока в курсе
 * @returns Результат валидации
 */
export function validateLesson(lesson: Lesson, index: number): { isValid: boolean; missingFields: string[] } {
  const result = {
    isValid: true,
    missingFields: [] as string[]
  };

  // Проверяем обязательные поля урока
  const requiredLessonFields = [
    { field: 'id', name: 'ID урока' },
    { field: 'title', name: 'Название урока' },
    { field: 'objectives', name: 'Цели урока' },
    { field: 'grammar', name: 'Грамматика' },
    { field: 'vocabulary', name: 'Лексика' },
    { field: 'activities', name: 'Активности' }
  ];

  // Проверяем каждое обязательное поле
  for (const { field, name } of requiredLessonFields) {
    if (!lesson[field as keyof Lesson]) {
      result.missingFields.push(name);
      result.isValid = false;
    }
  }

  // Проверяем массивы, что они не пустые
  const arrayFields = ['objectives', 'grammar', 'vocabulary', 'activities'];
  for (const field of arrayFields) {
    const value = lesson[field as keyof Lesson];
    if (value && Array.isArray(value) && value.length === 0) {
      result.missingFields.push(`${field} (пустой массив)`);
      result.isValid = false;
    }
  }

  // Проверяем домашнее задание только если оно есть
  if (lesson.homework) {
    if (!lesson.homework.description) {
      result.missingFields.push('Описание домашнего задания');
      result.isValid = false;
    }
    
    if (
      !lesson.homework.tasks || 
      !Array.isArray(lesson.homework.tasks) || 
      lesson.homework.tasks.length === 0
    ) {
      result.missingFields.push('Задания домашней работы');
      result.isValid = false;
    }
  }

  return result;
}

/**
 * Проверяет, была ли восстановлена ​​структура курса из неполных данных
 * @param course Структура курса
 * @param recoveryStatus Статус восстановления из API
 * @returns Информация о состоянии восстановления
 */
export function getCourseRecoveryInfo(
  course: CourseStructure | null, 
  recoveryStatus: 'success' | 'partial' | 'failure' | 'none'
): { 
  needsAttention: boolean; 
  message: string;
  validationScore?: number;
} {
  // Если нет статуса восстановления или курса, нечего анализировать
  if (recoveryStatus === 'none' || !course) {
    return {
      needsAttention: false,
      message: ''
    };
  }

  // Валидируем курс
  const validation = validateCourseStructure(course);

  switch (recoveryStatus) {
    case 'success':
      if (validation.isValid) {
        return {
          needsAttention: false,
          message: 'Данные были успешно восстановлены без потери информации.',
          validationScore: validation.score
        };
      } else {
        return {
          needsAttention: true,
          message: `Данные были восстановлены, но требуют внимания. Некоторые поля могут быть неполными.`,
          validationScore: validation.score
        };
      }
    
    case 'partial':
      return {
        needsAttention: true,
        message: `Данные были частично восстановлены. ${validation.lessonValidation.validLessons} из ${validation.lessonValidation.validLessons + validation.lessonValidation.invalidLessons} уроков полные.`,
        validationScore: validation.score
      };
    
    case 'failure':
      return {
        needsAttention: true,
        message: 'Не удалось восстановить данные полностью. Рекомендуется повторная генерация.',
        validationScore: validation.score
      };
      
    default:
      return {
        needsAttention: false,
        message: ''
      };
  }
} 