// src/composables/useTelegramApp.ts
import { ref, onMounted, onUnmounted } from 'vue'
import type { Ref } from 'vue'
import { TelegramService } from '@/services/telegram'
import type { TelegramUser, TelegramWebAppTheme } from '@/types'
import { useMainStore } from '@/store'
import { useRouter } from 'vue-router'

// Определяем интерфейс для Telegram WebApp
interface TelegramWebApp {
  BackButton: {
    show: () => void
    hide: () => void
    onClick: (callback: () => void) => void
    offClick: (callback: () => void) => void
    isVisible: boolean
  }
  MainButton: any
  BottomButton: any
  SecondaryButton: any
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
  sendData: (data: any) => void
  ready: () => void
  expand: () => void
  close: () => void
  isVersionAtLeast: (version: string) => boolean
  setHeaderColor: (color: string) => void
  setBackgroundColor: (color: string) => void
  enableClosingConfirmation: () => void
  disableClosingConfirmation: () => void
  onEvent: (eventType: string, callback: any) => void
  offEvent: (eventType: string, callback: any) => void
  platform: string
  version: string
  colorScheme: string
  themeParams: any
  initData: string
  initDataUnsafe: any
}

// Определяем глобальный объект Telegram
declare global {
  interface Window {
    Telegram: {
      WebApp: TelegramWebApp
    }
  }
}

