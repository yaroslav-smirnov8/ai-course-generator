<template>
  <!-- Проверка доступа к премиум функциям -->
  <PremiumRequired
    v-if="!hasPremiumAccess && isUserLoaded"
    feature-name="AI-ассистент"
  />

  <div
    v-else-if="hasPremiumAccess"
    ref="rootContainer"
    class="ai-assistant-container"
  >
    <!-- Планета сверху -->
    <div class="planet-container">
      <img :src="planetBg" alt="Планета" class="planet-image">
    </div>

    <!-- Заголовок отдельно -->
    <div class="title-container">
      <h2>AI-ассистент для репетиторов</h2>
    </div>

    <!-- Основной контент: форма и результат -->
    <div class="content">
      <form @submit.prevent="sendQuery" class="generation-form">
        <!-- Язык -->
        <div class="form-group">
          <label for="language">Язык ответа:</label>
          <select
            v-model="formData.language"
            id="language"
            required
            class="form-select"
          >
            <option value="" disabled selected>Выберите язык</option>
            <option value="english">Английский (English)</option>
            <option value="spanish">Испанский (Español)</option>
            <option value="french">Французский (Français)</option>
            <option value="german">Немецкий (Deutsch)</option>
            <option value="italian">Итальянский (Italiano)</option>
            <option value="chinese">Китайский (中文)</option>
            <option value="japanese">Японский (日本語)</option>
            <option value="korean">Корейский (한국어)</option>
            <option value="turkish">Турецкий (Türkçe)</option>
            <option value="russian">Русский</option>
            <option value="arabic">Арабский (العربية)</option>
          </select>
        </div>

        <!-- Запрос -->
        <div class="form-group">
          <label for="query">Ваш запрос:</label>
          <textarea
            v-model="formData.query"
            id="query"
            required
            class="form-textarea"
            placeholder="Введите ваш запрос к AI-ассистенту"
            rows="5"
          ></textarea>
        </div>

        <!-- Готовые шаблоны запросов -->
        <div class="form-group">
          <label>Готовые шаблоны запросов:</label>
          <div class="templates-grid">
            <button
              v-for="(template, index) in queryTemplates"
              :key="index"
              type="button"
              class="template-btn"
              @click="applyTemplate(template)"
            >
              {{ template.title }}
            </button>
          </div>
        </div>

        <!-- Информация о лимитах генерации -->
        <div class="generation-limits" v-if="!isUnlimited">
          <div class="limits-info">
            <span class="limits-label">Осталось генераций:</span>
            <span class="limits-value" :class="{'limits-warning': remainingGenerations <= 5, 'limits-danger': remainingGenerations <= 2}">
              {{ remainingGenerations }}/{{ generationsLimit }}
            </span>
          </div>
          <div class="tariff-info" v-if="!store.tariffInfo || store.tariffInfo.type === 'free'">
            <span class="tariff-warning">У вас нет активного тарифа. Вы можете использовать генерацию за баллы.</span>
          </div>
        </div>

        <!-- Кнопки отправки -->
        <div class="form-actions">
          <div class="buttons-container">
            <button
              type="submit"
              :disabled="isLoading || !canGenerate || !hasTariff"
              class="submit-btn"
            >
              <span v-if="isLoading" class="loader"></span>
              <template v-if="!hasTariff">
                Нет активного тарифа
              </template>
              <template v-else-if="!canGenerate">
                Лимит генераций исчерпан
              </template>
              <template v-else-if="isLoading">
                Обрабатываем запрос...
              </template>
              <template v-else>
                Отправить запрос
              </template>
            </button>

            <button
              type="button"
              class="submit-btn points-generate-button"
              :class="{'points-generate-button-highlight': !store.tariffInfo || store.tariffInfo.type === 'free'}"
              :disabled="isLoading"
              @click="sendQueryWithPoints"
            >
              <span v-if="isLoading" class="loader"></span>
              <template v-if="isLoading">
                Обрабатываем запрос...
              </template>
              <template v-else>
                <span class="points-icon">💎</span> Отправить за 8 баллов
              </template>
            </button>
          </div>
        </div>
      </form>

      <!-- Состояние загрузки -->
      <div v-if="isLoading" class="loading">
        <div class="loader"></div>
        <p>Обрабатываем ваш запрос...</p>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="clearError" class="error-close">✕</button>
      </div>

      <!-- Сгенерированный ответ -->
      <div v-if="aiResponse" class="result">
        <h3>Ответ AI-ассистента:</h3>
        <div class="result-actions">
          <button @click="copyToClipboard" class="action-button">
            <span class="icon">📋</span>
            Копировать
          </button>
          <button @click="regenerate" class="action-button regenerate">
            <span class="icon">🔄</span>
            Сгенерировать заново
          </button>
        </div>

        <!-- Отображение баллов пользователя -->
        <div class="assistant-points-display">
          <details class="assistant-points-details">
            <summary class="assistant-points-summary">
              <span class="assistant-points-icon">💎</span> Баланс баллов
            </summary>
            <div class="assistant-points-content">
              <p class="assistant-points-info">
                Ваш текущий баланс: <strong>{{ userPoints }}</strong> баллов
              </p>
              <p class="assistant-points-description">
                Используйте баллы для генерации без учета дневных лимитов тарифа.
                Каждая генерация стоит 8 баллов.
              </p>
            </div>
          </details>
        </div>

        <div class="response-content">
          <MarkdownRenderer :content="aiResponse" />
        </div>
      </div>
    </div>
  </div>

  <!-- Загрузочный экран для случаев когда данные пользователя еще не загружены -->
  <div v-else class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
    <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useMainStore, useCourseStore } from '@/store'
