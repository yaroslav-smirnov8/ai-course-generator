<template>
  <div>
    <slot v-if="!error"></slot>
    <div v-else class="error-boundary p-4 bg-red-500/10 rounded-lg m-4">
      <h2 class="text-xl font-bold text-red-500 mb-2">Произошла ошибка</h2>
      <p class="text-red-400 mb-4">{{ error.message }}</p>
      <div class="flex space-x-4">
        <button
          @click="resetError"
          class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          Попробовать снова
        </button>
        <button
          @click="goHome"
          class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Вернуться на главную
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const error = ref<Error | null>(null)

onErrorCaptured((err: Error) => {
  console.error('ErrorBoundary перехватил ошибку:', err)
  error.value = err
  
  // Проверяем, связана ли ошибка с DOM-операциями
  const isDOMError = err.message.includes('null') && 
                     (err.message.includes('insertBefore') || 
                      err.message.includes('appendChild') || 
                      err.message.includes('removeChild'))
  
  if (isDOMError) {
    console.warn('Обнаружена ошибка DOM-операции, выполняем глубокую очистку...')
    
    // Выполняем глубокую очистку DOM
    setTimeout(() => {
      // Очищаем проблемные контейнеры
      const problematicSelectors = [
        '.lesson-plan-container',
        '[data-component="lesson-plan"]',
        '.planet-background',
        '.simple-toast-container',
        '.form-group',
        '.title-form-group',
        '.generation-form',
        '.result-container',
        '.plan-content'
      ]
      
      problematicSelectors.forEach(selector => {
        try {
          const elements = document.querySelectorAll(selector)
          if (elements.length > 0) {
            console.warn(`Обнаружено ${elements.length} проблемных элементов ${selector}. Скрываем...`)
            elements.forEach(el => {
              try {
                // ВАЖНО: Только скрываем элемент, но не удаляем его
                // Это предотвращает ошибку "Cannot read properties of null (reading 'insertBefore')"
                if (el instanceof HTMLElement) {
                  el.style.display = 'none'
                  el.style.visibility = 'hidden'
                  el.style.opacity = '0'
                  el.style.pointerEvents = 'none'
                  el.style.zIndex = '-9999'
                  el.style.position = 'absolute'
                  el.style.left = '-9999px'
                  el.style.top = '-9999px'
                  el.style.width = '0'
                  el.style.height = '0'
                  el.style.overflow = 'hidden'
                }
              } catch (e) {
                console.error(`Ошибка при скрытии элемента ${selector}:`, e)
              }
            })
          }
        } catch (e) {
          console.error(`Ошибка при поиске элементов ${selector}:`, e)
        }
      })
      
      // Вызываем глобальную функцию очистки DOM, если она существует
      if (typeof window.cleanupDOM === 'function') {
        try {
          window.cleanupDOM()
          console.log('Вызвана глобальная функция очистки DOM')
        } catch (e) {
          console.error('Ошибка при вызове глобальной функции очистки DOM:', e)
        }
      }
      
      // Если ошибка связана с переходом на modes, пытаемся восстановить компонент
      const currentPath = router.currentRoute.value.path
      if (currentPath.includes('modes')) {
        console.log('Обнаружен переход на modes, пытаемся восстановить компонент')
        
        // Скрываем ErrorBoundary
        const errorBoundaryEl = document.querySelector('.error-boundary')
        if (errorBoundaryEl && errorBoundaryEl instanceof HTMLElement) {
          errorBoundaryEl.style.display = 'none'
        }
        
        // Показываем modes-view
        const modesView = document.querySelector('.modes-view')
        if (modesView && modesView instanceof HTMLElement) {
          modesView.style.display = 'block'
          modesView.style.visibility = 'visible'
          modesView.style.opacity = '1'
          modesView.style.zIndex = '30'
          console.log('Принудительно восстановлена видимость modes-view')
        }
        
        // Сбрасываем ошибку
        setTimeout(() => {
          error.value = null
        }, 100)
      }
    }, 0)
  }
  
  return false // Предотвращаем всплытие ошибки
})

// При монтировании компонента проверяем DOM
onMounted(() => {
  // Очищаем потенциальные мусорные контейнеры
  setTimeout(() => {
    const containers = document.querySelectorAll('.lesson-plan-container')
    const currentRoute = router.currentRoute.value.path
    
    // Если мы не на страницах с этими контейнерами, значит они остаточные
    if (currentRoute !== '/exercises' && currentRoute !== '/lesson-plan' && currentRoute !== '/lesson-plan-detailed') {
      if (containers.length > 0) {
        console.log(`ErrorBoundary: найдено ${containers.length} нежелательных контейнеров`)
        containers.forEach(container => {
          try {
            // ВАЖНО: Только скрываем элемент, но не удаляем его
            if (container instanceof HTMLElement) {
              container.style.display = 'none'
              container.style.visibility = 'hidden'
              container.style.opacity = '0'
              container.style.pointerEvents = 'none'
              container.style.zIndex = '-9999'
              container.style.position = 'absolute'
              container.style.left = '-9999px'
              container.style.top = '-9999px'
              container.style.width = '0'
              container.style.height = '0'
              container.style.overflow = 'hidden'
              console.log('ErrorBoundary: скрыт нежелательный контейнер')
            }
          } catch (e) {
            console.error('Ошибка при скрытии контейнера:', e)
          }
        })
      }
    }
  }, 200)
})

const resetError = () => {
  error.value = null
  router.go(0) // Перезагружаем текущий маршрут
}

const goHome = () => {
  error.value = null
  router.push('/') // Переходим на главную страницу
}
</script>
