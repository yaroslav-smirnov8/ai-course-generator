<template>
  <div class="admin-card">
    <div class="admin-card-header">
      <h3 class="admin-card-title">Promocode Statistics</h3>
      <!-- Фильтры по периоду -->
      <div class="flex items-center gap-4">
        <select
          v-model="period"
          class="bg-gray-700 text-white rounded-lg px-4 py-2"
          @change="loadStats"
        >
          <option value="week">Week</option>
          <option value="month">Month</option>
          <option value="year">Year</option>
          <option value="all">All Time</option>
        </select>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="mt-6 text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Загрузка статистики...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="mt-6 bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
      <p>{{ error }}</p>
      <button
        @click="loadStats"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Попробовать снова
      </button>
    </div>

    <template v-else>
      <!-- Общая статистика -->
      <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="p-4 bg-gray-700/50 rounded-lg">
          <p class="text-gray-400 text-sm">Всего активаций</p>
          <p class="text-2xl font-bold text-white mt-1">
            {{ totalStats.activations || 0 }}
          </p>
        </div>
        <div class="p-4 bg-gray-700/50 rounded-lg">
          <p class="text-gray-400 text-sm">Уникальных пользователей</p>
          <p class="text-2xl font-bold text-white mt-1">
            {{ totalStats.unique_users || 0 }}
          </p>
        </div>
        <div class="p-4 bg-gray-700/50 rounded-lg">
          <p class="text-gray-400 text-sm">Средняя конверсия</p>
          <p class="text-2xl font-bold text-white mt-1">
            {{ totalStats.avg_conversion || 0 }}%
          </p>
        </div>
      </div>

      <!-- Таблица статистики по промокодам -->
      <div class="mt-6">
        <!-- Empty state -->
        <div v-if="!promoStats.length" class="text-center py-8 bg-gray-800 rounded-lg">
          <p class="text-gray-400">Нет данных о промокодах за выбранный период</p>
        </div>

        <table v-else class="w-full">
          <thead class="bg-gray-900">
          <tr>
            <th class="p-4 text-left text-gray-400">Промокод</th>
            <th class="p-4 text-left text-gray-400">Активаций</th>
            <th class="p-4 text-left text-gray-400">Уник. пользователей</th>
            <th class="p-4 text-left text-gray-400">Последнее использование</th>
            <th class="p-4 text-left text-gray-400">Конверсия</th>
            <th class="p-4 text-left text-gray-400">Тариф</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="stat in promoStats"
              :key="stat.code"
              class="border-t border-gray-700">
            <td class="p-4 font-mono">{{ stat.code }}</td>
            <td class="p-4">{{ stat.total_activations }}</td>
            <td class="p-4">{{ stat.unique_users }}</td>
            <td class="p-4">{{ formatDate(stat.last_used) }}</td>
            <td class="p-4">
               <span
                 class="px-2 py-1 rounded-full text-xs"
                 :class="getConversionClass(stat.conversion_rate)"
               >
                 {{ stat.conversion_rate }}%
               </span>
            </td>
            <td class="p-4">{{ formatTariff(stat.tariff_type) }}</td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- График использования -->
      <div v-if="chartData.length > 0" class="mt-6 h-80">
        <LineChart
          :data="chartData"
          :margin="{ top: 20, right: 20, bottom: 20, left: 40 }"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" />
          <Tooltip
            :contentStyle="{
              backgroundColor: '#1F2937',
              border: 'none',
              borderRadius: '0.5rem',
              color: '#F3F4F6'
            }"
          />
          <Line
            type="monotone"
            dataKey="activations"
            stroke="#8B5CF6"
            name="Активации"
          />
        </LineChart>
      </div>

      <!-- No chart data state -->
      <div v-else class="mt-6 text-center py-8 bg-gray-800 rounded-lg">
        <p class="text-gray-400">Нет данных для построения графика за выбранный период</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMainStore } from '../../../store'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

// Define interfaces for our data types
interface PromocodeStat {
  code: string;
  total_activations: number;
  unique_users: number;
  last_used: string;
  conversion_rate: number;
  tariff_type: string;  // Add this property
}

interface TotalStats {
  activations: number;
  unique_users: number;
  avg_conversion: number;
}

interface ChartDataPoint {
  date: string;
  activations: number;
}

const store = useMainStore()

// UI state
const period = ref('month')
const isLoading = ref(false)
const error = ref<string | null>(null)

// Data
const promoStats = ref<PromocodeStat[]>([])
const chartData = ref<ChartDataPoint[]>([])
const totalStats = ref<TotalStats>({
  activations: 0,
  unique_users: 0,
  avg_conversion: 0
})

const formatDate = (date: string | null) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString()
}

const formatTariff = (tariffType: string) => {
  const tariffs: Record<string, string> = {
    'tariff_2': 'Basic',
    'tariff_4': 'Standard',
    'tariff_6': 'Premium'
  }
  return tariffs[tariffType] || tariffType
}

const getConversionClass = (rate: number) => {
  if (rate >= 75) return 'bg-green-500/20 text-green-300'
  if (rate >= 50) return 'bg-blue-500/20 text-blue-300'
  if (rate >= 25) return 'bg-yellow-500/20 text-yellow-300'
  return 'bg-red-500/20 text-red-300'
}

const loadStats = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await store.getPromocodesStats(period.value);

    if (response && typeof response === 'object') {
      // Обработка статистики по промокодам
      if (response.stats && Array.isArray(response.stats)) {
        promoStats.value = response.stats;
        console.log('Successfully loaded promocodes stats:', response.stats.length);
      } else {
        console.warn('No stats array in response:', response);
        promoStats.value = [];
      }

      // Обработка данных для графика
      if (response.chart_data && Array.isArray(response.chart_data)) {
        chartData.value = response.chart_data;
        console.log('Successfully loaded chart data:', response.chart_data.length);
      } else {
        console.warn('No chart_data array in response:', response);
        chartData.value = [];
      }

      // Обработка общей статистики
      if (response.total_stats && typeof response.total_stats === 'object') {
        totalStats.value = response.total_stats;
        console.log('Successfully loaded total stats');
      } else {
        console.warn('No total_stats object in response:', response);
        totalStats.value = {
          activations: 0,
          unique_users: 0,
          avg_conversion: 0
        };
      }
    } else {
      console.error('Unexpected promocodes stats response structure:', response);
      error.value = 'Неожиданная структура ответа от API';

      // Сбрасываем данные
      promoStats.value = [];
      chartData.value = [];
      totalStats.value = {
        activations: 0,
        unique_users: 0,
        avg_conversion: 0
      };
    }
  } catch (err: any) {
    console.error('Error loading promocodes stats:', err);
    error.value = `Ошибка при загрузке статистики промокодов: ${err.message || 'Неизвестная ошибка'}`;

    // Сбрасываем данные
    promoStats.value = [];
    chartData.value = [];
    totalStats.value = {
      activations: 0,
      unique_users: 0,
      avg_conversion: 0
    };
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  loadStats()
})
</script>
