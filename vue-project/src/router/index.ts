import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useMainStore } from '@/store'
import { TelegramService } from '@/services/telegram'
import { getToastManager } from '@/plugins/toastManager'

// Объявляем тип для telegramWebApp
declare global {
  interface Window {
    __VUE_TOASTIFICATION__?: {
      clear?: () => void;
      dismiss?: () => void;
    };
    __SIMPLE_TOAST__?: {
      success: (message: string, duration?: number) => number;
      error: (message: string, duration?: number) => number;
      info: (message: string, duration?: number) => number;
      warning: (message: string, duration?: number) => number;
      removeAll: () => void;
    };
    cleanupDOM?: () => void;
  }
}

import Home from '../views/Home.vue'
import LessonPlan from '../components/LessonPlan.vue'
import Exercises from '../components/Exercises.vue'
import Games from '../components/Games.vue'
import ImageGeneration from '../components/ImageGeneration.vue'
import VideoTranscriptWrapper from '../components/VideoTranscriptWrapper.vue'
import CourseGeneratorView from '@/views/CourseGeneratorView.vue'
import AIChatAssistantView from '@/views/AIChatAssistantView.vue'
import ConceptExplainerView from '@/views/ConceptExplainerView.vue'
import ProfileView from '@/views/ProfileView.vue'
import TextAnalyzer from '../components/TextAnalyzer.vue'

 // Импорт админских компонентов
import AdminLayout from '../views/Admin.vue'
import Dashboard from '../components/admin/Dashboard.vue'
import Users from '../components/admin/Users.vue'
import Generations from '../components/admin/Generations.vue'
import Tariffs from '../components/admin/Tariffs.vue'
import Achievements from '../components/admin/Achievements.vue'
import Content from '../components/admin/Content.vue'
import Analytics from '../components/admin/Analytics.vue'
import Settings from '../components/admin/Settings.vue'
import Promocodes from '../components/admin/Promocodes.vue'
import SystemSettings from '../components/admin/settings/SystemSettings.vue'
import FeatureUsage from '../components/admin/FeatureUsageAnalytics.vue'
import LessonPlanView from '@/views/LessonPlanView.vue'
import Courses from '@/views/Courses.vue'
import Error from '@/views/Error.vue'


// Проверка прав администратора
const adminGuard = (to: any, from: any, next: any) => {
  const store = useMainStore()
  if (!store.isAdmin) {
    next({ name: 'home' })
    return
  }
  next()
}

