<template>
  <div class="text-analyzer-container" :style="backgroundStyle">
    <!-- Заголовок -->
    <div class="title-container">
      <h2>Image Generator</h2>
    </div>

    <!-- Основной контент: форма и результат -->
    <div class="content">
        <!-- Информация о лимитах и баллах -->
      <div class="limits-info">
        <p v-if="!isUnlimited">Generations remaining today: {{ remainingImages }} / {{ maxImages }}</p>
        <p>Available points: {{ userPoints }} <span v-if="userPoints >= 15">(enough for {{ Math.floor(userPoints / 15) }} images)</span></p>
      </div>

      <!-- Форма генерации -->
      <form @submit.prevent="generateImage" class="text-analyzer-form">
        <!-- Стили изображений -->
        <div class="form-group">
          <label>Select Image Style</label>
          <div class="styles-grid">
            <button
              v-for="style in imageStyles"
              :key="style.id"
              type="button"
              @click="selectedStyle = style.id"
              class="style-btn"
              :class="{ 'active': selectedStyle === style.id }"
            >
              <div class="style-name">{{ style.name }}</div>
              <div class="style-desc">{{ style.description }}</div>
            </button>
          </div>
        </div>

        <!-- Промпт -->
        <div class="form-group">
          <label for="prompt">Image Description</label>
          <textarea
            v-model="prompt"
            id="prompt"
            class="form-textarea"
            placeholder="Describe the desired image..."
            :disabled="!canGenerateImage && !hasEnoughPoints"
          ></textarea>
        </div>
      </form>

      <!-- Кнопки действий -->
      <div class="action-buttons">
        <button
          @click="generateImage"
          :disabled="isLoading || !prompt || !selectedStyle || !canGenerateImage"
          class="action-button"
        >
          <span class="icon">🖼️</span>
          <span v-if="isLoading">Generating image...</span>
          <span v-else-if="!canGenerateImage">Daily limit reached</span>
          <span v-else>Generate Image</span>
        </button>

        <!-- Кнопка генерации за баллы -->
        <button
          @click="generateImageWithPoints"
          :disabled="isLoading || !prompt || !selectedStyle || !hasEnoughPoints"
          class="action-button points-button"
        >
          <span class="icon">💎</span>
          <span v-if="isLoading">Generating image...</span>
          <span v-else-if="!hasEnoughPoints">Not enough points (need 15)</span>
          <span v-else>Generate for 15 Points</span>
          <span v-if="userPoints > 0" class="points-info">(you have: {{ userPoints }} points)</span>
        </button>
      </div>

        <!-- Результат -->
      <div v-if="generatedImageUrls.length > 0" class="result">
        <h3>Generated Images ({{ generatedImageUrls.length }}):</h3>
        <div class="result-content">
          <div class="images-grid">
            <div v-for="(imageUrl, index) in generatedImageUrls" :key="index + imageUrl" class="image-item">
              <div class="image-container">
                <OptimizedImage
                  :src="imageUrl"
                  :alt="`Generated image ${index + 1}`"
                  :aspect-ratio="56.25"
                  :blur-up="true"
                  @error="(e) => handleImageError(e, index)"
                  ref="imageRef"
                />
              </div>
              <div class="image-actions">
                <div class="image-number">{{ index + 1 }}</div>
                <div>
                  <button @click="() => downloadSpecificImage(imageUrl)" class="image-action-btn">
                    <span class="icon">{{ downloadButtonIcon }}</span>
                  </button>
                  <button
                    v-if="isTelegramWebApp"
                    @click="() => shareSpecificImageToTelegram(imageUrl)"
                    class="image-action-btn"
                  >
                    <span class="icon">📤</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="result-actions">
            <button
              @click="regenerate"
              :disabled="!canGenerateImage && !hasEnoughPoints"
              class="result-action-btn"
            >
              <span class="icon">🔄</span>
              Regenerate
            </button>
          </div>
        </div>
      </div>

        <!-- Ошибка -->
      <div v-if="error" class="error">
        <p>{{ error }}</p>
        <button @click="error = ''" class="error-close">✕</button>
      </div>

      <!-- Состояние загрузки -->
      <div v-if="isLoading" class="loading">
        <div class="loader"></div>
        <p>Generating image...</p>
        </div>

        <!-- Предложение обновить план или использовать баллы -->
      <div v-if="!canGenerateImage && !isUnlimited" class="upgrade-plan">
        <p v-if="hasEnoughPoints">
          Daily generation limit reached. You can use points to generate images (15 points per image) or upgrade your plan.
        </p>
        <p v-else>
          Daily generation limit reached. Upgrade your plan or add points to create more images!
        </p>
        <div class="upgrade-actions">
          <router-link to="/modes" class="upgrade-btn">
            Upgrade Plan
          </router-link>
          <router-link to="/profile" class="points-btn" v-if="!hasEnoughPoints">
            Add Points
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMainStore } from '@/store'
import { UserRole, ContentType, ActionType, UNLIMITED_ROLES } from '@/core/constants'
import OptimizedImage from '@/components/common/OptimizedImage.vue'
import { TelegramService } from '@/services/telegram'
// Background import (same as in TextAnalyzer.vue)
import planetBg from '@/assets/images/lesson_plan/plan-backgroud-image.svg'
// Import apiClient and API_ENDPOINTS for direct API requests
import { apiClient } from '@/api/client'
import { API_ENDPOINTS } from '@/api/endpoints'

