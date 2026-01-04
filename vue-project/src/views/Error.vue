<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-lg w-full mx-4 p-8 bg-gray-800 rounded-lg shadow-lg">
      <div class="text-center">
        <!-- Error Icon -->
        <div class="mb-6">
          <svg class="mx-auto h-16 w-16 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>

        <!-- Error Title -->
        <h2 class="text-2xl font-bold text-white mb-4">
          {{ title }}
        </h2>

        <!-- Error Message -->
        <p class="text-gray-300 mb-8">
          {{ message }}
        </p>

        <!-- Action Buttons -->
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            @click="handleRetry"
            class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Try again
          </button>

          <button
            @click="handleClose"
            class="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { TelegramService } from '@/services/telegram'

const route = useRoute()
const router = useRouter()

// Получаем параметры ошибки из URL
const title = computed(() => {
  switch(route.query.code) {
    case 'AUTH_ERROR':
      return 'Authentication error'
    case 'INIT_ERROR':
      return 'Initialization error'
    default:
      return 'An error occurred'
  }
})

const message = computed(() =>
  route.query.message?.toString() || 'Please try again later'
)

// Обработчики
const handleRetry = async () => {
  try {
    // Reload the application
    window.location.reload()
  } catch (error) {
    console.error('Error retrying:', error)
  }
}

const handleClose = () => {
  // Close WebApp
  TelegramService.close()
}
</script>
