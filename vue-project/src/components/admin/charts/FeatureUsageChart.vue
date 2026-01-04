//components/admin/charts/FeatureUsageChart.vue
<template>
  <div class="h-[300px]">
    <div>
      <div>
        <div>
          <BarChart
            :data="data"
            :margin="{ top: 20, right: 20, bottom: 20, left: 40 }"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              :contentStyle="{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '0.5rem',
                color: '#F3F4F6'
              }"
            />
            <Bar dataKey="value" fill="#8B5CF6">
              <Cell v-for="(entry, index) in data" :key="index" :fill="colors[index % colors.length]" />
            </Bar>
          </BarChart>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts'

interface FeatureData {
  name: string
  value: number
}

const colors = ['#8B5CF6', '#34D399', '#3B82F6', '#F59E0B', '#EF4444']

defineProps<{
  data: FeatureData[]
}>()
</script>
