import type { Directive, DirectiveBinding } from 'vue'
import { getOptimizedImageUrl } from '@/services/imageOptimizer'

interface LazyLoadOptions {
  threshold?: number
  rootMargin?: string
}

// Карта для хранения оригинальных URL изображений
const srcMap = new WeakMap<HTMLElement, string>()

// Создаем IntersectionObserver один раз для всех элементов
let observer: IntersectionObserver | null = null

const createObserver = (options: LazyLoadOptions = {}) => {
  if (observer) return observer

  const defaultOptions = {
    threshold: 0.1,
    rootMargin: '50px 0px'
  }

  const config = { ...defaultOptions, ...options }

  observer = new IntersectionObserver((entries) => {
    entries.forEach(async (entry) => {
      if (!entry.isIntersecting) return

      const element = entry.target as HTMLImageElement
      const originalSrc = srcMap.get(element)

      if (!originalSrc) return

      try {
        // Получаем оптимизированный URL
        const optimizedSrc = await getOptimizedImageUrl(originalSrc)
        
        // Создаем предзагрузчик изображения
        const preloadImage = new Image()
        preloadImage.onload = () => {
          // Устанавливаем оптимизированный URL и удаляем плейсхолдер
          element.src = optimizedSrc
          element.classList.add('lazy-loaded')
          element.classList.remove('lazy-loading')
          
          // Отключаем наблюдение за элементом
          observer?.unobserve(element)
          srcMap.delete(element)
        }
        
        preloadImage.onerror = () => {
          // В случае ошибки используем оригинальный URL
          element.src = originalSrc
          element.classList.add('lazy-error')
          element.classList.remove('lazy-loading')
          
          // Отключаем наблюдение за элементом
          observer?.unobserve(element)
          srcMap.delete(element)
        }
        
        // Начинаем загрузку
        element.classList.add('lazy-loading')
        preloadImage.src = optimizedSrc
      } catch (error) {
        console.error('Ошибка при оптимизации изображения:', error)
        element.src = originalSrc
        observer?.unobserve(element)
        srcMap.delete(element)
      }
    })
  }, config)

  return observer
}

export const vLazyLoad: Directive = {
  mounted(el: HTMLImageElement, binding: DirectiveBinding) {
    // Сохраняем оригинальный URL
    const originalSrc = binding.value || el.getAttribute('data-src') || el.src
    srcMap.set(el, originalSrc)
    
    // Устанавливаем плейсхолдер
    const placeholder = el.getAttribute('data-placeholder') || 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E'
    el.src = placeholder
    
    // Добавляем класс для стилизации
    el.classList.add('lazy-image')
    
    // Создаем и запускаем наблюдатель
    const options = typeof binding.value === 'object' ? binding.value : {}
    const obs = createObserver(options)
    obs.observe(el)
  },
  
  beforeUnmount(el: HTMLImageElement) {
    // Очищаем ресурсы при удалении элемента
    observer?.unobserve(el)
    srcMap.delete(el)
  },
  
  updated(el: HTMLImageElement, binding: DirectiveBinding) {
    // Если URL изменился, обновляем его
    const newSrc = binding.value || el.getAttribute('data-src')
    const oldSrc = srcMap.get(el)
    
    if (newSrc && newSrc !== oldSrc) {
      srcMap.set(el, newSrc)
      
      // Если элемент уже загружен, сразу обновляем изображение
      if (el.classList.contains('lazy-loaded')) {
        getOptimizedImageUrl(newSrc)
          .then(optimizedSrc => {
            el.src = optimizedSrc
          })
          .catch(() => {
            el.src = newSrc
          })
      }
    }
  }
}

// Экспортируем директиву для использования в приложении
export default vLazyLoad 