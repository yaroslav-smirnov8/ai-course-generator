<template>
  <div>
    <!-- Компонент восстановления JSON -->
    <JsonRecoveryStatus 
      v-if="recoveryStatus !== 'none'" 
      :status="recoveryStatus" 
      :details="recoveryDetails" 
      :actions="recoveryActions"
    />
    
    <!-- Отображение ошибки API -->
    <div 
      v-if="apiError"
      class="w-full bg-red-800 text-white rounded-lg p-4 mb-4 border-l-4 border-red-500"
    >
      <div class="flex items-start justify-between">
        <div>
          <h3 class="font-medium mb-1">Ошибка API</h3>
          <p class="text-gray-300 text-sm">{{ apiError }}</p>
          
          <div v-if="errorDetails" class="mt-2 text-xs text-gray-400">
            <pre class="whitespace-pre-wrap rounded bg-gray-900 p-2 mt-1">{{ errorDetails }}</pre>
          </div>
        </div>
        
        <button 
          @click="clearError"
          class="text-gray-400 hover:text-white p-1"
        >
          ✕
        </button>
      </div>
      
      <div v-if="errorActions && errorActions.length" class="mt-3 flex gap-3">
        <button 
          v-for="(action, index) in errorActions" 
          :key="index"
          @click="action.handler"
          class="px-3 py-1 text-sm rounded-md"
          :class="action.primary ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-200'"
        >
          {{ action.label }}
        </button>
      </div>
    </div>
    
    <!-- Контент, обернутый компонентом -->
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useCourseStore } from '@/store/course';
import JsonRecoveryStatus from './JsonRecoveryStatus.vue';

const props = withDefaults(defineProps<{
  apiError?: string;
  errorDetails?: string;
  errorActions?: Array<{
    label: string;
    handler: () => void;
    primary?: boolean;
  }>;
  watchRecovery?: boolean;
}>(), {
  apiError: '',
  errorDetails: '',
  errorActions: () => [],
  watchRecovery: true
});

const emit = defineEmits(['clearError', 'retryRequest']);

// Состояние компонента
const store = useCourseStore();
const localApiError = ref(props.apiError);

// Реагируем на изменение входящей ошибки
watch(() => props.apiError, (newVal) => {
  localApiError.value = newVal;
});

// Методы
const clearError = () => {
  localApiError.value = '';
  emit('clearError');
};

// Компьютеды для восстановления данных из store
const recoveryStatus = computed(() => {
  return props.watchRecovery ? store.recoveryStatus : 'none';
});

const recoveryDetails = computed(() => {
  return {
    recoveredFields: store.recoveryDetails?.recoveredFields || [],
    missingFields: store.recoveryDetails?.missingFields || [],
    messages: store.recoveryDetails?.messages || []
  };
});

// Действия для компонента восстановления
const recoveryActions = computed(() => {
  const actions = [];
  
  if (recoveryStatus.value === 'partial' || recoveryStatus.value === 'success') {
    actions.push({
      label: 'Очистить',
      handler: () => store.resetRecoveryInfo(),
      primary: false
    });
  }
  
  return actions;
});
</script> 