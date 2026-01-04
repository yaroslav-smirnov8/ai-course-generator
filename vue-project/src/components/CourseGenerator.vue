# CourseGenerator.vue
<template>
  <!-- Проверка доступа к премиум функциям -->
  <PremiumRequired
    v-if="!hasPremiumAccess && isUserLoaded"
    feature-name="Course Generator"
  />

  <div v-else-if="hasPremiumAccess" class="generator-container w-full max-w-4xl mx-auto p-4 space-y-6">
    <!-- Диагностический блок удален -->

    <!-- Отображение лимитов генераций -->
    <GenerationLimitsDisplay :type="ContentType.COURSE" />

    <!-- Форма генерации курса -->
    <div v-if="!showCourseView && !showLessonView && !showMyCourses" class="generator-form-block">
      <div class="flex justify-between items-center mb-6">
        <h2 class="generator-title">Course Generator</h2>
        <button
          @click="showMyCourses = true"
          class="generator-secondary-button"
        >
          My Courses
        </button>
      </div>

      <!-- Отображение статуса восстановления данных -->
      <JsonRecoveryStatus
        v-if="store.recoveryStatus !== 'none'"
        :status="store.recoveryStatus"
        :details="{
          recoveredFields: store.recoveryDetails.recoveredFields,
          missingFields: store.recoveryDetails.missingFields,
          messages: store.recoveryDetails.messages
        }"
        :actions="[
          {
            label: 'Очистить',
            handler: () => store.resetRecoveryInfo(),
            primary: false
          }
        ]"
      />

      <form @submit.prevent="generateCourse" class="space-y-6">
        <!-- Основная информация о курсе -->
        <div class="generator-grid grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="generator-form-group">
            <label class="generator-label">Course Name</label>
            <input
              v-model="formData.courseName"
              type="text"
              required
              class="generator-input mt-1 w-full"
            >
          </div>

          <div class="generator-form-group">
            <label class="generator-label">Language</label>
            <select
              v-model="formData.language"
              class="generator-select mt-1 w-full"
            >
              <option value="english">English</option>
              <option value="spanish">Spanish</option>
              <option value="french">French</option>
              <option value="german">German</option>
            </select>
          </div>
        </div>

        <!-- Целевые уровни и аудитория -->
        <div class="generator-grid grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="generator-form-group">
            <label class="generator-label">Start Level</label>
            <select
              v-model="formData.startLevel"
              class="generator-select mt-1 w-full"
            >
              <option v-for="level in levels" :key="level" :value="level">
                {{ formatLevel(level) }}
              </option>
            </select>
          </div>

          <div class="generator-form-group">
            <label class="generator-label">Target Level</label>
            <select
              v-model="formData.level"
              class="generator-select mt-1 w-full"
            >
              <option v-for="level in levels" :key="level" :value="level">
                {{ formatLevel(level) }}
              </option>
            </select>
          </div>

          <div class="generator-form-group">
            <label class="generator-label">Target Audience</label>
            <select
              v-model="formData.targetAudience"
              class="generator-select mt-1 w-full"
            >
              <option v-for="audience in audiences" :key="audience" :value="audience">
                {{ formatAudience(audience) }}
              </option>
            </select>
          </div>
        </div>

        <!-- Информация о студенте -->
        <div class="generator-grid grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="generator-form-group">
            <label class="generator-label">Student Interests</label>
            <input
              v-model="formData.interests"
              type="text"
              placeholder="music, sports, technology, travel..."
              class="generator-input mt-1 w-full"
            >
          </div>
        </div>

        <!-- Цели и ошибки -->
        <div class="space-y-4 generator-form-group">
          <div>
            <label class="generator-label">Student Goals</label>
            <textarea
              v-model="formData.goals"
              placeholder="e.g., fluent communication, reading technical literature, preparing for relocation..."
              class="generator-textarea mt-1 w-full"
              rows="2"
            ></textarea>
          </div>

          <div>
            <label class="generator-label">Common Student Mistakes</label>
            <textarea
              v-model="formData.commonMistakes"
              placeholder="e.g., problems with tenses, articles, prepositions..."
              class="generator-textarea mt-1 w-full"
              rows="2"
            ></textarea>
          </div>
        </div>

        <!-- Методика обучения -->
        <div class="generator-form-group">
          <label class="generator-label">Teaching Methodology</label>
          <select
            v-model="formData.methodology"
            class="generator-select mt-1 w-full"
          >
            <option v-for="method in methodologies" :key="method" :value="method">
              {{ formatMethodology(method) }}
            </option>
          </select>
          <p class="generator-description mt-1 text-xs">{{ getMethodologyDescription(formData.methodology) }}</p>
        </div>

        <!-- Структура курса -->
        <div class="generator-grid grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="generator-form-group">
            <label class="generator-label">Number of Lessons</label>
            <input
              v-model.number="formData.lessonsCount"
              type="number"
              min="1"
              max="30"
              required
              class="generator-input mt-1 w-full"
            >
          </div>

          <div class="generator-form-group">
            <label class="generator-label">Lesson Duration (minutes)</label>
            <input
              v-model.number="formData.lessonDuration"
              type="number"
              min="30"
              max="180"
              step="15"
              required
              class="generator-input mt-1 w-full"
            >
          </div>
        </div>

        <!-- Дополнительные настройки -->
        <div class="generator-form-group">
          <label class="generator-label">Learning Format</label>
          <select
            v-model="formData.format"
            class="generator-select mt-1 w-full"
          >
            <option v-for="format in formats" :key="format" :value="format">
              {{ formatFormat(format) }}
            </option>
          </select>
        </div>

        <!-- Контент курса -->
        <div class="space-y-4 generator-form-group">
          <div>
            <label class="generator-label">Main Topics (comma separated)</label>
            <textarea
              v-model="formData.mainTopics"
              class="generator-textarea mt-1 w-full"
              rows="3"
            ></textarea>
          </div>

          <div class="generator-grid grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="generator-label">Grammar</label>
              <textarea
                v-model="formData.grammarFocus"
                class="generator-textarea mt-1 w-full"
                rows="2"
              ></textarea>
            </div>

            <div>
              <label class="generator-label">Vocabulary</label>
              <textarea
                v-model="formData.vocabularyFocus"
                class="generator-textarea mt-1 w-full"
                rows="2"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Навыки -->
        <div class="space-y-4 generator-form-group">
          <label class="generator-label">Skills to Include</label>
          <div class="generator-grid grid grid-cols-2 md:grid-cols-4 gap-4">
            <label class="generator-checkbox-label flex items-center space-x-2">
              <input
                v-model="formData.includeSpeaking"
                type="checkbox"
                class="generator-checkbox"
              >
              <span class="generator-checkbox-text">Speaking</span>
            </label>

            <label class="generator-checkbox-label flex items-center space-x-2">
              <input
                v-model="formData.includeListening"
                type="checkbox"
                class="generator-checkbox"
              >
              <span class="generator-checkbox-text">Listening</span>
            </label>

            <label class="generator-checkbox-label flex items-center space-x-2">
              <input
                v-model="formData.includeReading"
                type="checkbox"
                class="generator-checkbox"
              >
              <span class="generator-checkbox-text">Reading</span>
            </label>

            <label class="generator-checkbox-label flex items-center space-x-2">
              <input
                v-model="formData.includeWriting"
                type="checkbox"
                class="generator-checkbox"
              >
              <span class="generator-checkbox-text">Writing</span>
            </label>
          </div>
        </div>

        <!-- Подготовка к экзамену -->
        <div class="space-y-4 generator-form-group">
          <div>
            <label class="generator-label">Exam Preparation</label>
            <select
              v-model="formData.examPrep"
              class="generator-select mt-1 w-full"
            >
              <option value="">Not Required</option>
              <option value="TOEFL">TOEFL</option>
              <option value="IELTS">IELTS</option>
              <option value="Cambridge B2 First">Cambridge B2 First (FCE)</option>
              <option value="Cambridge C1 Advanced">Cambridge C1 Advanced (CAE)</option>
              <option value="Cambridge C2 Proficiency">Cambridge C2 Proficiency (CPE)</option>
              <option value="DELF">DELF (French)</option>
              <option value="DELE">DELE (Spanish)</option>
              <option value="Goethe">Goethe-Zertifikat (German)</option>
              <option value="Custom">Other (specify below)</option>
            </select>
          </div>

          <div v-if="formData.examPrep === 'Custom'">
            <label class="generator-label">Specify Exam</label>
            <input
              v-model="formData.customExam"
              type="text"
              placeholder="Exam name"
              class="generator-input mt-1 w-full"
            >
          </div>

          <div v-if="formData.examPrep">
            <label class="generator-label">Exam Preparation Duration (lessons)</label>
            <input
              v-model.number="formData.examPrepLessons"
              type="number"
              min="1"
              :max="formData.lessonsCount"
              required
              class="generator-input mt-1 w-full"
            >
          </div>
        </div>

        <!-- Информация о лимитах и баллах -->
        <div class="generator-limits-info pt-2 pb-2">
          <GenerationLimitsDisplay :content-type="ContentType.COURSE" />
          <div class="points-info mt-2">
            <span class="points-icon">💎</span> Points: {{ userPoints }}
            <span class="points-cost">(Cost: 8 points)</span>
          </div>
        </div>

        <!-- Кнопки генерации -->
        <div class="generator-form-actions pt-4 space-y-2">
          <button
            type="submit"
            :disabled="isGenerating"
            class="generator-button w-full"
          >
            <span v-if="isGenerating" class="generator-loader"></span>
            {{ isGenerating ? 'Generating course...' : 'Generate Course' }}
          </button>

          <button
            type="button"
            @click="generateCourseWithPoints"
            :disabled="isGenerating || userPoints < 8"
            class="generator-button-points w-full"
          >
            <span v-if="isGenerating" class="generator-loader"></span>
            <span class="points-icon">💎</span> Generate for Points
          </button>
        </div>
      </form>
    </div>

    <!-- Отображение сгенерированного курса -->
    <CourseView
      v-if="showCourseView && generatedCourse"
      :course="generatedCourse"
      :show-lesson-planner="false"
      @close="closeCourseView"
    />

    <!-- УДАЛЕНО: Блок упрощенного отображения -->

    <!-- Отображение сгенерированного одиночного урока -->
    <LessonView
      v-if="showLessonView && generatedLesson"
      :lesson="generatedLesson"
      :courseName="generatedCourse?.name"
      @back="resetView"
      @generate-plan="handleGeneratePlan"
      @generate-plan-with-points="handleGeneratePlanWithPoints"
      @generate-exercises="handleGenerateExercises"
      @generate-exercises-with-points="handleGenerateExercisesWithPoints"
      @generate-game="handleGenerateGame"
      @generate-game-with-points="handleGenerateGameWithPoints"
      @export="handleExport"
    />

    <!-- Отображение сгенерированного текстового плана урока -->
    <GeneratedLessonPlanView
      :planContent="generatedLessonPlanText"
      :isLoading="isPlanLoading"
      :isVisible="isLessonPlanVisible"
      @toggle-visibility="isLessonPlanVisible = !isLessonPlanVisible"
    />

    <!-- Отображение списка сохраненных курсов -->
    <MyCourses
      v-if="showMyCourses"
      @back="showMyCourses = false"
    />
  </div>

  <!-- Загрузочный экран для случаев когда данные пользователя еще не загружены -->
  <div v-else class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
    <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useCourseStore } from '../store/course'
