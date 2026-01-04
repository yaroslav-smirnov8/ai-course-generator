<template>
  <div class="simple-toast-container" :class="{ 'has-toasts': toasts.length > 0 }">
    <TransitionGroup name="simple-toast">
      <div 
        v-for="toast in toasts" 
        :key="toast.id" 
        class="simple-toast" 
        :class="[`simple-toast--${toast.type}`]"
        @click="removeToast(toast.id)"
      >
        <div class="simple-toast__content">
          {{ toast.message }}
        </div>
        <button class="simple-toast__close" @click.stop="removeToast(toast.id)">
          &times;
        </button>
        <div 
          class="simple-toast__progress" 
          :style="{ animationDuration: `${toast.duration}ms` }"
        ></div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration: number;
}

const toasts = ref<Toast[]>([])
let toastCounter = 0
const timeouts: number[] = []

// Экспортируем методы для использования в других компонентах
const showToast = (
  message: string, 
  type: Toast['type'] = 'info', 
  duration: number = 3000
) => {
  const id = toastCounter++
  toasts.value.push({ id, message, type, duration })
  
  const timeout = window.setTimeout(() => {
    removeToast(id)
  }, duration)
  
  timeouts.push(timeout)
  
  return id
}

const removeToast = (id: number) => {
  const index = toasts.value.findIndex(toast => toast.id === id)
  if (index !== -1) {
    toasts.value.splice(index, 1)
  }
}

// Очищаем таймауты при размонтировании компонента
onUnmounted(() => {
  // Очищаем все таймауты
  timeouts.forEach(timeout => clearTimeout(timeout))
  timeouts.length = 0
  
  // Удаляем все тосты
  toasts.value = []
  
  // Сбрасываем счетчик
  toastCounter = 0
  
  console.log('SimpleToast: компонент размонтирован, все ресурсы очищены')
})

// Создаем глобальный сервис тостов
const createToastService = () => {
  const service = {
    success: (message: string, duration: number = 3000) => showToast(message, 'success', duration),
    error: (message: string, duration: number = 4000) => showToast(message, 'error', duration),
    info: (message: string, duration: number = 3000) => showToast(message, 'info', duration),
    warning: (message: string, duration: number = 3500) => showToast(message, 'warning', duration),
    removeAll: () => { 
      // Полное очищение массива тостов
      toasts.value = [];
      
      // Очистка всех таймаутов
      timeouts.forEach(timeout => clearTimeout(timeout));
      timeouts.length = 0;
      
      // Сбрасываем счетчик
      toastCounter = 0;
      
      console.log('SimpleToast: все тосты очищены');
    }
  }
  
  // Устанавливаем глобально
  window.__SIMPLE_TOAST__ = service
  
  return service
}

// Экспортируем сервис тостов
onMounted(() => {
  createToastService()
  
  // Добавляем обработчики событий истории для очистки тостов при навигации
  window.addEventListener('popstate', () => {
    if (window.__SIMPLE_TOAST__) {
      window.__SIMPLE_TOAST__.removeAll();
    }
  });
})

// Объявляем тип для Window
declare global {
  interface Window {
    __SIMPLE_TOAST__?: {
      success: (message: string, duration?: number) => number;
      error: (message: string, duration?: number) => number;
      info: (message: string, duration?: number) => number;
      warning: (message: string, duration?: number) => number;
      removeAll: () => void;
    }
  }
}
</script>

<style scoped>
.simple-toast-container {
  position: fixed;
  bottom: var(--toast-bottom-offset, 20px);
  right: var(--toast-right-offset, 20px);
  max-width: var(--toast-max-width, 350px);
  z-index: var(--z-index-toast, 40);
  pointer-events: none;
  width: auto;
  height: 0;
  overflow: visible;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.simple-toast {
  margin-top: 10px;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: white;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  pointer-events: auto;
  opacity: 0.95;
  transition: all 0.3s ease;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.simple-toast:hover {
  opacity: 1;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.simple-toast--success {
  background-color: var(--toast-success-color, #4caf50);
}

.simple-toast--error {
  background-color: var(--toast-error-color, #f44336);
}

.simple-toast--info {
  background-color: var(--toast-info-color, #2196f3);
}

.simple-toast--warning {
  background-color: var(--toast-warning-color, #ff9800);
}

.simple-toast__content {
  margin-right: 25px;
  font-size: 14px;
  line-height: 1.4;
  word-break: break-word;
}

.simple-toast__close {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 20px;
  border: none;
  background: transparent;
  color: white;
  opacity: 0.7;
  cursor: pointer;
  transition: opacity 0.2s;
  line-height: 1;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.simple-toast__close:hover {
  opacity: 1;
}

.simple-toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  width: 100%;
  background-color: rgba(255, 255, 255, 0.4);
  animation: simple-toast-progress linear forwards;
  transform-origin: left;
}

@keyframes simple-toast-progress {
  0% {
    transform: scaleX(1);
  }
  100% {
    transform: scaleX(0);
  }
}

/* Переходы */
.simple-toast-enter-active,
.simple-toast-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
  max-height: 400px;
}

.simple-toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.simple-toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
  max-height: 0;
}

/* Медиа-запросы для адаптивности */
@media (max-width: 768px) {
  .simple-toast-container {
    left: var(--toast-mobile-left-offset, 10px);
    right: var(--toast-mobile-right-offset, 10px);
    max-width: var(--toast-mobile-max-width, calc(100% - 20px));
    bottom: var(--toast-mobile-bottom-offset, 10px);
  }
}
</style> 