<template>
  <div
    ref="rootContainer"
    class="exercises-lesson-plan-container"
    :class="{ 'exercises-global-background-active': isMounted }"
  >
    <div class="exercises-planet-background" :style="planetStyle"></div>
    <div class="exercises-content-wrapper">
      <div class="exercises-content">
        <!-- Заголовок -->
        <div class="exercises-title-form-group">
          <h2 class="exercises-title">Exercise Generation</h2>
        </div>

        <!-- Отображение лимитов генераций -->
        <GenerationLimitsDisplay :type="ContentType.LESSON_PLAN" />

        <!-- Сообщение об ошибке -->
        <ErrorMessage
          v-if="error"
          :error="error"
          class="exercises-error-message"
        />

        <!-- Форма генерации -->
        <form @submit.prevent="generateExercises" class="exercises-generation-form">
          <!-- Язык -->
          <div class="exercises-form-group">
            <label for="exercises-language">Language:</label>
            <select
              v-model="formData.language"
              id="exercises-language"
              required
              class="exercises-form-select"
            >
              <option value="english">English</option>
              <option value="spanish">Spanish</option>
              <option value="french">French</option>
              <option value="german">German</option>
              <option value="italian">Italian</option>
              <option value="chinese">Chinese</option>
              <option value="russian">Russian</option>
              <option value="arabic">Arabic</option>
            </select>
          </div>

          <!-- Уровень владения -->
          <div class="exercises-form-group">
            <label for="exercises-proficiency">Proficiency Level:</label>
            <select
              v-model="formData.proficiency"
              id="exercises-proficiency"
              required
              class="exercises-form-select"
            >
              <option value="beginner">Beginner (A1-A2)</option>
              <option value="intermediate">Intermediate (B1-B2)</option>
              <option value="advanced">Advanced (C1-C2)</option>
            </select>
          </div>

          <!-- Тема -->
          <div class="exercises-form-group">
            <label for="exercises-topic">Topic:</label>
            <input
              v-model="formData.topic"
              id="exercises-topic"
              required
              class="exercises-form-input"
              placeholder="Enter exercise topic"
            >
          </div>

          <!-- Выбор темы -->
          <div class="exercises-theme-selection">
            <h3 class="exercises-section-title">Exercise Theme</h3>
            <div class="exercises-themes-grid">
              <button
                v-for="theme in themes"
                :key="theme.value"
                type="button"
                @click="selectTheme(theme.value)"
                :class="[
                  'exercises-theme-button',
                  { 'exercises-active-theme': formData.theme === theme.value }
                ]"
              >
                <span class="exercises-theme-icon">{{ theme.icon }}</span>
                <span class="exercises-theme-label">{{ theme.label }}</span>
              </button>
            </div>
          </div>

          <!-- Творческие элементы -->
          <div class="exercises-creative-elements">
            <h3 class="exercises-section-title">Creative Elements</h3>

            <!-- Типы упражнений -->
            <div class="exercises-exercise-types">
              <h4 class="exercises-subtitle">Exercise Types</h4>
              <div class="exercises-types-grid">
                <div
                  v-for="type in exerciseTypes"
                  :key="type.id"
                  class="exercises-type-item"
                >
                  <label :for="type.id" class="exercises-type-label">
                    <input
                      type="checkbox"
                      :id="type.id"
                      v-model="formData.selectedTypes"
                      :value="type.id"
                      class="exercises-checkbox"
                    >
                    <div class="exercises-type-content">
                      <span class="exercises-type-icon">{{ type.icon }}</span>
                      <span class="exercises-type-title">{{ type.label }}</span>
                      <p class="exercises-type-description">{{ type.description }}</p>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <!-- Популярные форматы -->
            <div class="exercises-formats-section">
              <h4 class="exercises-subtitle">Popular Exercise Formats</h4>
              <div class="exercises-formats-grid">
                <div
                  v-for="format in exerciseFormats"
                  :key="format.id"
                  class="exercises-format-item"
                >
                  <label :for="format.id" class="exercises-format-label">
                    <input
                      type="checkbox"
                      :id="format.id"
                      v-model="formData.selectedFormats"
                      :value="format.id"
                      class="exercises-checkbox"
                    >
                    <div class="exercises-format-content">
                      <span class="exercises-format-icon">{{ format.icon }}</span>
                      <span class="exercises-format-title">{{ format.label }}</span>
                      <p class="exercises-format-description">{{ format.description }}</p>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <!-- Интерактивные функции -->
            <div class="exercises-features-section">
              <h4 class="exercises-subtitle">Interactive Features</h4>
              <div class="exercises-features-buttons">
                <button
                  v-for="feature in interactiveFeatures"
                  :key="feature.id"
                  type="button"
                  @click="toggleFeature(feature.id)"
                  :class="[
                    'exercises-feature-button',
                    { 'exercises-active-feature': formData.interactiveFeatures.includes(feature.id) }
                  ]"
                >
                  <span>{{ feature.icon }}</span>
                  <span>{{ feature.label }}</span>
                </button>
              </div>
            </div>

            <!-- Геймификация -->
            <div class="exercises-gamification-section">
              <h4 class="exercises-subtitle">Gamification Elements</h4>
              <div class="exercises-gamification-buttons">
                <button
                  v-for="element in gamificationElements"
                  :key="element.id"
                  type="button"
                  @click="toggleGamification(element.id)"
                  :class="[
                    'exercises-gamification-button',
                    { 'exercises-active-gamification': formData.gamification.includes(element.id) }
                  ]"
                >
                  <span>{{ element.icon }}</span>
                  <span>{{ element.label }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Настройки упражнений -->
          <div class="exercises-settings-section">
            <h3 class="exercises-section-title">Exercise Settings</h3>
            <div class="exercises-settings-grid">
              <!-- Difficulty -->
              <div class="exercises-difficulty-group">
                <label>Exercise Difficulty</label>
                <div class="exercises-difficulty-buttons">
                  <button
                    v-for="level in difficultyLevels"
                    :key="level.value"
                    type="button"
                    @click="setDifficulty(level.value)"
                    :class="[
                      'exercises-difficulty-btn',
                      { 'exercises-active-difficulty': formData.difficulty === level.value }
                    ]"
                  >
                    {{ level.label }}
                  </button>
                </div>
              </div>

              <!-- Quantity -->
              <div class="exercises-quantity-group">
                <label>Number of Exercises</label>
                <div class="exercises-quantity-controls">
                  <button
                    type="button"
                    @click="decrementQuantity"
                    :disabled="formData.quantity <= 1"
                    class="exercises-quantity-btn"
                  >
                    -
                  </button>
                  <span class="exercises-quantity-value">{{ formData.quantity }}</span>
                  <button
                    type="button"
                    @click="incrementQuantity"
                    :disabled="formData.quantity >= 10"
                    class="exercises-quantity-btn"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Формат урока -->
          <div class="exercises-format-options">
            <h3 class="exercises-section-title">Lesson Format</h3>
            <div class="exercises-format-grid">
              <div class="exercises-type-group">
                <h4 class="exercises-subtitle">Class Type</h4>
                <div class="exercises-type-buttons">
                  <button
                    type="button"
                    @click="formData.individual_group = 'individual'"
                    :class="[
                      'exercises-type-btn',
                      { 'exercises-active-type': formData.individual_group === 'individual' }
                    ]"
                  >
                    👤 Individual
                  </button>
                  <button
                    type="button"
                    @click="formData.individual_group = 'group'"
                    :class="[
                      'exercises-type-btn',
                      { 'exercises-active-type': formData.individual_group === 'group' }
                    ]"
                  >
                    👥 Group
                  </button>
                </div>
              </div>

              <div class="exercises-mode-group">
                <h4 class="exercises-subtitle">Delivery Format</h4>
                <div class="exercises-mode-buttons">
                  <button
                    type="button"
                    @click="formData.online_offline = 'online'"
                    :class="[
                      'exercises-mode-btn',
                      { 'exercises-active-mode': formData.online_offline === 'online' }
                    ]"
                  >
                    💻 Online
                  </button>
                  <button
                    type="button"
                    @click="formData.online_offline = 'offline'"
                    :class="[
                      'exercises-mode-btn',
                      { 'exercises-active-mode': formData.online_offline === 'offline' }
                    ]"
                  >
                    🏫 Offline
                  </button>
                </div>
              </div>
            </div>

            <!-- Дополнительные опции -->
            <div class="exercises-checkbox-group">
              <label class="exercises-option-checkbox">
                <input
                  type="checkbox"
                  v-model="formData.includeAnswers"
                  class="exercises-checkbox"
                >
                <span>Include Answers</span>
              </label>
              <label class="exercises-option-checkbox">
                <input
                  type="checkbox"
                  v-model="formData.includeInstructions"
                  class="exercises-checkbox"
                >
                <span>Teacher Instructions</span>
              </label>
              <label class="exercises-option-checkbox">
                <input
                  type="checkbox"
                  v-model="formData.adaptiveDifficulty"
                  class="exercises-checkbox"
                >
                <span>Adaptive Difficulty</span>
              </label>
            </div>
          </div>

          <!-- Кнопки генерации -->
          <div class="exercises-form-actions">
            <div class="exercises-buttons-container">
              <button
                type="submit"
                :disabled="isGenerating || !canGenerate"
                class="exercises-generate-button"
              >
                <span v-if="isGenerating" class="exercises-loader"></span>
                <template v-if="!canGenerate">
                  Generation Limit Reached
                </template>
                <template v-else-if="isGenerating">
                  Generating...
                </template>
                <template v-else>
                  Generate Exercises
                </template>
              </button>

              <button
                type="button"
                class="exercises-generate-button exercises-points-generate-button"
                :disabled="isGenerating"
                @click="generateExercisesWithPoints"
              >
                <span v-if="isGenerating" class="exercises-loader"></span>
                <template v-if="isGenerating">
                  Generating...
                </template>
                <template v-else>
                  <span class="exercises-points-icon">💎</span> Generate for 8 Points
                </template>
              </button>
            </div>
          </div>
        </form>

        <!-- Результаты генерации -->
        <div
          v-if="generatedContent.length > 0"
          class="exercises-generation-results"
        >
          <div class="exercises-results-header">
            <h3 class="exercises-results-title">Generated Exercises</h3>
            <div class="exercises-results-actions">
              <button
                @click="regenerateAll"
                :disabled="!canGenerate"
                class="exercises-regenerate-btn"
              >
                🔄 Refresh All
              </button>
              <button
                @click="regenerateAllWithPoints"
                class="exercises-regenerate-btn exercises-points-regenerate-btn"
              >
                💎 Refresh for 8 Points
              </button>
              <button
                @click="copyAllExercises"
                class="exercises-copy-btn"
              >
                📋 Copy All
              </button>
            </div>
          </div>

          <!-- Отображение баллов пользователя -->
          <div class="exercises-points-display">
            <details class="exercises-points-details">
              <summary class="exercises-points-summary">
                <span class="exercises-points-icon">💎</span> Points Balance
              </summary>
              <div class="exercises-points-content">
                <p class="exercises-points-info">
                  Your current balance: <strong>{{ userPoints }}</strong> points
                </p>
                <p class="exercises-points-description">
                  Use points to generate without daily plan limits.
                  Each generation costs 8 points.
                </p>
              </div>
            </details>
          </div>

          <div class="exercises-cards-container">
            <div
              v-for="(exercise, index) in generatedContent"
              :key="index"
              class="exercises-card"
            >
              <div class="exercises-card-header">
                <div class="exercises-card-title">
                  <h4>Exercise {{ index + 1 }}</h4>
                  <p class="exercises-card-type">{{ getExerciseType(exercise.type) }}</p>
                </div>
                <div class="exercises-card-actions">
                  <button
                    @click="regenerateExercise(index)"
                    :disabled="!canGenerate"
                    class="exercises-action-btn"
                    title="Обновить упражнение"
                  >
                    🔄
                  </button>
                  <button
                    @click="regenerateExerciseWithPoints(index)"
                    class="exercises-action-btn exercises-points-action-btn"
                    title="Обновить упражнение за 8 баллов"
                  >
                    💎
                  </button>
                  <button
                    @click="copyExercise(index)"
                    class="exercises-action-btn"
                    title="Копировать упражнение"
                  >
                    📋
                  </button>
                </div>
              </div>

              <div class="exercises-card-content">
                <ExercisesMarkdownRenderer
                  :content="exercise.content || ''"
                  class="exercises-markdown"
                />
              </div>

              <div v-if="exercise.answers" class="exercises-answers-section">
                <h5 class="exercises-section-label">Answers</h5>
                <div class="exercises-answers-content">
                  <ExercisesMarkdownRenderer
                    :content="formatAnswers(exercise.answers)"
                    class="exercises-markdown"
                  />
                </div>
              </div>

              <div v-if="exercise.instructions" class="exercises-instructions-section">
                <h5 class="exercises-section-label">Teacher Instructions</h5>
                <div class="exercises-instructions-content">
                  <ExercisesMarkdownRenderer
                    :content="exercise.instructions || ''"
                    class="exercises-markdown"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'

