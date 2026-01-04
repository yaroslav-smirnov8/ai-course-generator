<template>
  <div class="space-y-6">
    <!-- Фильтры -->
    <div class="bg-gray-800 rounded-lg p-6">
      <div class="flex flex-wrap gap-4 items-center">
        <div>
          <label class="block text-sm text-gray-400 mb-1">Period</label>
          <select
            v-model="period"
            class="bg-gray-700 text-white rounded-lg px-4 py-2 w-40"
            @change="loadData"
          >
            <option value="week">Week</option>
            <option value="month">Month</option>
            <option value="quarter">Quarter</option>
            <option value="year">Year</option>
          </select>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Tariff</label>
          <select
            v-model="tariffFilter"
            class="bg-gray-700 text-white rounded-lg px-4 py-2 w-40"
            @change="loadData"
          >
            <option value="all">All Tariffs</option>
            <option value="basic">Basic</option>
            <option value="standard">Standard</option>
            <option value="premium">Premium</option>
            <option value="vip">VIP</option>
          </select>
        </div>

        <button
          @click="exportContentData"
          class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          :disabled="isLoading"
        >
          <Download class="w-4 h-4" />
          Экспорт
        </button>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="isLoading" class="flex justify-center py-8">
      <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg">
      {{ error }}
    </div>

    <!-- Основные метрики -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Total Generations</h3>
        <p class="text-3xl font-bold text-purple-500">{{ contentData.totalGenerations }}</p>
        <p class="text-sm text-gray-400 mt-1">
          <span :class="contentData.generationsGrowth >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ contentData.generationsGrowth >= 0 ? '+' : '' }}{{ contentData.generationsGrowth.toFixed(1) }}%
          </span>
          compared to previous period
        </p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Most Popular</h3>
        <p class="text-3xl font-bold text-blue-500">{{ contentData.mostPopular.name }}</p>
        <p class="text-sm text-gray-400 mt-1">{{ contentData.mostPopular.count }} generations</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Success Rate</h3>
        <p class="text-3xl font-bold text-green-500">{{ contentData.successRate.toFixed(1) }}%</p>
        <p class="text-sm text-gray-400 mt-1">Successful generations</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Average Time</h3>
        <p class="text-3xl font-bold text-yellow-500">{{ contentData.avgGenerationTime }}s</p>
        <p class="text-sm text-gray-400 mt-1">Generation time</p>
      </div>
    </div>

    <!-- Графики -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Распределение по типам контента -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Distribution by Types</h3>
        <div class="h-64">
          <canvas ref="contentTypeChart"></canvas>
        </div>
      </div>

      <!-- Динамика генераций -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Generation Trends</h3>
        <div class="h-64">
          <canvas ref="generationTrendChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Топ контента -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Top Content Types</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="content in contentData.topContent"
          :key="content.type"
          class="bg-gray-700 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-white font-medium">{{ formatContentType(content.type) }}</h4>
            <span class="text-2xl">{{ getContentIcon(content.type) }}</span>
          </div>
          <p class="text-2xl font-bold text-purple-400 mb-1">{{ content.count }}</p>
          <p class="text-sm text-gray-400 mb-2">{{ content.percentage.toFixed(1) }}% от общего</p>
          <div class="w-full bg-gray-600 rounded-full h-2">
            <div
              class="bg-purple-500 h-2 rounded-full"
              :style="{ width: `${content.percentage}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Детальная таблица -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Детальная статистика</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-gray-900">
            <tr>
              <th class="p-4">Тип контента</th>
              <th class="p-4">Генераций</th>
              <th class="p-4">Уникальных пользователей</th>
              <th class="p-4">Успешность</th>
              <th class="p-4">Среднее время</th>
              <th class="p-4">Рост</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in contentData.detailedStats"
              :key="item.type"
              class="border-t border-gray-700 hover:bg-gray-700/50"
            >
              <td class="p-4">
                <div class="flex items-center gap-2">
                  <span class="text-xl">{{ getContentIcon(item.type) }}</span>
                  <span class="text-white">{{ formatContentType(item.type) }}</span>
                </div>
              </td>
              <td class="p-4 text-purple-400">{{ item.count }}</td>
              <td class="p-4 text-blue-400">{{ item.uniqueUsers }}</td>
              <td class="p-4">
                <span
                  class="px-2 py-1 rounded-full text-xs"
                  :class="item.successRate >= 95 ? 'bg-green-500/20 text-green-300' :
                         item.successRate >= 90 ? 'bg-yellow-500/20 text-yellow-300' :
                         'bg-red-500/20 text-red-300'"
                >
                  {{ item.successRate.toFixed(1) }}%
                </span>
              </td>
              <td class="p-4 text-gray-300">{{ item.avgTime }}с</td>
              <td class="p-4">
                <span
                  :class="item.growth >= 0 ? 'text-green-400' : 'text-red-400'"
                >
                  {{ item.growth >= 0 ? '+' : '' }}{{ item.growth.toFixed(1) }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>



    <!-- Сезонность -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Сезонные тренды</h3>
      <div class="h-64">
        <canvas ref="seasonalChart"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Download } from 'lucide-vue-next'