import type { CourseFormData, CourseStructure, Lesson } from '@/types/course'
import CourseView from './CourseView.vue'
import LessonView from './LessonView.vue'
import GeneratedLessonPlanView from './GeneratedLessonPlanView.vue'
import GenerationLimitsDisplay from './common/GenerationLimitsDisplay.vue'
import { ContentType } from '@/types/enums' // Используем импорт из types/enums
import { useMainStore } from '@/store'
import JsonRecoveryStatus from './common/JsonRecoveryStatus.vue'
import MyCourses from './MyCourses.vue' // Импортируем компонент MyCourses
import PremiumRequired from './access/PremiumRequired.vue'
import { usePremiumAccess } from '@/composables/usePremiumAccess'


// Определение интерфейсов для методов, которых нет в типах
interface ExtendedCourseStore {
  generateCourse: (formData: CourseFormData) => Promise<any>;
  generateCourseWithPoints: (formData: CourseFormData) => Promise<any>; // Добавляем метод для генерации за баллы
  generateLessonPlan: (lessonData: any) => Promise<any>; // Можно оставить для совместимости, если нужно
  fetchGeneratedLessonPlanText: (lessonData: any, courseContext: CourseFormData) => Promise<string | null>;
  fetchGeneratedLessonPlanTextWithPoints: (lessonData: any, courseContext: CourseFormData) => Promise<string | null>; // Добавляем метод для генерации за баллы
  generateLessonExercises: (lessonData: any) => Promise<any>;
  fetchGeneratedExercises: (lessonData: any, courseContext: CourseFormData) => Promise<string | null>;
  fetchGeneratedExercisesWithPoints: (lessonData: any, courseContext: CourseFormData) => Promise<string | null>; // Добавляем метод для генерации за баллы
  fetchGeneratedGame: (lessonData: any, courseContext: CourseFormData, gameType?: string) => Promise<any>;
  fetchGeneratedGameWithPoints: (lessonData: any, courseContext: CourseFormData, gameType?: string) => Promise<any>; // Добавляем метод для генерации за баллы
  // Добавляем новые свойства и методы
  recoveryStatus: 'success' | 'partial' | 'failure' | 'none';
  recoveryDetails: {
    recoveredFields: string[];
    missingFields: string[];
    messages: string[];
    timestamp: string;
  };
  resetRecoveryInfo: () => void;
}

