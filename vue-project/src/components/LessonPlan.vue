<!-- src/components/LessonPlan.vue -->
<template>
  <div class="lesson-plan-view">
    <!-- Декоративный элемент планеты -->
    <div class="planet-decoration" :style="planetBackgroundStyle"></div>

    <div class="content-container">
      <!-- Заголовок -->
      <div class="title-container">
        <h2>Lesson Plan Generator</h2>
      </div>

      <!-- Отображение лимитов генераций -->
      <GenerationLimitsDisplay :type="ContentType.LESSON_PLAN" />

      <!-- Форма генерации -->
      <form @submit.prevent="generateLessonPlan" class="generation-form">
        <!-- Язык -->
        <div class="form-group">
          <label for="language">Language:</label>
          <select
            v-model="formData.language"
            id="language"
            class="form-select"
            required
          >
            <option value="english">English</option>
            <option value="spanish">Spanish</option>
            <option value="french">French</option>
            <option value="german">German</option>
            <option value="italian">Italian</option>
            <option value="chinese">Chinese</option>
            <option value="russian">Russian</option>
            <option value="arabic">Arabic</option>
            <option value="japanese">Japanese</option>
            <option value="korean">Korean</option>
          </select>
        </div>

        <!-- Возраст -->
        <div class="form-group">
          <label>Age:</label>
          <div class="age-buttons">
            <button
              type="button"
              :class="['age-btn', { active: uiState.age === 'children' }]"
              @click="uiState.age = 'children'"
            >
              Children (7-12)
            </button>
            <button
              type="button"
              :class="['age-btn', { active: uiState.age === 'teens' }]"
              @click="uiState.age = 'teens'"
            >
              Teens (13-17)
            </button>
            <button
              type="button"
              :class="['age-btn', { active: uiState.age === 'adults' }]"
              @click="uiState.age = 'adults'"
            >
              Adults (18+)
            </button>
          </div>
        </div>

        <!-- Тема урока -->
        <div class="form-group">
          <label for="topic">Lesson Topic:</label>
          <input
            v-model="formData.topic"
            id="topic"
            class="form-input"
            placeholder="For example: Travel, Food, Technology..."
            required
          />
        </div>

        <!-- Уровень знаний -->
        <div class="form-group">
          <label for="level">Proficiency Level:</label>
          <select
            v-model="formData.level"
            id="level"
            class="form-select"
            required
          >
            <option value="">Select level</option>
            <option v-for="level in availableLevels" :key="level.id" :value="level.id">
              {{ level.name }}
            </option>
          </select>
          <div class="form-helper">
            Select student proficiency level for a more accurate lesson plan.
          </div>
        </div>

        <!-- Тема прошлого урока -->
        <div class="form-group">
          <label for="previous-lesson">Previous Lesson Topic (optional):</label>
          <textarea
            v-model="uiState.previous_lesson"
            id="previous-lesson"
            class="form-textarea"
            placeholder="Describe the topic and content of the previous lesson for better connection..."
          ></textarea>
        </div>

        <!-- Грамматика -->
        <div class="form-group">
          <label for="grammar">Grammar (optional):</label>
          <input
            v-model="uiState.grammar"
            id="grammar"
            class="form-input"
            placeholder="For example: Present Perfect, Conditionals..."
          />
        </div>

        <!-- Лексика -->
        <div class="form-group">
          <label for="vocabulary">Vocabulary (optional):</label>
          <input
            v-model="uiState.vocabulary"
            id="vocabulary"
            class="form-input"
            placeholder="For example: Select vocabulary words related to your topic"
          />
        </div>

        <!-- Методика обучения -->
        <div class="form-group">
          <label for="methodology">Teaching Methodology:</label>
          <select
            v-model="uiState.methodology"
            id="methodology"
            class="form-select"
          >
            <option value="">Select methodology</option>
            <optgroup label="Universal Methodologies">
              <option
                v-for="method in universalMethods"
                :key="method.id"
                :value="method.id"
              >
                {{ method.name }}
              </option>
            </optgroup>
            <optgroup v-if="languageSpecificMethods.length > 0" :label="`Methods for ${getLanguageName(formData.language)}`">
              <option
                v-for="method in languageSpecificMethods"
                :key="method.id"
                :value="method.id"
              >
                {{ method.name }}
              </option>
            </optgroup>
          </select>
          <div class="form-helper">
            Selecting a methodology will help structure the lesson plan according to a specific approach.
          </div>
        </div>

        <!-- Формат урока -->
        <div class="form-group">
          <label>Lesson Format:</label>
          <div class="format-buttons">
            <div class="format-row">
              <button
                type="button"
                :class="[
                  'format-btn',
                  { active: uiState.individual_group === 'individual' },
                ]"
                @click="uiState.individual_group = 'individual'"
              >
                <span class="icon">👤</span>
                Individual
              </button>
              <button
                type="button"
                :class="[
                  'format-btn',
                  { active: uiState.individual_group === 'group' },
                ]"
                @click="uiState.individual_group = 'group'"
              >
                <span class="icon">👥</span>
                Group
              </button>
            </div>
            <div class="format-row">
              <button
                type="button"
                :class="[
                  'format-btn',
                  { active: uiState.online_offline === 'online' },
                ]"
                @click="uiState.online_offline = 'online'"
              >
                <span class="icon">💻</span>
                Online
              </button>
              <button
                type="button"
                :class="[
                  'format-btn',
                  { active: uiState.online_offline === 'offline' },
                ]"
                @click="uiState.online_offline = 'offline'"
              >
                <span class="icon">🏫</span>
                Offline
              </button>
            </div>
          </div>
        </div>

        <!-- Экзамен -->
        <div class="form-group">
          <label for="exam">Exam (optional):</label>
          <input
            v-model="uiState.exam"
            id="exam"
            class="form-input"
            placeholder="For example: IELTS, TOEFL, etc."
          />
        </div>

        <!-- Кнопка генерации -->
        <div class="form-actions">
          <div class="buttons-container">
            <button
              type="submit"
              class="generate-button"
              :disabled="isGenerating || !canGenerate"
            >
              <span v-if="isGenerating" class="loading-spinner"></span>
              <span v-if="isGenerating">Generating...</span>
              <span v-else>Generate Lesson Plan</span>
            </button>

            <button
              type="button"
              class="generate-button points-generate-button"
              :disabled="isGenerating"
              @click="generateLessonPlanWithPoints"
            >
              <span v-if="isGenerating" class="loading-spinner"></span>
              <span v-if="isGenerating">Generating...</span>
              <span v-else><span class="points-icon">💎</span> Generate for 8 Points</span>
            </button>
          </div>
        </div>
      </form>

      <!-- Сообщение об ошибке -->
      <div v-if="error" class="error-message">
        <p>{{ error }}</p>
        <button @click="clearError" class="close-button">✕</button>
      </div>

      <!-- Результат генерации -->
      <div v-if="generatedContent" class="result-container">
        <h3>Generated Lesson Plan</h3>
        <div class="result-actions">
          <button @click="copyToClipboard" class="action-button copy-button">
            <span class="icon">📋</span>
            Copy
          </button>
          <button
            @click="regenerate"
            class="action-button"
            :disabled="!canGenerate"
          >
            <span class="icon">🔄</span>
            Regenerate
          </button>
        </div>
        <div class="plan-content" v-html="formattedContent"></div>

        <!-- Кнопки для детализации плана урока -->
        <div class="lesson-plan-details-buttons">
          <h4>Detail Lesson Plan:</h4>

          <div class="buttons-group">
         <h5>Detail Plan Points:</h5>
            <div class="buttons-grid">
              <button
                v-for="num in 8"
                :key="`detail-point-${num}`"
                @click="detailLessonPlanPoint(num)"
                class="detail-button"
                :disabled="isDetailLoading"
              >
                Point {{ num }}
              </button>
            </div>
          </div>

          <div class="buttons-group">
         <h5>Additional Materials:</h5>
            <div class="buttons-grid">
              <button @click="detailLessonPlanPoint('homework')" class="detail-button" :disabled="isDetailLoading">
                Homework
              </button>
              <button @click="detailLessonPlanPoint('script')" class="detail-button" :disabled="isDetailLoading">
                Teacher Script
              </button>
              <button @click="detailLessonPlanPoint('exercises')" class="detail-button" :disabled="isDetailLoading">
                More Exercises
              </button>
              <button @click="detailLessonPlanPoint('game')" class="detail-button" :disabled="isDetailLoading">
                Create Game for Lesson
              </button>
            </div>
          </div>

          <div class="buttons-group">
         <h5>Rewrite Plan Points:</h5>
            <div class="buttons-grid">
              <button
                v-for="num in 8"
                :key="`rewrite-point-${num}`"
                @click="rewriteLessonPlanPoint(num)"
                class="detail-button rewrite"
                :disabled="isDetailLoading"
              >
                Point {{ num }}
              </button>
            </div>
          </div>

          <!-- Блок для отображения детализированной информации -->
          <div v-if="detailedLessonContent" class="detailed-content">
            <h4>{{ detailedContentTitle }}</h4>
            <div class="result-actions">
              <button @click="copyDetailedContent" class="action-button copy-button">
                <span class="icon">📋</span>
                Copy
              </button>
            </div>

            <!-- Добавляем блок с исходным пунктом плана -->
            <div v-if="originalPointContent" class="original-point-content">
           <h5>Original Plan Point:</h5>
              <div class="original-content-text">{{ originalPointContent }}</div>
            </div>

            <div class="plan-content" v-html="formattedDetailedContent"></div>
            <button @click="detailedLessonContent = ''" class="close-detail-button">
              Close and Return to Plan
            </button>
          </div>
        </div>

        <!-- Спойлер для генерации за баллы -->
        <div class="points-generation-section">
          <details class="points-generation-details">
            <summary class="points-generation-summary">
              <span class="points-icon">💎</span> Generate with Points (8 points per generation)
            </summary>

            <div class="points-generation-content">
              <p class="points-info">
                Use points to generate without daily plan limits.
                <span class="points-balance">Your balance: <strong>{{ userPoints }}</strong> points</span>
              </p>

              <div class="buttons-group">
                <h5>Detail Plan Points with Points:</h5>
                <div class="buttons-grid">
                  <button
                    v-for="num in 8"
                    :key="`detail-point-points-${num}`"
                    @click="detailLessonPlanPointWithPoints(num)"
                    class="detail-button points-button"
                    :disabled="isDetailLoading"
                  >
                    Point {{ num }}
                  </button>
                </div>
              </div>

              <div class="buttons-group">
                <h5>Additional Materials with Points:</h5>
                <div class="buttons-grid">
                  <button @click="detailLessonPlanPointWithPoints('homework')" class="detail-button points-button" :disabled="isDetailLoading">
                    Homework
                  </button>
                  <button @click="detailLessonPlanPointWithPoints('script')" class="detail-button points-button" :disabled="isDetailLoading">
                    Teacher Script
                  </button>
                  <button @click="detailLessonPlanPointWithPoints('exercises')" class="detail-button points-button" :disabled="isDetailLoading">
                    More Exercises
                  </button>
                  <button @click="detailLessonPlanPointWithPoints('game')" class="detail-button points-button" :disabled="isDetailLoading">
                    Create Game for Lesson
                  </button>
                </div>
              </div>

              <div class="buttons-group">
                <h5>Rewrite Plan Points with Points:</h5>
                <div class="buttons-grid">
                  <button
                    v-for="num in 8"
                    :key="`rewrite-point-points-${num}`"
                    @click="rewriteLessonPlanPointWithPoints(num)"
                    class="detail-button rewrite points-button"
                    :disabled="isDetailLoading"
                  >
                    Point {{ num }}
                  </button>
                </div>
              </div>
            </div>
          </details>
        </div>

        <!-- Добавляем дополнительную кнопку копирования после содержимого -->
        <div class="bottom-copy-action">
          <button @click="copyToClipboard" class="action-button copy-button">
            <span class="icon">📋</span>
            Copy Lesson Plan
          </button>
        </div>
      </div>

      <!-- Loading indicator for lesson plan details -->
      <div v-if="isDetailLoading" class="detail-loading-overlay">
        <div class="loader"></div>
        <p>Processing request...</p>
      </div>

      <!-- Пространство для нижней навигации -->
      <div class="bottom-spacer"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';

