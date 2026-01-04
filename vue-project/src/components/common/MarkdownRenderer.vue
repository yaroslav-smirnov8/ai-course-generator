<!-- 
  Компонент для рендеринга Markdown-контента с поддержкой основных форматов разметки:
  - **Жирный текст**
  - *Курсив*
  - Заголовки в формате **1. Заголовок:**
  - Маркированные списки (*, -)
  - Нумерованные списки (1., 2. и т.д.)
  - Блоки кода с помощью `обратных кавычек`
-->
<template>
  <div class="markdown-renderer">
    <div v-html="formattedContent" class="md-content"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatMarkdown } from '../../utils/markdown'

const props = defineProps({
  // Исходный текст в формате Markdown
  content: {
    type: [String, Object, Array, Number, Boolean], // Разрешаем разные типы данных
    required: true
  }
})

// Форматируем контент с помощью функции из utils/markdown
const formattedContent = computed(() => {
  try {
    // Проверка на пустые значения или null/undefined
    if (!props.content && props.content !== 0 && props.content !== false) {
      console.warn('MarkdownRenderer: Получен пустой content', props.content);
      return '';
    }
    
    // Логгирование типа данных для отладки
    console.debug('MarkdownRenderer: тип content =', typeof props.content);
    
    // Преобразуем данные в строку, если они не строковые
    const contentToFormat = typeof props.content === 'string' 
      ? props.content 
      : String(props.content);
    
    return formatMarkdown(contentToFormat);
  } catch (error) {
    console.error('Ошибка при форматировании markdown:', error);
    return `<p class="error-message">Ошибка отображения контента</p>`;
  }
})
</script>

<style>
.markdown-renderer {
  width: 100%;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

/* Общие стили для markdown контента */
.md-content {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  font-size: 1rem;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
  color: #333;
}

.md-content h1,
.md-content h2,
.md-content h3,
.md-content h4,
.md-content h5,
.md-content h6 {
  font-weight: bold;
  margin-top: 1.2em;
  margin-bottom: 0.5em;
  color: #333;
}

.md-content p {
  margin-bottom: 1em;
}

.md-content ul,
.md-content ol {
  padding-left: 2em;
  margin-bottom: 1em;
}

.md-content li {
  margin-bottom: 0.5em;
}

.md-content code {
  font-family: monospace;
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
}
</style>