// Объявляем тип для Window
declare global {
  interface Window {
    saveComponentStyles?: (componentName: string, selectors: string[]) => void;
  }
}
import { useMainStore } from '@/store'
import ExercisesMarkdownRenderer from './common/ExercisesMarkdownRenderer.vue'
import ErrorMessage from './ErrorMessage.vue'
import LoadingState from './LoadingState.vue'
import planetBg from '@/assets/images/planets/exercises-background-image.svg'
import GenerationLimitsDisplay from './common/GenerationLimitsDisplay.vue'
import { ContentType, UNLIMITED_ROLES, UserRole } from '@/core/constants'
import { getAuthHeaders } from '@/utils/auth'

const store = useMainStore()
const rootContainer = ref<HTMLElement | null>(null)
const isMounted = ref(false)

// Состояния
const error = computed(() => store.error)
const isGenerating = ref(false)
const generatedContent = ref<Exercise[]>([])
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)

// Лимиты генераций
const canGenerate = computed(() => store.canGenerate(ContentType.LESSON_PLAN))
const isUnlimited = computed(() => {
  return store.user?.role && (UNLIMITED_ROLES as readonly UserRole[]).includes(store.user.role)
})
const remainingGenerations = computed(() => store.remainingGenerations(ContentType.LESSON_PLAN))
const userPoints = computed(() => store.user?.points || 0)