const store = useCourseStore() as unknown as ExtendedCourseStore
const mainStore = useMainStore()
const { hasPremiumAccess, isUserLoaded } = usePremiumAccess()

// --- НЕВЕРНО РАЗМЕЩЕННЫЙ ЛОГ УДАЛЕН ---

const levels = ['beginner', 'elementary', 'intermediate', 'upper_intermediate', 'advanced']
const formats = ['online', 'offline', 'hybrid']
const audiences = ['children', 'teens', 'adults', 'business']
const methodologies = ['communicative', 'task-based', 'natural', 'lexical', 'grammar-translation', 'audio-lingual', 'direct', 'total-physical-response']

const isGenerating = ref(false)
const showCourseView = ref(false)
const showLessonView = ref(false)
const showMyCourses = ref(false) // Добавляем переменную для отображения списка курсов

// Добавляем вычисляемое свойство для баллов пользователя
const userPoints = computed(() => mainStore.user?.points || 0)

// Базовая форма данных
const formData = ref<CourseFormData>({
  courseName: '',
  language: 'english',
  level: 'beginner',
  startLevel: 'beginner',
  targetAudience: 'adults',
  format: 'online',
  examPrep: '',
  examPrepLessons: 0,
  lessonsCount: 12,
  lessonDuration: 60,
  mainTopics: '',
  grammarFocus: '',
  vocabularyFocus: '',
  includeSpeaking: true,
  includeListening: true,
  includeReading: true,
  includeWriting: true,
  includeGames: true,
  methodology: 'communicative',
  age: 'adults',
  interests: '',
  goals: '',
  commonMistakes: ''
})

interface Activity {
  id: number;
  name: string;
  type: string;
  duration: number;
  description: string;
  materials?: string[];
  objectives?: string[];
}

interface SimplifiedLesson {
  id?: number;
  title: string;
  objectives?: string[];
  grammar?: string[];
  vocabulary?: string[];
  duration?: number;
  activities?: Activity[];
  materials?: string[];
  homework?: {
    description: string;
    tasks: string[];
    estimatedTime?: number;
  };
  order?: number;
}

// Сгенерированные данные
const generatedCourse = ref<CourseStructure | null>(null)
const generatedLesson = ref<SimplifiedLesson | null>(null)
const generatedLessonPlanText = ref<string | null>(null) // Для хранения текста плана
const isPlanLoading = ref(false) // Для статуса загрузки плана
const isLessonPlanVisible = ref(true) // Новое состояние для видимости плана одиночного урока


// Флаг подготовки к экзамену
const isExamPrep = computed(() => !!formData.value.examPrep)

// Методы форматирования
const formatLevel = (level: string) => {
  const labels: Record<string, string> = {
    'beginner': 'A1 - Beginner',
    'elementary': 'A2 - Elementary',
    'intermediate': 'B1 - Intermediate',
    'upper_intermediate': 'B2 - Upper Intermediate',
    'upper-intermediate': 'B2 - Upper Intermediate',
    'advanced': 'C1 - Advanced'
  }
  return labels[level] || level
}

const formatAudience = (audience: string) => {
  const labels: Record<string, string> = {
    'children': 'Children',
    'teens': 'Teens',
    'adults': 'Adults',
    'business': 'Business'
  }
  return labels[audience] || audience
}

const getMethodologyDescription = (methodology: string) => {
  const descriptions: Record<string, string> = {
    'communicative': 'Communicative approach focuses on using language in real communication contexts.',
    'task-based': 'Task-based learning centers around completing practical tasks.',
    'natural': 'Natural method mimics natural language acquisition.',
    'lexical': 'Lexical approach focuses on learning lexical chunks.',
    'grammar-translation': 'Grammar-translation method focuses on grammar and translation.',
    'audio-lingual': 'Audio-lingual method is based on repeated practice.',
    'direct': 'Direct method excludes the use of the native language.',
    'total-physical-response': 'Total Physical Response connects language with physical actions.'
  }
  return descriptions[methodology] || ''
}

