<template>
  <!-- Было: -->
  <!-- <div class="app min-h-screen bg-gray-900 text-white"> -->

  <!-- Станет: -->
  <div class="app min-h-screen text-white" :class="appClasses">
    <!-- Loading State -->
    <LoadingScreen v-if="isLoading || !isInitialized" />

    <!-- Access Denied Screen -->
    <AccessDenied
      v-else-if="store.accessDenied"
      :reason="store.accessDenied.reason"
      :channel-url="store.accessDenied.channelUrl"
      :error="store.accessDenied.error"
      @retry="handleRetry"
    />

    <!-- Main Application -->
    <template v-else>
      <main :class="['main-content-container', { 'pb-16': shouldShowBottomNav }]">
        <ErrorBoundary>
          <Suspense>
            <template #default>
              <router-view v-slot="{ Component, route }">
                <transition name="fade" mode="out-in">
                  <component :is="Component" :key="route.fullPath" />
                </transition>
              </router-view>
            </template>
            <template #fallback>
              <div class="flex items-center justify-center min-h-screen">
                <div class="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            </template>
          </Suspense>
        </ErrorBoundary>
      </main>

      <!-- Нижняя навигация -->
      <nav
        v-if="shouldShowBottomNav"
        class="bottom-navigation"
      >
        <div class="grid">
          <NavLink
            v-for="item in navItems"
            :key="item.id"
            :to="item.route"
            :active="route.path === item.route"
            class="nav-item"
            :class-name="route.path === item.route ? 'text-purple-600' : 'text-zinc-700'"
          >
            <component
              :is="item.icon"
              :active="route.path === item.route"
              class="w-5 h-5 mb-1 transition-transform duration-200"
              :class="{'scale-110': route.path === item.route}"
            />
            <span class="text-xs font-normal">{{ item.label }}</span>
          </NavLink>
        </div>
      </nav>
    </template>

    <!-- Наш собственный компонент для тостов -->
    <SimpleToast />

    <!-- Error toast -->
    <div
      v-if="store.error"
      class="error-toast"
      @click="store.clearError()"
    >
      {{ store.error }}
    </div>
  </div>
</template>

<script setup lang="ts">
 // Объявляем тип для Window с cleanupDOM функцией
declare global {
  interface Window {
    Telegram?: any;
    debugOverlays?: () => string;
    clearAllOverlays?: () => string;
    cleanupDOM?: () => void;
    saveComponentStyles?: (componentName: string, selectors: string[]) => void;
    debugTools?: {
      findHighZIndexElements: () => any[];
      findPositionedElements: () => any[];
      findOverlayElements: () => any[];
      checkComponentsVisibility: () => any[];
      forceShowComponent: (selector: string) => boolean;
      removeLessonPlanElements: () => number;
      restoreComponentsVisibility: () => any[];
      analyzeDOMTree: () => any;
      forceReloadApp: () => any;
      createComponentIfMissing: (selector: string, className: string) => boolean;
      fullDOMCleanup: () => any;
      checkCurrentRoute: () => any;
      saveOriginalStyles: () => void;
      restoreOriginalStyles: () => void;
      showSavedStyles: () => void;
    };
  }
}

import { ref, computed, onMounted, onErrorCaptured, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMainStore } from './store'
import { TelegramService } from '@/services/telegram'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import NavMainIcon from '@/components/icons/NavMainIcon.vue'
import NavModeIcon from '@/components/icons/NavModeIcon.vue'
import NavCoursesIcon from '@/components/icons/NavCoursesIcon.vue'
import NavProfileIcon from '@/components/icons/NavProfileIcon.vue'
import NavLink from '@/components/NavLink.vue'
import SimpleToast from '@/components/SimpleToast.vue'
import LoadingScreen from '@/components/LoadingScreen.vue' // <-- Добавлен импорт
import AccessDenied from '@/components/access/AccessDenied.vue'
import { getToastManager } from '@/plugins/toastManager'
import { useTelegramApp } from './composables/useTelegramApp'

const store = useMainStore()
const route = useRoute()
const router = useRouter()
const isLoading = ref(true)
const error = ref<string | null>(null)
const isInitialized = ref(false)
const toastManager = getToastManager()

// Хранилище изначальных стилей для восстановления
const originalStyles = new Map<string, string>()

// Navigation items
const navItems = [
  { id: '', label: 'Home', icon: NavMainIcon, route: '/' },
  { id: 'modes', label: 'Plans', icon: NavModeIcon, route: '/modes' },
  { id: 'courses', label: 'Courses', icon: NavCoursesIcon, route: '/courses' },
  { id: 'profile', label: 'Profile', icon: NavProfileIcon, route: '/profile' }
]

// Нижняя навигация
const shouldShowBottomNav = computed(() => {
  return !route.path.startsWith('/admin')
})

// Динамические классы для приложения
const appClasses = computed(() => {
  const routeClass = `page-${route.path.replace(/\//g, '-').replace(/^-/, '')}`;
  return {
    'global-background': true,
    'has-navigation': true,
    [routeClass]: true
  };
});

// Обработчик ошибок
const handleError = (error: unknown) => {
  console.error('Application error:', error)
  const errorMessage = error instanceof Error ? error.message : 'Произошла неизвестная ошибка'
  store.setError(errorMessage)
  return false // Предотвращаем всплытие ошибки
}


// Функция для полной перезагрузки приложения при критических проблемах
const forceRefreshApp = () => {
  try {
    console.log('Принудительная перезагрузка приложения...');
    // Сохраняем текущий маршрут
    const currentPath = router.currentRoute.value.path;

    // 1. Сначала очищаем DOM
    if (typeof window.cleanupDOM === 'function') {
      window.cleanupDOM();
    }

    // 2. Перезагружаем страницу если мы находимся на одной из основных страниц
    if (currentPath === '/' ||
        currentPath.includes('modes') ||
        currentPath.includes('courses') ||
        currentPath.includes('profile')) {

      // Используем history API для перезагрузки текущей страницы без полного обновления
      router.replace({ path: '/temp-redirect' })
        .then(() => router.replace({ path: currentPath }))
        .catch(err => console.error('Ошибка при программной навигации:', err));
    }
  } catch (error) {
    console.error('Ошибка при принудительной перезагрузке:', error);
  }
};

