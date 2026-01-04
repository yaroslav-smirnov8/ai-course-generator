<template>
  <div class="transcript-extensions">
    <div v-if="transcriptData" class="extensions-container">
      <div class="extensions-header">
        <h3>Создать на основе транскрипта</h3>
      </div>
      
      <div class="extensions-buttons">
        <v-btn 
          color="primary" 
          variant="outlined" 
          prepend-icon="mdi-book-open-variant" 
          @click="toggleExercisesPanel"
          class="extension-btn"
        >
          Упражнения
        </v-btn>
        
        <v-btn 
          color="success" 
          variant="outlined" 
          prepend-icon="mdi-gamepad-variant" 
          @click="toggleGamesPanel"
          class="extension-btn"
        >
          Игры
        </v-btn>
        
        <v-btn 
          color="info" 
          variant="outlined" 
          prepend-icon="mdi-notebook" 
          @click="toggleLessonPlanPanel"
          class="extension-btn"
        >
          План урока
        </v-btn>
      </div>
      
      <!-- Панель для создания упражнений -->
      <v-expand-transition>
        <div v-if="showExercisesPanel" class="extension-panel">
          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Создать упражнения на основе транскрипта</span>
              <v-spacer></v-spacer>
              <v-btn icon @click="toggleExercisesPanel">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            
            <v-card-text>
              <v-form ref="exerciseForm">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="exerciseData.topic"
                      label="Тема"
                      required
                    ></v-text-field>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="exerciseData.language"
                      :items="languageOptions"
                      label="Язык"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="exerciseData.level"
                      :items="levelOptions"
                      label="Уровень"
                      required
                    ></v-select>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="exerciseData.exercise_type"
                      :items="exerciseTypeOptions"
                      label="Тип упражнения"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="exerciseData.difficulty"
                      :items="difficultyOptions"
                      label="Сложность"
                      required
                    ></v-select>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="exerciseData.quantity"
                      :items="[1, 2, 3, 4, 5]"
                      label="Количество упражнений"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12">
                    <v-select
                      v-model="exerciseData.individual_group"
                      :items="formatOptions"
                      label="Формат урока"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
              </v-form>
            </v-card-text>
            
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn 
                color="primary" 
                @click="createExercises"
                :loading="isGeneratingExercises"
              >
                Создать упражнения
              </v-btn>
            </v-card-actions>
          </v-card>
        </div>
      </v-expand-transition>
      
      <!-- Панель для создания игр -->
      <v-expand-transition>
        <div v-if="showGamesPanel" class="extension-panel">
          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Создать игры на основе транскрипта</span>
              <v-spacer></v-spacer>
              <v-btn icon @click="toggleGamesPanel">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            
            <v-card-text>
              <v-form ref="gameForm">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="gameData.topic"
                      label="Тема"
                      required
                    ></v-text-field>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="gameData.language"
                      :items="languageOptions"
                      label="Язык"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="gameData.level"
                      :items="levelOptions"
                      label="Уровень"
                      required
                    ></v-select>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="gameData.game_type"
                      :items="gameTypeOptions"
                      label="Тип игры"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="gameData.age"
                      :items="ageOptions"
                      label="Возрастная группа"
                      required
                    ></v-select>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="gameData.individual_group"
                      :items="formatOptions"
                      label="Формат урока"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12">
                    <v-select
                      v-model="gameData.online_offline"
                      :items="onlineOfflineOptions"
                      label="Формат проведения"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
              </v-form>
            </v-card-text>
            
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn 
                color="success" 
                @click="createGames"
                :loading="isGeneratingGames"
              >
                Создать игры
              </v-btn>
            </v-card-actions>
          </v-card>
        </div>
      </v-expand-transition>
      
      <!-- Панель для создания плана урока -->
      <v-expand-transition>
        <div v-if="showLessonPlanPanel" class="extension-panel">
          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Создать план урока на основе транскрипта</span>
              <v-spacer></v-spacer>
              <v-btn icon @click="toggleLessonPlanPanel">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>
            
            <v-card-text>
              <v-form ref="lessonPlanForm">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="lessonPlanData.topic"
                      label="Тема"
                      required
                    ></v-text-field>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="lessonPlanData.language"
                      :items="languageOptions"
                      label="Язык"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="lessonPlanData.level"
                      :items="levelOptions"
                      label="Уровень"
                      required
                    ></v-select>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="lessonPlanData.age"
                      :items="ageOptions"
                      label="Возрастная группа"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="lessonPlanData.individual_group"
                      :items="formatOptions"
                      label="Формат урока"
                      required
                    ></v-select>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="lessonPlanData.online_offline"
                      :items="onlineOfflineOptions"
                      label="Формат проведения"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="lessonPlanData.grammar"
                      label="Грамматика"
                    ></v-text-field>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="lessonPlanData.vocabulary"
                      label="Лексика"
                    ></v-text-field>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12">
                    <v-text-field
                      v-model="lessonPlanData.previous_lesson"
                      label="Предыдущий урок"
                    ></v-text-field>
                  </v-col>
                </v-row>
              </v-form>
            </v-card-text>
            
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn 
                color="info" 
                @click="createLessonPlan"
                :loading="isGeneratingLessonPlan"
              >
                Создать план урока
              </v-btn>
            </v-card-actions>
          </v-card>
        </div>
      </v-expand-transition>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { toastService } from '@/services/toastService';
