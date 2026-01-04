<!-- src/components/common/TariffInfoPanel.vue -->
<template>
  <div class="bg-gray-800 rounded-lg p-4 mb-6">
    <!-- Tariff Info -->
    <div class="mb-4">
      <h3 class="text-lg font-semibold text-white mb-2">Current Plan</h3>
      <div class="flex items-center justify-between text-gray-300">
        <span>{{ tariffName }}</span>
        <span v-if="tariffExpiry" class="text-sm">
          Until {{ formatDate(tariffExpiry) }}
        </span>
      </div>
    </div>

    <!-- Points and Limits -->
    <div class="grid grid-cols-3 gap-4">
      <div class="bg-gray-700 rounded p-3">
        <div class="text-sm text-gray-400">Balance</div>
        <div class="text-lg font-semibold text-white">
          {{ points }} points
        </div>
      </div>
      <div class="bg-gray-700 rounded p-3">
        <div class="text-sm text-gray-400">Cost</div>
        <div class="text-lg font-semibold text-white">
          {{ cost }} points
        </div>
      </div>
      <div class="bg-gray-700 rounded p-3">
        <div class="text-sm text-gray-400">Remaining today</div>
        <div class="text-lg font-semibold text-white">
          {{ remaining }}/{{ limit }}
        </div>
      </div>
    </div>

    <!-- Warning Messages -->
    <div v-if="insufficientBalance" class="mt-4 bg-red-900/50 text-red-400 p-3 rounded">
      Insufficient points for generation. Please top up your balance.
    </div>
    <div v-if="limitReached" class="mt-4 bg-yellow-900/50 text-yellow-400 p-3 rounded">
      Daily generation limit reached for current plan.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMainStore } from '@/store'
import { ContentType } from '@/core/constants'

const props = defineProps<{
  contentType: ContentType
}>()

const store = useMainStore()

// Computed properties
const points = computed(() => store.user?.points || 0)
const tariffName = computed(() => store.currentTariff?.name || 'Базовый')
const tariffExpiry = computed(() => store.tariffInfo?.validUntil)
const cost = computed(() => store.getGenerationCost(props.contentType))
const limit = computed(() => store.currentTariffLimits?.generations_limit || 0)
const remaining = computed(() => store.remainingGenerations(props.contentType))

const insufficientBalance = computed(() => points.value < cost.value)
const limitReached = computed(() => remaining.value <= 0)

// Methods
const formatDate = (date: string | Date) => {
  return new Date(date).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}
</script>
