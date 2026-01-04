<template>
  <div class="w-full max-w-4xl mx-auto p-4 space-y-6">
    <div v-if="lesson" class="bg-gray-800 rounded-lg p-6">
      <div class="flex justify-between items-start mb-6">
        <h2 class="text-xl font-bold text-white">{{ lesson.title }}</h2>
        <button
          @click="$emit('back')"
          class="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600"
        >
          Назад
        </button>
      </div>

      <!-- Основная информация о уроке -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 text-sm">
        <div v-if="lesson.duration">
          <span class="text-gray-400">Длительность:</span>
          <span class="text-white ml-2">{{ lesson.duration }} минут</span>
        </div>
        <div v-if="courseName">
          <span class="text-gray-400">Курс:</span>
          <span class="text-white ml-2">{{ courseName }}</span>
        </div>
      </div>

      <!-- Цели урока -->
      <div v-if="lesson.objectives && lesson.objectives.length > 0" class="mb-6">
        <h3 class="text-lg font-bold text-white mb-3">Цели урока</h3>
        <ul class="list-disc list-inside text-gray-300 space-y-1">
          <li v-for="(objective, index) in lesson.objectives" :key="index">
            {{ objective }}
          </li>
        </ul>
      </div>

      <!-- Грамматика -->
      <div v-if="lesson.grammar && lesson.grammar.length > 0" class="mb-6">
        <h3 class="text-lg font-bold text-white mb-3">Грамматика</h3>
        <ul class="list-disc list-inside text-gray-300 space-y-1">
          <li v-for="(item, index) in lesson.grammar" :key="index">
            {{ item }}
          </li>
        </ul>
      </div>

      <!-- Словарь -->
      <div v-if="lesson.vocabulary && lesson.vocabulary.length > 0" class="mb-6">
        <h3 class="text-lg font-bold text-white mb-3">Словарь</h3>
        <ul class="list-disc list-inside text-gray-300 space-y-1">
          <li v-for="(item, index) in lesson.vocabulary" :key="index">
            {{ item }}
          </li>
        </ul>
      </div>

      <!-- Активности -->
      <div v-if="lesson.activities && lesson.activities.length > 0" class="mb-6">
        <h3 class="text-lg font-bold text-white mb-3">Активности</h3>
        <div v-for="(activity, index) in lesson.activities" :key="index"
             class="border border-gray-700 rounded-lg p-4 mb-3">
          <div class="flex justify-between items-start mb-2">
            <h4 class="font-medium text-white">{{ activity.name }}</h4>
            <span class="text-sm text-gray-400">{{ activity.duration }} минут</span>
          </div>
          <p class="text-gray-300 text-sm mb-2">{{ activity.description }}</p>
          <div v-if="activity.type" class="text-sm text-gray-400">
            Тип: {{ formatActivityType(activity.type) }}
          </div>
          <div v-if="activity.materials && activity.materials.length > 0" class="mt-2">
            <span class="text-sm font-medium text-gray-400">Материалы:</span>
            <ul class="list-disc list-inside text-sm text-gray-300 mt-1">
              <li v-for="(material, matIndex) in activity.materials" :key="matIndex">
                {{ material }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Материалы -->
      <div v-if="lesson.materials && lesson.materials.length > 0" class="mb-6">
        <h3 class="text-lg font-bold text-white mb-3">Материалы</h3>
        <ul class="list-disc list-inside text-gray-300 space-y-1">
          <li v-for="(material, index) in lesson.materials" :key="index">
            {{ material }}
          </li>
        </ul>
      </div>

      <!-- Домашнее задание -->
      <div v-if="lesson.homework" class="mb-6">
        <h3 class="text-lg font-bold text-white mb-3">Домашнее задание</h3>
        <div class="bg-gray-700 rounded-lg p-4">
          <p class="text-gray-300 mb-3">{{ lesson.homework.description }}</p>
          <div v-if="lesson.homework.tasks && lesson.homework.tasks.length > 0">
            <h4 class="font-medium text-white mb-2">Задания:</h4>
            <ul class="list-disc list-inside text-gray-300 space-y-1">
              <li v-for="(task, index) in lesson.homework.tasks" :key="index">
                {{ task }}
              </li>
            </ul>
          </div>
          <div v-if="lesson.homework.estimatedTime" class="mt-3 text-sm text-gray-400">
            Примерное время выполнения: {{ lesson.homework.estimatedTime }} минут
          </div>
        </div>
      </div>

      <!-- Информация о лимитах и баллах -->
      <div class="flex flex-wrap gap-3 mt-4 mb-4">
        <div class="w-full md:w-auto">
          <GenerationLimitsDisplay :content-type="ContentType.LESSON_PLAN" />
        </div>
        <div class="w-full md:w-auto points-info">
          <span class="points-icon">💎</span> Баллов: {{ mainStore.userPoints }}
          <span class="points-cost">(Стоимость: 8 баллов)</span>
        </div>
      </div>

      <!-- Кнопки действий -->
      <div class="flex flex-wrap gap-3 mt-6">
        <div class="flex flex-col gap-2 w-full md:w-auto">
          <button
            @click="generatePlan"
            :disabled="isGeneratingPlan"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-600"
          >
            {{ isGeneratingPlan ? 'Генерация плана...' : 'Сгенерировать план урока' }}
          </button>
          <button
            @click="generatePlanWithPoints"
            :disabled="isGeneratingPlan || mainStore.userPoints < 8"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600"
          >
            <span class="mr-1">💎</span> За баллы
          </button>
        </div>

        <div class="flex flex-col gap-2 w-full md:w-auto">
          <button
            @click="generateExercises"
            :disabled="isGeneratingExercises"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-600"
          >
            {{ isGeneratingExercises ? 'Генерация упражнений...' : 'Сгенерировать упражнения' }}
          </button>
          <button
            @click="generateExercisesWithPoints"
            :disabled="isGeneratingExercises || mainStore.userPoints < 8"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600"
          >
            <span class="mr-1">💎</span> За баллы
          </button>
        </div>

        <div class="flex flex-col gap-2 w-full md:w-auto">
          <button
            @click="generateGame"
            :disabled="isGeneratingGame"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-600"
          >
            {{ isGeneratingGame ? 'Генерация игры...' : 'Сгенерировать игру' }}
          </button>
          <button
            @click="generateGameWithPoints"
            :disabled="isGeneratingGame || mainStore.userPoints < 8"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-600"
          >
            <span class="mr-1">💎</span> За баллы
          </button>
        </div>

        <button
          @click="exportLesson('pdf')"
          :disabled="isExporting"
          class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:bg-gray-600"
        >
          {{ isExporting ? 'Экспорт...' : 'Экспорт в PDF' }}
        </button>
      </div>
    </div>

    <!-- Сообщение об ошибке, если урок не найден -->
    <div v-else class="bg-red-800 rounded-lg p-6 text-white">
      <h2 class="text-xl font-bold mb-3">Урок не найден</h2>
      <p>К сожалению, запрошенный урок не найден или произошла ошибка при его загрузке.</p>
      <button
        @click="$emit('back')"
        class="mt-4 px-4 py-2 bg-red-700 rounded-lg hover:bg-red-600"
      >
        Вернуться назад
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCourseStore } from '../store/course'
import { useMainStore } from '@/store'
import { ContentType } from '@/types/enums'
import GenerationLimitsDisplay from './common/GenerationLimitsDisplay.vue'