onErrorCaptured(handleError)

// Предзагрузка фонового изображения
const preloadBackground = () => {
  const img = new Image();
  img.src = '/src/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg';
}

// Функция для сохранения изначальных стилей ключевых элементов
const saveOriginalStyles = (additionalSelectors: string[] = []) => {
  const keyElements = [
    '.app',
    '.main-content-container',
    'router-view',
    '.bottom-navigation',
    '.home-view',
    '.courses-view',
    '.modes-view',
    '.profile-view',
    '#app',
    // Добавляем селекторы для компонентов
    '.games-container',
    '.games-content',
    '.games-form',
    '.games-background',
    '.exercises-container',
    '.exercises-content',
    '.exercises-form',
    '.lesson-plan-container',
    '.lesson-plan-content',
    '.lesson-plan-form',
    ...additionalSelectors
  ];

  keyElements.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el, index) => {
      const element = el as HTMLElement;
      const key = `${selector}-${index}`;

      // Сохраняем все важные CSS свойства
      const computedStyle = window.getComputedStyle(element);
      const importantStyles = {
        display: computedStyle.display,
        visibility: computedStyle.visibility,
        opacity: computedStyle.opacity,
        position: computedStyle.position,
        zIndex: computedStyle.zIndex,
        width: computedStyle.width,
        height: computedStyle.height,
        minWidth: computedStyle.minWidth,
        maxWidth: computedStyle.maxWidth,
        minHeight: computedStyle.minHeight,
        maxHeight: computedStyle.maxHeight,
        overflow: computedStyle.overflow,
        overflowX: computedStyle.overflowX,
        overflowY: computedStyle.overflowY,
        transform: computedStyle.transform,
        backgroundColor: computedStyle.backgroundColor,
        backgroundImage: computedStyle.backgroundImage,
        backgroundSize: computedStyle.backgroundSize,
        backgroundPosition: computedStyle.backgroundPosition,
        backgroundRepeat: computedStyle.backgroundRepeat,
        backgroundAttachment: computedStyle.backgroundAttachment,
        padding: computedStyle.padding,
        paddingTop: computedStyle.paddingTop,
        paddingRight: computedStyle.paddingRight,
        paddingBottom: computedStyle.paddingBottom,
        paddingLeft: computedStyle.paddingLeft,
        margin: computedStyle.margin,
        marginTop: computedStyle.marginTop,
        marginRight: computedStyle.marginRight,
        marginBottom: computedStyle.marginBottom,
        marginLeft: computedStyle.marginLeft,
        border: computedStyle.border,
        borderRadius: computedStyle.borderRadius,
        boxShadow: computedStyle.boxShadow,
        flex: computedStyle.flex,
        flexDirection: computedStyle.flexDirection,
        flexWrap: computedStyle.flexWrap,
        justifyContent: computedStyle.justifyContent,
        alignItems: computedStyle.alignItems,
        alignContent: computedStyle.alignContent,
        gridTemplateColumns: computedStyle.gridTemplateColumns,
        gridTemplateRows: computedStyle.gridTemplateRows,
        gap: computedStyle.gap,
        rowGap: computedStyle.rowGap,
        columnGap: computedStyle.columnGap,
        fontSize: computedStyle.fontSize,
        fontWeight: computedStyle.fontWeight,
        color: computedStyle.color,
        textAlign: computedStyle.textAlign,
        lineHeight: computedStyle.lineHeight,
        backdropFilter: computedStyle.backdropFilter,
        filter: computedStyle.filter,
        cursor: computedStyle.cursor,
        pointerEvents: computedStyle.pointerEvents,
        userSelect: computedStyle.userSelect,
        bottom: computedStyle.bottom,
        left: computedStyle.left,
        right: computedStyle.right,
        top: computedStyle.top
      };

      originalStyles.set(key, JSON.stringify(importantStyles));
      console.log(`Сохранены изначальные стили для ${key}`);
    });
  });
}

// Функция для восстановления изначальных стилей
const restoreOriginalStyles = (componentName?: string) => {
  const keyElements = [
    '.app',
    '.main-content-container',
    'router-view',
    '.bottom-navigation',
    '.home-view',
    '.courses-view',
    '.modes-view',
    '.profile-view',
    '#app'
  ];

  // Если указан компонент, добавляем его специфичные селекторы
  if (componentName === 'games') {
    keyElements.push(
      '.games-container',
      '.games-content',
      '.games-form',
      '.games-background',
      '.games-content-wrapper',
      '.games-title-container',
      '.games-form-group',
      '.games-form-input',
      '.games-form-select',
      '.games-types-section',
      '.games-duration-section',
      '.games-format-section',
      '.games-format-grid',
      '.games-format-group',
      '.games-format-btn',
      '.games-type-btn',
      '.games-submit-btn',
      '.games-form-actions',
      '.games-buttons-container',
      '.games-result-container',
      '.games-result-content',
      '.games-content-card',
      '.games-lesson-plan-container',
      '.games-planet-background',
      '.games-error',
      '.games-loading'
    );
  } else if (componentName === 'exercises') {
    keyElements.push(
      '.exercises-container',
      '.exercises-content',
      '.exercises-form',
      '.exercises-background',
      '.exercises-content-wrapper',
      '.exercises-title-container',
      '.exercises-form-group',
      '.exercises-settings',
      '.exercises-result-container',
      '.exercises-result-content',
      '.exercise-card',
      '.exercise-content',
      '.answer-content',
      '.instruction-content',
      '.generation-results',
      '.theme-selection',
      '.creative-elements',
      '.exercise-settings',
      '.additional-options',
      '.format-options'
    );
  } else if (componentName === 'lesson-plan') {
    keyElements.push(
      '.lesson-plan-container',
      '.lesson-plan-content',
      '.lesson-plan-form',
      '.lesson-plan-background',
      '.lesson-plan-heading',
      '.lesson-plan-subheading',
      '.lesson-plan-paragraph',
      '.lesson-plan-list',
      '.lesson-plan-list-item',
      '.lesson-plan-section-header',
      '.lesson-plan-bold',
      '.lesson-plan-italic',
      '.lesson-plan-empty-paragraph',
      '.title-form-group',
      '.generation-form',
      '.form-group',
      '.result-container',
      '.plan-content'
    );
  }

  keyElements.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el, index) => {
      const element = el as HTMLElement;

      // Ищем стили как для основных элементов, так и для компонентов
      const keys = [
        `${selector}-${index}`,
        `${selector}-${index}-${componentName || 'main'}`
      ];

      for (const key of keys) {
        const savedStyles = originalStyles.get(key);

        if (savedStyles) {
          try {
            const styles = JSON.parse(savedStyles);

            // Применяем сохраненные стили
            Object.entries(styles).forEach(([property, value]) => {
              if (value && value !== 'auto' && value !== 'none') {
                const cssProperty = property.replace(/([A-Z])/g, '-$1').toLowerCase();
                element.style.setProperty(cssProperty, value as string, 'important');
              }
            });

            console.log(`Восстановлены изначальные стили для ${key}`);
            break; // Если нашли стили, прекращаем поиск
          } catch (error) {
            console.error(`Ошибка при восстановлении стилей для ${key}:`, error);
          }
        }
      }
    });
  });
}

