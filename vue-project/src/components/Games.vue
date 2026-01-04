<template>
  <div
    ref="rootContainer"
    class="games-container"
    :class="{ 'games-global-background-active': true }"
  >
    <div class="games-background"></div>
    <div class="games-content-wrapper">
      <div class="games-content">
        <!-- Заголовок -->
        <div class="games-title-container">
          <h2 class="games-title">Create Language Game</h2>
        </div>

        <!-- Сообщение об ошибке -->
        <div v-if="error" class="games-error">
          <p>{{ error }}</p>
          <button @click="clearError" class="games-error-close">✕</button>
        </div>

        <!-- Форма генерации -->
        <form @submit.prevent="generateGame" class="games-form">
          <!-- Основные параметры -->
          <div class="games-form-group">
            <label for="language">Language:</label>
            <select v-model="formData.language" id="language" required class="games-form-select">
              <option value="" disabled selected>Select language</option>
              <option value="english">English</option>
              <option value="spanish">Spanish (Español)</option>
              <option value="french">French (Français)</option>
              <option value="german">German (Deutsch)</option>
              <option value="italian">Italian (Italiano)</option>
              <option value="chinese">Chinese (中文)</option>
              <option value="japanese">Japanese (日本語)</option>
              <option value="korean">Korean (한국어)</option>
              <option value="turkish">Turkish (Türkçe)</option>
              <option value="russian">Russian</option>
              <option value="arabic">Arabic (العربية)</option>
            </select>
          </div>

          <div class="games-form-group">
            <label for="topic">Topic:</label>
            <input
              v-model="formData.topic"
              id="topic"
              required
              type="text"
              inputmode="text"
              class="games-form-input"
              placeholder="Enter game topic"
            >
          </div>

          <div class="games-form-group">
            <label for="level">Level:</label>
            <select v-model="formData.level" id="level" required class="games-form-select">
              <option value="" disabled selected>Select level</option>
              <option value="beginner">Beginner (A1)</option>
              <option value="elementary">Elementary (A2)</option>
              <option value="intermediate">Intermediate (B1)</option>
              <option value="upper_intermediate">Upper Intermediate (B2)</option>
              <option value="advanced">Advanced (C1)</option>
              <option value="proficiency">Proficiency (C2)</option>
            </select>
          </div>

          <!-- Типы игр -->
          <div class="games-types-section">
            <h3 class="games-section-title">Game Type:</h3>
            <div class="games-types-grid">
              <button
                type="button"
                v-for="type in gameTypes"
                :key="type.value"
                :class="['games-type-btn', { 'games-active-type': formData.game_type === type.value }]"
                @click="formData.game_type = type.value"
              >
                <span class="games-type-icon">{{ type.icon }}</span>
                <span class="games-type-name">{{ type.label }}</span>
              </button>
            </div>
          </div>

          <!-- Продолжительность -->
          <div class="games-duration-section">
            <h3 class="games-section-title">Duration (minutes):</h3>
            <div class="games-duration-container">
              <input
                type="range"
                v-model.number="formData.duration"
                min="5"
                max="30"
                step="5"
                class="games-slider"
              >
              <div class="games-duration-value">{{ formData.duration }} minutes</div>
            </div>
          </div>

          <!-- Формат урока -->
          <div class="games-format-section">
            <h3 class="games-section-title">Lesson Format</h3>
            <div class="games-format-grid">
              <div class="games-format-group">
                <h4 class="games-format-title">Class Type</h4>
                <div class="games-format-buttons">
                  <button
                    type="button"
                    :class="[
                      'games-format-btn',
                      formData.individual_group === 'individual' ? 'games-active-format' : ''
                    ]"
                    @click="formData.individual_group = 'individual'"
                  >
                    <span class="games-format-icon">👤</span>
                    <span class="games-format-label">Individual</span>
                  </button>
                  <button
                    type="button"
                    :class="[
                      'games-format-btn',
                      formData.individual_group === 'group' ? 'games-active-format' : ''
                    ]"
                    @click="formData.individual_group = 'group'"
                  >
                    <span class="games-format-icon">👥</span>
                    <span class="games-format-label">Group</span>
                  </button>
                </div>
              </div>

              <div class="games-format-group">
                <h4 class="games-format-title">Delivery Format</h4>
                <div class="games-format-buttons">
                  <button
                    type="button"
                    :class="[
                      'games-format-btn',
                      formData.online_offline === 'online' ? 'games-active-format' : ''
                    ]"
                    @click="formData.online_offline = 'online'"
                  >
                    <span class="games-format-icon">💻</span>
                    <span class="games-format-label">Online</span>
                  </button>
                  <button
                    type="button"
                    :class="[
                      'games-format-btn',
                      formData.online_offline === 'offline' ? 'games-active-format' : ''
                    ]"
                    @click="formData.online_offline = 'offline'"
                  >
                    <span class="games-format-icon">🏫</span>
                    <span class="games-format-label">Offline</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Информация о лимитах генерации -->
          <div class="games-generation-limits" v-if="!isUnlimited">
            <div class="games-limits-info">
              <span class="games-limits-label">Generations remaining:</span>
              <span class="games-limits-value" :class="{'games-limits-warning': remainingGenerations <= 5, 'games-limits-danger': remainingGenerations <= 2}">
                {{ remainingGenerations }}/{{ generationsLimit }}
              </span>
            </div>
            <div class="games-tariff-info" v-if="!store.tariffInfo || store.tariffInfo.type === 'free'">
              <span class="games-tariff-warning">You don't have an active plan. You can use point-based generation.</span>
            </div>
          </div>

          <!-- Кнопки генерации -->
          <div class="games-form-actions">
            <div class="games-buttons-container">
              <button
                type="submit"
                :disabled="isGenerating || !canGenerate || !hasTariff"
                class="games-submit-btn"
              >
                <span v-if="isGenerating" class="games-loader"></span>
                <template v-if="!hasTariff">
                  No active plan
                </template>
                <template v-else-if="!canGenerate">
                  Generation limit reached
                </template>
                <template v-else-if="isGenerating">
                  Creating...
                </template>
                <template v-else>
                  Create Game
                </template>
              </button>

              <button
                type="button"
                class="games-submit-btn games-points-generate-button"
                :class="{'games-points-generate-button-highlight': !store.tariffInfo || store.tariffInfo.type === 'free'}"
                :disabled="isGenerating || !formData.language || !formData.topic || !formData.level"
                @click="generateGameWithPoints"
              >
                <span v-if="isGenerating" class="games-loader"></span>
                <template v-if="isGenerating">
                  Creating...
                </template>
                <template v-else>
                  <span class="games-points-icon">💎</span> Create for 8 Points
                </template>
              </button>
            </div>
          </div>
        </form>

        <!-- Loading State -->
        <div v-if="isGenerating" class="games-loading">
          <div class="games-loader"></div>
          <p>Creating your game...</p>
        </div>

        <!-- Generated Content -->
        <div v-if="generatedContent" class="games-result">
          <div class="games-result-header">
            <h3 class="games-result-title">Generated Game:</h3>
            <div class="games-result-actions">
              <button @click="copyToClipboard" class="games-action-button">
                <span class="games-button-icon">📋</span>
                Copy
              </button>
              <button @click="regenerate" class="games-action-button games-regenerate">
                <span class="games-button-icon">🔄</span>
                Regenerate
              </button>
            </div>
          </div>

          <!-- Отображение баллов пользователя -->
          <div class="games-points-display">
            <details class="games-points-details">
              <summary class="games-points-summary">
                <span class="games-points-icon">💎</span> Points Balance
              </summary>
              <div class="games-points-content">
                <p class="games-points-info">
                  Your current balance: <strong>{{ userPoints }}</strong> points
                </p>
                <p class="games-points-description">
                  Use points to generate without daily plan limits.
                  Each generation costs 8 points.
                </p>
              </div>
            </details>
          </div>
          <div class="games-content-card">
            <MarkdownRenderer :content="generatedContent" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, onActivated } from 'vue'

