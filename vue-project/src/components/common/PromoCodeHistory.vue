<template>
  <div class="bg-gray-800 rounded-lg p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-xl font-semibold text-white flex items-center gap-2">
        <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        История промокодов
      </h3>
      <button
        @click="loadHistory"
        class="px-3 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-500 transition-colors text-sm"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="flex items-center gap-1">
          <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Загрузка...
        </span>
        <span v-else>Обновить</span>
      </button>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="isLoading && history.length === 0" class="text-center py-8">
      <svg class="animate-spin w-8 h-8 text-purple-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-gray-400">Загружаем историю промокодов...</p>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="bg-red-800/50 border border-red-600 rounded-lg p-4 text-red-200">
      <div class="flex items-start gap-3">
        <svg class="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <div>
          <h4 class="font-medium mb-1">Ошибка загрузки</h4>
          <p class="text-sm">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Пустая история -->
    <div v-else-if="history.length === 0" class="text-center py-8">
      <svg class="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
      </svg>
      <h4 class="text-lg font-medium text-gray-300 mb-2">Промокоды не использовались</h4>
      <p class="text-gray-500 text-sm">Здесь будет отображаться история ваших активированных промокодов</p>
    </div>

    <!-- Список истории -->
    <div v-else class="space-y-3">
      <div
        v-for="item in history"
        :key="item.id"
        class="bg-gray-700/50 rounded-lg p-4 border border-gray-600"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-2">
              <code class="bg-gray-600 px-2 py-1 rounded text-sm font-mono text-purple-300">
                {{ item.promocode_code || 'N/A' }}
              </code>
              <span class="text-xs text-gray-400">
                {{ formatDate(item.used_at) }}
              </span>
            </div>
            
            <div class="space-y-1">
              <!-- Баллы -->
              <div v-if="item.points_added && item.points_added > 0" class="flex items-center gap-2 text-sm">
                <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                </svg>
                <span class="text-yellow-300">+{{ item.points_added }} баллов</span>
              </div>
              
              <!-- Тариф -->
              <div v-if="item.tariff_activated" class="flex items-center gap-2 text-sm">
                <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                </svg>
                <span class="text-green-300">
                  Тариф {{ formatTariffType(item.tariff_activated) }}
                  <span v-if="item.tariff_duration" class="text-gray-400">
                    ({{ item.tariff_duration }} мес.)
                  </span>
                </span>
              </div>
              
              <!-- Скидка -->
              <div v-if="item.discount_applied && item.discount_applied > 0" class="flex items-center gap-2 text-sm">
                <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                </svg>
                <span class="text-blue-300">Скидка {{ item.discount_applied }}%</span>
              </div>
            </div>
          </div>
          
          <!-- Статус -->
          <div class="flex-shrink-0">
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-800/50 text-green-300 border border-green-600">
              <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
              </svg>
              Применен
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMainStore } from '@/store'

interface PromoCodeUsage {
  id: number
  promocode_code?: string
  points_added?: number
  tariff_activated?: string
  tariff_duration?: number
  discount_applied?: number
  used_at: string
}

const store = useMainStore()

// Состояние компонента
const history = ref<PromoCodeUsage[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

// Загрузка истории промокодов
const loadHistory = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await store.getPromocodeHistory()
    
    if (Array.isArray(response)) {
      history.value = response
    } else if (response && Array.isArray(response.data)) {
      history.value = response.data
    } else {
      history.value = []
    }
    
  } catch (err: any) {
    console.error('Error loading promocode history:', err)
    error.value = err.message || 'Не удалось загрузить историю промокодов'
  } finally {
    isLoading.value = false
  }
}

// Форматирование даты
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'Неизвестно'
  }
}

// Форматирование типа тарифа
const formatTariffType = (tariffType: string) => {
  const tariffNames: Record<string, string> = {
    'tariff_1': 'Базовый',
    'tariff_2': 'Стандартный', 
    'tariff_3': 'Премиум',
    'basic': 'Базовый',
    'standard': 'Стандартный',
    'premium': 'Премиум'
  }
  
  return tariffNames[tariffType] || tariffType
}

// Загружаем историю при монтировании компонента
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
/* Дополнительные стили при необходимости */
</style>
