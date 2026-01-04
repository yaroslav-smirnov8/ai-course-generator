<!-- src/components/LessonPlan.vue -->
<template>
  <!-- Добавляем атрибут data-route для идентификации -->
  <div class="exercise-like-container lesson-plan-container" 
       data-view="lesson-plan" 
       data-route="/lesson-plan"
       data-component="lesson-plan">
    <!-- Контент без дополнительных оберток -->
    <div class="content">
      <h2>Генерация плана урока</h2>
      <GenerationLimitsDisplay type="LESSON_PLAN" />
      <form @submit.prevent="generateLessonPlan" class="generation-form">
        <!-- Язык -->
        <div class="form-group">
          <label for="language">Язык:</label>
          <select v-model="formData.language" id="language" required class="form-select">
            <option value="english">Английский</option>
            <option value="spanish">Испанский</option>
            <option value="french">Французский</option>
            <option value="german">Немецкий</option>
            <option value="italian">Итальянский</option>
            <option value="chinese">Китайский</option>
            <option value="russian">Русский</option>
            <option value="arabic">Арабский</option>
          </select>
        </div>

        <!-- Возраст -->
        <div class="form-group">
          <label for="age">Возраст:</label>
          <div class="age-buttons">
            <button type="button" :class="['age-btn', { active: formData.age === 'children' }]" @click="formData.age = 'children'">
              Ребёнок
            </button>
            <button type="button" :class="['age-btn', { active: formData.age === 'teens' }]" @click="formData.age = 'teens'">
              Подросток
            </button>
            <button type="button" :class="['age-btn', { active: formData.age === 'adults' }]" @click="formData.age = 'adults'">
              Взрослый
            </button>
          </div>
        </div>

        <!-- Тема урока -->
        <div class="form-group">
          <label for="topic">Тема урока:</label>
          <input v-model="formData.topic" id="topic" required class="form-input" placeholder="Введите тему урока" />
        </div>

        <!-- Тема прошлого урока -->
        <div class="form-group">
          <label for="previous-lesson">Тема прошлого урока:</label>
          <textarea v-model="formData.previous_lesson" id="previous-lesson" class="form-textarea" placeholder="Что было на прошлом уроке?"></textarea>
        </div>

        <!-- Грамматика -->
        <div class="form-group">
          <label for="grammar">Грамматика:</label>
          <input v-model="formData.grammar" id="grammar" class="form-input" placeholder="Укажите грамматические темы" />
        </div>

        <!-- Лексика -->
        <div class="form-group">
          <label for="vocabulary">Лексика:</label>
          <input v-model="formData.vocabulary" id="vocabulary" class="form-input" placeholder="Укажите ключевую лексику" />
        </div>

        <!-- Формат урока -->
        <div class="form-group">
          <label>Формат урока:</label>
          <div class="format-grid">
            <button type="button" :class="['format-btn', { active: formData.individual_group === 'individual' }]" @click="formData.individual_group = 'individual'">
              <span class="icon">👤</span>
              <span>Индивидуально</span>
            </button>
            <button type="button" :class="['format-btn', { active: formData.individual_group === 'group' }]" @click="formData.individual_group = 'group'">
              <span class="icon">👥</span>
              <span>Группа</span>
            </button>
            <button type="button" :class="['format-btn', { active: formData.online_offline === 'online' }]" @click="formData.online_offline = 'online'">
              <span class="icon">💻</span>
              <span>Онлайн</span>
            </button>
            <button type="button" :class="['format-btn', { active: formData.online_offline === 'offline' }]" @click="formData.online_offline = 'offline'">
              <span class="icon">🏫</span>
              <span>Офлайн</span>
            </button>
          </div>
        </div>

        <!-- Экзамен (опционально) -->
        <div class="form-group">
          <label for="exam">Экзамен (опционально):</label>
          <input v-model="formData.exam" id="exam" class="form-input" placeholder="Например: IELTS, TOEFL и т.д." />
        </div>

        <!-- Кнопка отправки -->
        <div class="form-actions">
          <button type="submit" :disabled="isLoading" class="submit-btn">
            {{ isLoading ? 'Генерируем...' : 'Сгенерировать план' }}
          </button>
        </div>
      </form>

      <!-- Состояние загрузки -->
      <div v-if="isLoading" class="loading">
        <div class="loader"></div>
        <p>Создаём план урока...</p>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="clearError" class="error-close">✕</button>
      </div>

      <!-- Сгенерированный план -->
      <div v-if="generatedContent" class="result">
        <h3>Сгенерированный план урока:</h3>
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
        <div class="plan-content" v-html="formatContent(generatedContent)"></div>
      </div>
      
      <!-- Пространство для нижней навигации -->
      <div class="bottom-nav-spacer"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMainStore } from '@/store'
