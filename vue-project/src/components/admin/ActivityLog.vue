<template>
  <div class="bg-gray-800 rounded-lg">
    <!-- Заголовок и фильтры -->
    <div class="p-6 border-b border-gray-700">
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-medium text-white">Activity History</h3>
        <div class="flex gap-4">
          <!-- Фильтр по типу -->
          <select
            v-model="selectedType"
            class="px-3 py-1.5 bg-gray-700 text-gray-300 rounded-lg border border-gray-600"
          >
            <option value="all">All Actions</option>
            <option v-for="type in activityTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </option>
          </select>

          <!-- Период -->
          <select
            v-model="selectedPeriod"
            class="px-3 py-1.5 bg-gray-700 text-gray-300 rounded-lg border border-gray-600"
          >
            <option value="day">Last 24 hours</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </select>

          <!-- Обновить -->
          <button
            @click="refreshActivities"
            class="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-700"
            :disabled="loading"
          >
            <RefreshCwIcon class="w-5 h-5" :class="{ 'animate-spin': loading }" />
          </button>
        </div>
      </div>
    </div>

    <!-- Список действий -->
    <div class="divide-y divide-gray-700">
      <!-- Группы по дням -->
      <div v-for="group in groupedActivities" :key="group.date" class="divide-y divide-gray-700/50">
        <!-- Заголовок группы -->
        <div class="px-6 py-2 bg-gray-700/30">
          <span class="text-sm font-medium text-gray-400">{{ formatGroupDate(group.date) }}</span>
        </div>

        <!-- Действия в группе -->
        <div v-for="activity in group.activities" :key="activity.id"
             class="px-6 py-4 hover:bg-gray-700/30 transition-colors">
          <div class="flex items-center justify-between">
            <!-- Иконка и основная информация -->
            <div class="flex items-center gap-4">
              <div class="p-2 rounded-lg" :class="getActivityColor(activity.type)">
                <component :is="getActivityIcon(activity.type)" class="w-5 h-5" />
              </div>
              <div>
                <div class="text-gray-200">{{ activity.description }}</div>
                <div class="text-sm text-gray-400 mt-1">{{ formatTime(activity.timestamp) }}</div>
              </div>
            </div>

            <!-- Статус и действия -->
            <div class="flex items-center gap-3">
              <span
                v-if="activity.status"
                class="px-2 py-1 text-xs rounded-full"
                :class="getStatusClass(activity.status)"
              >
                {{ activity.status }}
              </span>
              <button
                v-if="activity.hasDetails"
                @click="showDetails(activity)"
                class="p-1 text-gray-400 hover:text-white rounded"
              >
                <ChevronRightIcon class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- Дополнительные детали (если есть) -->
          <div v-if="activity.metadata" class="mt-2 pl-14">
            <div v-for="(value, key) in activity.metadata" :key="String(key)"
                 class="text-sm text-gray-400">
              {{ formatMetadataKey(key) }}: {{ formatMetadataValue(value) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="loading && activities.length === 0" class="p-12 text-center">
      <div class="inline-block w-8 h-8 border-2 border-t-transparent border-purple-500 rounded-full animate-spin"></div>
      <div class="mt-4 text-gray-400">Loading activities...</div>
    </div>

    <!-- Пустое состояние -->
    <div v-if="!loading && activities.length === 0" class="p-12 text-center">
      <div class="text-gray-400">No activities for selected period</div>
    </div>

    <!-- Подгрузка следующей страницы -->
    <div
      v-if="hasMorePages && !loading"
      class="p-4 text-center border-t border-gray-700"
    >
      <button
        @click="loadMore"
        class="text-purple-400 hover:text-purple-300"
      >
        Load more
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  RefreshCwIcon,
  ChevronRightIcon,
  Users,
  Zap,
  AlertTriangle,
  CreditCard,
  Activity
} from 'lucide-vue-next'
import { formatDistanceToNow, format, isToday, isYesterday } from 'date-fns'
import { ru, enUS } from 'date-fns/locale'

interface ActivityMetadata {
  [key: string]: string | number | boolean
}

interface Activity {
  id: number
  type: string
  description: string
  timestamp: string
  status?: string
  hasDetails?: boolean
  metadata?: ActivityMetadata
  userId?: number
  userName?: string
}

interface Props {
  activities: Activity[]
  loading?: boolean
  hasMorePages?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  hasMorePages: false
})

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'loadMore'): void
  (e: 'filterChange', type: string, period: string): void
  (e: 'showDetails', activity: Activity): void
}>()

const selectedType = ref('all')
const selectedPeriod = ref('day')

const activityTypes = [
  { value: 'user', label: 'Users' },
  { value: 'generation', label: 'Generations' },
  { value: 'tariff', label: 'Plans' },
  { value: 'error', label: 'Errors' }
]

// Группировка действий по дням
const groupedActivities = computed(() => {
  const groups: { [key: string]: Activity[] } = {}

  props.activities.forEach(activity => {
    const date = new Date(activity.timestamp).toDateString()
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(activity)
  })

  return Object.entries(groups).map(([date, activities]) => ({
    date,
    activities: activities.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  })).sort((a, b) =>
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )
})

// Форматирование дат
const formatGroupDate = (dateString: string) => {
  const date = new Date(dateString)
  if (isToday(date)) return 'Today'
  if (isYesterday(date)) return 'Yesterday'
  return format(date, 'd MMMM', { locale: enUS })
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  if (isToday(date)) {
    return format(date, 'HH:mm')
  }
  return formatDistanceToNow(date, { addSuffix: true, locale: enUS })
}

// Стилизация типов действий
const getActivityColor = (type: string) => {
  const colors = {
    user: 'bg-blue-500/20 text-blue-400',
    generation: 'bg-purple-500/20 text-purple-400',
    tariff: 'bg-green-500/20 text-green-400',
    error: 'bg-red-500/20 text-red-400'
  }
  return colors[type as keyof typeof colors] || 'bg-gray-500/20 text-gray-400'
}

const getActivityIcon = (type: string) => {
  const icons = {
    user: Users,
    generation: Zap,
    tariff: CreditCard,
    error: AlertTriangle
  }
  return icons[type as keyof typeof icons] || Activity
}

// Стилизация статусов
const getStatusClass = (status: string) => {
  const classes = {
    success: 'bg-green-500/20 text-green-300',
    pending: 'bg-yellow-500/20 text-yellow-300',
    error: 'bg-red-500/20 text-red-300'
  }
  return classes[status as keyof typeof classes] || 'bg-gray-500/20 text-gray-300'
}

// Форматирование метаданных
const formatMetadataKey = (key: string | number): string => {
  // Convert to string first
  const keyStr = String(key);
  return keyStr
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}

const formatMetadataValue = (value: string | number | boolean): string => {
  if (typeof value === 'boolean') return value ? 'Да' : 'Нет';
  if (typeof value === 'number') return value.toLocaleString();
  return String(value);
}

// Обработчики событий
const refreshActivities = () => {
  emit('refresh')
}

const loadMore = () => {
  emit('loadMore')
}

const showDetails = (activity: Activity) => {
  emit('showDetails', activity)
}

// Следим за изменениями фильтров
watch([selectedType, selectedPeriod], () => {
  emit('filterChange', selectedType.value, selectedPeriod.value)
})
</script>
