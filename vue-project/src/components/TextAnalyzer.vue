<!-- src/components/TextAnalyzer.vue -->
<template>
  <div class="text-analyzer-container" :style="backgroundStyle">
    <!-- Заголовок -->
    <div class="title-container">
      <h2>Text Trainer</h2>
      <div class="points-display" v-if="store.user">
        <span class="points-icon">💎</span>
        <span class="points-value">{{ userPoints }} points</span>
      </div>
    </div>

    <!-- Основной контент: форма и результат -->
    <div class="content">
      <form claыss="text-analyzer-form">
        <!-- Язык -->
        <div class="form-group">
          <label for="language">Text Language:</label>
          <select
            v-model="formData.language"
            id="language"
            required
            class="form-select"
          >
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
            <option value="russian">Russian (Русский)</option>
            <option value="arabic">Arabic (العربية)</option>
          </select>
        </div>

        <!-- Текст для анализа -->
        <div class="form-group">
          <label for="text-content">Text to Analyze:</label>
          <textarea
            v-model="formData.textContent"
            id="text-content"
            required
            class="form-textarea"
            placeholder="Enter text to analyze..."
            rows="8"
          ></textarea>
        </div>
      </form>

      <!-- Кнопки действий -->
      <div class="actions-panel">
        <h3>Text Actions</h3>
        <div class="action-buttons">
          <!-- Определить уровень текста -->
          <div class="action-button-group">
            <button @click="detectTextLevel" class="action-button">
              <span class="icon">📊</span>
              Detect Text Level
            </button>
            <button @click="detectTextLevelWithPoints" class="action-button points-button">
              <span class="points-icon">💎</span>
              For Points (8)
            </button>
          </div>

          <!-- Перегенерировать текст -->
          <button @click="showRegenerateOptions = !showRegenerateOptions" class="action-button">
            <span class="icon">🔄</span>
            Regenerate Text
          </button>
          <div v-if="showRegenerateOptions" class="options-panel">
            <div class="options-header">
              <h3>Regenerate Text</h3>
              <button @click="showRegenerateOptions = false" class="close-button">×</button>
            </div>

            <div class="game-options-container">
              <div class="game-option">
                <label>Select Vocabulary:</label>
                <select v-model="regenerateOptions.vocabulary" class="form-select sm">
                  <option value="simple">Simple</option>
                  <option value="neutral">Neutral</option>
                  <option value="advanced">Advanced</option>
                  <option value="academic">Academic</option>
                  <option value="professional">Professional</option>
                </select>
              </div>

              <div class="game-option">
                <label>Text Style:</label>
                <select v-model="regenerateOptions.style" class="form-select sm">
                  <option value="neutral">Neutral</option>
                  <option value="formal">Formal</option>
                  <option value="informal">Informal</option>
                  <option value="creative">Creative</option>
                  <option value="technical">Technical</option>
                  <option value="business">Business</option>
                  <option value="academic">Academic</option>
                </select>
              </div>

              <div class="game-option">
                <label>Target Level:</label>
                <select v-model="regenerateOptions.targetLevel" class="form-select sm">
                  <option value="">Keep Current</option>
                  <option v-for="level in availableLevels" :key="level.id" :value="level.id">
                    {{ level.name }}
                  </option>
                </select>
              </div>
            </div>

            <div class="buttons-row">
              <button @click="regenerateText" class="submit-btn">Regenerate</button>
              <button @click="regenerateTextWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Изменить уровень текста -->
          <button @click="showLevelChangeOptions = !showLevelChangeOptions" class="action-button">
            <span class="icon">📈</span>
            Change Text Level
          </button>
          <div v-if="showLevelChangeOptions" class="options-panel">
            <div class="options-header">
              <h3>Change Text Level</h3>
              <button @click="showLevelChangeOptions = false" class="close-button">×</button>
            </div>

            <div class="game-options-container">
              <div class="game-option">
                <label>Select Level:</label>
                <select v-model="levelChangeOptions.targetLevel" class="form-select sm">
                  <option v-for="level in availableLevels" :key="level.id" :value="level.id">
                    {{ level.name }}
                  </option>
                </select>
              </div>

              <div class="game-option">
                <label>Preserve Style:</label>
                <div class="toggle-container">
                  <input type="checkbox" id="preserve-style" v-model="levelChangeOptions.preserveStyle">
                  <label for="preserve-style" class="toggle-label"></label>
                </div>
              </div>
            </div>

            <div class="buttons-row">
              <button @click="changeTextLevel" class="submit-btn">Change Level</button>
              <button @click="changeTextLevelWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать вопросы к тексту -->
          <button @click="showQuestionsOptions = !showQuestionsOptions" class="action-button">
            <span class="icon">❓</span>
            Create Questions
          </button>
          <div v-if="showQuestionsOptions" class="options-panel">
            <label>Number of Questions:</label>
            <input v-model.number="questionsOptions.count" type="number" min="1" max="10" class="form-input sm">

            <label>Question Difficulty:</label>
            <select v-model="questionsOptions.difficulty" class="form-select sm">
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>

            <label>Target Vocabulary (leave empty for auto-detection):</label>
            <input v-model="questionsOptions.vocabulary" type="text" placeholder="For example: business, medical, technical..." class="form-input sm">

            <label>Target Grammar (leave empty for auto-detection):</label>
            <input v-model="questionsOptions.grammar" type="text" placeholder="For example: Present Perfect, Passive Voice..." class="form-input sm">

            <div class="buttons-row">
              <button @click="generateQuestions" class="submit-btn">Create Questions</button>
              <button @click="generateQuestionsWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать план урока -->
          <button @click="showLessonPlanOptions = !showLessonPlanOptions" class="action-button">
            <span class="icon">📝</span>
            Create Lesson Plan
          </button>
          <div v-if="showLessonPlanOptions" class="options-panel">
            <div class="options-header">
              <h3>Create Lesson Plan</h3>
              <button @click="showLessonPlanOptions = false" class="close-button">×</button>
            </div>

            <div class="game-options-container">
              <div class="game-option">
                <label>Age Group:</label>
                <select v-model="lessonPlanOptions.age" class="form-select sm">
                  <option value="children">Children (7-12 years)</option>
                  <option value="teens">Teens (13-17 years)</option>
                  <option value="adults">Adults (18+ years)</option>
                  <option value="young_learners">Young Learners (4-6 years)</option>
                  <option value="seniors">Seniors (60+ years)</option>
                </select>
              </div>

              <div class="game-option">
                <label>Teaching Methodology:</label>
                <select v-model="lessonPlanOptions.methodology" class="form-select sm">
                  <option value="">Not specified</option>
                  <optgroup label="Universal Methodologies">
                    <option value="celta">CELTA (Cambridge Certificate)</option>
                    <option value="clil">CLIL (Content and Language Integrated Learning)</option>
                    <option value="tbl">TBL (Task-Based Learning)</option>
                    <option value="tblt">TBLT (Task-Based Language Teaching)</option>
                    <option value="cbi">CBI (Content-Based Instruction)</option>
                    <option value="tpr">TPR (Total Physical Response)</option>
                    <option value="dm">Direct Method</option>
                    <option value="suggestopedia">Suggestopedia</option>
                    <option value="silentWay">Silent Way</option>
                    <option value="ali">Audio-Lingual Method</option>
                  </optgroup>
                  <optgroup label="English Language Methodologies">
                    <option value="esl">ESL Method</option>
                    <option value="efl">EFL Method</option>
                    <option value="esp">ESP (English for Specific Purposes)</option>
                    <option value="eap">EAP (English for Academic Purposes)</option>
                  </optgroup>
                </select>
              </div>

              <div class="game-option">
                <label>Lesson Duration:</label>
                <select v-model="lessonPlanOptions.duration" class="form-select sm">
                  <option value="30">30 minutes</option>
                  <option value="45">45 minutes</option>
                  <option value="60">60 minutes</option>
                  <option value="90">90 minutes</option>
                  <option value="120">120 minutes</option>
                </select>
              </div>

              <div class="game-option">
                <label>Lesson Type:</label>
                <select v-model="lessonPlanOptions.individual_group" class="form-select sm">
                  <option value="individual">Individual</option>
                  <option value="group">Group</option>
                  <option value="pair">Pair</option>
                </select>
              </div>

              <div class="game-option">
                <label>Delivery Format:</label>
                <select v-model="lessonPlanOptions.online_offline" class="form-select sm">
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                </select>
              </div>

              <div class="game-option">
                <label>Lesson Focus:</label>
                <select v-model="lessonPlanOptions.focus" class="form-select sm">
                  <option value="grammar">Grammar</option>
                  <option value="vocabulary">Vocabulary</option>
                  <option value="speaking">Speaking Practice</option>
                  <option value="listening">Listening</option>
                  <option value="reading">Reading</option>
                  <option value="writing">Writing</option>
                  <option value="mixed">Mixed Focus</option>
                </select>
              </div>

              <div class="game-option">
                <label>Difficulty Level:</label>
                <select v-model="lessonPlanOptions.level" class="form-select sm">
                  <option value="beginner">Beginner (A1)</option>
                  <option value="elementary">Elementary (A2)</option>
                  <option value="intermediate">Intermediate (B1)</option>
                  <option value="upper_intermediate">Upper Intermediate (B2)</option>
                  <option value="advanced">Advanced (C1)</option>
                  <option value="proficient">Proficient (C2)</option>
                </select>
              </div>
            </div>

            <div class="buttons-row">
              <button @click="generateLessonPlan" class="submit-btn">Create Lesson Plan</button>
              <button @click="generateLessonPlanWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать упражнения -->
          <button @click="showExercisesOptions = !showExercisesOptions" class="action-button">
            <span class="icon">📚</span>
            Create Exercises
          </button>
          <div v-if="showExercisesOptions" class="options-panel">
            <label>Type of Exercises:</label>
            <select v-model="exercisesOptions.type" class="form-select sm">
              <option value="vocabulary">Vocabulary</option>
              <option value="grammar">Grammar</option>
              <option value="reading">Reading</option>
              <option value="mixed">Mixed</option>
            </select>

            <label>Exercise Format:</label>
            <select v-model="exercisesOptions.format" class="form-select sm">
              <option value="matching">Matching</option>
              <option value="gap-fill">Gap Fill</option>
              <option value="word-definition">Word-Definition</option>
              <option value="mixed">Mixed Format</option>
            </select>

            <div class="buttons-row">
              <button @click="generateExercises" class="submit-btn">Create Exercises</button>
              <button @click="generateExercisesWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать игру -->
          <button @click="showGameOptions = !showGameOptions" class="action-button">
            <span class="icon">🎮</span>
            Create Game
          </button>
          <div v-if="showGameOptions" class="options-panel">
            <label>Game Type:</label>
            <select v-model="gameOptions.type" class="form-select sm">
              <option value="warm-up">Warm-up</option>
              <option value="review">Review</option>
              <option value="quiz">Quiz</option>
              <option value="roleplay">Roleplay</option>
              <option value="storytelling">Storytelling</option>
              <option value="vocabulary">Vocabulary Game</option>
              <option value="grammar">Grammar Game</option>
              <option value="speaking">Speaking Game</option>
              <option value="listening">Listening Game</option>
              <option value="reading">Reading Game</option>
              <option value="writing">Writing Game</option>
              <option value="cultural">Cultural Game</option>
            </select>

            <label>Game Format:</label>
            <select v-model="gameOptions.format" class="form-select sm">
              <option value="individual">Individual</option>
              <option value="group">Group</option>
              <option value="pair">Pair</option>
            </select>

            <label>Age Group:</label>
            <select v-model="gameOptions.age" class="form-select sm">
              <option value="children">Children</option>
              <option value="teenagers">Teenagers</option>
              <option value="adults">Adults</option>
              <option value="young_learners">Young Learners</option>
              <option value="seniors">Seniors</option>
            </select>

            <div class="buttons-row">
              <button @click="generateGame" class="submit-btn">Create Game</button>
              <button @click="generateGameWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать саммари -->
          <button @click="showSummaryOptions = !showSummaryOptions" class="action-button">
            <span class="icon">📋</span>
            Create Summary
          </button>
          <div v-if="showSummaryOptions" class="options-panel">
            <div class="options-row">
              <div class="option-item">
                <label>Summary Type:</label>
                <select v-model="summaryOptions.mode" class="form-select sm">
                  <option value="single">Single Summary</option>
                  <option value="multiple">Three Summaries of Different Lengths</option>
                </select>
              </div>
              <div class="option-item" v-if="summaryOptions.mode === 'single'">
                <label>Difficulty Level:</label>
                <select v-model="summaryOptions.level" class="form-select sm">
                  <option v-for="level in availableLevels" :key="level.id" :value="level.id">
                    {{ level.name }} - {{ level.description }}
                  </option>
                </select>
              </div>
            </div>
            <div class="buttons-row">
              <button @click="generateSummaries" class="submit-btn">Create Summary</button>
              <button @click="generateSummariesWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать названия -->
          <button @click="showTitlesOptions = !showTitlesOptions" class="action-button">
            <span class="icon">📌</span>
            Create Titles
          </button>
          <div v-if="showTitlesOptions" class="options-panel">
            <label>Number of Titles:</label>
            <input v-model.number="titlesOptions.count" type="number" min="1" max="10" class="form-input sm">
            <div class="buttons-row">
              <button @click="generateTitles" class="submit-btn">Create Titles</button>
              <button @click="generateTitlesWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>

          <!-- Создать тест на понимание -->
          <button @click="showComprehensionTestOptions = !showComprehensionTestOptions" class="action-button">
            <span class="icon">📊</span>
            Create Comprehension Test
          </button>
          <div v-if="showComprehensionTestOptions" class="options-panel">
            <label>Number of Questions:</label>
            <input v-model.number="comprehensionTestOptions.question_count" type="number" min="1" max="10" class="form-input sm">

            <label>Question Difficulty:</label>
            <select v-model="comprehensionTestOptions.difficulty" class="form-select sm">
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            <div class="buttons-row">
              <button @click="generateComprehensionTest" class="submit-btn">Create Test</button>
              <button @click="generateComprehensionTestWithPoints" class="submit-btn points-button">
                <span class="points-icon">💎</span> For Points (8)
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Результат анализа -->
      <div v-if="analysisResult" class="result">
        <h3>Result:</h3>
        <div class="result-content">
          <MarkdownRenderer :content="analysisResult" theme="light" />
        </div>

        <!-- Кнопки для детализации плана урока (показываются только если сгенерирован план урока) -->
        <div v-if="isLessonPlanGenerated" class="lesson-plan-details-buttons">
          <h4>Детализировать план урока:</h4>

          <div class="buttons-group">
            <h5>Детализировать пункты плана:</h5>
            <div class="buttons-row">
              <button
                v-for="num in 8"
                :key="`detail-point-${num}`"
                @click="detailLessonPlanPoint(num)"
                class="detail-button"
              >
                Пункт {{ num }}
              </button>
            </div>
          </div>

          <div class="buttons-group">
            <h5>Дополнительные материалы:</h5>
            <div class="buttons-row">
              <button @click="detailLessonPlanPoint('homework')" class="detail-button">
                Домашнее задание
              </button>
              <button @click="detailLessonPlanPoint('script')" class="detail-button">
                Скрипт учителя
              </button>
              <button @click="detailLessonPlanPoint('exercises')" class="detail-button">
                Больше упражнений
              </button>
              <button @click="detailLessonPlanPoint('game')" class="detail-button">
                Создать игру для урока
              </button>
            </div>
          </div>

          <div class="buttons-group">
            <h5>Переписать пункты плана:</h5>
            <div class="buttons-row">
              <button
                v-for="num in 8"
                :key="`rewrite-point-${num}`"
                @click="rewriteLessonPlanPoint(num)"
                class="detail-button rewrite"
              >
                Пункт {{ num }}
              </button>
            </div>
          </div>

          <!-- Блок для отображения детализированной информации -->
          <div v-if="detailedLessonContent" class="detailed-content">
            <h4>Детализированная информация:</h4>
            <div class="result-content">
              <MarkdownRenderer :content="detailedLessonContent" theme="light" />
            </div>
            <button @click="detailedLessonContent = ''" class="close-detail-button">
              Закрыть и вернуться к плану
            </button>
          </div>
        </div>
      </div>

      <!-- Состояние загрузки -->
      <div v-if="isLoading" class="loading">
        <div class="loader"></div>
        <p>Processing text...</p>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="clearError" class="error-close">✕</button>
      </div>

      <!-- После определения уровня показываем кнопки для быстрых действий -->
      <div v-if="detectedLevel" class="detected-level-actions">
        <div class="detected-level-info">
          <span class="level-label">Определенный уровень:</span>
          <span class="level-value">{{ detectedLevel }}</span>
        </div>
        <div class="quick-actions">
          <button @click="showLevelChangeOptions = true" class="quick-action-btn">
            <span class="icon">📈</span>
            Изменить уровень
          </button>
          <button @click="showRegenerateOptions = true" class="quick-action-btn">
            <span class="icon">🔄</span>
            Перегенерировать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useMainStore } from '@/store'
import { API_ENDPOINTS } from '@/api/endpoints'
import { ContentType } from '@/core/constants'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import { getLevelsByLanguage } from '@/constants/levels'

// Импорт фона (такой же как в LessonPlan.vue или аналогичный)
import planetBg from '@/assets/images/lesson_plan/plan-backgroud-image.svg'

const store = useMainStore()

// Функция-помощник для получения заголовков авторизации
const getAuthHeaders = () => {
  const webAppData = window.Telegram?.WebApp?.initData
  return {
    'Content-Type': 'application/json',
    'Authorization': webAppData ? `tma ${webAppData}` : 'Bearer null'
  }
}

// Состояние формы
const formData = ref({
  language: 'english',
  textContent: '',
  topic: 'general'
})