import type { LessonPlanFormData } from '@/store'
import { ContentType, ActionType } from '../core/constants'

// Импортируем SVG (убедитесь, что пути корректны)
// Закомментировали импорт фоновой планеты
// import planetBg from '@/assets/images/lesson_plan/plan-backgroud-image.svg'
import GenerationLimitsDisplay from "@/components/common/GenerationLimitsDisplay.vue";

const store = useMainStore()

const formData = ref<LessonPlanFormData>({
  language: 'english',
  age: 'teens',
  topic: '',
  previous_lesson: '',
  grammar: '',
  vocabulary: '',
  individual_group: 'individual',
  online_offline: 'online',
  exam: ''
})

const generatedContent = ref<string | null>(null)
const isLoading = computed(() => store.loading)
const error = computed(() => store.error)

// Закомментировали стиль фона
// const backgroundStyle = computed(() => ({
//   backgroundImage: `url(${planetBg})`,
//   backgroundSize: 'cover',
//   backgroundPosition: 'center',
//   backgroundRepeat: 'no-repeat',
//   backgroundAttachment: 'fixed'
// }))

// Функция для форматирования текста с курсивом
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
  formattedContent = formattedContent.replace(/\*\*([^*]+)\*\*/g, '<strong style="color: #000000 !important; background-color: #ffcce0 !important; padding: 0 5px !important; border-radius: 3px !important; display: inline-block !important; font-weight: bold !important;">$1</strong>');
  
  // Обработка курсива (между одинарными звездочками)
  formattedContent = formattedContent.replace(/\*([^*]+)\*/g, '<em style="color: #000000 !important; background-color: #ffe6ee !important; padding: 0 5px !important; border-radius: 3px !important; display: inline-block !important; font-style: italic !important;">$1</em>');
  
  // Обработка заголовков
  formattedContent = formattedContent
    // Заголовки (например, "1. Objectives:")
    .replace(/^(\d+\.\s+)(.+?)(:?)$/gm, '<h3 style="color: #ffffff !important; font-weight: bold !important; background-color: #ec407a !important; padding: 0.75rem 1rem !important; border-radius: 5px !important; display: inline-block !important; margin-bottom: 1rem !important;">$1$2$3</h3>')
    // Подзаголовки (например, "4.1 Vocabulary Building")
    .replace(/^(\d+\.\d+\s+)(.+?)(:?)$/gm, '<h4 style="color: #ffffff !important; font-weight: bold !important; background-color: #ff9ebb !important; padding: 0.5rem 0.75rem !important; border-radius: 4px !important; display: inline-block !important; margin-bottom: 0.75rem !important;">$1$2$3</h4>')
    // Заголовки с двойными звездочками (например, "**Total lesson time: 60 minutes**")
    .replace(/^<strong style="[^"]+">(.+?)<\/strong>$/gm, '<h3 style="color: #ffffff !important; font-weight: bold !important; background-color: #ec407a !important; padding: 0.75rem 1rem !important; border-radius: 5px !important; display: inline-block !important; margin-bottom: 1rem !important;">$1</h3>');
  
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
      result.push('<p style="color: #000000 !important; background-color: #f8f8f8 !important; padding: 0.75rem !important; border-radius: 4px !important; margin-bottom: 1rem !important; border-left: 4px solid #ec407a !important;">&nbsp;</p>'); // Добавляем пустой параграф для сохранения пробелов
      continue;
    }
    
    // Если строка начинается с заголовка (h3 или h4), закрываем список если он открыт
    if (line.startsWith('<h3') || line.startsWith('<h4')) {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      result.push(`<div class="section-header" style="margin-top: 1.5rem !important; margin-bottom: 1rem !important; display: block !important;">${line}</div>`);
      continue;
    }
    
    // Если строка начинается с дефиса
    if (line.startsWith('- ')) {
      // Если это первый элемент списка, открываем <ul>
      if (!inList) {
        result.push('<ul style="background-color: #f0f0f0 !important; padding: 0.75rem 0.75rem 0.75rem 2.5rem !important; border-radius: 4px !important; margin-bottom: 1.5rem !important; border-left: 4px solid #ec407a !important; list-style-type: disc !important; display: block !important;">');
        inList = true;
      }
      // Добавляем элемент списка
      result.push('<li style="color: #000000 !important; padding: 0.3rem 0 !important; margin-bottom: 0.5rem !important; display: list-item !important;">' + line.substring(2) + '</li>');
    } else {
      // Если это не элемент списка, но мы были в списке, закрываем его
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      
      // Добавляем строку как параграф
      result.push('<p style="color: #000000 !important; background-color: #f8f8f8 !important; padding: 0.75rem !important; border-radius: 4px !important; margin-bottom: 1rem !important; border-left: 4px solid #ec407a !important;">' + line + '</p>');
    }
  }
  
  // Если список не был закрыт, закрываем его
  if (inList) {
    result.push('</ul>');
  }
  
  // Объединяем строки обратно
  return result.join('');
}

