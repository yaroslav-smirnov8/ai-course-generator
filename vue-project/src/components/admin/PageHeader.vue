<!-- src/components/admin/PageHeader.vue -->
<template>
  <div class="mb-8">
    <Breadcrumbs class="mb-2" />
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ title }}
        </h1>
        <p v-if="description" class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ description }}
        </p>
      </div>
      <div class="flex items-center space-x-4">
        <slot name="actions"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Breadcrumbs from './Breadcrumbs.vue'

interface Props {
  title: string
  description?: string
}

defineProps<Props>()
</script>