import Chart from 'chart.js/auto'

// Состояние
const isLoading = ref(true)
const error = ref<string | null>(null)
const period = ref('month')
const tariffFilter = ref('all')

// Ссылки на canvas элементы
const contentTypeChart = ref<HTMLCanvasElement | null>(null)
const generationTrendChart = ref<HTMLCanvasElement | null>(null)
const seasonalChart = ref<HTMLCanvasElement | null>(null)

// Данные
const contentData = ref({
  totalGenerations: 0,
  generationsGrowth: 0,
  mostPopular: { name: '', count: 0 },
  successRate: 0,
  avgGenerationTime: 0,
  topContent: [],
  detailedStats: [],
  qualityStats: { high: 0, medium: 0, low: 0 },
  trendData: [],
  seasonalData: []
})

// Графики
let contentTypeChartInstance: Chart | null = null
let generationTrendChartInstance: Chart | null = null
let seasonalChartInstance: Chart | null = null

// Методы
const formatContentType = (type: string): string => {
  const typeMap: Record<string, string> = {
    'lesson_plan': 'Lesson Plan',
    'exercise': 'Exercise',
    'game': 'Game',
    'image': 'Image',
    'text_analysis': 'Text Analysis',
    'concept_explanation': 'Concept Explanation',
    'course': 'Course',
    'free_query': 'AI Assistant'
  }
  return typeMap[type] || type
}

const getContentIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    'lesson_plan': '📚',
    'exercise': '✏️',
    'game': '🎮',
    'image': '🖼️',
    'text_analysis': '📝',
    'concept_explanation': '💡',
    'course': '🎓',
    'free_query': '🤖'
  }
  return iconMap[type] || '📄'
}

