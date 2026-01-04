<!-- src/components/Home.vue -->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMainStore } from '@/store'
import { Settings, Shield, LayoutDashboard } from 'lucide-vue-next'
import { usePremiumAccess } from '@/composables/usePremiumAccess'

// Импорты изображений
import homeBackground from '../assets/images/home/home-backgroud-image.svg'
import exercisesBackground from '../assets/images/home/exercises-background-image.svg'
import buttonGame from '../assets/images/home/button-game.svg'
import buttonCourses from '../assets/images/home/button-courses.svg'
import buttonExercises from '../assets/images/home/button-exercises.svg'
import buttonImages from '../assets/images/home/button-images.svg'
import buttonLessonPlan from '../assets/images/home/button-lesson-plan.svg'
import buttonLessons from '../assets/images/home/button-lessons.svg'
import buttonGuide from '../assets/images/home/button-guide.svg'
import buttonVideoTranscript from '../assets/images/home/button-video-transcript.svg'
import controlCoursesButton from '../assets/images/home/control-courses-button.svg'
import controlHomeButton from '../assets/images/home/control-home-button.svg'
import controlPanelBackground from '../assets/images/home/Control Panel Background.svg'
import controlModeButton from '../assets/images/home/control-mode-button.svg'

const store = useMainStore()
const router = useRouter()
const { hasPremiumAccess } = usePremiumAccess()

// Добавляем ref для корневого элемента
const homeViewRef = ref<HTMLElement | null>(null);

// Data for generation section
const generationCards = [
  {
    id: 'lesson-plan',
    title: 'Lesson Plan',
    description: 'Lesson Plan',
    route: '/lesson-plan',
    icon: buttonLessonPlan,
    background: buttonLessonPlan
  },
  {
    id: 'exercises',
    title: 'Exercises',
    route: '/exercises',
    icon: buttonExercises,
    background: buttonExercises
  },
  {
    id: 'lesson-plan-detailed',
    title: 'Course Generator',
    description: 'Create a complete course with methodology and learning goals',
    route: '/courses/create',
    icon: buttonLessonPlan,
    background: buttonLessonPlan,
    requiresPremium: true
  },
  {
    id: 'ai-assistant',
    title: 'AI Assistant',
    description: 'AI assistant for tutors',
    route: '/ai-assistant',
    icon: buttonLessonPlan,
    background: buttonLessonPlan,
    requiresPremium: true
  },
  {
    id: 'concept-explainer',
    title: 'Concept Explainer',
    description: 'Explain complex concepts in simple words',
    route: '/concept-explainer',
    icon: buttonLessonPlan,
    background: buttonLessonPlan
  },
  {
    id: 'text-analyzer',
    title: 'Text Trainer',
    description: 'Text analysis and practice',
    route: '/text-analyzer',
    icon: buttonLessonPlan,
    background: buttonLessonPlan
  },
  {
    id: 'games',
    title: 'Games',
    route: '/games',
    icon: buttonGame,
    background: buttonGame
  },
  {
    id: 'images',
    title: 'Images',
    route: '/image-generation',
    icon: buttonImages,
    background: buttonImages
  },
  {
    id: 'transcripts',
    title: 'Video Transcript',
    route: '/video-transcript',
    icon: buttonVideoTranscript,
    background: buttonVideoTranscript
  }
]

// Data for education section
const educationCards = [
  {
    id: 'courses',
    title: 'Free Lessons and Courses',
    route: '/courses',
    icon: buttonLessons,
    background: buttonLessons
  },
  {
    id: 'free-lessons',
    title: 'App Guide',
    route: '/free-lessons',
    icon: buttonGuide,
    background: buttonGuide
  }
]

// Проверка на права администратора или модератора
const hasAdminAccess = computed(() => store.hasAdminAccess)

// Обработчик нажатия на карточку
const handleCardClick = (route: string, requiresPremium?: boolean) => {
  // If feature requires premium access and user doesn't have it
  if (requiresPremium && !hasPremiumAccess.value) {
    // Show message about premium requirement
    store.setError('Premium plan required to access this feature')
    router.push('/profile') // Redirect to profile page where user can purchase plan
    return
  }

  router.push(route)
}