const store = useMainStore()

const prompt = ref('')
const selectedStyle = ref('')
const generatedImageUrls = ref<string[]>([])
// For backward compatibility with existing code
const generatedImageUrl = computed(() => generatedImageUrls.value.length > 0 ? generatedImageUrls.value[0] : '')
const isLoading = ref(false)
const error = ref('')

// Planet background (similar to TextAnalyzer.vue)
const backgroundStyle = computed(() => ({
  backgroundImage: `url(${planetBg})`,
  backgroundSize: '90% auto',
  backgroundPosition: 'center -80px',
  backgroundRepeat: 'no-repeat',
  paddingTop: '60px'
}))

// Unlimited access check
const isUnlimited = computed(() => {
  return store.user?.role && (UNLIMITED_ROLES as readonly UserRole[]).includes(store.user.role)
})

// Getting limit information
const currentTariff = computed(() => {
  if (!store.user?.tariff) return null;
  return store.currentTariffLimits;
});

const remainingImages = computed(() => {
  if (isUnlimited.value) return Infinity
  if (!store.userStats) return 0
  return store.remainingGenerations(ContentType.IMAGE)
})

const maxImages = computed(() => {
  if (isUnlimited.value) return '∞'
  return currentTariff.value?.images_limit || 0
})

const canGenerateImage = computed(() => {
  return isUnlimited.value || remainingImages.value > 0
})

// Check if there are enough points for generation
const hasEnoughPoints = computed(() => {
  return store.user?.points >= 15
})

// Displaying user's points amount
const userPoints = computed(() => {
  return store.user?.points || 0
})

const imageStyles = [
  {
    id: 'disney-pixar',
    name: 'Disney/Pixar',
    description: 'Modern Disney/Pixar animation style',
    prompt: 'cute modern disney style, Pixar 3d portrait, ultra detailed, gorgeous, 3d zbrush, trending on dribbble, 8k render'
  },
  {
    id: 'neon',
    name: 'Neon',
    description: 'Bright neon style',
    prompt: 'neon lights, cyberpunk, glowing, vibrant neon colors, dark background, futuristic'
  },
  {
    id: 'isometric',
    name: 'Isometric',
    description: '3D isometric style',
    prompt: 'isometric design, 3D geometric, clean lines, 45-degree angles'
  },
  {
    id: 'realistic',
    name: 'Realistic',
    description: 'Photorealistic images',
    prompt: 'realistic, photographic, detailed'
  },
  {
    id: 'watercolor',
    name: 'Watercolor',
    description: 'Gentle watercolor style',
    prompt: 'watercolor painting, artistic, soft colors'
  },
  {
    id: 'cartoon',
    name: 'Cartoon',
    description: 'Colorful cartoon style',
    prompt: 'cartoon style, vibrant, animated'
  },
  {
    id: 'minimalist',
    name: 'Minimalist',
    description: 'Simple and clean lines',
    prompt: 'minimalist, clean lines, simple'
  },
  {
    id: 'pencil',
    name: 'Pencil Drawing',
    description: 'Black and white sketch',
    prompt: 'pencil sketch, black and white, hand-drawn'
  },
  {
    id: 'digital-art',
    name: 'Digital Art',
    description: 'Modern digital artwork',
    prompt: 'digital art, modern, vibrant colors'
  },
  {
    id: 'retro',
    name: 'Retro',
    description: 'Vintage style',
    prompt: 'vintage style, retro, old-fashioned'
  },
  {
    id: 'anime',
    name: 'Anime',
    description: 'Japanese anime style',
    prompt: 'anime style, manga, japanese animation'
  },
  {
    id: 'pixel-art',
    name: 'Pixel Art',
    description: '8-bit stylization',
    prompt: 'pixel art, 8-bit style, retro gaming'
  },
  {
    id: 'oil-painting',
    name: 'Oil Painting',
    description: 'Classical oil painting',
    prompt: 'oil painting, classical art, textured'
  },
  {
    id: 'pop-art',
    name: 'Pop Art',
    description: 'Bold pop art style',
    prompt: 'pop art style, bold colors, comic style'
  },
  {
    id: 'vector',
    name: 'Vector',
    description: 'Vector graphics',
    prompt: 'vector graphics, clean, scalable'
  }
]

