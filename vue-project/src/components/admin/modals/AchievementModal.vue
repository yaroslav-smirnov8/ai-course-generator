<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-gray-800 rounded-lg w-full max-w-xl mx-4">
      <!-- Заголовок -->
      <div class="flex justify-between items-center p-6 border-b border-gray-700">
        <h3 class="text-xl font-semibold text-white">
          {{ achievement ? 'Редактирование достижения' : 'Новое достижение' }}
        </h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-white">
          <XIcon class="w-6 h-6" />
        </button>
      </div>

      <!-- Форма -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <!-- Основная информация -->
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">
              Название
            </label>
            <input
              v-model="formData.name"
              type="text"
              required
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
            >
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">
              Код достижения
            </label>
            <input
              v-model="formData.code"
              type="text"
              required
              pattern="[A-Z0-9_]+"
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
            >
            <p class="text-xs text-gray-500 mt-1">
              Только заглавные буквы, цифры и подчеркивания
            </p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">
              Описание
            </label>
            <textarea
              v-model="formData.description"
              rows="3"
              required
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
            ></textarea>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">
                Эмодзи
              </label>
              <input
                v-model="formData.icon"
                type="text"
                maxlength="2"
                class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">
                Награда (баллы)
              </label>
              <input
                v-model.number="formData.points_reward"
                type="number"
                required
                min="0"
                class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
              >
            </div>
          </div>
        </div>

        <!-- Условия -->
        <div class="border-t border-gray-700 pt-4 space-y-4">
          <h4 class="text-white font-medium">Условия получения</h4>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">
                Тип условия
              </label>
              <select
                v-model="conditionType"
                class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
              >
                <option value="generation_count">Количество генераций</option>
                <option value="consecutive_days">Дней подряд</option>
                <option value="invites_count">Количество приглашений</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">
                Значение
              </label>
              <input
                v-model.number="conditionValue"
                type="number"
                min="1"
                class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
              >
            </div>
          </div>
        </div>

        <!-- Кнопки -->
        <div class="flex justify-end gap-4 pt-4 border-t border-gray-700">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
          >
            Отмена
          </button>
          <button
            type="submit"
            class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
          >
            Сохранить
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { X as XIcon } from 'lucide-vue-next'
import type { Achievement } from '@/types'
import { ContentType } from '@/core/constants'

interface Props {
  show: boolean
  achievement: Achievement | null
}

interface AchievementFormData {
  name: string
  code: string
  description: string
  icon?: string
  points_reward: number
  conditions: {
    type: string
    required_count?: number
    content_type?: ContentType
    consecutive_days?: number
    invites_count?: number
  }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', achievementData: Partial<Achievement>): void
}>()

const formData = ref<AchievementFormData>({
  name: '',
  code: '',
  description: '',
  icon: '🏆',
  points_reward: 10,
  conditions: {
    type: 'generation_count',
    required_count: 1
  }
})

const conditionType = ref('generation_count')
const conditionValue = ref(1)

watch(() => props.achievement, (newAchievement) => {
  if (newAchievement) {
    formData.value = { ...newAchievement }
    // Устанавливаем первое условие из объекта conditions
    if (newAchievement.conditions) {
      conditionType.value = newAchievement.conditions.type
      // Определяем правильное значение в зависимости от типа условия
      switch (newAchievement.conditions.type) {
        case 'generation_count':
          conditionValue.value = newAchievement.conditions.required_count || 1
          break
        case 'consecutive_days':
          conditionValue.value = newAchievement.conditions.consecutive_days || 1
          break
        case 'invites_count':
          conditionValue.value = newAchievement.conditions.invites_count || 1
          break
      }
    }
  } else {
    formData.value = {
      name: '',
      code: '',
      description: '',
      icon: '🏆',
      points_reward: 10,
      conditions: {
        type: 'generation_count',
        required_count: 1
      }
    }
    conditionType.value = 'generation_count'
    conditionValue.value = 1
  }
}, { immediate: true })

const handleSubmit = () => {
  // Создаем объект условий в зависимости от типа
  let conditions: AchievementFormData['conditions'];

  switch (conditionType.value) {
    case 'generation_count':
      conditions = {
        type: conditionType.value,
        required_count: conditionValue.value
      }
      break
    case 'consecutive_days':
      conditions = {
        type: conditionType.value,
        consecutive_days: conditionValue.value
      }
      break
    case 'invites_count':
      conditions = {
        type: conditionType.value,
        invites_count: conditionValue.value
      }
      break
    default:
      conditions = {
        type: conditionType.value,
        required_count: conditionValue.value
      }
  }

  formData.value.conditions = conditions
  emit('save', formData.value as Partial<Achievement>)
}
</script>