// Стили для планеты
const planetStyle = computed(() => {
  return {
    backgroundImage: `url(${planetBg})`,
    backgroundSize: isMobile.value ? '75% auto' : '45% auto',
    backgroundPosition: isMobile.value ? 'center 45px' : 'center 0',
    backgroundRepeat: 'no-repeat'
  }
})

// Данные формы
interface Exercise {
  id: string
  type: string
  content: string
  answers?: string
  instructions?: string
}

interface ExerciseFormData {
  language: string
  proficiency: string
  theme: string
  topic: string
  difficulty: string
  quantity: number
  selectedTypes: string[]
  selectedFormats: string[]
  interactiveFeatures: string[]
  gamification: string[]
  includeAnswers: boolean
  includeInstructions: boolean
  adaptiveDifficulty: boolean
  individual_group: string
  online_offline: string
}

const formData = reactive<ExerciseFormData>({
  language: '',
  proficiency: 'intermediate',
  theme: '',
  topic: '',
  difficulty: 'medium',
  quantity: 3,
  selectedTypes: [],
  selectedFormats: [],
  interactiveFeatures: [],
  gamification: [],
  includeAnswers: true,
  includeInstructions: true,
  adaptiveDifficulty: false,
  individual_group: 'individual',
  online_offline: 'online'
})

// Опции
const themes = [
  { value: 'adventure', label: 'Adventure Quest', icon: '🗺️' },
  { value: 'mystery', label: 'Mystery Investigation', icon: '🔍' },
  { value: 'scienceFiction', label: 'Space Exploration', icon: '🚀' },
  { value: 'fantasy', label: 'Magical Academy', icon: '🔮' },
  { value: 'nature', label: 'Wildlife Discovery', icon: '🌿' },
  { value: 'history', label: 'Time Travel', icon: '⏰' },
  { value: 'cooking', label: 'Culinary Journey', icon: '👨‍🍳' },
  { value: 'arts', label: 'Creative Studio', icon: '🎨' }
]

