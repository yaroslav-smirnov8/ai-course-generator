<template>
  <div class="course-view-container w-full max-w-4xl mx-auto space-y-6">
    <div v-if="course" class="course-view-block">
      <!-- Отображение статуса восстановления данных -->
      <JsonRecoveryStatus
        v-if="recoveryStatus !== 'none'"
        :status="recoveryStatus"
        :details="{
          recoveredFields: recoveryDetails.recoveredFields,
          missingFields: recoveryDetails.missingFields,
          messages: recoveryDetails.messages
        }"
      />

      <div class="course-view-header flex justify-between items-center mb-6">
        <div>
          <h2 class="course-view-title">{{ course.name }}</h2>
          <div class="points-display" v-if="mainStore.user">
            <span class="points-icon">💎</span>
            <span class="points-value">{{ userPoints }} points</span>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="course-view-button-back"
        >
          Back
        </button>
      </div>

      <!-- Основная информация о курсе -->
      <div class="course-view-details-grid grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-sm">
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Language:</span>
          <span class="course-view-detail-value ml-2">{{ formatLanguage(course.language) }}</span>
        </div>
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Starting level:</span>
          <span class="course-view-detail-value ml-2">{{ formatLevel(course.startLevel || course.level) }}</span>
        </div>
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Target level:</span>
          <span class="course-view-detail-value ml-2">{{ formatLevel(course.level) }}</span>
        </div>
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Audience:</span>
          <span class="course-view-detail-value ml-2">{{ formatAudience(course.targetAudience) }}</span>
        </div>
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Format:</span>
          <span class="course-view-detail-value ml-2">{{ formatFormat(course.format) }}</span>
        </div>
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Methodology:</span>
          <span class="course-view-detail-value ml-2">{{ formatMethodology(course.methodology || 'communicative') }}</span>
        </div>
        <div v-if="course.examPrep" class="course-view-detail-item">
          <span class="course-view-detail-label">Exam:</span>
          <span class="course-view-detail-value ml-2">{{ course.examPrep }}</span>
        </div>
        <div class="course-view-detail-item">
          <span class="course-view-detail-label">Duration:</span>
          <span class="course-view-detail-value ml-2">{{ formatDuration(course.totalDuration) }}</span>
        </div>
      </div>

      <!-- Дополнительная информация о курсе -->
      <div v-if="hasAdditionalInfo" class="course-view-additional-info mb-6 p-4 rounded-lg">
        <h3 class="course-view-section-title mb-4">Additional Information</h3>

        <div class="space-y-4">
          <!-- Информация о студенте -->
          <div v-if="course.studentAge || course.studentInterests">
            <h4 class="course-view-subsection-title mb-2">Student Information</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <div v-if="course.studentAge">
                <span class="course-view-detail-label">Age:</span>
                <span class="course-view-detail-value ml-2">{{ formatAge(course.studentAge) }}</span>
              </div>
              <div v-if="course.studentInterests">
                <span class="course-view-detail-label">Interests:</span>
                <span class="course-view-detail-value ml-2">{{ course.studentInterests }}</span>
              </div>
            </div>
          </div>

          <!-- Цели и ошибки -->
          <div v-if="course.studentGoals">
            <h4 class="course-view-subsection-title mb-2">Learning Goals</h4>
            <p class="course-view-text">{{ course.studentGoals }}</p>
          </div>

          <div v-if="course.commonMistakes">
            <h4 class="course-view-subsection-title mb-2">Common Mistakes</h4>
            <p class="course-view-text">{{ course.commonMistakes }}</p>
          </div>

          <!-- Требования и результаты -->
          <div v-if="course.prerequisites && course.prerequisites.length > 0" class="mt-2">
            <h4 class="course-view-subsection-title mb-2">Prerequisites</h4>
            <ul class="course-view-list list-disc list-inside text-sm">
              <li v-for="(prerequisite, idx) in course.prerequisites" :key="idx">
                {{ prerequisite }}
              </li>
            </ul>
          </div>

          <div v-if="course.learningOutcomes && course.learningOutcomes.length > 0" class="mt-2">
            <h4 class="course-view-subsection-title mb-2">Learning Outcomes</h4>
            <ul class="course-view-list list-disc list-inside text-sm">
              <li v-for="(outcome, idx) in course.learningOutcomes" :key="idx">
                {{ outcome }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Список уроков -->
      <div class="space-y-4">
        <h3 class="course-view-section-title mb-4">Course Structure ({{ course.lessons.length }} lessons)</h3>

        <div v-for="(lesson, index) in course.lessons" :key="index" class="course-view-lesson-item rounded-lg overflow-hidden">
          <!-- Заголовок урока -->
          <div
            class="course-view-lesson-header flex items-center justify-between p-4 cursor-pointer"
            @click="toggleLesson(index)"
          >
            <div>
              <h4 class="course-view-lesson-title">Lesson {{ index + 1 }}: {{ lesson.title }}</h4>
              <p class="course-view-lesson-duration">{{ lesson.duration }} minutes</p>
            </div>
            <button class="course-view-lesson-toggle-btn">
              {{ expandedLesson === index ? '−' : '+' }}
            </button>
          </div>

          <!-- Содержимое урока -->
          <div v-if="expandedLesson === index" class="course-view-lesson-content p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Левая колонка -->
              <div class="space-y-4">
                <div>
                  <h5 class="course-view-subsection-title mb-2">Goals</h5>
                  <ul class="course-view-list list-disc list-inside text-sm space-y-1">
                    <li v-for="(objective, idx) in lesson.objectives" :key="idx">
                      {{ objective }}
                    </li>
                  </ul>
                </div>

                <div>
                  <h5 class="course-view-subsection-title mb-2">Grammar</h5>
                  <ul class="course-view-list list-disc list-inside text-sm space-y-1">
                    <li v-for="(item, idx) in lesson.grammar" :key="idx">
                      {{ item }}
                    </li>
                  </ul>
                </div>

                <div>
                  <h5 class="course-view-subsection-title mb-2">Vocabulary</h5>
                  <ul class="course-view-list list-disc list-inside text-sm space-y-1">
                    <li v-for="(item, idx) in lesson.vocabulary" :key="idx">
                      {{ item }}
                    </li>
                  </ul>
                </div>
              </div>

              <!-- Правая колонка -->
              <div class="space-y-4">
                <div>
                  <h5 class="course-view-subsection-title mb-2">Activities</h5>
                  <div class="space-y-2">
                    <div
                      v-for="(activity, idx) in lesson.activities"
                      :key="idx"
                      class="course-view-activity-item p-3 rounded"
                    >
                      <div class="course-view-activity-name">{{ activity.name }}</div>
                      <div class="course-view-activity-duration">{{ activity.duration }} min</div>
                      <div class="course-view-activity-description">{{ activity.description }}</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h5 class="course-view-subsection-title mb-2">Materials</h5>
                  <ul class="course-view-list list-disc list-inside text-sm space-y-1">
                    <li v-for="(material, idx) in lesson.materials" :key="idx">
                      {{ material }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- УДАЛЕНО: Блок домашнего задания -->

            <!-- Информация о лимитах и баллах -->
            <div class="course-view-limits-info mt-4 mb-2 flex flex-wrap gap-3">
              <div class="w-full md:w-auto">
                <GenerationLimitsDisplay :content-type="ContentType.LESSON_PLAN" />
              </div>
              <div class="w-full md:w-auto points-info">
                <span class="points-icon">💎</span> Points: {{ userPoints }}
                <span class="points-cost">(Cost: 8 points)</span>
              </div>
            </div>

            <!-- Кнопки действий -->
            <div class="course-view-lesson-actions mt-4 pt-4 flex flex-wrap justify-between gap-4">
              <div class="flex flex-col gap-2 flex-1 min-w-[150px]">
                <button
                  @click="generateLessonPlan(lesson, index)"
                  class="course-view-action-button"
                  :disabled="planLoadings[index]"
                >
                  {{ planLoadings[index] ? 'Generating...' : 'Lesson Plan' }}
                </button>
                <button
                  @click="generateLessonPlanWithPoints(lesson, index)"
                  class="course-view-action-button-points"
                  :disabled="planLoadings[index] || userPoints < 8"
                >
                  <span class="points-icon">💎</span> For Points
                </button>
              </div>

              <div class="flex flex-col gap-2 flex-1 min-w-[150px]">
                <button
                  @click="generateExercises(lesson, index)"
                  class="course-view-action-button"
                  :disabled="generatingExercises === index || exerciseLoadings[index]"
                >
                  {{ exerciseLoadings[index] ? 'Generating...' : 'Exercises' }}
                </button>
                <button
                  @click="generateExercisesWithPoints(lesson, index)"
                  class="course-view-action-button-points"
                  :disabled="generatingExercises === index || exerciseLoadings[index] || userPoints < 8"
                >
                  <span class="points-icon">💎</span> For Points
                </button>
              </div>

              <div class="flex flex-col gap-2 flex-1 min-w-[150px]">
                <button
                  @click="generateGame(index)"
                  class="course-view-action-button"
                  :disabled="gameLoadings[index]"
                >
                  {{ gameLoadings[index] ? 'Generating...' : 'Game' }}
                </button>
                <button
                  @click="generateGameWithPoints(index)"
                  class="course-view-action-button-points"
                  :disabled="gameLoadings[index] || userPoints < 8"
                >
                  <span class="points-icon">💎</span> For Points
                </button>
              </div>
            </div>

             <!-- Селектор типа игры (появляется при клике на кнопку) -->
             <GameTypeSelector
               v-if="showGameTypeSelectorForLesson === index"
               :withPoints="isGeneratingGameWithPoints"
               @select="(selectedType) => confirmGenerateGame(lesson, index, selectedType)"
               @select-with-points="(selectedType) => confirmGenerateGameWithPoints(lesson, index, selectedType)"
               @cancel="showGameTypeSelectorForLesson = null"
             />

            <!-- Отображение сгенерированного плана урока -->
            <GeneratedLessonPlanView
              class="mt-4 col-span-1 md:col-span-2"
              :planContent="generatedPlans[index]"
              :isLoading="planLoadings[index] || false"
              :isVisible="planVisibility[index] ?? true"
              @toggle-visibility="togglePlanVisibility(index)"
            />

            <!-- Отображение сгенерированных упражнений -->
            <GeneratedExercisesView
              class="mt-4 col-span-1 md:col-span-2"
              :exercisesContent="generatedExercises[index]"
              :isLoading="exerciseLoadings[index] || false"
              :isVisible="exerciseVisibility[index] ?? true"
              @toggle-visibility="toggleExerciseVisibility(index)"
            />

            <!-- Отображение сгенерированной игры -->
            <GeneratedGameView
              class="mt-4 col-span-1 md:col-span-2"
              :gameContent="generatedGames[index]?.game_content ?? null"
              :gameType="generatedGames[index]?.game_type"
              :isLoading="gameLoadings[index] || false"
              :isVisible="gameVisibility[index] ?? true"
              @toggle-visibility="toggleGameVisibility(index)"
            />

          </div>
        </div>
      </div>

      <!-- Кнопки действий для всего курса -->
      <div class="course-view-course-actions mt-6 pt-6 flex flex-wrap gap-4">
        <button
          @click="exportCourse('pdf')"
          class="course-view-action-button course-view-action-button-pdf"
          :disabled="isExporting"
        >
          {{ isExporting ? 'Exporting...' : 'Export to PDF' }}
        </button>
        <button
          @click="exportCourse('docx')"
          class="course-view-action-button course-view-action-button-docx"
          :disabled="isExporting"
        >
          {{ isExporting ? 'Exporting...' : 'Export to DOCX' }}
        </button>
        <button
          @click="saveCourse"
          class="course-view-action-button course-view-action-button-save"
          :disabled="isSaving"
        >
          {{ isSaving ? 'Saving...' : 'Save Course' }}
        </button>
      </div>
    </div>

    <div v-else class="course-view-not-found p-6 text-center">
      <p>Course not found. Please generate a new course.</p>
      <button
        @click="$emit('close')"
        class="course-view-action-button mt-4"
      >
        Return to generator
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, computed } from 'vue'
import { useCourseStore } from '../store/course'
import { useMainStore } from '@/store'
import { ContentType } from '@/types/enums'
import type { CourseStructure, Lesson, CourseFormData, GeneratedGameResponse } from '@/types/course' // Добавляем GeneratedGameResponse
import JsonRecoveryStatus from './common/JsonRecoveryStatus.vue'
import GeneratedLessonPlanView from './GeneratedLessonPlanView.vue' // Импортируем компонент для плана
import GeneratedExercisesView from './GeneratedExercisesView.vue' // Импортируем компонент для упражнений
import GeneratedGameView from './GeneratedGameView.vue' // Импортируем компонент для игр
import GameTypeSelector from './GameTypeSelector.vue'; // Импортируем селектор типа игры
import GenerationLimitsDisplay from './common/GenerationLimitsDisplay.vue'

const props = defineProps<{
  course: CourseStructure | null
}>()

const emit = defineEmits(['back', 'close'])
const store = useCourseStore()
const mainStore = useMainStore()

// Добавляем данные о восстановлении
const recoveryStatus = computed(() => store.recoveryStatus || 'none')
const recoveryDetails = computed(() => ({
  recoveredFields: store.recoveryDetails?.recoveredFields || [],
  missingFields: store.recoveryDetails?.missingFields || [],
  messages: store.recoveryDetails?.messages || []
}))

const expandedLesson = ref<number | null>(null)
const generatingLesson = ref<number | null>(null) // Оставляем для обратной совместимости или будущих нужд
const generatingExercises = ref<number | null>(null) // Используется для disabled на кнопке упражнений
const isExporting = ref(false)
const isSaving = ref(false)

// Добавляем вычисляемое свойство для баллов пользователя
const userPoints = computed(() => mainStore.user?.points || 0)

// Новые состояния для планов уроков
const generatedPlans = ref<Record<number, string | null>>({}) // { index: planText }
const planLoadings = ref<Record<number, boolean>>({}) // { index: isLoading }
const planVisibility = ref<Record<number, boolean>>({}) // { index: isVisible } - новое состояние

// Новые состояния для упражнений
const generatedExercises = ref<Record<number, string | null>>({}) // { index: exercisesText }
const exerciseLoadings = ref<Record<number, boolean>>({}) // { index: isLoading }
const exerciseVisibility = ref<Record<number, boolean>>({}) // { index: isVisible }

// Новые состояния для игр
const generatedGames = ref<Record<number, GeneratedGameResponse | null>>({}) // { index: gameResponse } - Используем новый тип
const gameLoadings = ref<Record<number, boolean>>({}) // { index: isLoading }
const gameVisibility = ref<Record<number, boolean>>({}) // { index: isVisible }
const showGameTypeSelectorForLesson = ref<number | null>(null); // Для управления видимостью селектора
const isGeneratingGameWithPoints = ref<boolean>(false); // Для отслеживания генерации игры за баллы


const toggleLesson = (index: number) => {
  expandedLesson.value = expandedLesson.value === index ? null : index
}

const formatLanguage = (language: string) => {
  const languages: Record<string, string> = {
    'english': 'English',
    'spanish': 'Spanish',
    'french': 'French',
    'german': 'German'
  }
  return languages[language] || language.charAt(0).toUpperCase() + language.slice(1)
}

const formatLevel = (level: string) => {
  const levels: Record<string, string> = {
    'beginner': 'Beginner',
    'elementary': 'Elementary',
    'intermediate': 'Intermediate',
    'upper-intermediate': 'Upper Intermediate',
    'advanced': 'Advanced'
  }
  return levels[level] || level.split('-').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join('-')
}

const formatAudience = (audience: string) => {
  const audiences: Record<string, string> = {
    'children': 'Children',
    'teens': 'Teens',
    'adults': 'Adults',
    'business': 'Business'
  }
  // Добавляем проверку на существование audience
  if (!audience) return '';
  return audiences[audience] || audience.charAt(0).toUpperCase() + audience.slice(1)
}

const formatFormat = (format: string) => {
  const formats: Record<string, string> = {
    'online': 'Online',
    'offline': 'Offline',
    'hybrid': 'Hybrid'
  }
  return formats[format] || format.charAt(0).toUpperCase() + format.slice(1)
}

const formatMethodology = (methodology: string) => {
  const names: Record<string, string> = {
    'communicative': 'Communicative Method',
    'task-based': 'Task-based Learning',
    'natural': 'Natural Approach',
    'lexical': 'Lexical Approach',
    'grammar-translation': 'Grammar Translation Method',
    'audio-lingual': 'Audio-lingual Method',
    'direct': 'Direct Method',
    'total-physical-response': 'Total Physical Response'
  }
  return names[methodology] || methodology.charAt(0).toUpperCase() + methodology.slice(1)
}

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours > 0) {
    return `${hours} ч ${mins} мин`
  }
  return `${mins} мин`
}

