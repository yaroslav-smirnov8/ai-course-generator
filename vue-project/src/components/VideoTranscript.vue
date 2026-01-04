<template>
  <div class="video-transcript">
    <h2>Process Video Transcript</h2>

    <!-- Step 1: Get Transcript -->
    <form @submit.prevent="processTranscript" class="transcript-form" v-if="!transcript">
      <div class="form-group">
        <label for="video-id">YouTube Video ID:</label>
        <input
          v-model="formData.video_id"
          id="video-id"
          required
          class="form-input"
          placeholder="Enter YouTube Video ID"
        >
      </div>

      <div class="form-group">
        <label for="subtitle-language">Subtitles Language:</label>
        <select v-model="formData.subtitle_language" id="subtitle-language" required class="form-input">
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
        </select>
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="isLoading" class="submit-btn">
          {{ isLoading ? 'Processing...' : 'Get Transcript' }}
        </button>
      </div>
    </form>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading">
      <div class="loader"></div>
      <p>Processing video transcript...</p>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="clearError" class="error-close">✕</button>
    </div>

    <!-- Transcript Result -->
    <div v-if="transcript" class="result">
      <h3>Video Transcript:</h3>
      <div class="transcript-container">
        <pre class="transcript-content">{{ transcript }}</pre>
      </div>
      
      <!-- Заменяем старые кнопки на компонент расширений -->
      <video-transcript-extensions 
        :transcript-data="{ title: formData.title, language: formData.language }"
        :video-id="formData.videoId"
        :transcript="transcript"
      ></video-transcript-extensions>
      
      <!-- Удаляем старую форму генерации -->
      <div class="generation-form" v-if="!exercises && !games && !lessonPlan" style="display: none;">
        <h3>Generate Content from Transcript:</h3>
        <div class="generation-buttons">
          <button 
            class="btn primary-btn"
            @click="generateExercisesFromTranscript"
            :disabled="isGenerating"
          >
            Generate Exercises
          </button>
          <button 
            class="btn success-btn"
            @click="generateGamesFromTranscript"
            :disabled="isGenerating"
          >
            Generate Games
          </button>
          <button 
            class="btn info-btn"
            @click="generateLessonPlanFromTranscript"
            :disabled="isGenerating"
          >
            Generate Lesson Plan
          </button>
        </div>
      </div>
      
      <!-- Скрываем старые результаты генерации -->
      <div v-if="exercises" class="result" style="display: none;">
        <h3>Generated Exercises:</h3>
        <button @click="exercises = null" class="back-button">← Back to generation options</button>
        <pre class="generated-content">{{ exercises }}</pre>
      </div>
      
      <div v-if="games" class="result" style="display: none;">
        <h3>Generated Games:</h3>
        <button @click="games = null" class="back-button">← Back to generation options</button>
        <pre class="generated-content">{{ games }}</pre>
      </div>
      
      <div v-if="lessonPlan" class="result" style="display: none;">
        <h3>Generated Lesson Plan:</h3>
        <button @click="lessonPlan = null" class="back-button">← Back to generation options</button>
        <pre class="generated-content">{{ lessonPlan }}</pre>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';
import { useMainStore } from '@/store';
import VideoTranscriptExtensions from './VideoTranscriptExtensions.vue';

interface TranscriptFormData {
  video_id: string;
  subtitle_language: string;
  title: string;
  language: string;
  videoId: string;
}

interface GenerationData {
  language: string;
  topic: string;
}

