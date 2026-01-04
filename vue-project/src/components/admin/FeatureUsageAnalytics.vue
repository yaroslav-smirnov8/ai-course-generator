<template>
  <div class="space-y-6">
    <!-- Элементы управления -->
    <div class="flex justify-between items-center">
      <div class="flex gap-4">
        <select
          v-model="timeRange"
          class="bg-gray-800 text-white rounded-lg p-2"
        >
          <option value="day">Last 24 Hours</option>
          <option value="week">Last 7 Days</option>
          <option value="month">Last 30 Days</option>
        </select>

        <select
          v-model="featureType"
          class="bg-gray-800 text-white rounded-lg p-2"
        >
          <option value="">All Functions</option>
          <option
            v-for="feature in featureDistributionKeys"
            :key="feature"
            :value="feature"
          >
            {{ translateFeature(feature) }}
          </option>
        </select>
      </div>

      <button
        @click="fetchAnalytics"
        class="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
        title="Обновить данные"
      >
        <RefreshCw class="w-5 h-5" />
      </button>
    </div>

    <!-- Карточки с метриками -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Общее использование</h3>
        <div class="text-3xl font-bold text-purple-500">
          {{ analytics.total_usage.toLocaleString() }}
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Уникальные пользователи</h3>
        <div class="text-3xl font-bold text-blue-500">
          {{ analytics.unique_users.toLocaleString() }}
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">В среднем на пользователя</h3>
        <div class="text-3xl font-bold text-green-500">
          {{ averagePerUser }}
        </div>
      </div>
    </div>

    <!-- Распределение использования функций -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-2">Function Usage Distribution</h3>
      <p class="text-sm text-gray-400 mb-4">Distribution of usage across different functions</p>
      <div class="h-[400px] w-full relative bg-gray-900 rounded-lg">
        <canvas ref="pieChart" style="width: 100%; height: 100%; display: block;"></canvas>
        <!-- Индикатор загрузки -->
        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-gray-900/50">
          <div class="flex flex-col items-center gap-2">
            <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
            <div class="text-sm text-gray-400">Загрузка данных...</div>
          </div>
        </div>
        <!-- Сообщение об отсутствии данных -->
        <div v-if="!isLoading && Object.keys(analytics.feature_distribution).length === 0" class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <div class="text-gray-400 text-lg mb-2">📊</div>
            <div class="text-gray-400">No data for selected period</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Самые и наименее используемые функции -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Самые популярные функции</h3>
        <div class="space-y-2">
          <div
            v-if="analytics.most_popular.length > 0"
            v-for="(feature, index) in analytics.most_popular"
            :key="index"
            class="flex justify-between items-center"
          >
            <span class="text-gray-300">{{ feature.feature }}</span>
            <span class="text-gray-400">{{ feature.percentage.toFixed(1) }}%</span>
          </div>
          <div v-else class="text-center text-gray-400 py-4">
            Нет данных за выбранный период
          </div>
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Наименее используемые функции</h3>
        <div class="space-y-2">
          <div
            v-if="analytics.least_used.length > 0"
            v-for="(feature, index) in analytics.least_used"
            :key="index"
            class="flex justify-between items-center"
          >
            <span class="text-gray-300">{{ feature.feature }}</span>
            <span class="text-gray-400">{{ feature.percentage.toFixed(1) }}%</span>
          </div>
          <div v-else class="text-center text-gray-400 py-4">
            Нет данных за выбранный период
          </div>
        </div>
      </div>
    </div>

    <!-- Распределение по тарифам -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-2">Usage by Tariffs</h3>
      <p class="text-sm text-gray-400 mb-4">Distribution of function usage by tariff plans</p>
      <div class="h-[300px] w-full relative bg-gray-900 rounded-lg">
        <canvas ref="barChart" class="w-full h-full"></canvas>
        <!-- Сообщение об отсутствии данных -->
        <div v-if="!isLoading && Object.keys(analytics.user_distribution.by_tariff).length === 0" class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <div class="text-gray-400 text-lg mb-2">📊</div>
            <div class="text-gray-400">No data for selected period</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Экспорт -->
    <div class="flex justify-end">
      <button
        @click="exportData"
        class="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
      >
        <Download class="w-4 h-4" />
        Export Data
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Download, RefreshCw } from 'lucide-vue-next'
import Chart from 'chart.js/auto'
import type { Analytics } from '../../types/analytics'