// Глобальная функция для сохранения стилей конкретного компонента
const saveComponentStyles = (componentName: string, selectors: string[]) => {
  console.log(`Сохраняем стили для компонента ${componentName}`);

  selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el, index) => {
      const element = el as HTMLElement;
      const key = `${selector}-${index}-${componentName}`;

      // Сохраняем все важные CSS свойства
      const computedStyle = window.getComputedStyle(element);
      const importantStyles = {
        display: computedStyle.display,
        visibility: computedStyle.visibility,
        opacity: computedStyle.opacity,
        position: computedStyle.position,
        zIndex: computedStyle.zIndex,
        width: computedStyle.width,
        height: computedStyle.height,
        minWidth: computedStyle.minWidth,
        maxWidth: computedStyle.maxWidth,
        minHeight: computedStyle.minHeight,
        maxHeight: computedStyle.maxHeight,
        overflow: computedStyle.overflow,
        overflowX: computedStyle.overflowX,
        overflowY: computedStyle.overflowY,
        transform: computedStyle.transform,
        backgroundColor: computedStyle.backgroundColor,
        backgroundImage: computedStyle.backgroundImage,
        backgroundSize: computedStyle.backgroundSize,
        backgroundPosition: computedStyle.backgroundPosition,
        backgroundRepeat: computedStyle.backgroundRepeat,
        backgroundAttachment: computedStyle.backgroundAttachment,
        padding: computedStyle.padding,
        paddingTop: computedStyle.paddingTop,
        paddingRight: computedStyle.paddingRight,
        paddingBottom: computedStyle.paddingBottom,
        paddingLeft: computedStyle.paddingLeft,
        margin: computedStyle.margin,
        marginTop: computedStyle.marginTop,
        marginRight: computedStyle.marginRight,
        marginBottom: computedStyle.marginBottom,
        marginLeft: computedStyle.marginLeft,
        border: computedStyle.border,
        borderRadius: computedStyle.borderRadius,
        boxShadow: computedStyle.boxShadow,
        flex: computedStyle.flex,
        flexDirection: computedStyle.flexDirection,
        flexWrap: computedStyle.flexWrap,
        justifyContent: computedStyle.justifyContent,
        alignItems: computedStyle.alignItems,
        alignContent: computedStyle.alignContent,
        gridTemplateColumns: computedStyle.gridTemplateColumns,
        gridTemplateRows: computedStyle.gridTemplateRows,
        gap: computedStyle.gap,
        rowGap: computedStyle.rowGap,
        columnGap: computedStyle.columnGap,
        fontSize: computedStyle.fontSize,
        fontWeight: computedStyle.fontWeight,
        color: computedStyle.color,
        textAlign: computedStyle.textAlign,
        lineHeight: computedStyle.lineHeight,
        backdropFilter: computedStyle.backdropFilter,
        filter: computedStyle.filter,
        cursor: computedStyle.cursor,
        pointerEvents: computedStyle.pointerEvents,
        userSelect: computedStyle.userSelect,
        bottom: computedStyle.bottom,
        left: computedStyle.left,
        right: computedStyle.right,
        top: computedStyle.top
      };

      originalStyles.set(key, JSON.stringify(importantStyles));
      console.log(`Сохранены стили для ${key}`);
    });
  });
}

// Инициализация Telegram WebApp
const { trackRouteChange } = useTelegramApp()

