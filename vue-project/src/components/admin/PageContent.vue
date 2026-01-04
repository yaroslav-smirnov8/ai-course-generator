<!-- src/components/admin/PageContent.vue -->
<template>
  <div
    class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
    :class="[padding && 'p-6']"
  >
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
interface Props {
  padding?: boolean
}

withDefaults(defineProps<Props>(), {
  padding: true
})
</script>