// Объявляем тип для Window
declare global {
  interface Window {
    saveComponentStyles?: (componentName: string, selectors: string[]) => void;
  }
}
import { useMainStore } from '@/store';
import type { LessonPlanFormData } from '@/types';
import { ContentType, ActionType } from '@/core/constants';
// Импортируем файлы с методиками и уровнями
import { getLevelsByLanguage } from '@/constants/levels';
import { teachingMethods } from '@/constants/methods';
// Импортируем изображение планеты
import planetBg from '@/assets/images/lesson_plan/plan-backgroud-image.svg';
// Импортируем сервис для формы плана урока
import { lessonPlanFormService } from '@/services/lessonPlanFormService';
// Импортируем новый сервис для детализации плана урока
import { lessonPlanDetailService } from '@/services/lessonPlanDetailService';
// Импортируем компонент для отображения лимитов генераций
import GenerationLimitsDisplay from './common/GenerationLimitsDisplay.vue';

// Объявление интерфейса для Toast-уведомлений
interface SimpleToast {
  success: (message: string, duration?: number) => number;
  error: (message: string, duration?: number) => number;
  info: (message: string, duration?: number) => number;
  warning: (message: string, duration?: number) => number;
  removeAll: () => void;
}

// Объявление глобальных типов для TypeScript
declare global {
  interface Window {
    __SIMPLE_TOAST__?: SimpleToast;
  }
}

const store = useMainStore();

// Состояние формы
const formData = ref<LessonPlanFormData>({
  language: 'english',
  level: '',
  topic: '',
  duration: 60, // Устанавливаем значение по умолчанию для длительности урока
  methodologies: {
    mainMethod: '',
    supportMethods: []
  },
  objectives: [],
  materials: [],
  assessment: 'formative',
  format: 'online',
  culturalElements: false
});

// Дополнительные поля для UI, которые не входят в LessonPlanFormData
const uiState = ref({
  age: 'teens',
  previous_lesson: '',
  grammar: '',
  vocabulary: '',
  methodology: [] as string[], // Указываем, что это массив строк
  individual_group: 'individual',
  online_offline: 'online',
  exam: ''
});

// Состояние компонента
const generatedContent = ref<string | null>(null);
const isLoading = computed(() => store.loading);
const error = computed(() => store.error);
const canGenerate = computed(() => store.canGenerate(ContentType.LESSON_PLAN));
const userPoints = computed(() => store.user?.points || 0);

// Определение адаптивности
const isMobile = ref(window.innerWidth <= 768);

// Фон с планетой - вычисляемый стиль
const planetBackgroundStyle = computed(() => {
  return {
    backgroundImage: `url(${planetBg})`,
    backgroundSize: isMobile.value ? '75% auto' : '45% auto',
    backgroundPosition: isMobile.value ? 'center 45px' : 'center 0',
    backgroundRepeat: 'no-repeat'
  };
});

// Получаем доступные уровни в зависимости от выбранного языка
const availableLevels = computed(() => getLevelsByLanguage(formData.value.language));

// Определяем тип для методик
type MethodsType = {
  [key: string]: Array<{
    id: string;
    name: string;
    description: string;
    features?: string[];
    variants?: string[];
  }>;
};

// Методы разделяем на универсальные и языкоспецифичные для улучшения UX
const universalMethods = computed(() => {
  const methods = teachingMethods as MethodsType;
  return methods.universal || [];
});

const languageSpecificMethods = computed(() => {
  const methods = teachingMethods as MethodsType;
  const lang = formData.value.language;

  // Массив для хранения специфичных методик
  let specificMethods: any[] = [];

  // Проверяем разные категории методик
  if (methods[lang]) {
    specificMethods = [...specificMethods, ...methods[lang]];
  }

  if (lang === 'chinese' || lang === 'japanese' || lang === 'korean') {
    if (methods.asian) {
      // Добавляем только те методики, которых еще нет
      methods.asian.forEach(method => {
        if (!specificMethods.some(m => m.id === method.id)) {
          specificMethods.push(method);
        }
      });
    }
  }

  if (['spanish', 'french', 'german', 'italian'].includes(lang)) {
    if (methods.european) {
      methods.european.forEach(method => {
        if (!specificMethods.some(m => m.id === method.id)) {
          specificMethods.push(method);
        }
      });
    }
  }

  return specificMethods;
});

// Форматированный HTML для отображения сгенерированного контента
const formattedContent = computed(() => {
  return formatContent(generatedContent.value || '');
});

// Функция получения названия языка для отображения
const getLanguageName = (langCode: string) => {
  const languages: {[key: string]: string} = {
    'english': 'английского языка',
    'spanish': 'испанского языка',
    'french': 'французского языка',
    'german': 'немецкого языка',
    'italian': 'итальянского языка',
    'chinese': 'китайского языка',
    'russian': 'русского языка',
    'arabic': 'арабского языка',
    'japanese': 'японского языка',
    'korean': 'корейского языка'
  };

  return languages[langCode] || langCode;
};

// Обновляем мобильное состояние при изменении размера окна
onMounted(() => {
  const updateMobileStatus = () => {
    isMobile.value = window.innerWidth <= 768;
  };

  window.addEventListener('resize', updateMobileStatus);

  // Сохраняем стили компонента LessonPlan после монтирования
  setTimeout(() => {
    if (typeof window.saveComponentStyles === 'function') {
      const lessonPlanSelectors = [
        '.lesson-plan-container',
        '.lesson-plan-content',
        '.lesson-plan-form',
        '.lesson-plan-background',
        '.lesson-plan-heading',
        '.lesson-plan-subheading',
        '.lesson-plan-paragraph',
        '.lesson-plan-list',
        '.lesson-plan-list-item',
        '.lesson-plan-section-header',
        '.lesson-plan-bold',
        '.lesson-plan-italic',
        '.lesson-plan-empty-paragraph',
        '.title-form-group',
        '.generation-form',
        '.form-group',
        '.result-container',
        '.plan-content'
      ];

      window.saveComponentStyles('lesson-plan', lessonPlanSelectors);
      console.log('Стили компонента LessonPlan сохранены');
    }
  }, 500); // Задержка для полного рендеринга компонента

  // Очистка обработчика при размонтировании компонента
  return () => {
    window.removeEventListener('resize', updateMobileStatus);
  };
});

