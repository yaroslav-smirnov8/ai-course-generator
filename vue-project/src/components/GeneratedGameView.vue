<template>
  <div v-if="isLoading || gameContent" class="game-view-container mt-4">
    <div v-if="isLoading" class="text-center">
      <!-- Обновленный лоадер -->
      <div class="game-view-loader"></div>
      <p class="game-view-loader-text">Генерация игры...</p>
    </div>
    <!-- Отображаем блок, только если есть контент -->
    <div v-else-if="gameContent">
      <div class="game-view-header mb-3">
        <h3 class="game-view-title">Сгенерированная игра {{ gameType ? `(Тип: ${gameType})` : '' }}</h3>
        <!-- Кнопка Скрыть/Показать -->
        <button
          @click="$emit('toggle-visibility')"
          class="game-view-toggle-btn"
        >
          {{ isVisible ? 'Скрыть' : 'Показать' }}
        </button>
      </div>
      <!-- Скрываем/показываем сам контент игры (Markdown) -->
      <div v-if="isVisible">
        <!-- Используем pre для простого отображения Markdown или можно подключить библиотеку -->
        <pre class="game-view-content whitespace-pre-wrap">{{ gameContent }}</pre>
         <!-- Отображение ошибки, если gameContent содержит сообщение об ошибке -->
         <div v-if="gameContent.startsWith('### Error')" class="game-view-error mt-2 text-sm">
            {{ gameContent }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Убираем импорт GeneratedGameResponse, т.к. теперь работаем со строкой

defineProps<{
  gameContent: string | null; // Принимаем Markdown контент
  gameType?: string | null; // Тип игры опционален
  isLoading: boolean;
  isVisible: boolean;
}>()

defineEmits(['toggle-visibility'])
</script>

<style scoped>
.game-view-container {
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
/* .game-view-container:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5), 0 0 20px rgba(139, 92, 246, 0.4);
} */

.game-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
}

.game-view-title {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  text-shadow: 0 0 8px rgba(255, 103, 231, 0.5);
}

.game-view-toggle-btn {
  padding: 0.35rem 0.75rem;
  background-color: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.3s;
}

.game-view-toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.game-view-content {
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
.game-view-loader {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #ff67e7; /* Розовый цвет */
  animation: game-view-spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
  vertical-align: middle;
}

.game-view-loader-text {
  display: inline-block;
  color: rgba(255, 255, 255, 0.8);
  vertical-align: middle;
}

@keyframes game-view-spin {
  to {
    transform: rotate(360deg);
  }
}

/* Стили для ошибки */
.game-view-error {
  color: #dc3545; /* Красный цвет для ошибки */
  background-color: rgba(220, 53, 69, 0.1);
  border-left: 4px solid #dc3545;
  padding: 0.75rem 1rem;
  border-radius: 0 0.5rem 0.5rem 0;
}
</style>
