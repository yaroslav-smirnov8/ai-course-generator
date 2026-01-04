<template>
  <div 
    v-if="active" 
    class="w-full bg-gray-800 rounded-lg p-4 mb-4 border-l-4"
    :class="borderColor"
  >
    <div class="flex items-start justify-between">
      <div>
        <h3 class="text-white font-medium mb-1">{{ title }}</h3>
        <p class="text-gray-300 text-sm mb-2">{{ description }}</p>
        
        <div v-if="details" class="text-xs text-gray-400 mt-2">
          <div v-if="details.recoveredFields && details.recoveredFields.length">
            <div class="font-medium text-white mt-1">Восстановленные поля:</div>
            <ul class="list-disc list-inside mt-1 ml-2">
              <li v-for="(field, index) in details.recoveredFields" :key="index">
                {{ field }}
              </li>
            </ul>
          </div>
          
          <div v-if="details.missingFields && details.missingFields.length">
            <div class="font-medium text-white mt-2">Отсутствующие данные:</div>
            <ul class="list-disc list-inside mt-1 ml-2">
              <li v-for="(field, index) in details.missingFields" :key="index">
                {{ field }}
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <button 
        v-if="dismissible" 
        @click="dismiss"
        class="text-gray-400 hover:text-white p-1"
      >
        ✕
      </button>
    </div>
    
    <div v-if="actions && actions.length" class="mt-3 flex gap-3">
      <button 
        v-for="(action, index) in actions" 
        :key="index"
        @click="action.handler"
        class="px-3 py-1 text-sm rounded-md"
        :class="action.primary ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-200'"
      >
        {{ action.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Action {
  label: string;
  handler: () => void;
  primary?: boolean;
}

interface RecoveryDetails {
  recoveredFields?: string[];
  missingFields?: string[];
  timestamp?: string;
  messages?: string[];
}

interface Props {
  status: 'success' | 'partial' | 'failure' | 'none';
  details?: RecoveryDetails;
  dismissible?: boolean;
  actions?: Action[];
}

const props = withDefaults(defineProps<Props>(), {
  status: 'none',
  dismissible: true,
  details: undefined,
  actions: undefined,
});

const active = ref(props.status !== 'none');

const dismiss = () => {
  active.value = false;
};

const title = computed(() => {
  switch (props.status) {
    case 'success': 
      return 'Данные восстановлены успешно';
    case 'partial': 
      return 'Данные восстановлены частично';
    case 'failure': 
      return 'Ошибка восстановления данных';
    default: 
      return '';
  }
});

const description = computed(() => {
  switch (props.status) {
    case 'success': 
      return 'Структура курса была успешно восстановлена из неполных данных API.';
    case 'partial': 
      return 'Часть данных курса была восстановлена, но некоторые элементы могут отсутствовать.';
    case 'failure': 
      return 'Не удалось восстановить структуру курса из-за серьезных ошибок в данных.';
    default: 
      return '';
  }
});

const borderColor = computed(() => {
  switch (props.status) {
    case 'success': 
      return 'border-green-500';
    case 'partial': 
      return 'border-yellow-500';
    case 'failure': 
      return 'border-red-500';
    default: 
      return 'border-gray-500';
  }
});
</script> 