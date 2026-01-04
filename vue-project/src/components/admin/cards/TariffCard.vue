<template>
  <div class="bg-gray-800 rounded-lg p-6 relative">
    <!-- Loading overlay -->
    <div v-if="isLoading" class="absolute inset-0 bg-gray-900/70 rounded-lg flex items-center justify-center z-10">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="bg-red-500/20 text-red-300 p-4 rounded-lg mb-4">
      <p>{{ error }}</p>
      <button
        @click="$emit('retry')"
        class="mt-2 px-4 py-2 bg-red-500/30 hover:bg-red-500/50 rounded-lg text-white"
      >
        Попробовать снова
      </button>
    </div>

    <!-- Content -->
    <div v-else>
      <div class="flex justify-between items-start">
        <div>
          <h3 class="text-lg font-semibold text-white">{{ tariff.name }}</h3>
          <p class="text-gray-400">{{ tariff.price_points }} баллов</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            :checked="tariff.is_active"
            @change="toggleTariff"
            :disabled="isLoading"
            class="sr-only peer"
          >
          <div class="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4
                      peer-focus:ring-purple-800 rounded-full peer
                      peer-checked:after:translate-x-full
                      after:content-[''] after:absolute after:top-[2px] after:left-[2px]
                      after:bg-white after:rounded-full after:h-5 after:w-5
                      after:transition-all peer-checked:bg-purple-500">
          </div>
        </label>
      </div>

      <div class="mt-4 space-y-2">
        <div class="flex justify-between items-center">
          <span class="text-gray-400">Лимит генераций:</span>
          <span class="text-white">{{ getLimitValue('generations_limit') }}/день</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-gray-400">Лимит изображений:</span>
          <span class="text-white">{{ getLimitValue('images_limit') }}/день</span>
        </div>
      </div>

      <div class="mt-6 space-y-2">
        <h4 class="text-sm font-medium text-gray-400">Возможности:</h4>
        <ul v-if="hasFeatures" class="space-y-1">
          <li v-for="(feature, index) in getFeatures"
              :key="index"
              class="text-white flex items-center gap-2"
          >
            <span class="text-green-400">✓</span>
            {{ feature }}
          </li>
        </ul>
        <p v-else class="text-gray-500 italic">Нет доступных возможностей</p>
      </div>

      <div class="mt-6">
        <button
          @click="$emit('edit', tariff)"
          :disabled="isLoading"
          class="w-full py-2 bg-gray-700 hover:bg-gray-600
                text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Редактировать
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Define Tariff interface based on actual API response
interface TariffFeature {
  name: string;
  description: string;
  enabled: boolean;
}

interface Tariff {
  id: number;
  type: string;
  name: string;
  price_points: number;
  generations_limit?: number;
  images_limit?: number;
  features?: string[] | TariffFeature[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  settings?: {
    generations_limit?: number;
    images_limit?: number;
  };
}

interface Props {
  tariff: Tariff;
  isLoading?: boolean;
  error?: string | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'edit', tariff: Tariff): void;
  (e: 'toggle', id: number, isActive: boolean): void;
  (e: 'retry'): void;
}>();

// Computed properties to handle different data structures
const getLimitValue = (limitType: 'generations_limit' | 'images_limit') => {
  // Check if limit is directly on tariff object
  if (typeof props.tariff[limitType] === 'number') {
    return props.tariff[limitType];
  }

  // Check if limit is in settings object
  if (props.tariff.settings && typeof props.tariff.settings[limitType] === 'number') {
    return props.tariff.settings[limitType];
  }

  // Default value
  return '—';
};

const hasFeatures = computed(() => {
  return Array.isArray(props.tariff.features) && props.tariff.features.length > 0;
});

const getFeatures = computed(() => {
  if (!Array.isArray(props.tariff.features)) {
    return [];
  }

  // Handle different feature formats
  if (typeof props.tariff.features[0] === 'string') {
    return props.tariff.features;
  } else {
    // If features are objects with name property
    return (props.tariff.features as TariffFeature[])
      .filter(feature => feature.enabled)
      .map(feature => feature.name);
  }
});

// Methods
const toggleTariff = () => {
  emit('toggle', props.tariff.id, !props.tariff.is_active);
};
</script>