// Обработчик нажатия на кнопку профиля
const goToProfile = () => {
  router.push('/profile')
}

// Функция перехода в админ-панель
const goToAdmin = () => {
  router.push('/admin')
}

// Добавляем обработку для исправления отображения после плана урока
onMounted(() => {
  console.log('Home view mounted');

  // Проверяем, откуда мы пришли (из localStorage)
  const lastRoute = localStorage.getItem('lastRoute');
  let fromLessonPlan = false;

  if (lastRoute) {
    try {
      const parsed = JSON.parse(lastRoute);
      if (parsed.path && parsed.path.includes('/lesson-plan')) {
        fromLessonPlan = true;
        console.log('Home: детектирован переход с плана урока');
      }
    } catch (e) {
      console.error('Ошибка при чтении lastRoute:', e);
    }
  }

  // Если пришли с плана урока, принудительно делаем компонент видимым
  if (fromLessonPlan && homeViewRef.value) {
    // Делаем компонент видимым с задержкой (чтобы дать время другим процессам завершиться)
    setTimeout(() => {
      if (homeViewRef.value) {
        const el = homeViewRef.value;
        el.style.display = 'block';
        el.style.visibility = 'visible';
        el.style.opacity = '1';
        el.style.zIndex = '10'; // Используем z-index контента

        // Проверяем, что основной контейнер виден
        const mainContent = document.querySelector('.main-content-container');
        if (mainContent) {
          (mainContent as HTMLElement).style.display = 'block';
          (mainContent as HTMLElement).style.visibility = 'visible';
          (mainContent as HTMLElement).style.opacity = '1';
        }

        console.log('Home: принудительное восстановление видимости');
      }
    }, 100);

    // Дополнительно очищаем любые оставшиеся элементы плана урока
    setTimeout(() => {
      const lessonPlanElements = document.querySelectorAll('.lesson-plan-container');
      lessonPlanElements.forEach(el => {
        try {
          el.remove();
          console.log('Home: удален оставшийся элемент плана урока');
        } catch (e) {
          console.error('Ошибка при удалении элемента плана урока:', e);
        }
      });
    }, 200);
  }
});
</script>

<template>
  <div class="home-view" ref="homeViewRef">
    <div class="home min-h-screen pb-16">
      <!-- Заголовок с плашкой -->
      <header class="relative min-h-[49.9vh]">
        <!-- Кнопка админ-панели только для админов и модераторов -->
        <div v-if="hasAdminAccess" class="absolute top-4 right-4 z-10">
          <button @click="goToAdmin" class="admin-button-new">
            <LayoutDashboard class="w-5 h-5 mr-1" />
            <span>Admin Panel</span>
          </button>
        </div>

        <!-- Текст с плашкой -->
        <div class="relative pt-[39.9vh] px-6">
          <div class="bg-[#2D1E3E]/80 backdrop-blur-md rounded-2xl p-6 text-center">
            <h1 class="text-2xl font-bold text-white mb-2">
              Welcome to the AI Universe!
            </h1>
            <p class="text-gray-300 text-sm">
              This project aims to create new education through the latest approaches and technologies for creating educational products accessible to everyone
            </p>
          </div>
        </div>
      </header>

      <!-- Секция генераций -->
      <section class="mt-12 mb-05">
        <h2 class="text-xl font-semibold text-white pl-10 pr-5 mb-0125">Generations</h2>

        <div class="overflow-x-auto hide-scrollbar">
          <div class="inline-flex gap-025 px-4">
            <div
              v-for="card in generationCards"
              :key="card.id"
              class="w-64 flex-none"
            >
              <button
                @click="handleCardClick(card.route, card.requiresPremium)"
                class="w-full aspect-video relative group glow-effect"
                :class="{ 'premium-locked': card.requiresPremium && !hasPremiumAccess }"
              >
                <img
                  :src="card.background"
                  class="w-full h-full object-cover rounded-2xl"
                  :class="{ 'opacity-50': card.requiresPremium && !hasPremiumAccess }"
                  alt=""
                />

                <!-- Премиум бейдж -->
                <div
                  v-if="card.requiresPremium && !hasPremiumAccess"
                  class="absolute top-2 right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-1 rounded-full font-medium"
                >
                  Premium
                </div>

                <!-- Иконка замка для заблокированных функций -->
                <div
                  v-if="card.requiresPremium && !hasPremiumAccess"
                  class="absolute inset-0 flex items-center justify-center"
                >
                  <div class="bg-black/50 rounded-full p-3 mb-8">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                    </svg>
                  </div>
                </div>

                <div class="absolute inset-0 flex items-center justify-center">
                  <h3 class="text-white font-medium text-lg text-shadow-strong">{{ card.title }}</h3>
                </div>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Секция обучения -->
      <section class="mb-025">
        <h2 class="text-xl font-semibold text-white pl-10 pr-5 mb-0125">Education</h2>

        <div class="overflow-x-auto hide-scrollbar">
          <div class="inline-flex gap-07 px-4">
            <div
              v-for="card in educationCards"
              :key="card.id"
              class="w-64 flex-none"
            >
              <button
                @click="handleCardClick(card.route)"
                class="w-full aspect-video relative group glow-effect"
              >
                <img
                  :src="card.background"
                  class="w-full h-full object-cover rounded-2xl"
                  alt=""
                />
                <div class="absolute inset-0 flex items-center justify-center">
                  <h3 class="text-white font-medium text-lg text-shadow-strong">{{ card.title }}</h3>
                </div>
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home {
  background-image:
    url('../assets/images/home/home-backgroud-image.svg');
  background-size:
    70% auto;  /* Reduce planet size */
  background-position:
    center 3%;  /* Move planet higher */
  background-repeat: no-repeat;
  min-height: 100vh;
}

