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
            <option value="all">All Time</option>
          </select>
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1">Currency</label>
          <select
            v-model="currency"
            class="bg-gray-700 text-white rounded-lg px-4 py-2 w-32"
          >
            <option value="RUB">₽ RUB</option>
            <option value="USD">$ USD</option>
            <option value="EUR">€ EUR</option>
          </select>
        </div>

        <button
          @click="exportFinancialData"
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
        <h3 class="text-lg font-medium text-white mb-2">Total Revenue</h3>
        <p class="text-3xl font-bold text-green-500">{{ formatCurrency(financialData.totalRevenue) }}</p>
        <p class="text-sm text-gray-400 mt-1">
          <span :class="financialData.revenueGrowth >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ financialData.revenueGrowth >= 0 ? '+' : '' }}{{ financialData.revenueGrowth.toFixed(1) }}%
          </span>
          from previous period
        </p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">ARPU</h3>
        <p class="text-3xl font-bold text-blue-500">{{ formatCurrency(financialData.arpu) }}</p>
        <p class="text-sm text-gray-400 mt-1">Average Revenue Per User</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">Conversion</h3>
        <p class="text-3xl font-bold text-purple-500">{{ financialData.conversionRate.toFixed(1) }}%</p>
        <p class="text-sm text-gray-400 mt-1">From Free to Paid</p>
      </div>

      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-2">LTV</h3>
        <p class="text-3xl font-bold text-yellow-500">{{ formatCurrency(financialData.ltv) }}</p>
        <p class="text-sm text-gray-400 mt-1">Lifetime Value</p>
      </div>
    </div>

    <!-- Графики -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- График доходов -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Revenue Dynamics</h3>
        <div class="h-64">
          <canvas ref="revenueChart"></canvas>
        </div>
      </div>

      <!-- Распределение доходов по тарифам -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Revenue by Plans</h3>
        <div class="h-64">
          <canvas ref="tariffRevenueChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Таблица топ тарифов -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Top Plans by Revenue</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-gray-900">
            <tr>
              <th class="p-4">Plan</th>
              <th class="p-4">Subscribers</th>
              <th class="p-4">Revenue</th>
              <th class="p-4">Share</th>
              <th class="p-4">Average Check</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tariff in financialData.topTariffs"
              :key="tariff.name"
              class="border-t border-gray-700 hover:bg-gray-700/50"
            >
              <td class="p-4 text-white">{{ tariff.name }}</td>
              <td class="p-4 text-gray-300">{{ tariff.subscribers }}</td>
              <td class="p-4 text-green-400">{{ formatCurrency(tariff.revenue) }}</td>
              <td class="p-4 text-gray-300">{{ tariff.share.toFixed(1) }}%</td>
              <td class="p-4 text-blue-400">{{ formatCurrency(tariff.averageCheck) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Прогнозы -->
    <div class="bg-gray-800 rounded-lg p-6">
      <h3 class="text-lg font-medium text-white mb-4">Forecasts</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Next Month</h4>
          <p class="text-2xl font-bold text-green-400">{{ formatCurrency(financialData.forecast.nextMonth) }}</p>
          <p class="text-sm text-gray-400">Revenue forecast</p>
        </div>
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Next Quarter</h4>
          <p class="text-2xl font-bold text-blue-400">{{ formatCurrency(financialData.forecast.nextQuarter) }}</p>
          <p class="text-sm text-gray-400">Revenue forecast</p>
        </div>
        <div class="bg-gray-700 rounded-lg p-4">
          <h4 class="text-white font-medium mb-2">Churn Rate</h4>
          <p class="text-2xl font-bold text-red-400">{{ financialData.churnRate.toFixed(1) }}%</p>
          <p class="text-sm text-gray-400">User Churn</p>
        </div>
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
const currency = ref('RUB')

// Ссылки на canvas элементы
const revenueChart = ref<HTMLCanvasElement | null>(null)
const tariffRevenueChart = ref<HTMLCanvasElement | null>(null)

// Данные
const financialData = ref({
  totalRevenue: 0,
  revenueGrowth: 0,
  arpu: 0,
  conversionRate: 0,
  ltv: 0,
  churnRate: 0,
  topTariffs: [],
  revenueHistory: [],
  forecast: {
    nextMonth: 0,
    nextQuarter: 0
  }
})

// Графики
let revenueChartInstance: Chart | null = null
let tariffRevenueChartInstance: Chart | null = null

// Методы
const formatCurrency = (amount: number): string => {
  const symbols = { RUB: '₽', USD: '$', EUR: '€' }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.value,
    minimumFractionDigits: 0
  }).format(amount)
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

    const response = await fetch(`/api/v1/admin/analytics/financial?period=${period.value}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `tma ${webAppData}`
      }
    })

    if (!response.ok) {
      throw new Error('Ошибка загрузки данных')
    }

    financialData.value = await response.json()

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
  updateRevenueChart()
  updateTariffRevenueChart()
}

const updateRevenueChart = () => {
  if (!revenueChart.value) {
    console.warn('Revenue chart canvas not found')
    return
  }

  if (revenueChartInstance) {
    revenueChartInstance.destroy()
  }

  const ctx = revenueChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for revenue chart')
    return
  }

  console.log('Creating revenue chart with data:', financialData.value.revenueHistory)

  revenueChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: financialData.value.revenueHistory?.map(item => item.date) || [],
      datasets: [{
        label: 'Доход',
        data: financialData.value.revenueHistory?.map(item => item.revenue) || [],
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
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

const updateTariffRevenueChart = () => {
  if (!tariffRevenueChart.value) {
    console.warn('Tariff revenue chart canvas not found')
    return
  }

  if (tariffRevenueChartInstance) {
    tariffRevenueChartInstance.destroy()
  }

  const ctx = tariffRevenueChart.value.getContext('2d')
  if (!ctx) {
    console.warn('Cannot get 2d context for tariff revenue chart')
    return
  }

  console.log('Creating tariff revenue chart with data:', financialData.value.topTariffs)

  tariffRevenueChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: financialData.value.topTariffs?.map(tariff => tariff.name) || [],
      datasets: [{
        data: financialData.value.topTariffs?.map(tariff => tariff.revenue) || [],
        backgroundColor: ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
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

const exportFinancialData = async () => {
  // Здесь будет логика экспорта финансовых данных
  console.log('Экспорт финансовых данных')
}

onMounted(() => {
  loadData()
})
</script>
