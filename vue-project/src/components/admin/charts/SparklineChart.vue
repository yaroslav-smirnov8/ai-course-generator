<template>
  <div class="h-12">
    <svg :width="width" :height="height" class="sparkline">
      <path
        :d="pathD"
        :stroke="color"
        fill="none"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle
        v-if="data.length > 0"
        :cx="width - 2"
        :cy="getY(data[data.length - 1])"
        r="2"
        :fill="color"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: number[]
  color?: string
  width?: number
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  color: '#8B5CF6',
  width: 120,
  height: 48
})

const getX = (index: number) => {
  return (index * props.width) / (props.data.length - 1)
}

const getY = (value: number) => {
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min
  const normalized = (value - min) / (range || 1)
  return props.height - (normalized * props.height)
}

const pathD = computed(() => {
  if (props.data.length < 2) return ''

  return props.data.reduce((path, point, index) => {
    const x = getX(index)
    const y = getY(point)
    return path + `${index === 0 ? 'M' : 'L'} ${x},${y} `
  }, '')
})
</script>