// Определение типов
interface Activity {
  name: string;
  type?: string;
  duration: number;
  description: string;
  materials?: string[];
  objectives?: string[];
}

interface Homework {
  description: string;
  tasks: string[];
  estimatedTime?: number;
}

interface Lesson {
  id?: number;
  title: string;
  objectives?: string[];
  grammar?: string[];
  vocabulary?: string[];
  duration?: number;
  activities?: Activity[];
  materials?: string[];
  homework?: Homework;
}

// Получение входных параметров
const props = defineProps<{
  lesson?: Lesson;
  courseName?: string;
}>()

// События
const emit = defineEmits(['back', 'generate-plan', 'generate-plan-with-points', 'generate-exercises', 'generate-exercises-with-points', 'generate-game', 'generate-game-with-points', 'export'])

// Состояние компонента
const isGeneratingPlan = ref(false)
const isGeneratingExercises = ref(false)
const isGeneratingGame = ref(false)
const isExporting = ref(false)

const store = useCourseStore()
const mainStore = useMainStore()

// Методы
const generatePlan = async () => {
  if (!props.lesson) return

  isGeneratingPlan.value = true
  try {
    // Отправляем событие для генерации плана урока
    emit('generate-plan', props.lesson)
  } catch (error) {
    console.error('Ошибка при генерации плана урока:', error)
  } finally {
    isGeneratingPlan.value = false
  }
}