// Инициализируем Telegram WebApp при загрузке приложения
onMounted(async () => {
  try {
    isLoading.value = true;

    // Предзагрузка фонового изображения
    preloadBackground();

    // Сохраняем изначальные стили после небольшой задержки для полной загрузки
    setTimeout(() => {
      saveOriginalStyles();
    }, 1000);

    // Добавляем отладочную функцию для анализа перекрывающих элементов
    window.debugOverlays = () => {
      const allElements = document.querySelectorAll('*');
      console.log('=== DEBUGGER: Ищем перекрывающие элементы ===');

      interface SuspectElement {
        element: Element;
        tag: string;
        id: string;
        classes: string;
        position: string;
        zIndex: string;
        display: string;
        visibility: string;
        opacity: string;
        width: string;
        height: string;
        pointerEvents: string;
        transform: string;
      }

      // Массив для хранения подозрительных элементов
      const suspects: SuspectElement[] = [];

      allElements.forEach(el => {
        const styles = window.getComputedStyle(el);

        // Проверяем элементы с высоким z-index, fixed или absolute позиционированием
        if (
          (styles.position === 'fixed' || styles.position === 'absolute') &&
          (parseInt(styles.zIndex, 10) > 5 || styles.zIndex === 'auto') &&
          (el as HTMLElement).offsetWidth > window.innerWidth / 2 && // элемент занимает больше половины экрана по ширине
          (el as HTMLElement).offsetHeight > window.innerHeight / 2 // элемент занимает больше половины экрана по высоте
        ) {
          // Собираем информацию об элементе
          suspects.push({
            element: el,
            tag: el.tagName,
            id: el.id,
            classes: el.className.toString(),
            position: styles.position,
            zIndex: styles.zIndex,
            display: styles.display,
            visibility: styles.visibility,
            opacity: styles.opacity,
            width: styles.width,
            height: styles.height,
            pointerEvents: styles.pointerEvents,
            transform: styles.transform
          });

          // Временно подсвечиваем элементы для визуальной отладки
          const htmlEl = el as HTMLElement;
          const originalBg = htmlEl.style.backgroundColor;
          const originalOutline = htmlEl.style.outline;

          htmlEl.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
          htmlEl.style.outline = '2px solid red';

          setTimeout(() => {
            htmlEl.style.backgroundColor = originalBg;
            htmlEl.style.outline = originalOutline;
          }, 5000); // подсветка исчезнет через 5 секунд
        }
      });

      console.table(suspects);
      return 'Найдено подозрительных элементов: ' + suspects.length + '. Подробности в консоли.';
    };

    // Добавляем функцию для очистки всего DOM от перекрывающих элементов
    window.clearAllOverlays = () => {
      // Принудительно удаляем все fixed/absolute элементы с высоким z-index
      const selectors = [
        '.simple-toast-container',
        '[style*="position: fixed"]',
        '[style*="position: absolute"]',
        '[style*="z-index"]',
        '.lesson-plan-container'
      ];

      selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          // Если элемент не является частью основной навигации
          if (!el.classList.contains('bottom-navigation') && !el.closest('.bottom-navigation')) {
            // Устанавливаем нулевой z-index и прозрачность
            (el as HTMLElement).style.zIndex = '-1';
            (el as HTMLElement).style.opacity = '0';
            (el as HTMLElement).style.pointerEvents = 'none';
            console.log(`Скрыт элемент: ${el.tagName} с классами ${el.className}`);
          }
        });
      });

      return 'Все возможные перекрывающие элементы скрыты.';
    };

    // Добавим функцию для полной очистки и восстановления DOM
    // После объявления window.clearAllOverlays
    window.cleanupDOM = () => {
      console.log('Выполняем глобальную очистку DOM...');

      // 1. Удаление элементов плана урока и упражнений
      const problematicSelectors = [
        // Селекторы для LessonPlan
        '.lesson-plan-container',
        '[data-component="lesson-plan"]',
        '.planet-background',
        '.simple-toast-container',
        '.lesson-plan-heading',
        '.lesson-plan-subheading',
        '.lesson-plan-paragraph',
        '.lesson-plan-list',
        '.lesson-plan-list-item',
        '.lesson-plan-section-header',
        '.lesson-plan-bold',
        '.lesson-plan-italic',
        '.lesson-plan-empty-paragraph',
        '.title-form-group',
        '.generation-form',
        '.form-group',
        '.result-container',
        '.plan-content',
        // Селекторы для Exercises
        '[data-component="exercises"]',
        '[data-route="/exercises"]',
        '.exercise-card',
        '.exercise-content',
        '.answer-content',
        '.instruction-content',
        '.exercises-container',
        '.generation-results',
        '.theme-selection',
        '.creative-elements',
        '.exercise-settings',
        '.additional-options',
        '.format-options',
        '.exercise-cleanup-target',
        // Селекторы для Games
        '.games-container',
        '.games-background',
        '.games-content-wrapper',
        '.games-content',
        '.games-title-container',
        '.games-form',
        '.games-form-group',
        '.games-types-section',
        '.games-duration-section',
        '.games-result-container',
        '.games-result-content',
        '.games-global-background-active',
        '[data-component="games"]',
        '[data-route="/games"]',
        // Дополнительные селекторы для Games
        '.games-lesson-plan-container',
        '.games-planet-background',
        '.games-error',
        '.games-loading'
      ];

      // Удаляем все элементы по селекторам
      problematicSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`Найдено ${elements.length} элементов по селектору ${selector}`);
        elements.forEach(el => {
          if (el && el.parentNode) {
            try {
              // Полностью удаляем элемент из DOM
              el.parentNode.removeChild(el);
            } catch (error) {
              console.error('Ошибка при удалении элемента:', error);

              // Если не удалось удалить, скрываем элемент
              if (el instanceof HTMLElement) {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.opacity = '0';
                el.style.pointerEvents = 'none';
                el.style.zIndex = '-9999';
                el.style.position = 'absolute';
                el.style.left = '-9999px';
                el.style.width = '0';
                el.style.height = '0';
                el.style.overflow = 'hidden';
                el.style.clip = 'rect(0, 0, 0, 0)';
                el.style.margin = '-1px';
                el.style.padding = '0';
                el.style.border = '0';
              }
            }
          }
        });
      });

      // 2. Удаляем все стили, связанные с проблемными компонентами
      const styleSheets = document.styleSheets;
      for (let i = 0; i < styleSheets.length; i++) {
        try {
          const cssRules = styleSheets[i].cssRules || styleSheets[i].rules;
          if (cssRules) {
            for (let j = cssRules.length - 1; j >= 0; j--) {
              const rule = cssRules[j];
              // Проверяем, что это правило стиля с селектором
              if (rule instanceof CSSStyleRule && rule.selectorText && (
                rule.selectorText.includes('lesson-plan') ||
                rule.selectorText.includes('plan-content') ||
                rule.selectorText.includes('exercise-card') ||
                rule.selectorText.includes('exercise-content') ||
                rule.selectorText.includes('answer-content') ||
                rule.selectorText.includes('instruction-content') ||
                rule.selectorText.includes('exercises-container') ||
                rule.selectorText.includes('generation-results') ||
                rule.selectorText.includes('theme-selection') ||
                rule.selectorText.includes('creative-elements') ||
                rule.selectorText.includes('exercise-settings') ||
                rule.selectorText.includes('additional-options') ||
                rule.selectorText.includes('format-options') ||
                rule.selectorText.includes('games-container') ||
                rule.selectorText.includes('games-background') ||
                rule.selectorText.includes('games-content') ||
                rule.selectorText.includes('games-form') ||
                rule.selectorText.includes('games-result') ||
                rule.selectorText.includes('games-global-background-active') ||
                rule.selectorText.includes('games-lesson-plan-container') ||
                rule.selectorText.includes('games-planet-background') ||
                rule.selectorText.includes('games-error') ||
                rule.selectorText.includes('games-loading')
              )) {
                try {
                  styleSheets[i].deleteRule(j);
                } catch (e) {
                  console.error('Ошибка при удалении правила CSS:', e);
                }
              }
            }
          }
        } catch (e) {
          console.error('Ошибка при доступе к таблице стилей:', e);
        }
      }

      // 3. Удаляем все атрибуты data-v-* у элементов
      try {
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
          const attributes = el.attributes;
          const attributesToRemove = [];

          for (let i = 0; i < attributes.length; i++) {
            const attr = attributes[i];
            if (attr.name.startsWith('data-v-')) {
              attributesToRemove.push(attr.name);
            }
          }

          attributesToRemove.forEach(attrName => {
            el.removeAttribute(attrName);
          });
        });
      } catch (e) {
        console.error('Ошибка при удалении атрибутов data-v-*:', e);
      }

      // 4. Проверка и восстановление router-view
      const routerView = document.querySelector('router-view');
      if (!routerView) {
        console.log('router-view не найден, создаем новый');
        const app = document.querySelector('#app');
        if (app) {
          const newRouterView = document.createElement('router-view');
          app.appendChild(newRouterView);
          console.log('router-view создан и добавлен в #app');
        }
      }

      // 5. Восстанавливаем изначальные стили всех основных компонентов
      const currentPath = window.location.pathname;
      let componentName = '';

      if (currentPath.includes('games')) componentName = 'games';
      else if (currentPath.includes('exercises')) componentName = 'exercises';
      else if (currentPath.includes('lesson-plan')) componentName = 'lesson-plan';

      restoreOriginalStyles(componentName);

      // 5.1. Дополнительная обработка для компонента Games
      if (componentName === 'games') {
        setTimeout(() => {
          // Принудительно восстанавливаем стили формы Games
          const gamesContainer = document.querySelector('.games-container');
          if (gamesContainer && gamesContainer instanceof HTMLElement) {
            gamesContainer.style.setProperty('width', '100%', 'important');
            gamesContainer.style.setProperty('min-height', '100vh', 'important');
            gamesContainer.style.setProperty('padding', '2rem', 'important');
            gamesContainer.style.setProperty('position', 'relative', 'important');
            gamesContainer.style.setProperty('overflow-x', 'hidden', 'important');
            gamesContainer.style.setProperty('overflow-y', 'auto', 'important');
          }

          const gamesContentWrapper = document.querySelector('.games-content-wrapper');
          if (gamesContentWrapper && gamesContentWrapper instanceof HTMLElement) {
            gamesContentWrapper.style.setProperty('max-width', '800px', 'important');
            gamesContentWrapper.style.setProperty('margin', '0 auto', 'important');
            gamesContentWrapper.style.setProperty('padding-top', '120px', 'important');
            gamesContentWrapper.style.setProperty('position', 'relative', 'important');
            gamesContentWrapper.style.setProperty('z-index', '10', 'important');
            gamesContentWrapper.style.setProperty('display', 'flex', 'important');
            gamesContentWrapper.style.setProperty('flex-direction', 'column', 'important');
            gamesContentWrapper.style.setProperty('align-items', 'center', 'important');
          }

          const gamesForm = document.querySelector('.games-form');
          if (gamesForm && gamesForm instanceof HTMLElement) {
            gamesForm.style.setProperty('margin-bottom', '2rem', 'important');
            gamesForm.style.setProperty('width', '100%', 'important');
          }

          console.log('Дополнительные стили Games применены');
        }, 200);
      }

      // 6. Удаляем класс has-lesson-plan у body, если он есть
      if (document.body.classList.contains('has-lesson-plan')) {
        document.body.classList.remove('has-lesson-plan');
      }

      // 7. Принудительно устанавливаем глобальный фон
      const appElement = document.querySelector('.app');
      if (appElement && appElement instanceof HTMLElement) {
        appElement.classList.add('global-background');
      }

      // 8. Принудительно восстанавливаем видимость текущего маршрута
      const routePath = window.location.pathname;
      let currentViewClass = '';

      if (routePath === '/' || routePath === '') currentViewClass = '.home-view';
      else if (routePath.includes('modes')) currentViewClass = '.modes-view';
      else if (routePath.includes('courses')) currentViewClass = '.courses-view';
      else if (routePath.includes('profile')) currentViewClass = '.profile-view';

      if (currentViewClass) {
        const currentView = document.querySelector(currentViewClass);
        if (currentView && currentView instanceof HTMLElement) {
          // Сначала восстанавливаем изначальные стили, затем обеспечиваем видимость
          const key = `${currentViewClass}-0`;
          const savedStyles = originalStyles.get(key);

          if (savedStyles) {
            try {
              const styles = JSON.parse(savedStyles);
              Object.entries(styles).forEach(([property, value]) => {
                if (value && value !== 'auto' && value !== 'none') {
                  const cssProperty = property.replace(/([A-Z])/g, '-$1').toLowerCase();
                  currentView.style.setProperty(cssProperty, value as string, 'important');
                }
              });
            } catch (error) {
              console.error(`Ошибка при восстановлении стилей для ${currentViewClass}:`, error);
            }
          }

          // Дополнительно обеспечиваем видимость
          currentView.style.setProperty('display', 'block', 'important');
          currentView.style.setProperty('visibility', 'visible', 'important');
          currentView.style.setProperty('opacity', '1', 'important');

          console.log(`Принудительно активирован текущий компонент: ${currentViewClass}`);
        }
      }

      return 'DOM очищен и восстановлен';
    };

    // Делаем функцию сохранения стилей компонента глобально доступной
    window.saveComponentStyles = saveComponentStyles;

    // Добавляем функции для работы с изначальными стилями в debug tools
    window.debugTools = {
      ...window.debugTools,
      saveOriginalStyles: () => {
        saveOriginalStyles();
        console.log('Изначальные стили сохранены');
      },
      restoreOriginalStyles: () => {
        restoreOriginalStyles();
        console.log('Изначальные стили восстановлены');
      },
      showSavedStyles: () => {
        console.log('Сохраненные стили:', Object.fromEntries(originalStyles));
        return `Сохранено стилей для ${originalStyles.size} элементов`;
      }
    };



    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Timeout waiting for Telegram WebApp'));
      }, 5000);

      if (window.Telegram?.WebApp) {
        clearTimeout(timeout);
        TelegramService.initialize();
        resolve();
      } else {
        const checkInterval = setInterval(() => {
          if (window.Telegram?.WebApp) {
            clearInterval(checkInterval);
            clearTimeout(timeout);
            TelegramService.initialize();
            resolve();
          }
        }, 100);
      }
    });

    isInitialized.value = true;
    await store.initializeApp();

    // Дополнительное сохранение стилей после полной инициализации
    await nextTick();
    setTimeout(() => {
      saveOriginalStyles();
      console.log('Изначальные стили пересохранены после полной инициализации');
    }, 2000);

    const currentRoute = router.currentRoute.value;
    if (currentRoute.meta.requiresAdmin && !store.isAdmin) {
      await router.push({ name: 'home' });
    }

    // Настройка обработчиков для очистки тостов при навигации
    toastManager.setupRouterGuards(router);

    // Инициализация Telegram WebApp
    const { trackRouteChange } = useTelegramApp();

    // Отслеживание переходов между страницами
    router.afterEach((to) => {
      trackRouteChange(to.path);
    });

    // Принудительная инициализация кнопки "Назад" в Telegram
    setTimeout(() => {
      try {
        const currentPath = router.currentRoute.value.path;

        // Показываем кнопку "Назад" на всех страницах, кроме главной
        if (currentPath !== '/' && currentPath !== '') {
          console.log('Принудительно показываем кнопку "Назад" на:', currentPath);
          TelegramService.forceShowBackButton();
        } else {
          console.log('Принудительно скрываем кнопку "Назад" на главной странице');
          TelegramService.forceHideBackButton();
        }

        // Настраиваем обработчик нажатия на кнопку "Назад"
        TelegramService.setupBackButtonHandler(() => {
          console.log('Нажата кнопка "Назад" в Telegram');

          // Если мы можем вернуться назад в истории браузера
          if (window.history.state && window.history.state.back) {
            console.log('Возвращаемся назад по истории браузера');
            router.back();
          } else {
            console.log('Нет истории браузера, закрываем приложение');
            TelegramService.close();
          }
        });
      } catch (err) {
        console.error('Ошибка при принудительной инициализации кнопки "Назад":', err);
      }
    }, 1000);

  } catch (err) {
    handleError(err);
  } finally {
    isLoading.value = false;
  }
});