const generateImage = async () => {
  if (isLoading.value || !prompt.value || !selectedStyle.value) return

  error.value = ''
  isLoading.value = true
  imageLoadFailed.value = false

  try {
    await store.checkAndTrackGeneration(ContentType.IMAGE)

    const selectedStyleData = imageStyles.find(style => style.id === selectedStyle.value)
    const fullPrompt = `${prompt.value}, ${selectedStyleData?.prompt || ''}`

    const response = await store.generateImage({
      prompt: fullPrompt,
      user_id: store.user?.id
    })

    // Add new image to the beginning of the array
    generatedImageUrls.value.unshift(response)

    // Check achievements
    if (store.user?.id) {
      await store.checkAchievements(ActionType.GENERATION, {
        user_id: store.user.id,
        content_type: ContentType.IMAGE
      })
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Error generating image'
    console.error('Error generating image:', err)
  } finally {
    isLoading.value = false
  }
}

// Method for generating image with points
const generateImageWithPoints = async () => {
  if (isLoading.value || !prompt.value || !selectedStyle.value) return

  // Check if there are enough points
  if (!hasEnoughPoints.value) {
    error.value = 'Insufficient points for image generation. 15 points required.'
    return
  }

  error.value = ''
  isLoading.value = true
  imageLoadFailed.value = false

  try {
    console.log('Начинаем генерацию изображения за баллы')

    // Log current user points before generation
    const initialPoints = store.user?.points || 0
    console.log('Текущее количество баллов перед генерацией изображения:', initialPoints)

    // Use store method for checking and deducting points
    const pointsCost = 15
    const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.IMAGE, pointsCost)

    if (!canGenerate) {
      throw new Error(`Failed to deduct ${pointsCost} points. Possibly insufficient points on account.`)
    }

    const selectedStyleData = imageStyles.find(style => style.id === selectedStyle.value)
    const fullPrompt = `${prompt.value}, ${selectedStyleData?.prompt || ''}`

    // Use store.generateImageWithPoints method to send the request
    console.log('Отправляем запрос на генерацию изображения за баллы')

    // Prepare request data
    const formData = {
      user_id: store.user?.id,
      prompt: fullPrompt,
      with_points: true,  // Add with_points flag to bypass tariff check
      skip_points_check: true  // Add skip_points_check flag to avoid double point deduction
    }

    // Call store.generateImageWithPoints method
    const imageUrl = await store.generateImageWithPoints(formData)

    console.log('Получен URL изображения:', imageUrl)

    // Add new image to the beginning of the array
    generatedImageUrls.value.unshift(imageUrl)

    // Update user data to display new points balance
    await store.fetchCurrentUser()

    // Log points amount after generation
    console.log('Points amount after image generation:', store.user?.points)

    // Check achievements
    if (store.user?.id) {
      await store.checkAchievements(ActionType.GENERATION, {
        user_id: store.user.id,
        content_type: ContentType.IMAGE
      })
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Error generating image with points'
    console.error('Error generating image with points:', err)
  } finally {
    isLoading.value = false
  }
}

// Method for regenerating image
const regenerate = async () => {
  // If user doesn't have an active tariff or has reached daily limit, offer to use points
  if (!canGenerateImage.value) {
    // If user has enough points, offer to use them
    if (hasEnoughPoints.value) {
      if (confirm('Daily generation limit reached. Would you like to use 15 points to generate a new image?')) {
        await generateImageWithPoints()
        return
      }
    } else {
      error.value = 'Daily generation limit reached. To generate, you need to purchase a tariff or add points.'
      return
    }
  }

  // If limit is not reached, use normal generation
  await generateImage()
}

// Add variable to track image loading errors
const imageLoadFailed = ref(false)
const imageRef = ref<InstanceType<typeof OptimizedImage> | null>(null)

// Handler for image loading error
const handleImageError = (e: Event, index?: number) => {
  console.error('Image load failed:', e, 'Index:', index)
  imageLoadFailed.value = true

  if (index !== undefined && index >= 0 && index < generatedImageUrls.value.length) {
    // If index is specified, remove problematic image from array
    generatedImageUrls.value.splice(index, 1)
    error.value = 'Failed to load image. It has been removed from the list.'
  } else {
    error.value = 'Failed to load image. Please try generating again.'
  }
}

// Add mobile device detection
const isMobileDevice = computed(() => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
});