// При изменении языка проверяем и сбрасываем несовместимые уровни и методики
watch(() => formData.value.language, (newLanguage) => {
  // Проверка и сброс уровня
  const levels = getLevelsByLanguage(newLanguage);
  const levelExists = levels.some(level => level.id === formData.value.level);

  if (!levelExists && formData.value.level) {
    formData.value.level = '';
  }

  // Проверка и сброс методики
  const methods = teachingMethods as MethodsType;
  let availableMethods: any[] = [...(methods.universal || [])];

  // Добавляем методики в зависимости от языка
  if (methods[newLanguage]) {
    availableMethods = [...availableMethods, ...methods[newLanguage]];
  } else if (newLanguage === 'chinese' || newLanguage === 'japanese' || newLanguage === 'korean') {
    availableMethods = [...availableMethods, ...(methods.asian || [])];
  } else if (['spanish', 'french', 'german', 'italian'].includes(newLanguage)) {
    availableMethods = [...availableMethods, ...(methods.european || [])];
  }

  // Проверяем, существует ли выбранная методика в новом списке
  // Поскольку methodology - это массив, нам нужно проверить, есть ли хотя бы один элемент из массива в доступных методиках
  let methodsInvalid = true;

  if (uiState.value.methodology.length > 0) {
    methodsInvalid = !uiState.value.methodology.some(methodId =>
      availableMethods.some(method => method.id === methodId)
    );
  } else {
    methodsInvalid = false; // Если массив пуст, то все в порядке
  }

  if (methodsInvalid) {
    // Если ни одна из выбранных методик не подходит для нового языка, сбрасываем массив
    uiState.value.methodology = [];
  }
});

// Основные функции компонента
// Добавляем переменную для отслеживания состояния генерации
const isGenerating = ref(false);

