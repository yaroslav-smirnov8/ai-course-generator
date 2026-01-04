<template>
  <div v-if="isLoading || exercisesContent" class="exercises-view-container mt-4">
    <div v-if="isLoading" class="text-center">
      <!-- Обновленный лоадер -->
      <div class="exercises-view-loader"></div>
      <p class="exercises-view-loader-text">Генерация упражнений...</p>
    </div>
    <!-- Отображаем блок, только если есть контент (независимо от видимости) -->
    <div v-else-if="exercisesContent">
      <div class="exercises-view-header mb-3">
        <h3 class="exercises-view-title">Сгенерированные упражнения</h3>
        <!-- Кнопка Скрыть/Показать -->
        <button
          @click="$emit('toggle-visibility')"
          class="exercises-view-toggle-btn"
        >
          {{ isVisible ? 'Скрыть' : 'Показать' }}
        </button>
      </div>
      <!-- Скрываем/показываем сам контент упражнений -->
      <pre v-if="isVisible" class="exercises-view-content whitespace-pre-wrap">{{ exercisesContent }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  exercisesContent: string | null; // Меняем prop
  isLoading: boolean;
  isVisible: boolean;
}>()

defineEmits(['toggle-visibility']) // Оставляем то же событие
</script>

<style scoped>
.exercises-view-container {
  /* background: linear-gradient(135deg, rgba(88, 28, 135, 0.4), rgba(139, 92, 246, 0.2)); */ /* Фон удален */
  /* backdrop-filter: blur(10px); */ /* Фильтр удален */
  /* border: 1px solid rgba(139, 92, 246, 0.4); */ /* Рамка удалена */
  border-radius: 1rem; /* Оставляем скругление */
  padding: 1.5rem; /* Оставляем паддинг */
  /* box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(139, 92, 246, 0.3); */ /* Тень удалена */
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
  /* Добавим легкий фон, чтобы контент не был прямо на глобальном фоне */
  background-color: rgba(42, 8, 46, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.2); /* Легкая рамка для отделения */
}

/* Убираем hover эффект, связанный с тенью */
/* .exercises-view-container:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(139, 92, 246, 0.4);
} */

.exercises-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
}

.exercises-view-title {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.exercises-view-toggle-btn {
  padding: 0.35rem 0.75rem;
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s;
}

.exercises-view-toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.exercises-view-content {
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(236, 64, 122, 0.3);
  margin-top: 1rem;
  color: #333;
  line-height: 1.6;
  max-height: 500px;
  overflow-y: auto;
}

/* Стили для лоадера */
.exercises-view-loader {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #ff67e7; /* Розовый цвет */
  animation: exercises-view-spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
  vertical-align: middle;
}

.exercises-view-loader-text {
  display: inline-block;
  color: rgba(255, 255, 255, 0.8);
  vertical-align: middle;
}

@keyframes exercises-view-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
