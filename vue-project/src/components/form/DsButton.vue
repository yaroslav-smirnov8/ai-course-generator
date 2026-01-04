<template>
  <button
    :class="buttonClasses"
    :type="type"
    :disabled="disabled || loading"
    @click="onClick"
  >
    <div v-if="loading" class="ds-loader"></div>
    <span v-else-if="icon" class="button-icon">{{ icon }}</span>
    <span class="button-text">{{ text }}</span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Определяем props компонента
const props = defineProps<{
  text: string;
  variant?: 'primary' | 'secondary' | 'submit' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  icon?: string;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
}>();

// Определяем события
const emit = defineEmits(['click']);

// Формируем классы кнопки
const buttonClasses = computed(() => {
  const classes = ['ds-button'];
  
  // Добавляем класс варианта кнопки
  if (props.variant) {
    if (props.variant === 'submit') {
      classes.push('ds-submit-button');
    } else {
      classes.push(`ds-button-${props.variant}`);
    }
  } else {
    classes.push('ds-button-primary');
  }
  
  // Добавляем класс размера
  if (props.size) {
    classes.push(`ds-button-${props.size}`);
  }
  
  // Дополнительные классы
  if (props.fullWidth) {
    classes.push('full-width');
  }
  
  if (props.loading) {
    classes.push('ds-button-loading');
  }
  
  if (props.icon) {
    classes.push('has-icon');
  }
  
  return classes.join(' ');
});

// Обработчик клика
const onClick = (event: MouseEvent) => {
  if (!props.loading && !props.disabled) {
    emit('click', event);
  }
};
</script>

<style>
/* Дополнительные стили к тем, что в form-components.css */
.ds-button-loading {
  cursor: wait;
  opacity: 0.8;
}

.ds-button .ds-loader {
  margin-right: 8px;
}

.has-icon .button-icon {
  margin-right: 8px;
}

.ds-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style> 