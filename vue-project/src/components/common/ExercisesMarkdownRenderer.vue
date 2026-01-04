<template>
  <div class="exercises-markdown-renderer">
    <MarkdownRenderer 
      :content="processedContent" 
      theme="dark" 
      class="exercises-scoped-content"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import MarkdownRenderer from './MarkdownRenderer.vue';

// Пропсы компонента
const props = defineProps<{
  content: string;
}>();

// Обрабатываем контент, добавляя префикс "exercises-" к классам
const processedContent = computed(() => {
  if (!props.content) return '';
  
  // Добавляем стилизацию для заголовков уровня 1 и 2
  const content = props.content
    .replace(/^# (.*?)$/gm, '<h1 class="exercises-main-heading">$1</h1>')
    .replace(/^## (.*?)$/gm, '<h2 class="exercises-section-heading">$1</h2>');
  
  // Заменяем классы в контенте на версии с префиксом
  return content
    .replace(/class="lesson-plan-heading"/g, 'class="exercises-lesson-plan-heading"')
    .replace(/class="lesson-plan-subheading"/g, 'class="exercises-lesson-plan-subheading"')
    .replace(/class="lesson-plan-paragraph"/g, 'class="exercises-lesson-plan-paragraph"')
    .replace(/class="lesson-plan-list"/g, 'class="exercises-lesson-plan-list"')
    .replace(/class="lesson-plan-list-item"/g, 'class="exercises-lesson-plan-list-item"')
    .replace(/class="lesson-plan-bold"/g, 'class="exercises-lesson-plan-bold"')
    .replace(/class="lesson-plan-italic"/g, 'class="exercises-lesson-plan-italic"')
    .replace(/class="answer-content"/g, 'class="exercises-answer-content"')
    .replace(/class="instruction-content"/g, 'class="exercises-instruction-content"');
});
</script>

<style scoped>
.exercises-markdown-renderer {
  --exercises-text-color: #ffffff;
  --exercises-dark-bg: rgba(30, 30, 30, 0.6);
  --exercises-border-color: rgba(139, 92, 246, 0.4);
  
  color: var(--exercises-text-color);
  width: 100%;
}

.exercises-scoped-content {
  display: block;
  width: 100%;
}

:deep(.markdown-content) {
  color: var(--exercises-text-color);
  line-height: 1.6;
}

:deep(.exercises-main-heading) {
  font-size: 1.8rem;
  margin-top: 0;
  margin-bottom: 1.2em;
  color: #a855f7;
  text-align: center;
}

:deep(.exercises-section-heading) {
  font-size: 1.4rem;
  margin-top: 1.8em;
  margin-bottom: 0.8em;
  color: #d8b4fe;
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
  padding-bottom: 0.3em;
}

:deep(h1), 
:deep(h2), 
:deep(h3), 
:deep(h4), 
:deep(h5), 
:deep(h6) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  line-height: 1.3;
}

:deep(p) {
  margin-bottom: 1em;
}

:deep(ol), 
:deep(ul) {
  margin-left: 1.5rem;
  margin-bottom: 1em;
}

:deep(li) {
  margin-bottom: 0.5em;
}

:deep(pre), 
:deep(code) {
  background-color: var(--exercises-dark-bg);
  border-radius: 4px;
  padding: 0.2em 0.4em;
  font-family: monospace;
}

:deep(pre) {
  padding: 1em;
  overflow-x: auto;
  margin-bottom: 1em;
}

:deep(blockquote) {
  border-left: 4px solid var(--exercises-border-color);
  padding-left: 1em;
  margin-left: 0;
  margin-right: 0;
  font-style: italic;
}

:deep(a) {
  color: #a855f7;
  text-decoration: underline;
}

:deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 1em 0;
}
</style> 