<template>
  <div class="modal-backdrop" v-if="show" @click.self="$emit('close')">
    <div class="modal-container">
      <!-- Заголовок -->
      <div class="modal-header">
        <h3 class="modal-title">
          <span class="flex items-center gap-2">
            <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
            </svg>
            Activate Promo Code
          </span>
        </h3>
        <button @click="$emit('close')" class="modal-close">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Форма -->
      <form @submit.prevent="handleSubmit" class="modal-body">
        <!-- Описание -->
        <div class="text-gray-400 text-sm mb-4">
          Enter promo code to receive points, activate a plan, or get a discount.
        </div>

        <!-- Поле ввода промокода -->
        <div class="space-y-2">
          <label class="modal-label">Promo Code</label>
          <input
            v-model="promoCode"
            type="text"
            required
            class="modal-input uppercase tracking-wider"
            placeholder="Enter promo code"
            :disabled="isLoading"
            @input="handleInput"
            maxlength="50"
          >
          <div class="text-xs text-gray-500">
            Promo code can contain letters and numbers
          </div>
        </div>

        <!-- Ошибка -->
        <div v-if="error" class="bg-red-800/50 border border-red-600 rounded-lg p-3 text-red-200 text-sm">
          {{ error }}
        </div>

        <!-- Успешное применение -->
        <div v-if="successMessage" class="bg-green-800/50 border border-green-600 rounded-lg p-3 text-green-200 text-sm">
          {{ successMessage }}
        </div>

        <!-- Кнопки -->
        <div class="flex gap-3 pt-4">
          <button
            type="button"
            @click="$emit('close')"
            class="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
            :disabled="isLoading"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isLoading || !promoCode.trim()"
          >
            <span v-if="isLoading" class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Applying...
            </span>
            <span v-else>Apply</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useMainStore } from '@/store'
import { toastService } from '@/services/toastService'

interface Props {
  show: boolean
}

interface PromoCodeApplyResponse {
  success: boolean
  message: string
  points_added?: number
  tariff_activated?: string
  tariff_duration?: number
  discount_applied?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'success', result: PromoCodeApplyResponse): void
}>()

const store = useMainStore()

// Состояние формы
const promoCode = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const successMessage = ref<string | null>(null)

// Очистка формы при открытии/закрытии модального окна
watch(() => props.show, (newValue) => {
  if (newValue) {
    // Сброс формы при открытии
    promoCode.value = ''
    error.value = null
    successMessage.value = null
  }
})

// Обработка ввода - приведение к верхнему регистру и фильтрация символов
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  // Оставляем только буквы, цифры и некоторые символы
  const cleaned = target.value.toUpperCase().replace(/[^A-Z0-9\-_]/g, '')
  promoCode.value = cleaned
  
  // Очищаем ошибки при вводе
  if (error.value) {
    error.value = null
  }
  if (successMessage.value) {
    successMessage.value = null
  }
}

// Применение промокода
const handleSubmit = async () => {
  if (!promoCode.value.trim() || isLoading.value) return

  isLoading.value = true
  error.value = null
  successMessage.value = null

  try {
    // Вызываем метод из store
    const response = await store.applyPromocode(promoCode.value.trim())
    
    if (response.success) {
      // Успешное применение
      successMessage.value = response.message
      
      // Показываем toast уведомление
      toastService.success(response.message)
      
      // Добавляем тактильную обратную связь для Telegram
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('success')
      }
      
      // Уведомляем родительский компонент об успехе
      emit('success', response)
      
      // Закрываем модальное окно через 2 секунды
      setTimeout(() => {
        emit('close')
      }, 2000)
      
    } else {
      // Ошибка применения
      error.value = response.message || 'Не удалось применить промокод'
      
      // Показываем toast уведомление об ошибке
      toastService.error(error.value)
      
      // Добавляем тактильную обратную связь для Telegram
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred('error')
      }
    }
    
  } catch (err: any) {
    console.error('Error applying promocode:', err)
    error.value = err.message || 'Произошла ошибка при применении промокода'
    toastService.error(error.value)
    
    // Добавляем тактильную обратную связь для Telegram
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('error')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* Дополнительные стили для промокода */
.modal-input.uppercase {
  font-family: 'Courier New', monospace;
  letter-spacing: 0.1em;
}

/* Анимация для успешного сообщения */
.bg-green-800\/50 {
  animation: slideIn 0.3s ease-out;
}

.bg-red-800\/50 {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
