// src/hooks/useLessonPlan.ts
import { ref, computed } from 'vue'
import type { LessonPlanFormData, ValidationResult } from '@/types/LessonPlan'

export function useLessonPlan() {
  // Начальное состояние формы
  const formData = ref<LessonPlanFormData>({
    language: '',
    level: '',
    topic: '',
    duration: 60,
    methodologies: {
      mainMethod: '',
      supportMethods: []
    },
    teachingMethodology: '',
    objectives: [],
    materials: [],
    assessment: 'formative',
    format: 'online',
    culturalElements: false
  });

  // Состояние валидации
  const validation = ref<ValidationResult>({
    errors: [],
    warnings: []
  });

  // Валидация по шагам
  const validateStep = (step: number): boolean => {
    validation.value.errors = [];
    validation.value.warnings = [];

    switch (step) {
      case 1:
        if (!formData.value.language) {
          validation.value.errors.push('Выберите язык');
        }
        if (!formData.value.level) {
          validation.value.errors.push('Выберите уровень');
        }
        if (!formData.value.topic) {
          validation.value.errors.push('Введите тему урока');
        }
        if (formData.value.duration < 15 || formData.value.duration > 180) {
          validation.value.errors.push('Продолжительность должна быть от 15 до 180 минут');
        }
        break;

      case 2:
        if (!formData.value.methodologies.mainMethod) {
          validation.value.errors.push('Выберите основную методику');
        }
        if (!formData.value.teachingMethodology) {
          validation.value.errors.push('Выберите методику обучения');
        }
        if (formData.value.methodologies.supportMethods.length === 0) {
          validation.value.warnings.push('Рекомендуется добавить поддерживающие методики');
        }
        break;

      case 3:
        if (formData.value.objectives.length === 0) {
          validation.value.errors.push('Добавьте хотя бы одну цель обучения');
        }
        if (formData.value.materials.length === 0) {
          validation.value.warnings.push('Рекомендуется указать необходимые материалы');
        }
        break;

      case 4:
        // Дополнительные проверки не требуются
        break;
    }

    return validation.value.errors.length === 0;
  };

  // Методы для управления методиками
  const addMethod = (methodId: string, isMain: boolean) => {
    if (isMain) {
      formData.value.methodologies.mainMethod = methodId;
    } else {
      if (!formData.value.methodologies.supportMethods.includes(methodId)) {
        formData.value.methodologies.supportMethods.push(methodId);
      }
    }
  };

  const removeMethod = (methodId: string) => {
    if (formData.value.methodologies.mainMethod === methodId) {
      formData.value.methodologies.mainMethod = '';
    } else {
      formData.value.methodologies.supportMethods =
        formData.value.methodologies.supportMethods.filter(id => id !== methodId);
    }
  };

  // Генерация промпта
  const generatePrompt = async (): Promise<string> => {
    const {
      language,
      level,
      topic,
      duration,
      methodologies,
      teachingMethodology,
      objectives,
      materials,
      assessment,
      format,
      culturalElements
    } = formData.value;

    const prompt = `
Создай план урока по ${language} языку со следующими параметрами:

Основные характеристики:
- Уровень: ${level}
- Тема: ${topic}
- Продолжительность: ${duration} минут
- Формат: ${format}

Методология:
- Основной метод: ${methodologies.mainMethod}
${methodologies.supportMethods.length > 0 ? `- Поддерживающие методы: ${methodologies.supportMethods.join(', ')}` : ''}
- Методика обучения: ${teachingMethodology}

Цели урока:
${objectives.map(obj => `- ${obj}`).join('\n')}

${materials.length > 0 ? `Необходимые материалы:\n${materials.map(mat => `- ${mat}`).join('\n')}` : ''}

Дополнительные параметры:
- Тип оценивания: ${assessment}
${culturalElements ? '- Включить культурные элементы и контекст\n' : ''}

План должен включать:
1. Вступительную часть (Warm-up)
2. Основную часть с упражнениями
3. Практическую часть
4. Заключительную часть
5. Домашнее задание (если применимо)

Для каждой части укажи:
- Приблизительное время
- Конкретные активности
- Роль учителя
- Роль учеников
    `;

    return prompt.trim();
  };

  return {
    formData,
    validation,
    validateStep,
    addMethod,
    removeMethod,
    generatePrompt
  };
}
