<script setup>
import { ref, computed } from 'vue'
import { useMainStore } from '@/store'

const props = defineProps({
  show: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close', 'success'])
const store = useMainStore()

// Available packages
const pointsPackages = [
  { id: 1, points: 100, price: 99, popular: false },
  { id: 2, points: 500, price: 449, popular: true },
  { id: 3, points: 1000, price: 849, popular: false },
  { id: 4, points: 2000, price: 1599, popular: false }
]

const selectedPackage = ref(null)
const isLoading = ref(false)
const error = ref(null)

// Calculate bonus points based on package size
const getBonusPoints = (points) => {
  if (points >= 2000) return Math.floor(points * 0.2) // 20% bonus
  if (points >= 1000) return Math.floor(points * 0.15) // 15% bonus
  if (points >= 500) return Math.floor(points * 0.1) // 10% bonus
  return 0
}

const totalPoints = computed(() => {
  if (!selectedPackage.value) return 0
  const basePoints = selectedPackage.value.points
  const bonusPoints = getBonusPoints(basePoints)
  return basePoints + bonusPoints
})

const handlePackageSelect = (pkg) => {
  selectedPackage.value = pkg
}

const startPurchase = async () => {
  if (!selectedPackage.value) return

  try {
    isLoading.value = true
    error.value = null

    // Инициируем оплату через Telegram
    const result = await store.initPointsPurchase({
      amount: selectedPackage.value.points,
      price: selectedPackage.value.price,
      bonus: getBonusPoints(selectedPackage.value.points)
    })

    if (result.success) {
      emit('success', {
        points: totalPoints.value,
        price: selectedPackage.value.price
      })
    } else {
      error.value = result.error || 'Purchase failed'
    }
  } catch (err) {
    error.value = err.message || 'An error occurred'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 flex items-center justify-center z-50">
    <div class="absolute inset-0 bg-black/50" @click="emit('close')"></div>

    <div class="relative bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
      <h2 class="text-2xl font-bold text-white mb-6">Purchase Points</h2>

      <!-- Packages Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <button
          v-for="pkg in pointsPackages"
          :key="pkg.id"
          class="relative p-4 rounded-lg border-2 transition-colors text-left"
          :class="selectedPackage?.id === pkg.id
            ? 'border-purple-500 bg-purple-500/10'
            : 'border-gray-700 hover:border-gray-600'"
          @click="handlePackageSelect(pkg)"
        >
          <span
            v-if="pkg.popular"
            class="absolute -top-2 -right-2 bg-purple-500 text-white text-xs px-2 py-1 rounded-full"
          >
            Popular
          </span>

          <div class="text-xl font-bold text-white mb-1">
            {{ pkg.points }} Points
          </div>

          <div
            v-if="getBonusPoints(pkg.points) > 0"
            class="text-sm text-purple-400 mb-2"
          >
            +{{ getBonusPoints(pkg.points) }} Bonus Points
          </div>

          <div class="text-lg text-gray-300">
            ${{ pkg.price }}
          </div>
        </button>
      </div>

      <!-- Selection Summary -->
      <div
        v-if="selectedPackage"
        class="bg-gray-700/50 rounded-lg p-4 mb-6"
      >
        <div class="flex justify-between items-center">
          <div>
            <div class="text-gray-300">Selected Package:</div>
            <div class="text-xl font-bold text-white">
              {{ totalPoints }} Points
            </div>
          </div>
          <div class="text-2xl font-bold text-white">
            ${{ selectedPackage.price }}
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="error"
        class="bg-red-500/10 text-red-400 p-4 rounded-lg mb-6"
      >
        {{ error }}
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-4">
        <button
          class="flex-1 px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
          @click="emit('close')"
        >
          Cancel
        </button>

        <button
          class="flex-1 px-6 py-3 rounded-lg text-white transition-colors"
          :class="selectedPackage
            ? 'bg-purple-600 hover:bg-purple-700'
            : 'bg-gray-700 cursor-not-allowed'"
          @click="startPurchase"
          :disabled="!selectedPackage || isLoading"
        >
          {{ isLoading ? 'Processing...' : 'Purchase' }}
        </button>
      </div>
    </div>
  </div>
</template>