// Объявляем тип для Window
declare global {
  interface Window {
    saveComponentStyles?: (componentName: string, selectors: string[]) => void;
  }
}
import { useMainStore } from '@/store'
import { ContentType, ActionType, UNLIMITED_ROLES } from '../core/constants'
import MarkdownRenderer from './common/MarkdownRenderer.vue'
import type { GameFormData } from '@/store'
import { apiClient } from '@/api/client'
import { API_ENDPOINTS } from '@/api/endpoints'

const store = useMainStore()
const rootContainer = ref<HTMLElement | null>(null)
const generatedContent = ref<string | null>(null)
const isLoading = computed(() => store.loading)
const isGenerating = ref(false) // Добавляем переменную для отслеживания состояния генерации
const error = computed(() => store.error)
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)

// Генерация и лимиты
const isUnlimited = computed(() => {
  return store.user && UNLIMITED_ROLES.includes(store.user.role)
})
const hasTariff = computed(() => {
  return isUnlimited.value || (store.tariffInfo && store.tariffInfo.type !== 'free')
})
const canGenerate = computed(() => store.canGenerate(ContentType.GAME))
const remainingGenerations = computed(() => store.remainingGenerations(ContentType.GAME))
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

const gameTypes = [
  { value: 'quiz', label: 'Quiz', icon: '❓' },
  { value: 'roleplay', label: 'Role Play', icon: '🎭' },
  { value: 'board', label: 'Board Game', icon: '🎲' },
  { value: 'word', label: 'Word Game', icon: '📝' },
  { value: 'memory', label: 'Memory Game', icon: '🧠' },
  { value: 'card', label: 'Card Game', icon: '🃏' },
  { value: 'bingo', label: 'Bingo', icon: '🎯' },
  { value: 'charades', label: 'Charades', icon: '🎬' },
  { value: 'taboo', label: 'Taboo', icon: '🙊' },
  { value: 'puzzle', label: 'Puzzle', icon: '🧩' },
  { value: 'scavenger', label: 'Scavenger Hunt', icon: '🔍' },
  { value: 'storytelling', label: 'Storytelling', icon: '📚' }
]

const formData = ref<GameFormData>({
  language: '',
  topic: '',
  type: 'game',  // Добавлено для соответствия интерфейсу
  game_type: 'quiz',
  level: '',
  duration: 15,
  difficulty: 'medium',
  players: {
    min: 2,
    max: 6
  },
  individual_group: 'individual',
  online_offline: 'online'
})

