// src/components/LoadingState.vue
<template>
  <div class="loading-state" v-if="isLoading">
    <div class="loading-animation">
      <div class="spinner"></div>
    </div>
    <p class="loading-text">{{ loadingText }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  isLoading: boolean;
  loadingText?: string;
}

withDefaults(defineProps<Props>(), {
  loadingText: 'Генерация контента...'
});
</script>

<style scoped>
.loading-state {
  width: 100%;
  text-align: center;
  padding: 2rem;
}

.loading-animation {
  margin-bottom: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto;
  border: 3px solid transparent;
  border-top: 3px solid #8B5CF6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  color: #9CA3AF;
  font-size: 0.875rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