// Методы работы с API
const generateCourse = async () => {
  isGenerating.value = true
  showCourseView.value = false
  showLessonView.value = false

  try {
    // Лог состояния перед генерацией
    console.log('State before course generation:', {
        userStats: mainStore.userStats,
        tariffInfo: mainStore.tariffInfo,
        canGenerateResult: mainStore.canGenerate(ContentType.COURSE)
    });

     // === ДОБАВЛЕНО: Проверка наличия информации о тарифе ===
    if (!mainStore.tariffInfo && mainStore.user?.tariff) {
        console.warn('[generateCourse] Tariff info missing but user has tariff, trying to fetch it...');
        try {
            // Пробуем загрузить информацию о тарифе
            await mainStore.fetchUserTariff();

            // Если после попытки загрузки информация о тарифе все еще отсутствует
            if (!mainStore.tariffInfo) {
                console.error('[generateCourse] Failed to fetch tariff info after retry');
                alert('Failed to load tariff information. Please try refreshing the page.');
                isGenerating.value = false;
                return;
            }
        } catch (tariffError) {
            console.error('[generateCourse] Error fetching tariff info:', tariffError);
            alert('Error loading tariff information. Please try refreshing the page.');
            isGenerating.value = false;
            return;
        }
    }

    // === ДОБАВЛЕНО: Явная проверка лимитов ПОСЛЕ обновления состояния ===
    if (!mainStore.canGenerate(ContentType.COURSE)) {
        // Проверяем причину отказа в генерации
        let errorMsg = 'Failed to perform generation.';

        if (!mainStore.tariffInfo) {
            errorMsg = 'Tariff information is not loaded. Please try refreshing the page.';
        } else if (mainStore.userStats && mainStore.tariffInfo.limits) {
            const currentGenCount = mainStore.userStats.dailyGenerations;
            const limit = mainStore.tariffInfo.limits.generations;

            if (currentGenCount >= limit) {
                errorMsg = `Daily generation limit reached (${currentGenCount}/${limit}) for your tariff.`;
            }
        } else {
            errorMsg = 'Failed to check generation limits. Please try refreshing the page.';
        }

        console.error('[generateCourse] Limit check failed:', {
            tariffInfo: mainStore.tariffInfo,
            userStats: mainStore.userStats
        });

        alert(errorMsg); // TODO: Заменить на toast уведомление
        isGenerating.value = false; // Останавливаем индикатор загрузки
        return; // Прерываем выполнение функции
    }
    // === КОНЕЦ ДОБАВЛЕННОЙ ПРОВЕРКИ ===

    // Проверяем, что все обязательные поля-перечисления имеют допустимые значения
    const formDataCopy = { ...formData.value };

    // Проверяем start_level, если оно пустое, используем level
    if (!formDataCopy.startLevel) {
      formDataCopy.startLevel = formDataCopy.level;
    }

    // Преобразуем 'upper-intermediate' в 'upper_intermediate', так как в бэкенде используется underscore
    if (formDataCopy.startLevel === 'upper-intermediate') {
      formDataCopy.startLevel = 'upper_intermediate';
    }
    if (formDataCopy.level === 'upper-intermediate') {
      formDataCopy.level = 'upper_intermediate';
    }

    // Проверяем другие поля-перечисления
    if (!formDataCopy.targetAudience) formDataCopy.targetAudience = 'adults';
    if (!formDataCopy.format) formDataCopy.format = 'online';
    if (!formDataCopy.methodology) formDataCopy.methodology = 'communicative';

    // ---> СТАРЫЙ ЛОГ УДАЛЕН <---

    // Теперь вызываем генерацию курса из useCourseStore
    const result = await store.generateCourse(formDataCopy) // 'store' здесь относится к useCourseStore

    // Обрабатываем результат
    processGenerationResult(result)
  } catch (error: any) {
    console.error('Error generating course:', error)
    alert(`Error generating course: ${error.message || 'Unknown error'}`)
  } finally {
    isGenerating.value = false
  }
}

// Метод для генерации курса за баллы
const generateCourseWithPoints = async () => {
  isGenerating.value = true
  showCourseView.value = false
  showLessonView.value = false

  try {
    // Проверяем, что все обязательные поля заполнены
    if (!formData.value.courseName) {
      throw new Error('Please specify the course name')
    }

    if (!formData.value.language) {
      throw new Error('Please select a language')
    }

    if (!formData.value.level) {
      throw new Error('Please select a target level')
    }

    // Проверяем, что все обязательные поля-перечисления имеют допустимые значения
    const formDataCopy = { ...formData.value };

    // Проверяем start_level, если оно пустое, используем level
    if (!formDataCopy.startLevel) {
      formDataCopy.startLevel = formDataCopy.level;
    }

    // Преобразуем 'upper-intermediate' в 'upper_intermediate', так как в бэкенде используется underscore
    if (formDataCopy.startLevel === 'upper-intermediate') {
      formDataCopy.startLevel = 'upper_intermediate';
    }
    if (formDataCopy.level === 'upper-intermediate') {
      formDataCopy.level = 'upper_intermediate';
    }

    // Проверяем другие поля-перечисления
    if (!formDataCopy.targetAudience) formDataCopy.targetAudience = 'adults';
    if (!formDataCopy.format) formDataCopy.format = 'online';
    if (!formDataCopy.methodology) formDataCopy.methodology = 'communicative';

    // Вызываем генерацию курса за баллы из useCourseStore
    const result = await store.generateCourseWithPoints(formDataCopy)

    // Обрабатываем результат
    processGenerationResult(result)
  } catch (error: any) {
    console.error('Error generating course with points:', error)
    alert(`Error generating course with points: ${error.message || 'Unknown error'}`)
  } finally {
    isGenerating.value = false
  }
}

