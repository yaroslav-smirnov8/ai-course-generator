<template>
  <div class="relative w-full h-full">
    <!-- Сообщение о пустых данных -->
    <div v-if="!hasData" class="h-full flex flex-col items-center justify-center">
      <div class="text-gray-400 text-center">
        <p class="text-lg mb-2">No data to display</p>
        <p class="text-sm">За выбранный период не было активности</p>
      </div>
    </div>

    <div v-else class="h-72">
      <!-- Переключатель периода -->
      <div class="flex justify-end mb-4">
        <div class="inline-flex rounded-md shadow-sm" role="group">
          <button
            v-for="period in periods"
            :key="period.value"
            type="button"
            class="px-4 py-2 text-sm font-medium border"
            :class="[
              selectedPeriod === period.value
                ? 'bg-purple-600 text-white border-purple-700'
                : 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600',
              period === periods[0] ? 'rounded-l-lg' : '',
              period === periods[periods.length - 1] ? 'rounded-r-lg' : ''
            ]"
            @click="selectedPeriod = period.value"
          >
            {{ period.label }}
          </button>
        </div>
      </div>

      <!-- График -->
      <canvas ref="chartRef"></canvas>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-900/50">
      <div class="flex flex-col items-center gap-2">
        <div class="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
        <div class="text-sm text-gray-400">Загрузка данных...</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

interface ActivityData {
  date: string
  dateKey?: string
  generations: number
  activeUsers: number
}

interface Props {
  data: ActivityData[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const chartRef = ref<HTMLCanvasElement | null>(null)
const chart = ref<Chart | null>(null)

const periods = [
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' },
  { label: 'Year', value: 'year' }
]

const selectedPeriod = ref('week')

const hasData = computed(() => {
  console.log('CHART_DEBUG: Checking if activity chart has data');
  
  // Проверяем, что данные не пустые
  if (!props.data || !Array.isArray(props.data) || props.data.length === 0) {
    console.log('CHART_DEBUG: No data for activity chart');
    return false;
  }
  
  // Проверяем, есть ли хотя бы одна запись с ненулевыми значениями
  const hasActivity = props.data.some(point => {
    if (!point || typeof point !== 'object') return false;
    
    const hasGenerations = point.generations && point.generations > 0;
    const hasActiveUsers = point.activeUsers && point.activeUsers > 0;
    
    return hasGenerations || hasActiveUsers;
  });
  
  console.log('CHART_DEBUG: Has activity:', hasActivity);
  return hasActivity;
})

const filteredData = computed(() => {
  console.log('CHART_DEBUG: Filtering activity data by period:', selectedPeriod.value);
  
  if (!props.data || !Array.isArray(props.data) || props.data.length === 0) {
    console.log('CHART_DEBUG: No data to filter');
    return [];
  }
  
  // Для недели возвращаем все данные (предполагается, что данные уже за неделю)
  if (selectedPeriod.value === 'week') {
    return props.data;
  }
  
  // Для месяца и года нужно фильтровать данные
  // Но так как у нас нет реальных данных за месяц/год, просто возвращаем все данные
  // В реальном приложении здесь должна быть логика фильтрации по дате
  return props.data;
})

const updateChart = () => {
  if (!chartRef.value) {
    console.log('CHART_DEBUG: No chart ref, skipping chart update');
    return;
  }
  
  // Уничтожаем предыдущий график, если он существует
  if (chart.value) {
    console.log('CHART_DEBUG: Destroying existing chart');
    chart.value.destroy();
  }
  
  const data = filteredData.value;
  
  if (data.length === 0) {
    console.log('CHART_DEBUG: No data for chart, skipping chart creation');
    return;
  }
  
  console.log('CHART_DEBUG: Creating chart with data:', data);
  
  // Подготавливаем данные для графика
  const labels = data.map(item => item.date);
  const generationsData = data.map(item => item.generations);
  const usersData = data.map(item => item.activeUsers);
  
  // Создаем новый график
  chart.value = new Chart(chartRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Генерации',
          data: generationsData,
          borderColor: '#8B5CF6', // Violet
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Активные пользователи',
          data: usersData,
          borderColor: '#3B82F6', // Blue
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: '#E5E7EB' // Gray-200
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        },
        x: {
          ticks: {
            color: '#E5E7EB' // Gray-200
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      },
      plugins: {
        legend: {
          labels: {
            color: '#E5E7EB' // Gray-200
          }
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = context.raw as number;
              const label = context.dataset.label || '';
              return `${label}: ${value}`;
            }
          }
        }
      }
    }
  });
}

// Обновляем график при изменении данных или периода
watch([() => props.data, selectedPeriod], updateChart, { deep: true });

// Инициализируем график при монтировании компонента
onMounted(() => {
  console.log('CHART_DEBUG: ActivityChartNew mounted');
  updateChart();
});
</script>
