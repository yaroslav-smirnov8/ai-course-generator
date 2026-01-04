<!-- src/components/ErrorBoundary.vue -->
<template>
  <div>
    <slot v-if="!errorMessage"></slot>
    <div v-else class="error-boundary p-4 bg-red-500/10 rounded-lg m-4">
      <h2 class="text-xl font-bold text-red-500 mb-2">Произошла ошибка</h2>
      <p class="text-red-400 mb-4">{{ errorMessage }}</p>
      <button
        @click="resetError"
        class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
      >
        Попробовать снова
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const errorMessage = ref<string | null>(null)

onErrorCaptured((err: Error) => {
  errorMessage.value = err.message || 'Произошла неизвестная ошибка'
  console.error('Captured error:', err)
  return false // Предотвращаем всплытие ошибки
})

const resetError = () => {
  errorMessage.value = null
  router.go(0) // Перезагружаем текущий маршрут
}
</script>