const formatAge = (age: string) => {
  const ages: Record<string, string> = {
    'children_6_9': 'Children (6-9 years)',
    'children_10_12': 'Children (10-12 years)',
    'teenagers_13_15': 'Teenagers (13-15 years)',
    'teenagers_16_18': 'Teenagers (16-18 years)',
    'adults_18_25': 'Young Adults (18-25 years)',
    'adults_25_40': 'Adults (25-40 years)',
    'adults_40+': 'Adults (40+ years)'
  }
  return ages[age] || age
}

// Проверяем, есть ли дополнительная информация для отображения
const hasAdditionalInfo = computed(() => {
  if (!props.course) return false

  return !!(
    props.course.studentAge ||
    props.course.studentInterests ||
    props.course.studentGoals ||
    props.course.commonMistakes ||
    (props.course.prerequisites && props.course.prerequisites.length > 0) ||
    (props.course.learningOutcomes && props.course.learningOutcomes.length > 0)
  )
})

// Обновляем обработчик для вызова нового действия fetchGeneratedLessonPlanText
const generateLessonPlan = async (lesson: Lesson, index: number) => {
  if (!props.course) return

  planLoadings.value[index] = true // Устанавливаем загрузку для этого урока
  generatedPlans.value[index] = null // Очищаем предыдущий план
  generatingLesson.value = index // Можно оставить для индикации на кнопке
  planVisibility.value[index] = true // Показываем план при начале генерации

  try {
    // Убедимся, что метод fetchGeneratedLessonPlanText существует
    if (typeof store.fetchGeneratedLessonPlanText !== 'function') {
      throw new Error('Метод fetchGeneratedLessonPlanText не найден в хранилище course store.');
    }

    // Собираем контекст курса (упрощенный, т.к. полный formData здесь недоступен, берем из props.course)
    // Важно: Убедитесь, что props.course содержит все необходимые поля для course_context в API
    const courseContext: Partial<CourseFormData> = {
        language: props.course.language,
        level: props.course.level,
        targetAudience: props.course.targetAudience || 'adults', // Добавляем значение по умолчанию
        methodology: props.course.methodology,
        age: props.course.studentAge,
        goals: props.course.studentGoals,
        interests: props.course.studentInterests,
        // Добавьте другие поля из props.course, если они нужны
    };

    // Вызываем новый метод хранилища
    const planText = await store.fetchGeneratedLessonPlanText(lesson, courseContext as CourseFormData) // Передаем урок и контекст
    generatedPlans.value[index] = planText // Сохраняем результат

  } catch (error: any) {
    console.error('Ошибка при генерации плана урока:', error)
    generatedPlans.value[index] = `Ошибка: ${error.message || 'Неизвестная ошибка'}` // Показываем ошибку
  } finally {
    planLoadings.value[index] = false // Сбрасываем загрузку
    generatingLesson.value = null // Сбрасываем индикацию на кнопке
  }
}