export function useTelegramApp() {
  const isReady = ref(false)
  const error = ref<string | null>(null)
  const user = ref<TelegramUser | null>(null)
  const theme = ref<TelegramWebAppTheme | null>(null)
  const store = useMainStore()
  const router = useRouter()
  const isTelegramWebApp = ref(false)
  const webApp = ref<TelegramWebApp | null>(null)
  const sessionStartTime = ref<Date | null>(null)
  const appLaunches = ref(0)
  const currentRoute = ref('')
  const routeHistory = ref<string[]>([])

  // Обработчики событий
  const handleThemeChange = () => {
    theme.value = TelegramService.getTheme()
    updateThemeClasses()
  }

  const handleViewportChange = ({ isStateStable }: { isStateStable: boolean }) => {
    if (isStateStable) {
      // Дополнительная логика при изменении viewport
      console.log('Viewport changed and stabilized')
    }
  }

  const updateThemeClasses = () => {
    if (theme.value) {
      document.documentElement.style.setProperty('--tg-theme-bg-color', theme.value.bg_color)
      document.documentElement.style.setProperty('--tg-theme-text-color', theme.value.text_color)
      document.documentElement.style.setProperty('--tg-theme-hint-color', theme.value.hint_color)
      document.documentElement.style.setProperty('--tg-theme-link-color', theme.value.link_color)
      document.documentElement.style.setProperty('--tg-theme-button-color', theme.value.button_color)
      document.documentElement.style.setProperty('--tg-theme-button-text-color', theme.value.button_text_color)
    }
  }

  // Инициализация Telegram WebApp
  const initTelegramAppFunc = () => {
    if (window.Telegram?.WebApp) {
      webApp.value = window.Telegram.WebApp
      isTelegramWebApp.value = true

      // Сообщаем Telegram, что приложение готово
      webApp.value.ready()

      // Записываем время начала сессии
      sessionStartTime.value = new Date()

      // Увеличиваем счетчик запусков
      const launches = localStorage.getItem('app_launches') || '0'
      appLaunches.value = parseInt(launches) + 1
      localStorage.setItem('app_launches', appLaunches.value.toString())

      // Отправляем статистику запуска в наш store
      trackAppLaunch()

      // Настраиваем отслеживание закрытия приложения
      webApp.value.onEvent('viewportChanged', trackViewportChange)

      // Включаем подтверждение закрытия
      if (webApp.value.isVersionAtLeast('6.2')) {
        webApp.value.enableClosingConfirmation()
      }

      console.log('Telegram WebApp initialized', webApp.value.version)
    } else {
      console.log('Telegram WebApp not available')
    }
  }

  // Управление кнопкой "Назад"
  const setupBackButton = () => {
    if (!webApp.value) return

    try {
      // Проверяем наличие свойства BackButton
      if (!webApp.value.BackButton) {
        console.warn('BackButton is not available in this Telegram WebApp version')
        return
      }

      // Безопасно получаем ссылку на BackButton
      const backButton = webApp.value.BackButton

      // Проверяем наличие метода onClick
      if (typeof backButton.onClick !== 'function') {
        console.warn('BackButton onClick method is not available')
        return
      }

      // Обработчик нажатия на кнопку "Назад"
      const handleBackClick = () => {
        // Проверяем, можем ли мы вернуться назад в истории браузера
        if (window.history.state && window.history.state.back) {
          // Используем встроенный механизм Vue Router для возврата назад
          router.back()
        } else if (routeHistory.value.length > 1) {
          // Удаляем текущий маршрут из истории
          routeHistory.value.pop()
          // Переходим на предыдущий маршрут
          const previousRoute = routeHistory.value[routeHistory.value.length - 1]
          router.push(previousRoute)
        } else if (webApp.value) {
          // Если истории нет, просто закрываем приложение
          webApp.value.close()
        }
      }

      // Устанавливаем обработчик
      backButton.onClick(handleBackClick)
    } catch (err) {
      console.error('Error setting up back button:', err)
    }
  }

  // Отслеживание изменения маршрута
  const trackRouteChange = (to: string) => {
    if (to === currentRoute.value) return

    // Сохраняем предыдущий маршрут в историю
    if (currentRoute.value) {
      routeHistory.value.push(currentRoute.value)
    }

    // Обновляем текущий маршрут
    currentRoute.value = to

    // Управляем видимостью кнопки "Назад"
    updateBackButtonVisibility()

    // Отправляем статистику перехода
    trackPageViewFunc(to)
  }

  // Обновление видимости кнопки "Назад"
  const updateBackButtonVisibility = () => {
    if (!webApp.value) return

    try {
      // Проверяем наличие свойства BackButton
      if (!webApp.value.BackButton) {
        console.warn('BackButton is not available in this Telegram WebApp version')
        return
      }

      // Безопасно получаем ссылку на BackButton
      const backButton = webApp.value.BackButton

      // Проверяем наличие методов show и hide
      if (typeof backButton.show !== 'function' || typeof backButton.hide !== 'function') {
        console.warn('BackButton methods are not available')
        return
      }

      // Показываем кнопку "Назад" на всех страницах, кроме главной
      if (currentRoute.value !== '/' && currentRoute.value !== '') {
        console.log('Показываем кнопку "Назад" на маршруте:', currentRoute.value)
        backButton.show()
      } else {
        console.log('Скрываем кнопку "Назад" на главной странице')
        backButton.hide()
      }
    } catch (err) {
      console.error('Error updating back button visibility:', err)
    }
  }

  // Отслеживание запуска приложения
  const trackAppLaunch = async () => {
    if (!webApp.value) return

    try {
      // Получаем данные пользователя из Telegram
      const userData = webApp.value.initDataUnsafe?.user

      // Отправляем статистику в наш сервис
      await store.trackAppUsage({
        event: 'app_launch',
        platform: webApp.value.platform,
        version: webApp.value.version,
        user_id: userData?.id || 'unknown',
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error('Error tracking app launch:', error)
    }
  }

  // Отслеживание просмотра страницы
  const trackPageViewFunc = async (route: string) => {
    if (!webApp.value) return

    try {
      // Получаем данные пользователя из Telegram
      const userData = webApp.value.initDataUnsafe?.user

      // Отправляем статистику в наш сервис
      await store.trackAppUsage({
        event: 'page_view',
        page: route,
        platform: webApp.value.platform,
        version: webApp.value.version,
        user_id: userData?.id || 'unknown',
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error('Error tracking page view:', error)
    }
  }

  // Отслеживание действия пользователя
  const trackUserAction = async (action: string, details: any = {}) => {
    if (!webApp.value) return

    try {
      // Получаем данные пользователя из Telegram
      const userData = webApp.value.initDataUnsafe?.user

      // Отправляем статистику в наш сервис
      await store.trackAppUsage({
        event: 'user_action',
        action,
        details,
        platform: webApp.value.platform,
        version: webApp.value.version,
        user_id: userData?.id || 'unknown',
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error('Error tracking user action:', error)
    }
  }

  // Отслеживание времени использования
  const trackSessionDuration = async () => {
    if (!webApp.value || !sessionStartTime.value) return

    try {
      // Вычисляем длительность сессии
      const endTime = new Date()
      const durationMs = endTime.getTime() - sessionStartTime.value.getTime()
      const durationSeconds = Math.round(durationMs / 1000)

      // Получаем данные пользователя из Telegram
      const userData = webApp.value.initDataUnsafe?.user

      // Отправляем статистику в наш сервис
      await store.trackAppUsage({
        event: 'session_end',
        duration_seconds: durationSeconds,
        platform: webApp.value.platform,
        version: webApp.value.version,
        user_id: userData?.id || 'unknown',
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error('Error tracking session duration:', error)
    }
  }

  // Обработчик изменения viewport (для отслеживания закрытия приложения)
  const trackViewportChange = () => {
    if (!webApp.value) return

    // Если высота viewport стала меньше, возможно приложение закрывается
    if (webApp.value.viewportHeight < 100) {
      trackSessionDuration()
    }
  }

  onMounted(async () => {
    try {
      // Инициализация Telegram WebApp
      TelegramService.initialize()

      // Получаем начальные данные
      user.value = TelegramService.getUser()
      theme.value = TelegramService.getTheme()

      // Устанавливаем тему
      updateThemeClasses()

      // Добавляем слушатели событий
      TelegramService.onEvent('themeChanged', handleThemeChange)
      TelegramService.onEvent('viewportChanged', handleViewportChange)

      // Устанавливаем флаг готовности
      isReady.value = true

      // Пытаемся инициализировать store
      try {
        await store.initializeApp()
      } catch (storeError) {
        console.error('Store initialization error:', storeError)
      }

      initTelegramAppFunc()

      // Добавляем задержку перед настройкой кнопки "Назад"
      // Увеличиваем задержку до 1000 мс для полной инициализации Telegram Web App
      setTimeout(() => {
        try {
          setupBackButton()
        } catch (backButtonError) {
          console.error('Back button setup error:', backButtonError)
        }
      }, 1000)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to initialize Telegram WebApp'
      console.error('Telegram WebApp initialization error:', err)
    }
  })

  onUnmounted(() => {
    // Удаляем слушатели событий при уничтожении компонента
    if (TelegramService.isAvailable()) {
      TelegramService.offEvent('themeChanged', handleThemeChange)
      TelegramService.offEvent('viewportChanged', handleViewportChange)
    }

    // Отписываемся от событий при размонтировании компонента
    if (webApp.value) {
      try {
        webApp.value.offEvent('viewportChanged', trackViewportChange)

        // Безопасное отключение обработчика кнопки "Назад"
        try {
          // Проверяем наличие свойства BackButton и метода offClick
          if (webApp.value.BackButton && typeof webApp.value.BackButton.offClick === 'function') {
            webApp.value.BackButton.offClick(() => {})
          }
        } catch (err) {
          console.error('Error removing back button handler:', err)
        }

        // Отправляем статистику о длительности сессии
        trackSessionDuration()
      } catch (err) {
        console.error('Error during component unmount:', err)
      }
    }
  })

  // Методы для использования в компонентах
  const showAlert = async (message: string): Promise<void> => {
    return TelegramService.showAlert(message)
  }

  const showConfirm = async (message: string): Promise<boolean> => {
    return TelegramService.showConfirm(message)
  }

  const close = () => {
    TelegramService.close()
  }

  const expand = () => {
    TelegramService.expand()
  }

  const setMainButton = (text: string, color?: string) => {
    if (color) {
      TelegramService.setMainButtonColor(color)
    }
    TelegramService.setMainButtonText(text)
    TelegramService.showMainButton()
  }

  const hideMainButton = () => {
    TelegramService.hideMainButton()
  }

  return {
    // Состояния
    isReady,
    error,
    user,
    theme,
    isTelegramWebApp,
    webApp,
    trackRouteChange,
    trackUserAction,
    appLaunches,

    // Методы
    showAlert,
    showConfirm,
    close,
    expand,
    setMainButton,
    hideMainButton,
  }
}