import { ContentType, ActionType, UNLIMITED_ROLES } from '@/core/constants'
import MarkdownRenderer from './common/MarkdownRenderer.vue'
import planetBg from '@/assets/images/lesson_plan/plan-backgroud-image.svg'
import { apiClient } from '@/api/client'
import { API_ENDPOINTS } from '@/api/endpoints'
import PremiumRequired from './access/PremiumRequired.vue'
import { usePremiumAccess } from '@/composables/usePremiumAccess'

const store = useMainStore()
const courseStore = useCourseStore()
const { hasPremiumAccess, isUserLoaded } = usePremiumAccess()
const rootContainer = ref<HTMLElement | null>(null)
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)

// Генерация и лимиты
const isUnlimited = computed(() => {
  return store.user && UNLIMITED_ROLES.includes(store.user.role)
})
const hasTariff = computed(() => {
  return isUnlimited.value || (store.tariffInfo && store.tariffInfo.type !== 'free')
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

// Обновление ширины окна
const updateWindowWidth = () => {
  windowWidth.value = window.innerWidth
}

interface QueryTemplate {
  title: string;
  query: string;
}

const queryTemplates: QueryTemplate[] = [
  {
    title: "Методические консультации",
    query: "Как эффективно объяснить сложную грамматическую тему ученику, который постоянно делает одни и те же ошибки? Предложите пошаговую методику с примерами."
  },
  {
    title: "Адаптация под уровень",
    query: "У меня в группе ученики разных уровней (A2-B1). Как адаптировать один урок для всех участников, чтобы никому не было скучно или слишком сложно?"
  },
  {
    title: "Мотивация учеников",
    query: "Ученик потерял мотивацию к изучению языка после нескольких месяцев занятий. Какие техники и подходы помогут вернуть интерес к обучению?"
  },
  {
    title: "Работа с ошибками",
    query: "Создайте систему работы с типичными ошибками учеников: как их выявлять, классифицировать и исправлять без демотивации студента."
  },
  {
    title: "Планирование курса",
    query: "Помогите составить структуру 3-месячного интенсивного курса английского для подготовки к собеседованию в IT-компании. Уровень ученика - B1."
  },
  {
    title: "Оценка прогресса",
    query: "Какие критерии и методы оценки использовать для отслеживания прогресса ученика в разговорной речи? Предложите систему с конкретными показателями."
  },
  {
    title: "Использование технологий",
    query: "Порекомендуйте современные цифровые инструменты и приложения для изучения языка, которые можно интегрировать в традиционные уроки."
  },
  {
    title: "Работа с произношением",
    query: "Ученик из России изучает английский, но у него сильный акцент и проблемы с определенными звуками. Разработайте план коррекции произношения."
  },
  {
    title: "Подготовка к экзаменам",
    query: "Составьте детальный план подготовки к IELTS Speaking для ученика уровня B2, включая типичные ошибки русскоговорящих и способы их избежать."
  },
  {
    title: "Культурный контекст",
    query: "Как интегрировать изучение культурных особенностей в языковые уроки? Предложите практические активности для понимания менталитета носителей языка."
  }
]

const formData = ref({
  language: 'russian',
  query: ''
})

const aiResponse = ref<string | null>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)

const applyTemplate = (template: QueryTemplate) => {
  formData.value.query = template.query
}

const sendQuery = async () => {
  try {
    aiResponse.value = null
    error.value = null
    isLoading.value = true

    // Используем вычисляемое свойство hasTariff

    // Проверяем лимиты генерации
    if (!canGenerate.value && !isUnlimited.value) {
      throw new Error('Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или используйте генерацию за баллы.')
    }

    // Если нет активного тарифа, предлагаем использовать баллы
    if (!hasTariff) {
      console.log('Нет активного тарифа, предлагаем использовать баллы')
      if (store.user && store.user.points >= 8) {
        if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации?')) {
          await sendQueryWithPoints()
          return
        } else {
          throw new Error('Для генерации необходимо приобрести тариф или использовать баллы.')
        }
      } else {
        throw new Error('У вас нет активного тарифа. Для генерации необходимо приобрести тариф или пополнить баллы.')
      }
    }

    const requestData = {
      language: formData.value.language,
      query: formData.value.query
    }

    console.log('Отправляем запрос к AI:', requestData)

    // Отслеживаем использование для лимитов
    try {
      await store.checkAndTrackGeneration(ContentType.TEXT_ANALYSIS)
    } catch (limitError: any) {
      console.error('Ошибка при проверке лимитов:', limitError)
      // Если ошибка связана с отсутствием тарифа, предлагаем использовать баллы
      if (limitError.message && (
          limitError.message.includes('No active tariff') ||
          limitError.message.includes('Нет активного тарифа') ||
          limitError.message.includes('403')
        )) {
        if (store.user && store.user.points >= 8) {
          if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации?')) {
            await sendQueryWithPoints()
            return
          } else {
            throw new Error('Для генерации необходимо приобрести тариф или использовать баллы.')
          }
        } else {
          throw new Error('У вас нет активного тарифа. Для генерации необходимо приобрести тариф или пополнить баллы.')
        }
      }
      throw limitError
    }

    // Отправляем запрос напрямую через API для тарифной генерации
    const response = await apiClient.post(API_ENDPOINTS.GENERATE_FREE_QUERY, requestData)
    console.log('Получен ответ от API (тариф):', response)

    let result
    if (response && typeof response === 'object') {
      if (response.status === 'success' && response.data && response.data.content) {
        result = response.data.content
      } else if (response.content) {
        result = response.content
      } else if (typeof response === 'string') {
        result = response
      } else {
        result = JSON.stringify(response)
      }
    } else {
      result = typeof response === 'string' ? response : JSON.stringify(response)
    }

    console.log('Обработанный результат:', result)

    // Проверка и обработка ответа
    if (result === null || result === undefined) {
      throw new Error('Получен пустой ответ от сервера')
    }

    aiResponse.value = result

    // Отслеживаем достижение
    await store.checkAchievements(ActionType.GENERATION, {
      content_type: ContentType.TEXT_ANALYSIS,
      language: formData.value.language
    })
  } catch (err: any) {
    console.error('Error in component:', err)
    error.value = err.message || 'Произошла ошибка при обработке запроса'
  } finally {
    isLoading.value = false
  }
}

