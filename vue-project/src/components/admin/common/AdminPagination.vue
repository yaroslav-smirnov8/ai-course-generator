<template>
  <div class="flex items-center justify-between px-4 py-3 bg-gray-800 rounded-lg">
    <!-- Информация о количестве -->
    <div class="flex items-center text-sm text-gray-400">
      <span>Показано {{ from }}-{{ to }} из {{ total }} записей</span>

      <select
        v-model="perPage"
        class="ml-4 bg-gray-700 border-gray-600 text-gray-300 rounded-lg"
        @change="$emit('update:perPage', perPage)"
      >
        <option v-for="n in perPageOptions" :key="n" :value="n">
          {{ n }} на странице
        </option>
      </select>
    </div>

    <!-- Кнопки страниц -->
    <div class="flex gap-1">
      <!-- Первая страница -->
      <button
        @click="$emit('update:page', 1)"
        :disabled="currentPage === 1"
        class="pagination-btn"
        :class="{ 'opacity-50 cursor-not-allowed': currentPage === 1 }"
      >
        <ChevronsLeftIcon class="w-5 h-5" />
      </button>

      <!-- Предыдущая страница -->
      <button
        @click="$emit('update:page', currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-btn"
        :class="{ 'opacity-50 cursor-not-allowed': currentPage === 1 }"
      >
        <ChevronLeftIcon class="w-5 h-5" />
      </button>

      <!-- Номера страниц -->
      <div class="flex gap-1">
        <button
          v-for="pageNumber in displayedPages"
          :key="pageNumber"
          @click="$emit('update:page', pageNumber)"
          class="pagination-btn"
          :class="{
           'bg-purple-500 text-white': pageNumber === currentPage,
           'bg-gray-700 text-gray-300': pageNumber !== currentPage
         }"
        >
          {{ pageNumber }}
        </button>
      </div>

      <!-- Следующая страница -->
      <button
        @click="$emit('update:page', currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
        :class="{ 'opacity-50 cursor-not-allowed': currentPage === totalPages }"
      >
        <ChevronRightIcon class="w-5 h-5" />
      </button>

      <!-- Последняя страница -->
      <button
        @click="$emit('update:page', totalPages)"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
        :class="{ 'opacity-50 cursor-not-allowed': currentPage === totalPages }"
      >
        <ChevronsRightIcon class="w-5 h-5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-vue-next'

interface Props {
  page: number
  perPage: number
  total: number
  maxVisiblePages?: number
}

const props = withDefaults(defineProps<Props>(), {
  maxVisiblePages: 5
})

const emit = defineEmits<{
  (e: 'update:page', page: number): void
  (e: 'update:perPage', perPage: number): void
}>()

const perPage = ref(props.perPage)
const perPageOptions = [10, 25, 50, 100]

const currentPage = computed(() => props.page)
const totalPages = computed(() => Math.ceil(props.total / props.perPage))

const from = computed(() => {
  return (currentPage.value - 1) * props.perPage + 1
})

const to = computed(() => {
  return Math.min(currentPage.value * props.perPage, props.total)
})

// Вычисление отображаемых номеров страниц
const displayedPages = computed(() => {
  const pages: number[] = []
  let startPage = Math.max(1, currentPage.value - Math.floor(props.maxVisiblePages / 2))
  const endPage = Math.min(totalPages.value, startPage + props.maxVisiblePages - 1)

  if (endPage - startPage + 1 < props.maxVisiblePages) {
    startPage = Math.max(1, endPage - props.maxVisiblePages + 1)
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  return pages
})
</script>

<style scoped>
.pagination-btn {
  @apply flex items-center justify-center w-9 h-9 rounded-lg transition-colors;
  @apply hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500;
}
</style>
