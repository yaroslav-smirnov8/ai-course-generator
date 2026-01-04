<template>
  <div class="space-y-6">
    <PageHeader
      title="Generation History"
      description="Manage generated content"
    >
      <template #actions>
        <button
          @click="exportData"
          class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
        >
          <DownloadIcon class="w-5 h-5" />
        </button>
      </template>
    </PageHeader>

    <!-- Фильтры -->
    <AdminFilters
      @filter="handleFilter"
      @export="exportData"
      :showAdditionalFilters="true"
      :additionalFilters="typeFilters"
    />

    <!-- Статистика -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        title="Total generations"
        :value="stats.total_generations"
        icon="Zap"
      />
      <StatCard
        title="Lesson Plans"
        :value="stats.by_type.lesson_plans"
        icon="FileText"
      />
      <StatCard
        title="Images"
        :value="stats.by_type.images"
        icon="Image"
      />
    </div>

    <!-- Распределение по типам -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <PageContent>
        <h3 class="text-lg font-medium text-white mb-4">Distribution by type</h3>
        <div class="h-[400px]">
          <GenerationsPieChart :data="typeDistribution" />
        </div>
      </PageContent>

      <PageContent>
        <h3 class="text-lg font-medium text-white mb-4">Popular requests</h3>
        <div class="space-y-2">
          <div
            v-for="prompt in stats.popular_prompts"
            :key="prompt.prompt"
            class="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg"
          >
            <span class="text-gray-300 truncate max-w-[70%]">{{ prompt.prompt }}</span>
            <span class="text-purple-400">{{ prompt.count }}</span>
          </div>
        </div>
      </PageContent>
    </div>

    <!-- Таблица генераций -->
    <PageContent>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-900">
          <tr>
            <th class="p-4 text-left text-gray-400">ID</th>
            <th class="p-4 text-left text-gray-400">Type</th>
            <th class="p-4 text-left text-gray-400">User</th>
            <th class="p-4 text-left text-gray-400">Prompt</th>
            <th class="p-4 text-left text-gray-400">Date</th>
            <th class="p-4 text-left text-gray-400">Actions</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="generation in filteredGenerations"
              :key="generation.id"
              class="border-t border-gray-700 hover:bg-gray-700/50"
          >
            <td class="p-4">{{ generation.id }}</td>
            <td class="p-4">
                <span
                  class="px-2 py-1 rounded-full text-xs"
                  :class="getTypeClass(generation.type)"
                >
                  {{ formatType(generation.type) }}
                </span>
            </td>
            <td class="p-4">
              <button
                @click="viewUser(generation.user_id)"
                class="text-blue-400 hover:text-blue-300 flex items-center gap-2"
              >
                <span>tg://{{ generation.user?.telegram_id }}</span>
                <span v-if="generation.user?.username" class="text-gray-400">
                  @{{ generation.user.username }}
                </span>
              </button>
            </td>
            <td class="p-4 max-w-md truncate">{{ generation.prompt }}</td>
            <td class="p-4 text-gray-400">{{ formatDate(generation.created_at) }}</td>
            <td class="p-4">
              <div class="flex gap-2">
                <button
                  @click="viewGeneration(generation)"
                  class="text-blue-400 hover:text-blue-300"
                >
                  <EyeIcon class="w-5 h-5" />
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- Пагинация -->
      <div class="mt-4">
        <AdminPagination
          v-model:page="currentPage"
          :total="totalItems"
          :per-page="perPage"
        />
      </div>
    </PageContent>

    <!-- Модальное окно просмотра генерации -->
    <Dialog v-model:open="showGenerationModal">
      <DialogContent class="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Generation Details</DialogTitle>
        </DialogHeader>

        <div class="space-y-4" v-if="selectedGeneration">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm text-gray-400">ID</label>
              <p class="text-white">{{ selectedGeneration.id }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-400">Type</label>
              <p class="text-white">{{ formatType(selectedGeneration.type) }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-400">Creation Date</label>
              <p class="text-white">{{ formatDate(selectedGeneration.created_at) }}</p>
            </div>
          </div>

          <div>
            <label class="text-sm text-gray-400">Prompt</label>
            <pre class="mt-1 p-2 bg-gray-700 rounded-lg text-white text-sm whitespace-pre-wrap">{{ selectedGeneration.prompt }}</pre>
          </div>

          <div>
            <label class="text-sm text-gray-400">Content</label>
            <pre class="mt-1 p-2 bg-gray-700 rounded-lg text-white text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">{{ selectedGeneration.content }}</pre>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" @click="showGenerationModal = false">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import {
  Download as DownloadIcon,
  Eye as EyeIcon,
  Zap,
  FileText,
  Image
} from 'lucide-vue-next'
import { ContentType } from '@/core/constants'
import _ from 'lodash'

// Components
import PageHeader from '../admin/PageHeader.vue'
import PageContent from '../admin/PageContent.vue'
import StatCard from '../admin/cards/StatCard.vue'
import AdminFilters from '../admin/AdminFilters.vue'
import AdminPagination from '../admin/common/AdminPagination.vue'
import GenerationsPieChart from '../admin/charts/GenerationsPieChart.vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

const store = useMainStore()

// Interfaces
interface User {
  id: number
  telegram_id: string
  username?: string
}

interface Generation {
  id: number
  user_id: number
  type: ContentType
  content: string
  prompt: string
  created_at: Date
  user?: User
}

interface GenerationStats {
  total_generations: number
  by_type: {
    lesson_plans: number
    exercises: number
    games: number
    images: number
  }
  popular_prompts: Array<{
    prompt: string
    count: number
  }>
}

interface Filters {
  search: string
  dateFrom: string
  dateTo: string
  type: ContentType | 'all'
}

// State
const currentPage = ref(1)
const perPage = ref(10)
const totalItems = ref(0)
const generations = ref<Generation[]>([])
const selectedGeneration = ref<Generation | null>(null)
const showGenerationModal = ref(false)

const stats = ref<GenerationStats>({
  total_generations: 0,
  by_type: {
    lesson_plans: 0,
    exercises: 0,
    games: 0,
    images: 0
  },
  popular_prompts: []
})

// Filters
const filters = ref<Filters>({
  search: '',
  dateFrom: '',
  dateTo: '',
  type: 'all'
})

const typeFilters = [
  { value: ContentType.LESSON_PLAN, label: 'Lesson Plans' },
  { value: ContentType.EXERCISE, label: 'Exercises' },
  { value: ContentType.GAME, label: 'Games' },
  { value: ContentType.IMAGE, label: 'Images' }
]

// Computed properties
const filteredGenerations = computed(() => {
  let result = generations.value

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    result = result.filter(gen =>
      gen.prompt.toLowerCase().includes(search) ||
      gen.id.toString().includes(search)
    )
  }

  if (filters.value.type !== 'all') {
    result = result.filter(gen => gen.type === filters.value.type)
  }

  if (filters.value.dateFrom) {
    result = result.filter(gen =>
      new Date(gen.created_at) >= new Date(filters.value.dateFrom)
    )
  }

  if (filters.value.dateTo) {
    result = result.filter(gen =>
      new Date(gen.created_at) <= new Date(filters.value.dateTo)
    )
  }

  return result
})