// Отправка запроса за баллы
const sendQueryWithPoints = async () => {
  try {
    aiResponse.value = null
    error.value = null
    isLoading.value = true

    // Проверяем обязательные поля
    if (!formData.value.language) {
      throw new Error('Пожалуйста, выберите язык')
    }

    if (!formData.value.query) {
      throw new Error('Пожалуйста, введите запрос')
    }

    // Логируем текущее количество баллов пользователя перед генерацией
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед генерацией запроса:', initialPoints)

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.')
    }

    const requestData = {
      language: formData.value.language,
      query: formData.value.query,
      with_points: true // Добавляем флаг генерации за баллы
    }

    console.log('Отправляем запрос к AI за баллы:', requestData)

    try {
      // Добавляем параметры для обхода проверки тарифа и использования баллов
      const requestDataWithSkip = {
        ...requestData,
        skip_tariff_check: true,
        with_points: true,
        skip_limits: true
      }

      // Отправляем запрос напрямую через API клиент, минуя проверку тарифа
      const response = await apiClient.post(API_ENDPOINTS.GENERATE_FREE_QUERY, requestDataWithSkip)
      console.log('Получен ответ от API (за баллы):', response)

      let result
      if (response && typeof response === 'object') {
        if (response.status === 'success' && response.data && response.data.content) {
          result = response.data.content
        } else if (response.content) {
          result = response.content
        } else if (typeof response === 'string') {
          result = response
        } else {
          result = JSON.stringify(response)
        }
      } else {
        result = typeof response === 'string' ? response : JSON.stringify(response)
      }

      // Проверка и обработка ответа
      if (result === null || result === undefined) {
        throw new Error('Получен пустой ответ от сервера')
      }

      aiResponse.value = result
    } catch (apiError: any) {
      console.error('API Error in points generation:', apiError)

      // Если API вернул ошибку, пробуем использовать courseStore как запасной вариант
      console.log('Пробуем использовать courseStore как запасной вариант')
      const result = await courseStore.generateFreeQuery(requestData)
      console.log('Получен ответ от courseStore (за баллы):', result)

      if (result === null || result === undefined) {
        throw new Error('Получен пустой ответ от сервера')
      }

      // Преобразуем ответ в строку, если он не является строкой
      if (typeof result !== 'string') {
        console.warn('Ответ не является строкой, преобразуем:', result)
        aiResponse.value = JSON.stringify(result)
      } else {
        aiResponse.value = result
      }
    }

    // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
    await store.fetchCurrentUser()
    console.log('Количество баллов после генерации запроса:', store.user?.points)

    // Отслеживаем достижение
    await store.checkAchievements(ActionType.GENERATION, {
      content_type: ContentType.TEXT_ANALYSIS,
      language: formData.value.language,
      with_points: true
    })
  } catch (err: any) {
    console.error('Error in component (points generation):', err)
    error.value = err.message || 'Произошла ошибка при обработке запроса'
  } finally {
    isLoading.value = false
  }
}

