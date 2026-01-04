<template>
  <div class="mt-4 p-4 bg-gray-600 rounded-lg border border-gray-500">
    <label for="game-type-select" class="block text-sm font-medium text-gray-300 mb-2">Выберите тип игры:</label>
    <select
      id="game-type-select"
      v-model="selectedGameType"
      class="w-full bg-gray-700 border border-gray-500 rounded-lg px-3 py-2 text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
    >
      <option disabled value="">-- Выберите тип --</option>
      <option v-for="game in gameTypes" :key="game.value" :value="game.value">
        {{ game.label }}
      </option>
    </select>
    <div class="mt-3 flex justify-end gap-2">
       <button
         @click="$emit('cancel')"
         class="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-400"
       >
         Отмена
       </button>
       <button
        v-if="!props.withPoints"
        @click="confirmSelection"
        :disabled="!selectedGameType"
        class="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed"
      >
        Сгенерировать
      </button>
      <button
        v-else
        @click="confirmSelectionWithPoints"
        :disabled="!selectedGameType"
        class="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed"
      >
        <span class="mr-1">💎</span> За баллы
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps({
  withPoints: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['select', 'cancel', 'select-with-points']);

const selectedGameType = ref<string>('');

const gameTypes = ref([
  { value: 'matching', label: 'Сопоставление (Matching)' },
  { value: 'quiz', label: 'Викторина (Quiz)' },
  { value: 'fill_in_the_blanks', label: 'Заполнить пропуски' },
  { value: 'word_search', label: 'Поиск слов' },
  { value: 'true_false', label: 'Верно/Неверно (True/False)' },
  { value: 'sentence_scramble', label: 'Составить предложение (Sentence Scramble)' },
  { value: 'category_sort', label: 'Сортировка по категориям (Category Sort)' },
  { value: 'role_play_scenario', label: 'Ролевой сценарий' },
  // Кроссворд убран, добавлены новые типы
]);

const confirmSelection = () => {
  if (selectedGameType.value) {
    emit('select', selectedGameType.value);
  }
};

const confirmSelectionWithPoints = () => {
  if (selectedGameType.value) {
    emit('select-with-points', selectedGameType.value);
  }
};
</script>

<style scoped>
/* Стили при необходимости */
</style>