const generateExercises = async (lesson: Lesson, index: number) => {
  if (!props.course) return;

  exerciseLoadings.value[index] = true; // Устанавливаем загрузку
  generatedExercises.value[index] = null; // Очищаем предыдущие упражнения
  exerciseVisibility.value[index] = true; // Показываем блок при начале генерации
  generatingExercises.value = index; // Для индикации на кнопке (можно оставить или убрать)

  try {
    // Убедимся, что метод fetchGeneratedExercises существует
    if (typeof store.fetchGeneratedExercises !== 'function') {
      throw new Error('Метод fetchGeneratedExercises не найден в хранилище course store.');
    }
    console.log('[generateExercises] Checking props.course.targetAudience:', props.course.targetAudience); // Добавляем лог

    // Собираем контекст курса (аналогично generateLessonPlan)
    const courseContext: Partial<CourseFormData> = {
        language: props.course.language,
        level: props.course.level,
        targetAudience: props.course.targetAudience || 'adults', // Добавляем значение по умолчанию
        methodology: props.course.methodology,
        age: props.course.studentAge,
        goals: props.course.studentGoals,
        interests: props.course.studentInterests,
    };

    // Вызываем новое действие хранилища
    const exercisesText = await store.fetchGeneratedExercises(lesson, courseContext as CourseFormData);
    generatedExercises.value[index] = exercisesText; // Сохраняем результат

  } catch (error: any) {
    console.error('Ошибка при генерации упражнений:', error);
    generatedExercises.value[index] = `Ошибка: ${error.message || 'Неизвестная ошибка'}`; // Показываем ошибку
  } finally {
    exerciseLoadings.value[index] = false; // Сбрасываем загрузку
    generatingExercises.value = null; // Сбрасываем индикацию на кнопке
  }
}

