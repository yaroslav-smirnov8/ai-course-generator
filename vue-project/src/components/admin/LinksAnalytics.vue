<template>
  <div class="space-y-6">
    <!-- Заголовок и фильтры -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <h2 class="text-xl font-semibold text-white">Link Click Statistics</h2>

      <!-- Фильтры периода -->
      <div class="flex gap-2">
        <button
          v-for="period in periods"
          :key="period.value"
          @click="selectedPeriod = period.value; fetchData()"
          class="px-3 py-1 text-sm rounded-lg"
          :class="selectedPeriod === period.value
            ? 'bg-purple-500 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <!-- Карточки со статистикой -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <StatCard
        title="Всего переходов"
        :value="analytics.total_clicks || 0"
        icon="Link"
        :trend="10"
        color="purple"
      />
      <StatCard
        title="Уникальных пользователей"
        :value="analytics.unique_users || 0"
        icon="Users"
        :trend="5"
        color="blue"
      />
    </div>

    <!-- Графики -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- График активности -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Activity by Time</h3>

        <!-- Загрузка -->
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- График -->
        <div v-else class="h-64">
          <canvas id="activityChart" ref="activityChartRef"></canvas>
        </div>
      </div>

      <!-- Диаграмма распределения -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Popular Links</h3>

        <!-- Загрузка -->
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
        </div>

        <!-- График -->
        <div v-else class="h-64">
          <canvas id="distributionChart" ref="distributionChartRef"></canvas>
        </div>
      </div>
    </div>

    <!-- Таблица с данными -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Детальная информация</h3>

      <!-- Загрузка -->
      <div v-if="loading" class="flex justify-center items-center py-8">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- Таблица -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="text-gray-400 text-sm">
            <tr class="border-b border-gray-700">
              <th class="py-3 px-4">Название</th>
              <th class="py-3 px-4">URL</th>
              <th class="py-3 px-4 text-right">Переходы</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="link in analytics.popular_links" :key="link.link_id" class="border-b border-gray-700 hover:bg-gray-700/50">
              <td class="py-3 px-4 text-white">{{ link.link_title }}</td>
              <td class="py-3 px-4 text-gray-400">
                <a :href="link.link_url" target="_blank" class="text-purple-400 hover:text-purple-300 truncate block max-w-xs">
                  {{ link.link_url }}
                </a>
              </td>
              <td class="py-3 px-4 text-right text-white">{{ link.click_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { apiClient } from '@/api/client'
import StatCard from './cards/StatCard.vue'
import Chart from 'chart.js/auto'
import { Link, Users } from 'lucide-vue-next'

// Определение типов
interface LinkAnalytics {
  total_clicks: number
  unique_users: number
  popular_links: Array<{
    link_id: string
    link_title: string
    link_url: string
    click_count: number
  }>
  clicks_by_time: Array<{
    date: string
    count: number
  }>
  period: string
}

// Состояние компонента
const loading = ref(true)
const selectedPeriod = ref('week')
const analytics = ref<LinkAnalytics>({
  total_clicks: 0,
  unique_users: 0,
  popular_links: [],
  clicks_by_time: [],
  period: 'week'
})

// Периоды для фильтрации
const periods = [
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
  { value: 'year', label: 'Год' },
  { value: 'all', label: 'Все время' }
]

// Ссылки на элементы canvas для графиков
const activityChartRef = ref<HTMLCanvasElement | null>(null)
const distributionChartRef = ref<HTMLCanvasElement | null>(null)

// Экземпляры графиков
let activityChart: Chart | null = null
let distributionChart: Chart | null = null

// Цвета для графиков
const chartColors = [
  '#8B5CF6', // Purple
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Yellow
  '#EF4444', // Red
  '#EC4899', // Pink
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#F97316', // Orange
  '#8B5CF6', // Purple (repeat)
]

// Загрузка данных
const fetchData = async () => {
  console.log('LinksAnalytics: Начало загрузки данных')
  loading.value = true
  try {
    console.log('LinksAnalytics: Вызов apiClient.getLinksAnalytics с периодом:', selectedPeriod.value)
    const response = await apiClient.getLinksAnalytics({ period: selectedPeriod.value })
    console.log('LinksAnalytics: Получен ответ:', response)

    // Проверяем структуру ответа
    if (!response) {
      console.error('LinksAnalytics: Ответ пустой')
    } else {
      console.log('LinksAnalytics: Структура ответа:', {
        hasTotal: 'total_clicks' in response,
        hasUniqueUsers: 'unique_users' in response,
        hasPopularLinks: 'popular_links' in response && Array.isArray(response.popular_links),
        hasClicksByTime: 'clicks_by_time' in response && Array.isArray(response.clicks_by_time),
        hasPeriod: 'period' in response
      })
    }

    analytics.value = response

    // Обновляем графики после получения данных с небольшой задержкой,
    // чтобы DOM успел обновиться
    console.log('LinksAnalytics: Обновляем графики с задержкой')
    setTimeout(() => {
      updateCharts()
    }, 1000)
  } catch (error) {
    console.error('LinksAnalytics: Ошибка при загрузке данных:', error)
    console.error('LinksAnalytics: Детали ошибки:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })
  } finally {
    console.log('LinksAnalytics: Загрузка данных завершена')
    loading.value = false
  }
}

// Обновление графиков
const updateCharts = () => {
  console.log('LinksAnalytics: Начало обновления графиков')

  // Проверяем наличие данных для графиков
  if (!analytics.value.clicks_by_time || analytics.value.clicks_by_time.length === 0) {
    console.warn('LinksAnalytics: Нет данных для графика активности')
  }

  if (!analytics.value.popular_links || analytics.value.popular_links.length === 0) {
    console.warn('LinksAnalytics: Нет данных для графика распределения')
  }

  updateActivityChart()
  updateDistributionChart()

  console.log('LinksAnalytics: Обновление графиков завершено')
}

// Обновление графика активности
const updateActivityChart = () => {
  const chartCanvas = document.getElementById('activityChart') as HTMLCanvasElement
  if (!chartCanvas) {
    console.error('LinksAnalytics: Canvas element for activity chart not found')
    return
  }

  // Уничтожаем предыдущий график, если он существует
  if (activityChart) {
    activityChart.destroy()
  }

  // Получаем данные для графика
  const labels = analytics.value.clicks_by_time.map(item => item.date)
  const data = analytics.value.clicks_by_time.map(item => item.count)

  console.log('LinksAnalytics: Activity chart data:', { labels, data })

  // Создаем новый график
  activityChart = new Chart(chartCanvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Переходы',
        data,
        borderColor: '#8B5CF6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(75, 85, 99, 0.2)'
          },
          ticks: {
            color: '#9CA3AF'
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(75, 85, 99, 0.2)'
          },
          ticks: {
            color: '#9CA3AF'
          }
        }
      }
    }
  })
}

// Обновление диаграммы распределения
const updateDistributionChart = () => {
  const chartCanvas = document.getElementById('distributionChart') as HTMLCanvasElement
  if (!chartCanvas) {
    console.error('LinksAnalytics: Canvas element for distribution chart not found')
    return
  }

  // Уничтожаем предыдущий график, если он существует
  if (distributionChart) {
    distributionChart.destroy()
  }

  // Получаем данные для графика (только топ-5 ссылок)
  const topLinks = analytics.value.popular_links.slice(0, 5)
  const labels = topLinks.map(link => link.link_title)
  const data = topLinks.map(link => link.click_count)

  console.log('LinksAnalytics: Distribution chart data:', { labels, data })

  // Создаем новый график
  distributionChart = new Chart(chartCanvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: chartColors.slice(0, labels.length),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: '#E5E7EB' // Gray-200
          }
        }
      }
    }
  })
}

// Загружаем данные при монтировании компонента
onMounted(() => {
  fetchData()
})

// Обновляем данные при изменении периода
watch(selectedPeriod, () => {
  fetchData()
})
</script>