const generateLessonPlan = async () => {
  try {
    generatedContent.value = null;
    store.clearError();

    // First check if we can generate based on limits
    if (!store.canGenerate(ContentType.LESSON_PLAN)) {
      store.setError('Daily limit reached for lesson plan generation. Please upgrade your tariff or try again tomorrow.');
      return; // Return early to prevent further execution
    }

    const requestData = {
      user_id: store.user?.id,
      type: ContentType.LESSON_PLAN,
      prompt: JSON.stringify(formData.value)
    };

    // Now actually generate the content - this will internally track the generation
    const result = await store.generateLessonPlan(formData.value);

    // Record the achievement after successful generation
    await store.checkAchievements(ActionType.GENERATION, {
      content_type: ContentType.LESSON_PLAN,
      language: formData.value.language,
      age: formData.value.age,
      topic: formData.value.topic
    });

    // Set the generated content to display it
    generatedContent.value = result;

    // Log success for debugging
    console.log('Lesson plan generated successfully:', result ? result.substring(0, 100) + '...' : 'No content');
  } catch (err: unknown) {
    console.error('Error generating lesson plan:', err);

    // Type guard for Error objects
    if (err instanceof Error) {
      if (err.message.includes('Daily limit')) {
        store.setError('Daily limit reached for lesson plan generation. Please upgrade your tariff or try again tomorrow.');
      } else {
        store.setError(`Error generating lesson plan: ${err.message}`);
      }
    }
    // Type guard for error objects with response property
    else if (typeof err === 'object' && err !== null && 'response' in err) {
      const apiError = err as { response?: { status?: number } };
      if (apiError.response?.status === 404) {
        store.setError('API endpoint not found. Please contact support.');
      } else {
        store.setError('Error generating lesson plan: API error');
      }
    }
    // Fallback for unknown error types
    else {
      store.setError('Error generating lesson plan: Unknown error');
    }
  }
}

const regenerate = () => {
  generateLessonPlan()
}

const clearError = () => {
  store.clearError()
}

const copyToClipboard = async () => {
  if (generatedContent.value) {
    try {
      await navigator.clipboard.writeText(generatedContent.value)
    } catch (err) {
      console.error('Не удалось скопировать текст:', err)
    }
  }
}
</script>

<style>
/* Контейнер в стиле компонента упражнений */
.exercise-like-container {
  width: 100%;
  min-height: 100vh;
  padding: 50px 0 0;
  box-sizing: border-box;
  /* Убираем дублирование фонового изображения */
  background-color: rgba(28, 5, 34, 0.3);
  backdrop-filter: blur(3px);
  overflow-x: hidden;
}

/* Стили для lesson-plan-container */
.lesson-plan-container {
  /* Изменяем с fixed на absolute для лучшего удаления */
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 50; /* Уменьшаем z-index */
  
  /* Видимость */
  display: block;
  visibility: visible;
  opacity: 1;
  
  /* Скроллинг */
  overflow-y: auto;
  
  /* Предотвращение воздействия на другие элементы DOM */
  isolation: isolate;
  
  /* Не задаем фоновое изображение */
  background-color: transparent;
}

/* Удаляем или модифицируем стили для planet-background, если он используется */
.planet-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1; /* Отрицательный z-index, чтобы был под контентом */
  pointer-events: none; /* Не перехватывает клики */
}

