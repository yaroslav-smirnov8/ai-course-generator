<!-- src/components/admin/NavItem.vue -->
<template>
  <router-link
    :to="to"
    class="flex items-center px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
    :class="{ 'router-link-active': isActive }"
  >
    <component :is="icon" class="w-5 h-5 mr-3" />
    <span>{{ label }}</span>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type { Component } from 'vue'

interface Props {
  icon: Component
  to: string
  label: string
}

const props = defineProps<Props>()
const route = useRoute()

const isActive = computed(() => {
  if (props.to === '/admin' && route.path === '/admin') {
    return true
  }
  return route.path.startsWith(props.to) && props.to !== '/admin'
})
</script>

<style scoped>
.router-link-active {
  @apply bg-purple-50 text-purple-600 dark:bg-gray-700 dark:text-purple-400;
}

.router-link-enter-active,
.router-link-leave-active {
  transition: all 0.2s ease;
}

.router-link-enter-from,
.router-link-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
