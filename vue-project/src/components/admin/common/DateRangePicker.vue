<template>
  <div class="relative inline-flex">
    <!-- Кнопка вызова календаря -->
    <button
      type="button"
      @click="toggleDropdown"
      class="bg-gray-700 text-white rounded-lg px-4 py-2 inline-flex items-center gap-2"
    >
      <CalendarIcon class="h-5 w-5" />
      <span v-if="!start && !end">Select Period</span>
      <span v-else>{{ formatDateRange }}</span>
    </button>

    <!-- Выпадающий календарь -->
    <div
      v-if="isOpen"
      class="absolute z-50 mt-2 right-0 bg-gray-800 rounded-lg shadow-lg p-4 w-[300px]"
    >
      <!-- Быстрые фильтры -->
      <div class="mb-4 grid grid-cols-2 gap-2">
        <button
          v-for="filter in quickFilters"
          :key="filter.label"
          @click="applyQuickFilter(filter.value)"
          class="text-sm px-3 py-1.5 rounded-lg text-gray-300 hover:bg-gray-700"
          :class="{ 'bg-gray-700': isActiveFilter(filter.value) }"
        >
          {{ filter.label }}
        </button>
      </div>

      <div class="border-t border-gray-700 pt-4">
        <!-- Выбор начальной даты -->
        <div class="mb-3">
          <label class="block text-sm text-gray-400 mb-1">Period Start</label>
          <input
            type="date"
            v-model="startDate"
            class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600"
            :max="endDate || undefined"
          >
        </div>

        <!-- Выбор конечной даты -->
        <div class="mb-3">
          <label class="block text-sm text-gray-400 mb-1">Period End</label>
          <input
            type="date"
            v-model="endDate"
            class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600"
            :min="startDate || undefined"
          >
        </div>

        <!-- Кнопки -->
        <div class="flex justify-end gap-2 mt-4">
          <button
            @click="clearDates"
            class="px-3 py-1.5 text-sm rounded-lg text-gray-300 hover:bg-gray-700"
          >
            Reset
          </button>
          <button
            @click="applyDates"
            class="px-3 py-1.5 text-sm rounded-lg bg-purple-500 text-white hover:bg-purple-600"
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onUnmounted, onMounted} from 'vue'
import { Calendar as CalendarIcon } from 'lucide-vue-next'

interface Props {
  start?: string
  end?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:start', value: string): void
  (e: 'update:end', value: string): void
}>()

const isOpen = ref(false)
const startDate = ref(props.start || '')
const endDate = ref(props.end || '')

// Быстрые фильтры
const quickFilters = [
  { label: 'Today', value: 'today' },
  { label: 'Yesterday', value: 'yesterday' },
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' }
]

const formatDateRange = computed(() => {
  if (!props.start && !props.end) return 'Select Period'
  if (!props.end) return `From ${formatDate(props.start)}`
  if (!props.start) return `To ${formatDate(props.end)}`
  return `${formatDate(props.start)} - ${formatDate(props.end)}`
})

const formatDate = (date: string | undefined) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString()
}

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const applyQuickFilter = (filter: string) => {
  const today = new Date()
  const endOfDay = new Date(today)
  endOfDay.setHours(23, 59, 59, 999)

  switch (filter) {
    case 'today':
      startDate.value = today.toISOString().split('T')[0]
      endDate.value = today.toISOString().split('T')[0]
      break
    case 'yesterday':
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      startDate.value = yesterday.toISOString().split('T')[0]
      endDate.value = yesterday.toISOString().split('T')[0]
      break
    case 'week':
      const weekAgo = new Date(today)
      weekAgo.setDate(weekAgo.getDate() - 7)
      startDate.value = weekAgo.toISOString().split('T')[0]
      endDate.value = today.toISOString().split('T')[0]
      break
    case 'month':
      const monthAgo = new Date(today)
      monthAgo.setMonth(monthAgo.getMonth() - 1)
      startDate.value = monthAgo.toISOString().split('T')[0]
      endDate.value = today.toISOString().split('T')[0]
      break
  }

  applyDates()
}

const isActiveFilter = (filter: string): boolean => {
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0]
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0]

  switch (filter) {
    case 'today':
      return startDate.value === today && endDate.value === today
    case 'yesterday':
      return startDate.value === yesterday && endDate.value === yesterday
    case 'week':
      return startDate.value === weekAgo && endDate.value === today
    case 'month':
      return startDate.value === monthAgo && endDate.value === today
    default:
      return false
  }
}

const applyDates = () => {
  emit('update:start', startDate.value)
  emit('update:end', endDate.value)
  isOpen.value = false
}

const clearDates = () => {
  startDate.value = ''
  endDate.value = ''
  applyDates()
}

// Закрытие при клике вне компонента
const clickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.date-range-picker')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', clickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', clickOutside)
})
</script>
