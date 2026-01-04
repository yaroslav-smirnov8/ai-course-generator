<template>
  <div
    class="nav-link"
    @click="handleClick"
    :class="[
      active ? 'nav-link--active' : '',
      className
    ]"
  >
    <slot></slot>
    <span v-if="label" class="nav-label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getToastManager } from '@/plugins/toastManager';

const props = defineProps<{
  to: string;
  className?: string;
  active?: boolean;
  forceReload?: boolean;
  label?: string;
}>();

const emit = defineEmits(['navigate']);
const route = useRoute();
const router = useRouter();

// Обрабатываем клик по ссылке
const handleClick = () => {
  emit('navigate', props.to);
  
  // Очищаем тосты перед навигацией
  getToastManager().clearAll();
  
  // Стандартная навигация
  router.push(props.to);
};
</script>

<style scoped>
.nav-link {
  cursor: pointer;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
  transition: all 0.2s ease;
}

.nav-label {
  font-size: 12px;
  margin-top: 4px;
  font-weight: 500;
  transition: color 0.2s ease;
}

.nav-link--active {
  color: var(--primary-color);
  position: relative;
}

.nav-link--active .nav-label {
  color: #9333EA;
}

.nav-link--active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  background-color: #9333EA;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(147, 51, 234, 0.5);
}
</style> 