// Результат анализа
const analysisResult = ref<string | null>(null)
// Флаг загрузки для имитации запросов
const localLoading = ref(false)
// Общий флаг загрузки, комбинирующий локальный и из store
const isLoading = computed(() => store.loading || localLoading.value)
const error = computed(() => store.error)
const userPoints = computed(() => store.user?.points || 0)

// Фон с планетой (аналогично LessonPlan.vue)
const backgroundStyle = computed(() => ({
  backgroundImage: `url(${planetBg})`,
  backgroundSize: '90% auto',
  backgroundPosition: 'center -80px',
  backgroundRepeat: 'no-repeat',
  paddingTop: '60px'
}))

// Получаем доступные уровни в зависимости от выбранного языка
const availableLevels = computed(() => {
  return getLevelsByLanguage(formData.value.language)
})

// Флаги для отображения панелей опций
const showRegenerateOptions = ref(false)
const showLevelChangeOptions = ref(false)
const showQuestionsOptions = ref(false)
const showLessonPlanOptions = ref(false)
const showExercisesOptions = ref(false)
const showGameOptions = ref(false)
const showSummaryOptions = ref(false)
const showTitlesOptions = ref(false)
const showComprehensionTestOptions = ref(false)

// Храним определенный уровень текста
const detectedLevel = ref('')

// Опции для перегенерации текста
const regenerateOptions = ref({
  vocabulary: 'neutral',
  style: 'neutral',
  targetLevel: '',
  preserveStyle: true
})

// Опции для изменения уровня текста
const levelChangeOptions = ref({
  targetLevel: '',
  preserveStyle: true,
  vocabulary: 'neutral',
  style: 'neutral'
})

// Опции для генерации вопросов
const questionsOptions = ref({
  count: 5,
  difficulty: 'medium',
  vocabulary: '',
  grammar: ''
})

// Опции для генерации плана урока
const lessonPlanOptions = ref({
  age: 'teens',
  methodology: '',
  duration: '45',
  individual_group: 'group',
  online_offline: 'online',
  focus: 'mixed',
  level: 'intermediate'
})

// Опции для генерации упражнений
const exercisesOptions = ref({
  type: 'mixed',
  count: 5,
  format: 'mixed'
})

// Опции для генерации игр
const gameOptions = ref({
  type: 'vocabulary',
  duration: '10-15 минут',
  individual_group: 'group',
  online_offline: 'offline',
  age: 'adults',
  format: 'group'
})

// Опции для генерации саммари
const summaryOptions = ref({
  level: '',
  mode: 'single' // 'single' или 'multiple'
})

// Опции для генерации заголовков
const titlesOptions = ref({
  count: 5
})

// Опции для генерации теста на понимание
const comprehensionTestOptions = ref({
  question_count: 5,
  difficulty: 'medium'
})

// Методы для работы с текстом
const detectTextLevel = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    detectedLevel.value = '' // Сбрасываем определенный уровень
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points for text level determination?')) {
            await detectTextLevelWithPoints();
            return;
          } else {
            store.setError('You need to purchase a tariff or use points for generation.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. To generate, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.DETECT_TEXT_LEVEL}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ для определения уровня текста:', result.data);

        // Устанавливаем результат анализа
        analysisResult.value = result.data.content;

        // Используем определенный уровень из ответа API
        if (result.data.detected_level && result.data.detected_level !== 'Unknown') {
          detectedLevel.value = result.data.detected_level;
          console.log(`Установлен уровень текста: ${detectedLevel.value}`);
        } else {
          // Если API не вернул уровень, пытаемся извлечь его из контента
          const levelMatch = analysisResult.value && analysisResult.value.match(/[A-C][1-2][-+]?|ТЭУ|ТБУ|ТРКИ-[1-4]|HSK\s*[1-6]|N[1-5]|TOPIK\s*[1-6]|Beginner|Elementary|Intermediate|Upper[- ]?Intermediate|Advanced|Proficient|Superior|Native/i);
        if (levelMatch) {
            detectedLevel.value = levelMatch[0];
            console.log(`Извлечен уровень текста из контента: ${detectedLevel.value}`);
          }
        }
      } else {
        throw new Error(result.message || 'Error determining text level')
      }
    } catch (error) {
      console.error('Error determining text level:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error determining text level')
    } finally {
      localLoading.value = false
    }
  } catch (err) {
    console.error('Ошибка при определении уровня текста:', err)
    localLoading.value = false
  }
}

const regenerateText = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Создаем базовый запрос
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      vocabulary: regenerateOptions.value.vocabulary,
      style: regenerateOptions.value.style
    }

    // Если выбран целевой уровень, добавляем его в запрос
    if (regenerateOptions.value.targetLevel) {
      // Используем оператор расширения для создания нового объекта с дополнительным полем
      const requestWithLevel = {
        ...requestData,
        target_level: regenerateOptions.value.targetLevel
      }

      // Определяем эндпоинт для запроса с уровнем
      const endpoint = API_ENDPOINTS.CHANGE_TEXT_LEVEL

      try {
        // Делаем запрос к API бэкенда
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(requestWithLevel)
        })

        const result = await response.json()

        if (result.status === 'success') {
          analysisResult.value = result.data.content
          detectedLevel.value = '' // Сбрасываем определенный уровень, так как текст изменился
        } else {
          throw new Error(result.message || 'Ошибка при перегенерации текста')
        }
      } catch (error) {
        console.error('Ошибка при перегенерации текста:', error)
        store.setError(typeof error === 'object' && error !== null && 'message' in error ?
          (error as Error).message : 'Ошибка при перегенерации текста')
      } finally {
        localLoading.value = false
        showRegenerateOptions.value = false
      }
    } else {
      // Если целевой уровень не выбран, используем эндпоинт для обычной перегенерации
      const endpoint = API_ENDPOINTS.REGENERATE_TEXT

      try {
        // Добавляем параметры стиля и словарного запаса
        const requestWithStyle = {
          ...requestData,
          vocabulary: regenerateOptions.value.vocabulary || "neutral",
          style: regenerateOptions.value.style || "neutral",
          preserve_style: regenerateOptions.value.preserveStyle !== false
        }

        // Делаем запрос к API бэкенда
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(requestWithStyle)
        })

        const result = await response.json()

        if (result.status === 'success') {
          analysisResult.value = result.data.content
          detectedLevel.value = '' // Сбрасываем определенный уровень, так как текст изменился
        } else {
          throw new Error(result.message || 'Ошибка при перегенерации текста')
        }
      } catch (error) {
        console.error('Ошибка при перегенерации текста:', error)
        store.setError(typeof error === 'object' && error !== null && 'message' in error ?
          (error as Error).message : 'Ошибка при перегенерации текста')
      } finally {
        localLoading.value = false
        showRegenerateOptions.value = false
      }
    }
  } catch (err) {
    console.error('Ошибка при перегенерации текста:', err)
    localLoading.value = false
  }
}

const changeTextLevel = async () => {
  if (!validateInput() || !levelChangeOptions.value.targetLevel) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      target_level: levelChangeOptions.value.targetLevel,
      preserve_style: levelChangeOptions.value.preserveStyle,
      vocabulary: levelChangeOptions.value.vocabulary || "neutral",
      style: levelChangeOptions.value.vocabulary || "neutral"
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.CHANGE_TEXT_LEVEL}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        analysisResult.value = result.data.content
        detectedLevel.value = '' // Сбрасываем определенный уровень, так как текст изменился
      } else {
        throw new Error(result.message || 'Ошибка при изменении уровня текста')
      }
    } catch (error) {
      console.error('Ошибка при изменении уровня текста:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Ошибка при изменении уровня текста')
    } finally {
      localLoading.value = false
      showLevelChangeOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при изменении уровня текста:', err)
    localLoading.value = false
  }
}

const generateQuestions = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent?.trim()
    if (!userText) {
      store.setError('Please enter text for analysis')
      return
    }

    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points to create questions?')) {
            await generateQuestionsWithPoints();
            return;
          } else {
            store.setError('You need to purchase a tariff or use points for generation.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. For generation, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      count: questionsOptions.value.count,
      difficulty: questionsOptions.value.difficulty,
      vocabulary: questionsOptions.value.vocabulary,
      grammar: questionsOptions.value.grammar,
      force: true // Принудительно генерировать новые вопросы без использования кэша
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_QUESTIONS}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      // Отладочная информация
      console.log('Получен ответ от API:', result)
      if (result.status === 'success') {
        // Отладочная информация о полученных данных
        console.log('Успешный ответ от API! Формат данных:', typeof result.data);

        // Проверяем, есть ли в ответе массив вопросов с номером, текстом, ответами и вариантами ответов
        // Формат, который возвращает бэкенд согласно логам
        if (result.data && Array.isArray(result.data) && result.data.length > 0 &&
            result.data[0].number !== undefined &&
            result.data[0].question !== undefined) {
          console.log('Найден массив вопросов в ожидаемом формате:', result.data.slice(0, 2));

          // Преобразуем в нужный формат для отображения
          const formattedQuestions = result.data.map(q => ({
            questionNumber: q.number.toString(),
            question: q.question.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim(),
            options: Array.isArray(q.options) ? q.options : [],
            answer: q.answer ? q.answer.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim() : null
          }));

          console.log('Преобразованные вопросы:', formattedQuestions);
          analysisResult.value = formatQuestionsContent(formattedQuestions);
          localLoading.value = false;
          showQuestionsOptions.value = false;
          return;
        }

        // Проверяем содержимое ответа
        let contentStr = '';
        if (result.data && typeof result.data.content === 'string') {
          contentStr = result.data.content;
        } else if (result.data && typeof result.data === 'object') {
          contentStr = JSON.stringify(result.data);
        }

        console.log('Содержимое ответа:', contentStr.substring(0, 200) + '...');

        // Особая обработка для Markdown-формата с вопросами
        if (contentStr && (contentStr.includes('## Вопрос') || contentStr.includes('## Question'))) {
          console.log('Обнаружен Markdown-формат с вопросами, используем специальный парсер');

          // Сначала пробуем извлечь вопросы напрямую из Markdown-структуры
          const markdownQuestions = extractQuestionsFromMarkdown(contentStr);

          // Проверяем, что у нас есть вопросы и хотя бы у некоторых есть варианты ответов или правильные ответы
          if (markdownQuestions.length > 0 &&
              (markdownQuestions.some(q => q.options && q.options.length > 0) ||
               markdownQuestions.some(q => q.answer))) {
            console.log(`Успешно извлечены ${markdownQuestions.length} вопросов с вариантами/ответами:`, markdownQuestions);
            analysisResult.value = formatQuestionsContent(markdownQuestions);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          } else {
            console.log('Не удалось извлечь варианты ответов или правильные ответы из Markdown-структуры');
          }
        }

        // Сначала пробуем извлечь вопросы напрямую из Markdown/текстового формата
        if (contentStr) {
          const markdownQuestions = extractQuestionsFromMarkdown(contentStr);
          if (markdownQuestions.length > 0) {
            console.log(`Успешно извлечены ${markdownQuestions.length} вопросов из ответа:`, markdownQuestions);
            analysisResult.value = formatQuestionsContent(markdownQuestions);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          }
        }

        // Если бэкенд возвращает данные как чистый текст в формате Markdown
        if (result.data && typeof result.data.content === 'string') {
          const contentStr = result.data.content;
          console.log('Получен текстовый контент, проверяем наличие вопросов');

          // Если не удалось извлечь вопросы из Markdown, используем регулярные выражения
          const questionRegexes = [
            /Question (\d+):\s*([^\n]+)/gi,  // Question 1: Text
            /Вопрос (\d+):\s*([^\n]+)/gi,    // Вопрос 1: Text
            /(\d+)\.\s*([^\n]+)/g           // 1. Text
          ];

          let extractedQuestions: any[] = [];

          for (const regex of questionRegexes) {
            let match: RegExpExecArray | null;
            const matches: Array<{number: string, text: string, fullMatch: string}> = [];
            const regexCopy = new RegExp(regex);
            const textToSearch = contentStr;

            while ((match = regexCopy.exec(textToSearch)) !== null) {
              matches.push({
                number: match[1],
                text: match[2],
                fullMatch: match[0]
              });
            }

            if (matches.length > 0) {
              console.log(`Найдено ${matches.length} вопросов с помощью регулярного выражения ${regex}`);
              extractedQuestions = matches.map(m => ({
                question: m.text,
                questionNumber: m.number
              }));

              // Если нашли вопросы, пробуем извлечь варианты ответов и правильные ответы
              extractedQuestions = extractQuestionDetails(contentStr, extractedQuestions);
              break;
            }
          }

          if (extractedQuestions.length > 0) {
            console.log('Успешно извлечены вопросы из текста:', extractedQuestions);
            analysisResult.value = formatQuestionsContent(extractedQuestions);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          } else {
            // Если не удалось извлечь вопросы через регулярные выражения, просто отображаем контент как есть
            console.log('Не удалось извлечь вопросы, отображаем markdown как есть');
            analysisResult.value = contentStr;
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          }
        }

        // Обрабатываем различные форматы данных
        if (result.data) {
          if (Array.isArray(result.data.content)) {
            // Если содержимое - массив, обрабатываем как вопросы
            console.log('Содержимое - массив из', result.data.content.length, 'элементов');
            analysisResult.value = formatQuestionsContent(result.data.content);
          } else if (typeof result.data.content === 'string') {
            // Если содержимое - строка, пробуем распарсить как JSON
            try {
              const parsedContent = JSON.parse(result.data.content);
              if (Array.isArray(parsedContent)) {
                console.log('Распарсили содержимое как массив из JSON-строки');
                analysisResult.value = formatQuestionsContent(parsedContent);
              } else {
                console.log('Содержимое - строка, но не массив после парсинга');
                analysisResult.value = result.data.content;
              }
            } catch (e) {
              // Если не удалось распарсить как JSON, используем как обычный текст
              console.log('Содержимое - обычная строка (не JSON)');
              analysisResult.value = result.data.content;
            }
          } else if (Array.isArray(result.data)) {
            // Если данные напрямую являются массивом
            console.log('Данные напрямую являются массивом из', result.data.length, 'элементов');
            analysisResult.value = formatQuestionsContent(result.data);
          } else if (result.data.questions) {
            // Если есть поле questions, используем его
            console.log('Найдено поле questions в результате');
            analysisResult.value = formatQuestionsContent(result.data.questions);
          } else {
            // Если ничего не подошло, пробуем использовать data как есть
            console.log('Используем result.data как есть:', typeof result.data);
            analysisResult.value = typeof result.data === 'string' ?
              result.data :
              JSON.stringify(result.data, null, 2);
          }
        } else {
          // Если данных нет, показываем сообщение об ошибке
          analysisResult.value = '# Ошибка\n\nНе удалось получить содержимое';
          console.error('Данные не получены в ответе');
        }
      } else {
        throw new Error(result.message || 'Ошибка при генерации вопросов')
      }
    } catch (error) {
      console.error('Ошибка при генерации вопросов:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Ошибка при генерации вопросов')
    } finally {
      localLoading.value = false
      showQuestionsOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации вопросов:', err)
    localLoading.value = false
  }
}

const generateLessonPlan = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points to create a lesson plan?')) {
            await generateLessonPlanWithPoints();
            return;
          } else {
            store.setError('To generate, you need to purchase a tariff or use points.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. For generation, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Создаем промпт в формате JSON
    const promptData = {
      language: formData.value.language,
      text_content: userText,
      age: lessonPlanOptions.value.age,
      methodology: lessonPlanOptions.value.methodology,
      duration: lessonPlanOptions.value.duration,
      individual_group: lessonPlanOptions.value.individual_group,
      online_offline: lessonPlanOptions.value.online_offline,
      focus: lessonPlanOptions.value.focus,
      level: lessonPlanOptions.value.level
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'lesson_plan', // Используем правильное значение из enum ContentType
      prompt: JSON.stringify(promptData) // Преобразуем данные в строку JSON
    }

    console.log('Отправляем запрос на генерацию плана урока:', requestData)

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_LESSON_PLAN}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Ошибка API:', response.status, errorData);
        throw new Error(`Ошибка API: ${response.status} - ${errorData.detail || JSON.stringify(errorData)}`);
      }

      const result = await response.json()

      if (result.status === 'success') {
        // Добавляем логирование для проверки ответа API
        console.log('Получен ответ API для генерации плана урока:', result);
        console.log('Содержимое ответа API:', result.data);

        // Очищаем контент плана урока от артефактов форматирования
        const cleanedContent = cleanLessonPlanContent(result.data.content);
        analysisResult.value = cleanedContent;

        // Сохраняем оригинальный план урока и устанавливаем флаг
        originalLessonPlan.value = cleanedContent;
        isLessonPlanGenerated.value = true;
      } else {
        throw new Error(result.message || 'Error generating lesson plan')
      }
    } catch (error) {
      console.error('Error generating lesson plan:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating lesson plan')
    } finally {
      localLoading.value = false
      showLessonPlanOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации плана урока:', err)
    localLoading.value = false
  }
}

// Функция для очистки контента плана урока от артефактов форматирования
function cleanLessonPlanContent(content: string): string {
  if (!content) return '';

  // Удаляем слишком длинные последовательности подчеркиваний
  content = content.replace(/_{10,}/g, '_______');

  // Удаляем слишком длинные последовательности дефисов
  content = content.replace(/\-{10,}/g, '-------');

  // Нормализуем длинные пробельные последовательности
  content = content.replace(/\s{3,}/g, '  ');

  // Удаляем непечатаемые символы и прочие артефакты
  content = content.replace(/[^\S\n]{2,}/g, ' ');

  return content;
}