const regenerate = () => {
  // Используем вычисляемое свойство hasTariff

  // Если нет активного тарифа или обычная генерация недоступна, предлагаем использовать баллы
  if (!hasTariff || (!canGenerate.value && !isUnlimited.value)) {
    // Проверяем, есть ли у пользователя достаточно баллов
    if (store.user && store.user.points >= 8) {
      // Спрашиваем пользователя, хочет ли он использовать баллы
      const message = !hasTariff
        ? 'У вас нет активного тарифа. Хотите использовать 8 баллов для генерации нового ответа?'
        : 'Достигнут дневной лимит генераций. Хотите использовать 8 баллов для генерации нового ответа?';

      if (confirm(message)) {
        sendQueryWithPoints()
        return
      }
    } else {
      error.value = !hasTariff
        ? 'У вас нет активного тарифа. Для генерации необходимо приобрести тариф или пополнить баллы.'
        : 'Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или пополните баллы.';
      return
    }
  }

  sendQuery()
}

const clearError = () => {
  error.value = null
}

const copyToClipboard = async () => {
  if (aiResponse.value) {
    try {
      await navigator.clipboard.writeText(aiResponse.value)
    } catch (err) {
      console.error('Не удалось скопировать текст:', err)
    }
  }
}

// Жизненный цикл
onMounted(() => {
  window.addEventListener('resize', updateWindowWidth)
  updateWindowWidth()
  window.scrollTo(0, 0)

  // Добавляем глобальные стили для улучшения прокрутки
  document.documentElement.style.overflowY = 'auto'
  document.documentElement.style.height = 'auto'
  document.body.style.overflowY = 'auto'
  document.body.style.height = 'auto'
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWindowWidth)
})
</script>

<style scoped>
/* Основной контейнер */
.ai-assistant-container {
  width: 100%;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 2rem;
  background: #1c0522 url('@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  -webkit-overflow-scrolling: touch;
}

/* Планета сверху формы */
.planet-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 300px;
  overflow: hidden;
  z-index: 20;
  pointer-events: none;
}

.planet-image {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 512px;
  height: 512px;
  opacity: 0.8;
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
  max-width: 600px;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.75rem 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.title-container h2 {
  color: white;
  font-size: 2.2rem;
  margin: 0;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.9;
}

/* Контейнер формы и результата */
.content {
  position: relative;
  z-index: 10;
  max-width: 600px;
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
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

/* Инпуты, textarea, select */
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
}

/* Шаблоны запросов */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
  padding: 0.5rem;
  border-radius: 0.5rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 103, 231, 0.5) rgba(42, 8, 46, 0.25);
  -webkit-overflow-scrolling: touch;
}

.template-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem 0.5rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 1rem;
  cursor: pointer !important;
  transition: all 0.3s;
  color: #333;
  text-align: center;
  min-height: 60px;
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
}

.template-btn:hover {
  background-color: rgba(255, 103, 231, 0.5);
  transform: translateY(-2px);
}

.template-btn:active {
  transform: scale(0.97);
}

/* Кнопка "Отправить" */
.form-actions {
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

/* Контейнер для кнопок */
.buttons-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.submit-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #ff67e7 0%, #c400ff 100%);
  color: white;
  border: none;
  border-radius: 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer !important;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.3);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(255, 103, 231, 0.4);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.submit-btn:disabled {
  background: rgba(180, 180, 180, 0.5);
  cursor: not-allowed;
  box-shadow: none;
}