// State
const timeRange = ref('week')
const featureType = ref('')
const isLoading = ref(false)

// Chart refs
const pieChart = ref<HTMLCanvasElement | null>(null)
const barChart = ref<HTMLCanvasElement | null>(null)

// Chart instances
let pieChartInstance: Chart | null = null
let barChartInstance: Chart | null = null
const analytics = ref<Analytics>({
  total_usage: 0,
  unique_users: 0,
  feature_distribution: {},
  user_distribution: {
    by_role: {},
    by_tariff: {}
  },
  most_popular: [],
  least_used: []
})

// Constants
const COLORS = ['#8B5CF6', '#EC4899', '#10B981', '#3B82F6', '#F59E0B']

// Computed
const featureDistributionKeys = computed(() =>
  Object.keys(analytics.value.feature_distribution)
)

const averagePerUser = computed(() =>
  (analytics.value.total_usage / analytics.value.unique_users || 0).toFixed(1)
)



// Methods
const translateFeature = (feature: string) => {
  const featureMap: Record<string, string> = {
    'lesson_plan': 'Lesson Plans',
    'exercise': 'Exercises',
    'game': 'Games',
    'image': 'Images',
    'text_analysis': 'Text Analysis',
    'transcript': 'Transcript',
    'free_query': 'Free Queries',
    'concept_explanation': 'Concept Explanations',
    'course': 'Courses'
  }
  return featureMap[feature] || feature
}

// Chart functions
const updateCharts = () => {
  console.log('updateCharts called')
  console.log('Current analytics data:', analytics.value)
  updatePieChart()
  updateBarChart()
}

const updatePieChart = () => {
  console.log('updatePieChart called')
  console.log('pieChart.value:', pieChart.value)
  console.log('analytics.value.feature_distribution:', analytics.value.feature_distribution)

  if (!pieChart.value) {
    console.warn('Pie chart canvas not found')
    return
  }

  if (pieChartInstance) {
    console.log('Destroying previous pie chart instance')
    pieChartInstance.destroy()
  }

  const ctx = pieChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for pie chart')
    return
  }

  // Проверяем размеры canvas
  console.log('Canvas dimensions:', {
    width: pieChart.value.clientWidth,
    height: pieChart.value.clientHeight,
    offsetWidth: pieChart.value.offsetWidth,
    offsetHeight: pieChart.value.offsetHeight
  })

  // Проверяем, есть ли данные для отображения
  if (!analytics.value.feature_distribution || Object.keys(analytics.value.feature_distribution).length === 0) {
    console.warn('No feature distribution data available')
    return
  }

  console.log('Creating pie chart with data:', analytics.value.feature_distribution)

  let labels = Object.keys(analytics.value.feature_distribution).map(key => {
    const typeMap: Record<string, string> = {
      'lesson_plan': 'Lesson Plans',
      'exercise': 'Exercises',
      'game': 'Games',
      'image': 'Images',
      'text_analysis': 'Text Analysis'
    }
    return typeMap[key] || key
  })

  let data = Object.values(analytics.value.feature_distribution).map((item: any) => item.total_usage || 0)

  console.log('Pie chart labels:', labels)
  console.log('Pie chart data:', data)

  // Если нет данных, не создаем график
  if (data.length === 0 || data.every(value => !value || value <= 0)) {
    console.warn('No valid data for pie chart')
    return
  }

  // Устанавливаем размеры canvas явно
  const containerWidth = pieChart.value.offsetWidth || 400
  const containerHeight = pieChart.value.offsetHeight || 400

  console.log('Setting canvas size:', { containerWidth, containerHeight })

  pieChart.value.width = containerWidth
  pieChart.value.height = containerHeight

  // Дополнительная проверка
  console.log('Canvas actual size after setting:', {
    width: pieChart.value.width,
    height: pieChart.value.height,
    style: pieChart.value.style.cssText
  })

  pieChartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: COLORS,
        borderColor: '#1F2937',
        borderWidth: 3,
        hoverBorderWidth: 4,
        hoverBorderColor: '#FFFFFF'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 20,
          bottom: 20,
          left: 20,
          right: 20
        }
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#E5E7EB',
            padding: 15,
            usePointStyle: true,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: '#1F2937',
          titleColor: '#FFFFFF',
          bodyColor: '#E5E7EB',
          borderColor: '#374151',
          borderWidth: 1
        }
      },
      elements: {
        arc: {
          borderWidth: 3
        }
      },
      animation: {
        animateRotate: true,
        animateScale: true
      }
    }
  })

  console.log('Pie chart created successfully')
}

