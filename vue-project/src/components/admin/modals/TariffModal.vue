<template>
  <div v-if="show" class="modal-backdrop">
    <div class="modal-container">
      <!-- Заголовок -->
      <div class="modal-header">
        <h3 class="modal-title">
          {{ tariff ? 'Редактирование тарифа' : 'Новый тариф' }}
        </h3>
        <button @click="$emit('close')" class="modal-close">
          <XIcon class="w-6 h-6" />
        </button>
      </div>

      <!-- Форма -->
      <form @submit.prevent="handleSubmit" class="modal-body">
        <!-- Основные параметры -->
        <div class="modal-form-group">
          <div>
            <label class="modal-label">Название тарифа</label>
            <input
              v-model="formData.name"
              type="text"
              required
              class="modal-input"
            >
          </div>

          <div>
            <label class="modal-label">Тип тарифа</label>
            <select
              v-model="formData.type"
              required
              class="modal-input"
            >
              <option :value="tariffTypes.BASIC">Basic (2)</option>
              <option :value="tariffTypes.STANDARD">Standard (4)</option>
              <option :value="tariffTypes.PREMIUM">Premium (6)</option>
            </select>
          </div>

          <div>
            <label class="modal-label">Стоимость (в баллах)</label>
            <input
              v-model.number="formData.price_points"
              type="number"
              required
              min="0"
              class="modal-input"
            >
          </div>
        </div>

        <!-- Лимиты -->
        <div class="border-t border-gray-700 pt-4">
          <h4 class="text-white font-medium mb-4">Лимиты</h4>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="modal-label">Генераций в день</label>
              <input
                v-model.number="formData.generations_limit"
                type="number"
                required
                min="0"
                class="modal-input"
              >
            </div>

            <div>
              <label class="modal-label">Изображений в день</label>
              <input
                v-model.number="formData.images_limit"
                type="number"
                required
                min="0"
                class="modal-input"
              >
            </div>
          </div>
        </div>

        <!-- Возможности -->
        <div class="border-t border-gray-700 pt-4">
          <h4 class="text-white font-medium mb-4">Возможности</h4>

          <div class="space-y-2">
            <div v-for="(feature, index) in features"
                 :key="index"
                 class="space-y-2">
              <input
                v-model="features[index].name"
                type="text"
                :placeholder="'Название возможности ' + (index + 1)"
                class="modal-input"
              >
              <input
                v-model="features[index].description"
                type="text"
                :placeholder="'Описание возможности ' + (index + 1)"
                class="modal-input mt-2"
              >
              <button
                type="button"
                @click="removeFeature(index)"
                class="text-red-400 hover:text-red-300"
              >
                <XIcon class="w-5 h-5" />
              </button>
            </div>

            <button
              type="button"
              @click="addFeature"
              class="text-purple-400 hover:text-purple-300 text-sm flex items-center gap-1"
            >
              <PlusIcon class="w-4 h-4" />
              Добавить возможность
            </button>
          </div>
        </div>

        <!-- Кнопки -->
        <div class="modal-footer">
          <button type="button" @click="$emit('close')" class="modal-btn-cancel">
            Отмена
          </button>
          <button type="submit" class="modal-btn-submit">
            Сохранить
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { X as XIcon, Plus as PlusIcon } from 'lucide-vue-next'
import type { Tariff, TariffFeature } from '@/types'
import { TariffType } from '@/core/constants'

interface Props {
  show: boolean
  tariff: Tariff | null
}

interface TariffFormData {
  name: string
  type: TariffType
  price_points: number
  generations_limit: number
  images_limit: number
  features: TariffFeature[]
}

interface FeatureInput {
  name: string
  description: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: Partial<Tariff>): void
}>()

const tariffTypes = TariffType

// Состояние формы
const formData = ref<TariffFormData>({
  name: '',
  type: TariffType.BASIC,
  price_points: 0,
  generations_limit: 0,
  images_limit: 0,
  features: []
})

const features = ref<FeatureInput[]>([])

// Методы
const handleSubmit = () => {
  const tariffData: Partial<Tariff> = {
    name: formData.value.name,
    type: formData.value.type,
    price_points: formData.value.price_points,
    generations_limit: formData.value.generations_limit,
    images_limit: formData.value.images_limit,
    features: features.value
      .filter(f => f.name.trim() !== '')
      .map(feature => ({
        name: feature.name,
        description: feature.description,
        enabled: true
      }))
  }

  emit('save', tariffData)
}

const addFeature = () => {
  features.value.push({
    name: '',
    description: ''
  })
}

const removeFeature = (index: number) => {
  features.value.splice(index, 1)
}

// Отслеживаем изменение тарифа для обновления формы
watch(() => props.tariff, (newTariff) => {
  if (newTariff) {
    formData.value = {
      name: newTariff.name,
      type: newTariff.type,
      price_points: newTariff.price_points,
      generations_limit: newTariff.generations_limit,
      images_limit: newTariff.images_limit,
      features: newTariff.features
    }
    features.value = newTariff.features.map(f => ({
      name: f.name,
      description: f.description
    }))
  } else {
    formData.value = {
      name: '',
      type: TariffType.BASIC,
      price_points: 0,
      generations_limit: 0,
      images_limit: 0,
      features: []
    }
    features.value = []
  }
}, { immediate: true })
</script>

<style scoped>
.modal-input {
  @apply w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:border-purple-500 focus:ring-1 focus:ring-purple-500;
}

.modal-label {
  @apply block text-sm font-medium text-gray-400 mb-1;
}

.modal-form-group {
  @apply space-y-4;
}

.modal-footer {
  @apply flex justify-end gap-4 pt-4 border-t border-gray-700;
}

.modal-btn-cancel {
  @apply px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600;
}

.modal-btn-submit {
  @apply px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600;
}

.modal-backdrop {
  @apply fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50;
}

.modal-container {
  @apply bg-gray-800 rounded-lg w-full max-w-xl mx-4;
}

.modal-header {
  @apply flex justify-between items-center p-6 border-b border-gray-700;
}

.modal-title {
  @apply text-xl font-semibold text-white;
}

.modal-close {
  @apply text-gray-400 hover:text-white;
}

.modal-body {
  @apply p-6 space-y-4;
}
</style>
