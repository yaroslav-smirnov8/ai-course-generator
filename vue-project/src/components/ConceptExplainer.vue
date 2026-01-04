<template>
  <div
    ref="rootContainer"
    class="concept-explainer-container"
  >
    <!-- Заголовок отдельно -->
    <div class="title-container">
      <h2>Language Concept Explanation</h2>
    </div>

    <!-- Основной контент: форма и результат -->
    <div class="content">
      <form class="generation-form" @submit.prevent>
        <div class="form-group">
          <label for="language">Explanation Language</label>
          <select id="language" v-model="formData.language" class="form-select" required>
            <option value="" disabled>Select language</option>
            <option value="english">English</option>
            <option value="russian">Russian</option>
            <option value="spanish">Spanish</option>
            <option value="french">French</option>
            <option value="german">German</option>
            <option value="italian">Italian</option>
            <option value="chinese">Chinese</option>
            <option value="japanese">Japanese</option>
            <option value="korean">Korean</option>
            <option value="arabic">Arabic</option>
          </select>
        </div>

        <div class="form-group">
          <label for="concept">Which language concept needs explanation?</label>
          <textarea
            id="concept"
            v-model="formData.concept"
            class="form-textarea"
            placeholder="Describe the language concept to explain (e.g., Present Perfect, conditional sentences, articles, phrasal verbs, English tenses)"
            required
          ></textarea>
        </div>

        <div class="form-group">
          <label>Student Age</label>
          <div class="age-buttons">
            <button
              type="button"
              v-for="age in ageOptions"
              :key="age.value"
              :class="['age-btn', { active: formData.age === age.value }]"
              @click="formData.age = age.value"
            >
              {{ age.label }}
            </button>
          </div>
        </div>

        <div class="form-group" v-if="availableLevels.length > 0">
          <label for="level">Student Level</label>
          <select id="level" v-model="formData.level" class="form-select">
            <option value="" disabled>Select level</option>
            <option v-for="level in availableLevels" :key="level.value" :value="level.value">
              {{ level.label }}
            </option>
          </select>
          <div v-if="selectedLevelDescription" class="level-description">
            {{ selectedLevelDescription }}
          </div>
        </div>

        <div class="form-group">
          <label for="interests">Student Interests (optional)</label>
          <textarea
            id="interests"
            v-model="formData.interests"
            class="form-textarea"
            placeholder="Specify student interests for more relevant examples (e.g., IT, travel, sports, movies, music)"
          ></textarea>
        </div>

        <div class="form-group">
          <label for="style">Explanation Style</label>
          <select id="style" v-model="formData.style" class="form-select">
            <option value="" disabled>Select style</option>
            <option v-for="style in explanationStyles" :key="style.value" :value="style.value">
              {{ style.label }}
            </option>
          </select>
          <div v-if="selectedStyleDescription" class="style-description">
            {{ selectedStyleDescription }}
          </div>
        </div>

        <div class="form-actions">
          <div class="generation-info">
            <div class="generation-counter" v-if="hasTariff && !isUnlimited">
              <span>{{ remainingGenerations }}/{{ generationsLimit }} generations</span>
            </div>

            <!-- Display points balance in form -->
            <div class="points-balance-display">
              <span class="points-icon">💎</span>
              <span class="points-value">{{ userPoints }} points</span>
            </div>
          </div>

          <div class="buttons-container">
            <button
              type="submit"
              @click.prevent="generateExplanation"
              class="generate-button"
              :disabled="isLoading || !isFormValid || !hasTariff"
            >
              <span v-if="isLoading" class="loading-spinner"></span>
              <template v-if="!hasTariff">
                No active plan
              </template>
              <template v-else-if="isLoading">
                Generating explanation...
              </template>
              <template v-else>
                Explain Concept
              </template>
            </button>

            <button
              type="button"
              @click="generateExplanationWithPoints"
              :disabled="isLoading || !isFormValid || userPoints < 8"
              class="generate-button points-generate-button"
            >
              <span v-if="isLoading" class="loading-spinner"></span>
              <template v-if="isLoading">
                Generating with points...
              </template>
              <template v-else-if="userPoints < 8">
                Not enough points
              </template>
              <template v-else>
                <span class="points-icon">💎</span> Explain for 8 Points
              </template>
            </button>
          </div>
        </div>
      </form>

      <div v-if="isLoading" class="loading-container">
        <div class="loading-animation">
          <div class="concept-loader-large"></div>
          <p class="loading-text">Creating explanation suitable for the student...</p>
          <p class="loading-subtext">This may take a few seconds</p>
        </div>
      </div>

      <div v-if="error" class="error">
        <button class="error-close" @click="clearError">×</button>
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
      </div>

      <div v-if="explanation" class="result">
        <h3>Concept Explanation</h3>
        <div class="result-actions">
          <button
            class="action-button regenerate"
            @click="regenerate"
            :disabled="!hasTariff"
          >
            <span class="icon">🔄</span> Regenerate
          </button>
          <button
            class="action-button regenerate-points"
            @click="generateExplanationWithPoints"
            :disabled="isLoading"
          >
            <span class="icon">💎</span> Refresh for 8 Points
          </button>
          <button class="action-button copy" @click="copyExplanation">
            <span class="icon">📋</span> Copy
          </button>
        </div>

        <!-- Отображение баллов пользователя -->
        <div class="concept-points-display">
          <details class="concept-points-details">
            <summary class="concept-points-summary">
              <span class="concept-points-icon">💎</span> Points Balance
            </summary>
            <div class="concept-points-content">
              <p class="concept-points-info">
                Your current balance: <strong>{{ userPoints }}</strong> points
              </p>
              <p class="concept-points-description">
                Use points to generate without daily plan limits.
                Each generation costs 8 points.
              </p>
            </div>
          </details>
        </div>

        <div class="explanation-content">
          <MarkdownRenderer :content="explanation" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useMainStore } from '@/store'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import { ContentType, ActionType, UNLIMITED_ROLES } from '@/core/constants'