const updateBarChart = () => {
  if (!barChart.value) {
    console.warn('Bar chart canvas not found')
    return
  }

  if (barChartInstance) {
    barChartInstance.destroy()
  }

  const ctx = barChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for bar chart')
    return
  }

  console.log('Creating bar chart with data:', analytics.value.user_distribution.by_tariff)

  // Проверяем, есть ли данные по тарифам
  if (!analytics.value.user_distribution.by_tariff || Object.keys(analytics.value.user_distribution.by_tariff).length === 0) {
    console.warn('No tariff distribution data available')
    return
  }

  const labels = Object.keys(analytics.value.user_distribution.by_tariff).map(tariff => {
    const tariffMap: Record<string, string> = {
      'basic': 'Basic',
      'standard': 'Standard',
      'premium': 'Premium',
      'vip': 'VIP'
    }
    return tariffMap[tariff] || tariff
  })

  const data = Object.values(analytics.value.user_distribution.by_tariff).map((item: any) => item.count || 0)

  barChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Количество пользователей',
        data,
        backgroundColor: '#3B82F6',
        borderColor: '#2563EB',
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

const fetchAnalytics = async () => {
  try {
    isLoading.value = true;

    // Получаем данные авторизации из Telegram WebApp
    const webApp = (window as any).Telegram?.WebApp
    const webAppData = webApp?.initData || localStorage.getItem('tg_web_app_data')

    if (!webAppData) {
      throw new Error('Нет данных авторизации')
    }

    // Преобразуем timeRange в период для API
    let period = 'month'
    if (timeRange.value === 'day') period = 'week'
    else if (timeRange.value === 'week') period = 'week'
    else if (timeRange.value === 'month') period = 'month'

    const response = await fetch(`/api/v1/admin/analytics/feature-usage?period=${period}`, {
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
    const featureDistribution: Record<string, any> = {}
    const mostPopular: Array<{feature: string, percentage: number}> = []
    const leastUsed: Array<{feature: string, percentage: number}> = []

    // Обрабатываем данные функций
    if (data.features && Array.isArray(data.features)) {
      data.features.forEach((feature: any, index: number) => {
        featureDistribution[feature.name] = {
          total_usage: feature.usage,
          percentage: feature.percentage
        }

        // Добавляем в топ популярных (первые 5)
        if (index < 5) {
          mostPopular.push({
            feature: feature.name,
            percentage: feature.percentage
          })
        }

        // Добавляем в наименее используемые (последние 3)
        if (index >= data.features.length - 3) {
          leastUsed.push({
            feature: feature.name,
            percentage: feature.percentage
          })
        }
      })
    }

    analytics.value = {
      total_usage: data.totalGenerations || 0,
      unique_users: data.totalGenerations || 0, // Пока используем общее количество
      feature_distribution: featureDistribution,
      user_distribution: {
        by_role: {},
        by_tariff: {}
      },
      most_popular: mostPopular,
      least_used: leastUsed.reverse() // Переворачиваем для правильного порядка
    };

    // Обновляем графики с задержкой для корректной инициализации DOM
    setTimeout(() => {
      updateCharts()
    }, 100)
  } catch (error) {
    console.error('Error fetching analytics:', error);
    // В случае ошибки создаем пустую структуру
    analytics.value = {
      total_usage: 0,
      unique_users: 0,
      feature_distribution: {},
      user_distribution: {
        by_role: {},
        by_tariff: {}
      },
      most_popular: [],
      least_used: []
    };
  } finally {
    isLoading.value = false;
  }
}

const exportData = () => {
  // Реализация функции экспорта данных
  console.log('Экспорт данных аналитики использования функций')
}

// Watchers
watch([timeRange, featureType], () => {
  fetchAnalytics()
})

// Lifecycle
onMounted(() => {
  console.log('FeatureUsageAnalytics mounted')
  console.log('pieChart ref:', pieChart.value)
  console.log('barChart ref:', barChart.value)

  // Добавляем небольшую задержку для инициализации DOM
  setTimeout(() => {
    console.log('After timeout - pieChart ref:', pieChart.value)
    console.log('After timeout - barChart ref:', barChart.value)
    fetchAnalytics()
  }, 50)
})
</script>
