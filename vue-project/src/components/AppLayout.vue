# src/components/AppLayout.vue
<template>
  <div class="min-h-screen bg-gray-900 text-white">
    <!-- Loading overlay -->
    <div v-if="store.isLoading"
         class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
    </div>

    <!-- Main layout -->
    <div class="max-w-7xl mx-auto px-4 py-6">
      <!-- Header with user info and tariff -->
      <header class="mb-6">
        <div class="bg-gray-800 rounded-lg p-4">
          <div class="flex items-center justify-between">
            <!-- User info -->
            <div class="flex items-center gap-4">
              <div class="flex flex-col">
                <span class="font-medium">{{ store.user?.first_name }}</span>
                <span class="text-sm text-gray-400">{{ getTariffName(store.user?.tariff) }}</span>
              </div>
            </div>

            <!-- Points and limits -->
            <div class="flex items-center gap-6">
              <!-- Available generations -->
              <div class="text-center">
                <div class="text-sm text-gray-400">Generations</div>
                <div class="font-medium">
                  {{ store.remainingGenerations(ContentType.LESSON_PLAN) }}/
                  {{ getTariffLimit(store.user?.tariff, 'generations') }}
                </div>
              </div>

              <!-- Available images -->
              <div class="text-center">
                <div class="text-sm text-gray-400">Images</div>
                <div class="font-medium">
                  {{ store.remainingGenerations(ContentType.IMAGE) }}/
                  {{ getTariffLimit(store.user?.tariff, 'images') }}
                </div>
              </div>

              <!-- Points -->
              <div class="text-center">
                <div class="text-sm text-gray-400">Points</div>
                <div class="font-medium">{{ store.user?.points || 0 }}</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- Navigation menu -->
      <nav class="mb-6">
        <div class="bg-gray-800 rounded-lg p-2">
          <div class="flex items-center justify-around">
            <router-link
              v-for="item in navigationItems"
              :key="item.path"
              :to="item.path"
              class="px-4 py-2 rounded-lg transition-colors"
              :class="[
                route.path === item.path
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white'
              ]"
            >
              {{ item.name }}
            </router-link>
          </div>
        </div>
      </nav>

      <!-- Main content -->
      <main>
        <slot></slot>
      </main>
    </div>

    <!-- Not ready state -->
    <div v-else class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500 mx-auto mb-4"></div>
        <p class="text-gray-400">Loading application...</p>
      </div>
    </div>

    <!-- Error toast -->
    <div
      v-if="store.error"
      class="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg"
    >
      {{ store.error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMainStore } from '@/store';
import { useRoute } from 'vue-router';
import { ContentType, TariffType } from '@/core/constants';

const store = useMainStore();
const route = useRoute();


// Навигационные элементы
const navigationItems = [
  { name: 'Lessons', path: '/lessons' },
  { name: 'Exercises', path: '/exercises' },
  { name: 'Games', path: '/games' },
  { name: 'Images', path: '/images' }
];

// Преобразование типа тарифа в читаемое название
const getTariffName = (tariff: TariffType | undefined) => {
  if (!tariff) return 'No tariff';

  const names = {
    [TariffType.BASIC]: 'Basic tariff',
    [TariffType.STANDARD]: 'Standard tariff',
    [TariffType.PREMIUM]: 'Premium tariff'
  };

  return names[tariff];
};

// Получение лимитов тарифа
const getTariffLimit = (tariff: TariffType | undefined, type: 'generations' | 'images') => {
  if (!tariff) return 0;

  const limits = {
    [TariffType.BASIC]: { generations: 6, images: 2 },
    [TariffType.STANDARD]: { generations: 12, images: 5 },
    [TariffType.PREMIUM]: { generations: 25, images: 8 }
  };

  return limits[tariff][type];
};
</script>