// Метод для генерации плана урока за баллы
const generateLessonPlanWithPoints = async (lesson: Lesson, index: number) => {
  if (!props.course) return;

  planLoadings.value[index] = true; // Устанавливаем загрузку для этого урока
  generatedPlans.value[index] = null; // Очищаем предыдущий план
  planVisibility.value[index] = true; // Показываем план при начале генерации

  try {
    // Убедимся, что метод fetchGeneratedLessonPlanTextWithPoints существует
    if (typeof store.fetchGeneratedLessonPlanTextWithPoints !== 'function') {
      throw new Error('Метод fetchGeneratedLessonPlanTextWithPoints не найден в хранилище course store.');
    }

    // Собираем контекст курса
    const courseContext: Partial<CourseFormData> = {
        language: props.course.language,
        level: props.course.level,
        targetAudience: props.course.targetAudience || 'adults',
        methodology: props.course.methodology,
        age: props.course.studentAge,
        goals: props.course.studentGoals,
        interests: props.course.studentInterests,
    };

    // Вызываем метод хранилища для генерации за баллы
    const planText = await store.fetchGeneratedLessonPlanTextWithPoints(lesson, courseContext as CourseFormData);
    generatedPlans.value[index] = planText; // Сохраняем результат

  } catch (error: any) {
    console.error('Ошибка при генерации плана урока за баллы:', error);
    generatedPlans.value[index] = `Ошибка при генерации за баллы: ${error.message || 'Неизвестная ошибка'}`;
  } finally {
    planLoadings.value[index] = false;
  }
}

