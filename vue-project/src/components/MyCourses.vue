<template>
  <div class="my-courses-container w-full max-w-4xl mx-auto p-4 space-y-6">
    <!-- Заголовок и кнопка возврата -->
    <div class="flex justify-between items-center mb-4">
      <h2 class="my-courses-title">Мои курсы</h2>
      <button
        @click="$emit('back')"
        class="my-courses-button-back"
      >
        Назад
      </button>
    </div>

    <!-- Индикатор загрузки -->
    <div v-if="isLoading" class="my-courses-loading flex justify-center items-center py-8">
      <div class="my-courses-loader"></div>
      <span class="ml-3 text-white">Загрузка курсов...</span>
    </div>

    <!-- Сообщение об ошибке -->
    <div v-else-if="error" class="my-courses-error bg-red-800/50 p-4 rounded-lg text-white">
      <p>{{ error }}</p>
      <button @click="fetchCourses" class="mt-2 px-4 py-2 bg-red-700/50 rounded-lg hover:bg-red-600/50">
        Попробовать снова
      </button>
    </div>

    <!-- Сообщение, если нет курсов -->
    <div v-else-if="courses.length === 0" class="my-courses-empty bg-purple-800/30 p-6 rounded-lg text-center">
      <p class="text-white mb-4">У вас пока нет сохраненных курсов</p>
      <div class="flex justify-center space-x-4">
        <button @click="$emit('back')" class="px-4 py-2 bg-purple-600/50 rounded-lg hover:bg-purple-500/50 text-white">
          Создать новый курс
        </button>
        <button @click="fetchCourses" class="px-4 py-2 bg-blue-600/50 rounded-lg hover:bg-blue-500/50 text-white">
          Обновить список
        </button>
      </div>
      <p v-if="lastFetchTime" class="text-gray-400 text-sm mt-4">
        Последнее обновление: {{ formatLastFetchTime(lastFetchTime) }}
      </p>
    </div>

    <!-- Список курсов -->
    <div v-else class="my-courses-list space-y-4">
      <div
        v-for="course in courses"
        :key="course.id"
        class="my-courses-item bg-purple-900/30 rounded-lg overflow-hidden hover:bg-purple-800/30 transition-colors cursor-pointer"
        @click="viewCourse(course)"
      >
        <div class="p-4">
          <div class="flex justify-between items-start">
            <h3 class="my-courses-item-title text-xl font-bold text-white mb-2">{{ course.name }}</h3>
            <div class="my-courses-item-badge px-2 py-1 rounded text-xs" :class="getLevelClass(course.level)">
              {{ formatLevel(course.level) }}
            </div>
          </div>

          <div class="my-courses-item-details grid grid-cols-2 md:grid-cols-4 gap-2 text-sm mt-2">
            <div>
              <span class="text-gray-400">Язык:</span>
              <span class="text-white ml-1">{{ formatLanguage(course.language) }}</span>
            </div>
            <div>
              <span class="text-gray-400">Уроков:</span>
              <span class="text-white ml-1">{{ course.lessons.length }}</span>
            </div>
            <div>
              <span class="text-gray-400">Аудитория:</span>
              <span class="text-white ml-1">{{ formatAudience(course.targetAudience) }}</span>
            </div>
            <div>
              <span class="text-gray-400">Длительность:</span>
              <span class="text-white ml-1">{{ formatDuration(course.totalDuration) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно для просмотра курса -->
    <div v-if="showCourseView && selectedCourse" class="my-courses-modal">
      <CourseView
        :course="selectedCourse"
        @close="closeCourseView"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCourseStore } from '../store/course'
import type { CourseStructure } from '@/types/course'
import CourseView from './CourseView.vue'

const emit = defineEmits(['back'])
const store = useCourseStore()

const courses = ref<CourseStructure[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const selectedCourse = ref<CourseStructure | null>(null)
const showCourseView = ref(false)
const lastFetchTime = ref<Date | null>(null)

// Загрузка курсов при монтировании компонента
onMounted(() => {
  fetchCourses()
})

// Получение списка курсов
const fetchCourses = async () => {
  isLoading.value = true
  error.value = null

  try {
    console.log('Запрос на получение списка курсов');
    // Получаем курсы из хранилища
    const result = await store.fetchUserCourses()

    // Проверяем, что результат - массив
    if (Array.isArray(result)) {
      courses.value = result
      console.log(`Получено ${result.length} курсов`);
    } else {
      console.warn('Неожиданный формат данных курсов:', result)
      courses.value = []
    }

    // Если массив пустой, но ошибки нет, это нормально - просто нет курсов
    if (courses.value.length === 0) {
      console.log('Список курсов пуст')
    }

    // Обновляем время последнего запроса
    lastFetchTime.value = new Date()
  } catch (err: any) {
    console.error('Ошибка при загрузке курсов:', err)
    // Показываем ошибку пользователю
    error.value = err.message || 'Не удалось загрузить курсы'
    courses.value = []
  } finally {
    isLoading.value = false
  }
}

// Форматирование времени последнего запроса
const formatLastFetchTime = (date: Date) => {
  if (!date) return '';

  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Если прошло меньше минуты
  if (diff < 60 * 1000) {
    return 'только что';
  }

  // Если прошло меньше часа
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000));
    return `${minutes} ${minutes === 1 ? 'минуту' : minutes < 5 ? 'минуты' : 'минут'} назад`;
  }

  // Если прошло меньше суток
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    return `${hours} ${hours === 1 ? 'час' : hours < 5 ? 'часа' : 'часов'} назад`;
  }

  // Иначе форматируем дату
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Просмотр выбранного курса
const viewCourse = (course: CourseStructure) => {
  selectedCourse.value = course
  showCourseView.value = true
}

