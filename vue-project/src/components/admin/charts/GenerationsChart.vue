<template>
  <div class="bg-gray-800 rounded-lg p-6">
    <h3 class="text-xl font-semibold text-white mb-4">Generation Statistics</h3>

    <!-- Фильтры для сравнения периодов -->
    <div class="mb-6 flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">Current Period</label>
        <select
          v-model="currentPeriod"
          @change="loadData"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        >
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
        </select>
      </div>

      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-sm mb-1">Compare with</label>
        <select
          v-model="comparisonPeriod"
          @change="loadData"
          class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:border-purple-500"
        >
          <option value="">Don't compare</option>
          <option value="day">Previous day</option>
          <option value="week">Previous week</option>
          <option value="month">Previous month</option>
        </select>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="isLoading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      <p class="mt-2 text-gray-400">Loading data...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
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
      <!-- График по типам генераций -->
      <div class="bg-gray-700 rounded-lg p-4">
        <h4 class="text-lg font-medium text-white mb-2">Distribution by Types</h4>
        <div class="h-64">
          <canvas ref="typeChartRef"></canvas>
        </div>
      </div>

      <!-- График по дням -->
      <div class="bg-gray-700 rounded-lg p-4">
        <h4 class="text-lg font-medium text-white mb-2">Generation Trends</h4>
        <div class="h-64">
          <canvas ref="timeChartRef"></canvas>
        </div>
      </div>

      <!-- Сравнение с предыдущим периодом -->
      <div v-if="comparisonPeriod" class="bg-gray-700 rounded-lg p-4 md:col-span-2">
        <h4 class="text-lg font-medium text-white mb-2">Comparison with Previous Period</h4>
        <div class="h-64">
          <canvas ref="comparisonChartRef"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

// Props
const props = defineProps<{
  initialPeriod?: string,
  generations?: any[],
  generationStats?: any
}>()

// State
const currentPeriod = ref(props.initialPeriod || 'week')
const comparisonPeriod = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const typeChartRef = ref<HTMLCanvasElement | null>(null)
const timeChartRef = ref<HTMLCanvasElement | null>(null)
const comparisonChartRef = ref<HTMLCanvasElement | null>(null)
const typeChart = ref<Chart | null>(null)
const timeChart = ref<Chart | null>(null)
const comparisonChart = ref<Chart | null>(null)
const currentData = ref<any>(null)
const comparisonData = ref<any>(null)