// Метод для генерации упражнений за баллы
const generateExercisesWithPoints = async (lesson: Lesson, index: number) => {
  if (!props.course) return;

  exerciseLoadings.value[index] = true;
  generatedExercises.value[index] = null;
  exerciseVisibility.value[index] = true;
  generatingExercises.value = index;

  try {
    // Убедимся, что метод fetchGeneratedExercisesWithPoints существует
    if (typeof store.fetchGeneratedExercisesWithPoints !== 'function') {
      throw new Error('Метод fetchGeneratedExercisesWithPoints не найден в хранилище course store.');
    }

    // Собираем контекст курса
    const courseContext: Partial<CourseFormData> = {
        language: props.course.language,
        level: props.course.level,
        targetAudience: props.course.targetAudience || 'adults',
        methodology: props.course.methodology,
        age: props.course.studentAge,
        goals: props.course.studentGoals,
        interests: props.course.studentInterests,
    };

    // Вызываем метод хранилища для генерации за баллы
    const exercisesText = await store.fetchGeneratedExercisesWithPoints(lesson, courseContext as CourseFormData);
    generatedExercises.value[index] = exercisesText;

  } catch (error: any) {
    console.error('Ошибка при генерации упражнений за баллы:', error);
    generatedExercises.value[index] = `Ошибка при генерации за баллы: ${error.message || 'Неизвестная ошибка'}`;
  } finally {
    exerciseLoadings.value[index] = false;
    generatingExercises.value = null;
  }
}

// Метод, который показывает селектор типа игры
const generateGame = (index: number) => {
  showGameTypeSelectorForLesson.value = index;
  isGeneratingGameWithPoints.value = false; // Сбрасываем флаг генерации за баллы
}

// Метод для генерации игры за баллы
const generateGameWithPoints = (index: number) => {
  // Показываем селектор типа игры, но с флагом для генерации за баллы
  showGameTypeSelectorForLesson.value = index;
  isGeneratingGameWithPoints.value = true; // Устанавливаем флаг генерации за баллы
  // Вызываем confirmGenerateGameWithPoints после выбора типа игры
  // Это будет обработано в GameTypeSelector через событие select-with-points
}