import { apiClient } from '@/api/client'
import { API_ENDPOINTS } from '@/api/endpoints'

// Выводим доступные эндпоинты для отладки
console.log('Available API endpoints:', API_ENDPOINTS)
console.log('Concept explanation endpoint:', API_ENDPOINTS.GENERATE_CONCEPT_EXPLANATION)

const store = useMainStore()

interface AgeOption {
  value: string
  label: string
}

interface LevelOption {
  value: string
  label: string
  description: string
  languages: string[]
}

interface StyleOption {
  value: string
  label: string
  description: string
}

const ageOptions: AgeOption[] = [
  { value: 'children', label: '6-9 years' },
  { value: 'preteens', label: '10-12 years' },
  { value: 'teens', label: '13-17 years' },
  { value: 'adults', label: '18+ years' }
]

const levelOptions: LevelOption[] = [
  {
    value: 'beginner',
    label: 'A1-A2 (Beginner)',
    description: 'Student just starts learning the language, knows basic words and simple phrases.',
    languages: ['english', 'russian', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese', 'korean', 'arabic']
  },
  {
    value: 'elementary',
    label: 'B1 (Elementary)',
    description: 'Student understands basic grammar, can communicate on familiar topics.',
    languages: ['english', 'russian', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese', 'korean', 'arabic']
  },
  {
    value: 'intermediate',
    label: 'B2 (Upper Intermediate)',
    description: 'Student confidently uses the language, understands complex texts and abstract topics.',
    languages: ['english', 'russian', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese', 'korean', 'arabic']
  },
  {
    value: 'advanced',
    label: 'C1-C2 (Advanced)',
    description: 'Student fluently speaks the language, ready to study nuances and subtleties.',
    languages: ['english', 'russian', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese', 'korean', 'arabic']
  }
]

const explanationStyles: StyleOption[] = [
  {
    value: 'simple',
    label: 'Simple Explanation',
    description: 'Basic explanation using simple words and clear examples.'
  },
  {
    value: 'creative',
    label: 'Creative',
    description: 'Using stories, metaphors and creative approaches for memorizing rules.'
  },
  {
    value: 'analogy',
    label: 'Through Analogies',
    description: 'Explaining grammar by comparing with native language or familiar concepts.'
  },
  {
    value: 'visual',
    label: 'Visual',
    description: 'Explanation using diagrams, tables and visual examples.'
  },
  {
    value: 'humorous',
    label: 'Humorous',
    description: 'Explanation using humor and funny examples for better memorization.'
  },
  {
    value: 'practical',
    label: 'Practical',
    description: 'Focus on practical application with many real examples and exercises.'
  }
]

const formData = ref({
  language: '',
  concept: '',
  age: '',
  level: '',
  interests: '',
  style: ''
})

const isLoading = ref(false)
const error = ref('')
const explanation = ref('')

const rootContainer = ref<HTMLElement | null>(null)
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)

// Обновление ширины окна
const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}



const availableLevels = computed(() => {
  if (!formData.value.language) return []
  return levelOptions.filter(level => level.languages.includes(formData.value.language))
})

const selectedLevelDescription = computed(() => {
  const level = levelOptions.find(l => l.value === formData.value.level)
  return level ? level.description : ''
})

const selectedStyleDescription = computed(() => {
  const style = explanationStyles.find(s => s.value === formData.value.style)
  return style ? style.description : ''
})

// Генерация и лимиты
const isUnlimited = computed(() => {
  return store.user && UNLIMITED_ROLES.includes(store.user.role)
})

const hasTariff = computed(() => {
  // Проверяем, является ли пользователь неограниченным
  if (isUnlimited.value) return true

  // Проверяем наличие тарифа у пользователя
  if (store.user && store.user.tariff) return true

  // Проверяем информацию о тарифе, если она доступна
  if (store.tariffInfo && store.tariffInfo.type !== 'free') return true

  // По умолчанию считаем, что тарифа нет
  return false
})

// Проверка наличия баллов для генерации
const hasEnoughPoints = computed(() => {
  // Проверяем, есть ли у пользователя достаточно баллов для генерации
  const userPoints = store.user?.points || 0
  console.log(`[hasEnoughPoints] User points: ${userPoints}, required: 8, result: ${userPoints >= 8}`)
  console.log('User object:', store.user)

  // Добавляем дополнительную проверку для отладки
  if (userPoints >= 8) {
    console.log('User has enough points for generation!')
  } else {
    console.log('User does NOT have enough points for generation')
  }

  // Всегда возвращаем true, если у пользователя 8 или больше баллов
  return userPoints >= 8
})

const canGenerate = computed(() => store.canGenerate(ContentType.TEXT_ANALYSIS))
const remainingGenerations = computed(() => store.remainingGenerations(ContentType.TEXT_ANALYSIS))
const generationsLimit = computed(() => {
  if (store.tariffInfo && store.tariffInfo.limits) {
    return store.tariffInfo.limits.generations
  }
  return 0
})
const userPoints = computed(() => store.user?.points || 0)



const isFormValid = computed(() => {
  return formData.value.language &&
         formData.value.concept &&
         formData.value.age &&
         formData.value.level &&
         formData.value.style
})

async function generateExplanation() {
  if (!isFormValid.value) return

  isLoading.value = true
  error.value = ''

  try {
    // Отслеживаем использование для лимитов и обновляем локальные счетчики
    try {
      await store.checkAndTrackGeneration(ContentType.TEXT_ANALYSIS);
    } catch (limitError: any) {
      console.error('Ошибка при проверке лимитов:', limitError);
      // Если ошибка связана с отсутствием тарифа, предлагаем использовать баллы
      if (limitError.message && (
          limitError.message.includes('No active tariff') ||
          limitError.message.includes('Нет активного тарифа') ||
          limitError.message.includes('403')
        )) {
        if (store.user && store.user.points >= 8) {
          if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации объяснения?')) {
            await generateExplanationWithPoints();
            return;
          } else {
            error.value = 'Для генерации необходимо приобрести тариф или использовать баллы.';
            return;
          }
        } else {
          error.value = 'У вас нет активного тарифа. Для генерации необходимо приобрести тариф или пополнить баллы.';
          return;
        }
      }
      throw limitError;
    }

    const result = await store.generateConceptExplanation({
      language: formData.value.language,
      concept: formData.value.concept,
      age: formData.value.age,
      level: formData.value.level,
      interests: formData.value.interests,
      style: formData.value.style
    })

    // Логируем полученный результат для отладки
    console.log('Received explanation result:', result)

    // Проверяем тип результата и обрабатываем соответствующим образом
    if (result === null || result === undefined) {
      explanation.value = "Не удалось получить объяснение. Пожалуйста, попробуйте еще раз."
    } else if (typeof result === 'string') {
      explanation.value = result
    } else if (typeof result === 'object') {
      // Если объект имеет свойство content, используем его
      if (result.content && typeof result.content === 'string') {
        explanation.value = result.content
      }
      // Проверяем вложенную структуру data.content
      else if (result.data && result.data.content && typeof result.data.content === 'string') {
        explanation.value = result.data.content
      }
      // В качестве запасного варианта преобразуем объект в строку JSON
      else {
        console.warn('Unexpected result format:', result)
        explanation.value = JSON.stringify(result, null, 2)
      }
    } else {
      // Для любых других типов преобразуем в строку
      explanation.value = String(result)
    }
  } catch (err: any) {
    error.value = err.message || 'Произошла ошибка при генерации объяснения'
    console.error('Error generating explanation:', err)
  } finally {
    isLoading.value = false
  }
}

// Генерация объяснения за баллы
async function generateExplanationWithPoints() {
  if (!isFormValid.value) return

  isLoading.value = true
  error.value = '' // Очищаем ошибки, включая сообщения о тарифе

  try {
    console.log('Начинаем генерацию объяснения за баллы')

    // Логируем текущее количество баллов пользователя перед генерацией
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед генерацией объяснения:', initialPoints)

    // Используем метод store для проверки и списания баллов
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8);

    if (!canGenerate) {
      throw new Error('Не удалось списать баллы. Возможно, недостаточно баллов на счету.');
    }

    // Подготавливаем данные запроса
    const requestData = {
      user_id: store.user?.id,
      type: ContentType.TEXT_ANALYSIS,
      language: formData.value.language,
      concept: formData.value.concept,
      age: formData.value.age,
      level: formData.value.level,
      interests: formData.value.interests,
      style: formData.value.style,
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    console.log('Отправляем запрос на генерацию объяснения за баллы:', requestData)

    // Отправляем запрос через API
    const response = await apiClient.post(API_ENDPOINTS.GENERATE_CONCEPT_EXPLANATION, requestData)
    console.log('Получен ответ от API:', response)

    // Извлекаем контент из ответа
    let result = null
    if (response.data) {
      if (typeof response.data === 'string') {
        result = response.data
      } else if (response.data.content) {
        result = response.data.content
      } else if (response.data.data && response.data.data.content) {
        result = response.data.data.content
      } else {
        result = JSON.stringify(response.data)
      }
    }

    console.log('Получен результат генерации:', result)

    // Проверка и обработка ответа
    if (result === null || result === undefined) {
      throw new Error('Получен пустой ответ от сервера')
    }

    explanation.value = result
    console.log('Объяснение успешно сгенерировано за баллы')

    // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
    await store.fetchCurrentUser()

    // Логируем количество баллов после генерации
    console.log('Количество баллов после генерации объяснения:', store.user?.points)

    // Отслеживаем достижение
    try {
      await store.checkAchievements(ActionType.GENERATION, {
        content_type: ContentType.TEXT_ANALYSIS,
        language: formData.value.language,
        concept: formData.value.concept,
        with_points: true
      })
    } catch (achievementError) {
      console.warn('Ошибка при проверке достижений:', achievementError)
      // Продолжаем выполнение, даже если проверка достижений не удалась
    }
  } catch (err: any) {
    console.error('Error generating explanation with points:', err)
    error.value = err.message || 'Произошла ошибка при генерации объяснения за баллы'
  } finally {
    isLoading.value = false
  }
}

function regenerate() {
  // Проверяем наличие активного тарифа
  if (!hasTariff.value) {
    // Проверяем, есть ли у пользователя достаточно баллов (прямая проверка)
    const userPoints = store.user?.points || 0
    if (userPoints >= 8) {
      // Спрашиваем пользователя, хочет ли он использовать баллы
      if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации нового объяснения?')) {
        generateExplanationWithPoints()
        return
      }
    } else {
      error.value = 'У вас нет активного тарифа. Для генерации необходимо приобрести тариф или пополнить баллы.'
      return
    }
  }

  generateExplanation()
}

