<template>
  <div class="lesson-plan-extensions">
    <div v-if="lessonPlanData" class="extensions-container">
      <div class="extensions-header">
        <h3>Создать на основе плана урока</h3>
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
      </div>
      
      <!-- Панель для создания упражнений -->
      <v-expand-transition>
        <div v-if="showExercisesPanel" class="extension-panel">
          <v-card>
            <v-card-title class="d-flex align-center">
              <span>Создать упражнения на основе плана урока</span>
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
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="exerciseData.grammar"
                      label="Грамматика"
                    ></v-text-field>
                  </v-col>
                  
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="exerciseData.vocabulary"
                      label="Лексика"
                    ></v-text-field>
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
              <span>Создать игры на основе плана урока</span>
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
                      v-model="gameData.duration"
                      :items="[5, 10, 15, 20, 30]"
                      label="Продолжительность (мин)"
                      required
                    ></v-select>
                  </v-col>
                </v-row>
                
                <v-row>
                  <v-col cols="12">
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
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { toastService } from '@/services/toastService';
import { useContentStore } from '@/stores/content';
import { useUserStore } from '@/stores/user';

export default {
  name: 'LessonPlanExtensions',
  
  props: {
    lessonPlanData: {
      type: Object,
      default: null
    }
  },
  
  setup(props) {
    const router = useRouter();
    const contentStore = useContentStore();
    const userStore = useUserStore();
    
    // Состояние панелей
    const showExercisesPanel = ref(false);
    const showGamesPanel = ref(false);
    
    // Состояние загрузки
    const isGeneratingExercises = ref(false);
    const isGeneratingGames = ref(false);
    
    // Данные для создания упражнений
    const exerciseData = reactive({
      topic: '',
      language: 'English',
      level: 'Intermediate',
      exercise_type: 'grammar',
      difficulty: 'medium',
      quantity: 3,
      grammar: '',
      vocabulary: '',
      individual_group: 'individual'
    });
    
    // Данные для создания игр
    const gameData = reactive({
      topic: '',
      language: 'English',
      level: 'Intermediate',
      game_type: 'language',
      age: 'Adults',
      duration: 15,
      individual_group: 'individual',
      online_offline: 'online'
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
    
    // Наблюдение за изменениями в данных плана урока
    watch(() => props.lessonPlanData, (newValue) => {
      if (newValue) {
        // Заполняем данные для упражнений
        exerciseData.topic = newValue.topic || '';
        exerciseData.language = newValue.language || 'English';
        exerciseData.level = newValue.level || 'Intermediate';
        exerciseData.grammar = newValue.grammar || '';
        exerciseData.vocabulary = newValue.vocabulary || '';
        exerciseData.individual_group = newValue.individual_group || 'individual';
        
        // Заполняем данные для игр
        gameData.topic = newValue.topic || '';
        gameData.language = newValue.language || 'English';
        gameData.level = newValue.level || 'Intermediate';
        gameData.age = newValue.age || 'Adults';
        gameData.individual_group = newValue.individual_group || 'individual';
        gameData.online_offline = newValue.online_offline || 'online';
      }
    }, { immediate: true });
    
    // Методы для управления панелями
    const toggleExercisesPanel = () => {
      showExercisesPanel.value = !showExercisesPanel.value;
      if (showExercisesPanel.value) {
        showGamesPanel.value = false;
      }
    };
    
    const toggleGamesPanel = () => {
      showGamesPanel.value = !showGamesPanel.value;
      if (showGamesPanel.value) {
        showExercisesPanel.value = false;
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
          grammar: exerciseData.grammar || 'N/A',
          vocabulary: exerciseData.vocabulary || 'N/A',
          individual_group: exerciseData.individual_group
        };
        
        // Отправляем запрос на создание упражнений
        const response = await contentStore.generateExercises(requestData);
        
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
          duration: gameData.duration,
          individual_group: gameData.individual_group,
          online_offline: gameData.online_offline
        };
        
        // Отправляем запрос на создание игр
        const response = await contentStore.generateGame(requestData);
        
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
    
    return {
      // Состояние панелей
      showExercisesPanel,
      showGamesPanel,
      
      // Состояние загрузки
      isGeneratingExercises,
      isGeneratingGames,
      
      // Данные для форм
      exerciseData,
      gameData,
      
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
      createExercises,
      createGames
    };
  }
};
</script>

<style scoped>
.lesson-plan-extensions {
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
}

.extension-btn {
  min-width: 150px;
}

.extension-panel {
  margin-top: 16px;
  margin-bottom: 24px;
}
</style> 