const generateExercises = async () => {
  if (!props.lesson) return

  isGeneratingExercises.value = true
  try {
    // Отправляем событие для генерации упражнений
    emit('generate-exercises', props.lesson)
  } catch (error) {
    console.error('Ошибка при генерации упражнений:', error)
  } finally {
    isGeneratingExercises.value = false
  }
}

// Метод для генерации плана урока за баллы
const generatePlanWithPoints = async () => {
  if (!props.lesson) return

  isGeneratingPlan.value = true
  try {
    // Отправляем событие для генерации плана урока за баллы
    emit('generate-plan-with-points', props.lesson)
  } catch (error) {
    console.error('Ошибка при генерации плана урока за баллы:', error)
  } finally {
    isGeneratingPlan.value = false
  }
}

// Метод для генерации упражнений за баллы
const generateExercisesWithPoints = async () => {
  if (!props.lesson) return

  isGeneratingExercises.value = true
  try {
    // Отправляем событие для генерации упражнений за баллы
    emit('generate-exercises-with-points', props.lesson)
  } catch (error) {
    console.error('Ошибка при генерации упражнений за баллы:', error)
  } finally {
    isGeneratingExercises.value = false
  }
}

// Метод для генерации игры
const generateGame = async () => {
  if (!props.lesson) return

  isGeneratingGame.value = true
  try {
    // Отправляем событие для генерации игры
    emit('generate-game', props.lesson)
  } catch (error) {
    console.error('Ошибка при генерации игры:', error)
  } finally {
    isGeneratingGame.value = false
  }
}

// Метод для генерации игры за баллы
const generateGameWithPoints = async () => {
  if (!props.lesson) return

  isGeneratingGame.value = true
  try {
    // Отправляем событие для генерации игры за баллы
    emit('generate-game-with-points', props.lesson)
  } catch (error) {
    console.error('Ошибка при генерации игры за баллы:', error)
  } finally {
    isGeneratingGame.value = false
  }
}

const exportLesson = async (format: 'pdf' | 'docx') => {
  if (!props.lesson) return

  isExporting.value = true
  try {
    // Отправляем событие для экспорта урока
    emit('export', { lesson: props.lesson, format })
  } catch (error) {
    console.error('Ошибка при экспорте урока:', error)
  } finally {
    isExporting.value = false
  }
}

const formatActivityType = (type: string): string => {
  const types: Record<string, string> = {
    'warm-up': 'Разминка',
    'practice': 'Практика',
    'presentation': 'Презентация',
    'production': 'Продукция',
    'review': 'Повторение',
    'assessment': 'Оценивание'
  }
  return types[type] || type
}
</script>

<style scoped>
/* Дополнительные стили при необходимости */
.points-icon {
  margin-right: 5px;
  font-size: 16px;
}

.points-info {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: #4a5568;
  background-color: #e6f7ff;
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid #91d5ff;
}

.points-cost {
  margin-left: 0.5rem;
  font-size: 0.8rem;
  color: #718096;
}
</style>