function clearError() {
  error.value = ''
}

async function copyExplanation() {
  if (!explanation.value) return

  try {
    await navigator.clipboard.writeText(explanation.value)
    alert('Объяснение скопировано в буфер обмена')
  } catch (err) {
    console.error('Failed to copy:', err)
    alert('Не удалось скопировать текст')
  }
}

watch(() => formData.value.language, (newLanguage) => {
  const levelExists = availableLevels.value.some(level => level.value === formData.value.level)
  if (!levelExists) {
    formData.value.level = ''
  }
})

// Функция для очистки ошибок
const clearAllErrors = () => {
  error.value = ''
}

// Следим за изменением статуса тарифа
watch(() => store.tariffInfo, () => {
  // Обновляем UI при изменении тарифа
  if (!isLoading.value) {
    console.log('Tariff info changed:', store.tariffInfo)
  }
}, { immediate: true })

// Функция для загрузки данных пользователя
async function loadUserData() {
  try {
    // Принудительно загружаем данные пользователя с сервера
    await store.fetchCurrentUser()
    console.log('User data loaded:', store.user)

    // Проверяем наличие баллов для генерации
    if (store.user && store.user.points >= 8) {
      console.log('User has enough points for points-based generation:', store.user.points)
    }

    // Дополнительная проверка для отладки
    console.log('Current user points:', store.user?.points)
    console.log('hasEnoughPoints computed value:', hasEnoughPoints.value)

    // Принудительно обновляем вычисляемые свойства
    setTimeout(() => {
      console.log('After timeout - hasEnoughPoints:', hasEnoughPoints.value)
    }, 500)
  } catch (error) {
    console.error('Error loading user data:', error)
  }
}