/* Медиа-запрос для мобильных устройств */
@media (max-width: 768px) {
  .home {
    background-size:
      85% auto;
    background-position:
      center 2%;  /* Move planet higher on mobile */
  }
}

.glow-effect {
  position: relative;
  overflow: visible;
}

.glow-effect::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: radial-gradient(
    circle at 50% 50%,
    rgba(147, 51, 234, 0.3),
    transparent 70%
  );
  border-radius: inherit;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.glow-effect:hover::before {
  opacity: 1;
}

.glow-effect:hover {
  transform: scale(1.02);
  transition: transform 0.3s ease;
}

.overflow-x-auto {
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

.hide-scrollbar {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

.text-shadow-strong {
  text-shadow:
    0 0 4px rgba(0, 0, 0, 0.8),
    0 0 8px rgba(0, 0, 0, 0.6);
}

/* Custom margins */
.gap-025 {
  gap: 0.25rem !important; /* 4px */
}

.gap-07 {
  gap: 0.7rem !important; /* ~11px */
}

.mb-0125 {
  margin-bottom: 0.125rem !important; /* 2px */
}

.mb-025 {
  margin-bottom: 0.25rem !important; /* 4px */
}

.mb-05 {
  margin-bottom: 0.5rem !important; /* 8px */
}

.profile-button {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(5px);
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
}

.profile-button:hover {
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.3);
}

.profile-button:active {
  transform: scale(0.95);
}

/* Ensure component visibility */
.home-view {
  position: relative;
  z-index: 10;
  min-height: 100vh;
}

/* Styles for admin panel button */
.admin-button-new {
  @apply flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600
         text-white font-medium rounded-lg shadow-lg transition-all duration-300
         backdrop-blur-sm border border-purple-500/30;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.3), 0 1px 3px rgba(0, 0, 0, 0.1);
}

.admin-button-new:hover {
  @apply from-purple-700 to-indigo-700;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.4), 0 2px 5px rgba(0, 0, 0, 0.15);
}

.admin-button-new:active {
  @apply from-purple-800 to-indigo-800;
  transform: translateY(0);
  box-shadow: 0 2px 10px rgba(147, 51, 234, 0.2), 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Styles for locked premium features */
.premium-locked {
  cursor: not-allowed;
}

.premium-locked:hover {
  transform: none !important;
}

.premium-locked:hover::before {
  opacity: 0 !important;
}
</style>
