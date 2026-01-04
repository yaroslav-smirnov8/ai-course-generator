<!-- src/components/charts/GenerationsPieChart.vue -->
<template>
  <div class="relative w-full h-full">
    <!-- Сообщение о пустых данных -->
    <div v-if="!hasData" class="h-full flex flex-col items-center justify-center">
      <div class="text-gray-400 text-center">
        <p class="text-lg mb-2">Нет данных для отображения</p>
        <p class="text-sm">За выбранный период не было генераций</p>
      </div>
    </div>

    <template v-else>
      <!-- Легенда сверху -->
      <div class="flex flex-wrap gap-4 mb-4">
        <div
          v-for="(entry, index) in chartData"
          :key="entry.name"
          class="flex items-center gap-2"
        >
          <div
            class="w-3 h-3 rounded-full"
            :style="{ backgroundColor: chartColors[index % chartColors.length] }"
          ></div>
          <span class="text-sm text-gray-400">{{ formatName(entry.name) }}</span>
        </div>
      </div>

      <!-- График -->
      <div class="w-full h-[calc(100%-2rem)]">
        <PieChart :width="400" :height="300">
          <Pie
            :data="chartData"
            :cx="200"
            :cy="150"
            :innerRadius="60"
            :outerRadius="100"
            :paddingAngle="2"
            dataKey="value"
            nameKey="name"
            :label="renderCustomizedLabel"
          >
            <Cell
              v-for="(entry, index) in chartData"
              :key="entry.name"
              :fill="chartColors[index % chartColors.length]"
            />
          </Pie>
          <Tooltip :content="customTooltipContent" />
        </PieChart>
      </div>

      <!-- Центральная статистика -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div class="text-center">
          <div class="text-3xl font-bold text-white">{{ totalGenerations }}</div>
          <div class="text-sm text-gray-400">Всего генераций</div>
        </div>
      </div>
    </template>

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
import {computed, h, ref} from 'vue'
import { PieChart, Pie, Cell, Tooltip } from 'recharts'

interface ChartData {
  name: string
  value: number
}

interface PieChartProps {
  cx: number
  cy: number
  midAngle: number
  innerRadius: number
  outerRadius: number
  percent: number
}

interface Props {
  data: ChartData[]
  loading?: boolean
  colors?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  colors: () => [
    '#8B5CF6',
    '#3B82F6',
    '#10B981',
    '#F59E0B',
    '#EF4444'
  ]
})

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
    // Возвращаем заглушку с нулевыми значениями
    return [
      { name: 'lesson_plan', value: 0 },
      { name: 'exercise', value: 0 },
      { name: 'game', value: 0 },
      { name: 'image', value: 0 }
    ];
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

const chartColors = computed(() => props.colors)

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

const renderCustomizedLabel = (props: PieChartProps) => {
  try {
    const { cx, cy, midAngle, innerRadius, outerRadius, percent } = props
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    if (percent < 0.05) return null

    return {
      x,
      y,
      fill: 'white',
      textAnchor: x > cx ? 'start' : 'end',
      dominantBaseline: 'central',
      content: `${(percent * 100).toFixed(0)}%`
    }
  } catch (error) {
    console.error('Error rendering label:', error)
    return null
  }
}

const customTooltipContent = (props: { active?: boolean; payload?: any[] }) => {
  if (!props.active || !props.payload?.length) return null

  const data = props.payload[0].payload
  if (!data) return null

  return h('div', {
    class: 'bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-700'
  }, [
    h('div', { class: 'text-white font-medium' }, formatName(data.name)),
    h('div', { class: 'text-gray-400 text-sm mt-1' }, [
      h('div', null, `Количество: ${data.value.toLocaleString()}`),
      h('div', null, `Процент: ${((data.value / totalGenerations.value) * 100).toFixed(1)}%`)
    ])
  ])
}

const chartAnimation = computed(() => ({
  keyframes: [
    { opacity: 0, transform: 'scale(0.95)' },
    { opacity: 1, transform: 'scale(1)' }
  ],
  options: {
    duration: 800,
    easing: 'ease-out'
  }
}))
</script>

<style scoped>
.recharts-pie-label-text {
  font-size: 12px;
}

.recharts-tooltip-wrapper {
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

.chart-container-enter-active {
  animation: chart-fade-in v-bind("chartAnimation.options.duration + 'ms'") v-bind("chartAnimation.options.easing");
}

@keyframes chart-fade-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