// Метод для подтверждения и генерации игры после выбора типа
const confirmGenerateGame = async (lesson: Lesson, index: number, selectedGameType: string) => {
  showGameTypeSelectorForLesson.value = null; // Скрываем селектор
  isGeneratingGameWithPoints.value = false; // Сбрасываем флаг генерации за баллы
  if (!props.course) return;

  gameLoadings.value[index] = true;
  generatedGames.value[index] = null;
  gameVisibility.value[index] = true;

  try {
    if (typeof store.fetchGeneratedGame !== 'function') {
      throw new Error('Метод fetchGeneratedGame не найден в хранилище course store.');
    }

    // Собираем контекст курса
    const courseContext: Partial<CourseFormData> = {
        language: props.course.language,
        level: props.course.level,
        targetAudience: props.course.targetAudience || 'adults',
        methodology: props.course.methodology,
        age: props.course.studentAge,
        goals: props.course.studentGoals,
        interests: props.course.studentInterests,
    };

    // Вызываем действие хранилища с выбранным типом игры
    const gameResponse = await store.fetchGeneratedGame(lesson, courseContext as CourseFormData, selectedGameType);
    generatedGames.value[index] = gameResponse; // Сохраняем весь объект ответа

  } catch (error: any) {
    console.error('Ошибка при генерации игры:', error);
    // Сохраняем ошибку в формате Markdown для отображения
    generatedGames.value[index] = { game_content: `### Error\n\nОшибка: ${error.message || 'Неизвестная ошибка'}`, game_type: 'error' };
  } finally {
    gameLoadings.value[index] = false;
  }
}

// Метод для подтверждения и генерации игры за баллы после выбора типа
const confirmGenerateGameWithPoints = async (lesson: Lesson, index: number, selectedGameType: string) => {
  showGameTypeSelectorForLesson.value = null; // Скрываем селектор
  isGeneratingGameWithPoints.value = false; // Сбрасываем флаг генерации за баллы
  if (!props.course) return;

  gameLoadings.value[index] = true;
  generatedGames.value[index] = null;
  gameVisibility.value[index] = true;

  try {
    if (typeof store.fetchGeneratedGameWithPoints !== 'function') {
      throw new Error('Метод fetchGeneratedGameWithPoints не найден в хранилище course store.');
    }

    // Собираем контекст курса
    const courseContext: Partial<CourseFormData> = {
        language: props.course.language,
        level: props.course.level,
        targetAudience: props.course.targetAudience || 'adults',
        methodology: props.course.methodology,
        age: props.course.studentAge,
        goals: props.course.studentGoals,
        interests: props.course.studentInterests,
    };

    // Вызываем действие хранилища с выбранным типом игры за баллы
    const gameResponse = await store.fetchGeneratedGameWithPoints(lesson, courseContext as CourseFormData, selectedGameType);
    generatedGames.value[index] = gameResponse; // Сохраняем весь объект ответа

  } catch (error: any) {
    console.error('Ошибка при генерации игры за баллы:', error);
    // Сохраняем ошибку в формате Markdown для отображения
    generatedGames.value[index] = { game_content: `### Error\n\nОшибка при генерации за баллы: ${error.message || 'Неизвестная ошибка'}`, game_type: 'error' };
  } finally {
    gameLoadings.value[index] = false;
  }
}


const exportCourse = async (format: 'pdf' | 'docx') => {
  if (!props.course) return

  isExporting.value = true
  try {
    // Проверяем, что у курса есть ID
    if (!props.course.id) {
      throw new Error('Курс не сохранен. Пожалуйста, сохраните курс перед экспортом.');
    }

    // Экспортируем курс
    await store.exportCourse(props.course.id, format);

    // Показываем сообщение об успешном экспорте
    alert(`Курс успешно экспортирован в формате ${format.toUpperCase()}`);
  } catch (error: any) {
    console.error('Ошибка при экспорте курса:', error);

    // Показываем сообщение об ошибке
    alert(`Ошибка при экспорте курса: ${error.message || 'Неизвестная ошибка'}`);
  } finally {
    isExporting.value = false;
  }
}

const saveCourse = async () => {
  if (!props.course) return

  isSaving.value = true
  try {
    console.log('Начинаем сохранение курса:', props.course.name);

    // Проверяем, что у курса есть все необходимые поля
    if (!props.course.name || !props.course.language || !props.course.level) {
      throw new Error('Курс не содержит обязательных полей (название, язык, уровень)');
    }

    // Проверяем, что у курса есть уроки
    if (!props.course.lessons || props.course.lessons.length === 0) {
      throw new Error('Курс не содержит уроков');
    }

    // Сохраняем курс
    const savedCourse = await store.saveCourse(props.course);

    // Проверяем, что savedCourse не undefined и имеет свойство id
    if (savedCourse && savedCourse.id) {
      console.log('Курс успешно сохранен:', savedCourse);

      // Показываем сообщение об успешном сохранении
      alert(`Курс "${savedCourse.name}" успешно сохранен!`);

      // Обновляем ID курса, если он был создан впервые
      if (!props.course.id && savedCourse.id) {
        console.log(`Обновляем ID курса с ${props.course.id} на ${savedCourse.id}`);
        props.course.id = savedCourse.id;
      }

      // Обновляем другие поля курса, если они изменились
      props.course.name = savedCourse.name;
      props.course.description = savedCourse.description;

      // Обновляем список курсов в хранилище
      try {
        console.log('Обновляем список курсов в хранилище');
        await store.fetchUserCourses();
      } catch (fetchError) {
        console.warn('Не удалось обновить список курсов:', fetchError);
      }
    } else {
      // Если savedCourse не содержит ожидаемых данных, используем данные из props.course
      console.log('Сохраненный курс не содержит ожидаемых данных:', savedCourse);
      alert(`Курс "${props.course.name}" успешно сохранен!`);
    }
  } catch (error: any) {
    console.error('Ошибка при сохранении курса:', error);

    // Формируем понятное сообщение об ошибке
    let errorMessage = 'Ошибка при сохранении курса';

    if (error.message && error.message.includes('Ошибки валидации')) {
      // Если ошибка связана с валидацией, показываем более понятное сообщение
      errorMessage = 'Ошибка валидации данных курса. Пожалуйста, проверьте, что все поля заполнены корректно.';

      // Если в сообщении есть конкретные поля с ошибками, добавляем их
      if (error.message.includes('methodology') ||
          error.message.includes('student_age') ||
          error.message.includes('student_interests') ||
          error.message.includes('student_goals') ||
          error.message.includes('common_mistakes') ||
          error.message.includes('lessons_count') ||
          error.message.includes('lesson_duration') ||
          error.message.includes('lessons')) {
        errorMessage += '\n\nНекоторые поля не поддерживаются API. Мы попытались их автоматически исправить, но не удалось.';
      }
    } else if (error.message) {
      // Если есть сообщение об ошибке, используем его
      errorMessage += `: ${error.message}`;
    }

    // Показываем сообщение об ошибке
    alert(errorMessage);
  } finally {
    isSaving.value = false;
  }
}