// Закрытие просмотра курса
const closeCourseView = () => {
  showCourseView.value = false
  selectedCourse.value = null
}

// Форматирование языка
const formatLanguage = (language: string) => {
  const languages: Record<string, string> = {
    'english': 'Английский',
    'spanish': 'Испанский',
    'french': 'Французский',
    'german': 'Немецкий'
  }
  return languages[language] || language.charAt(0).toUpperCase() + language.slice(1)
}

// Форматирование уровня
const formatLevel = (level: string) => {
  const levels: Record<string, string> = {
    'beginner': 'Начальный',
    'elementary': 'Элементарный',
    'intermediate': 'Средний',
    'upper-intermediate': 'Выше среднего',
    'advanced': 'Продвинутый'
  }
  return levels[level] || level.split('-').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join('-')
}

// Получение класса для бейджа уровня
const getLevelClass = (level: string) => {
  const classes: Record<string, string> = {
    'beginner': 'bg-green-600/30 text-green-300',
    'elementary': 'bg-blue-600/30 text-blue-300',
    'intermediate': 'bg-yellow-600/30 text-yellow-300',
    'upper-intermediate': 'bg-orange-600/30 text-orange-300',
    'advanced': 'bg-red-600/30 text-red-300'
  }
  return classes[level] || 'bg-purple-600/30 text-purple-300'
}

// Форматирование аудитории
const formatAudience = (audience: string) => {
  const audiences: Record<string, string> = {
    'children': 'Дети',
    'teens': 'Подростки',
    'adults': 'Взрослые',
    'business': 'Бизнес'
  }
  if (!audience) return '';
  return audiences[audience] || audience.charAt(0).toUpperCase() + audience.slice(1)
}

// Форматирование длительности
const formatDuration = (minutes: number | undefined) => {
  if (minutes === undefined || minutes === null) {
    return 'Не указано'
  }

  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60

  if (hours > 0) {
    return `${hours} ч ${mins} мин`
  }
  return `${mins} мин`
}
</script>

<style scoped>
.my-courses-container {
  background-color: rgba(42, 8, 46, 0.25);
  border-radius: 1rem;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 103, 231, 0.2);
}

.my-courses-title {
  color: white;
  font-size: 1.8rem;
  font-weight: 700;
  text-shadow: 0 0 15px rgba(255, 103, 231, 0.8);
  opacity: 0.9;
}

.my-courses-button-back {
  padding: 0.5rem 1rem;
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.75rem;
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.my-courses-button-back:hover {
  background-color: rgba(255, 255, 255, 0.25);
}

.my-courses-loader {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: my-courses-spin 1s ease-in-out infinite;
}

@keyframes my-courses-spin {
  to {
    transform: rotate(360deg);
  }
}

.my-courses-item {
  transition: transform 0.2s;
}

.my-courses-item:hover {
  transform: translateY(-2px);
}

.my-courses-item-title {
  text-shadow: 0 0 10px rgba(255, 103, 231, 0.6);
}
</style>
