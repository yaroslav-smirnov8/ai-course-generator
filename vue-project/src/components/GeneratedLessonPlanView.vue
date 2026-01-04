<template>
  <div v-if="isLoading || planContent" class="plan-view-container mt-6">
    <div v-if="isLoading" class="text-center">
      <!-- Обновленный лоадер -->
      <div class="plan-view-loader"></div>
      <p class="plan-view-loader-text">Генерация плана урока...</p>
    </div>
    <!-- Отображаем блок, только если есть контент (независимо от видимости) -->
    <div v-else-if="planContent">
      <div class="plan-view-header mb-3">
        <h3 class="plan-view-title">Сгенерированный план урока</h3>
        <!-- Кнопка Скрыть/Показать -->
        <button
          @click="$emit('toggle-visibility')"
          class="plan-view-toggle-btn"
        >
          {{ isVisible ? 'Скрыть' : 'Показать' }}
        </button>
      </div>
      <!-- Скрываем/показываем сам контент плана -->
      <pre v-if="isVisible" class="plan-view-content whitespace-pre-wrap">{{ planContent }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  planContent: string | null;
  isLoading: boolean;
  isVisible: boolean; // Добавляем новый prop для управления видимостью
}>()

defineEmits(['toggle-visibility']) // Меняем событие
</script>

<style scoped>
.plan-view-container {
  /* background: linear-gradient(135deg, rgba(88, 28, 135, 0.4), rgba(139, 92, 246, 0.2)); */ /* Фон удален, используется глобальный */
  backdrop-filter: blur(10px);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(139, 92, 246, 0.3);
  transition: all 0.3s;
  position: relative;
  overflow: hidden; /* Чтобы градиент не вылезал */
}

.plan-view-container:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(139, 92, 246, 0.4);
}

.plan-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* margin-bottom: 1.25rem; */ /* Управляется mb-3 в template */
  padding-bottom: 0.75rem; /* Отступ снизу */
  border-bottom: 1px solid rgba(139, 92, 246, 0.3); /* Разделитель */
}

.plan-view-title {
  color: white;
  font-size: 1.25rem; /* Немного уменьшим */
  font-weight: 600;
  margin: 0;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.plan-view-toggle-btn {
  padding: 0.35rem 0.75rem; /* Уменьшим паддинг */
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.75rem; /* Уменьшим шрифт */
  cursor: pointer;
  transition: all 0.3s;
}

.plan-view-toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px); /* Меньший сдвиг */
}

.plan-view-content {
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.9));
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(236, 64, 122, 0.3);
  margin-top: 1rem; /* Добавим отступ сверху */
  color: #333; /* Цвет текста для контента */
  line-height: 1.6;
  max-height: 500px; /* Ограничение высоты */
  overflow-y: auto; /* Прокрутка */
}

/* Стили для лоадера */
.plan-view-loader {
  display: inline-block; /* Чтобы текст был рядом */
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #ff67e7; /* Розовый цвет */
  animation: plan-view-spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
  vertical-align: middle; /* Выравнивание по центру с текстом */
}

.plan-view-loader-text {
  display: inline-block; /* Чтобы текст был рядом */
  color: rgba(255, 255, 255, 0.8); /* Светлый текст */
  vertical-align: middle; /* Выравнивание по центру с лоадером */
}

@keyframes plan-view-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