// Check Web Share API support
const hasShareSupport = computed(() => {
  return !!navigator.share;
});

// Download button text depending on device
const downloadButtonText = computed(() => {
  return (isMobileDevice.value && hasShareSupport.value) ? 'Поделиться' : 'Скачать';
});

// Icon for the button
const downloadButtonIcon = computed(() => {
  return (isMobileDevice.value && hasShareSupport.value) ? '📤' : '💾';
});

// Download specific image
const downloadSpecificImage = async (imageUrl: string) => {
  if (!imageUrl) return

  try {
    // Determine if Web Share API is supported
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const canShare = !!navigator.share && isMobile;

    if (canShare) {
      // For mobile devices, use Web Share API
      try {
        // First, download the image
        const response = await fetch(imageUrl);
        const blob = await response.blob();

        // Create a file for transmission via Web Share API
        const file = new File([blob], `generated-image-${Date.now()}.png`, { type: blob.type });

        // Use Web Share API for downloading/sending image
        await navigator.share({
          title: 'Сгенерированное изображение',
          text: `Изображение по запросу: ${prompt.value}`,
          files: [file]
        });

        console.log('Изображение успешно отправлено через Web Share API');
      } catch (shareError) {
        console.warn('Не удалось использовать Web Share API:', shareError);
        // If Web Share API could not be used, use standard method
        useStandardDownload(imageUrl);
      }
    } else {
      // For desktops, use standard download method
      useStandardDownload(imageUrl);
    }
  } catch (err) {
    console.error('Error downloading image:', err);
    error.value = 'Ошибка при скачивании изображения';
  }
}

// Download first image (for backward compatibility)
const downloadImage = async () => {
  if (generatedImageUrls.value.length > 0) {
    await downloadSpecificImage(generatedImageUrls.value[0]);
  }
}