// Заменим обработчик afterEach на более надежный
router.afterEach(async (to, from) => {
  await nextTick();
  window.scrollTo(0, 0);

  // Список проблемных путей, после которых нужно восстанавливать DOM
  const problematicPaths = ['lesson-plan', 'exercises', 'content-view', 'exercise'];
  const hasProblematicTransition = problematicPaths.some(path => from.path.includes(path));

  // Специальная обработка для Games - не вызываем cleanupDOM при переходе с Games
  const isFromGames = from.path.includes('games');
  const isToNormalPage = ['/', '/modes', '/courses', '/profile'].includes(to.path);

  // Если был переход с проблемной страницы (но не с Games на обычную страницу)
  if (hasProblematicTransition || (isFromGames && !isToNormalPage)) {
    console.log(`Обнаружен переход с проблемной страницы: ${from.path} на ${to.path}`);

    // Вызываем полную очистку DOM только если это не переход с Games на обычную страницу
    if (!isFromGames || !isToNormalPage) {
      if (typeof window.cleanupDOM === 'function') {
        window.cleanupDOM();
      }
    } else {
      console.log('Пропускаем cleanupDOM для перехода с Games на обычную страницу');
    }

    // Ожидаем полной перерисовки Vue
    await nextTick();

    // Используем более длительную задержку для уверенности
    setTimeout(async () => {
      console.log('Принудительно восстанавливаем видимость интерфейса...');

      // Специальная обработка для перехода на Games
      if (to.path.includes('games')) {
        console.log('Обнаружен переход на Games, ждем загрузки компонента...');

        // Ждем дополнительное время для полной загрузки Games компонента
        setTimeout(() => {
          const gamesContainer = document.querySelector('.games-container');
          if (gamesContainer) {
            console.log('Games контейнер найден, проверяем стили...');

            const computedStyle = window.getComputedStyle(gamesContainer);
            const needsRestore = computedStyle.width === '0px' ||
                               computedStyle.display === 'none' ||
                               computedStyle.visibility === 'hidden' ||
                               computedStyle.opacity === '0';

            if (needsRestore) {
              console.log('Games контейнер поврежден, восстанавливаем...');

              // Принудительно восстанавливаем стили Games
              (gamesContainer as HTMLElement).style.setProperty('width', '100%', 'important');
              (gamesContainer as HTMLElement).style.setProperty('min-height', '100vh', 'important');
              (gamesContainer as HTMLElement).style.setProperty('padding', '2rem', 'important');
              (gamesContainer as HTMLElement).style.setProperty('position', 'relative', 'important');
              (gamesContainer as HTMLElement).style.setProperty('overflow-x', 'hidden', 'important');
              (gamesContainer as HTMLElement).style.setProperty('overflow-y', 'auto', 'important');
              (gamesContainer as HTMLElement).style.setProperty('display', 'block', 'important');
              (gamesContainer as HTMLElement).style.setProperty('visibility', 'visible', 'important');
              (gamesContainer as HTMLElement).style.setProperty('opacity', '1', 'important');

              console.log('Стили Games контейнера принудительно восстановлены');
            } else {
              console.log('Games контейнер в порядке, стили не требуют восстановления');
            }
          } else {
            console.log('Games контейнер не найден, ждем еще...');
          }
        }, 300);
      }

      // Проверяем, что текущий компонент отображается правильно
      let currentViewClass = '';
      if (to.path === '/' || to.path === '') currentViewClass = '.home-view';
      else if (to.path.includes('modes')) currentViewClass = '.modes-view';
      else if (to.path.includes('courses')) currentViewClass = '.courses-view';
      else if (to.path.includes('profile')) currentViewClass = '.profile-view';
      else if (to.path.includes('games')) currentViewClass = '.games-container';

      if (currentViewClass) {
        const currentView = document.querySelector(currentViewClass);
        if (currentView) {
          // Восстанавливаем изначальные стили для текущего компонента
          const key = `${currentViewClass}-0`;
          const savedStyles = originalStyles.get(key);

          if (savedStyles) {
            try {
              const styles = JSON.parse(savedStyles);
              Object.entries(styles).forEach(([property, value]) => {
                if (value && value !== 'auto' && value !== 'none') {
                  const cssProperty = property.replace(/([A-Z])/g, '-$1').toLowerCase();
                  (currentView as HTMLElement).style.setProperty(cssProperty, value as string, 'important');
                }
              });
            } catch (error) {
              console.error(`Ошибка при восстановлении стилей для ${currentViewClass}:`, error);
            }
          }

          // Дополнительно обеспечиваем видимость
          (currentView as HTMLElement).style.setProperty('display', 'block', 'important');
          (currentView as HTMLElement).style.setProperty('visibility', 'visible', 'important');
          (currentView as HTMLElement).style.setProperty('opacity', '1', 'important');

          console.log(`Принудительно активирован текущий компонент: ${currentViewClass}`);
        } else {
          console.warn(`Не найден текущий компонент: ${currentViewClass} - пробуем перезагрузить приложение`);
          // Если компонент не найден, пробуем перезагрузить приложение
          forceRefreshApp();
        }
      }

      // Проверяем визуальное состояние приложения
      const mainContent = document.querySelector('.main-content-container');
      const routerView = document.querySelector('router-view');

      // Если основные компоненты отсутствуют, инициируем восстановление
      if (!mainContent || !routerView) {
        console.warn('Критические компоненты приложения отсутствуют, инициируем перезагрузку');
        forceRefreshApp();
        return;
      }

      // Дополнительная проверка на наличие перекрывающих элементов
      const overlayElements = document.querySelectorAll('[style*="position: fixed"], [style*="position: absolute"]');
      overlayElements.forEach(el => {
        const styles = window.getComputedStyle(el);
        const zIndex = parseInt(styles.zIndex, 10);

        // Если элемент имеет высокий z-index и не является частью навигации
        if (zIndex > 10 && !el.classList.contains('bottom-navigation') && !el.closest('.bottom-navigation')) {
          console.warn(`Обнаружен перекрывающий элемент: ${el.tagName} с классами ${el.className}, z-index: ${zIndex}`);

          // Скрываем элемент
          (el as HTMLElement).style.display = 'none';
          (el as HTMLElement).style.visibility = 'hidden';
          (el as HTMLElement).style.opacity = '0';
          (el as HTMLElement).style.pointerEvents = 'none';
          (el as HTMLElement).style.zIndex = '-9999';
        }
      });

      // Специальная обработка для компонента Games
      if (to.path.includes('games')) {
        setTimeout(() => {
          console.log('Дополнительная обработка для Games компонента...');

          const gamesContainer = document.querySelector('.games-container');
          if (gamesContainer && gamesContainer instanceof HTMLElement) {
            // Принудительно восстанавливаем основные стили Games
            gamesContainer.style.setProperty('width', '100%', 'important');
            gamesContainer.style.setProperty('min-height', '100vh', 'important');
            gamesContainer.style.setProperty('padding', '2rem', 'important');
            gamesContainer.style.setProperty('position', 'relative', 'important');
            gamesContainer.style.setProperty('overflow-x', 'hidden', 'important');
            gamesContainer.style.setProperty('overflow-y', 'auto', 'important');
            gamesContainer.style.setProperty('display', 'block', 'important');
            gamesContainer.style.setProperty('visibility', 'visible', 'important');
            gamesContainer.style.setProperty('opacity', '1', 'important');

            console.log('Стили Games контейнера восстановлены');
          }

          const gamesContentWrapper = document.querySelector('.games-content-wrapper');
          if (gamesContentWrapper && gamesContentWrapper instanceof HTMLElement) {
            gamesContentWrapper.style.setProperty('max-width', '800px', 'important');
            gamesContentWrapper.style.setProperty('margin', '0 auto', 'important');
            gamesContentWrapper.style.setProperty('padding-top', '120px', 'important');
            gamesContentWrapper.style.setProperty('position', 'relative', 'important');
            gamesContentWrapper.style.setProperty('z-index', '10', 'important');
            gamesContentWrapper.style.setProperty('display', 'flex', 'important');
            gamesContentWrapper.style.setProperty('flex-direction', 'column', 'important');
            gamesContentWrapper.style.setProperty('align-items', 'center', 'important');

            console.log('Стили Games content wrapper восстановлены');
          }

          const gamesForm = document.querySelector('.games-form');
          if (gamesForm && gamesForm instanceof HTMLElement) {
            gamesForm.style.setProperty('margin-bottom', '2rem', 'important');
            gamesForm.style.setProperty('width', '100%', 'important');
            gamesForm.style.setProperty('display', 'block', 'important');

            console.log('Стили Games формы восстановлены');
          }
        }, 200);
      }

      // Принудительно устанавливаем глобальный фон
      const appElement = document.querySelector('.app');
      if (appElement && appElement instanceof HTMLElement) {
        appElement.classList.add('global-background');
      }

      console.log('Проверка и восстановление интерфейса завершены');
    }, 500); // Увеличиваем задержку до 500мс
  }
});