// Жизненный цикл
onMounted(async () => {
  // Загружаем данные пользователя
  await loadUserData()

  // Повторно загружаем данные пользователя через небольшую задержку
  // для гарантированного получения актуальных данных
  setTimeout(async () => {
    console.log('Reloading user data after timeout...')
    await loadUserData()

    // Проверяем состояние кнопки
    console.log('Button state after reload:')
    console.log('- hasEnoughPoints:', hasEnoughPoints.value)
    console.log('- User points:', store.user?.points)
    console.log('- isFormValid:', isFormValid.value)
    console.log('- isLoading:', isLoading.value)
  }, 1000)

  // Настраиваем UI
  window.addEventListener('resize', updateWindowWidth)
  updateWindowWidth()
  window.scrollTo(0, 0)

  // Добавляем глобальные стили для улучшения прокрутки
  document.documentElement.style.overflowY = 'auto'
  document.documentElement.style.height = 'auto'
  document.body.style.overflowY = 'auto'
  document.body.style.height = 'auto'

  // Убедимся, что мобильные устройства правильно обрабатывают высоту
  if (isMobile.value) {
    document.documentElement.style.minHeight = '100vh'
    document.body.style.minHeight = '100vh'
  }

  // Очищаем все ошибки при загрузке
  clearAllErrors()
})
</script>

