// src/components/LessonPlan/LessonPlanGenerator.vue
<template>
  <div class="space-y-6">
    <div class="bg-gray-800/50 rounded-xl p-6">
      <h2 class="text-xl font-semibold text-white mb-4">План урока</h2>

      <!-- Шаг 1: Основные настройки -->
      <div v-if="currentStep === 1" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Язык -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Язык</label>
            <select
              v-model="formData.language"
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
            >
              <option value="english">English</option>
              <option value="spanish">Spanish</option>
              <option value="french">French</option>
              <!-- Добавьте другие языки -->
            </select>
          </div>

          <!-- Уровень -->
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Уровень</label>
            <select
              v-model="formData.level"
              class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>

        <!-- Тема -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">Тема урока</label>
          <input
            v-model="formData.topic"
            type="text"
            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
            placeholder="Введите тему урока"
          />
        </div>

        <!-- Продолжительность -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">Продолжительность (минуты)</label>
          <input
            v-model.number="formData.duration"
            type="number"
            min="15"
            max="180"
            step="15"
            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
          />
        </div>
      </div>

      <!-- Шаг 2: Методики преподавания -->
      <div v-if="currentStep === 2" class="space-y-4">
        <MethodologySelector
          :language="formData.language"
          :selectedMethods="[formData.methodologies.mainMethod, ...formData.methodologies.supportMethods]"
          @select="addMethod"
          @remove="removeMethod"
        />
      </div>

      <!-- Шаг 3: Цели и материалы -->
      <div v-if="currentStep === 3" class="space-y-6">
        <!-- Цели обучения -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-300">Цели обучения</label>
          <div v-for="(objective, index) in formData.objectives" :key="index" class="flex gap-2">
            <input
              v-model="formData.objectives[index]"
              type="text"
              class="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
              placeholder="Введите цель обучения"
            />
            <button
              @click="removeObjective(index)"
              class="text-red-400 hover:text-red-300 px-2"
            >
              ✕
            </button>
          </div>
          <button
            @click="addObjective"
            class="text-purple-400 hover:text-purple-300 text-sm"
          >
            + Добавить цель
          </button>
        </div>

        <!-- Материалы -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-300">Материалы</label>
          <div v-for="(material, index) in formData.materials" :key="index" class="flex gap-2">
            <input
              v-model="formData.materials[index]"
              type="text"
              class="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
              placeholder="Введите необходимый материал"
            />
            <button
              @click="removeMaterial(index)"
              class="text-red-400 hover:text-red-300 px-2"
            >
              ✕
            </button>
          </div>
          <button
            @click="addMaterial"
            class="text-purple-400 hover:text-purple-300 text-sm"
          >
            + Добавить материал
          </button>
        </div>
      </div>

      <!-- Шаг 4: Дополнительные настройки -->
      <div v-if="currentStep === 4" class="space-y-4">
        <!-- Тип оценивания -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">Тип оценивания</label>
          <select
            v-model="formData.assessment"
            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
          >
            <option value="formative">Формирующее оценивание</option>
            <option value="summative">Итоговое оценивание</option>
            <option value="none">Без оценивания</option>
          </select>
        </div>

        <!-- Формат -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">Формат урока</label>
          <select
            v-model="formData.format"
            class="w-full bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600"
          >
            <option value="online">Онлайн</option>
            <option value="offline">Офлайн</option>
            <option value="hybrid">Гибридный</option>
          </select>
        </div>

        <!-- Культурные элементы -->
        <div class="flex items-center gap-2">
          <input
            v-model="formData.culturalElements"
            type="checkbox"
            class="w-4 h-4 bg-gray-700 border-gray-600 rounded text-purple-500 focus:ring-purple-500"
          />
          <label class="text-sm font-medium text-gray-300">
            Включить культурные элементы
          </label>
        </div>
      </div>

      <!-- Навигация -->
      <div class="flex justify-between mt-6">
        <button
          v-if="currentStep > 1"
          @click="previousStep"
          class="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
        >
          Назад
        </button>
        <button
          v-if="currentStep < 4"
          @click="nextStep"
          class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
          :disabled="!canProceed"
        >
          Далее
        </button>
        <button
          v-else
          @click="generatePlan"
          class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
          :disabled="isLoading"
        >
          {{ isLoading ? 'Генерация...' : 'Сгенерировать план' }}
        </button>
      </div>

      <!-- Ошибки валидации -->
      <div v-if="validation.errors.length > 0" class="mt-4">
        <div v-for="error in validation.errors" :key="error" class="text-red-400 text-sm">
          {{ error }}
        </div>
      </div>
    </div>

    <!-- Предпросмотр результата -->
    <div v-if="generatedPrompt" class="bg-gray-800/50 rounded-xl p-6">
      <h3 class="text-lg font-semibold text-white mb-4">Сгенерированный план</h3>
      <PromptPreview :prompt="generatedPrompt" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import MethodologySelector from './MethodologySelector.vue';
import PromptPreview from './PromptPreview.vue';
import { useLessonPlan } from '@/hooks/useLessonPlan';
import type { LessonPlanFormData, ValidationResult } from '@/types/LessonPlan';

// Состояние
const currentStep = ref(1);
const isLoading = ref(false);
const generatedPrompt = ref('');

// Используем хук для управления состоянием плана урока
const {
  formData,
  validation,
  addMethod,
  removeMethod,
  validateStep,
  generatePrompt
} = useLessonPlan();

// Методы для управления целями
const addObjective = () => {
  formData.value.objectives.push('');
};

const removeObjective = (index: number) => {
  formData.value.objectives.splice(index, 1);
};

// Методы для управления материалами
const addMaterial = () => {
  formData.value.materials.push('');
};

const removeMaterial = (index: number) => {
  formData.value.materials.splice(index, 1);
};

// Навигация
const canProceed = computed(() => validateStep(currentStep.value));

const nextStep = () => {
  if (canProceed.value) {
    currentStep.value++;
  }
};

const previousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
};

// Генерация плана
const generatePlan = async () => {
  try {
    isLoading.value = true;
    const prompt = await generatePrompt();
    generatedPrompt.value = prompt;
  } catch (error) {
    console.error('Error generating lesson plan:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>
