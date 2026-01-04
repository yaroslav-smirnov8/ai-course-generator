<template>
  <div class="optimized-image-container" :class="{ 'loading': isLoading, 'loaded': !isLoading && isLoaded }">
    <!-- Placeholder во время загрузки -->
    <div v-if="isLoading" class="image-placeholder" :style="{ paddingBottom: `${aspectRatio}%` }">
      <div class="loading-spinner"></div>
    </div>
    
    <!-- Изображение с ленивой загрузкой -->
    <img
      v-if="optimizedSrc"
      :src="optimizedSrc"
      :alt="alt"
      :width="width"
      :height="height"
      :class="['optimized-image', { 'blur-up': blurUp }]"
      loading="lazy"
      @load="onImageLoaded"
      @error="onImageError"
    />
    
    <!-- Низкокачественный предпросмотр для blur-up эффекта -->
    <img
      v-if="blurUp && placeholderSrc"
      :src="placeholderSrc"
      :alt="alt"
      class="placeholder-image"
      :style="{ opacity: isLoaded ? 0 : 1 }"
    />
    
    <!-- Сообщение об ошибке -->
    <div v-if="hasError" class="image-error">
      <slot name="error">
        <span>Не удалось загрузить изображение</span>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getOptimizedImageUrl } from '@/services/imageOptimizer'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  alt: {
    type: String,
    default: ''
  },
  width: {
    type: [Number, String],
    default: null
  },
  height: {
    type: [Number, String],
    default: null
  },
  aspectRatio: {
    type: Number,
    default: 56.25 // 16:9 по умолчанию
  },
  blurUp: {
    type: Boolean,
    default: true
  },
  placeholderSrc: {
    type: String,
    default: ''
  }
})

const isLoading = ref(true)
const isLoaded = ref(false)
const hasError = ref(false)
const optimizedSrc = ref<string | null>(null)

// Вычисляем оптимизированный URL изображения
const loadOptimizedImage = async () => {
  try {
    optimizedSrc.value = await getOptimizedImageUrl(props.src)
  } catch (error) {
    console.error('Failed to optimize image:', error)
    optimizedSrc.value = props.src // Fallback на оригинальный URL
  }
}

// Обработчики событий
const onImageLoaded = () => {
  isLoading.value = false
  isLoaded.value = true
}

const onImageError = () => {
  isLoading.value = false
  hasError.value = true
}

// Инициализация
onMounted(() => {
  loadOptimizedImage()
})
</script>

<style scoped>
.optimized-image-container {
  position: relative;
  overflow: hidden;
  width: 100%;
}

.image-placeholder {
  background-color: #f0f0f0;
  position: relative;
  width: 100%;
}

.loading-spinner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.optimized-image {
  display: block;
  width: 100%;
  height: auto;
  transition: opacity 0.3s ease;
}

.placeholder-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  filter: blur(10px);
  transition: opacity 0.3s ease;
  object-fit: cover;
}

.blur-up {
  opacity: 0;
}

.loaded .blur-up {
  opacity: 1;
}

.image-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8d7da;
  color: #721c24;
  padding: 1rem;
  text-align: center;
}

@keyframes spin {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

/* Темная тема */
:root[data-theme="dark"] .image-placeholder {
  background-color: #2d2d2d;
}

:root[data-theme="dark"] .loading-spinner {
  border-color: rgba(255, 255, 255, 0.1);
  border-top-color: #3498db;
}

:root[data-theme="dark"] .image-error {
  background-color: #2c1215;
  color: #f8d7da;
}
</style> 