// Новый метод для переключения видимости плана
const togglePlanVisibility = (index: number) => {
  // Если значение не определено, считаем его true (видимым) и переключаем на false
  // Иначе просто инвертируем текущее значение
  planVisibility.value[index] = !(planVisibility.value[index] ?? true);
}

// Метод для переключения видимости упражнений
const toggleExerciseVisibility = (index: number) => {
  exerciseVisibility.value[index] = !(exerciseVisibility.value[index] ?? true);
}

// Метод для переключения видимости игры
const toggleGameVisibility = (index: number) => {
  gameVisibility.value[index] = !(gameVisibility.value[index] ?? true);
}
</script>

<style scoped>
.course-view-container {
  /* Общий фон и паддинг для всего представления */
  /* background: #1c0522 url('@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg'); */ /* Фон удален */
  /* background-size: cover; */
  /* background-position: center; */
  /* background-repeat: no-repeat; */
  padding: 2rem; /* Оставляем паддинг */
  border-radius: 1rem; /* Оставляем скругление */
  /* box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(139, 92, 246, 0.3); */ /* Тень удалена */
}

.course-view-block {
  /* Основной блок контента */
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  margin-bottom: 1.5rem;
}

.course-view-header {
  border-bottom: 1px solid rgba(139, 92, 246, 0.3); /* Разделитель под заголовком */
  padding-bottom: 1rem;
}

.course-view-title {
  color: white;
  font-size: 1.8rem;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.9;
}

