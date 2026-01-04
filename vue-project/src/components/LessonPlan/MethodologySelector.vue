// src/components/LessonPlan/MethodologySelector.vue
<template>
  <div class="space-y-4">
    <h3 class="text-lg font-medium text-white">Выбор методик преподавания</h3>

    <!-- Основная методика -->
    <div>
      <label class="block text-sm font-medium text-gray-300 mb-2">
        Основная методика
      </label>
      <select
        v-model="selectedMain"
        class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
      >
        <option value="">Выберите основную методику</option>
        <option
          v-for="method in availableMethods"
          :key="method.id"
          :value="method.id"
        >
          {{ method.name }}
        </option>
      </select>
    </div>

    <!-- Поддерживающие методики -->
    <div>
      <label class="block text-sm font-medium text-gray-300 mb-2">
        Дополнительные методики
      </label>
      <div class="space-y-2">
        <div
          v-for="method in supportMethods"
          :key="method.id"
          class="flex items-center justify-between bg-gray-700 rounded-lg px-4 py-2"
        >
          <div>
            <div class="text-white">{{ method.name }}</div>
            <div class="text-sm text-gray-400">{{ method.description }}</div>
          </div>
          <button
            @click="removeSupportMethod(method.id)"
            class="text-red-400 hover:text-red-300"
          >
            Удалить
          </button>
        </div>
      </div>

      <!-- Добавление поддерживающей методики -->
      <div class="mt-2">
        <select
          v-model="selectedSupport"
          @change="addSupportMethod"
          class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
        >
          <option value="">Добавить поддерживающую методику</option>
          <option
            v-for="method in availableSupportMethods"
            :value="method.id"
          >
            {{ method.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Сведения о методиках -->
    <div v-if="selectedMain" class="mt-4 p-4 bg-gray-700/50 rounded-lg">
      <h4 class="text-white font-medium mb-2">О выбранной методике</h4>
      <div class="space-y-2">
        <p class="text-gray-300">{{ selectedMethodInfo?.description }}</p>
        <div class="space-y-1">
          <p class="text-sm text-gray-400">Особенности:</p>
          <ul class="list-disc list-inside">
            <li v-for="feature in selectedMethodInfo?.features" :key="feature" class="text-gray-300 text-sm">
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
import { teachingMethods } from '@/constants/methods'
import type { TeachingMethod } from '@/types/LessonPlan'

const props = defineProps<{
  language: string
  selectedMethods: string[]
}>()

const emit = defineEmits<{
  (e: 'select', methodId: string, isMain: boolean): void
  (e: 'remove', methodId: string): void
}>()

// Состояние
const selectedMain = ref('')
const selectedSupport = ref('')
const supportMethods = ref<TeachingMethod[]>([])

// Вычисляемые свойства
const availableMethods = computed(() => {
  const universalMethods = teachingMethods.universal
  const languageSpecificMethods = teachingMethods[props.language as keyof typeof teachingMethods] || []
  return [...universalMethods, ...languageSpecificMethods]
})

const availableSupportMethods = computed(() => {
  return availableMethods.value.filter(method => {
    return method.id !== selectedMain.value &&
      !supportMethods.value.find(m => m.id === method.id)
  })
})

const selectedMethodInfo = computed(() => {
  return availableMethods.value.find(method => method.id === selectedMain.value)
})

// Методы
const addSupportMethod = () => {
  if (!selectedSupport.value) return

  const method = availableMethods.value.find(m => m.id === selectedSupport.value)
  if (method) {
    supportMethods.value.push(method)
    emit('select', method.id, false)
    selectedSupport.value = ''
  }
}

const removeSupportMethod = (methodId: string) => {
  supportMethods.value = supportMethods.value.filter(m => m.id !== methodId)
  emit('remove', methodId)
}

// Отслеживание изменений основной методики
watch(selectedMain, (newValue) => {
  if (newValue) {
    emit('select', newValue, true)
  }
})

// Инициализация начальных значений
watch(() => props.selectedMethods, (newMethods) => {
  if (newMethods.length > 0) {
    selectedMain.value = newMethods[0]
    supportMethods.value = newMethods.slice(1)
      .map(id => availableMethods.value.find(m => m.id === id))
      .filter((m): m is TeachingMethod => m !== undefined)
  }
}, { immediate: true })
</script>