// Обработка переходов между страницами
watch(() => route.path, (newPath, oldPath) => {
  console.log(`Переход с ${oldPath} на ${newPath}`);

  // Сохраняем информацию о предыдущем маршруте
  localStorage.setItem('lastRoute', JSON.stringify({
    path: oldPath,
    name: route.name
  }));

  // Добавляем класс для страницы тарифов
  if (newPath.includes('tariffs') || newPath.includes('profile')) {
    document.body.classList.add('full-height-page');
  } else {
    document.body.classList.remove('full-height-page');
  }

  // Отслеживаем просмотр страницы
  trackRouteChange(newPath)
});

// Обработчик повторной попытки доступа
const handleRetry = async () => {
  try {
    isLoading.value = true
    store.accessDenied = null
    store.error = null

    // Пытаемся повторно инициализировать приложение
    await store.initializeApp()
  } catch (error) {
    console.error('Retry failed:', error)
    // Ошибка будет обработана в store.initializeApp
  } finally {
    isLoading.value = false
  }
}
</script>

<style>
/* Базовые стили */
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  width: 100%;
  height: 100%;
  min-height: 100vh;
}

/* Переменные для темы */
:root {
  --primary-color: #9333EA;
  --secondary-color: #ec407a;
  --background-color: #1a1a2e;
  --text-color: #ffffff;
  --z-index-background: -1;
  --z-index-content: 10;
  --z-index-component: 20;
  --z-index-navbar: 30;
  --z-index-toast: 40;
  --z-index-modal: 50;
  --z-index-overlay: 60;

  /* Переменные для тостов */
  --toast-bottom-offset: 4rem;
  --toast-right-offset: 1rem;
  --toast-max-width: 350px;
  --toast-success-color: #4caf50;
  --toast-error-color: #f44336;
  --toast-info-color: #2196f3;
  --toast-warning-color: #ff9800;
  --toast-mobile-bottom-offset: 5rem;
  --toast-mobile-right-offset: 0.5rem;
  --toast-mobile-left-offset: 0.5rem;
  --toast-mobile-max-width: calc(100% - 1rem);
}

