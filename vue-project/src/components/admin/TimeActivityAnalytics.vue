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
          </select>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Activity Type</label>
          <select
            v-model="activityType"
            class="bg-gray-700 text-white rounded-lg px-4 py-2 w-48"
            @change="loadData"
          >
            <option value="all">All Activity</option>
            <option value="generations">Generations</option>
            <option value="logins">Logins</option>
            <option value="purchases">Purchases</option>
          </select>
        </div>

        <button
          @click="exportTimeData"
          class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          :disabled="isLoading"
        >
          <Download class="w-4 h-4" />
          Export
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
        <h3 class="text-lg font-medium text-white mb-2">Peak Time</h3>
        <p class="text-3xl font-bold text-purple-500">{{ timeData.peakHour }}:00</p>
        <p class="text-sm text-gray-400 mt-1">Maximum Activity</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Most Active Day</h3>
        <p class="text-3xl font-bold text-blue-500">{{ timeData.peakDay }}</p>
        <p class="text-sm text-gray-400 mt-1">Day of Week</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Average Session</h3>
        <p class="text-3xl font-bold text-green-500">{{ timeData.avgSessionDuration }}m</p>
        <p class="text-sm text-gray-400 mt-1">Duration</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Active Users</h3>
        <p class="text-3xl font-bold text-yellow-500">{{ timeData.activeUsers }}</p>
        <p class="text-sm text-gray-400 mt-1">At Peak Time</p>
      </div>
    </div>

    <!-- Графики -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Активность по часам -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Activity by Hours</h3>
        <div class="h-64">
          <canvas ref="hourlyChart"></canvas>
        </div>
      </div>

      <!-- Активность по дням недели -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Activity by Weekdays</h3>
        <div class="h-64">
          <canvas ref="weeklyChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Тепловая карта -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Activity Heatmap</h3>
      <div class="overflow-x-auto">
        <div class="grid grid-cols-25 gap-1 min-w-max">
          <!-- Заголовки часов -->
          <div class="text-xs text-gray-400 p-1"></div>
          <div v-for="hour in 24" :key="hour" class="text-xs text-gray-400 p-1 text-center">
            {{ hour - 1 }}
          </div>

          <!-- Данные по дням -->
          <template v-for="(day, dayIndex) in timeData.heatmapData" :key="dayIndex">
            <div class="text-xs text-gray-400 p-1 text-right">{{ day.name }}</div>
            <div
              v-for="(value, hourIndex) in day.hours"
              :key="hourIndex"
              class="w-6 h-6 rounded-sm"
              :style="{ backgroundColor: getHeatmapColor(value) }"
              :title="`${day.name} ${hourIndex}:00 - ${value} активностей`"
            ></div>
          </template>
        </div>

        <!-- Легенда -->
        <div class="flex items-center justify-center mt-4 gap-2">
          <span class="text-xs text-gray-400">Меньше</span>
          <div class="flex gap-1">
            <div class="w-3 h-3 rounded-sm bg-gray-700"></div>
            <div class="w-3 h-3 rounded-sm bg-purple-900"></div>
            <div class="w-3 h-3 rounded-sm bg-purple-700"></div>
            <div class="w-3 h-3 rounded-sm bg-purple-500"></div>
            <div class="w-3 h-3 rounded-sm bg-purple-300"></div>
          </div>
          <span class="text-xs text-gray-400">Больше</span>
        </div>
      </div>
    </div>

    <!-- Статистика по временным зонам -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Activity by Time Zones</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Morning (6-12)</h4>
          <p class="text-2xl font-bold text-yellow-400">{{ timeData.timeZones.morning }}%</p>
          <p class="text-sm text-gray-400">of total activity</p>
        </div>
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Afternoon (12-18)</h4>
          <p class="text-2xl font-bold text-blue-400">{{ timeData.timeZones.afternoon }}%</p>
          <p class="text-sm text-gray-400">of total activity</p>
        </div>
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Evening (18-24)</h4>
          <p class="text-2xl font-bold text-purple-400">{{ timeData.timeZones.evening }}%</p>
          <p class="text-sm text-gray-400">of total activity</p>
        </div>
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Night (0-6)</h4>
          <p class="text-2xl font-bold text-gray-400">{{ timeData.timeZones.night }}%</p>
          <p class="text-sm text-gray-400">of total activity</p>
        </div>
      </div>
    </div>

    <!-- Таблица детальной статистики -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Detailed Daily Statistics</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-gray-900">
            <tr>
              <th class="p-4">Day of Week</th>
              <th class="p-4">Total Activities</th>
              <th class="p-4">Unique Users</th>
              <th class="p-4">Peak Time</th>
              <th class="p-4">Average Session</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="day in timeData.dailyStats"
              :key="day.name"
              class="border-t border-gray-700 hover:bg-gray-700/50"
            >
              <td class="p-4 text-white">{{ day.name }}</td>
              <td class="p-4 text-gray-300">{{ day.totalActivity }}</td>
              <td class="p-4 text-blue-400">{{ day.uniqueUsers }}</td>
              <td class="p-4 text-purple-400">{{ day.peakHour }}:00</td>
              <td class="p-4 text-green-400">{{ day.avgSession }}м</td>
            </tr>
          </tbody>
        </table>
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
const activityType = ref('all')

