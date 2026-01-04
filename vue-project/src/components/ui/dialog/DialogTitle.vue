# src/components/ui/dialog/DialogTitle.vue
<template>
  <DialogTitle as="h3" class="text-lg font-semibold leading-none">
    <slot />
  </DialogTitle>
</template>

<script setup lang="ts">
import { DialogTitle } from '@headlessui/vue'
</script>
