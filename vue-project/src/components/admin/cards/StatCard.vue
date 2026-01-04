<template>
  <div class="admin-card">
    <div class="p-6">
      <div class="flex justify-between items-start">
        <div>
          <p class="text-sm text-[var(--admin-text-secondary)]">
            {{ title }}
          </p>
          <p class="mt-2 text-3xl font-bold text-[var(--admin-text)]">
            {{ value }}
          </p>
        </div>
        <div class="p-2 bg-[var(--admin-accent)] bg-opacity-10 rounded-lg">
          <component
            :is="icon"
            class="w-6 h-6 text-[var(--admin-accent)]"
          />
        </div>
      </div>
      <div v-if="trend" class="mt-4 flex items-center">
        <span v-if="trend > 0" class="text-[var(--admin-success)]">
          ↑ {{ trend }}%
        </span>
        <span v-else class="text-[var(--admin-error)]">
          ↓ {{ Math.abs(trend) }}%
        </span>
        <span class="ml-2 text-sm text-[var(--admin-text-secondary)]">
          vs. last period
        </span>
      </div>
      <SparklineChart
        v-if="chart && chartData.length"
        :data="chartData"
        class="mt-4"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TrendingUp, TrendingDown } from 'lucide-vue-next'
import SparklineChart from '../charts/SparklineChart.vue'
import { Card } from '@/components/ui/card'

interface Props {
  title: string
  value: string | number
  trend?: number
  icon?: any
  chart?: boolean
  chartData?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  chart: false,
  chartData: () => []
})
</script>