const exerciseTypes = [
  {
    id: 'story',
    label: 'Story-based',
    icon: '📖',
    description: 'Create exercises based on engaging stories'
  },
  {
    id: 'roleplay',
    label: 'Role-playing',
    icon: '🎭',
    description: 'Practice through interactive dialogues'
  },
  {
    id: 'quiz',
    label: 'Interactive Quiz',
    icon: '❓',
    description: 'Test knowledge with dynamic quizzes'
  },
  {
    id: 'game',
    label: 'Language Games',
    icon: '🎮',
    description: 'Learn through fun game activities'
  },
  {
    id: 'project',
    label: 'Creative Projects',
    icon: '🎨',
    description: 'Express creativity while learning'
  },
  {
    id: 'media',
    label: 'Media Creation',
    icon: '🎥',
    description: 'Create videos, podcasts, and more'
  }
]

const exerciseFormats = [
  {
    id: 'gap_fill',
    label: 'Gap Fill',
    icon: '📝',
    description: 'Fill in the blanks with appropriate words'
  },
  {
    id: 'sentence_building',
    label: 'Sentence Building',
    icon: '🔤',
    description: 'Create sentences from a set of words'
  },
  {
    id: 'open_brackets',
    label: 'Open Brackets',
    icon: '( )',
    description: 'Put words in brackets in the correct form'
  },
  {
    id: 'sentence_matching',
    label: 'Sentence Matching',
    icon: '🔗',
    description: 'Connect parts of sentences together'
  },
  {
    id: 'word_definition',
    label: 'Word-Definition Matching',
    icon: '📚',
    description: 'Match words with their definitions'
  }
]

const interactiveFeatures = [
  {
    id: 'collaboration',
    label: 'Group Activities',
    icon: '🤝',
    description: 'Work together with other learners'
  }
]

const gamificationElements = [
  { id: 'points', label: 'Points System', icon: '🎯' },
  { id: 'badges', label: 'Achievement Badges', icon: '🏅' },
  { id: 'levels', label: 'Level System', icon: '📈' },
  { id: 'rewards', label: 'Rewards', icon: '🎁' },
  { id: 'challenges', label: 'Challenges', icon: '⚔️' },
  { id: 'streaks', label: 'Streaks', icon: '🔥' }
]

const difficultyLevels = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' }
]

// Вспомогательная функция для приведения упражнений к нужному формату
const normalizeExercises = (exercises: any[]): Exercise[] => {
  return exercises.map((ex, index) => {
    // Если упражнение уже в нужном формате
    if (ex && typeof ex === 'object' && ex.content) {
      return {
        id: ex.id || `exercise-${index}`,
        type: ex.type || 'exercise',
        content: ex.content || '',
        answers: ex.answers || ex.answer || undefined,
        instructions: ex.instructions || ex.instruction || undefined
      }
    }

    // Если это строка, преобразуем в объект
    if (typeof ex === 'string') {
      return {
        id: `exercise-${index}`,
        type: 'exercise',
        content: ex,
        answers: undefined,
        instructions: undefined
      }
    }

    // Если это просто объект с контентом
    return {
      id: `exercise-${index}`,
      type: 'exercise',
      content: ex || '',
      answers: undefined,
      instructions: undefined
    }
  })
}

// Методы
const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}

const selectTheme = (theme: string) => {
  formData.theme = theme
}

const toggleGamification = (elementId: string) => {
  const index = formData.gamification.indexOf(elementId)
  index === -1
    ? formData.gamification.push(elementId)
    : formData.gamification.splice(index, 1)
}

const toggleFeature = (featureId: string) => {
  const index = formData.interactiveFeatures.indexOf(featureId)
  index === -1
    ? formData.interactiveFeatures.push(featureId)
    : formData.interactiveFeatures.splice(index, 1)
}

const incrementQuantity = () => {
  if (formData.quantity < 10) formData.quantity++
}

const decrementQuantity = () => {
  if (formData.quantity > 1) formData.quantity--
}

const setDifficulty = (difficulty: string) => {
  formData.difficulty = difficulty
  nextTick(() => {
    const temp = formData.difficulty
    formData.difficulty = ''
    setTimeout(() => formData.difficulty = temp, 0)
  })
}

const getExerciseType = (type: string) => {
  return exerciseTypes.find(t => t.id === type)?.label || type
}

const formatAnswers = (answers: string | undefined): string => {
  if (!answers) return ''
  return answers.match(/^\d+\./m)
    ? answers.split('\n').filter(line => line.trim()).join('\n')
    : answers
}