export default defineComponent({
  name: 'VideoTranscript',
  components: {
    VideoTranscriptExtensions
  },

  // Добавляем emit для события transcript-ready
  emits: ['transcript-ready'],

  setup(props, { emit }) {
    const store = useMainStore();
    const formData = ref<TranscriptFormData>({
      video_id: '',
      subtitle_language: 'en',
      title: '',
      language: '',
      videoId: ''
    });

    const generationData = ref<GenerationData>({
      language: '',
      topic: ''
    });

    const transcript = ref<string | null>(null);
    const exercises = ref<string | null>(null);
    const games = ref<string | null>(null);
    const lessonPlan = ref<string | null>(null);
    const isGenerating = ref(false);

    const isLoading = computed(() => store.loading);
    const error = computed(() => store.error);

    const processTranscript = async () => {
      try {
        isLoading.value = true;
        errorMessage.value = '';
        transcript.value = null;
        exercises.value = null;
        games.value = null;
        lessonPlan.value = null;
        
        // Сохраняем ID видео для использования в компоненте расширений
        if (formData.value) {
          formData.value.videoId = formData.value.video_id;
        
          // Устанавливаем заголовок по умолчанию
          formData.value.title = `Video ${formData.value.video_id}`;
          
          // Устанавливаем язык для компонента расширений
          formData.value.language = formData.value.subtitle_language === 'en' ? 'English' : 
                                  formData.value.subtitle_language === 'es' ? 'Spanish' :
                                  formData.value.subtitle_language === 'fr' ? 'French' :
                                  formData.value.subtitle_language === 'de' ? 'German' :
                                  formData.value.subtitle_language === 'it' ? 'Italian' :
                                  formData.value.subtitle_language === 'ru' ? 'Russian' :
                                  formData.value.subtitle_language === 'zh' ? 'Chinese' :
                                  formData.value.subtitle_language === 'ja' ? 'Japanese' :
                                  formData.value.subtitle_language === 'ko' ? 'Korean' :
                                  formData.value.subtitle_language === 'ar' ? 'Arabic' : 'English';
        }
        
        const result = await store.processVideoTranscript({
          video_id: formData.value.video_id,
          subtitle_language: formData.value.subtitle_language,
          user_id: store.user?.id || 0
        });

        console.log('Тип полученного результата:', typeof result);
        console.log('Результат получения транскрипта:', result);

        if (!result) {
          console.error('Результат пуст или undefined');
          store.setError('Не удалось получить транскрипт видео - пустой ответ от сервера');
          return;
        }

        transcript.value = result;
        
        // Определяем язык на основе subtitle_language
        const language = formData.value.subtitle_language === 'en' ? 'English' : 
                        formData.value.subtitle_language === 'es' ? 'Spanish' :
                        formData.value.subtitle_language === 'fr' ? 'French' :
                        formData.value.subtitle_language === 'de' ? 'German' :
                        formData.value.subtitle_language === 'it' ? 'Italian' :
                        formData.value.subtitle_language === 'ru' ? 'Russian' :
                        formData.value.subtitle_language === 'zh' ? 'Chinese' :
                        formData.value.subtitle_language === 'ja' ? 'Japanese' :
                        formData.value.subtitle_language === 'ko' ? 'Korean' :
                        formData.value.subtitle_language === 'ar' ? 'Arabic' : 'English';
        
        // Генерируем событие transcript-ready
        emit('transcript-ready', {
          transcript: result,
          videoId: formData.value.video_id,
          title: `Video ${formData.value.video_id}`,
          language: language
        });
      } catch (error: any) {
        console.error('Ошибка при получении транскрипта:', error);
        store.setError(error.message || 'Не удалось получить транскрипт видео');
      } finally {
        isLoading.value = false;
      }
    };

    const generateExercisesFromTranscript = async () => {
      try {
        isGenerating.value = true;
        exercises.value = null;
        store.clearError();

        const result = await store.generateExercisesFromTranscript({
          video_id: formData.value.video_id,
          language: generationData.value.language,
          topic: generationData.value.topic,
          difficulty: 'medium',
          exercise_type: 'grammar',
          quantity: 3
        });

        exercises.value = result;
      } catch (error: any) {
        console.error('Error generating exercises:', error);
      } finally {
        isGenerating.value = false;
      }
    };

    const generateGamesFromTranscript = async () => {
      try {
        isGenerating.value = true;
        games.value = null;
        store.clearError();

        const result = await store.generateGamesFromTranscript({
          video_id: formData.value.video_id,
          language: generationData.value.language,
          topic: generationData.value.topic,
          game_type: 'language',
          duration: 15
        });

        games.value = result;
      } catch (error: any) {
        console.error('Error generating games:', error);
      } finally {
        isGenerating.value = false;
      }
    };

    const generateLessonPlanFromTranscript = async () => {
      try {
        isGenerating.value = true;
        lessonPlan.value = null;
        store.clearError();

        const result = await store.generateLessonPlanFromTranscript({
          video_id: formData.value.video_id,
          language: generationData.value.language,
          topic: generationData.value.topic,
          age: 'adults',
          individual_group: 'individual',
          online_offline: 'online'
        });

        lessonPlan.value = result;
      } catch (error: any) {
        console.error('Error generating lesson plan:', error);
      } finally {
        isGenerating.value = false;
      }
    };

    const clearError = () => {
      store.clearError();
    };

    return {
      formData,
      generationData,
      transcript,
      exercises,
      games,
      lessonPlan,
      isLoading,
      isGenerating,
      error,
      processTranscript,
      generateExercisesFromTranscript,
      generateGamesFromTranscript,
      generateLessonPlanFromTranscript,
      clearError
    };
  }
});
</script>

