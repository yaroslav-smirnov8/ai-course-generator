<template>
  <div class="relative inline-block">
    <!-- Иконка вопроса -->
    <button
      @mouseenter="showTooltip"
      @mouseleave="hideTooltip"
      @focus="showTooltip"
      @blur="hideTooltip"
      class="inline-flex items-center justify-center w-5 h-5 text-gray-400
            hover:text-gray-300 transition-colors relative"
      aria-label="Подробнее"
    >
      <HelpCircle class="w-5 h-5" />
      <span
        v-if="isNew"
        class="absolute -top-1 -right-1 w-2 h-2 bg-purple-500 rounded-full
              animate-ping"
      ></span>
    </button>

    <!-- Всплывающая подсказка с анимацией -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="show"
        class="absolute z-50 w-72 p-4 text-sm bg-gray-900 text-gray-300
              rounded-lg shadow-lg"
        :class="[
          position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2',
          position === 'left' ? 'right-full mr-2' : '',
          position === 'right' ? 'left-full ml-2' : ''
        ]"
        @mouseenter="keepVisible"
        @mouseleave="hideTooltip"
      >
        <!-- Заголовок подсказки, если есть -->
        <h4 v-if="title" class="font-medium text-white mb-2">
          {{ title }}
        </h4>

        <!-- Основной контент -->
        <div class="space-y-2">
          <slot></slot>
        </div>

        <!-- Дополнительные действия -->
        <div v-if="$slots.actions" class="mt-3 pt-2 border-t border-gray-700">
          <slot name="actions"></slot>
        </div>

        <!-- Стрелка -->
        <div
          class="absolute w-2 h-2 bg-gray-900 transform rotate-45"
          :class="getArrowPosition"
        ></div>

        <!-- Кнопка "Больше не показывать" -->
        <button
          v-if="dismissible"
          @click="dismiss"
          class="absolute top-2 right-2 text-gray-500 hover:text-gray-400"
        >
          <XIcon class="w-4 h-4" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { HelpCircle, X as XIcon } from 'lucide-vue-next'

interface Props {
  position?: 'top' | 'bottom' | 'left' | 'right'
  title?: string
  isNew?: boolean
  dismissible?: boolean
  id?: string
}

const props = withDefaults(defineProps<Props>(), {
  position: 'bottom',
  isNew: false,
  dismissible: false
})

const emit = defineEmits<{
  (e: 'dismiss', id: string): void
}>()

const show = ref(false)
let hideTimeout: NodeJS.Timeout | null = null

const showTooltip = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
  }
  show.value = true
}

const hideTooltip = () => {
  hideTimeout = setTimeout(() => {
    show.value = false
  }, 200)
}

const keepVisible = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
  }
}

const getArrowPosition = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-[-4px] left-[50%] -ml-1'
    case 'bottom':
      return 'top-[-4px] left-[50%] -ml-1'
    case 'left':
      return 'right-[-4px] top-[50%] -mt-1'
    case 'right':
      return 'left-[-4px] top-[50%] -mt-1'
    default:
      return ''
  }
})

const dismiss = () => {
  if (props.id) {
    // Сохраняем ID скрытой подсказки в localStorage
    const dismissedTips = JSON.parse(localStorage.getItem('dismissedTips') || '[]')
    if (!dismissedTips.includes(props.id)) {
      dismissedTips.push(props.id)
      localStorage.setItem('dismissedTips', JSON.stringify(dismissedTips))
    }
    emit('dismiss', props.id)
  }
  show.value = false
}
</script>
