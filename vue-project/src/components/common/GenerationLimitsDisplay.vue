<template>
  <div class="generation-limits p-4 mb-6 rounded-lg" :class="limitClass">
    <div class="flex justify-between items-center">
      <div>
        <h3 class="font-medium text-white">{{ title }}</h3>
        <p class="text-sm mt-1" :class="textColorClass">
          {{ message }}
        </p>
      </div>
      <div v-if="showCount" class="text-lg font-bold" :class="countClass">
        {{ remaining }}/{{ limit }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useMainStore } from '@/store';
import { ContentType, UNLIMITED_ROLES, UserRole } from '@/core/constants';

const props = defineProps({
  type: {
    type: String,
    default: ContentType.LESSON_PLAN
  }
});

const store = useMainStore();

// Computed properties
const remaining = computed(() => store.remainingGenerations(props.type));
const limit = computed(() => {
  if (store.tariffInfo) {
    return props.type === ContentType.IMAGE
      ? store.tariffInfo.limits.images
      : store.tariffInfo.limits.generations;
  }
  return 0;
});

const hasLimits = computed(() => {
  // Check if user has unlimited access
  if (store.user?.role && UNLIMITED_ROLES.includes(store.user.role)) {
    return false;
  }
  return true;
});

const showCount = computed(() => hasLimits.value && limit.value > 0);

const title = computed(() => {
  if (!hasLimits.value) {
    return "Unlimited Access";
  }

  if (remaining.value <= 0) {
    return "Daily Limit Reached";
  }

  return "Generation Limits";
});

const message = computed(() => {
  if (!hasLimits.value) {
    return "You have unlimited access to content generation";
  }

  if (remaining.value <= 0) {
    return "You have reached your daily limit. Please upgrade your plan or try again tomorrow.";
  }

  const typeLabel = props.type === ContentType.IMAGE ? "images" : "lesson plans";
  return `You can generate ${remaining.value} more ${typeLabel} today`;
});

const limitClass = computed(() => {
  if (!hasLimits.value) {
    return "bg-blue-900/30 border border-blue-700";
  }

  if (remaining.value <= 0) {
    return "bg-red-900/30 border border-red-700";
  }

  if (remaining.value < limit.value * 0.3) {
    return "bg-yellow-900/30 border border-yellow-700";
  }

  return "bg-green-900/30 border border-green-700";
});

const textColorClass = computed(() => {
  if (!hasLimits.value) {
    return "text-blue-300";
  }

  if (remaining.value <= 0) {
    return "text-red-300";
  }

  if (remaining.value < limit.value * 0.3) {
    return "text-yellow-300";
  }

  return "text-green-300";
});

const countClass = computed(() => {
  if (remaining.value <= 0) {
    return "text-red-300";
  }

  if (remaining.value < limit.value * 0.3) {
    return "text-yellow-300";
  }

  return "text-green-300";
});
</script>