const loadData = async () => {
  isLoading.value = true
  error.value = null

  try {
    // Получаем данные авторизации из Telegram WebApp
    const webApp = (window as any).Telegram?.WebApp
    const webAppData = webApp?.initData || localStorage.getItem('tg_web_app_data')

    if (!webAppData) {
      throw new Error('Нет данных авторизации')
    }

    const response = await fetch(`/api/v1/admin/analytics/content-popularity?period=${period.value}&tariff_filter=${tariffFilter.value}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `tma ${webAppData}`
      }
    })

    if (!response.ok) {
      throw new Error('Ошибка загрузки данных')
    }

    const data = await response.json()

    // Преобразуем данные в нужный формат
    const totalGenerations = data.popularContent?.reduce((sum: number, item: any) => sum + item.count, 0) || 0
    const mostPopular = data.popularContent?.[0] || { name: '', count: 0 }

    contentData.value = {
      totalGenerations,
      generationsGrowth: 0, // Заглушка
      mostPopular: {
        name: formatContentType(mostPopular.type || ''),
        count: mostPopular.count || 0
      },
      successRate: 95, // Заглушка
      avgGenerationTime: 2.3, // Заглушка
      topContent: data.popularContent?.map((item: any) => ({
        type: item.type,
        name: item.name,
        count: item.count,
        uniqueUsers: item.uniqueUsers,
        avgPerUser: item.avgPerUser
      })) || [],
      detailedStats: data.popularContent || [],
      qualityStats: { high: 75, medium: 20, low: 5 }, // Заглушка
      trendData: [], // Пока пустой
      seasonalData: [] // Пока пустой
    }

    // Обновляем графики с задержкой для корректной инициализации DOM
    setTimeout(() => {
      updateCharts()
    }, 100)
  } catch (err: any) {
    error.value = err.message || 'Ошибка загрузки данных'
  } finally {
    isLoading.value = false
  }
}

const updateCharts = () => {
  updateContentTypeChart()
  updateGenerationTrendChart()
  updateSeasonalChart()
}

const updateContentTypeChart = () => {
  if (!contentTypeChart.value) {
    console.warn('Content type chart canvas not found')
    return
  }

  if (contentTypeChartInstance) {
    contentTypeChartInstance.destroy()
  }

  const ctx = contentTypeChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for content type chart')
    return
  }

  console.log('Creating content type chart with data:', contentData.value.topContent)

  contentTypeChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: contentData.value.topContent?.map(item => formatContentType(item.type)) || [],
      datasets: [{
        data: contentData.value.topContent?.map(item => item.count) || [],
        backgroundColor: ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6366F1'],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#E5E7EB' }
        }
      }
    }
  })
}

const updateGenerationTrendChart = () => {
  if (!generationTrendChart.value) {
    console.warn('Generation trend chart canvas not found')
    return
  }

  if (generationTrendChartInstance) {
    generationTrendChartInstance.destroy()
  }

  const ctx = generationTrendChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for generation trend chart')
    return
  }

  console.log('Creating generation trend chart with data:', contentData.value.trendData)

  generationTrendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: contentData.value.trendData?.map(item => item.date) || [],
      datasets: [
        {
          label: 'Lesson Plan',
          data: contentData.value.trendData?.map(item => item.lesson_plan) || [],
          borderColor: '#8B5CF6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          tension: 0.4
        },
        {
          label: 'Exercise',
          data: contentData.value.trendData?.map(item => item.exercise) || [],
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4
        },
        {
          label: 'Game',
          data: contentData.value.trendData?.map(item => item.game) || [],
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#E5E7EB' }
        }
      },
      scales: {
        x: {
          ticks: { color: '#9CA3AF' },
          grid: { color: 'rgba(75, 85, 99, 0.2)' }
        },
        y: {
          ticks: { color: '#9CA3AF' },
          grid: { color: 'rgba(75, 85, 99, 0.2)' }
        }
      }
    }
  })
}

const updateSeasonalChart = () => {
  if (!seasonalChart.value) {
    console.warn('Seasonal chart canvas not found')
    return
  }

  if (seasonalChartInstance) {
    seasonalChartInstance.destroy()
  }

  const ctx = seasonalChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for seasonal chart')
    return
  }

  console.log('Creating seasonal chart with data:', contentData.value.seasonalData)

  const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']

  seasonalChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: months,
      datasets: [{
        label: 'Активность',
        data: contentData.value.seasonalData?.map(item => item.activity) || [],
        backgroundColor: '#8B5CF6',
        borderColor: '#7C3AED',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#E5E7EB' }
        }
      },
      scales: {
        x: {
          ticks: { color: '#9CA3AF' },
          grid: { color: 'rgba(75, 85, 99, 0.2)' }
        },
        y: {
          ticks: { color: '#9CA3AF' },
          grid: { color: 'rgba(75, 85, 99, 0.2)' }
        }
      }
    }
  })
}

const exportContentData = async () => {
  // Здесь будет логика экспорта данных популярности контента
  console.log('Экспорт данных популярности контента')
}

onMounted(() => {
  loadData()
})
</script>
