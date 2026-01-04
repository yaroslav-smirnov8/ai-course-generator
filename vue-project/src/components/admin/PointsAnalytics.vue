<template>
  <div class="space-y-6">
    <!-- Сообщение о недоступности API -->
    <div v-if="apiNotAvailable" class="bg-amber-500/20 text-amber-300 p-6 rounded-lg">
      <h3 class="text-lg font-medium mb-2">Points analytics API is under development</h3>
      <p class="mb-4">
        Endpoint <code>/api/v1/admin/points/operations</code> not found on server.
        To fully operate this section, the corresponding API needs to be implemented on the backend.
      </p>
      <p class="text-sm mb-4">
        This section is designed for analyzing user points usage:
        <ul class="list-disc pl-5 mt-2">
          <li>Which tariffs users purchase points on</li>
          <li>What points are spent on (content types)</li>
          <li>Points purchase and usage statistics</li>
          <li>Points operations history</li>
        </ul>
      </p>
      <button
        @click="loadData"
        class="mt-4 px-4 py-2 bg-amber-500/30 hover:bg-amber-500/50 rounded-lg text-white"
      >
        Check API availability
      </button>
    </div>

    <div v-else>
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
              <option value="all">All time</option>
            </select>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">Operation Type</label>
            <select
              v-model="operationType"
              class="bg-gray-700 text-white rounded-lg px-4 py-2 w-40"
            >
              <option value="all">All operations</option>
              <option value="purchase">Points purchase</option>
              <option value="usage">Points usage</option>
            </select>
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">Tariff</label>
            <select
              v-model="tariffFilter"
              class="bg-gray-700 text-white rounded-lg px-4 py-2 w-40"
            >
              <option value="all">All tariffs</option>
              <option value="none">No tariff</option>
              <option value="basic">Basic</option>
              <option value="tariff_2">Standard</option>
              <option value="tariff_4">Premium</option>
              <option value="tariff_6">VIP</option>
            </select>
          </div>

          <button
            @click="loadData"
            class="bg-purple-500 text-white rounded-lg px-4 py-2 mt-6"
          >
            Apply filters
          </button>
        </div>
      </div>

      <!-- Статистика -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-gray-800 rounded-lg p-6">
          <h3 class="text-lg font-medium text-white mb-2">Total points purchased</h3>
          <p class="text-3xl font-bold text-purple-500">{{ totalPointsPurchased }}</p>
        </div>

        <div class="bg-gray-800 rounded-lg p-6">
          <h3 class="text-lg font-medium text-white mb-2">Total points used</h3>
          <p class="text-3xl font-bold text-blue-500">{{ totalPointsUsed }}</p>
        </div>

        <div class="bg-gray-800 rounded-lg p-6">
          <h3 class="text-lg font-medium text-white mb-2">Active users</h3>
          <p class="text-3xl font-bold text-green-500">{{ uniqueUsers }}</p>
        </div>

        <div class="bg-gray-800 rounded-lg p-6">
          <h3 class="text-lg font-medium text-white mb-2">Average spending per user</h3>
          <p class="text-3xl font-bold text-amber-500">{{ averagePointsPerUser }}</p>
        </div>
      </div>

      <!-- Графики -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- График покупки баллов по тарифам -->
        <div class="bg-gray-800 rounded-lg p-6">
          <h3 class="text-lg font-medium text-white mb-4">Points purchase by tariff</h3>
          <div class="h-64">
            <canvas ref="purchaseByTariffChart"></canvas>
          </div>
        </div>

        <!-- График использования баллов по типам контента -->
        <div class="bg-gray-800 rounded-lg p-6">
          <h3 class="text-lg font-medium text-white mb-4">Points usage by content type</h3>
          <div class="h-64">
            <canvas ref="usageByTypeChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Таблица операций с баллами -->
      <div class="bg-gray-800 rounded-lg p-6">
        <h3 class="text-lg font-medium text-white mb-4">Points operations history</h3>

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

        <div v-else-if="!pointsOperations.length" class="text-center py-8">
          <p class="text-gray-400">No data to display</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left">
            <thead class="bg-gray-900">
              <tr>
                <th class="p-4">ID</th>
                <th class="p-4">User Name</th>
                <th class="p-4">Username</th>
                <th class="p-4">Tariff</th>
                <th class="p-4">Operation Type</th>
                <th class="p-4">Points Amount</th>
                <th class="p-4">Content Type</th>
                <th class="p-4">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="operation in pointsOperations"
                :key="operation.id"
                class="border-t border-gray-700 hover:bg-gray-700/50"
              >
                <td class="p-4">{{ operation.id }}</td>
                <td class="p-4">{{ operation.user_name || `User ${operation.user_id}` }}</td>
                <td class="p-4">
                  <span v-if="operation.username" class="text-gray-300">
                    @{{ operation.username }}
                  </span>
                  <span v-else class="text-gray-500">-</span>
                </td>
                <td class="p-4">
                  <span
                    v-if="operation.tariff"
                    class="px-2 py-1 rounded-full text-xs bg-blue-500/20 text-blue-300"
                  >
                    {{ formatTariff(operation.tariff) }}
                  </span>
                  <span v-else class="text-gray-500">-</span>
                </td>
                <td class="p-4">
                  <span
                    class="px-2 py-1 rounded-full text-xs"
                    :class="operation.type === 'purchase'
                      ? 'bg-green-500/20 text-green-300'
                      : 'bg-amber-500/20 text-amber-300'"
                  >
                    {{ operation.type === 'purchase' ? 'Purchase' : 'Usage' }}
                  </span>
                </td>
                <td class="p-4">{{ operation.points }}</td>
                <td class="p-4">{{ operation.content_type ? formatContentType(operation.content_type) : '-' }}</td>
                <td class="p-4">{{ formatDate(operation.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Пагинация -->
        <div class="flex justify-between items-center mt-4">
          <div class="text-sm text-gray-400">
            Showing {{ pointsOperations.length }} of {{ totalOperations }} operations
          </div>
          <div class="flex gap-2">
            <button
              @click="prevPage"
              :disabled="currentPage === 1"
              class="px-3 py-1 rounded-lg bg-gray-700 text-gray-300 disabled:opacity-50"
            >
              Back
            </button>
            <span class="px-3 py-1 text-gray-300">{{ currentPage }} / {{ totalPages }}</span>
            <button
              @click="nextPage"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 rounded-lg bg-gray-700 text-gray-300 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useMainStore } from '@/store'
import Chart from 'chart.js/auto'

const store = useMainStore()

// State
const period = ref('week')
const operationType = ref('all')
const tariffFilter = ref('all')
const isLoading = ref(false)
const error = ref<string | null>(null)
const pointsOperations = ref<any[]>([])
const totalOperations = ref(0)
const currentPage = ref(1)
const itemsPerPage = ref(10)
const apiNotAvailable = ref(false)
const usersWithPoints = ref<any[]>([])
const pointsStats = ref<any>(null)

// Chart refs
const purchaseByTariffChart = ref<HTMLCanvasElement | null>(null)
const usageByTypeChart = ref<HTMLCanvasElement | null>(null)
const purchaseChart = ref<Chart | null>(null)
const usageChart = ref<Chart | null>(null)

// Computed
const totalPages = computed(() => Math.ceil(totalOperations.value / itemsPerPage.value))
const totalPointsPurchased = computed(() => {
  // Если есть статистика в ответе API, используем ее
  if (pointsStats.value && pointsStats.value.total_purchased !== undefined) {
    return pointsStats.value.total_purchased;
  }

  // Иначе считаем из операций
  return pointsOperations.value
    .filter(op => op.type === 'purchase')
    .reduce((sum, op) => sum + op.points, 0)
})
const totalPointsUsed = computed(() => {
  // Если есть статистика в ответе API, используем ее
  if (pointsStats.value && pointsStats.value.total_used !== undefined) {
    return pointsStats.value.total_used;
  }

  // Иначе считаем из операций
  return pointsOperations.value
    .filter(op => op.type === 'usage')
    .reduce((sum, op) => sum + op.points, 0)
})
const uniqueUsers = computed(() => {
  const userIds = new Set(pointsOperations.value.map(op => op.user_id))
  return userIds.size
})
const averagePointsPerUser = computed(() => {
  if (uniqueUsers.value === 0) return 0
  return Math.round(totalPointsUsed.value / uniqueUsers.value)
})

// Methods
const checkApiAvailability = async () => {
  isLoading.value = true
  error.value = null

  try {
    console.log('Checking points API availability...')

    // Пробуем получить данные с минимальными параметрами
    const response = await store.getPointsOperations({
      page: 1,
      limit: 1,
      period: 'week'
    })

    console.log('API check response:', response)

    // Если получили ответ с items, значит API работает
    if (response && response.items) {
      apiNotAvailable.value = false

      // Загружаем данные с полными параметрами
      await loadData()
    } else {
      console.error('API check failed: Invalid response format')
      apiNotAvailable.value = true
      error.value = 'API не вернуло данные в ожидаемом формате'
    }
  } catch (err: any) {
    console.error('API check error:', err)

    // Проверяем, является ли ошибка 404 (API не найден)
    if (err.response && err.response.status === 404) {
      apiNotAvailable.value = true
      error.value = 'Points analytics API is not implemented on the server (404 Not Found)'
    } else {
      apiNotAvailable.value = true
      error.value = err.message || 'Error checking API availability'
    }
  } finally {
    isLoading.value = false
  }
}

const loadData = async () => {
  // Если API недоступно, не пытаемся загрузить данные
  if (apiNotAvailable.value) {
    return
  }

  isLoading.value = true
  error.value = null

  try {
    console.log('Loading points operations data...')

    // Параметры запроса
    const params: Record<string, any> = {
      page: currentPage.value,
      limit: itemsPerPage.value,
      period: period.value
    }

    // Добавляем фильтры, если они выбраны
    if (operationType.value !== 'all') {
      params.operation_type = operationType.value
    }

    if (tariffFilter.value !== 'all') {
      params.tariff = tariffFilter.value === 'none' ? null : tariffFilter.value
    }

    // Получаем данные об операциях с баллами
    const response = await store.getPointsOperations(params)

    console.log('Points operations response:', response)

    if (response && response.items) {
      console.log('Response data:', response);

      pointsOperations.value = response.items;
      totalOperations.value = response.total || response.items.length;

      // Сохраняем статистику, если она есть
      if (response.stats) {
        console.log('Setting pointsStats from response:', response.stats);
        pointsStats.value = response.stats;
      } else {
        console.log('No stats in response, calculating from items');
        pointsStats.value = null;
      }

      // Обновляем графики
      updateCharts();
    } else {
      console.error('Invalid response format:', response);
      error.value = 'Некорректный формат ответа от сервера';
    }
  } catch (err: any) {
    console.error('Error loading points data:', err)

    // Проверяем, является ли ошибка 404 (API не найден)
    if (err.response && err.response.status === 404) {
      apiNotAvailable.value = true
      error.value = 'Points analytics API is not implemented on the server (404 Not Found)'
    } else {
      error.value = err.message || 'Error loading data'
    }

    // Если API еще не реализовано, используем пустой массив
    pointsOperations.value = []
    totalOperations.value = 0
  } finally {
    isLoading.value = false
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadData()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadData()
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTariff = (tariff: string) => {
  const tariffMap: Record<string, string> = {
    'basic': 'Basic',
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
    'free_query': 'AI Assistant'
  }
  return typeMap[type] || type
}

const updateCharts = () => {
  updatePurchaseByTariffChart()
  updateUsageByTypeChart()
}

const updatePurchaseByTariffChart = () => {
  if (!purchaseByTariffChart.value) return

  // Уничтожаем предыдущий график, если он существует
  if (purchaseChart.value) {
    purchaseChart.value.destroy()
  }

  // Группируем данные по тарифам
  let tariffData: Record<string, number> = {}

  // Если есть статистика в ответе API, используем ее
  if (pointsStats.value && pointsStats.value.by_tariff) {
    console.log('Using stats.by_tariff for chart:', pointsStats.value.by_tariff);
    tariffData = pointsStats.value.by_tariff;
  } else {
    // Иначе считаем из операций
    console.log('Calculating tariff data from operations');
    pointsOperations.value
      .filter(op => op.type === 'purchase')
      .forEach(op => {
        const tariff = op.tariff || 'none'
        tariffData[tariff] = (tariffData[tariff] || 0) + op.points
      });
  }

  // Подготавливаем данные для графика
  const labels = Object.keys(tariffData).map(tariff => formatTariff(tariff))
  const data = Object.values(tariffData)

  console.log('Tariff chart data:', { labels, data });

  // Создаем новый график
  purchaseChart.value = new Chart(purchaseByTariffChart.value, {
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
          '#EF4444'  // Red
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
}

const updateUsageByTypeChart = () => {
  if (!usageByTypeChart.value) return

  // Уничтожаем предыдущий график, если он существует
  if (usageChart.value) {
    usageChart.value.destroy()
  }

  // Группируем данные по типам контента
  let typeData: Record<string, number> = {}

  // Если есть статистика в ответе API, используем ее
  if (pointsStats.value && pointsStats.value.by_content_type) {
    console.log('Using stats.by_content_type for chart:', pointsStats.value.by_content_type);
    typeData = pointsStats.value.by_content_type;
  } else {
    // Иначе считаем из операций
    console.log('Calculating content type data from operations');
    pointsOperations.value
      .filter(op => op.type === 'usage')
      .forEach(op => {
        if (op.content_type) {
          typeData[op.content_type] = (typeData[op.content_type] || 0) + op.points
        }
      });
  }

  // Подготавливаем данные для графика
  const labels = Object.keys(typeData).map(type => formatContentType(type))
  const data = Object.values(typeData)

  console.log('Content type chart data:', { labels, data });

  // Создаем новый график
  usageChart.value = new Chart(usageByTypeChart.value, {
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
}

// Обработка ошибок API
const handleApiError = (error: any) => {
  console.error('API Error:', error)

  if (error.response) {
    // Ошибка от сервера с ответом
    const status = error.response.status
    const data = error.response.data

    if (status === 404) {
      return 'API endpoint не найден. Возможно, функциональность еще не реализована на сервере.'
    } else if (status === 401) {
      return 'Ошибка авторизации. Пожалуйста, войдите в систему снова.'
    } else if (data && data.detail) {
      return `Ошибка сервера: ${data.detail}`
    }
  }

  return error.message || 'Неизвестная ошибка при загрузке данных'
}

// Загрузка пользователей с баллами
const loadUsersWithPoints = async () => {
  try {
    console.log('Loading users with points...');

    // Получаем список всех пользователей
    const users = await store.getUsers();

    console.log('Users response:', users);

    // Фильтруем пользователей с баллами
    usersWithPoints.value = users
      .filter((user: any) => user.points && user.points > 0)
      .sort((a: any, b: any) => b.points - a.points);

    console.log('Users with points:', usersWithPoints.value);
  } catch (err: any) {
    console.error('Error loading users with points:', err);
    error.value = err.message || 'Error loading user data';
  }
};

// Lifecycle hooks
onMounted(() => {
  // Проверяем доступность API при загрузке компонента
  checkApiAvailability();

  // Загружаем пользователей с баллами
  loadUsersWithPoints();
})
</script>