// Метод для обработки результатов генерации
const processGenerationResult = (result: any) => {
  if (result) {
    if (result.lessons && Array.isArray(result.lessons) && result.lessons.length > 0) {
      // Полный курс
      // Добавляем пустое поле homework для каждого урока, если его нет
      const processedLessons = result.lessons.map((lesson: any) => {
        if (!lesson.homework) {
          return {
            ...lesson,
            homework: {
              description: '',
              tasks: []
            }
          };
        }
        return lesson;
      });

      // Добавляем отладочный код
      console.log('Курс перед отображением:', JSON.stringify({
        id: result.id,
        name: result.name,
        lessonsCount: result.lessons.length,
        // Показываем первые несколько уроков
        sampleLessons: processedLessons.slice(0, 2)
      }, null, 2));

      try {
        generatedCourse.value = {
          ...result,
          lessons: processedLessons
        } as CourseStructure;
        showCourseView.value = true;
        console.log('CourseView показан:', showCourseView.value);
      } catch (viewError) {
        console.error('Ошибка при установке данных для CourseView:', viewError);
        alert('An error occurred while displaying the course. Details in console.');
      }
    } else if (result.title && (
      (result.objectives && Array.isArray(result.objectives)) ||
      (result.grammar && Array.isArray(result.grammar)) ||
      (result.vocabulary && Array.isArray(result.vocabulary))
    )) {
      // Одиночный урок
      // Добавляем недостающие свойства для корректного приведения типов
      const lessonWithRequiredProps = {
        ...result,
        id: result.id ?? 0,
        order: result.order ?? 0,
        duration: result.duration ?? 60,
        objectives: result.objectives ?? [],
        grammar: result.grammar ?? [],
        vocabulary: result.vocabulary ?? [],
        // Обеспечиваем корректные activities
        activities: (result.activities || []).map((act: any, index: number) => ({
          id: act.id ?? index + 1, // Если id нет, используем индекс + 1
          name: act.name,
          type: act.type ?? 'activity', // Если type нет, используем 'activity'
          duration: act.duration,
          description: act.description,
          materials: act.materials,
          objectives: act.objectives
        })),
        materials: result.materials || [],
        homework: {
          description: result.homework?.description || '',
          tasks: result.homework?.tasks || []
        }
      };

      // Создаем тип с необходимыми обязательными полями для CourseStructure
      type RequiredLesson = {
        id: number;
        title: string;
        order: number;
        objectives: string[];
        grammar: string[];
        vocabulary: string[];
        duration: number;
        activities: Activity[];
        materials: string[];
        homework: {
          description: string;
          tasks: string[];
        };
      };

      // Гарантируем наличие всех необходимых полей
      const requiredLesson = lessonWithRequiredProps as RequiredLesson;
      generatedLesson.value = requiredLesson;

      // Создаем базовую структуру курса для контекста
      generatedCourse.value = {
        id: 0,
        name: `Курс с уроком: ${result.title}`,
        language: formData.value.language,
        level: formData.value.level,
        targetAudience: formData.value.targetAudience,
        format: formData.value.format,
        totalDuration: result.duration || 60,
        description: `Курс, сгенерированный из одиночного урока: ${result.title}`,
        lessons: [requiredLesson]
      }
      showLessonView.value = true
    } else {
      // Неизвестный формат ответа
      console.error('Неизвестный формат ответа API:', result)
      alert('Получен неизвестный формат данных от API. Проверьте консоль для деталей.')
    }
  } else {
    // Пустой ответ
    alert('Failed to generate course. Please try again.')
  }
}

// Сброс представления к форме
const resetView = () => {
  showCourseView.value = false
  showLessonView.value = false
  showMyCourses.value = false // Сбрасываем отображение списка курсов
  generatedLessonPlanText.value = null // Сбрасываем текст плана при возврате
}

// Обработчики событий для LessonView
const handleGeneratePlan = async (lesson: SimplifiedLesson) => {
  if (!lesson) return

  isPlanLoading.value = true
  generatedLessonPlanText.value = null // Очищаем предыдущий план
  try {
    // Вызываем НОВЫЙ метод хранилища, передавая урок и контекст курса
    // Убедимся, что передаем lesson и formData.value
    // Убедитесь, что метод fetchGeneratedLessonPlanText существует в вашем store/course.ts
    if (typeof store.fetchGeneratedLessonPlanText !== 'function') {
       throw new Error('Метод fetchGeneratedLessonPlanText не найден в хранилище course store.');
    }
    const planText = await store.fetchGeneratedLessonPlanText(lesson, formData.value) // <-- ПРАВИЛЬНЫЙ ВЫЗОВ
    generatedLessonPlanText.value = planText // <-- СОХРАНЕНИЕ РЕЗУЛЬТАТА
    isLessonPlanVisible.value = true // Показываем план при успешной генерации
    // Убираем alert, так как результат теперь отображается
  } catch (error: any) {
    console.error('Error generating lesson plan:', error)
    // Отображаем ошибку в блоке плана
    generatedLessonPlanText.value = `Error during generation: ${error.message || 'Unknown error'}`
    isLessonPlanVisible.value = true // Показываем блок с ошибкой
    // Можно также показать alert или использовать систему уведомлений
    // alert(`Ошибка при генерации плана урока: ${error.message || 'Неизвестная ошибка'}`)
  } finally {
    isPlanLoading.value = false
  }
}

// Метод для генерации плана урока за баллы
const handleGeneratePlanWithPoints = async (lesson: SimplifiedLesson) => {
  if (!lesson) return

  isPlanLoading.value = true
  generatedLessonPlanText.value = null // Очищаем предыдущий план
  try {
    // Проверяем наличие метода
    if (typeof store.fetchGeneratedLessonPlanTextWithPoints !== 'function') {
       throw new Error('Метод fetchGeneratedLessonPlanTextWithPoints не найден в хранилище course store.');
    }

    // Вызываем метод для генерации за баллы
    const planText = await store.fetchGeneratedLessonPlanTextWithPoints(lesson, formData.value)
    generatedLessonPlanText.value = planText
    isLessonPlanVisible.value = true // Показываем план при успешной генерации
  } catch (error: any) {
    console.error('Error generating lesson plan with points:', error)
    // Отображаем ошибку в блоке плана
    generatedLessonPlanText.value = `Error during generation with points: ${error.message || 'Unknown error'}`
    isLessonPlanVisible.value = true
  } finally {
    isPlanLoading.value = false
  }
}

