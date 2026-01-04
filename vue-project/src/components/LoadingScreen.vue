<template>
  <div class="loading-screen">
    <div class="stars-container">
      <!-- Увеличиваем количество звезд -->
      <div class="star" v-for="n in 150" :key="`star-${n}`" :style="starStyle(n)"></div>
    </div>
    <!-- Шаттл v3 (Более строгий стиль) -->
    <svg class="rocket" viewBox="-15 -10 90 150" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <!-- Градиенты для корпуса и крыльев -->
        <linearGradient id="shuttleBodyGradientV3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#e0e0e0"/>
          <stop offset="50%" stop-color="#ffffff"/>
          <stop offset="100%" stop-color="#e0e0e0"/>
        </linearGradient>
        <linearGradient id="shuttleWingGradientV3" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#cccccc"/>
          <stop offset="100%" stop-color="#a0a0a0"/>
         </linearGradient>
         <!-- Градиент для красивого огненного выхлопа -->
         <radialGradient id="fireGradient" cx="50%" cy="80%" r="70%" fx="50%" fy="100%">
            <stop offset="0%" stop-color="#FFFDE7" stop-opacity="1"/> <!-- Ярко-желтый центр -->
            <stop offset="30%" stop-color="#FFECB3" stop-opacity="0.9"/>
            <stop offset="60%" stop-color="#FFB74D" stop-opacity="0.7"/> <!-- Оранжевый -->
            <stop offset="90%" stop-color="#E65100" stop-opacity="0.3"/> <!-- Темно-оранжевый/красный -->
            <stop offset="100%" stop-color="#BF360C" stop-opacity="0.1"/> <!-- Почти прозрачный красный -->
         </radialGradient>
         <!-- Фильтры для размытия -->
         <filter id="exhaustBlurV3" x="-50%" y="-50%" width="200%" height="200%">
           <feGaussianBlur in="SourceGraphic" stdDeviation="5" /> <!-- Чуть больше размытия -->
         </filter>
         <filter id="coreBlurV3" x="-50%" y="-50%" width="200%" height="200%">
           <feGaussianBlur in="SourceGraphic" stdDeviation="3" /> <!-- Чуть больше размытия ядра -->
         </filter>
       </defs>

       <!-- Выхлоп (красивый огонь) -->
       <g class="exhaust" filter="url(#exhaustBlurV3)">
         <!-- Несколько слоев для объема -->
         <ellipse cx="30" cy="120" rx="22" ry="45" fill="url(#fireGradient)" class="flame flame-outer" opacity="0.6"/>
         <ellipse cx="30" cy="115" rx="15" ry="35" fill="url(#fireGradient)" class="flame flame-mid" opacity="0.8"/>
         <ellipse cx="30" cy="110" rx="8" ry="25" fill="#FFFFE0" class="flame flame-core" filter="url(#coreBlurV3)" opacity="1"/> <!-- Яркое ядро -->
       </g>

       <!-- Корпус Шаттла (оставляем как есть) -->
      <path d="M30 0 L0 30 C-5 50, -5 70, 5 90 L20 100 H40 L55 90 C65 70, 65 50, 60 30 Z" fill="url(#shuttleBodyGradientV3)" stroke="#444" stroke-width="0.4"/>
      <!-- Носовая часть (темная) -->
      <path d="M30 0 L0 30 C10 15, 50 15, 60 30 Z" fill="#555"/>
      <!-- Крылья (более угловатые) -->
      <path d="M5 50 C-20 65, -20 85, 5 95 L15 85 C0 80, 0 60, 5 50 Z" fill="url(#shuttleWingGradientV3)" stroke="#333" stroke-width="0.2"/>
      <path d="M55 50 C80 65, 80 85, 55 95 L45 85 C60 80, 60 60, 55 50 Z" fill="url(#shuttleWingGradientV3)" stroke="#333" stroke-width="0.2"/>
      <!-- Хвостовой стабилизатор (вертикальный) -->
      <path d="M25 85 L20 100 H40 L35 85 C33 80, 27 80, 25 85 Z" fill="#bdbdbd" stroke="#333" stroke-width="0.2"/>
      <!-- Сопла (чуть детальнее) -->
      <rect x="22" y="98" width="6" height="4" fill="#444" rx="1"/>
      <rect x="32" y="98" width="6" height="4" fill="#444" rx="1"/>
    </svg>
    <div class="quote-container">
      <p class="quote">"{{ currentQuote.text }}"</p>
      <p class="author">- {{ currentQuote.author }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Quote {
  text: string;
  author: string;
}

const quotes: Quote[] = [
  { text: "Education is not preparation for life; education is life itself.", author: "John Dewey" },
  { text: "The only true wisdom is in knowing you know nothing.", author: "Socrates" },
  { text: "The purpose of learning is growth, and our minds, unlike our bodies, can continue growing as long as we live.", author: "Mortimer Adler" },
  { text: "Tell me and I forget. Show me and I remember. Involve me and I understand.", author: "Confucius" },
  { text: "An investment in knowledge pays the best interest.", author: "Benjamin Franklin" },
  { text: "The mind is not a vessel to be filled, but a fire to be kindled.", author: "Plutarch" },
  { text: "The task of the modern educator is not to cut down jungles, but to irrigate deserts.", author: "C.S. Lewis" },
];

const currentQuote = ref<Quote>(quotes[0]); // Инициализация

onMounted(() => {
  const randomIndex = Math.floor(Math.random() * quotes.length);
  currentQuote.value = quotes[randomIndex];
});

// Функция для генерации случайных стилей звезд
const starStyle = (n: number) => {
  const size = Math.random() * 2.5 + 1; // Увеличиваем макс. размер до 3.5px
  const top = Math.random() * 100; // Позиция по вертикали
  const left = Math.random() * 100; // Позиция по горизонтали
  const delay = Math.random() * 5; // Задержка анимации
  const duration = Math.random() * 3 + 2; // Длительность анимации

  return {
    width: `${size}px`,
    height: `${size}px`,
    top: `${top}%`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
  };
};
</script>

<style scoped>
.loading-screen {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* Темно-синий градиент */
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  color: white;
  z-index: 50; /* Должен быть выше остального контента */
  text-align: center;
  overflow: hidden; /* Скрыть звезды, выходящие за пределы */
}

.stars-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Чтобы не мешать кликам */
}