const generateExercises = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points to create exercises?')) {
            await generateExercisesWithPoints();
            return;
          } else {
            store.setError('To generate, you need to purchase a tariff or use points.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. For generation, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Создаем промпт в формате JSON
    const promptData = {
      language: formData.value.language,
      text_content: userText,
      count: exercisesOptions.value.count,
      exercise_type: exercisesOptions.value.type,
      format: exercisesOptions.value.format
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'exercise', // Используем правильное значение из enum ContentType
      prompt: JSON.stringify(promptData) // Преобразуем данные в строку JSON
    }

    console.log('Отправляем запрос на генерацию упражнений:', requestData)

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_EXERCISES}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      console.log('Получен ответ от сервера:', response.status, response.statusText)

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Ошибка API:', response.status, errorData);
        throw new Error(`Ошибка API: ${response.status} - ${errorData.detail || JSON.stringify(errorData)}`);
      }

      const result = await response.json()
      console.log('Результат запроса:', result)

      if (result.status === 'success') {
        analysisResult.value = result.data.content
      } else {
        throw new Error(result.message || 'Error generating exercises')
      }
    } catch (error) {
      console.error('Error generating exercises:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating exercises')
    } finally {
      localLoading.value = false
      showExercisesOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации упражнений:', err)
    localLoading.value = false
  }
}

const generateGame = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для создания игры?')) {
            await generateGameWithPoints();
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

    // Создаем объект с данными для промпта
    const promptData = {
      language: formData.value.language,
      topic: formData.value.topic || 'general',
      text_content: userText,
      game_type: gameOptions.value.type,
      duration: gameOptions.value.duration,
      individual_group: gameOptions.value.format,
      online_offline: gameOptions.value.online_offline,
      age: gameOptions.value.age,
      type: ContentType.GAME
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: ContentType.GAME,
      prompt: JSON.stringify(promptData)
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_GAME}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        analysisResult.value = result.data.content
      } else {
        throw new Error(result.message || 'Error generating game')
      }
    } catch (error) {
      console.error('Error generating game:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating game')
    } finally {
      localLoading.value = false
      showGameOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации игры:', err)
    localLoading.value = false
  }
}

const generateSummaries = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points to create summaries?')) {
            await generateSummariesWithPoints();
            return;
          } else {
            store.setError('To generate, you need to purchase a tariff or use points.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. For generation, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Нормализуем выбранный язык
    const languageMap: Record<string, string> = {
      'english': 'english',
      'spanish': 'spanish',
      'french': 'french',
      'german': 'german',
      'italian': 'italian',
      'chinese': 'chinese',
      'japanese': 'japanese',
      'korean': 'korean',
      'turkish': 'turkish',
      'russian': 'russian',
      'arabic': 'arabic'
    };

    // Определяем, какой эндпоинт использовать в зависимости от выбранного режима
    const endpoint = summaryOptions.value.mode === 'multiple'
      ? API_ENDPOINTS.GENERATE_SUMMARIES
      : API_ENDPOINTS.GENERATE_SUMMARY;

    // Создаем запрос в формате, ожидаемом API
    const requestData: any = {
      user_id: store.user.id,
      language: languageMap[formData.value.language] || formData.value.language,
      text_content: userText
    }

    // Только для единичного саммари добавляем level
    if (summaryOptions.value.mode === 'single') {
      requestData.level = summaryOptions.value.level;
    }

    console.log(`Отправляемый запрос на генерацию саммари (режим: ${summaryOptions.value.mode}):`, JSON.stringify(requestData, null, 2));

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ для саммари:', result.data);

        // Устанавливаем контент напрямую из ответа сервера
        if (result.data.content) {
          analysisResult.value = result.data.content;
        } else if (result.data.summary) {
          analysisResult.value = result.data.summary;
        } else if (result.data.summaries) {
          analysisResult.value = result.data.summaries;
        } else if (result.data && typeof result.data === 'object') {
          // Проверяем, является ли result.data объектом с полями user_id, language, original_text, summaries
          if (result.data.user_id !== undefined &&
              result.data.language !== undefined &&
              result.data.original_text !== undefined &&
              result.data.summaries !== undefined) {
            console.log('Обнаружен объект с полем summaries:', result.data);
            analysisResult.value = result.data.summaries;
          } else {
            // Если формат ответа неизвестен, но это объект, пробуем найти любое текстовое поле
            const textFields = ['summaries', 'content', 'summary', 'text', 'result'];
            let foundContent = null;

            for (const field of textFields) {
              if (result.data[field] && typeof result.data[field] === 'string') {
                console.log(`Найдено текстовое поле ${field} в ответе:`, result.data[field].substring(0, 100) + '...');
                foundContent = result.data[field];
                break;
              }
            }

            if (foundContent) {
              analysisResult.value = foundContent;
            } else {
              // Если не нашли текстовое поле, форматируем JSON в читаемый вид
              const jsonStr = JSON.stringify(result.data, null, 2);
              analysisResult.value = '# Результат анализа\n\n```json\n' + jsonStr + '\n```\n\nПожалуйста, свяжитесь с поддержкой, если вы видите этот текст вместо ожидаемого саммари.';
            }
          }
        } else {
          // Если контент не найден, используем все данные как есть
          const jsonStr = JSON.stringify(result.data, null, 2);
          analysisResult.value = '# Результат анализа\n\n```json\n' + jsonStr + '\n```\n\nПожалуйста, свяжитесь с поддержкой, если вы видите этот текст вместо ожидаемого саммари.';
        }
      } else {
        throw new Error(result.message || 'Error generating summary')
      }
    } catch (error) {
      console.error('Error generating summary:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating summary')
    } finally {
      localLoading.value = false
      showSummaryOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации саммари:', err)
    localLoading.value = false
  }
}

const generateTitles = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points to create titles?')) {
            await generateTitlesWithPoints();
            return;
          } else {
            store.setError('To generate, you need to purchase a tariff or use points.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. For generation, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Нормализуем выбранный язык
    const languageMap: Record<string, string> = {
      'english': 'english',
      'spanish': 'spanish',
      'french': 'french',
      'german': 'german',
      'italian': 'italian',
      'chinese': 'chinese',
      'japanese': 'japanese',
      'korean': 'korean',
      'turkish': 'turkish',
      'russian': 'russian',
      'arabic': 'arabic'
    };

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: languageMap[formData.value.language] || formData.value.language,
      text_content: userText,
      count: titlesOptions.value.count,
      force: true // Принудительно игнорируем кэш для получения свежих заголовков
    }

    console.log('Отправляемый запрос на генерацию заголовков:', JSON.stringify(requestData, null, 2));

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_TITLES}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`Ошибка при запросе: ${response.status} ${response.statusText}`);
      }

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ для заголовков:', result.data);

        // Используем titles_markdown, если он есть, иначе используем content
        analysisResult.value = result.data.titles_markdown || result.data.content;

        // Сохраняем информацию о заголовках
        // В новом формате: titles и recommended_index напрямую в data
        // В старом формате: в data.metadata
        const titlesArray = result.data.titles ||
                           (result.data.metadata ? result.data.metadata.titles : []);
        const recIndex = result.data.recommended_index !== undefined ?
                        result.data.recommended_index :
                        (result.data.metadata ? result.data.metadata.recommended_index : 0);

        console.log('Заголовки:', titlesArray);
        console.log('Рекомендуемый индекс:', recIndex);
      } else {
        throw new Error(result.message || 'Error generating titles')
      }
    } catch (error) {
      console.error('Error generating titles:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating titles')
    } finally {
      localLoading.value = false
      showTitlesOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации заголовков:', err)
    localLoading.value = false
  }
}

const generateComprehensionTest = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

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
          if (confirm('You don\'t have an active tariff. Would you like to use 8 points to create a comprehension test?')) {
            await generateComprehensionTestWithPoints();
            return;
          } else {
            store.setError('To generate, you need to purchase a tariff or use points.');
            return;
          }
        } else {
          store.setError('You don\'t have an active tariff. For generation, you need to purchase a tariff or add points.');
          return;
        }
      }
      throw limitError;
    }

    // Нормализуем выбранный язык
    const languageMap: Record<string, string> = {
      'english': 'english',
      'spanish': 'spanish',
      'french': 'french',
      'german': 'german',
      'italian': 'italian',
      'chinese': 'chinese',
      'japanese': 'japanese',
      'korean': 'korean',
      'turkish': 'turkish',
      'russian': 'russian',
      'arabic': 'arabic'
    };

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: languageMap[formData.value.language] || formData.value.language,
      text_content: userText,
      question_count: comprehensionTestOptions.value.question_count,
      difficulty: comprehensionTestOptions.value.difficulty,
      force: true // Всегда игнорируем кэш для генерации тестов на понимание
    }

    console.log('Отправляемый запрос на генерацию теста:', JSON.stringify(requestData, null, 2));

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_COMPREHENSION_TEST}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ для теста на понимание:', result.data);

        // Получаем текстовый контент
        const contentStr = result.data.content || '';

        // Проверяем, содержит ли контент Markdown-структуру с вопросами
        if (contentStr && (
            contentStr.includes('## Вопрос') ||
            contentStr.includes('## Question') ||
            contentStr.includes('True/False') ||
            contentStr.includes('Multiple-choice')
           )) {
          console.log('Обнаружена Markdown-структура с тестом на понимание');

          // Пробуем извлечь вопросы из Markdown-структуры
          const markdownQuestions = extractQuestionsFromMarkdown(contentStr);

          // Если нашли вопросы с вариантами или ответами, форматируем их
          if (markdownQuestions.length > 0 &&
             (markdownQuestions.some(q => q.options && q.options.length > 0) ||
              markdownQuestions.some(q => q.answer))) {
            console.log(`Успешно извлечены ${markdownQuestions.length} вопросов с вариантами/ответами:`, markdownQuestions);
            analysisResult.value = formatQuestionsContent(markdownQuestions);
          } else {
            // Если не удалось извлечь структурированные вопросы, используем контент как есть
            console.log('Не удалось извлечь структурированные вопросы, используем Markdown как есть');
            analysisResult.value = contentStr;
          }
        } else {
          // Если контент не содержит Markdown-структуру, используем его как есть
          analysisResult.value = contentStr;
        }
      } else {
        throw new Error(result.message || 'Error generating comprehension test')
      }
    } catch (error) {
      console.error('Error generating comprehension test:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating comprehension test')
    } finally {
      localLoading.value = false
      showComprehensionTestOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации теста на понимание:', err)
    localLoading.value = false
  }
}

// Валидация ввода
const validateInput = () => {
  if (!formData.value.textContent.trim()) {
    store.setError('Введите текст для анализа')
    return false
  }
  if (!formData.value.language) {
    store.setError('Выберите язык')
    return false
  }
  return true
}

// При изменении языка сбрасываем выбранный уровень в опциях, если он не подходит для нового языка
watch(() => formData.value.language, (newLanguage) => {
  if (levelChangeOptions.value.targetLevel) {
    const newLevels = getLevelsByLanguage(newLanguage)
    const levelExists = newLevels.some(level => level.id === levelChangeOptions.value.targetLevel)
    if (!levelExists) {
      levelChangeOptions.value.targetLevel = ''
    }
  }
  const levels = getLevelsByLanguage(newLanguage)
  if (levels && levels.length > 0) {
    summaryOptions.value.level = levels[0].id
  }
})

// Очистка ошибки
// Метод для определения уровня текста за баллы
const detectTextLevelWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    detectedLevel.value = '' // Сбрасываем определенный уровень
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.DETECT_TEXT_LEVEL}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ для определения уровня текста за баллы:', result.data);

        // Устанавливаем результат анализа
        analysisResult.value = result.data.content;

        // Используем определенный уровень из ответа API
        if (result.data.detected_level && result.data.detected_level !== 'Unknown') {
          detectedLevel.value = result.data.detected_level;
          console.log(`Установлен уровень текста: ${detectedLevel.value}`);
        } else {
          // Если API не вернул уровень, пытаемся извлечь его из контента
          const levelMatch = analysisResult.value && analysisResult.value.match(/[A-C][1-2][-+]?|ТЭУ|ТБУ|ТРКИ-[1-4]|HSK\s*[1-6]|N[1-5]|TOPIK\s*[1-6]|Beginner|Elementary|Intermediate|Upper[- ]?Intermediate|Advanced|Proficient|Superior|Native/i);
          if (levelMatch) {
            detectedLevel.value = levelMatch[0];
            console.log(`Извлечен уровень текста из контента: ${detectedLevel.value}`);
          }
        }
      } else {
        throw new Error(result.message || 'Ошибка при определении уровня текста')
      }
    } catch (error) {
      console.error('Error determining text level with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error determining text level')
    } finally {
      localLoading.value = false
    }
  } catch (err) {
    console.error('Error determining text level with points:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Error determining text level with points')
  }
}

// Метод для перегенерации текста за баллы
const regenerateTextWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем базовый запрос
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      vocabulary: regenerateOptions.value.vocabulary,
      style: regenerateOptions.value.style,
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    // Если выбран целевой уровень, добавляем его в запрос
    if (regenerateOptions.value.targetLevel) {
      // Используем оператор расширения для создания нового объекта с дополнительным полем
      const requestWithLevel = {
        ...requestData,
        target_level: regenerateOptions.value.targetLevel
      }

      // Определяем эндпоинт для запроса с уровнем
      const endpoint = API_ENDPOINTS.CHANGE_TEXT_LEVEL

      try {
        // Делаем запрос к API бэкенда
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(requestWithLevel)
        })

        const result = await response.json()

        if (result.status === 'success') {
          analysisResult.value = result.data.content
          detectedLevel.value = '' // Сбрасываем определенный уровень, так как текст изменился
        } else {
          throw new Error(result.message || 'Ошибка при перегенерации текста')
        }
      } catch (error) {
        console.error('Ошибка при перегенерации текста за баллы:', error)
        store.setError(typeof error === 'object' && error !== null && 'message' in error ?
          (error as Error).message : 'Ошибка при перегенерации текста')
      } finally {
        localLoading.value = false
        showRegenerateOptions.value = false
      }
    } else {
      // Если целевой уровень не выбран, используем эндпоинт для обычной перегенерации
      const endpoint = API_ENDPOINTS.REGENERATE_TEXT

      try {
        // Добавляем параметры стиля и словарного запаса
        const requestWithStyle = {
          ...requestData,
          vocabulary: regenerateOptions.value.vocabulary || "neutral",
          style: regenerateOptions.value.style || "neutral",
          preserve_style: regenerateOptions.value.preserveStyle !== false
        }

        // Делаем запрос к API бэкенда
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(requestWithStyle)
        })

        const result = await response.json()

        if (result.status === 'success') {
          analysisResult.value = result.data.content
          detectedLevel.value = '' // Сбрасываем определенный уровень, так как текст изменился
        } else {
          throw new Error(result.message || 'Ошибка при перегенерации текста')
        }
      } catch (error) {
        console.error('Ошибка при перегенерации текста за баллы:', error)
        store.setError(typeof error === 'object' && error !== null && 'message' in error ?
          (error as Error).message : 'Ошибка при перегенерации текста')
      } finally {
        localLoading.value = false
        showRegenerateOptions.value = false
      }
    }
  } catch (err) {
    console.error('Ошибка при перегенерации текста за баллы:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Ошибка при перегенерации текста за баллы')
  }
}

// Метод для изменения уровня текста за баллы
const changeTextLevelWithPoints = async () => {
  if (!validateInput() || !levelChangeOptions.value.targetLevel) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      target_level: levelChangeOptions.value.targetLevel,
      preserve_style: levelChangeOptions.value.preserveStyle,
      vocabulary: levelChangeOptions.value.vocabulary || "neutral",
      style: levelChangeOptions.value.vocabulary || "neutral",
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.CHANGE_TEXT_LEVEL}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        analysisResult.value = result.data.content
        detectedLevel.value = '' // Сбрасываем определенный уровень, так как текст изменился
      } else {
        throw new Error(result.message || 'Ошибка при изменении уровня текста')
      }
    } catch (error) {
      console.error('Ошибка при изменении уровня текста за баллы:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Ошибка при изменении уровня текста')
    } finally {
      localLoading.value = false
      showLevelChangeOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при изменении уровня текста за баллы:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Ошибка при изменении уровня текста за баллы')
  }
}

