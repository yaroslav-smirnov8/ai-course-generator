<template>
  <div 
    class="ai-chat-assistant-view" 
    :style="backgroundStyles"
  >
    <AIChatAssistant />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AIChatAssistant from './AIChatAssistant.vue'

// Фоновое изображение для темы
import bgOverlay from '@/assets/images/home/ai_assistant_bg_overlay.svg'

const backgroundStyles = computed(() => ({
  backgroundImage: `url(${bgOverlay})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat'
}))
</script>

<style scoped>
.ai-chat-assistant-view {
  position: relative;
  width: 100%;
  min-height: 100vh;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  background: #1c0522;
}
</style> 