import { useMainStore } from '../store';

export default {
  name: 'VideoTranscriptExtensions',
  
  props: {
    transcriptData: {
      type: Object,
      default: null
    },
    videoId: {
      type: String,
      default: ''
    },
    transcript: {
      type: String,
      default: ''
    }
  },
  
  setup(props) {
    const router = useRouter();
    const store = useMainStore();
    
    // Состояние панелей
    const showExercisesPanel = ref(false);
    const showGamesPanel = ref(false);
    const showLessonPlanPanel = ref(false);
    
    // Состояние загрузки
    const isGeneratingExercises = ref(false);
    const isGeneratingGames = ref(false);
    const isGeneratingLessonPlan = ref(false);
    
    // Данные для создания упражнений
    const exerciseData = reactive({
      topic: '',
      language: 'English',
      level: 'Intermediate',
      exercise_type: 'grammar',
      difficulty: 'medium',
      quantity: 3,
      individual_group: 'individual',
      video_id: ''
    });
    
    // Данные для создания игр
    const gameData = reactive({
      topic: '',
      language: 'English',
      level: 'Intermediate',
      game_type: 'language',
      age: 'Adults',
      individual_group: 'individual',
      online_offline: 'online',
      video_id: ''
    });
    
    // Данные для создания плана урока
    const lessonPlanData = reactive({
      topic: '',
      language: 'English',
      level: 'Intermediate',
      age: 'Adults',
      individual_group: 'individual',
      online_offline: 'online',
      grammar: '',
      vocabulary: '',
      previous_lesson: '',
      video_id: ''
    });
    
    // Опции для селектов
    const languageOptions = [
      'English', 'Spanish', 'French', 'German', 'Italian', 
      'Russian', 'Chinese', 'Japanese', 'Korean', 'Arabic'
    ];
    
    const levelOptions = [
      'Beginner', 'Elementary', 'Pre-Intermediate', 
      'Intermediate', 'Upper-Intermediate', 'Advanced', 'Proficiency'
    ];
    
    const exerciseTypeOptions = [
      'grammar', 'vocabulary', 'reading', 'writing', 
      'listening', 'speaking', 'pronunciation', 'mixed'
    ];
    
    const gameTypeOptions = [
      'language', 'vocabulary', 'grammar', 'speaking', 
      'listening', 'reading', 'writing', 'cultural', 
      'warm-up', 'review'
    ];
    
    const difficultyOptions = ['easy', 'medium', 'hard'];
    
    const formatOptions = ['individual', 'group'];
    
    const onlineOfflineOptions = ['online', 'offline'];
    
    const ageOptions = [
      'Young Learners (3-7)', 'Children (5-12)', 
      'Teenagers (13-17)', 'Adults (18+)', 'Seniors (65+)'
    ];
    
    // Наблюдение за изменениями в данных транскрипта и ID видео
    watch(() => [props.transcriptData, props.videoId], ([newTranscriptData, newVideoId]) => {
      if (newTranscriptData) {
        // Заполняем данные для упражнений
        exerciseData.topic = newTranscriptData.title || '';
        exerciseData.language = newTranscriptData.language || 'English';
        exerciseData.video_id = newVideoId || '';
        
        // Заполняем данные для игр
        gameData.topic = newTranscriptData.title || '';
        gameData.language = newTranscriptData.language || 'English';
        gameData.video_id = newVideoId || '';
        
        // Заполняем данные для плана урока
        lessonPlanData.topic = newTranscriptData.title || '';
        lessonPlanData.language = newTranscriptData.language || 'English';
        lessonPlanData.video_id = newVideoId || '';
      }
    }, { immediate: true });
    
    // Методы для управления панелями
    const toggleExercisesPanel = () => {
      showExercisesPanel.value = !showExercisesPanel.value;
      if (showExercisesPanel.value) {
        showGamesPanel.value = false;
        showLessonPlanPanel.value = false;
      }
    };
    
    const toggleGamesPanel = () => {
      showGamesPanel.value = !showGamesPanel.value;
      if (showGamesPanel.value) {
        showExercisesPanel.value = false;
        showLessonPlanPanel.value = false;
      }
    };
    
    const toggleLessonPlanPanel = () => {
      showLessonPlanPanel.value = !showLessonPlanPanel.value;
      if (showLessonPlanPanel.value) {
        showExercisesPanel.value = false;
        showGamesPanel.value = false;
      }
    };
    
    // Метод для создания упражнений
    const createExercises = async () => {
      try {
        isGeneratingExercises.value = true;
        
        // Подготавливаем данные для запроса
        const requestData = {
          topic: exerciseData.topic,
          language: exerciseData.language,
          level: exerciseData.level,
          exercise_type: exerciseData.exercise_type,
          difficulty: exerciseData.difficulty,
          quantity: exerciseData.quantity,
          individual_group: exerciseData.individual_group,
          video_id: exerciseData.video_id
        };
        
        // Отправляем запрос на создание упражнений
        const response = await store.generateExercisesFromTranscript({
          ...requestData,
          transcript: props.transcript
        });
        
        // Переходим на страницу с созданными упражнениями
        if (response && response.id) {
          router.push({ name: 'content-view', params: { id: response.id } });
          toastService.success('Упражнения успешно созданы!');
        }
      } catch (error) {
        console.error('Ошибка при создании упражнений:', error);
        toastService.error('Ошибка при создании упражнений. Пожалуйста, попробуйте еще раз.');
      } finally {
        isGeneratingExercises.value = false;
      }
    };
    
    // Метод для создания игр
    const createGames = async () => {
      try {
        isGeneratingGames.value = true;
        
        // Подготавливаем данные для запроса
        const requestData = {
          topic: gameData.topic,
          language: gameData.language,
          level: gameData.level,
          game_type: gameData.game_type,
          age: gameData.age,
          individual_group: gameData.individual_group,
          online_offline: gameData.online_offline,
          video_id: gameData.video_id
        };
        
        // Отправляем запрос на создание игр
        const response = await store.generateGamesFromTranscript({
          ...requestData,
          transcript: props.transcript
        });
        
        // Переходим на страницу с созданными играми
        if (response && response.id) {
          router.push({ name: 'content-view', params: { id: response.id } });
          toastService.success('Игры успешно созданы!');
        }
      } catch (error) {
        console.error('Ошибка при создании игр:', error);
        toastService.error('Ошибка при создании игр. Пожалуйста, попробуйте еще раз.');
      } finally {
        isGeneratingGames.value = false;
      }
    };
    
    // Метод для создания плана урока
    const createLessonPlan = async () => {
      try {
        isGeneratingLessonPlan.value = true;
        
        // Подготавливаем данные для запроса
        const requestData = {
          topic: lessonPlanData.topic,
          language: lessonPlanData.language,
          level: lessonPlanData.level,
          age: lessonPlanData.age,
          individual_group: lessonPlanData.individual_group,
          online_offline: lessonPlanData.online_offline,
          grammar: lessonPlanData.grammar || 'N/A',
          vocabulary: lessonPlanData.vocabulary || 'N/A',
          previous_lesson: lessonPlanData.previous_lesson || 'N/A',
          video_id: lessonPlanData.video_id
        };
        
        // Отправляем запрос на создание плана урока
        const response = await store.generateLessonPlanFromTranscript({
          ...requestData,
          transcript: props.transcript
        });
        
        // Переходим на страницу с созданным планом урока
        if (response && response.id) {
          router.push({ name: 'content-view', params: { id: response.id } });
          toastService.success('План урока успешно создан!');
        }
      } catch (error) {
        console.error('Ошибка при создании плана урока:', error);
        toastService.error('Ошибка при создании плана урока. Пожалуйста, попробуйте еще раз.');
      } finally {
        isGeneratingLessonPlan.value = false;
      }
    };
    
    return {
      // Состояние панелей
      showExercisesPanel,
      showGamesPanel,
      showLessonPlanPanel,
      
      // Состояние загрузки
      isGeneratingExercises,
      isGeneratingGames,
      isGeneratingLessonPlan,
      
      // Данные для форм
      exerciseData,
      gameData,
      lessonPlanData,
      
      // Опции для селектов
      languageOptions,
      levelOptions,
      exerciseTypeOptions,
      gameTypeOptions,
      difficultyOptions,
      formatOptions,
      onlineOfflineOptions,
      ageOptions,
      
      // Методы
      toggleExercisesPanel,
      toggleGamesPanel,
      toggleLessonPlanPanel,
      createExercises,
      createGames,
      createLessonPlan
    };
  }
};
</script>

<style scoped>
.transcript-extensions {
  margin-top: 20px;
  border-top: 1px solid #e0e0e0;
  padding-top: 20px;
}

.extensions-container {
  width: 100%;
}

.extensions-header {
  margin-bottom: 16px;
}

.extensions-buttons {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.extension-btn {
  min-width: 150px;
}

.extension-panel {
  margin-top: 16px;
  margin-bottom: 24px;
}
</style> 