// Метод для генерации вопросов за баллы
const generateQuestionsWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent?.trim()
    if (!userText) {
      store.setError('Please enter text for analysis')
      return
    }

    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      count: questionsOptions.value.count,
      difficulty: questionsOptions.value.difficulty,
      vocabulary: questionsOptions.value.vocabulary,
      grammar: questionsOptions.value.grammar,
      force: true, // Принудительно генерировать новые вопросы без использования кэша
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_QUESTIONS}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      // Отладочная информация
      console.log('Получен ответ от API (за баллы):', result)
      if (result.status === 'success') {
        // Отладочная информация о полученных данных
        console.log('Успешный ответ от API! Формат данных:', typeof result.data);

        // Проверяем, есть ли в ответе массив вопросов с номером, текстом, ответами и вариантами ответов
        // Формат, который возвращает бэкенд согласно логам
        if (result.data && Array.isArray(result.data) && result.data.length > 0 &&
            result.data[0].number !== undefined &&
            result.data[0].question !== undefined) {
          console.log('Найден массив вопросов в ожидаемом формате:', result.data.slice(0, 2));

          // Преобразуем в нужный формат для отображения
          const formattedQuestions = result.data.map(q => ({
            questionNumber: q.number.toString(),
            question: q.question.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim(),
            options: Array.isArray(q.options) ? q.options : [],
            answer: q.answer ? q.answer.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim() : null
          }));

          console.log('Преобразованные вопросы:', formattedQuestions);
          analysisResult.value = formatQuestionsContent(formattedQuestions);
          localLoading.value = false;
          showQuestionsOptions.value = false;
          return;
        }

        // Проверяем содержимое ответа
        let contentStr = '';
        if (result.data && typeof result.data.content === 'string') {
          contentStr = result.data.content;
        } else if (result.data && typeof result.data === 'object') {
          // Проверяем, является ли result.data массивом вопросов в формате скриншота
          if (Array.isArray(result.data) && result.data.length > 0 &&
              result.data[0].number !== undefined && result.data[0].question !== undefined) {
            console.log('Обнаружен массив вопросов в формате скриншота:', result.data.slice(0, 2));
            analysisResult.value = formatQuestionsContent(result.data);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          }
          contentStr = JSON.stringify(result.data);
        }

        console.log('Содержимое ответа:', contentStr.substring(0, 200) + '...');

        // Проверяем, является ли contentStr строкой JSON с вопросами
        if (contentStr && (contentStr.startsWith('[{') || contentStr.startsWith('{"questions"'))) {
          console.log('Обнаружена строка JSON с вопросами в ответе API');
          try {
            // Пробуем распарсить JSON
            const parsedData = JSON.parse(contentStr);
            if (parsedData) {
              if (Array.isArray(parsedData) && parsedData.length > 0 &&
                  parsedData[0].number !== undefined && parsedData[0].question !== undefined) {
                // Это массив вопросов
                console.log('Распарсили массив вопросов из JSON строки:', parsedData.slice(0, 2));
                analysisResult.value = formatQuestionsContent(parsedData);
                localLoading.value = false;
                showQuestionsOptions.value = false;
                return;
              } else if (parsedData.questions && Array.isArray(parsedData.questions)) {
                // Это объект с массивом вопросов
                console.log('Распарсили объект с массивом вопросов из JSON строки:', parsedData.questions.slice(0, 2));
                analysisResult.value = formatQuestionsContent(parsedData.questions);
                localLoading.value = false;
                showQuestionsOptions.value = false;
                return;
              }
            }
          } catch (e) {
            console.log('Ошибка при парсинге JSON строки из ответа API:', e);
          }
        }

        // Особая обработка для Markdown-формата с вопросами
        if (contentStr && (contentStr.includes('## Вопрос') || contentStr.includes('## Question'))) {
          console.log('Обнаружен Markdown-формат с вопросами, используем специальный парсер');

          // Сначала пробуем извлечь вопросы напрямую из Markdown-структуры
          const markdownQuestions = extractQuestionsFromMarkdown(contentStr);

          // Проверяем, что у нас есть вопросы и хотя бы у некоторых есть варианты ответов или правильные ответы
          if (markdownQuestions.length > 0 &&
              (markdownQuestions.some(q => q.options && q.options.length > 0) ||
               markdownQuestions.some(q => q.answer))) {
            console.log(`Успешно извлечены ${markdownQuestions.length} вопросов с вариантами/ответами:`, markdownQuestions);
            analysisResult.value = formatQuestionsContent(markdownQuestions);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          } else {
            console.log('Не удалось извлечь варианты ответов или правильные ответы из Markdown-структуры');
          }
        }

        // Сначала пробуем извлечь вопросы напрямую из Markdown/текстового формата
        if (contentStr) {
          const markdownQuestions = extractQuestionsFromMarkdown(contentStr);
          if (markdownQuestions.length > 0) {
            console.log(`Успешно извлечены ${markdownQuestions.length} вопросов из ответа:`, markdownQuestions);
            analysisResult.value = formatQuestionsContent(markdownQuestions);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          }
        }

        // Если бэкенд возвращает данные как чистый текст в формате Markdown
        if (result.data && typeof result.data.content === 'string') {
          const contentStr = result.data.content;
          console.log('Получен текстовый контент, проверяем наличие вопросов');

          // Если не удалось извлечь вопросы из Markdown, используем регулярные выражения
          const questionRegexes = [
            /Question (\d+):\s*([^\n]+)/gi,  // Question 1: Text
            /Вопрос (\d+):\s*([^\n]+)/gi,    // Вопрос 1: Text
            /(\d+)\.\s*([^\n]+)/g           // 1. Text
          ];

          let extractedQuestions: any[] = [];

          for (const regex of questionRegexes) {
            let match: RegExpExecArray | null;
            const matches: Array<{number: string, text: string, fullMatch: string}> = [];
            const regexCopy = new RegExp(regex);
            const textToSearch = contentStr;

            while ((match = regexCopy.exec(textToSearch)) !== null) {
              matches.push({
                number: match[1],
                text: match[2],
                fullMatch: match[0]
              });
            }

            if (matches.length > 0) {
              extractedQuestions = matches.map(m => ({
                questionNumber: m.number,
                question: m.text,
                options: [],
                answer: null
              }));
              break;
            }
          }

          if (extractedQuestions.length > 0) {
            console.log('Успешно извлечены вопросы из текста:', extractedQuestions);
            analysisResult.value = formatQuestionsContent(extractedQuestions);
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          } else {
            // Если не удалось извлечь вопросы через регулярные выражения, просто отображаем контент как есть
            console.log('Не удалось извлечь вопросы, отображаем markdown как есть');
            analysisResult.value = contentStr;
            localLoading.value = false;
            showQuestionsOptions.value = false;
            return;
          }
        }

        // Если ничего не сработало, проверяем формат данных еще раз
        if (typeof result.data === 'string') {
          // Если это строка, отображаем как есть
          analysisResult.value = result.data;
        } else if (Array.isArray(result.data) && result.data.length > 0) {
          // Если это массив, пробуем форматировать как вопросы
          console.log('Последняя попытка форматирования массива данных как вопросов');
          analysisResult.value = formatQuestionsContent(result.data);
        } else if (typeof result.data === 'object' && result.data !== null) {
          // Если это объект, проверяем наличие полей questions или content
          if (result.data.questions && Array.isArray(result.data.questions)) {
            console.log('Последняя попытка форматирования объекта с полем questions');
            analysisResult.value = formatQuestionsContent(result.data.questions);
          } else if (result.data.content) {
            console.log('Используем поле content из объекта');
            analysisResult.value = typeof result.data.content === 'string' ?
              result.data.content :
              formatQuestionsContent([result.data.content]);
          } else {
            // Если ничего не подошло, преобразуем в markdown
            const jsonStr = JSON.stringify(result.data, null, 2);
            analysisResult.value = '# Результат анализа\n\nПолучены данные в формате JSON:\n\n```json\n' + jsonStr + '\n```\n\nПожалуйста, свяжитесь с поддержкой, если вы видите этот текст вместо ожидаемых вопросов.';
          }
        } else {
          // Если ничего не подошло, отображаем сообщение об ошибке
          analysisResult.value = '# Ошибка форматирования\n\nНе удалось корректно отобразить результат. Пожалуйста, попробуйте еще раз или свяжитесь с поддержкой.';
        }
      } else {
        throw new Error(result.message || 'Ошибка при генерации вопросов')
      }
    } catch (error) {
      console.error('Ошибка при генерации вопросов за баллы:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Ошибка при генерации вопросов')
    } finally {
      localLoading.value = false
      showQuestionsOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации вопросов за баллы:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Ошибка при генерации вопросов за баллы')
  }
}

// Метод для генерации саммари за баллы
const generateSummariesWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    // Если выбран режим "multiple", добавляем соответствующий параметр
    if (summaryOptions.value.mode === 'multiple') {
      Object.assign(requestData, { mode: 'multiple' })
    } else {
      // Если выбран режим "single", добавляем уровень
      if (summaryOptions.value.level) {
        Object.assign(requestData, { level: summaryOptions.value.level })
      }
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_SUMMARIES}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ для саммари за баллы:', result.data);

        // Если получен массив саммари
        if (Array.isArray(result.data)) {
          // Форматируем массив саммари в Markdown
          const formattedSummaries = result.data.map((summary, index) => {
            const lengthLabel = index === 0 ? 'Короткое' : (index === 1 ? 'Среднее' : 'Полное')
            return `## ${lengthLabel} саммари\n\n${summary}`
          }).join('\n\n---\n\n')

          analysisResult.value = formattedSummaries
        } else if (result.data && typeof result.data.content === 'string') {
          // Если получен одиночный саммари
          analysisResult.value = result.data.content
        } else if (result.data && typeof result.data.summaries === 'string') {
          // Если получен саммари в поле summaries (как в примере)
          analysisResult.value = result.data.summaries
        } else if (result.data && typeof result.data === 'object') {
          // Проверяем, является ли result.data объектом с полями user_id, language, original_text, summaries
          if (result.data.user_id !== undefined &&
              result.data.language !== undefined &&
              result.data.original_text !== undefined &&
              result.data.summaries !== undefined) {
            console.log('Обнаружен объект с полем summaries:', result.data);
            analysisResult.value = result.data.summaries;
          } else {
            // Если формат ответа неизвестен, но это объект, пробуем найти любое текстовое поле
            const textFields = ['summaries', 'content', 'summary', 'text', 'result'];
            let foundContent = null;

            for (const field of textFields) {
              if (result.data[field] && typeof result.data[field] === 'string') {
                console.log(`Найдено текстовое поле ${field} в ответе:`, result.data[field].substring(0, 100) + '...');
                foundContent = result.data[field];
                break;
              }
            }

            if (foundContent) {
              analysisResult.value = foundContent;
            } else {
              // Если не нашли текстовое поле, форматируем JSON в читаемый вид
              const jsonStr = JSON.stringify(result.data, null, 2);
              analysisResult.value = '# Результат анализа\n\n```json\n' + jsonStr + '\n```\n\nПожалуйста, свяжитесь с поддержкой, если вы видите этот текст вместо ожидаемого саммари.';
            }
          }
        } else {
          // Если формат ответа неизвестен
          const jsonStr = JSON.stringify(result.data, null, 2);
          analysisResult.value = '# Результат анализа\n\n```json\n' + jsonStr + '\n```\n\nПожалуйста, свяжитесь с поддержкой, если вы видите этот текст вместо ожидаемого саммари.';
        }
      } else {
        throw new Error(result.message || 'Error generating summary')
      }
    } catch (error) {
      console.error('Error generating summary with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating summary')
    } finally {
      localLoading.value = false
      showSummaryOptions.value = false
    }
  } catch (err) {
    console.error('Error generating summary with points:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Error generating summary with points')
  }
}

// Метод для генерации заголовков за баллы
const generateTitlesWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Нормализуем выбранный язык
    const languageMap: Record<string, string> = {
      'english': 'english',
      'spanish': 'spanish',
      'french': 'french',
      'german': 'german',
      'italian': 'italian',
      'chinese': 'chinese',
      'japanese': 'japanese',
      'korean': 'korean',
      'turkish': 'turkish',
      'russian': 'russian',
      'arabic': 'arabic'
    };

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: languageMap[formData.value.language] || formData.value.language,
      text_content: userText,
      count: titlesOptions.value.count,
      force: true, // Принудительно игнорируем кэш для получения свежих заголовков
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    console.log('Отправляемый запрос на генерацию заголовков за баллы:', JSON.stringify(requestData, null, 2));

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_TITLES}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error(`Ошибка при запросе: ${response.status} ${response.statusText}`);
      }

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ от API (заголовки за баллы):', result);

        // Проверяем, есть ли в ответе массив заголовков
        if (result.data && Array.isArray(result.data.titles)) {
          // Форматируем заголовки в Markdown
          const titles = result.data.titles;
          const recommendedIndex = result.data.recommended_index || 0;

          const formattedTitles = titles.map((title, index) => {
            const isRecommended = index === recommendedIndex;
            return `${index + 1}. ${title} ${isRecommended ? '✅ (рекомендуемый)' : ''}`;
          }).join('\n\n');

          analysisResult.value = `## Сгенерированные заголовки\n\n${formattedTitles}`;
        } else if (result.data && typeof result.data.content === 'string') {
          // Если получен контент в виде строки
          analysisResult.value = result.data.content;
        } else {
          // Если формат ответа неизвестен
          analysisResult.value = JSON.stringify(result.data, null, 2);
        }
      } else {
        throw new Error(result.message || 'Error generating titles')
      }
    } catch (error) {
      console.error('Error generating titles with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating titles')
    } finally {
      localLoading.value = false
      showTitlesOptions.value = false
    }
  } catch (err) {
    console.error('Error generating titles with points:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Error generating titles with points')
  }
}

// Метод для генерации теста на понимание за баллы
const generateComprehensionTestWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      language: formData.value.language,
      text_content: userText,
      question_count: comprehensionTestOptions.value.question_count,
      difficulty: comprehensionTestOptions.value.difficulty,
      force: true, // Принудительно игнорируем кэш для получения свежего теста
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_COMPREHENSION_TEST}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ от API (тест на понимание за баллы):', result);

        // Проверяем содержимое ответа
        if (result.data && typeof result.data.content === 'string') {
          const contentStr = result.data.content;

          // Пробуем извлечь вопросы из Markdown-структуры
          const markdownQuestions = extractQuestionsFromMarkdown(contentStr);

          // Если нашли вопросы с вариантами или ответами, форматируем их
          if (markdownQuestions.length > 0 &&
             (markdownQuestions.some(q => q.options && q.options.length > 0) ||
              markdownQuestions.some(q => q.answer))) {
            console.log(`Успешно извлечены ${markdownQuestions.length} вопросов с вариантами/ответами:`, markdownQuestions);
            analysisResult.value = formatQuestionsContent(markdownQuestions);
          } else {
            // Если не удалось извлечь структурированные вопросы, используем контент как есть
            console.log('Не удалось извлечь структурированные вопросы, используем Markdown как есть');
            analysisResult.value = contentStr;
          }
        } else {
          // Если формат ответа неизвестен
          analysisResult.value = JSON.stringify(result.data, null, 2);
        }
      } else {
        throw new Error(result.message || 'Error generating comprehension test')
      }
    } catch (error) {
      console.error('Error generating comprehension test with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating comprehension test')
    } finally {
      localLoading.value = false
      showComprehensionTestOptions.value = false
    }
  } catch (err) {
    console.error('Error generating comprehension test with points:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Error generating comprehension test with points')
  }
}

// Метод для генерации плана урока за баллы
const generateLessonPlanWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем промпт в формате JSON
    const promptData = {
      language: formData.value.language,
      text_content: userText,
      age: lessonPlanOptions.value.age,
      methodology: lessonPlanOptions.value.methodology,
      duration: lessonPlanOptions.value.duration,
      individual_group: lessonPlanOptions.value.individual_group,
      online_offline: lessonPlanOptions.value.online_offline,
      focus: lessonPlanOptions.value.focus,
      level: lessonPlanOptions.value.level
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'lesson_plan', // Используем правильное значение из enum ContentType
      prompt: JSON.stringify(promptData), // Преобразуем данные в строку JSON
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    console.log('Отправляем запрос на генерацию плана урока за баллы:', requestData)

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_LESSON_PLAN}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Ошибка API:', response.status, errorData);
        throw new Error(`Ошибка API: ${response.status} - ${errorData.detail || JSON.stringify(errorData)}`);
      }

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ от API (план урока за баллы):', result);

        // Очищаем контент плана урока от артефактов форматирования
        const cleanedContent = cleanLessonPlanContent(result.data.content);
        analysisResult.value = cleanedContent;

        // Сохраняем оригинальный план урока и устанавливаем флаг
        originalLessonPlan.value = cleanedContent;
        isLessonPlanGenerated.value = true;
      } else {
        throw new Error(result.message || 'Error generating lesson plan')
      }
    } catch (error) {
      console.error('Error generating lesson plan with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating lesson plan')
    } finally {
      localLoading.value = false
      showLessonPlanOptions.value = false
    }
  } catch (err) {
    console.error('Error generating lesson plan with points:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Error generating lesson plan with points')
  }
}

// Метод для генерации упражнений за баллы
const generateExercisesWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'exercise',  // Используем тип ContentType.EXERCISE
      prompt: JSON.stringify({
        language: formData.value.language,
        text_content: userText,
        exerciseType: exercisesOptions.value.type,
        format: exercisesOptions.value.format
      }),
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_EXERCISES}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ от API (упражнения за баллы):', result);

        // Проверяем содержимое ответа
        if (result.data && typeof result.data.content === 'string') {
          analysisResult.value = result.data.content;
        } else {
          // Если формат ответа неизвестен
          analysisResult.value = JSON.stringify(result.data, null, 2);
        }
      } else {
        throw new Error(result.message || 'Error generating exercises')
      }
    } catch (error) {
      console.error('Error generating exercises with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating exercises')
    } finally {
      localLoading.value = false
      showExercisesOptions.value = false
    }
  } catch (err) {
    console.error('Ошибка при генерации упражнений за баллы:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Ошибка при генерации упражнений за баллы')
  }
}

