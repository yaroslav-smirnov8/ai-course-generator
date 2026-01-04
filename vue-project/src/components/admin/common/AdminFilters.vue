<template>
  <div class="flex flex-wrap gap-4 p-4 bg-gray-800 rounded-lg mb-6">
    <!-- Поиск -->
    <div class="flex-1 min-w-[200px]">
      <input
        v-model="search"
        type="text"
        :placeholder="searchPlaceholder"
        class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
        @input="emitFilters"
      >
    </div>

    <!-- Выбор периода -->
    <div class="min-w-[150px]">
      <select
        v-model="period"
        class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
        @change="emitFilters"
      >
        <option value="all">All Time</option>
        <option value="today">Today</option>
        <option value="week">Week</option>
        <option value="month">Month</option>
        <option value="custom">Select Period</option>
      </select>
    </div>

    <!-- Кастомный период -->
    <div v-if="period === 'custom'" class="flex gap-2">
      <DateRangePicker
        v-model:start="dateFrom"
        v-model:end="dateTo"
        @update:start="emitFilters"
        @update:end="emitFilters"
      />
    </div>

    <!-- Дополнительные фильтры -->
    <div v-if="showAdditionalFilters" class="min-w-[150px]">
      <select
        v-model="type"
        class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
        @change="emitFilters"
      >
        <option value="all">All Types</option>
        <option v-for="filter in additionalFilters"
                :key="filter.value"
                :value="filter.value">
          {{ filter.label }}
        </option>
      </select>
    </div>

    <!-- Кнопки -->
    <div class="flex gap-2">
      <button
        @click="exportData"
        class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
      >
        <DownloadIcon class="w-5 h-5" />
      </button>
      <button
        @click="resetFilters"
        class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
      >
        <RefreshCwIcon class="w-5 h-5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Download as DownloadIcon, RefreshCw as RefreshCwIcon } from 'lucide-vue-next'
import DateRangePicker from './DateRangePicker.vue'

interface Filter {
  value: string
  label: string
}

interface Props {
  searchPlaceholder?: string
  showAdditionalFilters?: boolean
  additionalFilters?: Filter[]
}

const props = withDefaults(defineProps<Props>(), {
  searchPlaceholder: 'Search...',
  showAdditionalFilters: false,
  additionalFilters: () => []
})

const emit = defineEmits<{
  (e: 'filter', filters: Record<string, any>): void
  (e: 'export'): void
}>()

const search = ref('')
const period = ref('all')
const dateFrom = ref('')
const dateTo = ref('')
const type = ref('all')

const emitFilters = () => {
  emit('filter', {
    search: search.value,
    period: period.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
    type: type.value
  })
}

const resetFilters = () => {
  search.value = ''
  period.value = 'all'
  dateFrom.value = ''
  dateTo.value = ''
  type.value = 'all'
  emitFilters()
}

const exportData = () => {
  emit('export')
}

// При изменении фильтров
watch([search, period, dateFrom, dateTo, type], () => {
  emitFilters()
})
</script>
