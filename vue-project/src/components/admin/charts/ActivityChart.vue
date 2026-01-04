<template>
  <div class="admin-card">
    <div class="admin-card-header mb-6">
      <h3 class="admin-card-title">{{ title }}</h3>
      <div class="flex gap-2">
        <button
          v-for="period in periods"
          :key="period.value"
          @click="selectedPeriod = period.value"
          :class="[
            'px-2 py-1 text-sm rounded-lg',
            selectedPeriod === period.value
              ? 'bg-purple-500 text-white'
              : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
          ]"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <div class="h-72">
      <!-- Сообщение о пустых данных -->
      <div v-if="!filteredData || filteredData.length === 0" class="h-full flex flex-col items-center justify-center">
        <div class="text-gray-400 text-center">
          <p class="text-lg mb-2">No data to display</p>
          <p class="text-sm">За выбранный период не было активности</p>
        </div>
      </div>

      <!-- Сообщение о нулевой активности (скрыто) -->
      <!-- Мы не показываем это сообщение, чтобы всегда отображать график -->
      <div v-if="false" class="h-full flex flex-col items-center justify-center">
        <div class="text-gray-400 text-center">
          <p class="text-lg mb-2">Нет активности</p>
          <p class="text-sm">За выбранный период не было генераций</p>
        </div>
      </div>

      <!-- График -->
      <div v-else>
        <div v-if="filteredData && filteredData.length > 0">
          <div>
            <LineChart
              :data="filteredData"
              :margin="{ top: 10, right: 10, bottom: 20, left: 40 }"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9CA3AF"
                :tick="{ fill: '#9CA3AF' }"
              />
              <YAxis
                stroke="#9CA3AF"
                :tick="{ fill: '#9CA3AF' }"
              />
              <Tooltip
                :contentStyle="{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '0.5rem',
                  color: '#F3F4F6'
                }"
                :formatter="tooltipFormatter"
              />
              <Legend :formatter="legendFormatter" />
              <Line
                v-for="line in lines"
                :key="line.key"
                type="monotone"
                :dataKey="line.key"
                :stroke="line.color"
                :name="line.name"
              />
            </LineChart>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts'

interface DataPoint {
  day: string
  generations: number
  activeUsers: number
  [key: string]: any
}

interface ChartLine {
  key: string
  name: string
  color: string
}

interface Props {
  title: string
  data: DataPoint[]
  lines: ChartLine[]
}

const props = defineProps<Props>()

const periods = [
  { value: 'day', label: '24h' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' }
]

const selectedPeriod = ref('week')

// Форматтеры для графиков
const tooltipFormatter = (value, name) => {
  console.log('CHART_DEBUG: Tooltip formatter called with:', { value, name });
  return [value, name];
}

const legendFormatter = (value) => {
  console.log('CHART_DEBUG: Legend formatter called with:', value);
  return value;
}

// Проверяем, есть ли ненулевые значения в данных
const hasNonZeroActivity = computed(() => {
  if (!filteredData.value || filteredData.value.length === 0) {
    return false;
  }

  return filteredData.value.some(point => {
    if (!point || typeof point !== 'object') return false;

    const hasGenerations = point.generations && point.generations > 0;
    const hasActiveUsers = point.activeUsers && point.activeUsers > 0;

    return hasGenerations || hasActiveUsers;
  });
});

const filteredData = computed(() => {
  console.log('CHART_DEBUG: Activity chart data:', props.data);

  // Проверяем, что данные не пустые
  if (!props.data || !Array.isArray(props.data) || props.data.length === 0) {
    console.log('CHART_DEBUG: No data for activity chart, using default data');

    // Создаем заглушку с нулевыми значениями
    const defaultData = [];
    const now = new Date();

    // Создаем данные в зависимости от выбранного периода
    let days = 7; // Default is week

    switch (selectedPeriod.value) {
      case 'day':
        days = 1;
        break;
      case 'week':
        days = 7;
        break;
      case 'month':
        days = 30;
        break;
    }

    // Создаем точки данных для каждого дня
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(now.getDate() - i);
      const dateStr = date.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' });

      defaultData.push({
        date: dateStr,
        generations: 0,
        activeUsers: 0
      });
    }

    // Если нет активности, возвращаем пустой массив, чтобы показать сообщение "Нет данных"
    return [];
  }

  // Проверяем, есть ли хоть одна запись с ненулевыми значениями
  const hasActivity = props.data.some(point => {
    if (!point || typeof point !== 'object') return false;

    // Проверяем, есть ли ненулевые значения
    const hasGenerations = point.generations && point.generations > 0;
    const hasActiveUsers = point.activeUsers && point.activeUsers > 0;

    console.log('CHART_DEBUG: Checking activity for point:', point);
    console.log('CHART_DEBUG: hasGenerations:', hasGenerations, 'hasActiveUsers:', hasActiveUsers);

    return hasGenerations || hasActiveUsers;
  });

  // Если нет активности, все равно возвращаем данные
  // Это позволит отобразить график с нулевыми значениями вместо сообщения "Нет данных"
  if (!hasActivity) {
    console.log('CHART_DEBUG: No activity in data, but still returning data for display');
    return props.data;
  }

  // Если данные есть, фильтруем их по выбранному периоду
  const now = new Date();
  const cutoff = new Date();

  switch (selectedPeriod.value) {
    case 'day':
      cutoff.setDate(now.getDate() - 1);
      break;
    case 'week':
      cutoff.setDate(now.getDate() - 7);
      break;
    case 'month':
      cutoff.setMonth(now.getMonth() - 1);
      break;
  }

  const filtered = props.data.filter(point => {
    if (!point || typeof point !== 'object') {
      console.error('CHART_DEBUG: Invalid data point:', point);
      return false;
    }

    try {
      // Проверяем, есть ли поле date
      if (!point.date) {
        console.error('CHART_DEBUG: Data point missing date:', point);
        return false;
      }

      // Используем dateKey вместо date для сравнения дат
      if (point.dateKey) {
        // Если есть dateKey, используем его для создания объекта Date
        const pointDate = new Date(point.dateKey);
        if (!isNaN(pointDate.getTime())) {
          return pointDate >= cutoff;
        }
      }

      // Если нет dateKey или он некорректный, пытаемся использовать date
      // Но date может быть в формате "пн, 15", который не преобразуется в Date
      // Поэтому просто включаем все точки данных для выбранного периода
      return true;
    } catch (e) {
      console.error('CHART_DEBUG: Error filtering data point:', e, point);
      return false;
    }
  });

  console.log('CHART_DEBUG: Filtered activity chart data:', filtered);

  // Если после фильтрации не осталось данных, возвращаем пустой массив
  if (filtered.length === 0) {
    console.log('CHART_DEBUG: No data after filtering, returning empty array');
    return [];
  }

  return filtered;
})
</script>
