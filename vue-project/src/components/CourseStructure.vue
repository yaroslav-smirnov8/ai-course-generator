# CourseStructure.vue
<template>
  <div class="space-y-6">
    <!-- Обзор курса -->
    <div class="bg-gray-800 rounded-lg p-6">
      <div class="flex justify-between items-start mb-4">
        <div>
          <h2 class="text-xl font-bold text-white">{{ course.name }}</h2>
          <div class="text-gray-400 text-sm mt-1">
            {{ course.level }} • {{ course.language }} • {{ course.format }}
          </div>
        </div>
        <div class="flex gap-2">
          <button @click="exportCourse('pdf')" class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            Экспорт PDF
          </button>
          <button @click="exportCourse('docx')" class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600">
            Экспорт DOCX
          </button>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <span class="text-gray-400">Всего уроков:</span>
          <!-- Отображаем общее количество, если оно есть, иначе текущее -->
          <span class="text-white ml-2">{{ course.totalLessonsCount ? `${course.lessons.length} / ${course.totalLessonsCount}` : course.lessons.length }}</span>
        </div>
        <div>
          <span class="text-gray-400">Длительность:</span>
          <span class="text-white ml-2">{{ course.totalDuration }} часов</span>
        </div>
        <div>
          <span class="text-gray-400">Аудитория:</span>
          <span class="text-white ml-2">{{ course.targetAudience }}</span>
        </div>
        <div>
          <span class="text-gray-400">Формат:</span>
          <span class="text-white ml-2">{{ course.format }}</span>
        </div>
      </div>
    </div>

    <!-- Структура курса -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-bold text-white mb-4">Структура курса</h3>

      <div class="space-y-4">
        <div v-for="(lesson, index) in course.lessons" :key="lesson.id" class="border border-gray-700 rounded-lg overflow-hidden">
          <!-- Заголовок урока -->
          <div
            class="flex items-center justify-between p-4 bg-gray-700 cursor-pointer hover:bg-gray-600"
            @click="toggleLesson(lesson.id)"
          >
            <div>
              <h4 class="font-medium text-white">
                Урок {{ index + 1 }}: {{ lesson.title }}
              </h4>
              <p class="text-sm text-gray-400">{{ lesson.duration }} минут</p>
            </div>
            <button class="p-1 hover:bg-gray-500 rounded">
              {{ expandedLesson === lesson.id ? '−' : '+' }}
            </button>
          </div>

          <!-- Детали урока -->
          <div v-if="expandedLesson === lesson.id" class="p-4 border-t border-gray-700">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Левая колонка -->
              <div class="space-y-4">
                <div>
                  <h5 class="font-medium text-white mb-2">Цели</h5>
                  <ul class="list-disc list-inside text-sm text-gray-400 space-y-1">
                    <li v-for="(objective, idx) in lesson.objectives" :key="idx">
                      {{ objective }}
                    </li>
                  </ul>
                </div>

                <div>
                  <h5 class="font-medium text-white mb-2">Грамматика</h5>
                  <ul class="list-disc list-inside text-sm text-gray-400 space-y-1">
                    <li v-for="(item, idx) in lesson.grammar" :key="idx">
                      {{ item }}
                    </li>
                  </ul>
                </div>

                <div>
                  <h5 class="font-medium text-white mb-2">Лексика</h5>
                  <ul class="list-disc list-inside text-sm text-gray-400 space-y-1">
                    <li v-for="(item, idx) in lesson.vocabulary" :key="idx">
                      {{ item }}
                    </li>
                  </ul>
                </div>
              </div>

              <!-- Правая колонка -->
              <div class="space-y-4">
                <div>
                  <h5 class="font-medium text-white mb-2">Активности</h5>
                  <div class="space-y-2">
                    <div
                      v-for="(activity, idx) in lesson.activities"
                      :key="idx"
                      class="bg-gray-700 p-3 rounded"
                    >
                      <div class="font-medium text-white">{{ activity.name }}</div>
                      <div class="text-sm text-gray-400">{{ activity.duration }} мин</div>
                      <div class="text-sm text-gray-300">{{ activity.description }}</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h5 class="font-medium text-white mb-2">Материалы</h5>
                  <ul class="list-disc list-inside text-sm text-gray-400 space-y-1">
                    <li v-for="(material, idx) in lesson.materials" :key="idx">
                      {{ material }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- Домашнее задание -->
            <div v-if="lesson.homework" class="mt-4">
              <h5 class="text-lg font-semibold text-indigo-300">Домашнее задание:</h5>
              {{ lesson.homework.description }}
              <ul v-if="lesson.homework.tasks" class="list-disc list-inside mt-2 space-y-1">
                <li v-for="(task, idx) in lesson.homework.tasks" :key="idx">
                  {{ task }}
                </li>
              </ul>
            </div>

            <!-- Кнопки действий -->
            <div class="mt-4 pt-4 border-t border-gray-700 flex gap-4">
              <button
                @click="downloadMaterials(lesson)"
                class="flex-1 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                Скачать материалы
              </button>
              <button
                @click="previewLesson(lesson)"
                class="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Предпросмотр
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопка Загрузить еще -->
      <div v-if="canLoadMore" class="mt-6 text-center">
        <button
          @click="loadMoreLessons"
          :disabled="isLoadingMore"
          class="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isLoadingMore ? 'Загрузка...' : 'Загрузить еще уроки' }}
        </button>
      </div>
    </div>

    <!-- Прогресс по курсу -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-bold text-white mb-4">Прогресс курса</h3>

      <div class="space-y-4">
        <div class="w-full bg-gray-700 rounded-full h-4">
          <div
            class="bg-purple-600 h-4 rounded-full transition-all duration-300"
            :style="{ width: `${course.progress || 0}%` }"
          />
        </div>

        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-400">Пройдено уроков:</span>
            <span class="text-white ml-2">{{ course.completedLessons }}/{{ course.lessons.length }}</span>
          </div>
          <div>
            <span class="text-gray-400">Общий прогресс:</span>
            <span class="text-white ml-2">{{ course.progress }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue' // Добавляем computed
import { useMainStore } from '@/store'
// Уточняем путь импорта типов, если они лежат глубже
import type { CourseStructure, Lesson } from '@/types/course'

const props = defineProps<{
  // Добавляем опциональное поле для общего числа уроков, если оно будет передаваться
  course: CourseStructure & { totalLessonsCount?: number }
}>()

const store = useMainStore()
const isLoadingMore = ref(false) // Состояние загрузки
const expandedLesson = ref<number | null>(null)

const toggleLesson = (lessonId: number) => {
  expandedLesson.value = expandedLesson.value === lessonId ? null : lessonId
}

const downloadMaterials = async (lesson: Lesson) => {
  try {
    // TODO: Реализовать действие 'generateLessonMaterials' в Pinia store (useMainStore)
    // Оно должно принимать lesson.id и инициировать скачивание материалов
    // await store.generateLessonMaterials(lesson.id)
    console.warn("Функциональность 'Скачать материалы' требует реализации в Pinia store.");
  } catch (error) {
    console.error('Error downloading materials:', error)
    // TODO: Показать ошибку пользователю
  }
}

const previewLesson = (lesson: Lesson) => {
  // Реализация предпросмотра урока
  console.log("Preview lesson:", lesson.title) // Заглушка
}

const exportCourse = async (format: 'pdf' | 'docx') => {
  try {
    // TODO: Реализовать действие 'exportCourse' в Pinia store (useMainStore)
    // Оно должно принимать course.id и format ('pdf' или 'docx')
    // await store.exportCourse(props.course.id, format)
    console.warn("Функциональность 'Экспорт курса' требует реализации в Pinia store.");
  } catch (error) {
    console.error('Error exporting course:', error)
    // TODO: Показать ошибку пользователю
  }
}

// Вычисляемое свойство для отображения кнопки "Загрузить еще"
const canLoadMore = computed(() => {
  // Показываем кнопку, если есть поле totalLessonsCount и оно больше текущего числа уроков
  return props.course.totalLessonsCount && props.course.lessons.length < props.course.totalLessonsCount;
});

// Метод для загрузки следующей порции уроков
const loadMoreLessons = async () => {
  if (isLoadingMore.value || !canLoadMore.value) return;

  isLoadingMore.value = true;
  try {
    const currentLessonCount = props.course.lessons.length;
    console.log(`Запрос на загрузку следующих уроков после ${currentLessonCount}`);

    // TODO: Реализовать действие в Pinia store (например, loadNextLessonsBatch)
    // Это действие должно вызвать API бэкенда, передав course.id и currentLessonCount
    // и затем обновить массив props.course.lessons новыми данными
    // await store.loadNextLessonsBatch(props.course.id, currentLessonCount);

    // Заглушка для имитации загрузки
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.warn("Функциональность 'Загрузить еще уроки' требует реализации в Pinia store и бэкенде.");


  } catch (error) {
    console.error('Ошибка при загрузке следующих уроков:', error);
    // TODO: Показать ошибку пользователю
  } finally {
    isLoadingMore.value = false;
  }
};

</script>