const generateGame = async () => {
  try {
    generatedContent.value = null
    store.clearError()

    // Устанавливаем флаг начала генерации
    isGenerating.value = true

    // Используем вычисляемое свойство hasTariff

    // Проверяем лимиты генерации
    if (!canGenerate.value && !isUnlimited.value) {
      store.setError('Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или используйте генерацию за баллы.')
      isGenerating.value = false // Сбрасываем флаг при ошибке
      return
    }

    // Если нет активного тарифа, предлагаем использовать баллы
    if (!hasTariff) {
      console.log('Нет активного тарифа, предлагаем использовать баллы')
      isGenerating.value = false // Сбрасываем флаг перед предложением использовать баллы
      if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации игры?')) {
        await generateGameWithPoints()
        return
      } else {
        store.setError('Для генерации необходимо приобрести тариф или использовать баллы.')
        return
      }
    }

    console.log('Начинаем генерацию игры с данными:', formData.value)

    try {
      // Отслеживаем использование для лимитов
      await store.checkAndTrackGeneration(ContentType.GAME)
    } catch (limitError: any) {
      console.error('Ошибка при проверке лимитов:', limitError)
      // Если ошибка связана с отсутствием тарифа, предлагаем использовать баллы
      if (limitError.message && (
          limitError.message.includes('No active tariff') ||
          limitError.message.includes('Нет активного тарифа') ||
          limitError.message.includes('403')
        )) {
        if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации игры?')) {
          await generateGameWithPoints()
          return
        } else {
          store.setError('Для генерации необходимо приобрести тариф или использовать баллы.')
          return
        }
      }
      throw limitError
    }

    // Формируем данные для отправки, убеждаясь, что все поля формы включены
    const gameData = {
      ...formData.value,
      language: formData.value.language || 'english',
      topic: formData.value.topic || 'General language practice',
      level: formData.value.level || 'intermediate',
      game_type: formData.value.game_type || 'quiz',
      duration: formData.value.duration || 15,
      difficulty: formData.value.difficulty || 'medium',
      individual_group: formData.value.individual_group || 'individual',
      online_offline: formData.value.online_offline || 'online',
      players: formData.value.players || { min: 2, max: 6 }
    }

    console.log('Отправляем запрос на генерацию игры с данными:', gameData)

    // Формируем правильный запрос для API через store
    const response = await store.generateGame(gameData)

    console.log('Тип полученного ответа:', typeof response)
    console.log('Полученный ответ:', response)

    // Получаем данные из ответа
    const result = response

    // Проверка структуры данных и форматирование для отображения
    console.log('Полный ответ от API (обычная генерация):', result)

    if (result) {
      // Проверяем структуру ответа API
      if (result.status === 'success' && result.data && result.data.content) {
        // Формат ответа: { status: 'success', data: { content: '...' } }
        console.log('Получен контент из data.content:', result.data.content)
        generatedContent.value = result.data.content
      }
      // Проверяем формат ответа API: { status: 'success', message: '...', content: '...' }
      else if (result.status === 'success' && result.content) {
        console.log('Получен контент из result.content (формат API):', result.content)
        generatedContent.value = result.content
      }
      // Если результат содержит поле content - это наиболее вероятный случай
      else if (typeof result === 'object' && result.content) {
        console.log('Найдено поле content в ответе, используем его')
        generatedContent.value = result.content
      }
      // Проверяем, является ли результат объектом с полями или строкой
      else if (typeof result === 'object') {
        console.log('Результат является объектом без поля content. Ключи:', Object.keys(result))
        // Если это объект, форматируем его в Markdown для отображения
        const formattedGame = formatGameToMarkdown(result)
        generatedContent.value = formattedGame
      } else if (typeof result === 'string') {
        console.log('Результат является строкой, длина:', result.length)
        // Просто используем как есть, если это строка
        generatedContent.value = result
      } else {
        console.log('Результат имеет неожиданный тип:', typeof result)
        generatedContent.value = JSON.stringify(result)
      }

      // Проверяем, что контент был установлен
      console.log('Установленный контент:', generatedContent.value)

      // Если контент не был установлен, пытаемся извлечь его из ответа другими способами
      if (!generatedContent.value) {
        console.log('Контент не был установлен, пытаемся извлечь его другими способами')

        // Пытаемся найти контент в любом вложенном объекте
        const findContent = (obj: any): string | null => {
          if (!obj || typeof obj !== 'object') return null

          // Проверяем наличие поля content
          if (obj.content && typeof obj.content === 'string') {
            return obj.content
          }

          // Проверяем все вложенные объекты
          for (const key in obj) {
            if (typeof obj[key] === 'object') {
              const found = findContent(obj[key])
              if (found) return found
            }
          }

          return null
        }

        const foundContent = findContent(result)
        if (foundContent) {
          console.log('Найден контент во вложенном объекте:', foundContent)
          generatedContent.value = foundContent
        } else {
          console.error('Не удалось найти контент в ответе API')
          generatedContent.value = 'Не удалось получить контент игры. Пожалуйста, попробуйте еще раз.'
          store.setError('Ошибка при обработке результата: не удалось найти контент')
        }
      }
    } else {
      console.error('Получен пустой результат от API')
      store.setError('Ошибка при обработке результата: пустые данные')
    }

  } catch (error: any) {
    console.error('Детали ошибки при генерации игры:', error)
    store.setError(error.message || 'Не удалось сгенерировать игру')
  } finally {
    // Сбрасываем флаг генерации, независимо от результата
    isGenerating.value = false
  }
}

