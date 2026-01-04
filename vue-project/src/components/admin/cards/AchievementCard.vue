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
      <div class="flex items-start justify-between">
        <div>
          <span class="text-2xl">{{ achievement.icon || '🏆' }}</span>
          <h3 class="text-lg font-semibold text-white mt-2">{{ achievement.name }}</h3>
          <p class="text-gray-400 text-sm mt-1">{{ achievement.description }}</p>
        </div>
      </div>

      <div class="mt-4">
        <div class="flex justify-between text-sm mb-1">
          <span class="text-gray-400">Код:</span>
          <span class="text-white font-mono">{{ achievement.code }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-gray-400">Награда:</span>
          <span class="text-yellow-400">{{ getPointsReward }} баллов</span>
        </div>
      </div>

      <div class="mt-4">
        <h4 class="text-sm font-medium text-gray-400 mb-2">Условия:</h4>
        <div v-if="hasConditions" class="space-y-1">
          <div v-for="(value, key) in achievement.conditions"
               :key="key"
               class="text-sm text-white"
          >
            {{ formatCondition(key, value) }}
          </div>
        </div>
        <p v-else class="text-gray-500 italic text-sm">Нет условий</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Edit as EditIcon } from 'lucide-vue-next';

// Define Achievement interface based on actual API response
interface AchievementConditions {
  type?: string;
  required_count?: number;
  content_type?: string;
  consecutive_days?: number;
  invites_count?: number;
  generation_count?: number;
  [key: string]: any;
}

interface Achievement {
  id: string | number;
  code: string;
  name: string;
  description: string;
  icon?: string;
  conditions: AchievementConditions;
  points_reward: number;
}

interface Props {
  achievement: Achievement;
  isLoading?: boolean;
  error?: string | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'retry'): void;
}>();

// Computed properties
const hasConditions = computed(() => {
  return props.achievement.conditions &&
         Object.keys(props.achievement.conditions).length > 0;
});

const getPointsReward = computed(() => {
  return props.achievement.points_reward || 0;
});

// Methods
const formatCondition = (key: string, value: any): string => {
  if (value === null || value === undefined) {
    return '';
  }

  switch (key) {
    case 'type':
      return `Тип: ${formatConditionType(value)}`;
    case 'generation_count':
    case 'required_count':
      return `Создать ${value} генераций`;
    case 'consecutive_days':
      return `${value} дней подряд`;
    case 'invites_count':
      return `Пригласить ${value} пользователей`;
    case 'content_type':
      return `Тип контента: ${formatContentType(value)}`;
    default:
      return `${key}: ${value}`;
  }
};

const formatConditionType = (type: string): string => {
  const types: Record<string, string> = {
    'generation': 'Генерация',
    'login': 'Вход',
    'invite': 'Приглашение',
    'consecutive': 'Последовательность',
    'purchase': 'Покупка'
  };

  return types[type] || type;
};

const formatContentType = (type: string): string => {
  const types: Record<string, string> = {
    'lesson_plan': 'Lesson Plan',
    'exercise': 'Exercise',
    'game': 'Game',
    'image': 'Image',
    'text_analysis': 'Text Analysis',
    'concept_explanation': 'Concept Explanation',
    'course': 'Course',
    'free_query': 'AI Assistant'
  };

  return types[type] || type;
};
</script>