// Генерация плана урока
const generateLessonPlan = async () => {
  try {
    generatedContent.value = null;
    store.clearError();

    // Устанавливаем флаг начала генерации
    isGenerating.value = true;

    // Проверяем лимиты генерации
    if (!canGenerate.value) {
      store.setError('Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или попробуйте завтра.');
      isGenerating.value = false; // Сбрасываем флаг при ошибке
      return;
    }

    // Подготавливаем данные формы для отправки в новый сервис
    const requestData = {
      language: formData.value.language,
      topic: formData.value.topic,
      level: formData.value.level,
      age: uiState.value.age,
      previous_lesson: uiState.value.previous_lesson,
      grammar: uiState.value.grammar,
      vocabulary: uiState.value.vocabulary,
      methodology: Array.isArray(uiState.value.methodology) ? uiState.value.methodology : [],
      individual_group: uiState.value.individual_group,
      online_offline: uiState.value.online_offline,
      exam: uiState.value.exam,
      duration: formData.value.duration
    };

    // Добавляем отладочный лог для проверки темы урока
    console.log('Генерация плана урока с темой:', requestData.topic);

    // Проверяем, что тема урока задана
    if (!requestData.topic || requestData.topic.trim() === '') {
      console.warn('Внимание: тема урока не указана!');
      store.setError('Необходимо указать тему урока');
      return;
    }

    // Отслеживаем использование для лимитов и обновляем локальные счетчики
    try {
      await store.checkAndTrackGeneration(ContentType.LESSON_PLAN);
    } catch (limitError: any) {
      console.error('Ошибка при проверке лимитов:', limitError);
      // Если ошибка связана с отсутствием тарифа, предлагаем использовать баллы
      if (limitError.message && (
          limitError.message.includes('No active tariff') ||
          limitError.message.includes('Нет активного тарифа') ||
          limitError.message.includes('403')
        )) {
        if (store.user && store.user.points >= 8) {
          if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации плана урока?')) {
            await generateLessonPlanWithPoints();
            return;
          } else {
            store.setError('Для генерации необходимо приобрести тариф или использовать баллы.');
            return;
          }
        } else {
          store.setError('У вас нет активного тарифа. Для генерации необходимо приобрести тариф или пополнить баллы.');
          return;
        }
      }
      throw limitError;
    }

    // Генерируем план урока с использованием нового сервиса
    const result = await lessonPlanFormService.generateLessonPlan(requestData);

    // Проверяем достижения
    await store.checkAchievements(ActionType.GENERATION, {
      content_type: ContentType.LESSON_PLAN,
      language: formData.value.language,
      age: uiState.value.age,
      topic: formData.value.topic,
      methodology: uiState.value.methodology,
      level: formData.value.level
    });

    // Устанавливаем результат
    generatedContent.value = result;

    // Прокручиваем к результату
    setTimeout(() => {
      const resultContainer = document.querySelector('.result-container');
      if (resultContainer) {
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);

  } catch (err: unknown) {
    console.error('Error generating lesson plan:', err);

    if (err instanceof Error) {
      if (err.message.includes('Daily limit') || err.message.includes('дневной лимит')) {
        store.setError('Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или попробуйте завтра.');
      } else if (err.message.includes('Invalid response') || err.message.includes('Неверный формат ответа')) {
        console.error('Детали ошибки от сервера:', err.message);
        store.setError('Проблема с ответом от сервера. Попробуйте еще раз позднее или обратитесь в поддержку.');
      } else if (err.message.includes('Network Error') || err.message.includes('timeout')) {
        store.setError('Проблема с подключением к серверу. Проверьте ваше интернет-соединение и попробуйте снова.');
      } else {
        store.setError(`Ошибка при генерации плана урока: ${err.message}`);
      }
    } else {
      store.setError('Ошибка при генерации плана урока: Неизвестная ошибка');
    }
  } finally {
    // Сбрасываем флаг генерации, независимо от результата
    isGenerating.value = false;
  }
};

// Генерация плана урока за баллы
const generateLessonPlanWithPoints = async () => {
  try {
    generatedContent.value = null;
    store.clearError();
    isGenerating.value = true;

    // Подготавливаем данные формы для отправки в новый сервис
    const requestData = {
      language: formData.value.language,
      topic: formData.value.topic,
      level: formData.value.level,
      age: uiState.value.age,
      previous_lesson: uiState.value.previous_lesson,
      grammar: uiState.value.grammar,
      vocabulary: uiState.value.vocabulary,
      methodology: Array.isArray(uiState.value.methodology) ? uiState.value.methodology : [],
      individual_group: uiState.value.individual_group,
      online_offline: uiState.value.online_offline,
      exam: uiState.value.exam,
      duration: formData.value.duration
    };

    // Добавляем отладочный лог для проверки темы урока
    console.log('Генерация плана урока за баллы с темой:', requestData.topic);

    // Проверяем, что тема урока задана
    if (!requestData.topic || requestData.topic.trim() === '') {
      console.warn('Внимание: тема урока не указана!');
      store.setError('Необходимо указать тему урока');
      return;
    }

    // Генерируем план урока с использованием нового сервиса
    const result = await lessonPlanFormService.generateLessonPlanWithPoints(requestData);

    // Проверяем достижения
    await store.checkAchievements(ActionType.GENERATION, {
      content_type: ContentType.LESSON_PLAN,
      language: formData.value.language,
      age: uiState.value.age,
      topic: formData.value.topic,
      methodology: uiState.value.methodology,
      level: formData.value.level,
      with_points: true
    });

    // Устанавливаем результат
    generatedContent.value = result;

    // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
    await store.fetchCurrentUser();
    console.log('Количество баллов после генерации плана урока:', store.user?.points);

    // Прокручиваем к результату
    setTimeout(() => {
      const resultContainer = document.querySelector('.result-container');
      if (resultContainer) {
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);

  } catch (err: unknown) {
    console.error('Error generating lesson plan with points:', err);

    if (err instanceof Error) {
      if (err.message.includes('Недостаточно баллов')) {
        store.setError('Недостаточно баллов для генерации. Требуется 8 баллов.');
      } else if (err.message.includes('Invalid response') || err.message.includes('Неверный формат ответа')) {
        console.error('Детали ошибки от сервера:', err.message);
        store.setError('Проблема с ответом от сервера. Попробуйте еще раз позднее или обратитесь в поддержку.');
      } else if (err.message.includes('Network Error') || err.message.includes('timeout')) {
        store.setError('Проблема с подключением к серверу. Проверьте ваше интернет-соединение и попробуйте снова.');
      } else {
        store.setError(`Ошибка при генерации плана урока за баллы: ${err.message}`);
      }
    } else {
      store.setError('Ошибка при генерации плана урока за баллы: Неизвестная ошибка');
    }
  } finally {
    isGenerating.value = false;
  }
};

// Повторная генерация плана
const regenerate = () => {
  generateLessonPlan();
};

// Очистка ошибок
const clearError = () => {
  store.clearError();
};

// Копирование в буфер обмена
const copyToClipboard = async () => {
  if (generatedContent.value) {
    try {
      await navigator.clipboard.writeText(generatedContent.value);

      // Показываем уведомление об успешном копировании
      if (window.__SIMPLE_TOAST__) {
        window.__SIMPLE_TOAST__.success('Текст скопирован в буфер обмена', 2000);
      }
    } catch (err) {
      console.error('Не удалось скопировать текст:', err);

      // Показываем уведомление об ошибке
      if (window.__SIMPLE_TOAST__) {
        window.__SIMPLE_TOAST__.error('Не удалось скопировать текст', 2000);
      }
    }
  }
};

// Форматирование текста для отображения
const formatContent = (content: string) => {
  if (!content) return '';

  // Создаем временную копию контента для обработки
  let formattedContent = content;

  // Заменяем все HTML-теги на безопасные эквиваленты
  formattedContent = formattedContent
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Сначала заменяем переносы строк на временные маркеры
  formattedContent = formattedContent.replace(/\n/g, '###NEWLINE###');

  // Обработка жирного текста (между двойными звездочками)
  formattedContent = formattedContent.replace(/\*\*([^*]+)\*\*/g, '<strong class="lesson-plan-bold">$1</strong>');

  // Обработка курсива (между одинарными звездочками)
  formattedContent = formattedContent.replace(/\*([^*]+)\*/g, '<em class="lesson-plan-italic">$1</em>');

  // Обработка заголовков
  formattedContent = formattedContent
    // Заголовки (например, "1. Objectives:")
    .replace(/^(\d+\.\s+)(.+?)(:?)$/gm, '<h3 class="lesson-plan-heading">$1$2$3</h3>')
    // Подзаголовки (например, "4.1 Vocabulary Building")
    .replace(/^(\d+\.\d+\s+)(.+?)(:?)$/gm, '<h4 class="lesson-plan-subheading">$1$2$3</h4>')
    // Заголовки с двойными звездочками (например, "**Total lesson time: 60 minutes**")
    .replace(/^<strong class="lesson-plan-bold">(.+?)<\/strong>$/gm, '<h3 class="lesson-plan-heading">$1</h3>');

  // Находим группы строк, начинающихся с дефиса, и оборачиваем их в <ul>
  const lines = formattedContent.split('###NEWLINE###');
  let inList = false;
  const result = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Пропускаем пустые строки
    if (line === '') {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      result.push('<p class="lesson-plan-empty-paragraph">&nbsp;</p>');
      continue;
    }

    // Если строка начинается с заголовка (h3 или h4), закрываем список если он открыт
    if (line.startsWith('<h3') || line.startsWith('<h4')) {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      result.push(`<div class="lesson-plan-section-header">${line}</div>`);
      continue;
    }

    // Если строка начинается с дефиса
    if (line.startsWith('- ')) {
      // Если это первый элемент списка, открываем <ul>
      if (!inList) {
        result.push('<ul class="lesson-plan-list">');
        inList = true;
      }
      // Добавляем элемент списка
      result.push('<li class="lesson-plan-list-item">' + line.substring(2) + '</li>');
    } else {
      // Если это не элемент списка, но мы были в списке, закрываем его
      if (inList) {
        result.push('</ul>');
        inList = false;
      }

      // Добавляем строку как параграф
      result.push('<p class="lesson-plan-paragraph">' + line + '</p>');
    }
  }

  // Если список не был закрыт, закрываем его
  if (inList) {
    result.push('</ul>');
  }

  // Объединяем строки обратно
  return result.join('');
};

// Дополнительные переменные для детальной информации
const isDetailLoading = ref(false);
const detailedLessonContent = ref('');
const detailedContentTitle = ref('');
const formattedDetailedContent = ref('');
const originalPointContent = ref('');

// Функция для копирования детального содержимого в буфер обмена
const copyDetailedContent = () => {
  try {
    const detailText = formattedDetailedContent.value.replace(/<[^>]*>/g, '');
    navigator.clipboard.writeText(detailText);

    // Показываем уведомление об успешном копировании
    if (window.__SIMPLE_TOAST__) {
      window.__SIMPLE_TOAST__.success('Детализированное содержимое скопировано в буфер обмена');
    } else {
      alert('Детализированное содержимое скопировано в буфер обмена');
    }
  } catch (error) {
    console.error('Error copying to clipboard:', error);
    if (window.__SIMPLE_TOAST__) {
      window.__SIMPLE_TOAST__.error('Не удалось скопировать содержимое');
    } else {
      alert('Не удалось скопировать содержимое');
    }
  }
};

// Функция для получения заголовков авторизации
const getAuthHeaders = () => {
  // Получаем данные авторизации из Telegram WebApp
  const webApp = window.Telegram?.WebApp;
  const webAppData = webApp?.initData;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };

  if (webAppData) {
    headers['Authorization'] = `tma ${webAppData}`;
  }

  return headers;
};

// Функция для детализации пункта плана урока
const detailLessonPlanPoint = async (point: string | number) => {
  try {
    isDetailLoading.value = true;
    detailedLessonContent.value = String(point);

    // Проверяем лимиты генерации перед отправкой запроса
    console.log('Проверка лимитов генерации перед детализацией пункта плана');

    // Сначала пробуем обычную генерацию
    let canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN);

    // Если обычная генерация недоступна, предлагаем использовать баллы
    if (!canGenerate) {
      // Проверяем, есть ли у пользователя достаточно баллов
      if (store.user && store.user.points >= 8) {
        // Спрашиваем пользователя, хочет ли он использовать баллы
        if (confirm('Достигнут дневной лимит генераций. Хотите использовать 8 баллов для детализации пункта плана?')) {
          // Пытаемся списать баллы
          canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN);
          if (!canGenerate) {
            throw new Error('Не удалось списать баллы. Пожалуйста, попробуйте еще раз.');
          }
        } else {
          throw new Error('Достигнут дневной лимит генераций. Пожалуйста, попробуйте позже или обновите тариф.');
        }
      } else {
        throw new Error('Достигнут дневной лимит генераций. Пожалуйста, попробуйте позже или обновите тариф.');
      }
    }

    if (typeof point === 'number') {
      detailedContentTitle.value = `Детализация пункта ${point}`;
    } else {
      const titles: Record<string, string> = {
        'homework': 'Домашнее задание',
        'script': 'Скрипт учителя',
        'exercises': 'Дополнительные упражнения',
        'game': 'Игра для урока'
      };
      detailedContentTitle.value = titles[point] || String(point);
    }

    // Получаем содержимое плана урока
    const lessonPlanContent = generatedContent.value || '';

    // Пытаемся найти исходный пункт плана, если запрашивается числовой пункт
    if (typeof point === 'number') {
      // Ищем по различным паттернам разделов плана урока
      const patterns = [
        new RegExp(`${point}\\.(\\s+)?([^\\n.]+)`, 'i'), // Для формата "1. Заголовок"
        new RegExp(`([^\\n.]+)\\s+\\(${point}(\\s+)?мин\\)`, 'i'), // Для формата "Заголовок (5 мин)"
        new RegExp(`${point}(\\s+)?\\.(\\s+)?([^\\n]+)`, 'i') // Более общий шаблон
      ];

      let foundOriginalPoint = '';
      for (const pattern of patterns) {
        const match = lessonPlanContent.match(pattern);
        if (match && match[0]) {
          foundOriginalPoint = match[0].trim();
          break;
        }
      }

      originalPointContent.value = foundOriginalPoint || `Пункт ${point}`;
    } else if (point === 'script') {
      originalPointContent.value = 'Скрипт учителя на основе плана урока';
    } else if (point === 'homework') {
      originalPointContent.value = 'Домашнее задание к плану урока';
    } else if (point === 'exercises') {
      originalPointContent.value = 'Дополнительные упражнения к плану урока';
    } else if (point === 'game') {
      originalPointContent.value = 'Игра для урока на основе плана';
    } else {
      originalPointContent.value = `Детализация: ${String(point)}`;
    }

    // Используем новый сервис для детализации на основе типа запроса
    let detailedContent = '';

    try {
      console.log('Используем новый сервис для детализации плана урока');

      // Объединяем данные из formData и uiState для передачи в сервис
      const combinedFormData = {
        ...formData.value,
        age: uiState.value.age,
        methodology: uiState.value.methodology,
        individual_group: uiState.value.individual_group,
        online_offline: uiState.value.online_offline,
        previous_lesson: uiState.value.previous_lesson,
        grammar: uiState.value.grammar,
        vocabulary: uiState.value.vocabulary,
        exam: uiState.value.exam
      };

      console.log('Объединенные данные для детализации:', combinedFormData);

      if (typeof point === 'number') {
        // Детализируем конкретный пункт плана
        detailedContent = await lessonPlanDetailService.detailLessonPlanPoint(lessonPlanContent, combinedFormData, point);
      } else {
        // Определяем тип запроса и вызываем соответствующий метод
        switch (point) {
          case 'script':
            detailedContent = await lessonPlanDetailService.detailLessonPlanScript(lessonPlanContent, combinedFormData);
            break;
          case 'homework':
            detailedContent = await lessonPlanDetailService.detailLessonPlanHomework(lessonPlanContent, combinedFormData);
            break;
          case 'exercises':
            detailedContent = await lessonPlanDetailService.detailLessonPlanExercises(lessonPlanContent, combinedFormData);
            break;
          case 'game':
            detailedContent = await lessonPlanDetailService.detailLessonPlanGame(lessonPlanContent, combinedFormData);
            break;
          default:
            throw new Error(`Неизвестный тип детализации: ${point}`);
        }
      }

      console.log('Получен ответ детализации:', detailedContent ? 'Успешно' : 'Пустой ответ');

      // Форматируем результат
      formattedDetailedContent.value = formatContent(detailedContent || '');
      detailedLessonContent.value = detailedContent;

      // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
      await store.fetchCurrentUser();
      console.log('Количество баллов после детализации пункта плана:', store.user?.points);

      // Прокручиваем к детализированному содержимому
      setTimeout(() => {
        const detailedContent = document.querySelector('.detailed-content');
        if (detailedContent) {
          detailedContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);

    } catch (serviceError) {
      console.error('Ошибка при использовании нового сервиса детализации:', serviceError);

      // Если новый сервис не сработал, используем старый метод через API
      console.log('Падаем на запасной вариант детализации через API');

      // Определяем тип контента и действие в зависимости от запрошенного пункта
      let pointToDetail;
      let actionText;

      if (typeof point === 'number') {
        pointToDetail = `point_${point}`;
        actionText = `Детализация пункта ${point} плана урока на языке ${getLanguageName(formData.value.language)}.
        Предоставь подробное описание, включающее конкретные инструкции, примеры и рекомендации для учителя.`;
      } else {
        switch (point) {
          case 'script':
            pointToDetail = 'teacher_script';
            actionText = `ВНИМАНИЕ: Это запрос на создание скрипта учителя для существующего плана урока на ${formData.value.language} языке.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА ИЛИ ЕГО ПЕРЕСКАЗ.
Создай подробный скрипт учителя с точными фразами и инструкциями для проведения урока.
Скрипт должен включать:
1. Фактические слова, которые учитель говорит на каждом этапе
2. Четкие инструкции к заданиям для учеников
3. Вопросы для проверки понимания и вовлечения учеников
4. Переходы между этапами урока
5. Комментарии о взаимодействии с учениками

ВАЖНО: Скрипт должен быть на ${formData.value.language} языке и содержать конкретные фразы и формулировки, которые учитель использует в классе.`;
            break;
          case 'homework':
            pointToDetail = 'homework';
            actionText = `ВНИМАНИЕ: Это запрос на создание домашнего задания для существующего плана урока на ${formData.value.language} языке.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Создай подробное и детальное домашнее задание для приведенного плана урока.
Задание должно соответствовать теме, целям и содержанию плана.
Включи конкретные инструкции, вопросы, упражнения или задачи.
Учитывай уровень учеников и тип занятия из исходного плана.
ВАЖНО: Задание должно быть на ${formData.value.language} языке.`;
            break;
          case 'exercises':
            pointToDetail = 'exercises';
            actionText = `ВНИМАНИЕ: Это запрос на создание дополнительных упражнений для существующего плана урока на ${formData.value.language} языке.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Создай набор конкретных упражнений для приведенного плана урока.
Упражнения должны:
1. Соответствовать теме, целям и уровню учеников из исходного плана
2. Быть подробно описаны с инструкциями по выполнению
3. Включать различные типы заданий (письменные, устные, интерактивные)
4. Быть готовыми к использованию без дополнительной подготовки
5. Учитывать формат проведения урока (онлайн/оффлайн, индивидуальный/групповой)
ВАЖНО: Упражнения должны быть на ${formData.value.language} языке.`;
            break;
          case 'game':
            pointToDetail = 'game';
            actionText = `ВНИМАНИЕ: Это запрос на создание игровой активности для существующего плана урока на ${formData.value.language} языке.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Создай детальное описание игры или интерактивной активности, которую можно использовать в рамках данного урока.
Описание должно включать:
1. Название игры
2. Необходимые материалы
3. Подробные правила
4. Пошаговые инструкции для учителя
5. Примерную продолжительность
6. Варианты адаптации (для разных уровней/возрастов)
ВАЖНО: Описание игры должно быть на ${formData.value.language} языке.`;
            break;
          default:
            pointToDetail = point;
            actionText = `Детализация ${point} для плана урока на языке ${getLanguageName(formData.value.language)}`;
        }
      }

      // Проверяем авторизацию пользователя
      if (!store.user || !store.user.id) {
        throw new Error('Пользователь не авторизован');
      }

      // Создаем данные для промпта в формате JSON
      const promptData = {
        content: lessonPlanContent,
        content_type: pointToDetail,
        language: formData.value.language,
        age_group: uiState.value.age,
        methodology: Array.isArray(uiState.value.methodology) && uiState.value.methodology.length ? uiState.value.methodology.join(',') : '',
        is_individual: uiState.value.individual_group === 'individual',
        is_online: uiState.value.online_offline === 'online',
        lesson_focus: formData.value.topic,
        duration: formData.value.duration,
        level: formData.value.level,
        action: actionText, // Используем подготовленный текст действия
        instruction_language: formData.value.language // Явно указываем язык выходного контента
      };

      // Создаем запрос в формате, ожидаемом API
      const requestData = {
        user_id: store.user.id,
        type: ContentType.LESSON_PLAN,
        prompt: JSON.stringify(promptData) // Передаем данные в формате JSON в поле prompt
      };

      console.log('Отправка запроса на детализацию пункта плана (запасной вариант):', requestData);

      // Используем метод из store для отправки запроса вместо прямого fetch
      const result = await store.detailLessonPlan(requestData);

      if (result.error) {
        throw new Error(result.error);
      }

      console.log('Получен ответ детализации (запасной вариант):', result);

      // Форматируем результат
      formattedDetailedContent.value = formatContent(result.content || '');

      // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
      await store.fetchCurrentUser();
      console.log('Количество баллов после детализации пункта плана (запасной вариант):', store.user?.points);

      // Прокручиваем к детализированному содержимому
      setTimeout(() => {
        const detailedContent = document.querySelector('.detailed-content');
        if (detailedContent) {
          detailedContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);

      // Получаем исходный пункт плана
      originalPointContent.value = result.original_point || '';
    }
  } catch (err: unknown) {
    console.error('Error getting detailed lesson plan point:', err);
    if (err instanceof Error) {
      store.setError(`Ошибка при получении детализированной информации: ${err.message}`);
    } else {
      store.setError('Ошибка при получении детализированной информации: Неизвестная ошибка');
    }
  } finally {
    isDetailLoading.value = false;
  }
};

// Функция для переписывания пункта плана урока
const rewriteLessonPlanPoint = async (point: string | number) => {
  try {
    isDetailLoading.value = true;
    const pointStr = String(point);
    detailedLessonContent.value = pointStr;
    detailedContentTitle.value = `Переписанный пункт ${point}`;

    // Проверяем лимиты генерации перед отправкой запроса
    console.log('Проверка лимитов генерации перед переписыванием пункта плана');

    // Сначала пробуем обычную генерацию
    let canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN);

    // Если обычная генерация недоступна, предлагаем использовать баллы
    if (!canGenerate) {
      // Проверяем, есть ли у пользователя достаточно баллов
      if (store.user && store.user.points >= 8) {
        // Спрашиваем пользователя, хочет ли он использовать баллы
        if (confirm('Достигнут дневной лимит генераций. Хотите использовать 8 баллов для переписывания пункта плана?')) {
          // Пытаемся списать баллы
          canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN);
          if (!canGenerate) {
            throw new Error('Не удалось списать баллы. Пожалуйста, попробуйте еще раз.');
          }
        } else {
          throw new Error('Достигнут дневной лимит генераций. Пожалуйста, попробуйте позже или обновите тариф.');
        }
      } else {
        throw new Error('Достигнут дневной лимит генераций. Пожалуйста, попробуйте позже или обновите тариф.');
      }
    }

    // Получаем содержимое плана урока
    const lessonPlanContent = generatedContent.value || '';

    // Определяем тип контента и действие в зависимости от запрошенного пункта
    let pointToRewrite;
    let actionText;
    let pointContent = '';

    // Если это числовой пункт, извлекаем его содержимое
    if (typeof point === 'number') {
      // Используем те же паттерны, что и в detailLessonPlanPoint
      const patterns = [
        // Формат "5. Заголовок"
        new RegExp(`${point}\\.(\\s+)?([^\\n]+)(\\n|$)`, 'i'),
        // Формат "5) Заголовок"
        new RegExp(`${point}\\)(\\s+)?([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Пункт 5: Заголовок"
        new RegExp(`[Пп]ункт\\s+${point}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Stage 5: Заголовок"
        new RegExp(`[Ss]tage\\s+${point}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Activity 5: Заголовок"
        new RegExp(`[Aa]ctivity\\s+${point}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "5. Заголовок" и следующие за ним строки до следующего пункта
        new RegExp(`${point}\\.(\\s+)?([^\\n]+)(\\n(?!\\d+\\.)[^\\n]+)*`, 'i')
      ];

      // Ищем содержимое пункта
      for (const pattern of patterns) {
        const match = lessonPlanContent.match(pattern);
        if (match && match[0]) {
          pointContent = match[0].trim();
          break;
        }
      }

      // Если не нашли пункт по паттернам, попробуем найти по номеру раздела
      if (!pointContent) {
        // Разбиваем план на разделы
        const sections = lessonPlanContent.split(/\n\s*\n/);

        // Ищем раздел, который может соответствовать нужному пункту
        if (sections.length >= point && point > 0) {
          // Берем раздел с индексом (point - 1), так как массивы начинаются с 0
          pointContent = sections[point - 1].trim();
        }
      }

      // Если все еще не нашли, используем общий подход - ищем по номеру в начале строки
      if (!pointContent) {
        const lines = lessonPlanContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].trim().startsWith(`${point}.`) ||
              lines[i].trim().startsWith(`${point})`) ||
              lines[i].trim().match(new RegExp(`^\\s*${point}[.:\\s)]`))) {
            let j = i + 1;
            pointContent = lines[i].trim();

            while (j < lines.length) {
              const nextLine = lines[j].trim();
              // Останавливаемся, если нашли следующий пункт или пустую строку
              if (nextLine === '' || /^\d+[.:]/.test(nextLine)) {
                break;
              }
              pointContent += '\n' + lines[j];
              j++;
            }
            break;
          }
        }
      }

      console.log(`Извлеченный пункт ${point} для переписывания:`, pointContent || 'Не найден');

      pointToRewrite = `rewrite_point_${point}`;
      actionText = `ВНИМАНИЕ: Это запрос на переписывание пункта ${point} плана урока на ${formData.value.language} языке.

НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${formData.value.topic}".

ИСХОДНЫЙ ПУНКТ ПЛАНА:
${pointContent || `Пункт ${point} (не найден явно в плане урока)`}

ЗАДАЧА:
Перепиши указанный пункт плана, чтобы сделать его более:
1. Подробным и детальным
2. Практически применимым в классе
3. Ориентированным на вовлечение учеников
4. Соответствующим уровню и возрасту учащихся

ОБРАТИ ВНИМАНИЕ: Это ${uiState.value.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${uiState.value.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
Адаптируй инструкции именно для ${uiState.value.individual_group === 'individual' ? 'работы с одним учеником' : 'работы с группой учеников'}.

ВАЖНО: Переписанный пункт должен быть на ${formData.value.language} языке и сохранять общую цель оригинального пункта.

ФОРМАТ ОТВЕТА:
Предоставь переписанный пункт ${point}, не спрашивая дополнительной информации.
Не начинай ответ с фраз типа "Вот переписанный пункт ${point}".
Просто предоставь содержательный переписанный пункт.`;
    } else {
      pointToRewrite = `rewrite_${point}`;
      actionText = `ВНИМАНИЕ: Это запрос на переписывание секции "${point}" плана урока на ${formData.value.language} языке.

НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${formData.value.topic}".

Перепиши указанную секцию, чтобы сделать ее более детальной и практически применимой.
Сохрани тему и цели оригинального плана, но улучши содержание и подход.

ОБРАТИ ВНИМАНИЕ: Это ${uiState.value.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${uiState.value.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
Адаптируй инструкции именно для ${uiState.value.individual_group === 'individual' ? 'работы с одним учеником' : 'работы с группой учеников'}.

ВАЖНО: Переписанная секция должна быть на ${formData.value.language} языке.

ФОРМАТ ОТВЕТА:
Предоставь переписанную секцию "${point}", не спрашивая дополнительной информации.
Не начинай ответ с фраз типа "Вот переписанная секция".
Просто предоставь содержательную переписанную секцию.`;
    }

    // Проверяем авторизацию пользователя
    if (!store.user || !store.user.id) {
      throw new Error('Пользователь не авторизован');
    }

    // Создаем данные для промпта в формате JSON
    const promptData = {
      content: lessonPlanContent,
      content_type: pointToRewrite,
      language: formData.value.language,
      age_group: uiState.value.age,
      methodology: Array.isArray(uiState.value.methodology) && uiState.value.methodology.length ? uiState.value.methodology.join(',') : '',
      is_individual: uiState.value.individual_group === 'individual',
      is_online: uiState.value.online_offline === 'online',
      lesson_focus: formData.value.topic,
      duration: formData.value.duration,
      level: formData.value.level,
      action: actionText,
      instruction_language: formData.value.language, // Явно указываем язык выходного контента
      original_point: pointContent || (typeof point === 'number' ? `Пункт ${point}` : `Секция "${point}"`)
    };

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: ContentType.LESSON_PLAN,
      prompt: JSON.stringify(promptData) // Передаем данные в формате JSON в поле prompt
    };

    console.log('Отправка запроса на переписывание пункта плана:', requestData);

    // Используем метод из store для отправки запроса вместо прямого fetch
    const result = await store.detailLessonPlan(requestData);

    if (result.error) {
      throw new Error(result.error);
    }

    console.log('Получен ответ на переписывание:', result);

    // Форматируем результат
    formattedDetailedContent.value = formatContent(result.content || '');

    // Сохраняем оригинальный пункт для отображения
    originalPointContent.value = pointContent || (typeof point === 'number' ? `Пункт ${point}` : `Секция "${point}"`);

    // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
    await store.fetchCurrentUser();
    console.log('Количество баллов после переписывания пункта плана:', store.user?.points);

    // Прокручиваем к детализированному содержимому
    setTimeout(() => {
      const detailedContent = document.querySelector('.detailed-content');
      if (detailedContent) {
        detailedContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  } catch (err: unknown) {
    console.error('Error rewriting lesson plan point:', err);
    if (err instanceof Error) {
      store.setError(`Ошибка при переписывании пункта плана: ${err.message}`);
    } else {
      store.setError('Ошибка при переписывании пункта плана: Неизвестная ошибка');
    }
  } finally {
    isDetailLoading.value = false;
  }
};

// Функции для генерации за баллы
// Детализация пункта плана за баллы
const detailLessonPlanPointWithPoints = async (point: string | number) => {
  try {
    isDetailLoading.value = true;
    const pointStr = String(point);
    detailedLessonContent.value = pointStr;

    // Устанавливаем заголовок в зависимости от типа пункта
    if (typeof point === 'number') {
      detailedContentTitle.value = `Детализация пункта ${point} (за баллы)`;
    } else {
      switch (point) {
        case 'script':
          detailedContentTitle.value = 'Скрипт учителя (за баллы)';
          break;
        case 'homework':
          detailedContentTitle.value = 'Домашнее задание (за баллы)';
          break;
        case 'exercises':
          detailedContentTitle.value = 'Дополнительные упражнения (за баллы)';
          break;
        case 'game':
          detailedContentTitle.value = 'Игра для урока (за баллы)';
          break;
        default:
          detailedContentTitle.value = `Детализация ${point} (за баллы)`;
      }
    }

    // Получаем содержимое плана урока
    const lessonPlanContent = generatedContent.value || '';

    // Используем новый сервис для детализации пункта плана за баллы
    try {
      console.log(`Детализация пункта ${point} плана урока за баллы`);

      let result;

      // Объединяем данные из formData и uiState для передачи в сервис
      const combinedFormData = {
        ...formData.value,
        age: uiState.value.age,
        methodology: uiState.value.methodology,
        individual_group: uiState.value.individual_group,
        online_offline: uiState.value.online_offline,
        previous_lesson: uiState.value.previous_lesson,
        grammar: uiState.value.grammar,
        vocabulary: uiState.value.vocabulary,
        exam: uiState.value.exam
      };

      if (typeof point === 'number') {
        // Детализация числового пункта
        // Добавляем отладочный лог для проверки передаваемых данных
        console.log('Детализация пункта плана за баллы. Передаваемые данные:', {
          lessonPlanContent,
          formData: combinedFormData,
          point
        });

        result = await lessonPlanDetailService.detailLessonPlanPointWithPoints(
          lessonPlanContent,
          combinedFormData,
          point
        );
      } else {
        // Детализация специального пункта
        switch (point) {
          case 'script':
            result = await lessonPlanDetailService.detailLessonPlanScriptWithPoints(
              lessonPlanContent,
              combinedFormData
            );
            break;
          case 'homework':
            result = await lessonPlanDetailService.detailLessonPlanHomeworkWithPoints(
              lessonPlanContent,
              combinedFormData
            );
            break;
          case 'exercises':
            result = await lessonPlanDetailService.detailLessonPlanExercisesWithPoints(
              lessonPlanContent,
              combinedFormData
            );
            break;
          case 'game':
            result = await lessonPlanDetailService.detailLessonPlanGameWithPoints(
              lessonPlanContent,
              combinedFormData
            );
            break;
          default:
            throw new Error(`Неизвестный тип пункта: ${point}`);
        }
      }

      // Форматируем результат
      detailedLessonContent.value = result;
      formattedDetailedContent.value = formatContent(result);

      // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
      await store.fetchCurrentUser();
      console.log('Количество баллов после детализации пункта плана за баллы:', store.user?.points);

      // Прокручиваем к детализированному содержимому
      setTimeout(() => {
        const detailedContent = document.querySelector('.detailed-content');
        if (detailedContent) {
          detailedContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);

    } catch (serviceError) {
      console.error('Ошибка при использовании сервиса детализации за баллы:', serviceError);
      throw serviceError;
    }
  } catch (err: unknown) {
    console.error('Error getting detailed lesson plan point with points:', err);
    if (err instanceof Error) {
      store.setError(`Ошибка при генерации за баллы: ${err.message}`);
    } else {
      store.setError('Ошибка при генерации за баллы: Неизвестная ошибка');
    }
  } finally {
    isDetailLoading.value = false;
  }
};

// Переписывание пункта плана за баллы
const rewriteLessonPlanPointWithPoints = async (point: string | number) => {
  try {
    isDetailLoading.value = true;
    const pointStr = String(point);
    detailedLessonContent.value = pointStr;
    detailedContentTitle.value = `Переписанный пункт ${point} (за баллы)`;

    // Проверяем баллы перед отправкой запроса
    console.log('Проверка баллов перед переписыванием пункта плана');
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN);

    if (!canGenerate) {
      throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.');
    }

    // Получаем содержимое плана урока
    const lessonPlanContent = generatedContent.value || '';

    // Определяем тип контента и действие в зависимости от запрошенного пункта
    let pointContent = '';

    // Если это числовой пункт, извлекаем его содержимое
    if (typeof point === 'number') {
      // Используем те же паттерны, что и в detailLessonPlanPoint
      const patterns = [
        // Формат "5. Заголовок"
        new RegExp(`${point}\\.(\\s+)?([^\\n]+)(\\n|$)`, 'i'),
        // Формат "5) Заголовок"
        new RegExp(`${point}\\)(\\s+)?([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Пункт 5: Заголовок"
        new RegExp(`[Пп]ункт\\s+${point}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Stage 5: Заголовок"
        new RegExp(`[Ss]tage\\s+${point}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Activity 5: Заголовок"
        new RegExp(`[Aa]ctivity\\s+${point}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "5. Заголовок" и следующие за ним строки до следующего пункта
        new RegExp(`${point}\\.(\\s+)?([^\\n]+)(\\n(?!\\d+\\.)[^\\n]+)*`, 'i')
      ];

      // Ищем содержимое пункта
      for (const pattern of patterns) {
        const match = lessonPlanContent.match(pattern);
        if (match && match[0]) {
          pointContent = match[0].trim();
          break;
        }
      }

      // Если не нашли пункт по паттернам, попробуем найти по номеру раздела
      if (!pointContent) {
        // Разбиваем план на разделы
        const sections = lessonPlanContent.split(/\n\s*\n/);

        // Ищем раздел, который может соответствовать нужному пункту
        if (sections.length >= point && point > 0) {
          // Берем раздел с индексом (point - 1), так как массивы начинаются с 0
          pointContent = sections[point - 1].trim();
        }
      }

      // Если все еще не нашли, используем общий подход - ищем по номеру в начале строки
      if (!pointContent) {
        const lines = lessonPlanContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].trim().startsWith(`${point}.`) ||
              lines[i].trim().startsWith(`${point})`) ||
              lines[i].trim().match(new RegExp(`^\\s*${point}[.:\\s)]`))) {
            let j = i + 1;
            pointContent = lines[i].trim();

            while (j < lines.length) {
              const nextLine = lines[j].trim();
              // Останавливаемся, если нашли следующий пункт или пустую строку
              if (nextLine === '' || /^\d+[.:]/.test(nextLine)) {
                break;
              }
              pointContent += '\n' + lines[j];
              j++;
            }
            break;
          }
        }
      }

      console.log(`Извлеченный пункт ${point} для переписывания за баллы:`, pointContent || 'Не найден');
    }

    // Создаем данные для промпта в формате JSON
    const promptData = {
      content: lessonPlanContent,
      content_type: typeof point === 'number' ? `rewrite_point_${point}` : `rewrite_${point}`,
      language: formData.value.language,
      age_group: uiState.value.age,
      methodology: Array.isArray(uiState.value.methodology) && uiState.value.methodology.length ? uiState.value.methodology.join(',') : '',
      is_individual: uiState.value.individual_group === 'individual',
      is_online: uiState.value.online_offline === 'online',
      lesson_focus: formData.value.topic,
      duration: formData.value.duration,
      level: formData.value.level,
      action: `ВНИМАНИЕ: Это запрос на переписывание пункта ${point} плана урока на ${formData.value.language} языке.

НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${formData.value.topic}".

ИСХОДНЫЙ ПУНКТ ПЛАНА:
${pointContent || `Пункт ${point} (не найден явно в плане урока)`}

ЗАДАЧА:
Перепиши указанный пункт плана, чтобы сделать его более:
1. Подробным и детальным
2. Практически применимым в классе
3. Ориентированным на вовлечение учеников
4. Соответствующим уровню и возрасту учащихся

ОБРАТИ ВНИМАНИЕ: Это ${uiState.value.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${uiState.value.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
Адаптируй инструкции именно для ${uiState.value.individual_group === 'individual' ? 'работы с одним учеником' : 'работы с группой учеников'}.

ВАЖНО: Переписанный пункт должен быть на ${formData.value.language} языке и сохранять общую цель оригинального пункта.

ФОРМАТ ОТВЕТА:
Предоставь переписанный пункт ${point}, не спрашивая дополнительной информации.
Не начинай ответ с фраз типа "Вот переписанный пункт ${point}".
Просто предоставь содержательный переписанный пункт.`,
      instruction_language: formData.value.language,
      original_point: pointContent || (typeof point === 'number' ? `Пункт ${point}` : `Секция "${point}"`)
    };

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user?.id,
      type: ContentType.LESSON_PLAN,
      prompt: JSON.stringify(promptData),
      with_points: true, // Указываем, что это генерация за баллы
      skip_points_check: true // Указываем, что баллы уже были списаны
    };

    console.log('Отправка запроса на переписывание пункта плана за баллы:', requestData);

    // Используем метод из store для отправки запроса
    const result = await store.detailLessonPlan(requestData);

    if (result.error) {
      throw new Error(result.error);
    }

    console.log('Получен ответ на переписывание за баллы:', result);

    // Форматируем результат
    formattedDetailedContent.value = formatContent(result.content || '');

    // Сохраняем оригинальный пункт для отображения
    originalPointContent.value = pointContent || (typeof point === 'number' ? `Пункт ${point}` : `Секция "${point}"`);

    // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
    await store.fetchCurrentUser();
    console.log('Количество баллов после переписывания пункта плана за баллы:', store.user?.points);

    // Прокручиваем к детализированному содержимому
    setTimeout(() => {
      const detailedContent = document.querySelector('.detailed-content');
      if (detailedContent) {
        detailedContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  } catch (err: unknown) {
    console.error('Error rewriting lesson plan point with points:', err);
    if (err instanceof Error) {
      store.setError(`Ошибка при переписывании пункта плана за баллы: ${err.message}`);
    } else {
      store.setError('Ошибка при переписывании пункта плана за баллы: Неизвестная ошибка');
    }
  } finally {
    isDetailLoading.value = false;
  }
};
</script>

<style scoped>
.lesson-plan-view {
  width: 100%;
  min-height: 100vh;
  position: relative;
  background-color: transparent;
  overflow-x: hidden;
}

/* Декоративная планета */
.planet-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 300px;
  z-index: 1;
  pointer-events: none;
}

/* Контейнер контента */
.content-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 170px 1rem 1rem;
  position: relative;
  z-index: 2;
}

/* Контейнер заголовка */
.title-container {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.75rem 1.25rem;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  text-align: center;
}

/* Стиль заголовка */
.title-container h2 {
  color: white;
  font-size: 2.2rem;
  margin: 0;
  text-align: center;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
}

/* Группы полей формы */
.form-group {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

/* Поля ввода */
.form-input,
.form-select,
.form-textarea {
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

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  box-shadow: 0 0 0 3px rgba(255, 103, 231, 0.4), inset 0 2px 6px rgba(0, 0, 0, 0.1);
  outline: none;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

/* Кнопки выбора возраста */
.age-buttons {
  display: flex;
  gap: 0.5rem;
}

.age-btn {
  flex: 1;
  padding: 0.75rem 0.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.age-btn.active {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
  transform: scale(1.05);
}

/* Кнопки формата урока */
.format-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.format-row {
  display: flex;
  gap: 0.5rem;
}

.format-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem 0.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.format-btn .icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.format-btn.active {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
  transform: scale(1.05);
}

/* Контейнер для кнопки генерации */
.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
  margin-bottom: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 1rem;
  padding: 1.25rem 1rem;
}

/* Контейнер для вертикального расположения кнопок */
.buttons-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 1.75rem; /* Увеличиваем расстояние между кнопками, чтобы они не налазили друг на друга */
}

/* Кнопка генерации */
.generate-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1rem;
  background-color: #ec407a; /* Розовый цвет для основной кнопки генерации */
  border: none;
  border-radius: 1rem;
  color: white;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(236, 64, 122, 0.5);
}

.generate-button:hover:not(:disabled) {
  background-color: #ff67e7; /* Более яркий розовый при наведении */
  box-shadow: 0 6px 18px rgba(255, 103, 231, 0.6);
  transform: translateY(-2px);
}

.generate-button:disabled {
  background-color: #687284;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* Отдельный стиль для отключенной кнопки генерации за баллы */
.points-generate-button:disabled {
  background-color: #687284;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* Анимированная загрузка */
.loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Сообщение об ошибке */
.error-message {
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: rgba(220, 53, 69, 0.2);
  border-left: 4px solid #dc3545;
  border-radius: 0 0.5rem 0.5rem 0;
  color: white;
  position: relative;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.2);
}

.close-button {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1.2rem;
}

/* Результат генерации */
.result-container {
  margin-top: 2.5rem;
  padding: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15);
}

.result-container h3 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.result-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 0.75rem;
  color: #333;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.action-button:hover:not(:disabled) {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.4);
  transform: translateY(-1px);
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Стилизованное содержимое плана */
.plan-content {
  padding: 1.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 1rem;
  color: #333;
  line-height: 1.6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Стиль для кнопки копирования */
.copy-button {
  background-color: #6a1b9a;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(106, 27, 154, 0.4);
}

.copy-button:hover {
  background-color: #8e24aa;
  box-shadow: 0 6px 16px rgba(142, 36, 170, 0.5);
  transform: translateY(-2px);
}

.bottom-copy-action {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}

.bottom-copy-action .copy-button {
  padding: 0.75rem 1.5rem;
  font-size: 1.1rem;
}

/* Отступ для нижней навигации */
.bottom-spacer {
  width: 100%;
  height: 80px;
  display: block;
}

/* Стиль для подсказки */
.form-helper {
  margin-top: 0.5rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  font-style: italic;
}

/* Стили для выпадающих списков */
.form-select {
  max-height: 300px;
  overflow-y: auto;
}

.form-select option {
  padding: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Стили для форматированного контента */
:deep(.lesson-plan-section-header) {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  display: block;
}

:deep(.lesson-plan-bold) {
  color: #000000;
  background-color: #ffcce0;
  padding: 0 5px;
  border-radius: 3px;
  display: inline-block;
  font-weight: bold;
}

:deep(.lesson-plan-italic) {
  color: #000000;
  background-color: #ffe6ee;
  padding: 0 5px;
  border-radius: 3px;
  display: inline-block;
  font-style: italic;
}

:deep(.lesson-plan-heading) {
  color: #ffffff;
  font-weight: bold;
  background-color: #ec407a;
  padding: 0.75rem 1rem;
  border-radius: 5px;
  display: inline-block;
  margin-bottom: 1rem;
}

:deep(.lesson-plan-subheading) {
  color: #ffffff;
  font-weight: bold;
  background-color: #ff9ebb;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 0.75rem;
}

:deep(.lesson-plan-paragraph) {
  color: #000000;
  background-color: #f8f8f8;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid #ec407a;
}

:deep(.lesson-plan-empty-paragraph) {
  color: #000000;
  background-color: #f8f8f8;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid #ec407a;
}

:deep(.lesson-plan-list) {
  background-color: #f0f0f0;
  padding: 0.75rem 0.75rem 0.75rem 2.5rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  border-left: 4px solid #ec407a;
  list-style-type: disc;
  display: block;
}

:deep(.lesson-plan-list-item) {
  color: #000000;
  padding: 0.3rem 0;
  margin-bottom: 0.5rem;
  display: list-item;
}

/* Медиа-запросы для мобильных устройств */
@media (max-width: 768px) {
  .age-buttons {
    flex-direction: column;
  }

  .generate-button {
    padding: 0.75rem;
  }

  .content-container {
    padding-top: 120px;
  }

  .title-container {
    padding: 1.25rem 1rem;
  }

  .title-container h2 {
    font-size: 1.8rem;
  }

  .form-group {
    margin-bottom: 1.2rem;
    padding: 1rem;
  }
}

/* Дополнительные стили для детализации плана урока */
.lesson-plan-details-buttons {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.buttons-group {
  margin-bottom: 1.5rem;
}

.buttons-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

/* Медиа-запросы для адаптивного отображения кнопок */
@media (max-width: 768px) {
  .buttons-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .buttons-grid {
    grid-template-columns: 1fr;
  }
}

.detail-button {
  padding: 0.75rem 0.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 0.75rem;
  color: #333;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.detail-button:hover:not(:disabled) {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.4);
  transform: translateY(-1px);
}

.detail-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.rewrite {
  background-color: #ff67e7;
  color: white;
}

.rewrite:hover:not(:disabled) {
  background-color: #ff9ebb;
  color: #333;
}

.detailed-content {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.detailed-content h4 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.close-detail-button {
  margin-top: 1.5rem;
  padding: 0.75rem 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 0.75rem;
  color: #333;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.close-detail-button:hover {
  background-color: #ff67e7;
  color: white;
}

/* Индикатор загрузки для детализации плана */
.detail-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.detail-loading-overlay .loader {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.detail-loading-overlay p {
  color: white;
  margin-top: 1rem;
  font-size: 1.2rem;
  font-weight: 500;
}

/* Дополнительные стили для детализации плана урока */
.original-point-content {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.original-point-content h5 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.original-content-text {
  color: white;
  font-size: 1rem;
  line-height: 1.6;
}

/* Добавляем стили для спиннера загрузки */
.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Стиль для отключенной кнопки - применяем только один раз */
.generate-button:disabled {
  background-color: #687284;
  cursor: not-allowed;
}
/* Стили для секции генерации за баллы */
.points-generation-section {
  margin-top: 1.5rem;
  margin-bottom: 1.5rem;
}

.points-generation-details {
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 0.5rem;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.points-generation-summary {
  padding: 0.75rem;
  cursor: pointer;
  font-weight: 600;
  color: white;
  display: flex;
  align-items: center;
  border-radius: 0.75rem;
  transition: background-color 0.2s;
}

/* Стили для кнопки генерации за баллы */
.points-generate-button {
  background-color: #1e88e5; /* Голубой цвет для кнопки генерации за баллы */
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5);
}

.points-generate-button:hover:not(:disabled) {
  background-color: #42a5f5; /* Более светлый голубой при наведении */
  box-shadow: 0 6px 18px rgba(30, 136, 229, 0.6);
  transform: translateY(-2px);
}

.points-icon {
  margin-right: 0.5rem;
  display: inline-block;
  font-size: 1.2rem;
}

.points-generation-summary:hover {
  background-color: rgba(255, 103, 231, 0.2);
}

/* Специальный стиль для иконки в кнопке генерации за баллы */
.points-generate-button .points-icon {
  color: #ffffff;
}

.points-generation-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0.75rem;
  margin-top: 0.5rem;
}

.points-info {
  color: #ffccf3;
  margin-bottom: 1rem;
  font-style: italic;
}

.points-balance {
  display: block;
  margin-top: 0.5rem;
  font-size: 1rem;
  color: #ffffff;
  background-color: rgba(0, 0, 0, 0.2);
  padding: 0.5rem;
  border-radius: 0.5rem;
  text-align: center;
  font-style: normal;
}

.points-balance strong {
  color: #ffcc00;
  font-size: 1.1rem;
}

.detail-button.points-button {
  background-color: rgba(30, 136, 229, 0.3) !important; /* Используем тот же голубой цвет, что и для основной кнопки */
  border: 1px solid rgba(30, 136, 229, 0.5) !important;
}

.detail-button.points-button:hover {
  background-color: rgba(30, 136, 229, 0.5) !important;
  box-shadow: 0 0 10px rgba(30, 136, 229, 0.5) !important;
}

.detail-button.points-button.rewrite {
  background-color: rgba(255, 215, 0, 0.3) !important;
  border: 1px solid rgba(255, 215, 0, 0.5) !important;
}

.detail-button.points-button.rewrite:hover {
  background-color: rgba(255, 215, 0, 0.5) !important;
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
}
</style>