<style scoped>
/* Основной контейнер */
.concept-explainer-container {
  width: 100%;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 2rem;
  -webkit-overflow-scrolling: touch;
}

/* Глобальные стили для улучшения прокрутки и взаимодействия */
:deep(html), :deep(body) {
  overflow-y: auto !important;
  height: auto !important;
}

/* Заголовок, отдельный блок */
.title-container {
  position: relative;
  z-index: 10;
  text-align: center;
  margin: 0 auto 2rem auto;
  max-width: 700px;
  background-color: rgba(42, 8, 46, 0.5);
  border-radius: 1.2rem;
  padding: 1.75rem 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(255, 103, 231, 0.3);
  border: 1px solid rgba(255, 103, 231, 0.2);
}

.title-container h2 {
  color: white;
  font-size: 2.2rem;
  margin: 0;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.95;
}

/* Контейнер формы и результата */
.content {
  position: relative;
  z-index: 10;
  max-width: 700px;
  margin: 0 auto;
  padding: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

/* Базовые стили формы */
.generation-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
  width: 100%;
}

/* Группы элементов формы */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background-color: rgba(42, 8, 46, 0.5);
  border-radius: 1.2rem;
  padding: 1.25rem 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(255, 103, 231, 0.25);
  border: 1px solid rgba(255, 103, 231, 0.15);
  transition: all 0.3s ease;
}

.form-group:hover {
  box-shadow: 0 6px 25px rgba(255, 103, 231, 0.35);
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  font-size: 1.05rem;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

/* Инпуты, textarea, select */
.form-select,
.form-textarea {
  width: 100%;
  padding: 0.85rem 1.1rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 204, 243, 0.3);
  background-color: rgba(255, 204, 243, 0.8);
  color: #333;
  font-size: 1rem;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  cursor: pointer;
  touch-action: manipulation;
}

.form-textarea {
  min-height: 120px;
  resize: vertical;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23333' stroke='%23333' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 16px;
  padding-right: 2.5rem;
}