const handleGenerateExercises = async (lesson: SimplifiedLesson) => {
  if (!lesson) return

  try {
    // Проверяем наличие нового метода
    if (typeof store.fetchGeneratedExercises === 'function') {
      const exercisesText = await store.fetchGeneratedExercises(lesson, formData.value)
      if (exercisesText) {
        alert('Упражнения успешно сгенерированы!')
      } else {
        throw new Error('Failed to get exercises text')
      }
    } else {
      // Используем старый метод для обратной совместимости
      await store.generateLessonExercises({
        id: lesson.id,
        title: lesson.title,
        level: formData.value.level,
        grammar: lesson.grammar,
        vocabulary: lesson.vocabulary
      })
      alert('Упражнения успешно сгенерированы!')
    }
  } catch (error: any) {
    console.error('Error generating exercises:', error)
    alert(`Error generating exercises: ${error.message || 'Unknown error'}`)
  }
}

// Метод для генерации упражнений за баллы
const handleGenerateExercisesWithPoints = async (lesson: SimplifiedLesson) => {
  if (!lesson) return

  try {
    // Проверяем наличие метода
    if (typeof store.fetchGeneratedExercisesWithPoints !== 'function') {
      throw new Error('Метод fetchGeneratedExercisesWithPoints не найден в хранилище course store.')
    }

    // Вызываем метод для генерации за баллы
    const exercisesText = await store.fetchGeneratedExercisesWithPoints(lesson, formData.value)
    if (exercisesText) {
      alert('Упражнения успешно сгенерированы за баллы!')
    } else {
      throw new Error('Failed to get exercises text')
    }
  } catch (error: any) {
    console.error('Error generating exercises with points:', error)
    alert(`Error generating exercises with points: ${error.message || 'Unknown error'}`)
  }
}

interface ExportParams {
  lesson: SimplifiedLesson;
  format: 'pdf' | 'docx';
}

// Обработчик для генерации игры
const handleGenerateGame = async (lesson: SimplifiedLesson) => {
  if (!lesson) return

  try {
    // Здесь должен быть код для генерации игры
    console.log(`Генерация игры для урока "${lesson.title}"`)
    alert(`Генерация игры для урока "${lesson.title}" запущена!`)
  } catch (error: any) {
    console.error('Error generating game:', error)
    alert(`Error generating game: ${error.message || 'Unknown error'}`)
  }
}

// Обработчик для генерации игры за баллы
const handleGenerateGameWithPoints = async (lesson: SimplifiedLesson) => {
  if (!lesson) return

  try {
    // Здесь должен быть код для генерации игры за баллы
    console.log(`Генерация игры за баллы для урока "${lesson.title}"`)
    alert(`Генерация игры за баллы для урока "${lesson.title}" запущена!`)
  } catch (error: any) {
    console.error('Error generating game with points:', error)
    alert(`Error generating game with points: ${error.message || 'Unknown error'}`)
  }
}

const handleExport = async ({ lesson, format }: ExportParams) => {
  if (!lesson) return

  try {
    // Здесь должен быть код для экспорта урока
    console.log(`Экспорт урока "${lesson.title}" в формате ${format}`)
    alert(`Экспорт урока в формате ${format.toUpperCase()} запущен!`)
  } catch (error: any) {
    console.error('Error exporting lesson:', error)
    alert(`Error exporting lesson: ${error.message || 'Unknown error'}`)
  }
}

const formatFormat = (format: string) => {
  const names: Record<string, string> = {
    'online': 'Online',
    'offline': 'Offline',
    'hybrid': 'Hybrid'
  }
  return names[format] || format
}

const formatMethodology = (methodology: string) => {
  const names: Record<string, string> = {
    'communicative': 'Communicative',
    'task-based': 'Task-based',
    'natural': 'Natural',
    'lexical': 'Lexical',
    'grammar-translation': 'Grammar Translation',
    'audio-lingual': 'Audio-lingual',
    'direct': 'Direct',
    'total-physical-response': 'Total Physical Response'
  }
  return names[methodology] || methodology.charAt(0).toUpperCase() + methodology.slice(1)
}

// Добавляем логирование при изменении ключевых переменных
watch(() => generatedCourse, (newVal) => {
  console.log('[DEBUG] generatedCourse изменился:', newVal ? 'Есть данные' : 'Нет данных', newVal);
}, { deep: true });

watch(() => showCourseView, (newVal) => {
  console.log('[DEBUG] showCourseView изменился:', newVal);
});

// УДАЛЕНО: Логирование useSimpleView и определение Telegram

onMounted(() => {
  console.log('[DEBUG] CourseGenerator mounted');
  // Явно выводим начальные значения
  console.log('[DEBUG] Начальные значения:');
  console.log('- showCourseView:', showCourseView.value);
  console.log('- generatedCourse:', generatedCourse.value ? 'Есть данные' : 'Нет данных');
});

// Определяем метод closeCourseView, который был упомянут, но не определен
const closeCourseView = () => {
  showCourseView.value = false
  showMyCourses.value = false // Сбрасываем отображение списка курсов при закрытии просмотра курса
}
</script>

<style>
/* Стилизация результатов */
.course-content {
  all: initial !important; /* Сбрасываем все стили */
  display: block !important; /* Восстанавливаем блочное отображение */
  font-family: Arial, sans-serif !important; /* Более читаемый шрифт */
  background: #ffffff !important; /* Полностью белый фон */
  color: #000000 !important; /* Полностью черный текст */
  padding: 1.5rem !important;
  border-radius: 8px !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
  margin-top: 1rem;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.3) !important; /* Усиленная тень */
  border: 2px solid #000 !important; /* Черная рамка для контраста */
  position: relative !important; /* Добавляем позиционирование */
  z-index: 10 !important; /* Высокий z-index для перекрытия других элементов */
  isolation: isolate !important; /* Изолируем от внешних стилей */
}