// Загрузка данных
const loadData = async () => {
  console.log('CHART_DEBUG: GenerationsChart - loadData started');
  console.log('CHART_DEBUG: Current period:', currentPeriod.value);
  console.log('CHART_DEBUG: Comparison period:', comparisonPeriod.value);
  console.log('CHART_DEBUG: Props generations:', props.generations);
  console.log('CHART_DEBUG: Props generationStats:', props.generationStats);

  isLoading.value = true
  error.value = null

  try {
    // Проверяем, есть ли переданные данные
    if (props.generationStats) {
      console.log('CHART_DEBUG: Using props.generationStats');

      // Создаем данные для графиков на основе переданных данных
      currentData.value = {
        total_generations: props.generationStats.total_generations || 0,
        generations_by_type: props.generationStats.by_type || {},
        start_date: new Date(new Date().getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 дней назад
        end_date: new Date().toISOString(),
        period: currentPeriod.value
      };

      console.log('CHART_DEBUG: Created currentData from props:', currentData.value);

      // Обновляем графики и завершаем загрузку
      updateCharts();
      isLoading.value = false;
      return;
    }

    // Если нет переданных данных, загружаем из API
    console.log('CHART_DEBUG: No props data, loading from API');

    // Импортируем apiClient
    const { apiClient } = await import('@/api/client')
    console.log('CHART_DEBUG: apiClient imported');

    // Загружаем данные для текущего периода
    console.log('CHART_DEBUG: Fetching data for current period:', currentPeriod.value);
    const currentResponse = await apiClient.get('/api/v1/statistics/generations', {
      params: {
        period: currentPeriod.value
      }
    })

    console.log('CHART_DEBUG: Current period response:', currentResponse);
    console.log('CHART_DEBUG: Current period data:', currentResponse.data);

    currentData.value = currentResponse.data

    // Загружаем данные для сравнения, если выбран период сравнения
    if (comparisonPeriod.value) {
      const comparisonResponse = await apiClient.get('/api/v1/statistics/generations', {
        params: {
          period: comparisonPeriod.value
        }
      })

      comparisonData.value = comparisonResponse.data
    } else {
      comparisonData.value = null
    }

    // Обновляем графики
    updateCharts()
  } catch (e: any) {
    console.error('Error loading generation statistics:', e)
    error.value = `Ошибка загрузки статистики: ${e.message || 'Неизвестная ошибка'}`
  } finally {
    isLoading.value = false
  }
}

// Обновление графиков
const updateCharts = () => {
  console.log('CHART_DEBUG: updateCharts called');

  if (!currentData.value) {
    console.log('CHART_DEBUG: No currentData.value, returning');
    return;
  }

  console.log('CHART_DEBUG: currentData.value:', currentData.value);
  console.log('CHART_DEBUG: currentData.value.generations_by_type:', currentData.value.generations_by_type);
  console.log('CHART_DEBUG: currentData.value.total_generations:', currentData.value.total_generations);

  // Обновляем график по типам
  console.log('CHART_DEBUG: Updating type chart');
  updateTypeChart();

  // Обновляем график по времени
  console.log('CHART_DEBUG: Updating time chart');
  updateTimeChart();

  // Обновляем график сравнения
  if (comparisonData.value) {
    console.log('CHART_DEBUG: Updating comparison chart');
    updateComparisonChart();
  } else {
    console.log('CHART_DEBUG: No comparisonData.value, skipping comparison chart');
  }

  console.log('CHART_DEBUG: All charts updated');
}

// График по типам
const updateTypeChart = () => {
  console.log('CHART_DEBUG: updateTypeChart called');

  if (!typeChartRef.value) {
    console.log('CHART_DEBUG: No typeChartRef.value, returning');
    return;
  }

  console.log('CHART_DEBUG: typeChartRef.value:', typeChartRef.value);

  // Уничтожаем предыдущий график, если он существует
  if (typeChart.value) {
    console.log('CHART_DEBUG: Destroying existing type chart');
    typeChart.value.destroy();
  }

  // Получаем данные для графика
  let byType = currentData.value.generations_by_type || {};
  console.log('CHART_DEBUG: byType from currentData:', byType);

  // Если нет данных в currentData, но есть в props.generationStats
  if (Object.keys(byType).length === 0 && props.generationStats && props.generationStats.by_type) {
    console.log('CHART_DEBUG: Using byType from props.generationStats');
    byType = props.generationStats.by_type;
  }

  // Если все еще нет данных, но есть props.generations, создаем данные из них
  if (Object.keys(byType).length === 0 && props.generations && props.generations.length > 0) {
    console.log('CHART_DEBUG: Creating byType from props.generations');

    // Группируем генерации по типам
    props.generations.forEach(gen => {
      if (gen.type) {
        byType[gen.type] = (byType[gen.type] || 0) + 1;
      }
    });
  }

  console.log('CHART_DEBUG: Final byType:', byType);

  const labels = Object.keys(byType).map(key =>
    key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  );
  console.log('CHART_DEBUG: labels:', labels);

  const data = Object.values(byType);
  console.log('CHART_DEBUG: data:', data);

  // Проверяем, есть ли данные для отображения
  if (labels.length === 0 || data.length === 0) {
    console.log('CHART_DEBUG: No data for type chart, using default data');
    // Создаем заглушку с нулевыми значениями
    labels.push('Нет данных');
    data.push(0);
  }

  // Создаем новый график
  typeChart.value = new Chart(typeChartRef.value, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: [
          '#4F46E5', // Indigo
          '#10B981', // Emerald
          '#F59E0B', // Amber
          '#EF4444', // Red
          '#8B5CF6', // Violet
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

// Функция для получения данных временного ряда
const getTimeSeriesData = () => {
  if (!currentData.value && !props.generations) {
    console.log('CHART_DEBUG: No data for time series');
    return { labels: [], data: [] }
  }

  console.log('CHART_DEBUG: Getting time series data');

  // Проверяем, есть ли данные в props.generations
  if (props.generations && props.generations.length > 0) {
    console.log('CHART_DEBUG: Creating time series from props.generations');

    // Группируем генерации по дням
    const generationsByDay = new Map();

    // Определяем диапазон дат
    // Сначала найдем минимальную и максимальную даты в генерациях
    let minDate = new Date();
    let maxDate = new Date(0); // Начало эпохи

    console.log('CHART_DEBUG: Finding min and max dates in generations');

    props.generations.forEach(gen => {
      try {
        const genDate = new Date(gen.created_at);
        if (genDate < minDate) {
          minDate = genDate;
        }
        if (genDate > maxDate) {
          maxDate = genDate;
        }
      } catch (e) {
        console.error('CHART_DEBUG: Error processing date for min/max:', e);
      }
    });

    console.log('CHART_DEBUG: Min date found:', minDate);
    console.log('CHART_DEBUG: Max date found:', maxDate);

    // Если нет генераций или даты некорректны, используем последние 7 дней
    if (minDate > maxDate || props.generations.length === 0) {
      console.log('CHART_DEBUG: Using default date range (last 7 days)');
      maxDate = new Date();
      minDate = new Date();
      minDate.setDate(maxDate.getDate() - 6); // 7 дней включая сегодня
    } else {
      // Расширяем диапазон на 1 день в обе стороны для лучшего отображения
      minDate.setDate(minDate.getDate() - 1);
      maxDate.setDate(maxDate.getDate() + 1);
    }

    // Убедимся, что диапазон не слишком большой (максимум 30 дней)
    const daysDiff = Math.floor((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24));
    if (daysDiff > 30) {
      console.log('CHART_DEBUG: Date range too large, limiting to 30 days');
      minDate = new Date(maxDate);
      minDate.setDate(maxDate.getDate() - 29); // 30 дней включая последний
    }

    console.log('CHART_DEBUG: Final date range:', { minDate, maxDate, daysDiff });

    // Инициализируем все дни нулевыми значениями
    const currentDate = new Date(minDate);
    while (currentDate <= maxDate) {
      const dateKey = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD
      generationsByDay.set(dateKey, 0);

      // Переходим к следующему дню
      currentDate.setDate(currentDate.getDate() + 1);
    }

    console.log('CHART_DEBUG: Initialized days:', Array.from(generationsByDay.keys()));

    // Подсчитываем генерации по дням
    console.log('CHART_DEBUG: Processing generations for time series:', props.generations);

    props.generations.forEach(gen => {
      try {
        console.log('CHART_DEBUG: Processing generation:', gen);
        console.log('CHART_DEBUG: Generation created_at:', gen.created_at);

        const genDate = new Date(gen.created_at);
        console.log('CHART_DEBUG: Parsed date:', genDate);

        const dateKey = genDate.toISOString().split('T')[0]; // YYYY-MM-DD
        console.log('CHART_DEBUG: Date key:', dateKey);

        // Проверяем, что дата входит в диапазон
        if (generationsByDay.has(dateKey)) {
          console.log('CHART_DEBUG: Date is in range, incrementing count');
          generationsByDay.set(dateKey, generationsByDay.get(dateKey) + 1);
        } else {
          console.log('CHART_DEBUG: Date is not in range:', dateKey);
          console.log('CHART_DEBUG: Available date keys:', Array.from(generationsByDay.keys()));
        }
      } catch (e) {
        console.error('CHART_DEBUG: Error processing generation date:', e, gen);
      }
    });

    console.log('CHART_DEBUG: Final generations by day:', Object.fromEntries(generationsByDay));

    // Создаем массивы для графика
    const labels = [];
    const data = [];

    // Сортируем даты
    const sortedDates = Array.from(generationsByDay.keys()).sort();

    // Заполняем массивы
    sortedDates.forEach(dateKey => {
      const date = new Date(dateKey);
      labels.push(date.toLocaleDateString());
      data.push(generationsByDay.get(dateKey));
    });

    console.log('CHART_DEBUG: Created time series from generations:', { labels, data });
    return { labels, data };
  }

  // Если нет данных в props.generations, проверяем наличие time_series в ответе
  if (currentData.value && currentData.value.time_series) {
    // Если есть time_series, используем его
    const timeData = currentData.value.time_series || []
    const labels = timeData.map((item: any) => new Date(item.date).toLocaleDateString())
    const data = timeData.map((item: any) => item.count)
    console.log('CHART_DEBUG: Using time_series data:', { labels, data });
    return { labels, data }
  } else {
    // Если time_series отсутствует, создаем временной ряд на основе общего количества
    // и периода (начальная и конечная даты)
    const startDate = new Date(currentData.value?.start_date || new Date(new Date().getTime() - 7 * 24 * 60 * 60 * 1000))
    const endDate = new Date(currentData.value?.end_date || new Date())
    const totalGenerations = currentData.value?.total_generations ||
                            (props.generationStats?.total_generations || 0)

    // Создаем несколько точек данных для более информативного графика
    const labels = [];
    const data = [];

    // Определяем количество дней между датами
    const daysDiff = Math.max(1, Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)));
    console.log('CHART_DEBUG: Days difference:', daysDiff);

    // Если у нас есть данные о типах генераций, используем их для распределения по дням
    const byType = currentData.value?.generations_by_type || props.generationStats?.by_type || {};

    if (Object.keys(byType).length > 0) {
      const totalByType = Object.values(byType).reduce((sum: number, val: any) => sum + (val || 0), 0);

      // Создаем точки данных для каждого дня
      for (let i = 0; i < daysDiff; i++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + i);
        labels.push(date.toLocaleDateString());

        // Распределяем генерации по дням (простое равномерное распределение)
        const dailyCount = Math.round(totalGenerations / daysDiff);
        data.push(dailyCount);
      }
    } else {
      // Если нет данных о типах, просто создаем одну точку
      labels.push(startDate.toLocaleDateString());
      data.push(totalGenerations);
    }

    console.log('CHART_DEBUG: Created time series data from total:', { labels, data });
    return { labels, data }
  }
}

// График по времени
const updateTimeChart = () => {
  if (!timeChartRef.value) return

  // Уничтожаем предыдущий график, если он существует
  if (timeChart.value) {
    timeChart.value.destroy()
  }

  // Получаем данные для графика
  const timeData = getTimeSeriesData()

  // Создаем новый график
  timeChart.value = new Chart(timeChartRef.value, {
    type: 'line',
    data: {
      labels: timeData.labels,
      datasets: [{
        label: 'Количество генераций',
        data: timeData.data,
        borderColor: '#8B5CF6', // Violet
        backgroundColor: 'rgba(139, 92, 246, 0.2)',
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#E5E7EB' // Gray-200
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#9CA3AF' // Gray-400
          },
          grid: {
            color: 'rgba(75, 85, 99, 0.2)' // Gray-600 with opacity
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: '#9CA3AF' // Gray-400
          },
          grid: {
            color: 'rgba(75, 85, 99, 0.2)' // Gray-600 with opacity
          }
        }
      }
    }
  })
}