/* Блок с основным содержимым */
.content {
  max-width: 480px;
  margin: 0 auto;
  padding: 1rem;
  background-color: rgba(42, 8, 46, 0.25);
  backdrop-filter: blur(5px);
  border-radius: 16px;
}

/* Специальный элемент для создания отступа под навигацией */
.bottom-nav-spacer {
  width: 100%;
  height: 80px; /* Увеличенный отступ, чтобы точно не наезжало */
  display: block;
}

/* Заголовок */
.content h2 {
  color: white;
  font-size: 1.8rem;
  margin-bottom: 1rem;
  text-align: center;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

/* Стили для полей ввода и кнопок с нужным розовым цветом */
.form-input,
.form-select,
.form-textarea {
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
  background-color: rgba(255, 204, 243, 0.7) !important; /* FFCCF3 с прозрачностью 70% */
  color: #333;
  outline: none;
}

/* Группа кнопок возраста */
.age-buttons {
  display: flex;
  gap: 8px;
  width: 100%;
}

/* Кнопки возраста */
.age-btn {
  flex: 1;
  padding: 0.75rem 0.5rem;
  border: none;
  border-radius: 24px;
  font-size: 0.9rem;
  cursor: pointer;
  background-color: rgba(255, 204, 243, 0.7) !important; /* FFCCF3 с прозрачностью 70% */
  color: #333;
  transition: all 0.2s;
}

.age-btn.active {
  background-color: #ff67e7 !important;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

/* Сетка для кнопок формата */
.format-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

/* Кнопки формата */
.format-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem 0.5rem;
  border: none;
  border-radius: 24px;
  font-size: 0.9rem;
  cursor: pointer;
  background-color: rgba(255, 204, 243, 0.7) !important; /* FFCCF3 с прозрачностью 70% */
  color: #333;
  transition: all 0.2s;
}

.format-btn .icon {
  font-size: 1.5rem;
  margin-bottom: 5px;
}

.format-btn.active {
  background-color: #ff67e7 !important;
  color: white;
  box-shadow: 0 0 10px rgba(255, 103, 231, 0.5);
}

/* Кнопка отправки */
.submit-btn {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 24px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  background-color: rgba(255, 204, 243, 0.7) !important; /* FFCCF3 с прозрачностью 70% */
  color: #333;
  transition: all 0.2s;
}

.submit-btn:hover {
  background-color: #ff67e7 !important;
  color: white;
  box-shadow: 0 0 15px rgba(255, 103, 231, 0.6);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Контейнер с результатом */
.result {
  background-color: rgba(42, 8, 46, 0.25) !important; /* 2A082E с прозрачностью 25% */
  backdrop-filter: blur(5px);
  border-radius: 16px;
  padding: 1rem;
  margin-top: 1.5rem;
}

.result h3 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1rem;
  font-weight: bold;
}

/* Действия с результатом */
.result-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

/* Кнопки действий */
.action-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: rgba(255, 204, 243, 0.7) !important; /* FFCCF3 с прозрачностью 70% */
  color: #333;
  transition: all 0.2s;
}

.action-button:hover {
  background-color: #ff67e7 !important;
  color: white;
}

/* Стили для групп формы с нужным фиолетовым цветом */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background-color: rgba(42, 8, 46, 0.25) !important; /* 2A082E с прозрачностью 25% */
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 0.5rem;
}

.form-group label {
  color: white;
  font-weight: 500;
}

/* Контейнер для отправки формы */
.form-actions {
  background-color: rgba(42, 8, 46, 0.25) !important; /* 2A082E с прозрачностью 25% */
  border-radius: 16px;
  padding: 1rem;
  margin-top: 1rem;
}

/* Контент плана урока */
.plan-content {
  background-color: rgba(255, 204, 243, 0.7) !important; /* FFCCF3 с прозрачностью 70% */
  padding: 1rem;
  border-radius: 10px;
  margin-top: 1rem;
}

/* Индикатор загрузки */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
}

.loader {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #ff67e7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading p {
  color: white;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Стили для ошибки */
.error {
  background-color: rgba(220, 53, 69, 0.2);
  border-left: 4px solid #dc3545;
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 0 10px 10px 0;
  position: relative;
  color: white;
}

.error-close {
  position: absolute;
  top: 5px;
  right: 5px;
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
}

/* Фиксы для мобильных устройств */
@media (max-width: 768px) {
  .format-grid {
    grid-template-columns: 1fr;
  }
}
</style>