// Методы для генерации и манипуляции с упражнениями
const generateExercises = async () => {
  if (!canGenerate.value) return

  isGenerating.value = true
  store.clearError() // Clear error through store

  try {
    // Check required fields
    if (!formData.language) {
      throw new Error('Please select a language')
    }

    if (!formData.topic) {
      throw new Error('Please specify the exercise topic')
    }

    // Track usage for limits and update local counters
    try {
      await store.checkAndTrackGeneration(ContentType.EXERCISE);
    } catch (limitError: any) {
      console.error('Ошибка при проверке лимитов:', limitError);
      // Если ошибка связана с отсутствием тарифа, предлагаем использовать баллы
      if (limitError.message && (
          limitError.message.includes('No active tariff') ||
          limitError.message.includes('Нет активного тарифа') ||
          limitError.message.includes('403')
        )) {
        if (store.user && store.user.points >= 8) {
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points for exercise generation?')) {
            await generateExercisesWithPoints();
            return;
          } else {
            store.setError('To generate, you need to purchase a tariff or use points.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. To generate, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // API call for exercise generation
    const response = await fetch('/api/exercises/generate', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(), // Добавляем заголовок авторизации
      },
      body: JSON.stringify({
        language: formData.language,
        proficiency: formData.proficiency,
        topic: formData.topic,
        theme: formData.theme,
        difficulty: formData.difficulty,
        quantity: formData.quantity,
        exerciseTypes: formData.selectedTypes,
        formats: formData.selectedFormats,
        interactiveFeatures: formData.interactiveFeatures,
        gamification: formData.gamification,
        includeAnswers: formData.includeAnswers,
        includeInstructions: formData.includeInstructions,
        adaptiveDifficulty: formData.adaptiveDifficulty,
        individualGroup: formData.individual_group,
        onlineOffline: formData.online_offline
      })
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()
    // Use processed_content if exercises doesn't exist
    const rawExercises = data.exercises || data.data?.processed_content || []
    generatedContent.value = normalizeExercises(rawExercises)

    // Local counters are already updated in checkAndTrackGeneration()
  } catch (err) {
    store.setError('Error generating exercises') // Set error through store
    console.error(err)
  } finally {
    isGenerating.value = false
  }
}

// Функции для работы с баллами пользователя
const getUserPoints = async (): Promise<number> => {
  try {
    const response = await fetch('/api/users/me', {
      headers: {
        ...getAuthHeaders()
      }
    })

    if (!response.ok) {
      console.error('Ошибка при получении данных пользователя:', response.status)
      return 0
    }

    const userData = await response.json()
    return userData.points || 0
  } catch (error) {
    console.error('Ошибка при получении баллов пользователя:', error)
    return 0
  }
}

// Метод updateUserPoints удален, так как заменен на store.fetchCurrentUser()

// Генерация упражнений за баллы
const generateExercisesWithPoints = async () => {
  isGenerating.value = true
  store.clearError() // Clear error through store

  try {
    // Check required fields
    if (!formData.language) {
      throw new Error('Please select a language')
    }

    if (!formData.topic) {
      throw new Error('Please specify the exercise topic')
    }

    // Получаем текущее количество баллов пользователя перед генерацией
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед генерацией:', initialPoints)

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.EXERCISE, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for exercise generation. 8 points required.')
    }

    // Вызываем API для генерации упражнений напрямую
    const response = await fetch('/api/exercises/generate', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(), // Добавляем заголовок авторизации
      },
      body: JSON.stringify({
        language: formData.language,
        proficiency: formData.proficiency,
        topic: formData.topic,
        theme: formData.theme,
        difficulty: formData.difficulty,
        quantity: formData.quantity,
        exerciseTypes: formData.selectedTypes,
        formats: formData.selectedFormats,
        interactiveFeatures: formData.interactiveFeatures,
        gamification: formData.gamification,
        includeAnswers: formData.includeAnswers,
        includeInstructions: formData.includeInstructions,
        adaptiveDifficulty: formData.adaptiveDifficulty,
        individualGroup: formData.individual_group,
        onlineOffline: formData.online_offline,
        with_points: true // Используем флаг with_points для генерации за баллы
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `API Error: ${response.status}`)
    }

    const data = await response.json()
    // Use processed_content if exercises doesn't exist
    const rawExercises = data.exercises || data.data?.processed_content || []
    generatedContent.value = normalizeExercises(rawExercises)

    // Обновляем данные пользователя, чтобы отобразить актуальное количество баллов
    try {
      await store.fetchCurrentUser()
      console.log('Количество баллов после генерации:', store.user?.points)
    } catch (userError) {
      console.error('Ошибка при обновлении данных пользователя:', userError)
    }
  } catch (err) {
    store.setError(err instanceof Error ? err.message : 'Error generating exercises with points')
    console.error(err)
  } finally {
    isGenerating.value = false
  }
}

const regenerateExercise = async (index: number) => {
  if (!canGenerate.value) return

  isGenerating.value = true
  store.clearError() // Clear error through store

  try {
    // Track usage for limits and update local counters
    await store.checkAndTrackGeneration(ContentType.EXERCISE);

    const exerciseId = generatedContent.value[index].id

    // Вызов API для регенерации конкретного упражнения
    const response = await fetch(`/api/exercises/regenerate/${exerciseId}`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(), // Добавляем заголовок авторизации
      },
      body: JSON.stringify({
        language: formData.language,
        proficiency: formData.proficiency,
        topic: formData.topic,
        type: generatedContent.value[index].type,
        includeAnswers: formData.includeAnswers,
        includeInstructions: formData.includeInstructions
      })
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()

    // Обновляем только одно упражнение
    const rawExercise = data.exercise || (data.data?.processed_content ? data.data.processed_content[0] : null)
    if (rawExercise) {
      const normalizedExercise = normalizeExercises([rawExercise])[0]
      generatedContent.value.splice(index, 1, normalizedExercise)
    }

    // Local counters are already updated in checkAndTrackGeneration()
  } catch (err) {
    store.setError('Error regenerating exercise') // Set error through store
    console.error(err)
  } finally {
    isGenerating.value = false
  }
}

const regenerateExerciseWithPoints = async (index: number) => {
  // Проверяем, достаточно ли баллов
  const userPoints = await getUserPoints()
  const requiredPoints = 8
  const canGenerate = userPoints >= requiredPoints

  if (!canGenerate) {
    store.setError(`Недостаточно баллов для регенерации упражнения. Требуется ${requiredPoints} баллов.`)
    return
  }

  isGenerating.value = true
  store.clearError() // Clear error through store

  try {
    // Получаем текущее количество баллов пользователя перед генерацией
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед регенерацией:', initialPoints)

    const exerciseId = generatedContent.value[index].id

    // Проверяем возможность генерации за баллы через store
    const canGenerateWithPoints = await store.checkAndTrackGenerationWithPoints(ContentType.EXERCISE, requiredPoints)
    if (!canGenerateWithPoints) {
      throw new Error(`Недостаточно баллов для регенерации упражнения. Требуется ${requiredPoints} баллов.`)
    }

    // Вызов API для регенерации конкретного упражнения за баллы
    const response = await fetch(`/api/exercises/regenerate/${exerciseId}`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(), // Добавляем заголовок авторизации
      },
      body: JSON.stringify({
        language: formData.language,
        proficiency: formData.proficiency,
        topic: formData.topic,
        type: generatedContent.value[index].type,
        includeAnswers: formData.includeAnswers,
        includeInstructions: formData.includeInstructions,
        with_points: true // Используем флаг with_points для генерации за баллы
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `API Error: ${response.status}`)
    }

    const data = await response.json()

    // Обновляем только одно упражнение
    const rawExercise = data.exercise || (data.data?.processed_content ? data.data.processed_content[0] : null)
    if (rawExercise) {
      const normalizedExercise = normalizeExercises([rawExercise])[0]
      generatedContent.value.splice(index, 1, normalizedExercise)
    }

    // Обновляем данные пользователя, чтобы отобразить актуальное количество баллов
    try {
      await store.fetchCurrentUser()
      console.log('Количество баллов после регенерации:', store.user?.points)
    } catch (userError) {
      console.error('Ошибка при обновлении данных пользователя:', userError)
    }

  } catch (err) {
    store.setError(err instanceof Error ? err.message : 'Error regenerating exercise with points')
    console.error(err)
  } finally {
    isGenerating.value = false
  }
}

const regenerateAll = async () => {
  if (!canGenerate.value) return

  isGenerating.value = true
  store.clearError() // Clear error through store

  try {
    // Track usage for limits and update local counters
    await store.checkAndTrackGeneration(ContentType.EXERCISE);

    // Вызов API для регенерации всех упражнений
    const response = await fetch('/api/exercises/regenerate-all', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(), // Добавляем заголовок авторизации
      },
      body: JSON.stringify({
        language: formData.language,
        proficiency: formData.proficiency,
        topic: formData.topic,
        exerciseTypes: formData.selectedTypes,
        quantity: formData.quantity,
        includeAnswers: formData.includeAnswers,
        includeInstructions: formData.includeInstructions
      })
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }

    const data = await response.json()
    // Use processed_content if exercises doesn't exist
    const rawExercises = data.exercises || data.data?.processed_content || []
    generatedContent.value = normalizeExercises(rawExercises)

    // Local counters are already updated in checkAndTrackGeneration()
  } catch (err) {
    store.setError('Error regenerating all exercises') // Set error through store
    console.error(err)
  } finally {
    isGenerating.value = false
  }
}

const regenerateAllWithPoints = async () => {
  // Проверяем, достаточно ли баллов
  const userPoints = await getUserPoints()
  const requiredPoints = 8
  const canGenerate = userPoints >= requiredPoints

  if (!canGenerate) {
    store.setError(`Недостаточно баллов для регенерации упражнений. Требуется ${requiredPoints} баллов.`)
    return
  }

  isGenerating.value = true
  store.clearError() // Clear error through store

  try {
    // Получаем текущее количество баллов пользователя перед генерацией
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед регенерацией всех упражнений:', initialPoints)

    // Проверяем возможность генерации за баллы через store
    const canGenerateWithPoints = await store.checkAndTrackGenerationWithPoints(ContentType.EXERCISE, requiredPoints)
    if (!canGenerateWithPoints) {
      throw new Error(`Недостаточно баллов для регенерации упражнений. Требуется ${requiredPoints} баллов.`)
    }

    // Вызов API для регенерации всех упражнений за баллы
    const response = await fetch('/api/exercises/regenerate-all', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(), // Добавляем заголовок авторизации
      },
      body: JSON.stringify({
        language: formData.language,
        proficiency: formData.proficiency,
        topic: formData.topic,
        exerciseTypes: formData.selectedTypes,
        quantity: formData.quantity,
        includeAnswers: formData.includeAnswers,
        includeInstructions: formData.includeInstructions,
        with_points: true // Используем флаг with_points для генерации за баллы
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `API Error: ${response.status}`)
    }

    const data = await response.json()
    // Use processed_content if exercises doesn't exist
    const rawExercises = data.exercises || data.data?.processed_content || []
    generatedContent.value = normalizeExercises(rawExercises)

    // Обновляем данные пользователя, чтобы отобразить актуальное количество баллов
    try {
      await store.fetchCurrentUser()
      console.log('Количество баллов после регенерации всех упражнений:', store.user?.points)
    } catch (userError) {
      console.error('Ошибка при обновлении данных пользователя:', userError)
    }

  } catch (err) {
    store.setError(err instanceof Error ? err.message : 'Ошибка при регенерации упражнений за баллы')
    console.error(err)
  } finally {
    isGenerating.value = false
  }
}

const copyExercise = (index: number) => {
  const exercise = generatedContent.value[index]
  const content = [
    exercise.content,
    exercise.answers ? `\n\n### Ответы\n${exercise.answers}` : '',
    exercise.instructions ? `\n\n### Инструкции для учителя\n${exercise.instructions}` : ''
  ].join('')

  navigator.clipboard.writeText(content)
    .then(() => {
      // Можно добавить уведомление об успешном копировании
    })
    .catch(err => {
      console.error('Ошибка при копировании в буфер обмена:', err)
    })
}

const copyAllExercises = () => {
  const content = generatedContent.value.map((exercise, i) => {
    return [
      `\n\n## Упражнение ${i + 1}\n`,
      exercise.content,
      exercise.answers ? `\n\n### Ответы\n${exercise.answers}` : '',
      exercise.instructions ? `\n\n### Инструкции для учителя\n${exercise.instructions}` : ''
    ].join('')
  }).join('\n\n---\n')

  navigator.clipboard.writeText(content)
    .then(() => {
      // Можно добавить уведомление об успешном копировании
    })
    .catch(err => {
      console.error('Ошибка при копировании в буфер обмена:', err)
    })
}

// Жизненный цикл
onMounted(() => {
  isMounted.value = true
  window.addEventListener('resize', updateWindowWidth)
  updateWindowWidth()
  window.scrollTo(0, 0)

  // Сохраняем стили компонента Exercises после монтирования
  setTimeout(() => {
    if (typeof window.saveComponentStyles === 'function') {
      const exercisesSelectors = [
        '.exercises-container',
        '.exercises-content',
        '.exercises-form',
        '.exercises-background',
        '.exercises-content-wrapper',
        '.exercises-title-container',
        '.exercises-form-group',
        '.exercises-settings',
        '.exercises-result-container',
        '.exercises-result-content',
        '.exercises-lesson-plan-container',
        '.exercises-planet-background',
        '.exercise-card',
        '.exercise-content',
        '.answer-content',
        '.instruction-content',
        '.generation-results',
        '.theme-selection',
        '.creative-elements',
        '.exercise-settings',
        '.additional-options',
        '.format-options'
      ];

      window.saveComponentStyles('exercises', exercisesSelectors);
      console.log('Стили компонента Exercises сохранены');
    }
  }, 500); // Задержка для полного рендеринга компонента
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWindowWidth)
})
</script>

<style scoped>
.exercises-lesson-plan-container {
  width: 100%;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  padding: 2rem;
  /* background: #1c0522 url('@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg'); */ /* Фон удален, используется глобальный */
  /* background-size: cover; */
  /* background-position: center; */
  /* background-repeat: no-repeat; */
}

.exercises-planet-background {
  position: absolute;
  top: -25px;
  left: 0;
  width: 100%;
  height: 360px;
  z-index: 2;
  pointer-events: none;
}

.exercises-content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding-top: 160px;
  position: relative;
  z-index: 1;
}