// Метод для генерации игры за баллы
const generateGameWithPoints = async () => {
  if (!validateInput()) return

  try {
    analysisResult.value = null
    store.clearError()

    localLoading.value = true

    // Получаем текст пользователя
    const userText = formData.value.textContent.trim()

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Проверяем возможность генерации за баллы
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.TEXT_ANALYSIS, 8)
    if (!canGenerate) {
      throw new Error('Insufficient points for generation. 8 points required.')
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'game',  // Используем тип ContentType.GAME
      prompt: JSON.stringify({
        language: formData.value.language,
        text_content: userText,
        gameType: gameOptions.value.type,
        format: gameOptions.value.format,
        age: gameOptions.value.age
      }),
      with_points: true,
      skip_tariff_check: true,
      skip_limits: true
    }

    try {
      // Делаем запрос к API бэкенда
      const response = await fetch(`${API_ENDPOINTS.GENERATE_GAME}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      const result = await response.json()

      if (result.status === 'success') {
        console.log('Получен ответ от API (игра за баллы):', result);

        // Проверяем содержимое ответа
        if (result.data && typeof result.data.content === 'string') {
          analysisResult.value = result.data.content;
        } else {
          // Если формат ответа неизвестен
          analysisResult.value = JSON.stringify(result.data, null, 2);
        }
      } else {
        throw new Error(result.message || 'Error generating game')
      }
    } catch (error) {
      console.error('Error generating game with points:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error generating game')
    } finally {
      localLoading.value = false
      showGameOptions.value = false
    }
  } catch (err) {
    console.error('Error generating game with points:', err)
    localLoading.value = false
    store.setError(typeof err === 'object' && err !== null && 'message' in err ?
      (err as Error).message : 'Error generating game with points')
  }
}

const clearError = () => {
  store.clearError()
}

// Копирование в буфер обмена
const copyToClipboard = async () => {
  if (analysisResult.value) {
    try {
      await navigator.clipboard.writeText(analysisResult.value)
    } catch (err) {
      console.error('Не удалось скопировать текст:', err)
    }
  }
}

// Вспомогательная функция для форматирования вопросов в markdown строку
function formatQuestionsContent(questions: any[]): string {
  if (!Array.isArray(questions) || questions.length === 0) {
    return '# Анализ текста\n\n**Вопросы не найдены**\n\nНе удалось создать вопросы по этому тексту. Пожалуйста, попробуйте другой текст или измените параметры запроса.';
  }

  // Отладочное логирование всей структуры вопросов
  console.log("Полная структура вопросов:", JSON.stringify(questions, null, 2));

  // Проверяем, является ли входной объект строкой JSON
  if (questions.length === 1 && typeof questions[0] === 'string') {
    try {
      // Проверяем, содержит ли строка JSON-подобную структуру
      const jsonPattern = /^\s*\{\s*"questions"\s*:/;
      const jsonArrayPattern = /^\s*\[\s*\{\s*"number"\s*:/;

      if (jsonPattern.test(questions[0]) || jsonArrayPattern.test(questions[0])) {
        console.log("Обнаружена JSON-подобная структура, пробуем распарсить");

        // Пытаемся распарсить JSON
        const parsedData = JSON.parse(questions[0]);
        if (parsedData) {
          console.log("Успешно распарсили JSON строку в объект:", parsedData);

          // Проверяем, есть ли в объекте поле questions
          if (parsedData.questions && Array.isArray(parsedData.questions)) {
            console.log("Найдено поле questions в JSON объекте");
            return formatQuestionsContent(parsedData.questions);
          }

          // Проверяем, есть ли в объекте поле markdown_content
          if (parsedData.markdown_content) {
            console.log("Найдено поле markdown_content в JSON объекте");
            return formatQuestionsContent([parsedData]);
          }

          // Если объект сам является массивом вопросов
          if (Array.isArray(parsedData) && parsedData.length > 0 &&
              (parsedData[0].number !== undefined || parsedData[0].question)) {
            console.log("JSON объект является массивом вопросов");
            return formatQuestionsContent(parsedData);
          }

          // Если объект сам является вопросом
          if (parsedData.question || parsedData.questionText) {
            console.log("JSON объект является вопросом");
            return formatQuestionsContent([parsedData]);
          }
        }
      } else {
        // Если строка не похожа на JSON, проверяем, содержит ли она уже отформатированные вопросы
        if (questions[0].includes('**Вопрос') || questions[0].includes('# Вопрос')) {
          console.log("Строка уже содержит отформатированные вопросы");
          return questions[0];
        }
      }
    } catch (e) {
      console.log("Ошибка при парсинге JSON строки:", e);
    }
  }

  // Проверяем, есть ли в данных специальный формат с markdown_content и meta
  if (questions.length === 1 && questions[0].markdown_content && questions[0].meta) {
    console.log("Обнаружен специальный формат с markdown_content и meta");

    // Извлекаем данные из специального формата
    const { markdown_content, meta, questions: questionsArray } = questions[0];

    // Если есть массив вопросов внутри, используем его для форматирования
    if (Array.isArray(questionsArray) && questionsArray.length > 0) {
      console.log("Найден массив вопросов внутри специального формата, форматируем его");

      // Создаем весь текст одним блоком
      let markdown = '# Вопросы по тексту\n\n';

      // Добавляем информацию о языке и сложности, если они есть
      if (meta && meta.language) {
        markdown = `# Вопросы по тексту (${meta.language})`;
        if (meta.difficulty) {
          markdown += ` - ${meta.difficulty} уровень`;
        }
        markdown += '\n\n';
      }

      // Форматируем каждый вопрос
      for (const question of questionsArray) {
        if (!question.number || !question.question) continue;

        // Добавляем вопрос
        markdown += `**Вопрос ${question.number}:** ${question.question}\n\n`;

        // Добавляем варианты ответов, если они есть
        if (Array.isArray(question.options) && question.options.length > 0) {
          markdown += '**Варианты ответов:**\n\n';

          // Определяем правильный ответ
          let correctOption = null;
          if (question.answer) {
            // Извлекаем букву правильного ответа (A, B, C, D)
            const letterMatch = question.answer.match(/^([A-D])\./);
            if (letterMatch) {
              correctOption = letterMatch[1];
            }
          }

          // Форматируем каждый вариант ответа
          for (let i = 0; i < question.options.length; i++) {
            const option = question.options[i];
            const optionLetter = String.fromCharCode(65 + i); // A, B, C, D...
            const isCorrect = correctOption === optionLetter;
            const marker = isCorrect ? '✓ ' : '';

            if (isCorrect) {
              markdown += `* <span class="option-letter">${optionLetter}</span> ${marker}${option} <span class="correct-badge">Правильный</span>\n`;
            } else {
              markdown += `* <span class="option-letter">${optionLetter}</span> ${option}\n`;
            }
          }

          markdown += '\n';
        }

        // Добавляем правильный ответ
        if (question.answer) {
          markdown += `<div class="correct-answer-box">**Правильный ответ:** ${question.answer}</div>\n\n`;
        }
      }

      return markdown;
    }

    // Если нет массива вопросов, но есть готовый markdown_content, форматируем его
    if (markdown_content) {
      console.log("Форматируем markdown_content");

      // Заменяем формат "--- 4:" на "**Вопрос 4:**"
      let formattedContent = markdown_content
        .replace(/---\s+(\d+):\s+/g, '**Вопрос $1:** ')
        .replace(/Correct\s+:\s+/g, '<div class="correct-answer-box">**Правильный ответ:** ');

      // Добавляем закрывающий тег для блока правильного ответа
      formattedContent = formattedContent.replace(/([A-D]\.\s+[^\n]+)(\n\n|$)/g, '$1</div>$2');

      // Форматируем варианты ответов
      const optionLetters = ['A', 'B', 'C', 'D'];
      for (const letter of optionLetters) {
        // Находим строки с вариантами ответов
        const optionRegex = new RegExp(`${letter}\\. ([^\\n]+)(?:\\s+Правильный)?`, 'g');
        formattedContent = formattedContent.replace(optionRegex, (match, optionText) => {
          const isCorrect = match.includes('Правильный');
          const marker = isCorrect ? '✓ ' : '';
          const correctBadge = isCorrect ? ' <span class="correct-badge">Правильный</span>' : '';
          return `* <span class="option-letter">${letter}</span> ${marker}${optionText}${correctBadge}`;
        });
      }

      // Добавляем заголовок на основе meta данных
      let title = '# Вопросы по тексту';
      if (meta && meta.language) {
        title = `# Вопросы по тексту (${meta.language})`;
        if (meta.difficulty) {
          title += ` - ${meta.difficulty} уровень`;
        }
      }

      return `${title}\n\n${formattedContent}`;
    }
  }

  // Специальная обработка для формата, показанного на скриншоте
  // Проверяем, есть ли в данных поле questions с массивом вопросов
  if (questions.length === 1 && typeof questions[0] === 'object' && questions[0].questions) {
    console.log("Обнаружен объект с полем questions");

    const questionsArray = questions[0].questions;
    if (Array.isArray(questionsArray) && questionsArray.length > 0) {
      console.log("Найден массив вопросов в поле questions, форматируем его");

      // Создаем весь текст одним блоком
      let markdown = '# Вопросы по тексту\n\n';

      // Форматируем каждый вопрос
      for (const question of questionsArray) {
        if (!question.number || !question.question) continue;

        // Добавляем вопрос
        markdown += `**Вопрос ${question.number}:** ${question.question}\n\n`;

        // Добавляем варианты ответов, если они есть
        if (Array.isArray(question.options) && question.options.length > 0) {
          markdown += '**Варианты ответов:**\n\n';

          // Определяем правильный ответ
          let correctOption = null;
          if (question.answer) {
            // Извлекаем букву правильного ответа (A, B, C, D)
            const letterMatch = question.answer.match(/^([A-D])\./);
            if (letterMatch) {
              correctOption = letterMatch[1];
            }
          }

          // Форматируем каждый вариант ответа
          for (let i = 0; i < question.options.length; i++) {
            const option = question.options[i];
            const optionLetter = String.fromCharCode(65 + i); // A, B, C, D...
            const isCorrect = correctOption === optionLetter;
            const marker = isCorrect ? '✓ ' : '';

            if (isCorrect) {
              markdown += `* <span class="option-letter">${optionLetter}</span> ${marker}${option} <span class="correct-badge">Правильный</span>\n`;
            } else {
              markdown += `* <span class="option-letter">${optionLetter}</span> ${option}\n`;
            }
          }

          markdown += '\n';
        }

        // Добавляем правильный ответ
        if (question.answer) {
          markdown += `<div class="correct-answer-box">**Правильный ответ:** ${question.answer}</div>\n\n`;
        }
      }

      return markdown;
    }
  }

  // Специальная обработка для формата, показанного на скриншоте, где данные могут быть в виде строки JSON
  if (questions.length === 1 && typeof questions[0] === 'string') {
    // Проверяем, содержит ли строка структуру JSON с вопросами
    const jsonMatch = questions[0].match(/\{\s*"questions"\s*:\s*\[.*?\]\s*,\s*"markdown_content"\s*:/s);

    // Проверяем, содержит ли строка структуру JSON с массивом вопросов (как на скриншоте)
    const directQuestionsMatch = questions[0].match(/^\s*\[\s*\{\s*"number"\s*:\s*\d+\s*,\s*"question"\s*:/s);

    if (jsonMatch || directQuestionsMatch) {
      console.log("Обнаружена строка, содержащая JSON с вопросами");
      try {
        // Пытаемся извлечь и распарсить JSON
        const jsonStartPos = questions[0].indexOf('{') !== -1 ? questions[0].indexOf('{') : questions[0].indexOf('[');
        const jsonEndPos = questions[0].lastIndexOf('}') !== -1 ? questions[0].lastIndexOf('}') + 1 : questions[0].lastIndexOf(']') + 1;

        if (jsonStartPos !== -1 && jsonEndPos !== -1) {
          const jsonText = questions[0].substring(jsonStartPos, jsonEndPos);
          const parsedData = JSON.parse(jsonText);

          // Если это массив вопросов напрямую (как на скриншоте)
          if (Array.isArray(parsedData) && parsedData.length > 0 &&
              parsedData[0].number !== undefined && parsedData[0].question !== undefined) {
            console.log("Обнаружен массив вопросов в формате скриншота:", parsedData.slice(0, 2));

            // Создаем весь текст одним блоком
            let markdown = '# Вопросы по тексту\n\n';

            // Форматируем каждый вопрос
            for (const question of parsedData) {
              if (!question.number || !question.question) continue;

              // Добавляем вопрос
              markdown += `**Вопрос ${question.number}:** ${question.question}\n\n`;

              // Добавляем варианты ответов, если они есть
              if (Array.isArray(question.options) && question.options.length > 0) {
                markdown += '**Варианты ответов:**\n\n';

                // Определяем правильный ответ
                let correctOption = null;
                if (question.answer) {
                  // Извлекаем букву правильного ответа (A, B, C, D)
                  const letterMatch = question.answer.match(/^([A-D])\./);
                  if (letterMatch) {
                    correctOption = letterMatch[1];
                  }
                }

                // Форматируем каждый вариант ответа
                for (let i = 0; i < question.options.length; i++) {
                  const option = question.options[i];
                  const optionLetter = String.fromCharCode(65 + i); // A, B, C, D...
                  const isCorrect = correctOption === optionLetter;
                  const marker = isCorrect ? '✓ ' : '';

                  if (isCorrect) {
                    markdown += `* <span class="option-letter">${optionLetter}</span> ${marker}${option} <span class="correct-badge">Правильный</span>\n`;
                  } else {
                    markdown += `* <span class="option-letter">${optionLetter}</span> ${option}\n`;
                  }
                }

                markdown += '\n';
              }

              // Добавляем правильный ответ
              if (question.answer) {
                markdown += `<div class="correct-answer-box">**Правильный ответ:** ${question.answer}</div>\n\n`;
              }
            }

            return markdown;
          }

          if (parsedData && parsedData.questions && Array.isArray(parsedData.questions)) {
            console.log("Успешно извлечены вопросы из JSON строки:", parsedData.questions);

            // Создаем весь текст одним блоком
            let markdown = '# Вопросы по тексту\n\n';

            // Форматируем каждый вопрос
            for (const question of parsedData.questions) {
              if (!question.number || !question.question) continue;

              // Добавляем вопрос
              markdown += `**Вопрос ${question.number}:** ${question.question}\n\n`;

              // Добавляем варианты ответов, если они есть
              if (Array.isArray(question.options) && question.options.length > 0) {
                markdown += '**Варианты ответов:**\n\n';

                // Определяем правильный ответ
                let correctOption = null;
                if (question.answer) {
                  // Извлекаем букву правильного ответа (A, B, C, D)
                  const letterMatch = question.answer.match(/^([A-D])\./);
                  if (letterMatch) {
                    correctOption = letterMatch[1];
                  }
                }

                // Форматируем каждый вариант ответа
                for (let i = 0; i < question.options.length; i++) {
                  const option = question.options[i];
                  const optionLetter = String.fromCharCode(65 + i); // A, B, C, D...
                  const isCorrect = correctOption === optionLetter;
                  const marker = isCorrect ? '✓ ' : '';

                  if (isCorrect) {
                    markdown += `* <span class="option-letter">${optionLetter}</span> ${marker}${option} <span class="correct-badge">Правильный</span>\n`;
                  } else {
                    markdown += `* <span class="option-letter">${optionLetter}</span> ${option}\n`;
                  }
                }

                markdown += '\n';
              }

              // Добавляем правильный ответ
              if (question.answer) {
                markdown += `<div class="correct-answer-box">**Правильный ответ:** ${question.answer}</div>\n\n`;
              }
            }

            return markdown;
          }

          // Если есть markdown_content, форматируем его
          if (parsedData && parsedData.markdown_content) {
            console.log("Найден markdown_content в JSON строке");

            // Заменяем формат "--- 4:" на "**Вопрос 4:**"
            let formattedContent = parsedData.markdown_content
              .replace(/---\s+(\d+):\s+/g, '**Вопрос $1:** ')
              .replace(/Correct\s+:\s+/g, '<div class="correct-answer-box">**Правильный ответ:** ');

            // Добавляем закрывающий тег для блока правильного ответа
            formattedContent = formattedContent.replace(/([A-D]\.\s+[^\n]+)(\n\n|$)/g, '$1</div>$2');

            // Форматируем варианты ответов
            const optionLetters = ['A', 'B', 'C', 'D'];
            for (const letter of optionLetters) {
              // Находим строки с вариантами ответов
              const optionRegex = new RegExp(`${letter}\\. ([^\\n]+)(?:\\s+Правильный)?`, 'g');
              formattedContent = formattedContent.replace(optionRegex, (match, optionText) => {
                const isCorrect = match.includes('Правильный');
                const marker = isCorrect ? '✓ ' : '';
                const correctBadge = isCorrect ? ' <span class="correct-badge">Правильный</span>' : '';
                return `* <span class="option-letter">${letter}</span> ${marker}${optionText}${correctBadge}`;
              });
            }

            // Добавляем заголовок
            let title = '# Вопросы по тексту';
            if (parsedData.meta && parsedData.meta.language) {
              title = `# Вопросы по тексту (${parsedData.meta.language})`;
              if (parsedData.meta.difficulty) {
                title += ` - ${parsedData.meta.difficulty} уровень`;
              }
            }

            return `${title}\n\n${formattedContent}`;
          }
        }
      } catch (e) {
        console.log("Ошибка при извлечении JSON из строки:", e);
      }
    }

    // Проверяем, содержит ли строка форматированный текст с вопросами
    if (questions[0].includes('**Вопрос') || questions[0].includes('# about the text')) {
      console.log("Обнаружен форматированный текст с вопросами");

      // Заменяем формат "--- 1:" на "**Вопрос 1:**"
      let formattedContent = questions[0]
        .replace(/---\s+(\d+):\s+/g, '**Вопрос $1:** ')
        .replace(/Correct\s+:\s+/g, '<div class="correct-answer-box">**Правильный ответ:** ');

      // Заменяем формат "# about the text --- 1:" на "**Вопрос 1:**"
      formattedContent = formattedContent
        .replace(/# about the text\s+---\s+(\d+):/g, '**Вопрос $1:**')
        .replace(/<span[^>]*>(\d+):<\/span>/g, '**Вопрос $1:**');

      // Добавляем закрывающий тег для блока правильного ответа
      formattedContent = formattedContent.replace(/([A-D]\.\s+[^\n]+)(\n\n|$)/g, '$1</div>$2');

      // Форматируем варианты ответов
      const optionLetters = ['A', 'B', 'C', 'D'];
      for (const letter of optionLetters) {
        // Находим строки с вариантами ответов
        const optionRegex = new RegExp(`${letter}\\. ([^\\n]+)(?:\\s+Правильный)?`, 'g');
        formattedContent = formattedContent.replace(optionRegex, (match, optionText) => {
          const isCorrect = match.includes('Правильный') || match.includes('✓');
          const marker = isCorrect ? '✓ ' : '';
          const correctBadge = isCorrect ? ' <span class="correct-badge">Правильный</span>' : '';
          return `* <span class="option-letter">${letter}</span> ${marker}${optionText}${correctBadge}`;
        });

        // Находим строки с вариантами ответов в формате <span>A</span>
        const spanOptionRegex = new RegExp(`<span[^>]*>${letter}<\/span>([^<\\n]+)`, 'g');
        formattedContent = formattedContent.replace(spanOptionRegex, (match, optionText) => {
          const isCorrect = match.includes('✓');
          const marker = isCorrect ? '✓ ' : '';
          return `* <span class="option-letter">${letter}</span> ${marker}${optionText}`;
        });
      }

      // Добавляем заголовок
      const title = '# Вопросы по тексту';

      return `${title}\n\n${formattedContent}`;
    }
  }

  // Проверяем, содержат ли вопросы поле questionType, что указывает на тест на понимание
  const isComprehensionTest = questions.some(q => q.questionType);

  // Создаем весь текст одним блоком
  let markdown = isComprehensionTest ?
    '# Тест на понимание текста\n\n' :
    '# Вопросы по тексту\n\n';

  for (let i = 0; i < questions.length; i++) {
    const question = questions[i];

    // Определяем номер вопроса из разных возможных источников
    let questionNumber = i + 1;
    if (question.number) {
      questionNumber = parseInt(question.number);
    } else if (question.questionNumber) {
      questionNumber = parseInt(question.questionNumber);
    }

    // Получаем тип вопроса, если есть
    const questionType = question.questionType || 'Generic';

    console.log(`Обработка вопроса ${questionNumber} (${questionType}):`, question);

    // Проверяем, является ли вопрос объектом или строкой
    if (typeof question === 'string') {
      // Если это строка, используем её как текст вопроса
      markdown += `**Вопрос ${questionNumber}:** ${question}\n\n`;
      continue;
    }

    // РАСШИРЕННАЯ ПРОВЕРКА: Проверяем наличие различных форматов полей с текстом вопроса
    const possibleFields = [
      'questionText', 'text', 'question', 'content', 'title', 'prompt',
      'QuestionText', 'Text', 'Question', 'Content', 'Title', 'Prompt'
    ];

    let foundQuestionText: string | null = null;

    // Проверяем все возможные поля
    for (const field of possibleFields) {
      if (question[field] && typeof question[field] === 'string') {
        foundQuestionText = question[field];
        console.log(`Найдено поле ${field} с текстом вопроса:`, foundQuestionText);
        break;
      }
    }

    // Если не нашли ни в одном поле, проверяем вложенные структуры
    if (!foundQuestionText) {
      // Ищем любое поле, которое может содержать текст вопроса
      for (const key in question) {
        if (typeof question[key] === 'string' &&
            question[key].length > 10 &&
            !key.toLowerCase().includes('answer') &&
            !key.toLowerCase().includes('option')) {
          foundQuestionText = question[key];
          console.log(`Найден возможный текст вопроса в поле ${key}:`, foundQuestionText);
          break;
        }
      }
    }

    // Если до сих пор не нашли, используем отладочное сообщение
    if (!foundQuestionText) {
      foundQuestionText = `[Вопрос ${questionNumber}. Текст не найден. Доступные поля: ${Object.keys(question).join(', ')}]`;
      console.log("Не удалось найти текст вопроса, используем отладочное сообщение:", foundQuestionText);
    }

    // Удаляем из текста вопроса потенциальные звездочки и другие форматирования
    if (foundQuestionText) {
      foundQuestionText = foundQuestionText.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim();
    }

    // Добавляем вопрос и его текст с учетом типа вопроса
    if (questionType && questionType !== 'Generic') {
      markdown += `**Вопрос ${questionNumber} (${questionType}):** ${foundQuestionText}\n\n`;
    } else {
    markdown += `**Вопрос ${questionNumber}:** ${foundQuestionText}\n\n`;
    }

    // Ищем правильный ответ
    let correctAnswer = null;
    const answerFields = ['answer', 'correctAnswer', 'correct', 'Answer', 'CorrectAnswer', 'Correct'];

    for (const field of answerFields) {
      if (question[field] && typeof question[field] === 'string') {
        correctAnswer = question[field];
        console.log(`Найдено поле ${field} с правильным ответом:`, correctAnswer);
        break;
      }
    }

    // Удаляем из текста ответа потенциальные звездочки и другие форматирования
    if (correctAnswer) {
      correctAnswer = correctAnswer.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim();
    }

    // Обрабатываем тип вопроса True/False отдельно
    if (questionType === 'True/False') {
      markdown += '**Варианты:**\n\n';
      const options = ['True', 'False', 'Not Stated'];

      for (let j = 0; j < options.length; j++) {
        const isCorrect = correctAnswer && options[j].toLowerCase() === correctAnswer.toLowerCase();
        const marker = isCorrect ? '✓ ' : '';

        if (isCorrect) {
          markdown += `* <span class="option-letter">${String.fromCharCode(65 + j)}</span> ${marker}${options[j]} <span class="correct-badge">Правильный</span>\n`;
        } else {
          markdown += `* <span class="option-letter">${String.fromCharCode(65 + j)}</span> ${options[j]}\n`;
        }
      }

      markdown += '\n';

      // Добавляем правильный ответ
      if (correctAnswer) {
        markdown += `<div class="correct-answer-box">**Правильный ответ:** ${correctAnswer}</div>\n\n`;
      }

      continue; // Переходим к следующему вопросу
    }

    // Для вопросов с коротким ответом
    if (questionType === 'Short answer') {
      if (correctAnswer) {
        markdown += `<div class="correct-answer-box">**Правильный ответ:** ${correctAnswer}</div>\n\n`;
      }

      continue; // Переходим к следующему вопросу
    }

    // Получаем варианты ответов
    let options: string[] = [];
    if (Array.isArray(question.options) && question.options.length > 0) {
      // Удаляем потенциальные звездочки и другие форматирования из вариантов
      options = question.options.map((opt: any) => {
        if (typeof opt === 'string') {
          return opt.replace(/^\*\*\s*/, '').replace(/\*\*$/, '').trim();
        }
        return typeof opt === 'object' ? JSON.stringify(opt) : String(opt);
      });
    }

    // Обрабатываем случай, когда есть правильный ответ, но нет вариантов
    if (correctAnswer && (!options.length || options.length === 0)) {
      // Проверяем, содержит ли правильный ответ букву (например, "C. To keep up with...")
      const letterMatch = correctAnswer.match(/^([A-D])\.\s*(.*)/);
      if (letterMatch) {
        const letter = letterMatch[1];
        const correctOptionText = letterMatch[2].trim();

        // Генерируем фиктивные варианты ответов на основе правильного ответа
        const optionLetters = ['A', 'B', 'C', 'D'];

        // Создаем массив вариантов, где правильный ответ имеет букву из исходного ответа
        options = [];
        for (let j = 0; j < optionLetters.length; j++) {
          if (optionLetters[j] === letter) {
            options.push(correctOptionText);
          } else {
            options.push(`Вариант ответа ${optionLetters[j]}`);
          }
        }

        question.options = options;

        console.log(`Сгенерированы варианты ответов на основе правильного ответа:`, options);
      }
    }

    // Если есть варианты ответов, добавляем их
    if (options.length > 0) {
      markdown += '**Варианты ответов:**\n\n';

      // Извлекаем букву правильного ответа, если она есть
      let correctLetter = null;
      if (correctAnswer) {
        const letterMatch = correctAnswer.match(/^([A-D])\.?\s*(.+)$/);
        if (letterMatch) {
          correctLetter = letterMatch[1];
          // Если в correctAnswer указана только буква, пытаемся найти полный текст
          if (!letterMatch[2] || letterMatch[2].trim().length === 0) {
            const optionIndex = correctLetter.charCodeAt(0) - 65; // A=0, B=1, ...
            if (optionIndex >= 0 && optionIndex < options.length) {
              const optionText = typeof options[optionIndex] === 'string' ?
                options[optionIndex] :
                (options[optionIndex].text || options[optionIndex].content || '');
              correctAnswer = `${correctLetter}. ${optionText}`;
            }
          }
        }
      }

      for (let j = 0; j < options.length; j++) {
        const option = options[j];
        const optionLetter = String.fromCharCode(65 + j); // A, B, C, D...

        // Проверяем, является ли этот вариант правильным ответом
        let isCorrect = false;

        if (correctLetter) {
          // Если есть буква правильного ответа, сравниваем с ней
          isCorrect = optionLetter === correctLetter;
        } else if (correctAnswer) {
          // Иначе проверяем, содержит ли вариант текст правильного ответа или наоборот
          if (typeof option === 'string' && typeof correctAnswer === 'string') {
            isCorrect = option.includes(correctAnswer) || correctAnswer.includes(option);
          } else {
            // Если типы не строки, преобразуем в строки для сравнения
            isCorrect = String(option).includes(String(correctAnswer)) ||
                       String(correctAnswer).includes(String(option));
          }
        }

        const marker = isCorrect ? '✓ ' : '';

        // Проверяем, является ли вариант объектом или строкой
        const optionText = typeof option === 'string' ? option :
                          (option.text || option.content || JSON.stringify(option));

        if (isCorrect) {
          markdown += `* <span class="option-letter">${optionLetter}</span> ${marker}${optionText} <span class="correct-badge">Правильный</span>\n`;
        } else {
          markdown += `* <span class="option-letter">${optionLetter}</span> ${optionText}\n`;
        }
      }
      markdown += '\n';
    }

    // Всегда добавляем правильный ответ, если он есть и это не тип с вариантами или True/False
    if (correctAnswer && questionType !== 'True/False') {
      markdown += `<div class="correct-answer-box">**Правильный ответ:** ${correctAnswer}</div>\n\n`;
    } else if (!correctAnswer) {
      // Если ответа нет, пробуем поискать его в тексте вопроса или других полях
      for (const key in question) {
        if (typeof question[key] === 'string' &&
            key.toLowerCase().includes('answer') &&
            !key.toLowerCase().includes('wrong')) {
          correctAnswer = question[key];
          markdown += `<div class="correct-answer-box">**Правильный ответ:** ${correctAnswer}</div>\n\n`;
          break;
        }
      }
    }
  }

  return markdown;
}

// Дополнительная функция для извлечения вопросов и ответов из markdown структуры
function extractQuestionsFromMarkdown(text: string): any[] {
  console.log('Извлекаем вопросы из Markdown структуры...');
  console.log('Текст для извлечения:', text);

  const questions: any[] = [];

  // Проверяем, является ли это тестом на понимание
  if ((text.includes('True/False') || text.includes('Multiple Choice') ||
       text.includes('Complete the sentence') || text.includes('Short answer') ||
       text.includes('Multiple-choice') || text.includes('Kurze Antwort') ||
       text.includes('Ergänze den Satz') || text.includes('Bedeutung der Frage'))) {

    console.log('Обнаружен формат теста на понимание, используем специальную обработку');

    // Разделяем текст на секции по маркерам заголовков
    let sections = text.split(/(?=###\s+\d+\.)/g);

    // Если не удалось разделить по ###, пробуем по другим маркерам
    if (sections.length <= 1) {
      sections = text.split(/(?=\d+\.\s+(?:Multiple|True|Complete|Short|Bedeutung|Kurze|Ergänze))/g);
    }

    console.log(`Найдено ${sections.length} секций в тесте на понимание`);

    // Обрабатываем каждую секцию
    for (let i = 0; i < sections.length; i++) {
      const section = sections[i].trim();

      // Пропускаем заголовки и пустые секции
      if (!section || section.startsWith('# ') || section.length < 10) continue;

      console.log(`Обрабатываем секцию ${i+1}: ${section.substring(0, 50)}...`);

      // Извлекаем номер и тип вопроса
      const sectionHeaderMatch = section.match(/###\s*(\d+)\.\s*([^\n]+)|^(\d+)\.\s*([^\n]+)/);
      if (!sectionHeaderMatch) continue;

      const questionNumber = sectionHeaderMatch[1] || sectionHeaderMatch[3];
      const questionType = sectionHeaderMatch[2] || sectionHeaderMatch[4];

      // Извлекаем текст вопроса (первая строка после заголовка)
      const lines = section.split('\n').filter(line => line.trim());
      let questionText = '';

      // Ищем текст вопроса в первых нескольких строках после заголовка
      for (let j = 1; j < Math.min(lines.length, 5); j++) {
        const line = lines[j];
        if (line && !line.startsWith('###') && !line.match(/^[a-d]\)/) && !line.includes('Options:') && !line.includes('Answer:')) {
          questionText = line.trim();
          break;
        }
      }

      // Если не нашли текст вопроса, берем весь раздел без заголовка
      if (!questionText) {
        questionText = section.replace(/###\s*\d+\.\s*[^\n]+\n/, '').trim().split('\n')[0] || 'Вопрос';
      }

      console.log(`Определен вопрос ${questionNumber} (${questionType}): ${questionText}`);

      // Извлекаем варианты ответов
      const options: string[] = [];
      let answer: string | null = null;

      // Ищем варианты ответов (a), b), c), d) или a., b., c., d.)
      const optionRegex = /(?:[a-d]\)|[a-d]\.)\s*(?:\*\*)?([^*\n]+)(?:\*\*)?(?:\s*✓)?/gi;
      let optionMatch;
      while ((optionMatch = optionRegex.exec(section)) !== null) {
        options.push(optionMatch[1].trim());
      }

      // Ищем правильный ответ отмеченный ✓
      const correctOptionMatch = section.match(/(?:[a-d]\)|[a-d]\.)\s*(?:\*\*)?([^*\n]+)(?:\*\*)?(?:\s*✓)/i);
      if (correctOptionMatch) {
        const letter = section.match(/([a-d])[\.)\]](?:.*?)✓/i)?.[1].toUpperCase() || '';
        answer = letter ? `${letter}. ${correctOptionMatch[1].trim()}` : correctOptionMatch[1].trim();
      } else {
        // Если не нашли по ✓, ищем в явном виде
        const answerMatch = section.match(/(?:\*\*)?(?:Answer|Antwort|Правильный ответ):(?:\*\*)?\s*([^\n]+)/i);
        if (answerMatch) {
          answer = answerMatch[1].trim();
        }
      }

      // Поправка для True/False/Not Stated
      if (questionType.includes('True/False') || section.includes('True') && section.includes('False')) {
        if (!options.length) {
          options.push('True');
          options.push('False');
          if (section.includes('Not Stated')) {
            options.push('Not Stated');
          }
        }
      }

      // Добавляем вопрос в список
      questions.push({
        questionNumber,
        question: questionText,
        options,
        answer,
        questionType
      });
    }

    // Если не удалось извлечь вопросы стандартным способом, пробуем альтернативный
    if (questions.length === 0) {
      console.log('Не удалось извлечь вопросы обычным способом, пробуем альтернативный');

      // Альтернативный подход - используем регулярное выражение для поиска каждого вопроса
      const altRegex = /(?:Question|Вопрос|Frage)\s*(\d+)(?:[:.]\s*|\s+\([^)]+\)\s*:?\s*)([^\n]+)/g;
      let altMatch;

      while ((altMatch = altRegex.exec(text)) !== null) {
        const qNumber = altMatch[1];
        const qText = altMatch[2].trim();

        // Находим конец текущего вопроса (начало следующего или конец текста)
        const currentPos = altMatch.index;
        let nextMatchPos = text.indexOf(`Question ${parseInt(qNumber) + 1}`, currentPos);
        if (nextMatchPos === -1) {
          nextMatchPos = text.indexOf(`Вопрос ${parseInt(qNumber) + 1}`, currentPos);
        }
        if (nextMatchPos === -1) {
          nextMatchPos = text.indexOf(`Frage ${parseInt(qNumber) + 1}`, currentPos);
        }

        const endPos = nextMatchPos !== -1 ? nextMatchPos : text.length;
        const questionBlock = text.substring(currentPos, endPos);

        console.log(`Найден вопрос ${qNumber} альтернативным способом: ${qText.substring(0, 50)}...`);

        // Извлекаем варианты ответов
        const options: string[] = [];
        const optMatches = questionBlock.matchAll(/(?:[a-d]\)|[a-d]\.)\s*([^\n]+)/g);
        for (const optMatch of Array.from(optMatches)) {
          options.push(optMatch[1].trim().replace(/\*\*/g, '').replace(/✓/g, ''));
        }

        // Ищем правильный ответ
        let answer: string | null = null;

        // Сначала ищем ответ отмеченный символом ✓
        const correctOptMatch = questionBlock.match(/(?:[a-d]\)|[a-d]\.)\s*([^\n]+)(?:\s*✓)/i);
        if (correctOptMatch) {
          const letter = questionBlock.match(/([a-d])[\.)\]](?:.*?)✓/i)?.[1].toUpperCase() || '';
          answer = letter ? `${letter}. ${correctOptMatch[1].trim().replace(/\*\*/g, '')}` : correctOptMatch[1].trim();
        } else {
          // Если не нашли по ✓, ищем в явном виде
          const ansMatch = questionBlock.match(/(?:Answer|Antwort|Правильный ответ):?\s*([^\n]+)/i);
          if (ansMatch) {
            answer = ansMatch[1].trim();
          }
        }

        let qType = 'Generic';
        if (questionBlock.includes('Multiple Choice') || questionBlock.includes('Multiple-choice')) {
          qType = 'Multiple-choice';
        } else if (questionBlock.includes('True/False')) {
          qType = 'True/False';
          if (!options.length) {
            options.push('True');
            options.push('False');
            if (questionBlock.includes('Not Stated')) {
              options.push('Not Stated');
            }
          }
        } else if (questionBlock.includes('Complete the sentence') || questionBlock.includes('Ergänze den Satz')) {
          qType = 'Complete the sentence';
        } else if (questionBlock.includes('Short answer') || questionBlock.includes('Kurze Antwort')) {
          qType = 'Short answer';
        } else if (questionBlock.includes('Meaning') || questionBlock.includes('Bedeutung')) {
          qType = 'Meaning';
        }

        questions.push({
          questionNumber: qNumber,
          question: qText,
          options,
          answer,
          questionType: qType
        });
      }
    }
  }

  // Если ничего не нашли по разделам теста на понимание,
  // проверяем простой формат "Вопрос N: ... Правильный ответ: ..."
  if (questions.length === 0) {
    const simpleQuestionRegex = /(?:Вопрос|Question|Frage) (\d+):?\s*([^\n]+?)[\n\?]+\s*(?:[\n\s]*(?:Правильный ответ|Answer|Antwort):?\s*([^\n]+))?/gi;
    let match;

    while ((match = simpleQuestionRegex.exec(text)) !== null) {
      const questionNumber = match[1];
      const questionText = match[2].trim();
      const answer = match[3] ? match[3].trim() : null;

      console.log(`Найден вопрос в простом формате ${questionNumber}: ${questionText}, ответ: ${answer}`);

      // Извлекаем варианты ответов
      const options: string[] = [];

      // Ищем блок текста между текущим вопросом и следующим вопросом или концом текста
      const currentPos = match.index;
      const nextMatchIndex = text.indexOf(`Вопрос ${parseInt(questionNumber) + 1}`, currentPos);
      const endPos = nextMatchIndex !== -1 ? nextMatchIndex : text.length;
      const questionBlock = text.substring(currentPos, endPos);

      // Извлекаем варианты ответов из блока
      const optMatches = questionBlock.matchAll(/(?:[A-D]|[a-d])[\.)]\s*([^\n]+)/g);
      for (const optMatch of Array.from(optMatches)) {
        options.push(optMatch[1].trim());
      }

      questions.push({
        questionNumber,
        question: questionText,
        options,
        answer,
        questionType: 'Generic'
      });
    }
  }

  return questions;
}