/* Переопределяем стили для лучшей читаемости */
:deep(.prose) {
  all: initial !important;
  display: block !important;
  color: #000000 !important;
  max-width: none !important;
  font-family: Arial, sans-serif !important;
  line-height: 1.6 !important;
  font-size: 1rem !important;
}

:deep(.prose h1),
:deep(.prose h2),
:deep(.prose h3),
:deep(.prose h4),
:deep(.prose h5),
:deep(.prose h6) {
  all: revert !important;
  color: #ffffff !important;
  font-weight: bold !important;
  background-color: #4caf50 !important; /* Зеленый фон для заголовков */
  padding: 0.75rem 1rem !important;
  border-radius: 5px !important;
  display: block !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
  margin-bottom: 1rem !important;
  margin-top: 1.5rem !important;
  position: relative !important;
  z-index: 12 !important;
  font-family: Arial, sans-serif !important;
  line-height: 1.6 !important;
}

:deep(.prose h1) {
  font-size: 1.4rem !important;
}

:deep(.prose h2) {
  font-size: 1.3rem !important;
}

:deep(.prose h3) {
  font-size: 1.2rem !important;
}

:deep(.prose h4) {
  font-size: 1.1rem !important;
  background-color: #81c784 !important; /* Более светлый зеленый фон для подзаголовков */
}

:deep(.prose p) {
  all: revert !important;
  margin-bottom: 1rem !important;
  background-color: #f8f8f8 !important; /* Светло-серый фон для параграфов */
  padding: 0.75rem !important;
  border-radius: 4px !important;
  color: #000000 !important; /* Принудительно черный текст */
  font-weight: normal !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  border-left: 4px solid #4caf50 !important; /* Зеленая полоса слева */
  position: relative !important;
  z-index: 11 !important;
  font-family: Arial, sans-serif !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
  display: block !important;
}

:deep(.prose ul),
:deep(.prose ol) {
  all: revert !important;
  margin-bottom: 1.5rem !important;
  background-color: #f0f0f0 !important; /* Более светлый фон для списков */
  padding: 0.75rem 0.75rem 0.75rem 2.5rem !important;
  border-radius: 4px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  border-left: 4px solid #4caf50 !important;
  position: relative !important;
  z-index: 11 !important;
  display: block !important;
  font-family: Arial, sans-serif !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
}

:deep(.prose ul) {
  list-style-type: disc !important;
}

:deep(.prose ol) {
  list-style-type: decimal !important;
}

:deep(.prose li) {
  all: revert !important;
  margin-bottom: 0.5rem !important;
  color: #000000 !important;
  padding: 0.3rem 0 !important;
  font-weight: normal !important;
  position: relative !important;
  z-index: 12 !important;
  display: list-item !important;
  font-family: Arial, sans-serif !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
}

:deep(.prose strong) {
  all: revert !important;
  font-weight: bold !important;
  color: #000000 !important;
  background-color: #c8e6c9 !important; /* Светло-зеленый фон для жирного текста */
  padding: 0 5px !important;
  border-radius: 3px !important;
  border-bottom: 1px solid #4caf50 !important;
  position: relative !important;
  z-index: 13 !important;
  display: inline-block !important;
  font-family: Arial, sans-serif !important;
}

:deep(.prose em) {
  all: revert !important;
  font-style: italic !important;
  color: #000000 !important;
  font-weight: 600 !important;
  background-color: #e8f5e9 !important; /* Светло-зеленый фон для курсива */
  padding: 0 5px !important;
  border-radius: 3px !important;
  display: inline-block !important;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.2) !important;
  border-bottom: 1px solid #4caf50 !important;
  position: relative !important;
  z-index: 13 !important;
  font-family: Arial, sans-serif !important;
}

:deep(.prose code) {
  all: revert !important;
  font-family: monospace !important;
  background-color: #f0f0f0 !important;
  color: #000000 !important;
  padding: 0.2rem 0.4rem !important;
  border-radius: 3px !important;
  border: 1px solid #ddd !important;
  font-size: 0.9rem !important;
  position: relative !important;
  z-index: 13 !important;
}