.exercises-content {
  position: relative;
  z-index: 1;
}

.exercises-title-form-group {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.75rem 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  text-align: center;
}

.exercises-title {
  color: white;
  font-size: 2.2rem;
  margin: 0;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.9;
}

.exercises-form-group {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.exercises-form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.exercises-remaining-text {
  color: #ccc;
  text-align: center;
  font-size: 0.9rem;
}

.exercises-form-input,
.exercises-form-select {
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

.exercises-form-input:focus,
.exercises-form-select:focus {
  box-shadow: 0 0 0 3px rgba(255, 103, 231, 0.4), inset 0 2px 6px rgba(0, 0, 0, 0.1);
  outline: none;
}

.exercises-theme-selection,
.exercises-creative-elements,
.exercises-settings-section,
.exercises-format-options {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.exercises-section-title {
  color: white;
  font-size: 1.3rem;
  margin-bottom: 1rem;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.exercises-subtitle {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.exercises-themes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}

.exercises-theme-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.exercises-theme-icon {
  font-size: 1.5rem;
}

.exercises-theme-button:hover:not(.exercises-active-theme) {
  background-color: rgba(255, 103, 231, 0.5);
  transform: translateY(-2px);
}

.exercises-active-theme {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
  transform: scale(1.05);
}

.exercises-exercise-types,
.exercises-formats-section,
.exercises-features-section,
.exercises-gamification-section {
  margin-bottom: 1.5rem;
}

.exercises-types-grid,
.exercises-formats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}

.exercises-type-label,
.exercises-format-label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-type-label:hover,
.exercises-format-label:hover {
  background-color: rgba(255, 103, 231, 0.5);
  transform: translateY(-2px);
}

.exercises-type-content,
.exercises-format-content {
  display: flex;
  flex-direction: column;
}

.exercises-type-icon,
.exercises-format-icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.exercises-type-title,
.exercises-format-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.exercises-type-description,
.exercises-format-description {
  font-size: 0.85rem;
  opacity: 0.8;
}

.exercises-checkbox {
  margin-right: 0.5rem;
}

.exercises-features-buttons,
.exercises-gamification-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.exercises-feature-button,
.exercises-gamification-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-feature-button:hover:not(.exercises-active-feature),
.exercises-gamification-button:hover:not(.exercises-active-gamification) {
  background-color: rgba(255, 103, 231, 0.5);
}

.exercises-active-feature,
.exercises-active-gamification {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

.exercises-settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.exercises-difficulty-group,
.exercises-quantity-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.exercises-difficulty-group label,
.exercises-quantity-group label {
  color: white;
  font-weight: 500;
}

.exercises-difficulty-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.exercises-difficulty-btn {
  padding: 0.75rem 0.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-difficulty-btn:hover:not(.exercises-active-difficulty) {
  background-color: rgba(255, 103, 231, 0.5);
}

.exercises-active-difficulty {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

.exercises-quantity-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 1rem;
  padding: 0.5rem;
}

.exercises-quantity-btn {
  width: 2.5rem;
  height: 2.5rem;
  background-color: rgba(255, 103, 231, 0.7);
  border: none;
  border-radius: 0.75rem;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.exercises-quantity-btn:hover:not(:disabled) {
  background-color: #ff67e7;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

.exercises-quantity-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.exercises-quantity-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

.exercises-format-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.exercises-type-group,
.exercises-mode-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.exercises-type-buttons,
.exercises-mode-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.exercises-type-btn,
.exercises-mode-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.exercises-type-btn:hover:not(.exercises-active-type),
.exercises-mode-btn:hover:not(.exercises-active-mode) {
  background-color: rgba(255, 103, 231, 0.5);
}

.exercises-active-type,
.exercises-active-mode {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

.exercises-checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}

.exercises-option-checkbox {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border-radius: 1rem;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-option-checkbox:hover {
  background-color: rgba(255, 103, 231, 0.5);
}

.exercises-form-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 1rem;
  padding: 1rem;
}

/* Контейнер для вертикального расположения кнопок */
.exercises-buttons-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 1.75rem; /* Увеличиваем расстояние между кнопками */
}

.exercises-generate-button {
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

.exercises-generate-button:hover:not(:disabled) {
  background-color: #ff67e7;
  box-shadow: 0 6px 18px rgba(255, 103, 231, 0.6);
  transform: translateY(-2px);
}

.exercises-generate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Стили для кнопки генерации за баллы */
.exercises-points-generate-button {
  background-color: #1e88e5; /* Голубой цвет для кнопки генерации за баллы */
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5);
}

.exercises-points-generate-button:hover:not(:disabled) {
  background-color: #42a5f5; /* Более светлый голубой при наведении */
  box-shadow: 0 6px 18px rgba(30, 136, 229, 0.6);
  transform: translateY(-2px);
}

.exercises-points-icon {
  margin-right: 0.5rem;
  display: inline-block;
  font-size: 1.2rem;
}

.exercises-loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: exercises-spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
}

@keyframes exercises-spin {
  to {
    transform: rotate(360deg);
  }
}

.exercises-error-message {
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: rgba(220, 53, 69, 0.2);
  border-left: 4px solid #dc3545;
  border-radius: 0 0.5rem 0.5rem 0;
  color: white;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.2);
}

.exercises-generation-results {
  margin-top: 2.5rem;
}

.exercises-results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.exercises-results-title {
  color: white;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.exercises-results-actions {
  display: flex;
  gap: 0.75rem;
}

.exercises-regenerate-btn,
.exercises-copy-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-regenerate-btn {
  background-color: #8b5cf6;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
}

.exercises-regenerate-btn:hover:not(:disabled) {
  background-color: #9f71fb;
  box-shadow: 0 6px 18px rgba(139, 92, 246, 0.6);
  transform: translateY(-2px);
}

.exercises-regenerate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.exercises-points-regenerate-btn {
  background-color: rgba(30, 136, 229, 0.7);
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
}

/* Стили для отображения баллов */
.exercises-points-display {
  margin: 1rem 0;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 0.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.exercises-points-details {
  width: 100%;
}

.exercises-points-summary {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  color: white;
  font-weight: 500;
  transition: all 0.3s;
}

.exercises-points-summary:hover {
  background-color: rgba(255, 103, 231, 0.1);
  border-radius: 0.5rem;
}

.exercises-points-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.exercises-points-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

.exercises-points-info {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.exercises-points-description {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.exercises-points-regenerate-btn:hover:not(:disabled) {
  background-color: #42a5f5;
  box-shadow: 0 6px 16px rgba(30, 136, 229, 0.5);
}

.exercises-copy-btn {
  background-color: #6a1b9a;
  color: white;
  box-shadow: 0 4px 12px rgba(106, 27, 154, 0.4);
}

.exercises-copy-btn:hover {
  background-color: #8e24aa;
  box-shadow: 0 6px 16px rgba(142, 36, 170, 0.5);
  transform: translateY(-2px);
}

.exercises-cards-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

.exercises-card {
  background: linear-gradient(135deg, rgba(88, 28, 135, 0.4), rgba(139, 92, 246, 0.2));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(139, 92, 246, 0.3);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.exercises-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(139, 92, 246, 0.4);
}

.exercises-card::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.3;
  z-index: -1;
  pointer-events: none;
}

.exercises-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
}

.exercises-card-title h4 {
  color: white;
  font-size: 1.25rem;
  margin: 0 0 0.25rem 0;
  font-weight: 600;
}

.exercises-card-type {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.exercises-card-actions {
  display: flex;
  gap: 0.5rem;
}

.exercises-action-btn {
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-action-btn:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.exercises-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.exercises-points-action-btn {
  background-color: rgba(30, 136, 229, 0.3);
}

.exercises-points-action-btn:hover:not(:disabled) {
  background-color: rgba(30, 136, 229, 0.5);
}

.exercises-card-content {
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(236, 64, 122, 0.3);
  margin-bottom: 1.25rem;
}

.exercises-answers-section,
.exercises-instructions-section {
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(236, 64, 122, 0.3);
  margin-top: 1.25rem;
}

.exercises-section-label {
  font-size: 1rem;
  font-weight: 600;
  color: #6a1b9a;
  margin-top: 0;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(106, 27, 154, 0.2);
}

.exercises-markdown {
  color: #333;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .exercises-content-wrapper {
    padding-top: 120px;
  }

  .exercises-planet-background {
    top: -40px;
    height: 300px;
  }

  .exercises-title {
    font-size: 1.8rem;
  }

  .exercises-settings-grid,
  .exercises-format-grid {
    grid-template-columns: 1fr;
  }

  .exercises-themes-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }

  .exercises-types-grid,
  .exercises-formats-grid,
  .exercises-checkbox-group {
    grid-template-columns: 1fr;
  }

  .exercises-features-buttons,
  .exercises-gamification-buttons {
    flex-direction: column;
  }

  .exercises-results-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .exercises-results-actions {
    justify-content: space-between;
  }
}
</style>
