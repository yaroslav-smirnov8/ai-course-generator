<template>
  <div class="design-system-provider">
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, provide, reactive } from 'vue'
import { initDesignSystem, DesignSystemVars } from '@/plugins/designSystem'

// Инициализация переменных дизайн-системы
const designSystem = reactive<DesignSystemVars>({
  colors: {
    primary: '#ff67e7',
    primaryDark: '#ec407a',
    primaryLight: '#ffcaf8',
    primaryBg: 'rgba(255, 103, 231, 0.2)',
    secondary: '#6a1b9a',
    secondaryLight: '#8e24aa',
    secondaryDark: '#4a148c',
    background: '#13111c',
    backgroundLight: '#1e1a29',
    surface: 'rgba(42, 8, 46, 0.25)',
    surfaceLight: 'rgba(255, 204, 243, 0.7)',
    text: '#ffffff',
    textSecondary: 'rgba(255, 255, 255, 0.7)',
    textDark: '#333333',
    error: '#dc3545',
    success: '#28a745',
    warning: '#ffc107',
    info: '#17a2b8'
  },
  shadows: {
    sm: '0 2px 6px rgba(0, 0, 0, 0.1)',
    md: '0 4px 12px rgba(0, 0, 0, 0.15)',
    lg: '0 6px 18px rgba(0, 0, 0, 0.2)',
    primary: '0 4px 12px rgba(255, 103, 231, 0.3)'
  },
  zIndices: {
    background: -1,
    content: 1,
    header: 100,
    modal: 1000,
    toast: 2000,
    navbar: 100
  },
  radius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '1rem'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.25rem',
    xl: '1.5rem',
    xxl: '2rem'
  },
  transitions: {
    fast: '0.2s',
    normal: '0.3s',
    slow: '0.5s'
  }
})

// Предоставляем дизайн-систему через provide/inject API Vue
provide('designSystem', designSystem)

// Инициализация при монтировании
onMounted(() => {
  // Инициализируем дизайн-систему
  initDesignSystem()
  
  // Добавляем класс для активации стилей системы дизайна на уровне body
  document.body.classList.add('ds-enabled')
})

// Очистка при размонтировании
onUnmounted(() => {
  document.body.classList.remove('ds-enabled')
})
</script>

<style>
.design-system-provider {
  width: 100%;
  height: 100%;
  contain: content;
}
</style> 