/* Принудительные правила для решения проблемы с невидимостью */
.app,
.main-content-container,
router-view,
.home-view,
.courses-view,
.modes-view,
.profile-view {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  overflow: auto !important;
  min-height: 100vh !important;
  height: 100% !important;
}

/* Специальные правила для текущего активного вида */
.home-view,
.courses-view,
.modes-view,
.profile-view {
  position: relative !important;
  z-index: 20 !important;
  min-height: 100vh !important;
  height: 100% !important;
}

/* Фиксированное позиционирование для нижней навигации */
.bottom-navigation {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #ffcaf8;
  border-top: 1px solid #ffb5f7;
  z-index: var(--z-index-navbar);
  box-shadow: 0 -4px 6px -1px rgba(255, 202, 248, 0.2);
  width: 100%;
}

.bottom-navigation .grid {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.bottom-navigation .grid > * {
  flex: 1;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Отступ для контента при наличии нижней навигации */
body:has(.bottom-navigation) {
  padding-bottom: 4rem;
}

/* Правила для переходов между страницами */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease !important;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0 !important;
}

/* Предотвращение скрытия контента в Telegram WebApp */
#app {
  width: 100% !important;
  min-height: 100vh !important;
  height: 100% !important;
  background-color: transparent !important;
}

.app {
  position: relative;
  width: 100%;
  min-height: 100vh;
  height: 100%;
  padding: 0;
  margin: 0;
  overflow-x: hidden;
}