.form-select:focus,
.form-textarea:focus {
  box-shadow: 0 0 0 3px rgba(255, 103, 231, 0.4), inset 0 2px 6px rgba(0, 0, 0, 0.1);
  outline: none;
  border-color: rgba(255, 103, 231, 0.5);
}

/* Кнопки выбора возраста */
.age-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.85rem;
}

.age-btn {
  padding: 0.85rem 1rem;
  border: 1px solid rgba(255, 204, 243, 0.3);
  border-radius: 1.2rem;
  cursor: pointer !important;
  background-color: rgba(255, 204, 243, 0.8);
  color: #333;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s;
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.age-btn:hover {
  background-color: rgba(255, 103, 231, 0.5);
  transform: translateY(-2px);
  color: white;
}

.age-btn:active {
  transform: scale(0.97);
}

.age-btn.active {
  background: linear-gradient(135deg, #ff67e7 0%, #c400ff 100%);
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.4);
  border-color: rgba(255, 255, 255, 0.2);
}

/* Описания стилей и уровней */
.style-description,
.level-description {
  margin-top: 0.75rem;
  padding: 0.875rem 1rem;
  background-color: rgba(255, 255, 255, 0.15);
  border-radius: 0.75rem;
  font-size: 0.95rem;
  color: white;
  line-height: 1.5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Кнопка "Отправить" */
.form-actions {
  background-color: rgba(42, 8, 46, 0.5);
  border-radius: 1.2rem;
  padding: 1.25rem 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(255, 103, 231, 0.25);
  border: 1px solid rgba(255, 103, 231, 0.15);
}

/* Контейнер для кнопок */
.buttons-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 1.75rem; /* Увеличенное расстояние между кнопками */
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

/* Общие стили для кнопок генерации */
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

.generate-button:active:not(:disabled) {
  transform: translateY(1px);
}

.generate-button:disabled {
  background-color: #687284;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* Информация о генерациях */
.generation-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

/* Счетчик генераций */
.generation-counter {
  color: white;
  font-size: 0.9rem;
  background-color: rgba(255, 255, 255, 0.15);
  padding: 0.75rem;
  border-radius: 0.75rem;
  font-weight: 500;
}

/* Отображение баланса баллов в форме */
.points-balance-display {
  color: white;
  font-size: 0.9rem;
  background-color: rgba(255, 103, 231, 0.15);
  padding: 0.75rem;
  border-radius: 0.75rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Кнопка генерации за баллы (синяя) */
.points-generate-button {
  background-color: #1e88e5; /* Голубой цвет для кнопки генерации за баллы */
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5);
  margin-top: 1.75rem; /* Увеличиваем отступ между кнопками */
}

.points-generate-button:hover:not(:disabled) {
  background-color: #42a5f5; /* Более светлый голубой при наведении */
  box-shadow: 0 6px 18px rgba(30, 136, 229, 0.6);
  transform: translateY(-2px);
}

/* Отдельный стиль для отключенной кнопки генерации за баллы */
.points-generate-button:disabled {
  background-color: #687284;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.points-icon {
  margin-right: 0.25rem;
  display: inline-block;
  font-size: 1.2rem;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(255, 235, 59, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(255, 235, 59, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(255, 235, 59, 0);
  }
}

/* Лоадер для кнопок */
.loading-spinner {
  display: inline-block;
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

/* Загрузка */
.loading-container {
  margin: 2rem auto;
  text-align: center;
  width: 100%;
  max-width: 600px;
}

.loading-animation {
  background: linear-gradient(135deg, rgba(88, 28, 135, 0.4), rgba(139, 92, 246, 0.2));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(139, 92, 246, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.5s ease-in-out;
}

.concept-loader-large {
  display: inline-block;
  width: 60px;
  height: 60px;
  border: 5px solid rgba(255, 204, 243, 0.3);
  border-top: 5px solid #ff67e7;
  border-radius: 50%;
  margin: 0 auto 1.5rem;
  animation: spin 1.2s linear infinite;
}

.loading-text {
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.loading-subtext {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Ошибка */
.error {
  margin: 1.5rem 0;
  padding: 1rem 1.25rem;
  background: rgba(198, 40, 40, 0.3);
  backdrop-filter: blur(10px);
  border-radius: 1.2rem;
  color: #ffebee;
  position: relative;
  box-shadow: 0 4px 15px rgba(198, 40, 40, 0.3);
  width: 100%;
  border: 1px solid rgba(198, 40, 40, 0.2);
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.error p {
  margin: 0.5rem 0;
  font-size: 1rem;
  padding-left: 2rem;
}

.error-close {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  color: #ffebee;
  font-size: 1.2rem;
  cursor: pointer !important;
  z-index: 20;
  touch-action: manipulation;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.error-close:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.error-info {
  background: rgba(33, 150, 243, 0.3);
  border: 1px solid rgba(33, 150, 243, 0.3);
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
}

.error-icon {
  position: absolute;
  left: 1rem;
  top: 1rem;
  font-size: 1.2rem;
}

.error-action {
  margin-top: 0.75rem;
  display: flex;
  justify-content: flex-end;
}

.error-action-button {
  background: linear-gradient(135deg, #42a5f5 0%, #1565c0 100%);
  color: white;
  border: none;
  border-radius: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.4);
}

.error-action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.5);
}

.error-action-button:active {
  transform: translateY(0);
}

/* Результат */
.result {
  margin-top: 2rem;
  background-color: rgba(42, 8, 46, 0.5);
  border-radius: 1.2rem;
  padding: 1.75rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(255, 103, 231, 0.25);
  width: 100%;
  border: 1px solid rgba(255, 103, 231, 0.15);
}

.result h3 {
  color: white;
  font-size: 1.6rem;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.result-actions {
  display: flex;
  gap: 1rem;
  margin: 1.5rem 0;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.85rem 1.1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer !important;
  transition: all 0.3s;
  background: linear-gradient(135deg, #ff67e7 0%, #c400ff 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 103, 231, 0.3);
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
  flex: 1;
  letter-spacing: 0.02em;
}

.action-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(255, 103, 231, 0.4);
}

.action-button:active {
  transform: translateY(1px);
}

.icon {
  font-size: 1.2rem;
}

.action-button.regenerate {
  background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);
}

.action-button.regenerate-points {
  background-color: #1e88e5; /* Голубой цвет для кнопки генерации за баллы */
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-button.regenerate-points:hover {
  background-color: #42a5f5; /* Более светлый голубой при наведении */
  box-shadow: 0 6px 18px rgba(30, 136, 229, 0.6);
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* Стили для отображения баллов */
.concept-points-display {
  margin: 1rem 0;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 0.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.concept-points-details {
  width: 100%;
}

.concept-points-summary {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  color: white;
  font-weight: 500;
  transition: all 0.3s;
}

.concept-points-summary:hover {
  background-color: rgba(255, 103, 231, 0.1);
  border-radius: 0.5rem;
}

.concept-points-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.concept-points-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

.concept-points-info {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.concept-points-description {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* Текст сгенерированного ответа */
.explanation-content {
  background: white;
  border-radius: 1rem;
  padding: 1.75rem;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  overflow-y: auto;
  max-height: 60vh;
  -webkit-overflow-scrolling: touch;
  margin-top: 1.25rem;
  border: 1px solid rgba(255, 103, 231, 0.1);
}

/* Адаптивные настройки */
@media (max-width: 768px) {
  .concept-explainer-container {
    padding: 1rem;
    padding-bottom: 4rem;
  }

  .title-container {
    margin-bottom: 1.5rem;
    padding: 1.25rem 1rem;
  }

  .title-container h2 {
    font-size: 1.8rem;
  }

  .age-buttons {
    grid-template-columns: 1fr 1fr;
  }

  .form-group {
    padding: 1.1rem;
  }

  .form-textarea,
  .form-select,
  .submit-btn {
    font-size: 16px; /* Предотвращает масштабирование на iOS */
    padding: 0.875rem;
  }

  .result-actions {
    flex-direction: column;
    width: 100%;
    gap: 0.75rem;
  }

  .action-button {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 0;
  }

  .buttons-container {
    gap: 1rem;
  }

  .explanation-content {
    padding: 1.25rem;
    max-height: 50vh;
  }

  label {
    font-size: 1rem;
  }
}

/* Скроллбары */
.explanation-content::-webkit-scrollbar {
  width: 8px;
}

.explanation-content::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 4px;
}

.explanation-content::-webkit-scrollbar-thumb {
  background: #ff67e7;
  border-radius: 4px;
}

/* Предотвращаем нежелательное выделение текста и улучшаем интерактивность */
.age-btn,
.submit-btn,
.action-button,
button {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
  user-select: none;
}
</style>