<style scoped>
.video-transcript {
  max-width: 100%;
  margin: 0 auto;
  padding: 1rem;
  box-sizing: border-box;
}

h2, h3 {
  text-align: center;
  margin-bottom: 1.5rem;
}

h2 {
  font-size: 1.5rem;
}

h3 {
  font-size: 1.2rem;
}

.transcript-form, .generation-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 500;
  font-size: 0.9rem;
  color: #333;
}

.form-input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  background-color: white;
  width: 100%;
}

.submit-btn, .action-button, .back-button {
  padding: 1rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn {
  background: #4CAF50;
  color: white;
}

.action-button {
  background: #2196F3;
  color: white;
}

.back-button {
  background: #f5f5f5;
  color: #333;
  margin-bottom: 1rem;
}

.submit-btn:disabled,
.action-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.generation-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.loading {
  margin: 2rem 0;
  text-align: center;
}

.loader {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4CAF50;
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  margin: 1rem 0;
  padding: 1rem;
  background: #ffebee;
  border-radius: 8px;
  color: #c62828;
  position: relative;
}

.error-close {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  color: #c62828;
  font-size: 1.2rem;
  cursor: pointer;
}

.transcript-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.transcript-content,
.generated-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.9rem;
  line-height: 1.5;
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 8px;
}

/* Mobile optimizations */
@media (max-width: 768px) {
  .video-transcript {
    padding: 0.5rem;
  }

  .generation-buttons {
    flex-direction: column;
  }

  .action-button {
    width: 100%;
  }
}

/* Dark theme support */
:root[data-theme="dark"] {
  .video-transcript {
    background: #1f1f1f;
    color: #fff;
  }

  .form-input {
    background-color: #2d2d2d;
    border-color: #3d3d3d;
    color: #fff;
  }

  label {
    color: #fff;
  }

  .back-button {
    background: #2d2d2d;
    color: #fff;
  }

  .transcript-content,
  .generated-content {
    background: #2d2d2d;
    color: #fff;
  }

  .transcript-container {
    border-color: #3d3d3d;
  }
}

/* Стилизация результатов */
.transcript-content {
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
  background-color: #3f51b5 !important; /* Синий фон для заголовков */
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
  background-color: #7986cb !important; /* Более светлый синий фон для подзаголовков */
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
  border-left: 4px solid #3f51b5 !important; /* Синяя полоса слева */
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
  border-left: 4px solid #3f51b5 !important;
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
  background-color: #c5cae9 !important; /* Светло-синий фон для жирного текста */
  padding: 0 5px !important;
  border-radius: 3px !important;
  border-bottom: 1px solid #3f51b5 !important;
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
  background-color: #e8eaf6 !important; /* Светло-синий фон для курсива */
  padding: 0 5px !important;
  border-radius: 3px !important;
  display: inline-block !important;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.2) !important;
  border-bottom: 1px solid #3f51b5 !important;
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

/* Стили для самого транскрипта */
.transcript-text {
  all: initial !important;
  display: block !important;
  font-family: Arial, sans-serif !important;
  background: #ffffff !important;
  color: #000000 !important;
  padding: 1.5rem !important;
  border-radius: 8px !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
  margin-top: 1rem;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.3) !important;
  border: 2px solid #000 !important;
  position: relative !important;
  z-index: 10 !important;
  isolation: isolate !important;
  white-space: pre-wrap !important;
}

/* Медиа запросы для адаптивности */
@media (max-width: 768px) {
  .transcript-content,
  .transcript-text {
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
    white-space: pre-wrap !important;
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
    background-color: #3f51b5 !important;
    border-radius: 5px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
    font-family: Arial, sans-serif !important;
    line-height: 1.6 !important;
  }
  
  :deep(.prose h4) {
    background-color: #7986cb !important;
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
    border-left: 4px solid #3f51b5 !important;
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
    border-left: 4px solid #3f51b5 !important;
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
    background-color: #e8eaf6 !important;
    display: inline-block !important;
    font-family: Arial, sans-serif !important;
    border-radius: 3px !important;
  }
  
  :deep(.prose em) {
    font-style: italic !important;
    font-weight: 600 !important;
    border-bottom: 1px solid #3f51b5 !important;
  }
  
  :deep(.prose strong) {
    font-weight: bold !important;
    background-color: #c5cae9 !important;
    border-bottom: 1px solid #3f51b5 !important;
  }
}
</style>
