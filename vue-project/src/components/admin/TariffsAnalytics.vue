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
          Apply Filters
        </button>
      </div>
    </div>

    <!-- Общая статистика -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Overall Tariff Statistics</h3>

      <div v-if="isLoading" class="flex justify-center py-8">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg">
        <p>{{ error }}</p>
        <button
          @click="loadData"
          class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
        >
          Try again
        </button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          v-for="(tariff, key) in tariffsData"
          :key="key"
          class="bg-gray-700 rounded-lg p-4"
        >
          <h4 class="text-md font-medium text-white mb-2">{{ formatTariff(key) }}</h4>
          <p class="text-2xl font-bold text-purple-500 mb-2">{{ tariff.total }}</p>
          <p class="text-sm text-gray-400">generations</p>

          <div class="mt-4">
            <h5 class="text-sm font-medium text-white mb-2">Popular content types:</h5>
            <ul class="space-y-2">
              <li
                v-for="type in tariff.popular_types"
                :key="type.type"
                class="flex justify-between items-center"
              >
                <span class="text-sm text-gray-300">{{ formatContentType(type.type) }}</span>
                <div class="flex items-center">
                  <span class="text-sm text-gray-400 mr-2">{{ type.count }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                    {{ type.percent }}%
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Детальная статистика по тарифам -->
    <div v-for="(tariff, key) in tariffsData" :key="`detail-${key}`" class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">
        {{ formatTariff(key) }}: Distribution by Content Types
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- График распределения по типам контента -->
        <div class="bg-gray-700 rounded-lg p-4">
          <div class="h-64">
            <canvas :id="`chart-${key}`"></canvas>
          </div>
        </div>

        <!-- Таблица с данными -->
        <div class="bg-gray-700 rounded-lg p-4">
          <table class="w-full text-left">
            <thead class="bg-gray-800">
              <tr>
                <th class="p-2">Content Type</th>
                <th class="p-2">Count</th>
                <th class="p-2">Percentage</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(count, type) in tariff.by_type"
                :key="`${key}-${type}`"
                class="border-t border-gray-600 hover:bg-gray-600/50"
              >
                <td class="p-2">{{ formatContentType(String(type)) }}</td>
                <td class="p-2">{{ count }}</td>
                <td class="p-2">
                  <span class="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                    {{ tariff.by_type_percent[type] }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- История покупок тарифов -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Tariff Purchase History</h3>

      <div v-if="isLoading" class="flex justify-center py-8">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>

      <div v-else-if="purchaseHistory.length === 0" class="text-center py-8 text-gray-400">
        <p>No tariff purchase data for selected period</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-gray-700">
            <tr>
              <th class="p-3 text-gray-300">Date</th>
              <th class="p-3 text-gray-300">User</th>
              <th class="p-3 text-gray-300">Tariff</th>
              <th class="p-3 text-gray-300">Cost</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="purchase in purchaseHistory"
              :key="`${purchase.user_name}-${purchase.purchased_at}`"
              class="border-t border-gray-600 hover:bg-gray-700/50"
            >
              <td class="p-3 text-gray-300">{{ purchase.date }}</td>
              <td class="p-3">
                <div class="flex flex-col">
                  <span class="text-white font-medium">{{ purchase.user_name }}</span>
                  <span class="text-gray-400 text-sm">@{{ purchase.username || 'unknown' }}</span>
                </div>
              </td>
              <td class="p-3">
                <div class="flex flex-col">
                  <span class="text-white font-medium">{{ purchase.tariff_name || formatTariff(purchase.tariff_type) }}</span>
                  <span class="text-gray-400 text-sm">{{ purchase.tariff_type }}</span>
                </div>
              </td>
              <td class="p-3">
                <span class="px-2 py-1 rounded-full bg-purple-500/20 text-purple-300 text-sm">
                  {{ purchase.price_points }} баллов
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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
const tariffsData = ref<Record<string, any>>({})
const purchaseHistory = ref<any[]>([])
const charts = ref<Record<string, Chart>>({})

// Methods
const loadData = async () => {
  isLoading.value = true
  error.value = null

  try {
    console.log('Loading tariffs analytics data...')

    // Получаем данные об аналитике тарифов
    const response = await store.getTariffsAnalytics(period.value)

    console.log('Tariffs analytics response:', response)

    if (response && response.by_tariff) {
      tariffsData.value = response.by_tariff
      purchaseHistory.value = response.purchase_history || []

      // Обновляем графики после получения данных и обновления DOM
      console.log('Setting timeout to update charts...')
      setTimeout(() => {
        console.log('Updating charts after timeout...')
        console.log('Available tariffs:', Object.keys(tariffsData.value))
        updateCharts()
      }, 1000)
    } else {
      console.error('Invalid response format:', response)
      error.value = 'Некорректный формат ответа от сервера'
    }
  } catch (err: any) {
    console.error('Error loading tariffs analytics data:', err)
    error.value = err.message || 'Ошибка загрузки данных'
  } finally {
    isLoading.value = false
  }
}

const updateCharts = () => {
  console.log('updateCharts called with tariffsData:', tariffsData.value)

  // Проверяем, что у нас есть данные
  if (!tariffsData.value || Object.keys(tariffsData.value).length === 0) {
    console.warn('No tariffs data available for charts')
    return
  }

  // Уничтожаем предыдущие графики
  Object.values(charts.value).forEach(chart => {
    chart.destroy()
  })

  // Очищаем объект с графиками
  charts.value = {}

  // Создаем новые графики для каждого тарифа
  Object.keys(tariffsData.value).forEach(tariff => {
    console.log(`Looking for canvas element: chart-${tariff}`)
    const chartRef = document.getElementById(`chart-${tariff}`) as HTMLCanvasElement

    if (!chartRef) {
      console.error(`Chart canvas for tariff ${tariff} not found`)
      // Попробуем найти все canvas элементы на странице для отладки
      const allCanvases = document.querySelectorAll('canvas')
      console.log('All canvas elements found:', Array.from(allCanvases).map(c => c.id))
      return
    }

    console.log(`Found chart canvas for tariff ${tariff}:`, chartRef)

    const tariffData = tariffsData.value[tariff]

    // Подготавливаем данные для графика
    const labels = Object.keys(tariffData.by_type).map(type => formatContentType(type as string))
    const data = Object.values(tariffData.by_type) as number[]

    // Создаем новый график
    charts.value[tariff] = new Chart(chartRef, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: [
            '#8B5CF6', // Violet
            '#3B82F6', // Blue
            '#10B981', // Emerald
            '#F59E0B', // Amber
            '#EF4444', // Red
            '#EC4899', // Pink
            '#06B6D4', // Cyan
            '#F97316'  // Orange
          ],
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
  })
}

const formatTariff = (tariff: string) => {
  const tariffMap: Record<string, string> = {
    'free': 'Free',
    'tariff_2': 'Standard',
    'tariff_4': 'Premium',
    'tariff_6': 'VIP'
  }
  return tariffMap[tariff] || tariff
}

const formatContentType = (type: string) => {
  const typeMap: Record<string, string> = {
    'lesson_plan': 'Lesson Plan',
    'exercise': 'Exercise',
    'game': 'Game',
    'image': 'Image',
    'text_analysis': 'Text Analysis',
    'concept_explanation': 'Concept Explanation',
    'course': 'Course',
    'free_query': 'AI Assistant',
    'unknown': 'Unknown'
  }
  return typeMap[type] || type
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