// Генерация игры за баллы
const generateGameWithPoints = async () => {
  try {
    generatedContent.value = null
    store.clearError()

    // Устанавливаем флаг начала генерации
    isGenerating.value = true

    // Получаем текущее количество баллов пользователя перед генерацией
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед генерацией игры:', initialPoints)

    // Проверяем обязательные поля
    if (!formData.value.language) {
      throw new Error('Пожалуйста, выберите язык')
    }

    if (!formData.value.topic) {
      throw new Error('Пожалуйста, укажите тему игры')
    }

    if (!formData.value.level) {
      throw new Error('Пожалуйста, выберите уровень')
    }

    // Используем метод store для проверки и списания баллов
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.GAME, 8)

    if (!canGenerate) {
      throw new Error('Не удалось списать баллы. Возможно, недостаточно баллов на счету.')
    }

    // Формируем данные для отправки, убеждаясь, что все поля формы включены
    const gameData = {
      ...formData.value,
      language: formData.value.language || 'english',
      topic: formData.value.topic || 'General language practice',
      level: formData.value.level || 'intermediate',
      game_type: formData.value.game_type || 'quiz',
      duration: formData.value.duration || 15,
      difficulty: formData.value.difficulty || 'medium',
      individual_group: formData.value.individual_group || 'individual',
      online_offline: formData.value.online_offline || 'online',
      players: formData.value.players || { min: 2, max: 6 },
      with_points: true,
      type: 'game'
    }

    console.log('Отправляем запрос на генерацию игры за баллы с данными:', gameData)

    // Используем метод apiClient.post для отправки запроса
    // Важно: параметр with_points должен быть в корне запроса
    // Параметры skip_tariff_check и skip_limits не принимаются моделью запроса на бэкенде
    const response = await apiClient.post(API_ENDPOINTS.GENERATE_GAME, {
      user_id: store.user?.id,
      type: ContentType.GAME,
      prompt: JSON.stringify(gameData),
      with_points: true
    })

    // Получаем данные из ответа
    const result = response.data
    console.log('Получен ответ от API (за баллы):', result)

    // Проверка структуры данных и форматирование для отображения
    console.log('Полный ответ от API:', result)

    if (result) {
      // Проверяем структуру ответа API
      if (result.status === 'success' && result.data && result.data.content) {
        // Формат ответа: { status: 'success', data: { content: '...' } }
        console.log('Получен контент из data.content:', result.data.content)
        generatedContent.value = result.data.content
      }
      // Проверяем формат ответа API: { status: 'success', message: '...', content: '...' }
      else if (result.status === 'success' && result.content) {
        console.log('Получен контент из result.content (формат API):', result.content)
        generatedContent.value = result.content
      }
      // Если результат содержит поле content - это наиболее вероятный случай
      else if (typeof result === 'object' && result.content) {
        console.log('Получен контент из result.content:', result.content)
        generatedContent.value = result.content
      }
      // Проверяем, является ли результат объектом с полями или строкой
      else if (typeof result === 'object') {
        // Если это объект, форматируем его в Markdown для отображения
        console.log('Форматирование объекта в Markdown:', result)
        const formattedGame = formatGameToMarkdown(result)
        generatedContent.value = formattedGame
      } else if (typeof result === 'string') {
        // Просто используем как есть, если это строка
        console.log('Получена строка:', result)
        generatedContent.value = result
      } else {
        console.log('Неизвестный формат ответа, преобразуем в JSON:', result)
        generatedContent.value = JSON.stringify(result)
      }
    } else {
      throw new Error('Получен пустой результат от API')
    }

    // Проверяем, что контент был установлен
    console.log('Установленный контент:', generatedContent.value)

    // Если контент не был установлен, пытаемся извлечь его из ответа другими способами
    if (!generatedContent.value && result) {
      console.log('Контент не был установлен, пытаемся извлечь его другими способами')

      // Пытаемся найти контент в любом вложенном объекте
      const findContent = (obj: any): string | null => {
        if (!obj || typeof obj !== 'object') return null

        // Проверяем наличие поля content
        if (obj.content && typeof obj.content === 'string') {
          return obj.content
        }

        // Проверяем все вложенные объекты
        for (const key in obj) {
          if (typeof obj[key] === 'object') {
            const found = findContent(obj[key])
            if (found) return found
          }
        }

        return null
      }

      const foundContent = findContent(result)
      if (foundContent) {
        console.log('Найден контент во вложенном объекте:', foundContent)
        generatedContent.value = foundContent
      } else {
        console.error('Не удалось найти контент в ответе API')
        generatedContent.value = 'Не удалось получить контент игры. Пожалуйста, попробуйте еще раз.'
      }
    }

    // Обновляем данные пользователя, чтобы отобразить новый баланс баллов
    await store.fetchCurrentUser()
    console.log('Количество баллов после генерации игры:', store.user?.points)

    // Отслеживаем достижение
    await store.checkAchievements(ActionType.GENERATION, {
      content_type: ContentType.GAME,
      language: formData.value.language,
      level: formData.value.level,
      with_points: true
    })
  } catch (error: any) {
    console.error('Детали ошибки при генерации игры за баллы:', error)
    store.setError(error.message || 'Не удалось сгенерировать игру за баллы')
  } finally {
    // Сбрасываем флаг генерации, независимо от результата
    isGenerating.value = false
  }
}

