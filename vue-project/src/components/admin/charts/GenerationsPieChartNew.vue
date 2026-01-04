<template>
  <div class="relative w-full h-full">
    <!-- Сообщение о пустых данных -->
    <div v-if="!hasData" class="h-full flex flex-col items-center justify-center">
      <div class="text-gray-400 text-center">
        <p class="text-lg mb-2">Нет данных для отображения</p>
        <p class="text-sm">За выбранный период не было генераций</p>
      </div>
    </div>

    <div v-else class="h-64">
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

interface ChartData {
  name: string
  value: number
}

interface Props {
  data: ChartData[]
  loading?: boolean
  colors?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  colors: () => [
    '#8B5CF6', // Violet
    '#3B82F6', // Blue
    '#10B981', // Emerald
    '#F59E0B', // Amber
    '#EF4444', // Red
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#F97316'  // Orange
  ]
})

const chartRef = ref<HTMLCanvasElement | null>(null)
const chart = ref<Chart | null>(null)

const nameMap = {
  lesson_plan: 'Lesson Plans',
  exercise: 'Exercises',
  game: 'Games',
  image: 'Images',
  text_analysis: 'Text Analysis',
  concept_explanation: 'Concept Explanations',
  course: 'Courses',
  ai_assistant: 'AI Assistant',
  transcript: 'Transcripts'
} as const

const formatName = (name: string): string => {
  console.log('CHART_DEBUG: formatName called with:', name);
  
  if (!name || typeof name !== 'string') {
    console.error('CHART_DEBUG: Invalid name passed to formatName:', name);
    return 'Неизвестный тип';
  }
  
  const formattedName = nameMap[name as keyof typeof nameMap] || name;
  console.log('CHART_DEBUG: Formatted name:', formattedName);
  return formattedName;
}

const hasData = computed(() => {
  console.log('CHART_DEBUG: Checking if pie chart has data');
  
  // Проверяем, что данные не пустые
  if (!props.data || !Array.isArray(props.data) || props.data.length === 0) {
    console.log('CHART_DEBUG: No data for pie chart');
    return false;
  }
  
  // Проверяем, есть ли хотя бы одно ненулевое значение
  const hasNonZeroValue = props.data.some(item => {
    if (!item || typeof item !== 'object') return false;
    return item.value > 0;
  });
  
  console.log('CHART_DEBUG: Has non-zero values:', hasNonZeroValue);
  return hasNonZeroValue;
})

const chartData = computed(() => {
  console.log('CHART_DEBUG: Computing pie chart data');
  
  // Проверяем, что данные не пустые
  if (!props.data || !Array.isArray(props.data) || props.data.length === 0) {
    console.log('CHART_DEBUG: No data for pie chart, using default data');
    return [];
  }
  
  // Проверяем, что все элементы имеют правильную структуру
  const validData = props.data.filter(item => {
    if (!item || typeof item !== 'object') {
      console.error('CHART_DEBUG: Invalid data item:', item);
      return false;
    }
    
    if (typeof item.name !== 'string') {
      console.error('CHART_DEBUG: Item has invalid name:', item);
      return false;
    }
    
    if (typeof item.value !== 'number') {
      console.error('CHART_DEBUG: Item has invalid value:', item);
      return false;
    }
    
    return true;
  });
  
  console.log('CHART_DEBUG: Valid pie chart data:', validData);
  
  // Фильтруем только ненулевые значения
  const nonZeroData = validData.filter(item => item.value > 0);
  console.log('CHART_DEBUG: Non-zero pie chart data:', nonZeroData);
  
  return nonZeroData;
})

const totalGenerations = computed(() => {
  try {
    if (!props.data || props.data.length === 0) {
      console.log('CHART_DEBUG: No data for calculating total generations');
      return 0;
    }
    
    const total = props.data.reduce((sum, entry) => sum + entry.value, 0);
    console.log('CHART_DEBUG: Total generations calculated:', total);
    return total;
  } catch (error) {
    console.error('CHART_DEBUG: Error calculating total generations:', error);
    return 0;
  }
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
  
  const data = chartData.value;
  
  if (data.length === 0) {
    console.log('CHART_DEBUG: No data for chart, skipping chart creation');
    return;
  }
  
  console.log('CHART_DEBUG: Creating chart with data:', data);
  
  // Подготавливаем данные для графика
  const labels = data.map(item => formatName(item.name));
  const values = data.map(item => item.value);
  
  // Создаем новый график
  chart.value = new Chart(chartRef.value, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: props.colors.slice(0, data.length),
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
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = context.raw as number;
              const percent = ((value / totalGenerations.value) * 100).toFixed(1);
              return `${context.label}: ${value} (${percent}%)`;
            }
          }
        }
      }
    }
  });
}

// Обновляем график при изменении данных
watch(() => props.data, updateChart, { deep: true });

// Инициализируем график при монтировании компонента
onMounted(() => {
  console.log('CHART_DEBUG: GenerationsPieChartNew mounted');
  updateChart();
});
</script>
