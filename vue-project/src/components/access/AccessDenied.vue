<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
    <div class="max-w-md w-full">
      <!-- Заблокированный пользователь -->
      <div v-if="reason === 'banned'" class="text-center">
        <div class="mb-8">
          <div class="w-24 h-24 mx-auto mb-6 bg-red-500/20 rounded-full flex items-center justify-center">
            <svg class="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-white mb-4">Доступ запрещен</h1>
          <p class="text-gray-300 text-lg mb-6">
            Ваш аккаунт заблокирован администратором
          </p>
          <p class="text-gray-400 text-sm">
            Если вы считаете, что это ошибка, обратитесь в службу поддержки
          </p>
        </div>
      </div>

      <!-- Неподписанный пользователь -->
      <div v-else-if="reason === 'not_subscribed'" class="text-center">
        <div class="mb-8">
          <div class="w-24 h-24 mx-auto mb-6 bg-blue-500/20 rounded-full flex items-center justify-center">
            <svg class="w-12 h-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 0h10m-10 0a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2M9 12l2 2 4-4"></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-white mb-4">Требуется подписка</h1>
          <p class="text-gray-300 text-lg mb-6">
            Для использования приложения необходимо подписаться на наш канал
          </p>

          <!-- Кнопка подписки -->
          <div class="space-y-4">
            <a
              v-if="channelUrl"
              :href="channelUrl"
              target="_blank"
              class="inline-flex items-center justify-center w-full px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors duration-200"
            >
              <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.374 0 0 5.373 0 12s5.374 12 12 12 12-5.373 12-12S18.626 0 12 0zm5.568 8.16c-.169 1.858-.896 6.728-.896 6.728-.377 2.655-.377 2.655-1.377 2.655-.896 0-1.377-1.169-1.377-2.655 0 0-.727-4.87-.896-6.728-.169-1.858.727-2.655 1.377-2.655s1.546.797 1.377 2.655z"/>
              </svg>
              Подписаться на канал
            </a>

            <!-- Кнопка проверки подписки -->
            <button
              @click="checkSubscription"
              :disabled="isChecking"
              class="w-full px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white font-medium rounded-lg transition-colors duration-200 disabled:cursor-not-allowed"
            >
              <span v-if="isChecking" class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Проверяем...
              </span>
              <span v-else>Я подписался</span>
            </button>
          </div>

          <!-- Сообщение об ошибке -->
          <div v-if="checkError" class="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p class="text-red-300 text-sm">{{ checkError }}</p>
          </div>
        </div>
      </div>

      <!-- Неподписанный на канал приложения -->
      <div v-else-if="reason === 'evo_subscription_required'" class="text-center">
        <div class="mb-8">
          <div class="w-24 h-24 mx-auto mb-6 bg-purple-500/20 rounded-full flex items-center justify-center">
            <svg class="w-12 h-12 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-white mb-4">Требуется подписка на EVO Teach AI</h1>
          <p class="text-gray-300 text-lg mb-6">
            Для доступа к приложению необходимо подписаться на наш канал EVO Teach AI
          </p>

          <!-- Кнопка подписки на канал приложения -->
          <div class="space-y-4">
            <a
              v-if="channelUrl"
              :href="channelUrl"
              target="_blank"
              class="inline-flex items-center justify-center w-full px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg transition-colors duration-200"
            >
              <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.374 0 0 5.373 0 12s5.374 12 12 12 12-5.373 12-12S18.626 0 12 0zm5.568 8.16c-.169 1.858-.896 6.728-.896 6.728-.377 2.655-.377 2.655-1.377 2.655-.896 0-1.377-1.169-1.377-2.655 0 0-.727-4.87-.896-6.728-.169-1.858.727-2.655 1.377-2.655s1.546.797 1.377 2.655z"/>
              </svg>
              Подписаться на EVO Teach AI
            </a>

            <!-- Кнопка проверки подписки -->
            <button
              @click="checkSubscription"
              :disabled="isChecking"
              class="w-full px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 text-white font-medium rounded-lg transition-colors duration-200 disabled:cursor-not-allowed"
            >
              <span v-if="isChecking" class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Проверяем...
              </span>
              <span v-else>Я подписался</span>
            </button>
          </div>

          <!-- Сообщение об ошибке -->
          <div v-if="checkError" class="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
            <p class="text-red-300 text-sm">{{ checkError }}</p>
          </div>
        </div>
      </div>

      <!-- Неизвестная ошибка -->
      <div v-else class="text-center">
        <div class="mb-8">
          <div class="w-24 h-24 mx-auto mb-6 bg-yellow-500/20 rounded-full flex items-center justify-center">
            <svg class="w-12 h-12 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-white mb-4">Ошибка доступа</h1>
          <p class="text-gray-300 text-lg mb-6">
            Произошла ошибка при проверке доступа
          </p>
          <button
            @click="retry"
            class="px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg transition-colors duration-200"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMainStore } from '@/store'

interface Props {
  reason: 'banned' | 'not_subscribed' | 'evo_subscription_required' | 'unknown'
  channelUrl?: string
  error?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'retry'): void
}>()

const store = useMainStore()
const isChecking = ref(false)
const checkError = ref('')

const checkSubscription = async () => {
  isChecking.value = true
  checkError.value = ''

  try {
    // Пытаемся повторно аутентифицироваться
    await store.initializeApp()

    // Если успешно, перезагружаем страницу
    window.location.reload()
  } catch (error: any) {
    console.error('Subscription check failed:', error)

    if (error.response?.status === 402) {
      const errorDetail = error.response.data?.detail;
      if (errorDetail?.reason === 'evo_subscription_required') {
        checkError.value = 'Вы еще не подписались на канал EVO Teach AI'
      } else {
        checkError.value = 'Вы еще не подписались на канал'
      }
    } else if (error.response?.status === 403) {
      checkError.value = 'Ваш аккаунт заблокирован'
    } else {
      checkError.value = 'Ошибка при проверке подписки. Попробуйте позже.'
    }
  } finally {
    isChecking.value = false
  }
}

const retry = () => {
  emit('retry')
}
</script>