// Вспомогательная функция для извлечения вариантов ответов и правильных ответов
function extractQuestionDetails(text: string, questions: any[]): any[] {
  const enhancedQuestions = [...questions];

  // Сначала пробуем извлечь вопросы из Markdown структуры
  // Этот блок должен быть особенно эффективным для структуры, которую возвращает сервер
  if (text.includes('## Вопрос') || text.includes('## Question')) {
    console.log('Обнаружена Markdown-структура, пробуем извлечь вопросы...');

    const markdownQuestions = extractQuestionsFromMarkdown(text);
    if (markdownQuestions.length > 0 &&
       (markdownQuestions.some(q => q.options && q.options.length > 0) ||
        markdownQuestions.some(q => q.answer))) {
      console.log('Успешно извлечены вопросы из Markdown структуры с вариантами/ответами:', markdownQuestions);
      return markdownQuestions;
    }
  }

  // Проверяем, содержит ли текст структуру JSON с вопросами и ответами
  try {
    if (text.includes('"question"') && (text.includes('"options"') || text.includes('"answer"'))) {
      const jsonStartPos = text.indexOf('{');
      const jsonEndPos = text.lastIndexOf('}') + 1;
      if (jsonStartPos !== -1 && jsonEndPos !== -1) {
        const jsonText = text.substring(jsonStartPos, jsonEndPos);
        try {
          const jsonData = JSON.parse(jsonText);
          if (jsonData.questions || (Array.isArray(jsonData) && jsonData.length > 0 && jsonData[0].question)) {
            const questionsData = jsonData.questions || jsonData;
            console.log('Найдены вопросы в JSON структуре:', questionsData);

            const formattedQuestions = questionsData.map((q: any) => ({
              questionNumber: (q.number || q.questionNumber || '').toString(),
              question: q.question || q.questionText || q.text || '',
              options: Array.isArray(q.options) ? q.options : [],
              answer: q.answer || q.correctAnswer || q.correct || null
            }));

            return formattedQuestions;
          }
        } catch (e) {
          console.log('Ошибка при парсинге JSON:', e);
        }
      }
    }
  } catch (e) {
    console.log('Ошибка при проверке JSON структуры:', e);
  }

  // Если в тексте есть "### Варианты ответов:" или "### Правильный ответ:",
  // но не удалось извлечь вопросы методом extractQuestionsFromMarkdown,
  // попробуем использовать более прямой подход
  if ((text.includes('### Варианты ответов:') || text.includes('### Options:')) &&
      (text.includes('### Правильный ответ:') || text.includes('### Correct answer:'))) {

    console.log('Обнаружены заголовки вариантов и ответов, пробуем напрямую разбить текст на секции');

    // Разбиваем текст на секции по вопросам
    const sections = text.split(/(?=## Вопрос \d+:|## Question \d+:)/);

    if (sections.length > 1) {
      const markdownQuestions: any[] = [];

      for (let i = 1; i < sections.length; i++) {
        const section = sections[i];

        // Извлекаем номер и текст вопроса
        const questionMatch = section.match(/## (?:Вопрос|Question) (\d+):([^#]*)/);
        if (!questionMatch) continue;

        const questionNumber = questionMatch[1];
        const questionText = questionMatch[2].trim();

        // Извлекаем варианты ответов
        const options: string[] = [];
        const optionsMatch = section.match(/### (?:Варианты ответов|Options):([\s\S]*?)(?=###|---|\n## |$)/);

        if (optionsMatch) {
          const optionsText = optionsMatch[1].trim();
          const optionLines = optionsText.split('\n').filter(line => line.trim());

          for (const line of optionLines) {
            const optionMatch = line.match(/([A-D])\.\s*(?:\*\*)?([^*\n]+)(?:\*\*)?(?:\s*✓)?/);
            if (optionMatch) {
              options.push(optionMatch[2].trim());
            }
          }
        }

        // Извлекаем правильный ответ
        let answer = null;
        const answerMatch = section.match(/### (?:Правильный ответ|Correct answer|Answer):([\s\S]*?)(?=###|---|\n## |$)/);

        if (answerMatch) {
          let answerText = answerMatch[1].trim();
          // Удаляем форматирование
          answerText = answerText.replace(/\*\*/g, '').replace(/✓/g, '').trim();
          answer = answerText;
        }

        // Если не нашли правильный ответ в явном виде, ищем по отметке ✓
        if (!answer && section.includes('✓')) {
          const correctOptionMatch = section.match(/([A-D])\.\s*(?:\*\*)?([^*\n]+)(?:\*\*)?\s*✓/);
          if (correctOptionMatch) {
            answer = `${correctOptionMatch[1]}. ${correctOptionMatch[2].trim()}`;
          }
        }

        markdownQuestions.push({
          questionNumber,
          question: questionText,
          options,
          answer
        });
      }

      if (markdownQuestions.length > 0) {
        console.log('Напрямую извлечены вопросы из Markdown структуры:', markdownQuestions);
        return markdownQuestions;
      }
    }
  }

  console.log('Извлекаем дополнительные данные из текста:', text.substring(0, 200) + '...');

  // Для каждого вопроса пытаемся найти варианты ответов и правильный ответ
  for (let i = 0; i < enhancedQuestions.length; i++) {
    const questionNumber = enhancedQuestions[i].questionNumber;
    const questionText = enhancedQuestions[i].question;

    // Ищем вопрос в тексте разными способами
    let startPos = -1;
    const searchPatterns = [
      enhancedQuestions[i].fullMatch,
      `Вопрос ${questionNumber}:`,
      `Вопрос ${questionNumber}`,
      `Question ${questionNumber}:`,
      `Question ${questionNumber}`,
      `## Вопрос ${questionNumber}:`,
      `## Question ${questionNumber}:`,
      `${questionNumber}.`
    ];

    for (const pattern of searchPatterns) {
      if (!pattern) continue;
      const pos = text.indexOf(pattern);
      if (pos !== -1) {
        startPos = pos;
        break;
      }
    }

    // Если не нашли вопрос в тексте, пытаемся найти по тексту вопроса
    if (startPos === -1 && questionText) {
      const escapedQuestionText = questionText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const questionRegex = new RegExp(`(Вопрос|Question)\\s*${questionNumber}[:.\\s]+\\s*${escapedQuestionText}`, 'i');
      const match = text.match(questionRegex);
      if (match) {
        startPos = match.index;
      } else {
        // Ищем просто по тексту вопроса
        startPos = text.indexOf(questionText);
      }
    }

    console.log(`Поиск вопроса ${questionNumber}: ${startPos !== -1 ? 'найден на позиции ' + startPos : 'не найден'}`);

    if (startPos === -1) continue;

    // Определяем конец блока текущего вопроса (до следующего вопроса или конца текста)
    let nextQuestionIndex = text.length;

    // Проверяем разные форматы следующего вопроса
    const nextFormats = [
      `Вопрос ${parseInt(questionNumber) + 1}:`,
      `## Вопрос ${parseInt(questionNumber) + 1}:`,
      `Question ${parseInt(questionNumber) + 1}:`,
      `## Question ${parseInt(questionNumber) + 1}:`,
      `${parseInt(questionNumber) + 1}.`,
      '---' // Разделитель между вопросами
    ];

    for (const format of nextFormats) {
      const pos = text.indexOf(format, startPos);
      if (pos !== -1 && pos < nextQuestionIndex) {
        nextQuestionIndex = pos;
      }
    }

    const questionBlock = text.substring(startPos, nextQuestionIndex);
    console.log(`Блок вопроса ${questionNumber} (${questionBlock.length} символов): ${questionBlock.substring(0, 100)}...`);

    // Ищем варианты ответов (A., B., 1., 2., etc.)
    const optionRegexes = [
      /([A-D])\.\s*([^\n]+)/g,     // A. Text
      /([A-D])\)\s*([^\n]+)/g,     // A) Text
      /(\d+)\.\s*([^\n]+)/g,       // 1. Text
      /\* ([A-D])\.\s*([^\n]+)/g,  // * A. Text
      /- ([A-D])\.\s*([^\n]+)/g,   // - A. Text
      /([A-D])\. \*\*([^\*]+)\*\*/g, // A. **Text**
      /([A-D])\. ([^\n]+) ✓/g,     // A. Text ✓
      /option[^:]*:\s*['"]([^'"]+)['"]/gi, // option: "Text"
      /options\[[^\]]*\]:\s*['"]([^'"]+)['"]/gi // options[..]: "Text"
    ];

    let options: string[] = [];
    for (const regex of optionRegexes) {
      let match;
      const optionMatches: string[] = [];
      const regexCopy = new RegExp(regex);

      while ((match = regexCopy.exec(questionBlock)) !== null) {
        optionMatches.push(match[2] || match[1]);
        console.log(`Найден вариант ответа: ${match[2] || match[1]}`);
      }

      if (optionMatches.length > 0) {
        options = optionMatches;
        break;
      }
    }

    // Проверяем, если в блоке есть массив вариантов в JSON-формате
    const optionsArrayMatch = questionBlock.match(/options\s*[=:]\s*(\[[^\]]+\])/);
    if (optionsArrayMatch) {
      try {
        // Попытаемся распарсить JSON массив
        const jsonArray = JSON.parse(optionsArrayMatch[1].replace(/'/g, '"'));
        if (Array.isArray(jsonArray) && jsonArray.length > 0) {
          options = jsonArray.map(o => typeof o === 'string' ? o : JSON.stringify(o));
          console.log(`Найден массив вариантов в JSON формате:`, options);
        }
      } catch (e) {
        console.log('Ошибка при парсинге JSON массива вариантов:', e);
      }
    }

    // Если нашли варианты, добавляем их к вопросу
    if (options.length > 0) {
      enhancedQuestions[i].options = options;
    }

    // Ищем правильный ответ, проверяя разные форматы
    const answerRegexes = [
      /Правильный ответ:?\s*\*\*([^\*]+)\*\*/i,
      /Correct answer:?\s*\*\*([^\*]+)\*\*/i,
      /Ответ:?\s*\*\*([^\*]+)\*\*/i,
      /Answer:?\s*\*\*([^\*]+)\*\*/i,
      /Правильный ответ:?\s*([^\n]+)/i,
      /Correct answer:?\s*([^\n]+)/i,
      /Ответ:?\s*([^\n]+)/i,
      /Answer:?\s*([^\n]+)/i,
      /answer[^:]*:\s*['"]([^'"]+)['"]/i, // answer: "Text"
      /([A-D]\.[^✓]+)✓/,           // A. Text ✓
      /\*\*([A-D])\.\s*([^\*]+)\*\*\s*✓/  // **A. Text** ✓
    ];

    for (const regex of answerRegexes) {
      const answerMatch = questionBlock.match(regex);
    if (answerMatch) {
        enhancedQuestions[i].answer = answerMatch[1].trim();
        console.log(`Найден ответ для вопроса ${questionNumber}: ${enhancedQuestions[i].answer}`);
        break;
      }
    }

    // Если не нашли ответ, но есть отмеченный вариант с ✓, используем его
    if (!enhancedQuestions[i].answer) {
      const checkMarkIndex = questionBlock.indexOf('✓');
      if (checkMarkIndex !== -1) {
        // Ищем букву варианта перед символом ✓
        const letterMatch = questionBlock.substring(Math.max(0, checkMarkIndex - 50), checkMarkIndex).match(/([A-D])\.\s*([^\n]+)$/);
        if (letterMatch) {
          enhancedQuestions[i].answer = `${letterMatch[1]}. ${letterMatch[2].trim()}`;
          console.log(`Найден ответ по отметке ✓ для вопроса ${questionNumber}: ${enhancedQuestions[i].answer}`);
        }
      }
    }
  }

  return enhancedQuestions;
}

onMounted(() => {
  const levels = getLevelsByLanguage(formData.value.language)
  if (levels && levels.length > 0) {
    summaryOptions.value.level = levels[0].id
  }
})

// Флаг для отслеживания, что сгенерирован именно план урока
const isLessonPlanGenerated = ref(false)

// Сохраняем оригинальный план урока для использования в запросах детализации
const originalLessonPlan = ref<string>('')

// Переменная для хранения детализированной информации о плане урока
const detailedLessonContent = ref<string>('')

// Функция для ограничения размера плана урока
const trimLessonPlan = (lessonPlan: string, maxLength: number = 10000) => {
  if (!lessonPlan || lessonPlan.length <= maxLength) {
    return lessonPlan;
  }

  // Ищем последний полный пункт перед ограничением
  const truncationPoint = lessonPlan.substring(0, maxLength).lastIndexOf("\n\n");

  if (truncationPoint === -1) {
    // Если не нашли двойной перенос строки, ищем одинарный
    const singleNewLine = lessonPlan.substring(0, maxLength).lastIndexOf("\n");
    return singleNewLine !== -1 ? lessonPlan.substring(0, singleNewLine) : lessonPlan.substring(0, maxLength);
  }

  return lessonPlan.substring(0, truncationPoint);
};

// Функция для детализации пункта плана урока
const detailLessonPlanPoint = async (pointId: number | string) => {
  if (!validateInput() || !originalLessonPlan.value) return

  try {
    store.clearError()
    localLoading.value = true

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Ограничиваем размер плана урока для оптимизации запроса
    const trimmedLessonPlan = trimLessonPlan(originalLessonPlan.value);
    console.log(`Оригинальный план урока: ${originalLessonPlan.value.length} символов, после обрезки: ${trimmedLessonPlan.length} символов`);

    // Определяем действие и тип контента на основе pointId
    let actionText = '';
    let pointName = '';
    let contentType = '';

    if (typeof pointId === 'number') {
      pointName = `пункт ${pointId}`;
      contentType = `point_${pointId}`;
      actionText = `ВНИМАНИЕ: Это запрос на детализацию конкретного пункта существующего плана урока.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Детализируй ТОЛЬКО пункт ${pointId} плана урока так, чтобы его можно было сразу использовать в классе.
Предоставь подробное описание:
1. Точные шаги выполнения упражнения/активности
2. Примеры фраз, вопросов, которые может использовать учитель
3. Ожидаемые ответы учеников
4. Четкое распределение времени на каждый этап активности

Результат должен быть максимально конкретным и готовым к непосредственному использованию в классе.`;
    } else {
      switch (pointId) {
        case 'homework':
          pointName = 'домашнее задание';
          contentType = 'homework';
          actionText = `ВНИМАНИЕ: Это запрос на создание домашнего задания для существующего плана урока.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Создай подробное и детальное домашнее задание для приведенного ниже плана урока.
Задание должно соответствовать теме, целям и содержанию плана.
Включи конкретные инструкции, вопросы, упражнения или задачи.
Учитывай уровень учеников и тип занятия из исходного плана.`;
          break;
        case 'script':
          pointName = 'скрипт учителя';
          contentType = 'teacher_script';
          actionText = `ВНИМАНИЕ: Это запрос на создание скрипта учителя для существующего плана урока.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА ИЛИ ЕГО ПЕРЕСКАЗ.
Создай подробный скрипт учителя с точными фразами и инструкциями для проведения урока.
Скрипт должен включать:
1. Фактические слова, которые учитель говорит на каждом этапе
2. Четкие инструкции к заданиям для учеников
3. Вопросы для проверки понимания и вовлечения учеников
4. Переходы между этапами урока
5. Комментарии о взаимодействии с учениками

Скрипт должен следовать исходному плану урока, но содержать конкретные фразы и формулировки.`;
          break;
        case 'exercises':
          pointName = 'упражнения';
          contentType = 'exercises';
          actionText = `ВНИМАНИЕ: Это запрос на создание дополнительных упражнений для существующего плана урока.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Создай набор конкретных упражнений для приведенного ниже плана урока.
Упражнения должны:
1. Соответствовать теме, целям и уровню учеников из исходного плана
2. Быть подробно описаны с инструкциями по выполнению
3. Включать различные типы заданий (письменные, устные, интерактивные)
4. Быть готовыми к использованию без дополнительной подготовки
5. Учитывать формат проведения урока (онлайн/оффлайн, индивидуальный/групповой)`;
          break;
        case 'game':
          pointName = 'игра для урока';
          contentType = 'game';
          actionText = `ВНИМАНИЕ: Это запрос на создание игровой активности для существующего плана урока.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
Создай детальное описание игры или игровой активности для приведенного ниже плана урока.
Игра должна:
1. Соответствовать теме, целям и уровню учеников из исходного плана
2. Включать подробные правила и инструкции по проведению
3. Учитывать формат урока (онлайн/оффлайн, индивидуальный/групповой)
4. Быть интересной, увлекательной и обучающей
5. Содержать все необходимые материалы или описание их подготовки`;
          break;
      }
    }

    // Создаем промпт в формате JSON
    const promptData = {
      language: formData.value.language,
      lesson_plan: trimmedLessonPlan,
      content_type: contentType,
      action: actionText,
      instruction: `Это запрос на создание специального контента "${pointName}" для существующего плана урока.
НЕ создавай новый план урока с нуля на случайную тему.
Вместо этого предоставь конкретный запрашиваемый тип контента (${pointName}) для исходного плана, который прилагается ниже.`,
      // Передаем оригинальные настройки плана урока
      original_options: {
        age: lessonPlanOptions.value.age,
        methodology: lessonPlanOptions.value.methodology,
        duration: lessonPlanOptions.value.duration,
        individual_group: lessonPlanOptions.value.individual_group,
        online_offline: lessonPlanOptions.value.online_offline,
        focus: lessonPlanOptions.value.focus,
        level: lessonPlanOptions.value.level
      },
      system_instruction: "Ты опытный преподаватель, который создает специализированные дополнительные материалы для существующего плана урока."
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'lesson_plan', // Используем тип плана урока
      prompt: JSON.stringify(promptData) // Преобразуем данные в строку JSON
    }

    console.log('Отправляем запрос на детализацию плана урока:', requestData)

    try {
      // Делаем запрос к новому API эндпоинту для детализации
      const response = await fetch(`${API_ENDPOINTS.DETAIL_LESSON_PLAN}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Ошибка API:', response.status, errorData);
        throw new Error(`Ошибка API: ${response.status} - ${errorData.detail || JSON.stringify(errorData)}`);
      }

      const result = await response.json()

      if (result.status === 'success') {
        // Добавляем логирование для проверки ответа API
        console.log('Получен ответ API для детализации плана урока:', result);
        console.log('Содержимое ответа API:', result.data);

        // Очищаем контент от артефактов форматирования
        const cleanedContent = cleanLessonPlanContent(result.data.content);

        // Сохраняем детализированный контент в отдельной переменной
        detailedLessonContent.value = cleanedContent;

        // Не меняем флаг isLessonPlanGenerated, т.к. мы все еще работаем с планом урока
      } else {
        throw new Error(result.message || 'Error detailing lesson plan')
      }
    } catch (error) {
      console.error('Error detailing lesson plan:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error detailing lesson plan')
    } finally {
      localLoading.value = false
    }
  } catch (err) {
    console.error('Ошибка при детализации плана урока:', err)
    localLoading.value = false
  }
}

// Функция для переписывания пункта плана урока
const rewriteLessonPlanPoint = async (pointNumber: number) => {
  if (!validateInput() || !originalLessonPlan.value) return

  try {
    store.clearError()
    localLoading.value = true

    // Проверяем авторизацию
    if (!store.user || !store.user.id) {
      throw new Error('User is not authorized')
    }

    // Ограничиваем размер плана урока для оптимизации запроса
    const trimmedLessonPlan = trimLessonPlan(originalLessonPlan.value);
    console.log(`Оригинальный план урока: ${originalLessonPlan.value.length} символов, после обрезки: ${trimmedLessonPlan.length} символов`);

    // Создаем промпт в формате JSON
    const promptData = {
      language: formData.value.language,
      lesson_plan: trimmedLessonPlan,
      content_type: 'rewrite_lesson_point',
      action: `ВНИМАНИЕ: Это запрос на переписание конкретного пункта существующего плана урока.
НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА И НЕ ПЕРЕПИСЫВАЙ ВЕСЬ ПЛАН.
Перепиши ТОЛЬКО пункт ${pointNumber} плана урока в другом стиле и с другим подходом.
Сохраняй основную суть и образовательные цели пункта, но сделай его:
1. Более интересным и вовлекающим
2. С использованием других методик или подходов
3. С более конкретными активностями и инструкциями
4. Четко обозначенным по времени и материалам
5. Соответствующим формату урока (индивидуальный/групповой, онлайн/оффлайн)

Результат должен быть готов к непосредственному использованию в классе.`,
      instruction: `Это запрос на ПЕРЕПИСАНИЕ одного конкретного пункта существующего плана урока.
НЕ создавай новый план урока с нуля и НЕ ПЕРЕПИСЫВАЙ весь план целиком.
Вместо этого перепиши ТОЛЬКО указанный пункт ${pointNumber} исходного плана в другом стиле и с другим подходом.
В ответе должен быть ТОЛЬКО переписанный пункт ${pointNumber}, а не весь план урока.`,
      // Передаем оригинальные настройки плана урока
      original_options: {
        age: lessonPlanOptions.value.age,
        methodology: lessonPlanOptions.value.methodology,
        duration: lessonPlanOptions.value.duration,
        individual_group: lessonPlanOptions.value.individual_group,
        online_offline: lessonPlanOptions.value.online_offline,
        focus: lessonPlanOptions.value.focus,
        level: lessonPlanOptions.value.level
      },
      system_instruction: "Ты опытный преподаватель, который переписывает отдельные пункты существующего плана урока, а не создает новые планы."
    }

    // Создаем запрос в формате, ожидаемом API
    const requestData = {
      user_id: store.user.id,
      type: 'lesson_plan', // Используем тип плана урока
      prompt: JSON.stringify(promptData) // Преобразуем данные в строку JSON
    }

    console.log('Отправляем запрос на переписывание пункта плана урока:', requestData)

    try {
      // Делаем запрос к новому API эндпоинту для детализации
      const response = await fetch(`${API_ENDPOINTS.DETAIL_LESSON_PLAN}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Ошибка API:', response.status, errorData);
        throw new Error(`Ошибка API: ${response.status} - ${errorData.detail || JSON.stringify(errorData)}`);
      }

      const result = await response.json()

      if (result.status === 'success') {
        // Добавляем логирование для проверки ответа API
        console.log('Получен ответ API для переписывания пункта плана урока:', result);
        console.log('Содержимое ответа API:', result.data);

        // Очищаем контент от артефактов форматирования
        const cleanedContent = cleanLessonPlanContent(result.data.content);

        // Сохраняем детализированный контент в отдельной переменной
        detailedLessonContent.value = cleanedContent;

        // Не меняем флаг isLessonPlanGenerated, т.к. мы все еще работаем с планом урока
      } else {
        throw new Error(result.message || 'Error rewriting lesson plan section')
      }
    } catch (error) {
      console.error('Error rewriting lesson plan section:', error)
      store.setError(typeof error === 'object' && error !== null && 'message' in error ?
        (error as Error).message : 'Error rewriting lesson plan section')
    } finally {
      localLoading.value = false
    }
  } catch (err) {
    console.error('Ошибка при переписывании пункта плана урока:', err)
    localLoading.value = false
  }
}
</script>

<style scoped>
/* Базовые стили контейнера */
.text-analyzer-container {
  min-height: 100vh;
  overflow: visible !important;
  background-repeat: no-repeat;
  padding-top: 20px;
}

/* Заголовок, отдельный блок */
.title-container {
  position: relative;
  z-index: 2;
  text-align: center;
  margin-top: 30vh;
  margin-bottom: 1rem;
}
.title-container h2 {
  color: #fff;
  font-size: 1.8rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
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

/* Контейнер формы и результата */
.content {
  position: relative;
  z-index: 1;
  max-width: 480px;
  margin: 0 auto;
  padding: 1rem;
  background: rgba(255, 192, 203, 0.1);
  border-radius: 16px;
}

/* Форма анализа текста */
.text-analyzer-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

/* Группа формы */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 0.5rem;
}

/* Метки полей */
label {
  font-weight: 500;
  font-size: 0.9rem;
  color: #fff;
}

/* Инпуты, textarea, select */
.form-input,
.form-select,
.form-textarea {
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
  background-color: #ffc0cb;
  color: #333;
  outline: none;
}

.form-textarea {
  min-height: 150px;
  resize: vertical;
  border-radius: 16px;
}

.form-select {
  -webkit-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%23333' stroke='%23333' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 16px;
  padding-right: 2.5rem;
}

/* Панель действий */
.actions-panel {
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.actions-panel h3 {
  color: #fff;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

/* Результат анализа */
.result {
  margin-top: 2rem;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  color: #333;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
  max-width: 100%;
}
.result h3 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}
.result-content {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  line-height: 1.5;
}

/* Стиль заголовка h1 */
.result-content :deep(h1) {
  color: #333;
  margin: 0 0 1.5rem 0;
  text-shadow: none;
  border-bottom: 2px solid #ec407a;
  padding-bottom: 10px;
  text-align: center;
  font-size: 1.6rem;
}

/* Стиль для заголовков вопросов */
.result-content :deep(h2) {
  color: #333;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  text-shadow: none;
  font-size: 1.3rem;
}

/* Стиль для обычного текста */
.result-content :deep(p) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  line-height: 1.6;
  margin-bottom: 0.75rem;
  color: #333;
}

/* Стили для выделения текста */
.result-content :deep(strong) {
  font-weight: 600;
  color: #ec407a;
}

.result-content :deep(em) {
  font-style: italic;
  color: #555;
}

.result-content :deep(code) {
  background-color: rgba(236, 64, 122, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
  color: #333;
}

.result-content :deep(blockquote) {
  border-left: 4px solid #ec407a;
  padding-left: 1rem;
  margin-left: 0;
  color: #555;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 0 8px 8px 0;
}

.result-content :deep(a) {
  color: #ec407a;
  text-decoration: none;
}

/* Единый стиль списка вариантов ответов */
.result-content :deep(ul) {
  list-style-type: none;
  padding-left: 0;
  margin-bottom: 1.5rem;
}

.result-content :deep(li) {
  position: relative;
  padding: 6px 0;
  margin-bottom: 4px;
  color: #333;
}

/* Стили для маркеров вариантов ответов */
.result-content :deep(.option-letter) {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background-color: #ec407a;
  color: white;
  border-radius: 50%;
  margin-right: 8px;
  font-weight: bold;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.result-content :deep(.correct-badge) {
  display: inline-block;
  background-color: #4caf50;
  color: white;
  font-size: 0.8rem;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.result-content :deep(.correct-answer-box) {
  background-color: rgba(236, 64, 122, 0.08);
  padding: 10px;
  border-radius: 8px;
  border-left: 4px solid #ec407a;
  margin: 0 0 1.5rem 0;
}

/* Кнопки действий */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-button-group {
  display: flex;
  width: 100%;
  margin: 5px 0;
  gap: 0.5rem;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  background: #ffc0cb;
  color: #333;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  flex: 1;
}
.action-button:hover {
  background: #ff9ebb;
}
.action-button:active {
  transform: scale(0.97);
}

.points-button {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  color: #1890ff;
}

.points-button:hover {
  background-color: #bae7ff;
  border-color: #69c0ff;
}

.points-icon {
  margin-right: 5px;
  font-size: 16px;
}

.buttons-row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

/* Панель опций */
.options-panel {
  background: rgba(255, 192, 203, 0.2);
  border-radius: 12px;
  padding: 1rem;
  margin: 0.5rem 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.options-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(138, 180, 248, 0.3);
  padding-bottom: 10px;
}

.options-header h3 {
  color: rgba(138, 180, 248, 1);
  font-size: 1.2rem;
  margin: 0;
  text-shadow: 0 0 5px rgba(138, 180, 248, 0.6);
}

.close-button {
  background: transparent;
  border: none;
  color: rgba(138, 180, 248, 0.8);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  transition: color 0.2s, text-shadow 0.2s;
}

.close-button:hover {
  color: rgba(138, 180, 248, 1);
  text-shadow: 0 0 8px rgba(138, 180, 248, 0.8);
}

.game-options-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.game-option {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.game-option label {
  color: rgba(138, 180, 248, 0.9);
  font-size: 0.9rem;
  text-shadow: 0 0 4px rgba(138, 180, 248, 0.5);
}

.space-select {
  position: relative;
}

.cosmic-dropdown {
  width: 100%;
  padding: 10px 15px;
  background: rgba(20, 30, 60, 0.7);
  border: 1px solid rgba(138, 180, 248, 0.4);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  appearance: none;
  cursor: pointer;
  transition: all 0.3s;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
  box-shadow: 0 0 8px rgba(138, 180, 248, 0.2), 0 0 3px rgba(138, 180, 248, 0.1) inset;
}

.cosmic-dropdown:hover, .cosmic-dropdown:focus {
  background: rgba(30, 40, 70, 0.8);
  border-color: rgba(138, 180, 248, 0.7);
  box-shadow: 0 0 10px rgba(138, 180, 248, 0.3), 0 0 5px rgba(138, 180, 248, 0.2) inset;
}

.cosmic-dropdown-icon {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(138, 180, 248, 0.8);
  pointer-events: none;
  text-shadow: 0 0 5px rgba(138, 180, 248, 0.6);
}

.cosmic-button {
  background: linear-gradient(135deg, rgba(92, 124, 250, 0.8), rgba(48, 79, 254, 0.8));
  border: none;
  border-radius: 8px;
  color: white;
  padding: 12px 24px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  display: block;
  width: 100%;
  margin-top: 10px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  box-shadow: 0 2px 10px rgba(48, 79, 254, 0.3), 0 0 15px rgba(48, 79, 254, 0.1) inset, 0 0 0 1px rgba(138, 180, 248, 0.5);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.cosmic-button:hover {
  background: linear-gradient(135deg, rgba(92, 124, 250, 0.9), rgba(48, 79, 254, 0.9));
  box-shadow: 0 3px 15px rgba(48, 79, 254, 0.4), 0 0 20px rgba(48, 79, 254, 0.2) inset, 0 0 0 1px rgba(138, 180, 248, 0.8);
  transform: translateY(-1px);
  text-shadow: 0 0 5px rgba(255, 255, 255, 0.8);
}

.cosmic-button:active {
  transform: translateY(1px);
  box-shadow: 0 1px 5px rgba(48, 79, 254, 0.3), 0 0 0 1px rgba(138, 180, 248, 0.8);
}

/* Добавляем стили для новых элементов */
.detected-level-actions {
  margin-top: 20px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1.5rem;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detected-level-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.level-label {
  font-weight: 500;
  font-size: 0.9rem;
}

.level-value {
  font-size: 1.2rem;
  font-weight: 600;
}

.quick-actions {
  display: flex;
  gap: 0.5rem;
}

.quick-action-btn {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 24px;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.quick-action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Стили для отображения заголовков */
.recommended-title {
  color: #1e7e34;
  font-weight: bold;
  border-left: 4px solid #1e7e34;
  padding-left: 8px;
  background-color: #f0fff0;
  border-radius: 4px;
}

.title-recommendation-mark {
  color: #28a745;
  margin-left: 8px;
}

.titles-list {
  margin-top: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
}

.title-item {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.title-item:hover {
  background-color: #f8f9fa;
}

.options-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.option-item {
  flex: 1;
  min-width: 180px;
}

.option-item label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

/* Возраст */
.age-buttons {
  display: flex;
  gap: 0.5rem;
}
.age-buttons.sm {
  flex-wrap: wrap;
}
.age-btn {
  flex: 1;
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  background: #ffc0cb;
  color: #333;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, transform 0.1s;
}
.age-btn:hover {
  background: #ff9ebb;
}
.age-btn:active {
  transform: scale(0.97);
}
.age-btn.active {
  background: #ec407a;
  color: #fff;
}

/* Маленькие поля */
.form-select.sm, .form-input.sm {
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
}

/* Кнопка подтверждения опций */
.submit-btn {
  padding: 0.75rem;
  background: #ec407a;
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}
.submit-btn:hover {
  background: #e91e63;
}
.submit-btn:active {
  transform: scale(0.97);
}

/* Загрузка */
.loading {
  margin-top: 2rem;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  color: #fff;
}
.loader {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #ec407a;
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Адаптивные настройки */
@media (max-width: 768px) {
  .title-container {
    margin-top: 18vh;
  }
  .content {
    padding: 0.75rem;
    max-width: 100%;
  }
  .action-button {
    padding: 0.75rem;
    font-size: 0.85rem;
  }
  .text-analyzer-container {
    background-position: center 30px !important;
    padding-top: 50px;
  }
}

/* Добавляем космические стили для выпадающих списков */
.space-themed-panel {
  background: rgba(13, 23, 42, 0.8);
  border: 1px solid rgba(138, 180, 248, 0.5);
  border-radius: 12px;
  box-shadow: 0 0 15px rgba(138, 180, 248, 0.3), 0 0 30px rgba(138, 180, 248, 0.1) inset;
  padding: 20px;
  backdrop-filter: blur(8px);
  color: #ffffff;
}

/* ... other styles ... */

/* Стили для кнопок детализации плана урока */
.lesson-plan-details-buttons {
  margin-top: 2rem;
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
}

.lesson-plan-details-buttons h4 {
  color: #fff;
  font-size: 1.2rem;
  margin-bottom: 1rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.lesson-plan-details-buttons h5 {
  color: rgba(138, 180, 248, 1);
  font-size: 1rem;
  margin: 0.5rem 0;
  text-shadow: 0 0 5px rgba(138, 180, 248, 0.6);
}

.buttons-group {
  margin-bottom: 1.5rem;
}

.buttons-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.detail-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 24px;
  font-size: 0.9rem;
  background: #ffc0cb;
  color: #333;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}

.detail-button:hover {
  background: #ff9ebb;
}

.detail-button:active {
  transform: scale(0.97);
}

.detail-button.rewrite {
  background: rgba(138, 180, 248, 0.8);
  color: #fff;
}

.detail-button.rewrite:hover {
  background: rgba(138, 180, 248, 1);
}

/* Блок для отображения детализированной информации */
.detailed-content {
  margin-top: 1.5rem;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
}

.close-detail-button {
  display: block;
  margin: 1rem auto 0;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 24px;
  background: rgba(138, 180, 248, 0.8);
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}

.close-detail-button:hover {
  background: rgba(138, 180, 248, 1);
  transform: scale(1.05);
}

/* Стили для отображения вопросов */
.option-letter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #ff6b9a;
  color: white;
  font-weight: bold;
  margin-right: 10px;
}

.correct-badge {
  background-color: #4CAF50;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  margin-left: 10px;
}

.correct-answer-box {
  background-color: #f8ecf0;
  padding: 10px;
  border-radius: 5px;
  margin: 10px 0;
}
</style>
