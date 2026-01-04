<template>
  <div 
    class="ai-chat-assistant-view" 
    :style="backgroundStyles"
  >
    <AIChatAssistant />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AIChatAssistant from '@/components/AIChatAssistant.vue'

// Background image for space theme
import bgOverlay from '@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg'

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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  background: #1c0522;
  -webkit-overflow-scrolling: touch;
}

/* Apply styles to root element for better scrolling */
:deep(html), :deep(body) {
  overflow-y: auto !important;
  height: auto !important;
  background: #1c0522;
}
</style> 