// Standard download method for desktops and as fallback option
const useStandardDownload = async (imageUrl: string) => {
  try {
    const response = await fetch(imageUrl);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `generated-image-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  } catch (err) {
    console.error('Error in standard download:', err);
    error.value = 'Ошибка при скачивании изображения';
  }
}

// Check if app is running in Telegram WebApp
const isTelegramWebApp = computed(() => {
  return !!window.Telegram?.WebApp
})

// Send specific image to Telegram
const shareSpecificImageToTelegram = async (imageUrl: string) => {
  if (!imageUrl || !isTelegramWebApp.value) return

  try {
    // Use TelegramService.sendData
    TelegramService.sendData({
      type: 'image',
      url: imageUrl,
      prompt: prompt.value
    })
  } catch (err) {
    console.error('Error sharing to Telegram:', err)
    error.value = 'Ошибка при отправке изображения в Telegram'
  }
}

// Send first image to Telegram (for backward compatibility)
const shareToTelegram = async () => {
  if (generatedImageUrls.value.length > 0) {
    await shareSpecificImageToTelegram(generatedImageUrls.value[0]);
  }
}

// Watch changes in store.error
watch(() => store.error, (newError) => {
  if (newError) {
    error.value = newError
  }
})

// Initialization on mount
onMounted(() => {
  // If there is an error in store, display it
  if (store.error) {
    error.value = store.error
  }
})
</script>

<style scoped>
/* Base container styles */
.text-analyzer-container {
  min-height: 100vh;
  overflow: visible !important;
  background-repeat: no-repeat;
  padding-top: 20px;
}

/* Header, separate block */
.title-container {
  position: relative;
  z-index: 2;
  text-align: center;
  margin-top: 30vh;
  margin-bottom: 1rem;
}
.title-container h2 {
  color: #fff;
  font-size: 1.8rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* Form and result container */
.content {
  position: relative;
  z-index: 1;
  max-width: 480px;
  margin: 0 auto;
  padding: 1rem;
  background: rgba(255, 192, 203, 0.1);
  border-radius: 16px;
}

/* Limits information */
.limits-info {
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 0.75rem;
  margin-bottom: 1rem;
  text-align: center;
  color: #fff;
  font-size: 0.9rem;
}

/* Text analysis form */
.text-analyzer-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

/* Form group */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border-radius: 16px;
  padding: 1rem;
  margin-bottom: 0.5rem;
}

/* Field labels */
label {
  font-weight: 500;
  font-size: 0.9rem;
  color: #fff;
}

/* Inputs, textareas, selects */
.form-input,
.form-select,
.form-textarea {
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
  background-color: #ffc0cb;
  color: #333;
  outline: none;
}

.form-textarea {
  min-height: 150px;
  resize: vertical;
  border-radius: 16px;
}

/* Image styles */
.styles-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.style-btn {
  padding: 0.75rem;
  border: none;
  border-radius: 12px;
  background: rgba(255, 192, 203, 0.3);
  color: #fff;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}
.style-btn:hover {
  background: rgba(255, 192, 203, 0.5);
  transform: translateY(-2px);
}
.style-btn:active {
  transform: translateY(0);
}
.style-btn.active {
  background: #ffc0cb;
  color: #333;
  font-weight: 500;
}

.style-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}
.style-desc {
  font-size: 0.75rem;
  opacity: 0.8;
}

/* Action buttons */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem;
  border: none;
  border-radius: 24px;
  background: #ffc0cb;
  color: #333;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
}
.action-button:hover {
  background: #ff9ebb;
}
.action-button:active {
  transform: scale(0.97);
}
.action-button:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
}

/* Styles for points-based generation button */
.points-button {
  background: #4a90e2;
  color: white;
  margin-top: 0.5rem;
}
.points-button:hover {
  background: #3a7bc8;
}
.points-button:disabled {
  background: #e0e0e0;
  color: #999;
}
.points-info {
  display: block;
  font-size: 0.8rem;
  margin-top: 0.25rem;
  opacity: 0.8;
}

/* Analysis result */
.result {
  margin-top: 1.5rem;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
}

.result h3 {
  color: #fff;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.result-content {
  background-color: rgba(255, 255, 255, 0.95);
  padding: 1.5rem;
  border-radius: 16px;
  overflow: hidden;
  color: #333;
  font-weight: 500;
}

/* Images grid */
.images-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 1rem;
}

/* Image item */
.image-item {
  flex: 1 0 calc(50% - 8px);
  min-width: 200px;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(0, 0, 0, 0.05);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px; /* Add bottom margin for all elements */
}

/* Image container */
.image-container {
  width: 100%;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}

/* Actions for specific image */
.image-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.03);
}

/* Image number */
.image-number {
  font-weight: bold;
  font-size: 0.9rem;
  color: #333;
  background-color: rgba(255, 192, 203, 0.3);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Image action button */
.image-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  background: #f0f0f0;
  color: #333;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}
.image-action-btn:hover {
  background: #e0e0e0;
}
.image-action-btn:active {
  transform: scale(0.97);
}

/* Result actions */
.result-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.result-action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 8px;
  background: #f0f0f0;
  color: #333;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}
.result-action-btn:hover {
  background: #e0e0e0;
}
.result-action-btn:active {
  transform: scale(0.97);
}
.result-action-btn:disabled {
  background: #e0e0e0;
  color: #999;
  cursor: not-allowed;
}

/* Loading */
.loading {
  margin-top: 2rem;
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  color: #fff;
}
.loader {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #ec407a;
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Error */
.error {
  margin-top: 1rem;
  background: rgba(244, 67, 54, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.error-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
}

/* Plan upgrade suggestion */
.upgrade-plan {
  margin-top: 1.5rem;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 1rem;
  text-align: center;
  color: #fff;
}

.upgrade-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 0.5rem;
}

.upgrade-btn {
  display: inline-block;
  margin-top: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: #ffc0cb;
  color: #333;
  border-radius: 24px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}
.upgrade-btn:hover {
  background: #ff9ebb;
  transform: translateY(-2px);
}
.upgrade-btn:active {
  transform: translateY(0);
}

.points-btn {
  display: inline-block;
  margin-top: 0.75rem;
  padding: 0.75rem 1.5rem;
  background: #4a90e2;
  color: white;
  border-radius: 24px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}
.points-btn:hover {
  background: #3a7bc8;
  transform: translateY(-2px);
}
.points-btn:active {
  transform: translateY(0);
}

/* Responsive settings */
@media (max-width: 768px) {
  .title-container {
    margin-top: 18vh;
  }
  .content {
    padding: 0.75rem;
    max-width: 100%;
  }
  .text-analyzer-container {
    background-position: center 30px !important;
    padding-top: 50px;
  }
  .styles-grid {
    grid-template-columns: 1fr;
  }
  .result-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  .images-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .image-item {
    width: 100%;
    margin-bottom: 16px;
  }
}
</style>
