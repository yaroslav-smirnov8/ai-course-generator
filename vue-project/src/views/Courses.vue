<!-- src/views/Courses.vue -->
<template>
  <div
    class="min-h-screen py-4"
    :style="{
      backgroundImage: `url(${backgroundCourses})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }"
  >
    <!-- Добавляем ref для корневого элемента -->
    <div class="courses-view" ref="coursesViewRef">
      <!-- Header -->
      <div class="rounded-[32px] bg-[#2A0944]/80 mx-4 mb-4">
        <div class="flex justify-between items-center px-6 py-4">
          <h1 class="text-2xl font-bold text-white">
            Courses and Products
          </h1>
          <router-link
            to="/courses/create"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Create Course
          </router-link>
        </div>
      </div>

      <!-- Course cards -->
      <div class="space-y-4 px-4">
        <!-- Course card -->
        <div
          v-for="card in cards"
          :key="card.id"
          class="relative cursor-pointer hover:scale-[1.02] transition-transform duration-200"
          @click="handleCardClick(card)"
        >
          <!-- Image -->
          <img
            :src="card.image"
            :alt="card.title"
            class="w-full h-[160px] object-cover rounded-[32px]"
          />

          <!-- Text field -->
          <div class="relative -mt-8 mx-4 rounded-[32px] bg-[#2A0944]/80 p-6">
            <h3 class="text-lg font-medium text-white mb-2">
              {{ card.title }}
            </h3>
            <p class="text-sm text-gray-300/80 leading-relaxed">
              {{ card.description }}
            </p>
            <!-- External link indicator -->
            <div v-if="card.externalUrl" class="mt-3 flex items-center text-purple-400 text-xs">
              <span class="mr-1">External link</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Add typing for window.cleanupDOM
declare global {
  interface Window {
    cleanupDOM?: () => void;
  }
}

import buttonFreeLesson from '@/assets/images/courses/button-free-lesson.svg'
import buttonAiCourse from '@/assets/images/courses/button-ai-course.svg'
import buttonIntensive from '@/assets/images/courses/button-intensive.svg'
import buttonApp from '@/assets/images/courses/button-app.svg'
import buttonChannel from '@/assets/images/courses/button-channel.svg'
import backgroundCourses from '@/assets/images/courses/background-courses.svg'
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import axios, { AxiosError } from 'axios'

// Add ref for root element
const coursesViewRef = ref<HTMLElement | null>(null);
const router = useRouter();

// Импортируем API клиент
import { apiClient } from '@/api/client';
import { useMainStore } from '@/store';

const mainStore = useMainStore();

// Function to handle card click
const handleCardClick = async (card: any) => {
  console.log('handleCardClick called for card:', card);

  if (card.externalUrl) {
    try {
      // Detailed logging before sending request
      console.log('Sending request to log transition:', {
        link_id: card.id.toString(),
        link_title: card.title,
        link_url: card.externalUrl,
        user_id: mainStore.user?.id || null,
        user: mainStore.user
      });

      // Check if API client is available
      console.log('API client available:', !!apiClient);
      console.log('logLinkClick method available:', !!apiClient.logLinkClick);
      console.log('API_ENDPOINTS.LOG_LINK_CLICK:', '/api/v1/analytics/link_click');

      // Get authorization data from Telegram
      const webApp = window.Telegram?.WebApp;
      const webAppData = webApp?.initData;

      console.log('Telegram authorization data:', {
        webApp: webApp ? 'available' : 'unavailable',
        webAppData: webAppData ? 'data available' : 'no data',
        webAppInitDataUnsafe: webApp?.initDataUnsafe ? 'data available' : 'no data',
        webAppUser: webApp?.initDataUnsafe?.user ? 'user exists' : 'no user'
      });

      // Получаем заголовок авторизации
      let authHeader = '';

      if (webAppData) {
        authHeader = `tma ${webAppData}`;
        console.log('Используем данные из WebApp:', authHeader.substring(0, 20) + '...');
      } else {
        // Проверяем, есть ли данные в localStorage
        const storedWebAppData = localStorage.getItem('tg_web_app_data');
        if (storedWebAppData) {
          authHeader = `tma ${storedWebAppData}`;
          console.log('Используем данные из localStorage:', authHeader.substring(0, 20) + '...');
        } else {
          console.warn('Не удалось получить данные авторизации Telegram');
        }
      }

      console.log('Заголовок авторизации:', authHeader ? 'Установлен' : 'Не установлен');

      // Логируем переход по ссылке напрямую через axios для отладки
      if (authHeader) {
        try {
          // Используем axios напрямую вместо приватного свойства client
          const directResponse = await axios.post(
            'https://aiteachers-api.ru.tuna.am/api/v1/analytics/link_click',
            {
              link_id: card.id.toString(),
              link_title: card.title,
              link_url: card.externalUrl,
              user_id: mainStore.user?.id || null
            },
            {
              withCredentials: true,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': authHeader
              }
            }
          );
          console.log('Прямой ответ от API при логировании перехода:', directResponse);
        } catch (error) {
          const directError = error as AxiosError;
          console.error('Ошибка при прямом вызове API:', directError);
          console.error('Детали ошибки:', {
            message: directError.message,
            response: directError.response?.data,
            status: directError.response?.status
          });
        }
      } else {
        console.warn('Пропускаем прямой вызов API, так как отсутствует заголовок авторизации');
      }

      // Логируем переход по ссылке через метод apiClient
      const response = await apiClient.logLinkClick({
        link_id: card.id.toString(),
        link_title: card.title,
        link_url: card.externalUrl,
        user_id: mainStore.user?.id || null
      });

      console.log('Ответ от API при логировании перехода:', response);
    } catch (err) {
      const error = err as AxiosError;
      console.error('Ошибка при логировании перехода:', error);
      console.error('Детали ошибки:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
    }

    // Open external link in new tab
    console.log('Opening link:', card.externalUrl);
    window.open(card.externalUrl, '_blank');
  } else {
    // Here you can add logic for internal links if needed
    console.log('Click on card without external link:', card.title);
  }
};

const cards = [
  {
    id: 1,
    title: 'Free AI Lesson',
    description: 'Get a free lesson on using AI in education',
    image: buttonFreeLesson,
    externalUrl: 'https://t.me/aiteachersbot'
  },
  {
    id: 2,
    title: 'AI Intensive Course',
    description: 'Intensive course on applying AI for teachers',
    image: buttonIntensive,
    externalUrl: 'https://ai-dlya-prepodavateley-o200pwe.gamma.site/'
  },
  {
    id: 3,
    title: 'AI Course - AI Universe',
    description: 'Complete course on artificial intelligence and neural networks for education',
    image: buttonAiCourse,
    externalUrl: 'https://ai4teachers.my.canva.site/2-0'
  },
  {
    id: 4,
    title: 'Request Custom App Development',
    description: 'Order development of your own application for your educational goals',
    image: buttonApp,
    externalUrl: 'https://t.me/yaroslav_english'
  },
  {
    id: 5,
    title: 'Channel About Trendsetting Projects',
    description: 'Join the channel to learn about creating trending projects',
    image: buttonChannel,
    externalUrl: 'https://t.me/anastasia_lvlup'
  },
  {
    id: 6,
    title: 'AI Community After Intensive',
    description: 'Join our community to continue learning and networking after the intensive',
    image: buttonIntensive,
    externalUrl: 'https://ai-dlya-uchiteley-vy25x4l.gamma.site/'
  }
]

// Component lifecycle handling
onMounted(() => {
  console.log('Courses: component is mounting');

  // Принудительно делаем компонент видимым
  if (coursesViewRef.value) {
    coursesViewRef.value.style.display = 'block';
    coursesViewRef.value.style.visibility = 'visible';
    coursesViewRef.value.style.opacity = '1';
    coursesViewRef.value.style.zIndex = '30';
    console.log('Courses: принудительно установлена видимость компонента');
  }

  // Проверяем, был ли переход с LessonPlan
  const lastRoute = localStorage.getItem('lastLessonPlanRoute');
  const lessonPlanUnmounted = localStorage.getItem('lessonPlanUnmounted');

  if (lastRoute && lastRoute.includes('lesson-plan') || lessonPlanUnmounted) {
    console.log('Courses: обнаружен переход с LessonPlan, выполняем дополнительную очистку');

    // Удаляем все элементы, связанные с LessonPlan
    const selectors = [
      '.lesson-plan-container',
      '[data-component="lesson-plan"]',
      '.planet-background',
      '.simple-toast-container',
      '.form-group',
      '.title-form-group',
      '.generation-form',
      '.result-container',
      '.plan-content'
    ];

    selectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        console.log(`Courses: найдено ${elements.length} элементов по селектору ${selector}`);

        elements.forEach(el => {
          try {
            // Скрываем и удаляем элемент
            (el as HTMLElement).style.display = 'none';
            (el as HTMLElement).style.visibility = 'hidden';
            (el as HTMLElement).style.opacity = '0';
            (el as HTMLElement).style.pointerEvents = 'none';
            (el as HTMLElement).style.zIndex = '-9999';

            // Удаляем элемент
            if (el.parentNode) {
              el.parentNode.removeChild(el);
            } else {
              el.remove();
            }
            console.log(`Courses: удален элемент ${selector}`);
          } catch (e) {
            console.error(`Courses: ошибка при удалении элемента ${selector}:`, e);
          }
        });
      }
    });

    // Проверяем наличие элементов с высоким z-index или fixed/absolute позиционированием
    const allElements = document.querySelectorAll('*');
    console.log('Courses: Проверяем все элементы DOM на наличие подозрительных стилей');

    allElements.forEach(el => {
      try {
        const styles = window.getComputedStyle(el);

        // Проверяем элементы с высоким z-index, fixed или absolute позиционированием
        if (
          (styles.position === 'fixed' || styles.position === 'absolute') &&
          (parseInt(styles.zIndex, 10) > 5 || styles.zIndex === 'auto') &&
          !el.classList.contains('bottom-navigation') &&
          !el.closest('.bottom-navigation') &&
          !el.classList.contains('dialog') &&
          !el.classList.contains('modal') &&
          !el.closest('.dialog') &&
          !el.closest('.modal')
        ) {
          // Проверяем, не содержит ли элемент или его родители атрибуты или классы, связанные с LessonPlan
          const elHtml = (el as HTMLElement).outerHTML.toLowerCase();
          const parentHtml = el.parentElement ? el.parentElement.outerHTML.toLowerCase() : '';

          if (
            elHtml.includes('lesson-plan') ||
            parentHtml.includes('lesson-plan') ||
            elHtml.includes('planet') ||
            parentHtml.includes('planet')
          ) {
            console.log('Courses: Найден подозрительный элемент с высоким z-index:', el);

            // Скрываем и удаляем элемент
            (el as HTMLElement).style.display = 'none';
            (el as HTMLElement).style.visibility = 'hidden';
            (el as HTMLElement).style.opacity = '0';
            (el as HTMLElement).style.pointerEvents = 'none';
            (el as HTMLElement).style.zIndex = '-9999';

            // Пытаемся удалить элемент
            try {
              if (el.parentNode) {
                el.parentNode.removeChild(el);
              } else {
                el.remove();
              }
              console.log('Courses: Удален подозрительный элемент');
            } catch (e) {
              console.error('Courses: Ошибка при удалении подозрительного элемента:', e);
            }
          }
        }
      } catch (e) {
        // Игнорируем ошибки при проверке стилей
      }
    });

    // Вызываем глобальную функцию очистки DOM
    if (typeof window.cleanupDOM === 'function') {
    window.cleanupDOM();
    console.log('Courses: вызвана глобальная функция очистки DOM');
    }
    
    // Очищаем информацию о переходе
    localStorage.removeItem('lastLessonPlanRoute');
    localStorage.removeItem('lessonPlanUnmounted');
  }

  // Восстанавливаем видимость основных компонентов
  const mainContent = document.querySelector('.main-content-container');
  if (mainContent) {
    (mainContent as HTMLElement).style.display = 'block';
    (mainContent as HTMLElement).style.visibility = 'visible';
    (mainContent as HTMLElement).style.opacity = '1';
    (mainContent as HTMLElement).style.zIndex = '10';
    console.log('Courses: восстановлена видимость main-content-container');
  }

  // Добавляем обработчик события размонтирования LessonPlan
  document.addEventListener('lessonplan-unmounted', (event: Event) => {
    console.log('Courses: получено событие lessonplan-unmounted', event);

    // Принудительно делаем компонент видимым
    if (coursesViewRef.value) {
      coursesViewRef.value.style.display = 'block';
      coursesViewRef.value.style.visibility = 'visible';
      coursesViewRef.value.style.opacity = '1';
      coursesViewRef.value.style.zIndex = '30';
      console.log('Courses: принудительно установлена видимость компонента после события lessonplan-unmounted');
    }

    // Вызываем глобальную функцию очистки DOM
    if (typeof window.cleanupDOM === 'function') {
      window.cleanupDOM();
      console.log('Courses: вызвана глобальная функция очистки DOM после события lessonplan-unmounted');
    }
  });

  // Добавляем обработчик события размонтирования Games
  document.addEventListener('games-unmounted', (event: Event) => {
    console.log('Courses: получено событие games-unmounted', event);

    // Принудительно делаем компонент видимым
    if (coursesViewRef.value) {
      coursesViewRef.value.style.display = 'block';
      coursesViewRef.value.style.visibility = 'visible';
      coursesViewRef.value.style.opacity = '1';
      coursesViewRef.value.style.zIndex = '30';
      console.log('Courses: принудительно установлена видимость компонента после события games-unmounted');
    }

    // Вызываем глобальную функцию очистки DOM
    if (typeof window.cleanupDOM === 'function') {
      window.cleanupDOM();
      console.log('Courses: вызвана глобальная функция очистки DOM после события games-unmounted');
    }
  });
});

onBeforeUnmount(() => {
  console.log('Courses: component is unmounting');

  // Note: event handlers were added as anonymous functions,
  // so they cannot be removed. This is not critical as they check
  // existence of elements before working.
});
</script>

<style scoped>
/* Ensure component visibility */
.courses-view {
  position: relative;
  z-index: 10;
  min-height: 100vh;
}
</style>