const typeDistribution = computed(() => {
  const { by_type } = stats.value
  return [
    { name: 'Lesson Plans', value: by_type.lesson_plans },
    { name: 'Exercises', value: by_type.exercises },
    { name: 'Games', value: by_type.games },
    { name: 'Images', value: by_type.images }
  ]
})

// Methods
const loadGenerationStats = async () => {
  try {
    const response = await store.getGenerationStatistics({
      page: currentPage.value,
      perPage: perPage.value,
      filters: filters.value
    })

    if (response) {
      generations.value = response.generations || []
      totalItems.value = response.total || 0
      stats.value = {
        total_generations: response.total_generations || 0,
        by_type: response.by_type || {
          lesson_plans: 0,
          exercises: 0,
          games: 0,
          images: 0
        },
        popular_prompts: response.popular_prompts || []
      }
    }
  } catch (error) {
    console.error('Error loading generation statistics:', error)
  }
}

const handleFilter = (newFilters: Partial<Filters>) => {
  filters.value = { ...filters.value, ...newFilters }
}

const viewGeneration = (generation: Generation) => {
  selectedGeneration.value = generation
  showGenerationModal.value = true
}

const viewUser = async (userId: number) => {
  try {
    await store.openUserModal(userId)
  } catch (error) {
    console.error('Error opening user modal:', error)
  }
}

const exportData = async () => {
  try {
    await store.exportData('generations', 'csv')
  } catch (error) {
    console.error('Error exporting data:', error)
  }
}

// Utility functions
const formatType = (type: string): string => {
  const types = {
    [ContentType.LESSON_PLAN]: 'Lesson Plan',
    [ContentType.EXERCISE]: 'Exercise',
    [ContentType.GAME]: 'Game',
    [ContentType.IMAGE]: 'Image'
  }
  return types[type as keyof typeof types] || type
}

const getTypeClass = (type: string): string => {
  const classes = {
    [ContentType.LESSON_PLAN]: 'bg-blue-500/20 text-blue-300',
    [ContentType.EXERCISE]: 'bg-green-500/20 text-green-300',
    [ContentType.GAME]: 'bg-yellow-500/20 text-yellow-300',
    [ContentType.IMAGE]: 'bg-purple-500/20 text-purple-300'
  }
  return classes[type as keyof typeof classes] || 'bg-gray-500/20 text-gray-300'
}

const formatDate = (date: string | Date): string => {
  const d = new Date(date)
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Initialization
onMounted(async () => {
  await loadGenerationStats()
})

// Watch changes
watch([currentPage, perPage], loadGenerationStats)
watch(filters, () => {
  currentPage.value = 1 // Сброс страницы при изменении фильтров
  loadGenerationStats()
})
</script>

<style scoped>
pre::-webkit-scrollbar {
  width: 8px;
}

pre::-webkit-scrollbar-track {
  background: #374151;
}

pre::-webkit-scrollbar-thumb {
  background: #4B5563;
  border-radius: 4px;
}

pre::-webkit-scrollbar-thumb:hover {
  background: #6B7280;
}
</style>