.course-view-button-back {
  padding: 0.5rem 1rem;
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.75rem;
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.course-view-button-back:hover {
  background-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.course-view-details-grid {
  /* Стили для сетки с деталями курса */
  color: white;
}

.course-view-detail-item {
  background-color: rgba(255, 204, 243, 0.1);
  padding: 0.5rem 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(255, 103, 231, 0.2);
}

.course-view-detail-label {
  color: rgba(255, 255, 255, 0.7); /* Цвет метки */
}

.course-view-detail-value {
  font-weight: 500;
}

.course-view-additional-info {
  /* Блок с доп. информацией */
  background-color: rgba(88, 28, 135, 0.2); /* Немного другой оттенок */
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.course-view-section-title {
  color: white;
  font-size: 1.3rem;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
  padding-bottom: 0.5rem;
}

.course-view-subsection-title {
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  opacity: 0.9;
}

.course-view-text {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.95rem;
  line-height: 1.6;
}

.course-view-list {
  color: rgba(255, 255, 255, 0.85);
  padding-left: 1rem; /* Отступ для маркеров списка */
}
.course-view-list li {
  margin-bottom: 0.25rem;
}

.course-view-lesson-item {
  /* Карточка урока */
  background: linear-gradient(135deg, rgba(88, 28, 135, 0.3), rgba(139, 92, 246, 0.15));
  backdrop-filter: blur(5px);
  border: 1px solid rgba(139, 92, 246, 0.4);
  transition: all 0.3s;
}
.course-view-lesson-item:hover {
  border-color: rgba(255, 103, 231, 0.5);
}

.course-view-lesson-header {
  background-color: rgba(255, 255, 255, 0.05);
  transition: background-color 0.3s;
}
.course-view-lesson-header:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.course-view-lesson-title {
  color: white;
  font-weight: 600;
}

.course-view-lesson-duration {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
}

.course-view-lesson-toggle-btn {
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}
.course-view-lesson-toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.course-view-lesson-content {
  border-top: 1px solid rgba(139, 92, 246, 0.3);
  background-color: rgba(0, 0, 0, 0.1); /* Темный фон для контента урока */
}

.course-view-activity-item {
  background-color: rgba(255, 204, 243, 0.15);
  border-left: 3px solid #ff67e7;
}

.course-view-activity-name {
  color: white;
  font-weight: 500;
}
.course-view-activity-duration {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
}
.course-view-activity-description {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.course-view-lesson-actions {
  border-top: 1px solid rgba(139, 92, 246, 0.3);
}

.course-view-action-button {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 1rem;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #8b5cf6; /* Фиолетовый по умолчанию */
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.course-view-action-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(139, 92, 246, 0.5);
  background-color: #9f71fb;
}

.course-view-action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #6b4b9a;
}

.course-view-action-button-points {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 1rem;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #1890ff; /* Синий для баллов */
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
}

.course-view-action-button-points:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(24, 144, 255, 0.5);
  background-color: #40a9ff;
}

.course-view-action-button-points:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #1e40af;
}

.points-icon {
  margin-right: 5px;
  font-size: 16px;
}

.points-info {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: #4a5568;
  background-color: #e6f7ff;
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid #91d5ff;
}

.points-cost {
  margin-left: 0.5rem;
  font-size: 0.8rem;
  color: #718096;
}

.points-display {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(5px);
  border-radius: 20px;
  padding: 8px 15px;
  display: inline-flex;
  align-items: center;
  margin-top: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.points-display .points-icon {
  font-size: 1.2rem;
  margin-right: 8px;
}

.points-display .points-value {
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Стили для отображения баллов */
.course-view-points-display {
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 0.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.course-view-points-details {
  width: 100%;
}

.course-view-points-summary {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  color: white;
  font-weight: 500;
  transition: all 0.3s;
}

.course-view-points-summary:hover {
  background-color: rgba(255, 103, 231, 0.1);
  border-radius: 0.5rem;
}

.course-view-points-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.course-view-points-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

.course-view-points-info {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.course-view-points-description {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.course-view-limits-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Цвета для кнопок экспорта/сохранения */
.course-view-action-button-pdf {
  background-color: #ec407a; /* Розовый */
  box-shadow: 0 4px 12px rgba(236, 64, 122, 0.5);
}
.course-view-action-button-pdf:hover:not(:disabled) {
  background-color: #ff67e7;
  box-shadow: 0 6px 18px rgba(255, 103, 231, 0.6);
}
.course-view-action-button-pdf:disabled {
  background-color: #a05784;
}

.course-view-action-button-docx {
  background-color: #6a1b9a; /* Темно-фиолетовый */
  box-shadow: 0 4px 12px rgba(106, 27, 154, 0.4);
}
.course-view-action-button-docx:hover:not(:disabled) {
  background-color: #8e24aa;
  box-shadow: 0 6px 16px rgba(142, 36, 170, 0.5);
}
.course-view-action-button-docx:disabled {
  background-color: #581c7a;
}

.course-view-action-button-save {
  background-color: #2563eb; /* Синий */
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
}
.course-view-action-button-save:hover:not(:disabled) {
  background-color: #3b82f6;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
}
.course-view-action-button-save:disabled {
  background-color: #1e40af;
}


.course-view-course-actions {
  border-top: 1px solid rgba(139, 92, 246, 0.3);
  justify-content: center; /* Центрируем кнопки */
}

.course-view-not-found {
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  color: white;
}
.course-view-not-found p {
  margin-bottom: 1rem;
}

/* Адаптивность для мобильных устройств */
@media (max-width: 640px) { /* Используем 640px как точку перелома для мобильных */
  .course-view-container {
    padding: 1rem; /* Уменьшаем общий паддинг контейнера */
  }

  .course-view-block {
    padding: 1rem; /* Уменьшаем паддинг основного блока */
  }

  .course-view-title {
    font-size: 1.5rem; /* Уменьшаем заголовок */
  }

  .course-view-details-grid {
    grid-template-columns: 1fr; /* Детали курса в одну колонку */
    gap: 0.5rem; /* Уменьшаем отступ */
  }

  .course-view-lesson-header {
    padding: 0.75rem; /* Уменьшаем паддинг заголовка урока */
  }

  .course-view-lesson-content {
    padding: 0.75rem; /* Уменьшаем паддинг контента урока */
  }

  .course-view-lesson-actions {
     gap: 0.5rem; /* Уменьшаем отступ между кнопками */
  }

  .course-view-action-button {
    padding: 0.5rem 0.75rem; /* Уменьшаем кнопки */
    font-size: 0.8rem;
    min-width: auto; /* Убираем минимальную ширину */
  }

  .course-view-course-actions {
    gap: 0.5rem; /* Уменьшаем отступ между кнопками */
    justify-content: space-around; /* Распределяем кнопки */
  }
}

/* Дополнительная адаптивность для очень узких экранов */
@media (max-width: 380px) {
  .course-view-container {
    padding: 0.5rem; /* Еще меньше паддинг */
  }
  .course-view-block {
    padding: 0.75rem; /* Еще меньше паддинг */
  }
  .course-view-lesson-header,
  .course-view-lesson-content {
    padding: 0.5rem; /* Еще меньше паддинг */
  }
  .course-view-action-button {
    font-size: 0.75rem; /* Еще меньше шрифт кнопок */
  }
}

/* Дополнительная адаптивность для очень узких экранов */
@media (max-width: 380px) {
  .course-view-container {
    padding: 0.5rem; /* Еще меньше паддинг */
  }
  .course-view-block {
    padding: 0.75rem; /* Еще меньше паддинг */
  }
  .course-view-lesson-header,
  .course-view-lesson-content {
    padding: 0.5rem; /* Еще меньше паддинг */
  }
  .course-view-action-button {
    font-size: 0.75rem; /* Еще меньше шрифт кнопок */
  }
}

</style>
