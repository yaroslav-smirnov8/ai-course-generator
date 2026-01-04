<template>
  <div class="ds-form-group">
    <label v-if="label" :for="id" class="ds-form-label">{{ label }}</label>
    <select
      :id="id"
      :value="modelValue"
      @change="onChange"
      class="ds-form-select"
      :disabled="disabled"
    >
      <option v-if="placeholder" value="" disabled selected>{{ placeholder }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <div v-if="helperText" class="ds-form-helper">{{ helperText }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface SelectOption {
  value: string;
  label: string;
}

// Определяем props компонента
const props = defineProps<{
  modelValue: string;
  options: SelectOption[];
  label?: string;
  id?: string;
  placeholder?: string;
  helperText?: string;
  disabled?: boolean;
}>();

// Определяем события
const emit = defineEmits(['update:modelValue']);

// Генерируем уникальный ID, если он не предоставлен
const id = computed(() => props.id || `select-${Math.random().toString(36).substring(2, 9)}`);

// Обработчик изменения
const onChange = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
};
</script>

<style>
/* Стили находятся в form-components.css */
</style> 