// Проверка доступа к премиум функциям
const premiumGuard = (to: any, from: any, next: any) => {
  const store = useMainStore()

  // Проверяем, загружены ли данные пользователя
  if (!store.user) {
    // Если данные не загружены, перенаправляем на главную
    next({ name: 'home' })
    return
  }

  // Проверяем, является ли пользователь админом или имеет безлимитную роль
  const isUnlimitedUser = store.user.role === 'admin' ||
                         store.user.role === 'friend' ||
                         store.user.role === 'mod'

  // Проверяем, есть ли у пользователя Premium тариф
  const hasPremiumTariff = store.user.tariff === 'tariff_6'

  if (!isUnlimitedUser && !hasPremiumTariff) {
    // Если нет доступа, перенаправляем на главную с сообщением
    store.setError('Для доступа к этой функции требуется Premium тариф')
    next({ name: 'home' })
    return
  }

  next()
}

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/lesson-plan',
    name: 'lessonPlan',
    component: LessonPlan,
    meta: { requiresAuth: true }
  },
  {
    path: '/courses/create',
    name: 'course-create',
    component: CourseGeneratorView,
    meta: {
      requiresAuth: true,
      requiresPremium: true,
      title: 'Генератор курсов уроков'
    },
    alias: '/lesson-plan-detailed',
    beforeEnter: premiumGuard
  },
  {
    path: '/ai-assistant',
    name: 'ai-assistant',
    component: AIChatAssistantView,
    meta: {
      requiresAuth: true,
      requiresPremium: true,
      title: 'AI-ассистент для репетиторов'
    },
    beforeEnter: premiumGuard
  },
  {
    path: '/concept-explainer',
    name: 'concept-explainer',
    component: ConceptExplainerView,
    meta: {
      requiresAuth: true,
      title: 'Объяснение сложных концепций'
    }
  },
  {
    path: '/exercises',
    name: 'exercises',
    component: Exercises,
    meta: { requiresAuth: true }
  },
  {
    path: '/games',
    name: 'games',
    component: Games,
    meta: { requiresAuth: true }
  },
  {
    path: '/image-generation',
    name: 'imageGeneration',
    component: ImageGeneration,
    meta: { requiresAuth: true }
  },
  {
    path: '/video-transcript',
    name: 'videoTranscript',
    component: VideoTranscriptWrapper,
    meta: { requiresAuth: true }
  },
  {
    path: '/modes',
    name: 'modes',
    component: () => import('../views/Modes.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/courses',
    name: 'courses',
    component: Courses,
    meta: { requiresAuth: true }
  },
  {
    path: '/free-lessons',
    name: 'freeLessons',
    component: () => import('../views/FreeLessons.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: {
      requiresAuth: true,
      title: 'Профиль пользователя'
    }
  },
  {
    path: '/text-analyzer',
    name: 'textAnalyzer',
    component: TextAnalyzer,
    meta: {
      requiresAuth: true,
      title: 'Текст-тренажер'
    }
  },
  {
    path: '/error',
    name: 'error',
    component: Error
  },

  // Административные маршруты
  // Админские маршруты
  {
    path: '/admin',
    name: 'admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: Dashboard
      },
      {
        path: 'users',
        name: 'admin-users',
        component: Users
      },
      {
        path: 'generations',
        name: 'admin-generations',
        component: Generations
      },
      {
        path: 'tariffs',
        name: 'admin-tariffs',
        component: Tariffs
      },
      {
        path: 'achievements',
        name: 'admin-achievements',
        component: Achievements
      },
      {
        path: 'content',
        name: 'admin-content',
        component: Content
      },
      {
        path: 'analytics',
        name: 'admin-analytics',
        component: Analytics
      },
      {
        path: 'settings',
        name: 'admin-settings',
        component: Settings
      },
      {
        path: 'promocodes',
        name: 'admin-promocodes',
        component: Promocodes
      },
      {
        path: 'system-settings',
        name: 'admin-system-settings',
        component: SystemSettings
      },
      {
        path: 'feature-usage',
        name: 'admin-feature-usage',
        component: FeatureUsage
      }
    ]
  },
  // Маршрут для ошибки 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Очистка тостов и других ресурсов перед переходом
router.beforeEach((to, from, next) => {
  console.log(`Переход НАЧАТ: с "${from.path}" на "${to.path}"`)

  // Очищаем тосты при каждой навигации
  const toastManager = getToastManager();
  toastManager.clearAll();

  // Устанавливаем мета-информацию в локальное хранилище для восстановления состояния при необходимости
  if (from.name) {
    localStorage.setItem('lastRoute', JSON.stringify({
      name: from.name,
      path: from.path,
      timestamp: Date.now()
    }));
  }

  // Специальная обработка при переходе с проблемных страниц
  if (from.path.includes('lesson-plan')) {
    console.log('Router: Обнаружен переход с lesson-plan страницы')

    // Функция для безопасной очистки DOM
    const safeCleanup = () => {
      try {
        // 1. Очищаем все toast контейнеры
        if (window.__SIMPLE_TOAST__) {
          window.__SIMPLE_TOAST__.removeAll();
        }

        // 2. Принудительно удаляем проблемные элементы
        [
          '.lesson-plan-container',
          '.simple-toast-container',
          '.v-toastification',
          '[data-component="lesson-plan"]'
        ].forEach(selector => {
          const elements = document.querySelectorAll(selector);
          elements.forEach(el => {
            try {
              // Сначала делаем элемент невидимым
              const htmlEl = el as HTMLElement;
              htmlEl.style.display = 'none';
              htmlEl.style.opacity = '0';
              htmlEl.style.visibility = 'hidden';
              htmlEl.style.position = 'absolute';
              htmlEl.style.zIndex = '-9999';
              htmlEl.style.pointerEvents = 'none';
              htmlEl.style.width = '0';
              htmlEl.style.height = '0';

              // Затем пытаемся удалить элемент
        setTimeout(() => {
          try {
                  el.remove();
                  console.log(`Router: Удален элемент ${selector}`);
                } catch (removalError) {
                  console.error(`Router: Ошибка при удалении элемента ${selector}:`, removalError);
          }
        }, 50);
      } catch (e) {
              console.error(`Router: Ошибка при обработке элемента ${selector}:`, e);
            }
          });
        });

        // 3. Восстанавливаем видимость основного контейнера
        const mainContent = document.querySelector('.main-content-container');
        if (mainContent) {
          const mainEl = mainContent as HTMLElement;
          mainEl.style.display = 'block';
          mainEl.style.visibility = 'visible';
          mainEl.style.opacity = '1';
          mainEl.style.zIndex = 'var(--z-index-content)';
        }

        console.log('Router: Очистка DOM завершена');
      } catch (e) {
        console.error('Router: Ошибка при очистке DOM:', e);
      }
    };

    // Выполняем очистку DOM асинхронно
    setTimeout(safeCleanup, 0);
  }

  next();
})

