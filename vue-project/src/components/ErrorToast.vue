<template>
  <Transition name="ds-toast">
    <div v-if="visible" class="ds-toast ds-toast-error">
      <div class="ds-toast-content">
        <div class="ds-toast-icon">❌</div>
        <div class="ds-toast-message">{{ message }}</div>
        <button class="ds-toast-close" @click="onClose">×</button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { initDesignSystem } from '@/plugins/designSystem';

defineProps<{
  visible: boolean;
  message: string;
}>();

const emit = defineEmits(['close']);

const onClose = () => {
  emit('close');
};

onMounted(() => {
  initDesignSystem();
});
</script>

<style scoped>
.ds-toast {
  position: fixed;
  top: var(--spacing-md);
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - var(--spacing-lg));
  max-width: 500px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-index-toast);
  overflow: hidden;
}

.ds-toast-error {
  background-color: var(--color-danger);
  color: var(--color-white);
}

.ds-toast-content {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
}

.ds-toast-icon {
  flex-shrink: 0;
  margin-right: var(--spacing-sm);
}

.ds-toast-message {
  flex-grow: 1;
  font-size: var(--font-size-sm);
}

.ds-toast-close {
  background: none;
  border: none;
  color: var(--color-white);
  font-size: var(--font-size-xl);
  cursor: pointer;
  padding: 0;
  margin-left: var(--spacing-sm);
  line-height: 1;
}

/* Анимации */
.ds-toast-enter-active,
.ds-toast-leave-active {
  transition: opacity var(--transition-speed) ease, transform var(--transition-speed) ease;
}

.ds-toast-enter-from,
.ds-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(calc(-1 * var(--spacing-lg)));
}
</style> 