<template>
  <div class="bg-gray-800 rounded-lg p-4">
    <h3 class="text-lg font-medium text-white mb-2">Предпросмотр промпта</h3>
    <pre class="text-sm text-gray-300 whitespace-pre-wrap">{{ prompt }}</pre>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  prompt: string
}>()
</script>