/* Медиа запросы для адаптивности */
@media (max-width: 768px) {
  .course-content {
    all: initial !important;
    display: block !important;
    font-size: 0.95rem !important;
    padding: 1rem !important;
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #000 !important;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.3) !important;
    position: relative !important;
    z-index: 100 !important;
    isolation: isolate !important;
    font-family: Arial, sans-serif !important;
    line-height: 1.6 !important;
    text-align: left !important;
    margin-top: 1rem;
  }

  :deep(.prose h1),
  :deep(.prose h2),
  :deep(.prose h3),
  :deep(.prose h4) {
    all: revert !important;
    font-size: 1.1rem !important;
    padding: 0.6rem 0.8rem !important;
    margin-top: 1.2rem !important;
    margin-bottom: 0.8rem !important;
    display: block !important;
    position: relative !important;
    z-index: 101 !important;
    width: 100% !important;
    box-sizing: border-box !important;
    color: #ffffff !important;
    font-weight: bold !important;
    background-color: #4caf50 !important;
    border-radius: 5px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    font-family: Arial, sans-serif !important;
    line-height: 1.6 !important;
  }

  :deep(.prose h4) {
    background-color: #81c784 !important;
    font-size: 1rem !important;
  }

  :deep(.prose p) {
    all: revert !important;
    padding: 0.6rem !important;
    margin-bottom: 0.8rem !important;
    position: relative !important;
    z-index: 101 !important;
    width: 100% !important;
    box-sizing: border-box !important;
    background-color: #ffffff !important;
    border: 1px solid #ddd !important;
    color: #000000 !important;
    font-weight: normal !important;
    border-left: 4px solid #4caf50 !important;
    border-radius: 4px !important;
    font-family: Arial, sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    display: block !important;
  }

  :deep(.prose ul),
  :deep(.prose ol) {
    all: revert !important;
    padding: 0.6rem 0.6rem 0.6rem 2rem !important;
    margin-bottom: 1rem !important;
    position: relative !important;
    z-index: 101 !important;
    width: 100% !important;
    box-sizing: border-box !important;
    background-color: #ffffff !important;
    border: 1px solid #ddd !important;
    border-left: 4px solid #4caf50 !important;
    border-radius: 4px !important;
    font-family: Arial, sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    display: block !important;
  }

  :deep(.prose li) {
    all: revert !important;
    padding: 0.25rem 0 !important;
    position: relative !important;
    z-index: 102 !important;
    color: #000000 !important;
    font-weight: normal !important;
    margin-bottom: 0.5rem !important;
    display: list-item !important;
    font-family: Arial, sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
  }

  :deep(.prose em),
  :deep(.prose strong) {
    all: revert !important;
    padding: 0 4px !important;
    position: relative !important;
    z-index: 103 !important;
    color: #000000 !important;
    background-color: #e8f5e9 !important;
    display: inline-block !important;
    font-family: Arial, sans-serif !important;
    border-radius: 3px !important;
  }

  :deep(.prose em) {
    font-style: italic !important;
    font-weight: 600 !important;
    border-bottom: 1px solid #4caf50 !important;
  }

  :deep(.prose strong) {
    font-weight: bold !important;
    background-color: #c8e6c9 !important;
    border-bottom: 1px solid #4caf50 !important;
  }

  /* Добавляем стили для лоадера на мобильных */
  .generator-loader {
    width: 16px !important; /* Уменьшаем размер */
    height: 16px !important;
    border-width: 2px !important; /* Делаем обводку тоньше */
    margin-right: 0.3rem !important; /* Уменьшаем отступ */
  }
}

.debug-panel {
  font-family: monospace;
  border: 1px solid #ff6b6b;
}

/* --- Стили, скопированные и адаптированные из Exercises.vue --- */

.generator-container {
  /* background: #1c0522 url('@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg'); */ /* Фон удален, используется глобальный */
  /* background-size: cover; */
  /* background-position: center; */
  /* background-repeat: no-repeat; */
  padding: 2rem; /* Добавляем общий паддинг */
  border-radius: 1rem; /* Скругление для контейнера */
  /* box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(139, 92, 246, 0.3); */ /* Тень тоже уберем, т.к. фон теперь глобальный */
}

.generator-form-block {
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.5rem; /* Увеличим паддинг */
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  margin-bottom: 1.5rem; /* Добавим отступ снизу */
}

.generator-title {
  color: white;
  font-size: 1.8rem; /* Увеличим немного */
  margin: 0;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.9;
  text-align: center; /* Центрируем заголовок формы */
}

.generator-form-group {
  margin-bottom: 1rem; /* Отступ между группами полей */
  /* Убираем фон и тень с отдельных групп, т.к. есть общий фон блока */
}

.generator-label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
  font-size: 0.9rem; /* Немного уменьшим */
}

.generator-input,
.generator-select,
.generator-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  border: none;
  background-color: rgba(255, 204, 243, 0.7);
  color: #333;
  font-size: 1rem;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.generator-input:focus,
.generator-select:focus,
.generator-textarea:focus {
  box-shadow: 0 0 0 3px rgba(255, 103, 231, 0.4), inset 0 2px 6px rgba(0, 0, 0, 0.1);
  outline: none;
}

.generator-textarea {
  resize: vertical; /* Разрешаем изменять размер по вертикали */
}

.generator-description {
  color: rgba(255, 255, 255, 0.7); /* Цвет для описания методики */
}

.generator-checkbox-label {
  color: white;
  transition: color 0.3s;
}
.generator-checkbox-label:hover {
  color: #ffc1f3; /* Цвет при наведении */
}

.generator-checkbox {
  width: 1.1rem;
  height: 1.1rem;
  border-radius: 0.25rem;
  border: 1px solid rgba(255, 103, 231, 0.5);
  background-color: rgba(255, 204, 243, 0.3);
  appearance: none;
  cursor: pointer;
  position: relative;
  transition: all 0.3s;
}

.generator-checkbox:checked {
  background-color: #ff67e7;
  border-color: #ff67e7;
}

.generator-checkbox:checked::after {
  content: '✔';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 0.8rem;
}

.generator-checkbox-text {
  margin-left: 0.5rem;
  font-size: 0.9rem;
}

.generator-form-actions {
  /* Стили для контейнера кнопки */
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 1rem;
  padding: 1rem;
  margin-top: 1.5rem; /* Отступ сверху */
}

.generator-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1rem;
  background-color: #ec407a;
  border: none;
  border-radius: 1rem;
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(236, 64, 122, 0.5);
}

.generator-button:hover:not(:disabled) {
  background-color: #ff67e7;
  box-shadow: 0 6px 18px rgba(255, 103, 231, 0.6);
  transform: translateY(-2px);
}

.generator-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #a05784; /* Цвет для неактивной кнопки */
}

.generator-button-points {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1rem;
  background-color: #1890ff;
  border: none;
  border-radius: 1rem;
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.5);
}

.generator-button-points:hover:not(:disabled) {
  background-color: #40a9ff;
  box-shadow: 0 6px 18px rgba(24, 144, 255, 0.6);
  transform: translateY(-2px);
}

.generator-button-points:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #5784a0; /* Цвет для неактивной кнопки */
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

.generator-limits-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.generator-secondary-button {
  padding: 0.5rem 1rem;
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.75rem;
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.generator-secondary-button:hover {
  background-color: rgba(255, 255, 255, 0.25);
}

.generator-loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: generator-spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
}

@keyframes generator-spin {
  to {
    transform: rotate(360deg);
  }
}

/* Адаптивность для гридов */
@media (max-width: 768px) {
  .generator-grid {
    grid-template-columns: 1fr; /* Все поля в одну колонку на мобильных */
  }
}

</style>
