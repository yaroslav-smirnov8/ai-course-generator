<template>
  <div class="ds-form-group">
    <label v-if="label" :for="id" class="ds-form-label">{{ label }}</label>
    <textarea
      :id="id"
      :value="modelValue"
      @input="onInput"
      class="ds-form-textarea"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled"
    ></textarea>
    <div v-if="helperText" class="ds-form-helper">{{ helperText }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Определяем props компонента
const props = defineProps<{
  modelValue: string;
  label?: string;
  id?: string;
  placeholder?: string;
  rows?: number;
  helperText?: string;
  disabled?: boolean;
}>();

// Определяем события
const emit = defineEmits(['update:modelValue']);

// Генерируем уникальный ID, если он не предоставлен
const id = computed(() => props.id || `textarea-${Math.random().toString(36).substring(2, 9)}`);

// Обработчик ввода
const onInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement;
  emit('update:modelValue', target.value);
};
</script>

<style>
/* Стили находятся в form-components.css */
</style> 