// Авторизационный guard
router.beforeEach(async (to, from) => {
  const store = useMainStore();

  const publicRoutes = ['error', 'not-found'];
  if (publicRoutes.includes(to.name as string)) {
    return true;
  }

  try {
    if (!store.isInitialized) {
      await store.initializeApp();
    }

    // Выведем логи для отладки
    console.log('Auth state:', {
      isInitialized: store.isInitialized,
      authenticated: store.authenticated,
      isAuthenticated: store.isAuthenticated,
      user: store.user
    });

    // Для страниц требующих аутентификации
    if (to.meta.requiresAuth && !store.isAuthenticated) {
      store.setError('Требуется авторизация')
      return { name: 'home' }
    }

    // Доступ к администраторским страницам
    if (to.meta.requiresAdmin && !store.isAdmin) {
      store.setError('У вас нет доступа к этой странице')
      return { name: 'home' }
    }

    return true
  } catch (e) {
    console.error('Ошибка при проверке авторизации:', e)
    store.setError('Произошла ошибка при проверке авторизации')
    return { name: 'error' }
  }
});

// Обработчик ошибок роутера
router.onError((e) => {
  console.log('Router error:', e);
  const store = useMainStore();
  store.setError(typeof e === 'string' ? e : 'Navigation error occurred');
});

// Принудительно обновляем стили app
const app = document.querySelector('#app');
if (app) {
  (app as HTMLElement).style.display = 'block';
  (app as HTMLElement).style.visibility = 'visible';
  (app as HTMLElement).style.opacity = '1';
}

// Добавляем обработчик после завершения перехода
router.afterEach((to, from) => {
  // Сохраняем информацию о текущем маршруте
  localStorage.setItem('currentRoute', JSON.stringify({
    name: to.name,
    path: to.path,
    timestamp: Date.now()
  }));

  // Управление кнопкой "Назад" в Telegram
  try {
    // Показываем кнопку "Назад" на всех страницах, кроме главной
    if (to.path !== '/' && to.path !== '') {
      console.log('Router: показываем кнопку "Назад" на:', to.path);
      TelegramService.forceShowBackButton();
    } else {
      console.log('Router: скрываем кнопку "Назад" на главной странице');
      TelegramService.forceHideBackButton();
    }
  } catch (err) {
    console.error('Router: ошибка при управлении кнопкой "Назад":', err);
  }

  // Если переход на страницу modes, проверяем компонент
  if (to.path.includes('modes')) {
    console.log('Переход на страницу Modes, проверяем компонент');

    // Используем setTimeout, чтобы дать Vue время для рендеринга
    setTimeout(() => {
      const modesView = document.querySelector('.modes-view');
      if (modesView) {
        console.log('modes-view найден после перехода');
      } else {
        console.log('modes-view НЕ найден после перехода');
      }
    }, 100);
  }
});

export default router
