<template>
  <div class="free-lessons-view">
    <header class="p-6 text-center">
      <h1 class="text-2xl font-bold text-white mb-2">Free lessons</h1>
      <p class="text-gray-300 text-sm">
        Learn languages with our free materials
      </p>
    </header>

    <div class="categories-scroll mb-6">
      <div class="flex gap-2 px-4 overflow-x-auto hide-scrollbar">
        <button
          v-for="category in categories"
          :key="category.id"
          @click="currentCategory = category.id"
          class="px-4 py-2 rounded-full whitespace-nowrap"
          :class="currentCategory === category.id
            ? 'bg-purple-500 text-white'
            : 'bg-gray-800 text-gray-300'"
        >
          {{ category.name }}
        </button>
      </div>
    </div>

    <div class="lessons-grid px-4 grid gap-4">
      <div
        v-for="lesson in filteredLessons"
        :key="lesson.id"
        class="lesson-card bg-gray-800/50 rounded-xl overflow-hidden"
      >
        <!-- Lesson preview -->
        <div class="aspect-video bg-gradient-to-br from-indigo-500/30 to-purple-500/30 relative">
          <img
            v-if="lesson.image"
            :src="lesson.image"
            :alt="lesson.title"
            class="w-full h-full object-cover absolute inset-0"
          />
          <div class="absolute bottom-4 right-4">
            <span class="px-2 py-1 bg-black/50 rounded text-xs text-white">
              {{ lesson.duration }}
            </span>
          </div>
        </div>

        <!-- Lesson information -->
        <div class="p-4">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-400">
              {{ lesson.level }}
            </span>
            <span class="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-400">
              {{ lesson.language }}
            </span>
          </div>

          <h3 class="text-lg font-bold text-white">{{ lesson.title }}</h3>
          <p class="text-gray-400 text-sm mt-1">{{ lesson.description }}</p>

          <!-- Progress and tags -->
          <div class="mt-4 space-y-3">
            <div v-if="lesson.progress" class="relative h-2 bg-gray-700 rounded">
              <div
                class="absolute h-full bg-green-500 rounded"
                :style="{ width: `${lesson.progress}%` }"
              ></div>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in lesson.tags"
                :key="tag"
                class="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="flex gap-2 mt-4">
            <button
              @click="startLesson(lesson.id)"
              class="flex-1 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium"
            >
              {{ lesson.progress ? 'Continue' : 'Start' }}
            </button>
            <button
              @click="toggleFavorite(lesson.id)"
              class="w-10 h-10 flex items-center justify-center rounded-lg"
              :class="lesson.isFavorite
                ? 'bg-pink-500/20 text-pink-400'
                : 'bg-gray-700 text-gray-400'"
            >
              ❤
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentCategory = ref('all')

const categories = ref([
  { id: 'all', name: 'All lessons' },
  { id: 'grammar', name: 'Grammar' },
  { id: 'vocabulary', name: 'Vocabulary' },
  { id: 'speaking', name: 'Speaking' },
  { id: 'writing', name: 'Writing' }
])

const lessons = ref([
  {
    id: 'lesson1',
    title: 'Present Simple vs Present Continuous',
    description: 'Understanding the difference between two tenses',
    duration: '30 мин',
    level: 'Beginner',
    language: 'English',
    category: 'grammar',
    progress: 60,
    isFavorite: false,
    image: null,
    tags: ['Grammar', 'Tenses', 'Basic']
  },
  {
    id: 'lesson2',
    title: 'Food and Cooking Vocabulary',
    description: 'Learning words about food and cooking',
    duration: '45 мин',
    level: 'Intermediate',
    language: 'English',
    category: 'vocabulary',
    progress: 0,
    isFavorite: true,
    image: null,
    tags: ['Vocabulary', 'Food', 'Daily Life']
  },
  {
    id: 'lesson3',
    title: 'Job Interview Practice',
    description: 'Practicing speaking skills for interviews',
    duration: '60 мин',
    level: 'Advanced',
    language: 'English',
    category: 'speaking',
    progress: 25,
    isFavorite: false,
    image: null,
    tags: ['Speaking', 'Business', 'Interview']
  }
])

const filteredLessons = computed(() => {
  if (currentCategory.value === 'all') return lessons.value
  return lessons.value.filter(lesson => lesson.category === currentCategory.value)
})

const startLesson = (lessonId: string) => {
  router.push(`/free-lessons/${lessonId}`)
}

const toggleFavorite = (lessonId: string) => {
  const lesson = lessons.value.find(l => l.id === lessonId)
  if (lesson) {
    lesson.isFavorite = !lesson.isFavorite
  }
}
</script>

<style scoped>
.free-lessons-view {
  min-height: calc(100vh - 64px);
}

.categories-scroll {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: rgb(17 24 39 / var(--tw-bg-opacity));
  padding: 1rem 0;
}

.lessons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 640px) {
  .lessons-grid {
    grid-template-columns: 1fr;
  }
}

.hide-scrollbar {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