// Функция для форматирования объекта игры в Markdown
const formatGameToMarkdown = (game: any): string => {
  // Формируем строку Markdown из объекта игры
  let markdown = `# ${game.title || 'Language Game'}\n\n`

  // Добавляем материалы, если они есть
  if (game.materials && Array.isArray(game.materials) && game.materials.length > 0) {
    markdown += '## Необходимые материалы\n\n'
    game.materials.forEach((material: string) => {
      markdown += `- ${material}\n`
    })
    markdown += '\n'
  }

  // Добавляем инструкции по подготовке
  if (game.setup) {
    markdown += '## Подготовка\n\n'
    markdown += `${game.setup}\n\n`
  }

  // Добавляем правила
  if (game.rules) {
    markdown += '## Правила игры\n\n'
    markdown += `${game.rules}\n\n`
  }

  // Добавляем систему подсчета очков
  if (game.scoring) {
    markdown += '## Система подсчета очков\n\n'
    markdown += `${game.scoring}\n\n`
  }

  // Добавляем варианты игры
  if (game.variations && Array.isArray(game.variations) && game.variations.length > 0) {
    markdown += '## Варианты игры\n\n'
    game.variations.forEach((variant: string) => {
      markdown += `- ${variant}\n`
    })
    markdown += '\n'
  }

  return markdown
}

const regenerate = () => {
  // Используем вычисляемое свойство hasTariff

  // Если нет активного тарифа или обычная генерация недоступна, предлагаем использовать баллы
  if (!hasTariff || (!canGenerate.value && !isUnlimited.value)) {
    // Спрашиваем пользователя, хочет ли он использовать баллы
    const message = !hasTariff
      ? 'У вас нет активного тарифа. Хотите использовать 8 баллов для генерации новой игры?'
      : 'Достигнут дневной лимит генераций. Хотите использовать 8 баллов для генерации новой игры?';

    if (confirm(message)) {
      generateGameWithPoints()
      return
    } else {
      store.setError(!hasTariff
        ? 'У вас нет активного тарифа. Для генерации необходимо приобрести тариф или использовать баллы.'
        : 'Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или используйте баллы.')
      return
    }
  }

  generateGame()
}

const clearError = () => {
  store.clearError()
}

