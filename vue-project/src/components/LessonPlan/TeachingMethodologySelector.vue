<template>
  <div class="space-y-4">
    <h3 class="text-lg font-medium text-white">Выбор методики обучения</h3>

    <!-- Основная методика обучения -->
    <div>
      <label class="block text-sm font-medium text-gray-300 mb-2">
        Методика обучения
      </label>
      <select
        v-model="selectedMethodology"
        class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
        @change="emitSelection"
      >
        <option value="">Выберите методику обучения</option>
        <optgroup label="Универсальные методики">
          <option
            v-for="method in universalMethodologies"
            :key="method.id"
            :value="method.id"
          >
            {{ method.name }}
          </option>
        </optgroup>
        <optgroup v-if="languageSpecificMethods.length > 0" :label="`Методики для ${languageLabel}`">
          <option
            v-for="method in languageSpecificMethods"
            :key="method.id"
            :value="method.id"
          >
            {{ method.name }}
          </option>
        </optgroup>
      </select>
    </div>

    <!-- Информация о выбранной методике -->
    <div v-if="selectedMethodInfo" class="mt-4 p-4 bg-gray-700/50 rounded-lg">
      <h4 class="text-white font-medium mb-2">О выбранной методике</h4>
      <div class="space-y-2">
        <p class="text-gray-300">{{ selectedMethodInfo.description }}</p>
        <div class="space-y-1">
          <p class="text-sm text-gray-400">Особенности:</p>
          <ul class="list-disc list-inside">
            <li v-for="feature in selectedMethodInfo.features" :key="feature" class="text-gray-300 text-sm">
              {{ feature }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { teachingMethodologies, languageSpecificMethodologies } from '@/constants/methods'

// Определение типов
interface Methodology {
  id: string;
  name: string;
  description: string;
  features: string[];
  languages?: string[];
}

const props = defineProps<{
  language: string
  selectedMethodology: string
}>()

const emit = defineEmits<{
  (e: 'select', methodologyId: string): void
}>()

// Состояние
const selectedMethodology = ref(props.selectedMethodology || '')

// Вычисляемые свойства
const universalMethodologies = computed((): Methodology[] => {
  return teachingMethodologies
})

const languageSpecificMethods = computed((): Methodology[] => {
  if (!props.language) return []
  
  // Получаем методики для конкретного языка
  const specificMethods = languageSpecificMethodologies[props.language as keyof typeof languageSpecificMethodologies] || []
  return specificMethods
})

const languageLabel = computed((): string => {
  const languageMap: Record<string, string> = {
    english: 'английского языка',
    spanish: 'испанского языка',
    french: 'французского языка',
    german: 'немецкого языка',
    italian: 'итальянского языка',
    chinese: 'китайского языка',
    arabic: 'арабского языка',
    russian: 'русского языка'
  }
  
  return languageMap[props.language] || props.language
})

const selectedMethodInfo = computed((): Methodology | null => {
  if (!selectedMethodology.value) return null
  
  // Ищем в универсальных методиках
  const universalMethod = universalMethodologies.value.find(
    (method: Methodology) => method.id === selectedMethodology.value
  )
  
  if (universalMethod) return universalMethod
  
  // Ищем в специфических методиках для языка
  return languageSpecificMethods.value.find(
    (method: Methodology) => method.id === selectedMethodology.value
  ) || null
})

// Методы
const emitSelection = (): void => {
  emit('select', selectedMethodology.value)
}

// Отслеживание изменений выбранной методики из props
watch(() => props.selectedMethodology, (newValue) => {
  if (newValue !== selectedMethodology.value) {
    selectedMethodology.value = newValue
  }
}, { immediate: true })

// Отслеживание изменений языка
watch(() => props.language, () => {
  // Если выбранная методика специфична для языка, который больше не выбран,
  // сбрасываем выбор
  if (selectedMethodology.value && 
      !universalMethodologies.value.some((m: Methodology) => m.id === selectedMethodology.value) &&
      !languageSpecificMethods.value.some((m: Methodology) => m.id === selectedMethodology.value)) {
    selectedMethodology.value = ''
    emit('select', '')
  }
})
</script> 