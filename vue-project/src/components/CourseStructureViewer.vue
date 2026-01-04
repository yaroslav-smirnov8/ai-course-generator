<template>
  <div class="bg-gray-800 rounded-lg p-4 mb-4">
    <div class="flex justify-between items-start mb-4">
      <h3 class="text-white font-medium">Структура курса</h3>
      
      <div class="flex items-center gap-2">
        <!-- Индикатор здоровья данных -->
        <div 
          v-if="validationScore !== null"
          class="px-3 py-1 rounded-full text-xs font-medium"
          :class="qualityBadgeClass"
        >
          {{ validationScore }}% полнота
        </div>
        
        <!-- Индикатор восстановления данных -->
        <div 
          v-if="recoveryStatus !== 'none'"
          class="px-3 py-1 rounded-full text-xs font-medium"
          :class="recoveryBadgeClass"
        >
          {{ recoveryStatusText }}
        </div>
      </div>
    </div>
    
    <!-- Предупреждение о неполных данных -->
    <div 
      v-if="recoveryMessage"
      class="p-3 mb-4 rounded text-sm"
      :class="needsAttention ? 'bg-yellow-800 text-yellow-200' : 'bg-gray-700 text-gray-300'"
    >
      {{ recoveryMessage }}
    </div>
    
    <!-- Структура курса -->
    <div v-if="course" class="space-y-3">
      <!-- Основная информация -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3 text-sm">
        <div class="bg-gray-700 p-2 rounded">
          <div class="text-gray-400">Название:</div>
          <div class="text-white">{{ course.name || 'Не указано' }}</div>
        </div>
        
        <div class="bg-gray-700 p-2 rounded">
          <div class="text-gray-400">Язык:</div>
          <div class="text-white">{{ course.language || 'Не указан' }}</div>
        </div>
        
        <div class="bg-gray-700 p-2 rounded">
          <div class="text-gray-400">Уровень:</div>
          <div class="text-white">{{ course.level || 'Не указан' }}</div>
        </div>
      </div>
      
      <!-- Уроки -->
      <div class="space-y-2">
        <div class="text-gray-400 text-sm">Уроки ({{ course.lessons?.length || 0 }}):</div>
        
        <div 
          v-for="(lesson, index) in course.lessons" 
          :key="index"
          class="bg-gray-700 p-2 rounded text-sm"
          :class="{'border border-yellow-500': !isLessonValid(lesson, index)}"
        >
          <div class="flex justify-between">
            <div class="text-white font-medium">{{ lesson.title || `Урок ${index + 1}` }}</div>
            
            <!-- Индикатор здоровья урока -->
            <div 
              v-if="!isLessonValid(lesson, index)"
              class="px-2 py-0.5 bg-yellow-800 text-yellow-200 rounded-full text-xs"
              :title="getLessonMissingFields(index).join(', ')"
            >
              Неполный
            </div>
          </div>
          
          <!-- Детали урока -->
          <div class="mt-1 text-gray-400 text-xs flex flex-wrap gap-2">
            <span v-if="lesson.grammar?.length">
              Грамматика: {{ lesson.grammar.length }}
            </span>
            <span v-if="lesson.vocabulary?.length">
              Лексика: {{ lesson.vocabulary.length }}
            </span>
            <span v-if="lesson.activities?.length">
              Активности: {{ lesson.activities.length }}
            </span>
          </div>
          
          <!-- Предупреждение о неполных данных -->
          <div 
            v-if="!isLessonValid(lesson, index)"
            class="mt-2 text-xs text-yellow-200 bg-yellow-900 p-1.5 rounded"
          >
            <div class="font-medium">Отсутствующие данные:</div>
            <ul class="list-disc list-inside mt-0.5">
              <li v-for="(field, idx) in getLessonMissingFields(index)" :key="idx">
                {{ field }}
              </li>
            </ul>
          </div>
        </div>
        
        <!-- Если нет уроков -->
        <div 
          v-if="!course.lessons || course.lessons.length === 0"
          class="bg-red-800 text-white p-3 rounded text-sm"
        >
          Уроки отсутствуют. Структура курса неполная.
        </div>
      </div>
    </div>
    
    <!-- Нет курса -->
    <div 
      v-else
      class="bg-red-800 text-white p-3 rounded text-sm"
    >
      Данные курса отсутствуют.
    </div>
    
    <!-- Кнопки действий -->
    <div v-if="course" class="mt-4 pt-4 border-t border-gray-600 flex gap-3">
      <button
        v-if="course && needsAttention"
        @click="$emit('regenerate')"
        class="px-3 py-1.5 bg-yellow-600 text-white rounded-md text-sm hover:bg-yellow-700"
      >
        Перегенерировать
      </button>
      
      <button
        @click="$emit('close')"
        class="px-3 py-1.5 bg-gray-700 text-white rounded-md text-sm hover:bg-gray-600"
      >
        Закрыть
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CourseStructure, Lesson } from '@/types/course';
import { validateCourseStructure, validateLesson, getCourseRecoveryInfo } from '@/utils/courseValidation';

interface Props {
  course: CourseStructure | null;
  recoveryStatus: 'success' | 'partial' | 'failure' | 'none';
}

const props = defineProps<Props>();
const emit = defineEmits(['regenerate', 'close']);

// Переиспользуем функции валидации
const validation = computed(() => validateCourseStructure(props.course));
const recoveryInfo = computed(() => getCourseRecoveryInfo(props.course, props.recoveryStatus));

// Компьютеды для отображения
const validationScore = computed(() => validation.value.score);
const needsAttention = computed(() => recoveryInfo.value.needsAttention);
const recoveryMessage = computed(() => recoveryInfo.value.message);

// Методы для проверки валидности уроков
const isLessonValid = (lesson: Lesson, index: number) => {
  return !validation.value.lessonValidation.missingFields[index];
};

const getLessonMissingFields = (index: number) => {
  return validation.value.lessonValidation.missingFields[index] || [];
};

// Определение классов для отображения
const qualityBadgeClass = computed(() => {
  const score = validationScore.value;
  if (score >= 90) return 'bg-green-600 text-white';
  if (score >= 70) return 'bg-green-700 text-white';
  if (score >= 50) return 'bg-yellow-600 text-white';
  return 'bg-red-600 text-white';
});

const recoveryBadgeClass = computed(() => {
  switch (props.recoveryStatus) {
    case 'success':
      return 'bg-green-600 text-white';
    case 'partial':
      return 'bg-yellow-600 text-white';
    case 'failure':
      return 'bg-red-600 text-white';
    default:
      return 'bg-gray-600 text-white';
  }
});

const recoveryStatusText = computed(() => {
  switch (props.recoveryStatus) {
    case 'success':
      return 'Восстановлено';
    case 'partial':
      return 'Частично восстановлено';
    case 'failure':
      return 'Ошибка восстановления';
    default:
      return '';
  }
});
</script> 