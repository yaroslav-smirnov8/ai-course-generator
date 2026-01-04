import type { Router } from 'vue-router';
import { toastService } from '@/services/toastService';

/**
 * Менеджер тостов, более безопасная версия
 */
export class ToastManager {
  // Singleton экземпляр
  private static instance: ToastManager;
  
  // Приватный конструктор для Singleton
  private constructor() {}
  
  // Получение экземпляра менеджера
  public static getInstance(): ToastManager {
    if (!ToastManager.instance) {
      ToastManager.instance = new ToastManager();
    }
    return ToastManager.instance;
  }
  
  // Очистка всех тостов
  public clearAll(): void {
    // Используем глобальный объект SimpleToast для очистки
    if (window.__SIMPLE_TOAST__ && typeof window.__SIMPLE_TOAST__.removeAll === 'function') {
      window.__SIMPLE_TOAST__.removeAll();
      console.log('ToastManager: вызван removeAll для __SIMPLE_TOAST__');
    } else {
      // Запасной вариант для старой реализации
      if (window.__VUE_TOASTIFICATION__) {
        if (typeof window.__VUE_TOASTIFICATION__.clear === 'function') {
          window.__VUE_TOASTIFICATION__.clear();
          console.log('ToastManager: вызван clear для __VUE_TOASTIFICATION__');
        } else if (typeof window.__VUE_TOASTIFICATION__.dismiss === 'function') {
          window.__VUE_TOASTIFICATION__.dismiss();
          console.log('ToastManager: вызван dismiss для __VUE_TOASTIFICATION__');
        }
      }
    }
  }
  
  // Методы для показа разных типов тостов
  public success(message: string, duration: number = 3000): void {
    toastService.success(message, duration);
  }
  
  public error(message: string, duration: number = 4000): void {
    toastService.error(message, duration);
  }
  
  public info(message: string, duration: number = 3000): void {
    toastService.info(message, duration);
  }
  
  public warning(message: string, duration: number = 3500): void {
    toastService.warning(message, duration);
  }
  
  // Добавление обработчиков для автоматической очистки при навигации
  public setupRouterGuards(router: Router): void {
    router.beforeEach((to, from, next) => {
      // Очищаем все тосты при каждой навигации
      this.clearAll();
      next();
    });
  }
}

// Экспортируем функцию для получения экземпляра
export const getToastManager = () => ToastManager.getInstance();

// Объявляем глобальный тип для тостов
declare global {
  interface Window {
    __SIMPLE_TOAST__?: {
      success: (message: string, duration?: number) => number;
      error: (message: string, duration?: number) => number;
      info: (message: string, duration?: number) => number;
      warning: (message: string, duration?: number) => number;
      removeAll: () => void;
    };
  }
} 