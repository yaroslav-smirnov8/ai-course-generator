<template>
  <div class="bg-gray-800 rounded-lg p-6">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-medium text-white">User Distribution by Plans</h3>
      <div class="flex gap-2">
        <button
          v-for="period in periods"
          :key="period.value"
          @click="currentPeriod = period.value"
          class="px-3 py-1 text-sm rounded-lg"
          :class="currentPeriod === period.value
            ? 'bg-purple-500 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="isLoading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Loading data...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg">
      <p>{{ error }}</p>
      <button
        @click="loadData"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Try again
      </button>
    </div>

    <!-- Графики -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Круговая диаграмма -->
      <div class="bg-gray-700 rounded-lg p-4">
        <h4 class="text-lg font-medium text-white mb-2">Distribution by Plans</h4>
        <div class="h-64">
          <canvas ref="pieChartRef"></canvas>
        </div>
      </div>

      <!-- Статистика -->
      <div class="bg-gray-700 rounded-lg p-4">
        <h4 class="text-lg font-medium text-white mb-4">Plan Statistics</h4>
        <div class="space-y-4">
          <div v-for="(stat, index) in tariffStats" :key="index" class="flex justify-between items-center">
            <div class="flex items-center">
              <div
                class="w-3 h-3 rounded-full mr-2"
                :style="{ backgroundColor: chartColors[index % chartColors.length] }"
              ></div>
              <span class="text-gray-300">{{ formatTariffName(stat.name) }}</span>
            </div>
            <div class="flex items-center">
              <span class="text-white font-medium">{{ stat.count }}</span>
              <span class="text-gray-400 ml-2">({{ Math.round(stat.percentage) }}%)</span>
            </div>
          </div>

          <div class="border-t border-gray-600 pt-4 mt-4">
            <div class="flex justify-between items-center">
              <span class="text-gray-300">Total users:</span>
              <span class="text-white font-medium">{{ totalUsers }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import Chart from 'chart.js/auto'

// Props
const props = defineProps<{
  users?: any[]
}>()

// State
const currentPeriod = ref('all')
const isLoading = ref(false)
const error = ref<string | null>(null)
const pieChartRef = ref<HTMLCanvasElement | null>(null)
const pieChart = ref<Chart | null>(null)
const tariffData = ref<any[]>([])

// Constants
const periods = [
  { value: 'all', label: 'All' },
  { value: 'month', label: 'Month' },
  { value: 'week', label: 'Week' }
]

const chartColors = [
  '#4F46E5', // Indigo
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Violet
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#F97316'  // Orange
]

// Computed
const tariffStats = computed(() => {
  console.log('TARIFF_CHART: Computing tariffStats');
  console.log('TARIFF_CHART: props.users:', props.users);

  if (!props.users || props.users.length === 0) {
    console.log('TARIFF_CHART: No users data, returning default stats');
    return [
      { name: 'basic', count: 0, percentage: 0 },
      { name: 'tariff_2', count: 0, percentage: 0 },
      { name: 'tariff_4', count: 0, percentage: 0 },
      { name: 'tariff_6', count: 0, percentage: 0 },
      { name: 'no_tariff', count: 0, percentage: 0 }
    ]
  }

  // Фильтруем пользователей по периоду, если нужно
  let filteredUsers = [...props.users]
  if (currentPeriod.value !== 'all') {
    const now = new Date()
    const cutoff = new Date()

    if (currentPeriod.value === 'week') {
      cutoff.setDate(now.getDate() - 7)
    } else if (currentPeriod.value === 'month') {
      cutoff.setMonth(now.getMonth() - 1)
    }

    filteredUsers = filteredUsers.filter(user => {
      const createdAt = new Date(user.created_at)
      return createdAt >= cutoff
    })
  }

  // Группируем пользователей по тарифам
  const tariffCounts: Record<string, number> = {
    'basic': 0,
    'tariff_2': 0,
    'tariff_4': 0,
    'tariff_6': 0,
    'no_tariff': 0
  }

  filteredUsers.forEach(user => {
    const tariff = user.tariff || 'no_tariff'
    tariffCounts[tariff] = (tariffCounts[tariff] || 0) + 1
  })

  // Преобразуем в массив для отображения
  const total = filteredUsers.length
  return Object.entries(tariffCounts).map(([name, count]) => ({
    name,
    count,
    percentage: total > 0 ? (count / total) * 100 : 0
  })).sort((a, b) => b.count - a.count) // Сортируем по убыванию количества
})

const totalUsers = computed(() => {
  if (!props.users) return 0

  // Фильтруем пользователей по периоду, если нужно
  if (currentPeriod.value === 'all') {
    return props.users.length
  }

  const now = new Date()
  const cutoff = new Date()

  if (currentPeriod.value === 'week') {
    cutoff.setDate(now.getDate() - 7)
  } else if (currentPeriod.value === 'month') {
    cutoff.setMonth(now.getMonth() - 1)
  }

  return props.users.filter(user => {
    const createdAt = new Date(user.created_at)
    return createdAt >= cutoff
  }).length
})

// Methods
const formatTariffName = (tariff: string): string => {
  const tariffMap: Record<string, string> = {
    'basic': 'Basic',
    'tariff_2': 'Standard',
    'tariff_4': 'Premium',
    'tariff_6': 'VIP',
    'no_tariff': 'No Tariff'
  }
  return tariffMap[tariff] || tariff
}

const updateChart = () => {
  if (!pieChartRef.value) return

  // Уничтожаем предыдущий график, если он существует
  if (pieChart.value) {
    pieChart.value.destroy()
  }

  // Получаем данные для графика
  const labels = tariffStats.value.map(stat => formatTariffName(stat.name))
  const data = tariffStats.value.map(stat => stat.count)

  // Создаем новый график
  pieChart.value = new Chart(pieChartRef.value, {
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
  updateChart()
})

// Следим за изменением периода и данных пользователей
watch([currentPeriod, () => props.users], () => {
  updateChart()
})
</script>