.star {
  position: absolute;
  background-color: white;
  border-radius: 50%;
  opacity: 0;
  /* Добавляем свечение */
  box-shadow: 0 0 4px #fff, 0 0 6px #fff;
  animation: twinkle linear infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 1; transform: scale(1); }
}

/* Стили и анимация для ракеты v3 */
.rocket {
  position: absolute;
  width: 70px; /* Слегка увеличим */
  height: 140px;
  bottom: -180px; /* Стартует еще ниже */
  left: 25%;
  z-index: 2;
  animation: flyUpV3 8s ease-out infinite; /* Дольше, плавнее выход */
  filter: drop-shadow(0 0 6px rgba(180, 180, 220, 0.4)); /* Холодное свечение */
}

.rocket .exhaust {
   transform-origin: 30px 100px; /* Центр у основания сопел */
 }

 .rocket .flame {
   /* Применяем анимацию ко всем слоям пламени */
   animation: firePulse 0.18s ease-in-out infinite alternate;
 }
 .rocket .flame-mid {
    animation-delay: 0.05s; /* Небольшие задержки для слоев */
 }
 .rocket .flame-core {
    animation-delay: 0.09s;
 }


 @keyframes flyUpV3 {
  /* Еще более плавный полет, почти без вращения */
  0% {
    bottom: -180px;
    left: 25%;
    transform: scale(0.5) rotate(-2deg);
    opacity: 0.7;
  }
  20% {
     transform: scale(0.7) rotate(0deg);
     opacity: 1;
  }
  100% {
    bottom: 120%; /* Улетает дальше */
    left: 55%;
    transform: scale(1) rotate(1deg);
    opacity: 1;
  }
 }

 /* Более энергичная пульсация огня */
 @keyframes firePulse {
   0% {
     transform: scale(0.9, 0.95) skewX(-2deg);
     opacity: 0.75;
   }
   100% {
     transform: scale(1.1, 1.05) skewX(2deg);
     opacity: 1;
   }
 }


 .quote-container {
  padding: 20px;
  max-width: 80%;
  z-index: 1; /* Поверх звезд */
  background-color: rgba(0, 0, 0, 0.3); /* Полупрозрачный фон для читаемости */
  border-radius: 8px;
}

.quote {
  font-size: 1.1em; /* Немного уменьшил */
  margin-bottom: 10px;
  font-style: italic;
  line-height: 1.4;
}

.author {
  font-size: 0.9em; /* Немного уменьшил */
  color: #cbd5e1; /* Светло-серый */
}
</style>