const copyToClipboard = async () => {
  if (generatedContent.value) {
    try {
      await navigator.clipboard.writeText(generatedContent.value)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }
}

// Жизненный цикл
onMounted(() => {
  window.addEventListener('resize', updateWindowWidth)
  updateWindowWidth()
  window.scrollTo(0, 0)

  // Проверяем, не был ли компонент поврежден предыдущими переходами
  const gamesContainer = document.querySelector('.games-container');
  const needsStyleRestore = !gamesContainer ||
    window.getComputedStyle(gamesContainer).width === '0px' ||
    window.getComputedStyle(gamesContainer).display === 'none' ||
    window.getComputedStyle(gamesContainer).visibility === 'hidden';

  if (needsStyleRestore) {
    console.log('Games компонент поврежден, восстанавливаем стили...');

    // Сначала восстанавливаем общие стили
    if (typeof window.debugTools?.restoreOriginalStyles === 'function') {
      window.debugTools.restoreOriginalStyles();
    }

    // Затем принудительно применяем стили Games
    setTimeout(() => {
      const container = document.querySelector('.games-container');
      if (container && container instanceof HTMLElement) {
        container.style.setProperty('width', '100%', 'important');
        container.style.setProperty('min-height', '100vh', 'important');
        container.style.setProperty('padding', '2rem', 'important');
        container.style.setProperty('position', 'relative', 'important');
        container.style.setProperty('overflow-x', 'hidden', 'important');
        container.style.setProperty('overflow-y', 'auto', 'important');
        container.style.setProperty('display', 'block', 'important');
        container.style.setProperty('visibility', 'visible', 'important');
        container.style.setProperty('opacity', '1', 'important');
      }

      const contentWrapper = document.querySelector('.games-content-wrapper');
      if (contentWrapper && contentWrapper instanceof HTMLElement) {
        contentWrapper.style.setProperty('max-width', '800px', 'important');
        contentWrapper.style.setProperty('margin', '0 auto', 'important');
        contentWrapper.style.setProperty('padding-top', '120px', 'important');
        contentWrapper.style.setProperty('position', 'relative', 'important');
        contentWrapper.style.setProperty('z-index', '10', 'important');
        contentWrapper.style.setProperty('display', 'flex', 'important');
        contentWrapper.style.setProperty('flex-direction', 'column', 'important');
        contentWrapper.style.setProperty('align-items', 'center', 'important');
      }

      const form = document.querySelector('.games-form');
      if (form && form instanceof HTMLElement) {
        form.style.setProperty('margin-bottom', '2rem', 'important');
        form.style.setProperty('width', '100%', 'important');
        form.style.setProperty('display', 'block', 'important');
      }

      console.log('Стили Games принудительно восстановлены');
    }, 100);
  }

  // Сохраняем стили компонента Games после монтирования
  setTimeout(() => {
    if (typeof window.saveComponentStyles === 'function') {
      const gamesSelectors = [
        '.games-container',
        '.games-content',
        '.games-form',
        '.games-background',
        '.games-content-wrapper',
        '.games-title-container',
        '.games-form-group',
        '.games-form-input',
        '.games-form-select',
        '.games-types-section',
        '.games-duration-section',
        '.games-format-section',
        '.games-format-grid',
        '.games-format-group',
        '.games-format-btn',
        '.games-type-btn',
        '.games-submit-btn',
        '.games-form-actions',
        '.games-buttons-container',
        '.games-result-container',
        '.games-result-content',
        '.games-content-card',
        '.games-lesson-plan-container',
        '.games-planet-background',
        '.games-error',
        '.games-loading'
      ];

      window.saveComponentStyles('games', gamesSelectors);
      console.log('Стили компонента Games сохранены');
    }
  }, 500); // Задержка для полного рендеринга компонента

  // Дополнительная проверка стилей через 2 секунды
  setTimeout(() => {
    const container = document.querySelector('.games-container');
    if (container) {
      const computedStyle = window.getComputedStyle(container);
      const needsRestore = computedStyle.width === '0px' ||
                         computedStyle.display === 'none' ||
                         computedStyle.visibility === 'hidden' ||
                         computedStyle.opacity === '0';

      if (needsRestore) {
        console.log('Обнаружена проблема со стилями Games через 2 секунды, восстанавливаем...');

        // Принудительно восстанавливаем стили
        (container as HTMLElement).style.setProperty('width', '100%', 'important');
        (container as HTMLElement).style.setProperty('min-height', '100vh', 'important');
        (container as HTMLElement).style.setProperty('padding', '2rem', 'important');
        (container as HTMLElement).style.setProperty('position', 'relative', 'important');
        (container as HTMLElement).style.setProperty('overflow-x', 'hidden', 'important');
        (container as HTMLElement).style.setProperty('overflow-y', 'auto', 'important');
        (container as HTMLElement).style.setProperty('display', 'block', 'important');
        (container as HTMLElement).style.setProperty('visibility', 'visible', 'important');
        (container as HTMLElement).style.setProperty('opacity', '1', 'important');

        const contentWrapper = document.querySelector('.games-content-wrapper');
        if (contentWrapper && contentWrapper instanceof HTMLElement) {
          contentWrapper.style.setProperty('max-width', '800px', 'important');
          contentWrapper.style.setProperty('margin', '0 auto', 'important');
          contentWrapper.style.setProperty('padding-top', '120px', 'important');
          contentWrapper.style.setProperty('position', 'relative', 'important');
          contentWrapper.style.setProperty('z-index', '10', 'important');
          contentWrapper.style.setProperty('display', 'flex', 'important');
          contentWrapper.style.setProperty('flex-direction', 'column', 'important');
          contentWrapper.style.setProperty('align-items', 'center', 'important');
        }

        const form = document.querySelector('.games-form');
        if (form && form instanceof HTMLElement) {
          form.style.setProperty('margin-bottom', '2rem', 'important');
          form.style.setProperty('width', '100%', 'important');
          form.style.setProperty('display', 'block', 'important');
        }

        console.log('Стили Games восстановлены через дополнительную проверку');
      } else {
        console.log('Стили Games в порядке при дополнительной проверке');
      }
    }
  }, 2000);
})

// Хук для восстановления стилей при активации компонента (возврат из других компонентов)
onActivated(() => {
  console.log('Games component activated - restoring styles');

  // Принудительно восстанавливаем стили компонента
  setTimeout(() => {
    if (typeof window.debugTools?.restoreOriginalStyles === 'function') {
      window.debugTools.restoreOriginalStyles();
      console.log('Стили Games восстановлены через onActivated');
    }

    // Дополнительно сохраняем стили заново
    if (typeof window.saveComponentStyles === 'function') {
      const gamesSelectors = [
        '.games-container',
        '.games-content',
        '.games-form',
        '.games-background',
        '.games-content-wrapper',
        '.games-title-container',
        '.games-form-group',
        '.games-form-input',
        '.games-form-select',
        '.games-types-section',
        '.games-duration-section',
        '.games-format-section',
        '.games-format-grid',
        '.games-format-group',
        '.games-format-btn',
        '.games-type-btn',
        '.games-submit-btn',
        '.games-form-actions',
        '.games-buttons-container',
        '.games-result-container',
        '.games-result-content',
        '.games-content-card',
        '.games-lesson-plan-container',
        '.games-planet-background',
        '.games-error',
        '.games-loading'
      ];

      window.saveComponentStyles('games', gamesSelectors);
      console.log('Стили компонента Games пересохранены при активации');
    }
  }, 100);
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWindowWidth)

  // Диспатчим событие для уведомления других компонентов
  window.dispatchEvent(new CustomEvent('games-unmounted'));

  console.log('Games component unmounted');
})
</script>

