<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <div class="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full flex items-center justify-center">
          <svg class="w-12 h-12 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
          </svg>
        </div>
        
        <h1 class="text-3xl font-bold text-white mb-4">Требуется Premium тариф</h1>
        
        <p class="text-gray-300 text-lg mb-6">
          {{ featureName }} доступен только пользователям с Premium тарифом
        </p>
        
        <div class="bg-gray-800/50 rounded-lg p-4 mb-6">
          <h3 class="text-white font-medium mb-2">Premium тариф включает:</h3>
          <ul class="text-gray-300 text-sm space-y-1">
            <li>✨ 25 генераций в день</li>
            <li>🖼️ 8 изображений в день</li>
            <li>📚 Генератор курсов</li>
            <li>🤖 AI-ассистент</li>
            <li>🎯 Все остальные функции</li>
          </ul>
        </div>
        
        <!-- Кнопка покупки тарифа -->
        <div class="space-y-4">
          <button
            @click="goToTariffs"
            class="inline-flex items-center justify-center w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg transition-all duration-200 transform hover:scale-105"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            Купить Premium тариф
          </button>
          
          <!-- Кнопка возврата -->
          <button
            @click="goBack"
            class="w-full px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg transition-colors duration-200"
          >
            Вернуться назад
          </button>
        </div>
        
        <!-- Информация о текущем тарифе -->
        <div v-if="currentTariff" class="mt-6 text-sm text-gray-400">
          <p>Ваш текущий тариф: <span class="text-white">{{ getTariffName(currentTariff) }}</span></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMainStore } from '@/store'
import { TariffType } from '@/core/constants'

interface Props {
  featureName: string
}

const props = defineProps<Props>()
const router = useRouter()
const store = useMainStore()

const currentTariff = computed(() => store.user?.tariff)

const getTariffName = (tariff: string) => {
  switch (tariff) {
    case TariffType.BASIC:
      return 'Базовый'
    case TariffType.STANDARD:
      return 'Стандартный'
    case TariffType.PREMIUM:
      return 'Premium'
    default:
      return 'Бесплатный'
  }
}

const goToTariffs = () => {
  router.push('/tariffs')
}

const goBack = () => {
  router.go(-1)
}
</script>