/* Стили для кнопки генерации за баллы */
.points-generate-button {
  background: linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%);
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5);
}

.points-generate-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #42a5f5 0%, #1565c0 100%);
  box-shadow: 0 6px 18px rgba(30, 136, 229, 0.6);
  transform: translateY(-2px);
}

.points-generate-button-highlight {
  animation: pulse 2s infinite;
  border: 2px solid #ffeb3b;
  background: linear-gradient(135deg, #42a5f5 0%, #1565c0 100%);
  font-weight: 700;
  transform: scale(1.05);
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

.points-icon {
  margin-right: 0.5rem;
  display: inline-block;
  font-size: 1.2rem;
}

/* Стили для отображения лимитов генерации */
.generation-limits {
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.limits-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.limits-label {
  color: white;
  font-weight: 500;
}

.limits-value {
  color: #4caf50;
  font-weight: 700;
  padding: 0.25rem 0.75rem;
  background-color: rgba(76, 175, 80, 0.2);
  border-radius: 1rem;
}

.limits-warning {
  color: #ff9800;
  background-color: rgba(255, 152, 0, 0.2);
}

.limits-danger {
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.2);
}

.tariff-info {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  background-color: rgba(255, 152, 0, 0.2);
}

.tariff-warning {
  color: #ff9800;
  font-weight: 500;
  font-size: 0.9rem;
}

/* Загрузка */
.loading {
  margin: 2rem auto;
  text-align: center;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  max-width: 400px;
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 204, 243, 0.3);
  border-top: 3px solid #ff67e7;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  color: white;
  font-size: 1.1rem;
  margin: 0;
}

/* Ошибка */
.error {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(198, 40, 40, 0.3);
  backdrop-filter: blur(8px);
  border-radius: 1rem;
  color: #ffebee;
  position: relative;
  box-shadow: 0 4px 12px rgba(198, 40, 40, 0.3);
  width: 100%;
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
}

/* Результат */
.result {
  margin-top: 2rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  width: 100%;
}

.result h3 {
  color: white;
  font-size: 1.5rem;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.result-actions {
  display: flex;
  gap: 0.75rem;
  margin: 1.5rem 0;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 0.75rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer !important;
  transition: all 0.3s;
  background: linear-gradient(135deg, #ff67e7 0%, #c400ff 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 103, 231, 0.3);
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
  flex: 1;
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.4);
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

/* Стили для отображения баллов */
.assistant-points-display {
  margin: 1rem 0;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 0.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.assistant-points-details {
  width: 100%;
}

.assistant-points-summary {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  color: white;
  font-weight: 500;
  transition: all 0.3s;
}

.assistant-points-summary:hover {
  background-color: rgba(255, 103, 231, 0.1);
  border-radius: 0.5rem;
}

.assistant-points-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.assistant-points-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

.assistant-points-info {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.assistant-points-description {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* Текст сгенерированного ответа */
.response-content {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15);
  overflow-y: auto;
  max-height: 60vh;
  -webkit-overflow-scrolling: touch;
  margin-top: 1rem;
}

/* Адаптивные настройки */
@media (max-width: 768px) {
  .ai-assistant-container {
    padding: 1rem;
    padding-bottom: 3rem;
  }

  .title-container {
    margin-bottom: 1.5rem;
  }

  .title-container h2 {
    font-size: 1.8rem;
  }

  .templates-grid {
    grid-template-columns: 1fr 1fr;
    max-height: 300px;
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
  }

  .action-button {
    width: 100%;
  }

  .response-content {
    padding: 1rem;
    max-height: 50vh;
  }
}

/* Скроллбары */
.templates-grid::-webkit-scrollbar {
  width: 8px;
}

.templates-grid::-webkit-scrollbar-track {
  background: rgba(42, 8, 46, 0.25);
  border-radius: 4px;
}

.templates-grid::-webkit-scrollbar-thumb {
  background: rgba(255, 103, 231, 0.5);
  border-radius: 4px;
}

.response-content::-webkit-scrollbar {
  width: 8px;
}

.response-content::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 4px;
}

.response-content::-webkit-scrollbar-thumb {
  background: #ff67e7;
  border-radius: 4px;
}

/* Предотвращаем нежелательное выделение текста и улучшаем интерактивность */
.template-btn,
.submit-btn,
.action-button,
button {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
  user-select: none;
}
</style>