<style scoped>
/* Основной контейнер */
.games-container {
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

/* Удалены глобальные стили которые ломали прокрутку */

.games-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 300px;
  background-image: url('@/assets/images/lesson_plan/plan-backgroud-image.svg');
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
  z-index: 2;
  pointer-events: none;
}

.games-content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding-top: 120px;
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.games-content {
  position: relative;
  z-index: 10;
  width: 100%;
}

.games-title-container {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.75rem 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  text-align: center;
}

.games-title {
  color: white;
  font-size: 2.2rem;
  margin: 0;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.9;
}

.games-error {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(198, 40, 40, 0.3);
  backdrop-filter: blur(8px);
  border-radius: 1rem;
  color: #ffebee;
  position: relative;
  box-shadow: 0 4px 12px rgba(198, 40, 40, 0.3);
}

.games-error-close {
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

.games-form {
  margin-bottom: 2rem;
  width: 100%;
}

.games-form-group {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.games-form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: white;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.games-form-input,
.games-form-select {
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

.games-form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23333' stroke='%23333' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 16px;
  padding-right: 2.5rem;
}

.games-form-input:focus,
.games-form-select:focus {
  box-shadow: 0 0 0 3px rgba(255, 103, 231, 0.4), inset 0 2px 6px rgba(0, 0, 0, 0.1);
  outline: none;
}

.games-types-section,
.games-duration-section,
.games-format-section {
  margin-bottom: 1.5rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.games-section-title {
  color: white;
  font-size: 1.3rem;
  margin-bottom: 1rem;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.games-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
  max-height: 400px;
  overflow-y: auto;
  padding: 0.5rem;
  border-radius: 0.5rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 103, 231, 0.5) rgba(42, 8, 46, 0.25);
  -webkit-overflow-scrolling: touch;
}

.games-type-btn {
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
  min-height: 80px;
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
}

.games-type-btn:hover:not(.games-active-type) {
  background-color: rgba(255, 103, 231, 0.5);
  transform: translateY(-2px);
}

.games-active-type {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
  transform: scale(1.05);
}

.games-type-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.games-type-name {
  font-size: 0.875rem;
  font-weight: 500;
}

.games-duration-container {
  padding: 1rem;
  background: rgba(255, 204, 243, 0.3);
  border-radius: 0.75rem;
}

.games-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  background: rgba(255, 204, 243, 0.7);
  border-radius: 4px;
  margin-bottom: 1rem;
  outline: none;
  cursor: pointer;
  z-index: 15;
  touch-action: manipulation;
}

.games-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  background: #ff67e7;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.games-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  background: #ff67e7;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.games-duration-value {
  text-align: center;
  font-weight: 500;
  color: white;
  font-size: 1.1rem;
}

.games-format-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {
  .games-format-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.games-format-group {
  background: rgba(42, 8, 46, 0.3);
  border-radius: 0.75rem;
  padding: 1rem;
}

.games-format-title {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.games-format-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.games-format-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: rgba(255, 204, 243, 0.7);
  border: none;
  border-radius: 0.75rem;
  cursor: pointer !important;
  transition: all 0.3s;
  color: #333;
  flex: 1;
  min-width: 120px;
  touch-action: manipulation;
  z-index: 15;
  user-select: none;
}

.games-format-btn:hover:not(.games-active-format) {
  background-color: rgba(255, 103, 231, 0.5);
  color: white;
}

.games-active-format {
  background-color: #ff67e7;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

.games-format-icon {
  font-size: 1.2rem;
}

.games-format-label {
  font-size: 0.9rem;
  font-weight: 500;
}

.games-form-actions {
  margin-top: 2rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.25rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

/* Контейнер для кнопок */
.games-buttons-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.games-submit-btn {
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

.games-submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(255, 103, 231, 0.4);
}

.games-submit-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.games-submit-btn:disabled {
  background: rgba(180, 180, 180, 0.5);
  cursor: not-allowed;
  box-shadow: none;
}

/* Стили для кнопки генерации за баллы */
.games-points-generate-button {
  background: linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%);
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.5);
}

.games-points-generate-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #42a5f5 0%, #1565c0 100%);
  box-shadow: 0 6px 18px rgba(30, 136, 229, 0.6);
  transform: translateY(-2px);
}

.games-points-generate-button-highlight {
  animation: games-pulse 2s infinite;
  border: 2px solid #ffeb3b;
  background: linear-gradient(135deg, #42a5f5 0%, #1565c0 100%);
  font-weight: 700;
  transform: scale(1.05);
}

@keyframes games-pulse {
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

.games-points-icon {
  margin-right: 0.5rem;
  display: inline-block;
  font-size: 1.2rem;
}

/* Стили для отображения лимитов генерации */
.games-generation-limits {
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.games-limits-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.games-limits-label {
  color: white;
  font-weight: 500;
}

.games-limits-value {
  color: #4caf50;
  font-weight: 700;
  padding: 0.25rem 0.75rem;
  background-color: rgba(76, 175, 80, 0.2);
  border-radius: 1rem;
}

.games-limits-warning {
  color: #ff9800;
  background-color: rgba(255, 152, 0, 0.2);
}

.games-limits-danger {
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.2);
}

.games-tariff-info {
  margin-top: 0.5rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  background-color: rgba(255, 152, 0, 0.2);
}

.games-tariff-warning {
  color: #ff9800;
  font-weight: 500;
  font-size: 0.9rem;
}

.games-loading {
  margin: 2rem auto;
  text-align: center;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  max-width: 400px;
}

.games-loader {
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

.games-loading p {
  color: white;
  font-size: 1.1rem;
  margin: 0;
}

.games-result {
  margin-top: 2rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  padding: 1.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
  width: 100%;
}

.games-result-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

@media (min-width: 640px) {
  .games-result-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.games-result-title {
  color: white;
  font-size: 1.5rem;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 103, 231, 0.5);
}

.games-result-actions {
  display: flex;
  gap: 0.75rem;
}

.games-action-button {
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
}

.games-action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.4);
}

.games-action-button:active {
  transform: translateY(1px);
}

.games-button-icon {
  font-size: 1.2rem;
}

.games-regenerate {
  background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);
}