// График сравнения
const updateComparisonChart = () => {
  if (!comparisonChartRef.value || !comparisonData.value) return

  // Уничтожаем предыдущий график, если он существует
  if (comparisonChart.value) {
    comparisonChart.value.destroy()
  }

  // Получаем данные для графика
  const currentByType = currentData.value.generations_by_type || {}
  const comparisonByType = comparisonData.value.generations_by_type || {}

  console.log('Comparison chart data:', {
    currentByType,
    comparisonByType,
    currentPeriod: currentPeriod.value,
    comparisonPeriod: comparisonPeriod.value
  })

  // Объединяем ключи из обоих периодов
  const allTypes = [...new Set([...Object.keys(currentByType), ...Object.keys(comparisonByType)])]

  // Форматируем метки
  const labels = allTypes.map(key =>
    key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  )

  // Получаем данные для текущего периода
  const currentValues = allTypes.map(type => currentByType[type] || 0)

  // Получаем данные для периода сравнения
  const comparisonValues = allTypes.map(type => comparisonByType[type] || 0)

  console.log('Comparison chart prepared data:', {
    labels,
    currentValues,
    comparisonValues
  })

  // Создаем новый график
  comparisonChart.value = new Chart(comparisonChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Current Period',
          data: currentValues,
          backgroundColor: '#8B5CF6', // Violet
          borderColor: '#7C3AED',
          borderWidth: 1
        },
        {
          label: 'Previous Period',
          data: comparisonValues,
          backgroundColor: '#10B981', // Emerald
          borderColor: '#059669',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#E5E7EB' // Gray-200
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#9CA3AF' // Gray-400
          },
          grid: {
            color: 'rgba(75, 85, 99, 0.2)' // Gray-600 with opacity
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: '#9CA3AF' // Gray-400
          },
          grid: {
            color: 'rgba(75, 85, 99, 0.2)' // Gray-600 with opacity
          }
        }
      }
    }
  })
}

// Загружаем данные при монтировании компонента
onMounted(() => {
  loadData()
})

// Следим за изменением периодов
watch([currentPeriod, comparisonPeriod], () => {
  loadData()
})
</script>
