import { inject, computed } from 'vue';
import type { DesignSystemVars } from '@/plugins/designSystem';

/**
 * Хук для доступа к переменным дизайн-системы в компонентах
 */
export function useDesignSystem() {
  // Получаем дизайн-систему из provide/inject контекста
  const designSystem = inject<DesignSystemVars>('designSystem');
  
  if (!designSystem) {
    console.warn('DesignSystem не найден в контексте. Убедитесь, что DesignSystemProvider правильно настроен.');
    
    // Возвращаем значения по умолчанию, если дизайн-система не найдена
    return {
      colors: {
        primary: '#ff67e7',
        primaryDark: '#ec407a',
        primaryLight: '#ffcaf8',
        // ... и т.д.
      },
      // Другие значения по умолчанию...
      
      // Вспомогательные функции
      isDarkMode: computed(() => false),
      isMobileView: computed(() => window.innerWidth < 768)
    };
  }
  
  // Вычисляемое свойство для определения темного режима
  const isDarkMode = computed(() => {
    // Проверка на предпочтения пользователя или настройки приложения
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  
  // Вычисляемое свойство для мобильного вида
  const isMobileView = computed(() => {
    return window.innerWidth < 768;
  });
  
  return {
    ...designSystem,
    isDarkMode,
    isMobileView
  };
}

/**
 * Хук для доступа к утилитам и классам дизайн-системы
 */
export function useDesignClasses() {
  // Функция для генерации классов компонентов
  const getComponentClass = (componentName: string, variant?: string, size?: string) => {
    let className = `ds-${componentName}`;
    
    if (variant) {
      className += ` ds-${componentName}-${variant}`;
    }
    
    if (size) {
      className += ` ds-${componentName}-${size}`;
    }
    
    return className;
  };
  
  // Функция для генерации классов утилит
  const getUtilityClass = (utility: string, value?: string) => {
    if (value) {
      return `ds-${utility}-${value}`;
    }
    
    return `ds-${utility}`;
  };
  
  // Предоставляем готовые классы для распространенных компонентов
  const buttonClass = (variant = 'primary', size = 'md') => getComponentClass('button', variant, size);
  const inputClass = (variant = 'default', size = 'md') => getComponentClass('form-input', variant, size);
  const cardClass = (variant = 'default') => getComponentClass('card', variant);
  const textClass = (size = 'md') => getComponentClass('text', undefined, size);
  
  return {
    getComponentClass,
    getUtilityClass,
    buttonClass,
    inputClass,
    cardClass,
    textClass
  };
} 