.games-content-card {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15);
  overflow-y: auto;
  max-height: 60vh;
  -webkit-overflow-scrolling: touch;
}

/* Стили для отображения баллов */
.games-points-display {
  margin: 1rem 0;
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  padding: 0.5rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.games-points-details {
  width: 100%;
}

.games-points-summary {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  cursor: pointer;
  color: white;
  font-weight: 500;
  transition: all 0.3s;
}

.games-points-summary:hover {
  background-color: rgba(255, 103, 231, 0.1);
  border-radius: 0.5rem;
}

.games-points-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.games-points-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  margin-top: 0.5rem;
}

.games-points-info {
  color: white;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.games-points-description {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.games-content-card :deep(.markdown-renderer) {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", sans-serif;
  line-height: 1.6;
  color: #333;
}

.games-content-card :deep(h1) {
  font-size: 1.8rem;
  font-weight: bold;
  margin: 1.5rem 0 1rem 0;
  padding-bottom: 0.3rem;
  border-bottom: 2px solid #ff67e7;
  color: #333;
}

.games-content-card :deep(h2) {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 1.5rem 0 1rem 0;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid #ff67e7;
  color: #333;
}

.games-content-card :deep(h3) {
  font-size: 1.3rem;
  font-weight: bold;
  margin: 1.2rem 0 0.8rem 0;
  color: #333;
}

.games-content-card :deep(p) {
  margin-bottom: 1rem;
  color: #333;
}

.games-content-card :deep(ul),
.games-content-card :deep(ol) {
  margin-bottom: 1.5rem;
  padding-left: 2rem;
}

.games-content-card :deep(li) {
  margin-bottom: 0.5rem;
  padding: 0.3rem 0;
  color: #333;
}

.games-content-card :deep(strong) {
  font-weight: bold;
  color: #333;
}

.games-content-card :deep(em) {
  font-style: italic;
  color: #333;
}

.games-content-card :deep(code) {
  font-family: monospace;
  background-color: #f5f5f5;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  color: #333;
}

/* Мобильные стили */
@media (max-width: 768px) {
  .games-container {
    padding: 1rem;
    padding-bottom: 3rem;
  }

  .games-content-wrapper {
    padding-top: 40px;
  }

  .games-title {
    font-size: 1.8rem;
  }

  .games-types-grid {
    grid-template-columns: 1fr 1fr;
    max-height: 300px;
  }

  .games-type-btn {
    flex-direction: row;
    justify-content: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
  }

  .games-form-input,
  .games-form-select,
  .games-submit-btn {
    font-size: 16px; /* Предотвращает масштабирование на iOS */
    padding: 0.875rem;
  }

  .games-result-actions {
    flex-direction: column;
    width: 100%;
  }

  .games-action-button {
    width: 100%;
  }

  .games-content-card {
    padding: 1rem;
    max-height: 50vh;
  }
}

/* Доступность */
*:focus {
  outline: 3px solid rgba(255, 103, 231, 0.5);
  outline-offset: 3px;
}

/* Скроллбары */
.games-types-grid::-webkit-scrollbar {
  width: 8px;
}

.games-types-grid::-webkit-scrollbar-track {
  background: rgba(42, 8, 46, 0.25);
  border-radius: 4px;
}

.games-types-grid::-webkit-scrollbar-thumb {
  background: rgba(255, 103, 231, 0.5);
  border-radius: 4px;
}

.games-content-card::-webkit-scrollbar {
  width: 8px;
}

.games-content-card::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 4px;
}

.games-content-card::-webkit-scrollbar-thumb {
  background: #ff67e7;
  border-radius: 4px;
}

/* Предотвращаем нежелательное выделение текста и улучшаем интерактивность */
.games-type-btn,
.games-format-btn,
.games-submit-btn,
.games-action-button,
button {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
  user-select: none;
}

/* Стили для анимации загрузки */
.games-loader {
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

/* Стили для состояния загрузки */
.games-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background-color: rgba(42, 8, 46, 0.45);
  border-radius: 1rem;
  margin: 1.5rem 0;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.games-loading .games-loader {
  width: 40px;
  height: 40px;
  border-width: 4px;
  margin-bottom: 1rem;
}

.games-loading p {
  color: white;
  font-size: 1.2rem;
  font-weight: 500;
}
</style>