// Ссылки на canvas элементы
const hourlyChart = ref<HTMLCanvasElement | null>(null)
const weeklyChart = ref<HTMLCanvasElement | null>(null)

// Данные
const timeData = ref({
  peakHour: 14,
  peakDay: 'Среда',
  avgSessionDuration: 23,
  activeUsers: 156,
  timeZones: {
    morning: 18,
    afternoon: 42,
    evening: 35,
    night: 5
  },
  heatmapData: [],
  dailyStats: [],
  hourlyActivity: [],
  weeklyActivity: []
})

// Графики
let hourlyChartInstance: Chart | null = null
let weeklyChartInstance: Chart | null = null

// Методы
const getHeatmapColor = (value: number): string => {
  if (value === 0) return '#374151'
  if (value <= 5) return '#581C87'
  if (value <= 15) return '#7C3AED'
  if (value <= 30) return '#A855F7'
  return '#C084FC'
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

    const response = await fetch(`/api/v1/admin/analytics/time-activity?period=${period.value}&activity_type=${activityType.value}`, {
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
    timeData.value = {
      peakHour: data.hourlyActivity?.reduce((max: any, curr: any) =>
        curr.count > max.count ? curr : max, {hour: 14, count: 0})?.hour || 14,
      peakDay: data.dailyActivity?.reduce((max: any, curr: any) =>
        curr.count > max.count ? curr : max, {day: 'Среда', count: 0})?.day || 'Среда',
      avgSessionDuration: data.avgSessionDuration || 0,
      activeUsers: data.hourlyActivity?.reduce((sum: number, item: any) => sum + item.count, 0) || 0,
      timeZones: {
        morning: data.hourlyActivity?.slice(6, 12).reduce((sum: number, item: any) => sum + item.count, 0) || 0,
        afternoon: data.hourlyActivity?.slice(12, 18).reduce((sum: number, item: any) => sum + item.count, 0) || 0,
        evening: data.hourlyActivity?.slice(18, 24).reduce((sum: number, item: any) => sum + item.count, 0) || 0,
        night: data.hourlyActivity?.slice(0, 6).reduce((sum: number, item: any) => sum + item.count, 0) || 0
      },
      heatmapData: [],
      dailyStats: [],
      hourlyActivity: data.hourlyActivity || [],
      weeklyActivity: data.dailyActivity || []
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
  updateHourlyChart()
  updateWeeklyChart()
}

const updateHourlyChart = () => {
  if (!hourlyChart.value) {
    console.warn('Hourly chart canvas not found')
    return
  }

  if (hourlyChartInstance) {
    hourlyChartInstance.destroy()
  }

  const ctx = hourlyChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for hourly chart')
    return
  }

  console.log('Creating hourly chart with data:', timeData.value.hourlyActivity)

  hourlyChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: timeData.value.hourlyActivity?.map(item => `${item.hour}:00`) || [],
      datasets: [{
        label: 'Активность',
        data: timeData.value.hourlyActivity?.map(item => item.count) || [],
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

const updateWeeklyChart = () => {
  if (!weeklyChart.value) {
    console.warn('Weekly chart canvas not found')
    return
  }

  if (weeklyChartInstance) {
    weeklyChartInstance.destroy()
  }

  const ctx = weeklyChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for weekly chart')
    return
  }

  console.log('Creating weekly chart with data:', timeData.value.weeklyActivity)

  weeklyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: timeData.value.weeklyActivity?.map(item => item.day) || [],
      datasets: [{
        label: 'Активность',
        data: timeData.value.weeklyActivity?.map(item => item.count) || [],
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
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

const exportTimeData = async () => {
  // Здесь будет логика экспорта данных активности по времени
  console.log('Экспорт данных активности по времени')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.grid-cols-25 {
  grid-template-columns: repeat(25, minmax(0, 1fr));
}
</style>
