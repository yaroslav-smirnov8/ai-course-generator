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
          >
            <option value="week">Week</option>
            <option value="month">Month</option>
            <option value="year">Year</option>
            <option value="all">All Time</option>
          </select>
        </div>

        <button
          @click="loadData"
          class="bg-purple-500 text-white rounded-lg px-4 py-2 mt-6"
        >
          Применить фильтры
        </button>
      </div>
    </div>

    <!-- Общая статистика -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Общая статистика по достижениям</h3>

      <div v-if="isLoading" class="flex justify-center py-8">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg">
        <p>{{ error }}</p>
        <button
          @click="loadData"
          class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
        >
          Попробовать снова
        </button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-md font-medium text-white mb-2">Всего достижений</h4>
          <p class="text-2xl font-bold text-purple-500 mb-2">{{ achievementsStats.total_achievements || 0 }}</p>
        </div>

        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-md font-medium text-white mb-2">Разблокировано</h4>
          <p class="text-2xl font-bold text-green-500 mb-2">{{ achievementsStats.unlocked_achievements || 0 }}</p>
          <p class="text-sm text-gray-400">
            {{ calculatePercentage(achievementsStats.unlocked_achievements, achievementsStats.total_achievements) }}% от общего числа
          </p>
        </div>

        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-md font-medium text-white mb-2">Баллов начислено</h4>
          <p class="text-2xl font-bold text-yellow-500 mb-2">{{ achievementsStats.total_points_earned || 0 }}</p>
        </div>

        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-md font-medium text-white mb-2">Активных пользователей</h4>
          <p class="text-2xl font-bold text-blue-500 mb-2">{{ achievementsStats.active_users || 0 }}</p>
        </div>
      </div>
    </div>

    <!-- Популярные достижения -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Популярные достижения</h3>

      <div v-if="isLoading" class="flex justify-center py-8">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="!achievementsStats.popular_achievements || achievementsStats.popular_achievements.length === 0" class="text-gray-400 italic">
        Нет данных о популярных достижениях
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="achievement in achievementsStats.popular_achievements"
          :key="achievement.id"
          class="bg-gray-700 rounded-lg p-4"
        >
          <div class="flex items-start">
            <span class="text-2xl mr-3">{{ achievement.icon || '🏆' }}</span>
            <div>
              <h4 class="text-md font-medium text-white">{{ achievement.name }}</h4>
              <p class="text-sm text-gray-400">{{ achievement.description }}</p>
              <div class="mt-2 flex items-center">
                <span class="text-green-400 font-medium">{{ achievement.unlock_count || 0 }}</span>
                <span class="text-gray-400 text-sm ml-2">разблокировано</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- График разблокировки достижений -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Динамика разблокировки достижений</h3>

      <div v-if="isLoading" class="flex justify-center py-8">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="!achievementsStats.unlocks_over_time || achievementsStats.unlocks_over_time.length === 0" class="text-gray-400 italic">
        Нет данных о динамике разблокировки достижений
      </div>

      <div v-else class="h-80">
        <canvas id="achievements-chart"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import Chart from 'chart.js/auto'

const store = useMainStore()

// State
const period = ref('week')
const isLoading = ref(false)
const error = ref<string | null>(null)
const achievementsStats = ref<any>({
  total_achievements: 0,
  unlocked_achievements: 0,
  total_points_earned: 0,
  active_users: 0,
  popular_achievements: [],
  unlocks_over_time: []
})
let chart: Chart | null = null

// Methods
const loadData = async () => {
  isLoading.value = true
  error.value = null

  try {
    console.log('Loading achievements analytics data for period:', period.value)

    // Вызываем метод из хранилища для получения статистики по достижениям
    const response = await store.getAchievementsAnalytics(period.value)

    console.log('Achievements analytics response:', response)

    if (response) {
      achievementsStats.value = response

      // Обновляем график после получения данных
      setTimeout(() => {
        updateChart()
      }, 300)
    } else {
      console.error('Invalid response format:', response)
      error.value = 'Некорректный формат ответа от сервера'
    }
  } catch (err: any) {
    console.error('Error loading achievements analytics data:', err)
    error.value = err.message || 'Ошибка загрузки данных'
  } finally {
    isLoading.value = false
  }
}

const updateChart = () => {
  // Уничтожаем предыдущий график, если он существует
  if (chart) {
    chart.destroy()
  }

  // Получаем canvas элемент
  const chartCanvas = document.getElementById('achievements-chart') as HTMLCanvasElement

  if (!chartCanvas) {
    console.error('Chart canvas not found')
    return
  }

  // Проверяем наличие данных для графика
  if (!achievementsStats.value.unlocks_over_time || achievementsStats.value.unlocks_over_time.length === 0) {
    console.error('No data for chart')
    return
  }

  // Подготавливаем данные для графика
  const labels = achievementsStats.value.unlocks_over_time.map((item: any) => item.date)
  const data = achievementsStats.value.unlocks_over_time.map((item: any) => item.count)

  // Создаем новый график
  chart = new Chart(chartCanvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Разблокировано достижений',
        data,
        borderColor: '#8B5CF6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderWidth: 2,
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: '#E5E7EB'
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#9CA3AF'
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: '#9CA3AF'
          }
        }
      }
    }
  })
}

const calculatePercentage = (value: number, total: number): number => {
  if (!total) return 0
  return Math.round((value / total) * 100)
}



// Watch
watch(period, () => {
  loadData()
})

// Lifecycle hooks
onMounted(() => {
  loadData()
})
</script>