.global-background {
  background-image: url('@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  min-height: 100vh;
  height: 100%;
  position: relative;
  z-index: 0;
}

/* Добавляем псевдоэлемент для обеспечения полного покрытия фоном */
.global-background::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: -1;
}

.main-content-container {
  position: relative;
  z-index: var(--z-index-content);
  min-height: 100vh;
  height: 100%;
}

.bottom-navigation {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #ffcaf8;
  border-top: 1px solid #ffb5f7;
  z-index: var(--z-index-navbar);
  box-shadow: 0 -4px 6px -1px rgba(255, 202, 248, 0.2);
}

/* Стили для toast-уведомлений об ошибках */
.error-toast {
  position: fixed;
  bottom: 4rem;
  right: 1rem;
  background-color: #f44336;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: var(--z-index-toast);
  cursor: pointer;
}

/* Анимации переходов между страницами */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Стили для активных ссылок навигации */
.router-link-active {
  position: relative;
}

.router-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  background-color: var(--primary-color);
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(147, 51, 234, 0.5);
}

.router-link-active svg {
  filter: drop-shadow(0 0 4px rgba(147, 51, 234, 0.5));
}

/* Дополнительные стили для мобильных устройств */
@media (max-width: 768px) {
  .global-background {
    background-attachment: scroll; /* Для лучшей производительности на мобильных */
  }

  .global-background::before {
    background-attachment: scroll;
    background-size: cover;
    height: 100vh; /* Фиксированная высота для мобильных */
  }

  html, body, #app, .app {
    height: -webkit-fill-available; /* Для iOS Safari */
    min-height: -webkit-fill-available;
  }
}

/* Стили для страниц, требующих полной высоты */
body.full-height-page {
  min-height: 100vh;
  height: 100%;
  overflow: auto;
}

body.full-height-page #app,
body.full-height-page .app,
body.full-height-page .main-content-container,
body.full-height-page router-view {
  min-height: 100vh !important;
  height: 100% !important;
}

body.full-height-page .global-background::before {
  height: 100vh;
  min-height: 100%;
}
</style>
