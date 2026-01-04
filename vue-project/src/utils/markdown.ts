/**
 * Функция форматирования Markdown-разметки в HTML
 * Преобразует простую разметку (**, *, списки, таблицы и т.д.) в форматированный HTML
 */
export function formatMarkdown(content: any): string {
  // Проверка типа и конвертация в строку, если нужно
  if (content === null || content === undefined) return '';

  // Преобразуем не-строковые данные в строку
  const contentStr = typeof content === 'string' ? content : String(content);

  if (!contentStr) return '';

  // Сначала обрабатываем таблицы, чтобы они не конфликтовали с другими правилами
  let formatted = processMarkdownTables(contentStr);

  // Обработка заголовков
  formatted = formatted
    // Заголовки с решеткой
    .replace(/^#\s+(.*?)$/gm, '<h1>$1</h1>')
    .replace(/^##\s+(.*?)$/gm, '<h2>$1</h2>')
    .replace(/^###\s+(.*?)$/gm, '<h3>$1</h3>')

  // Обработка форматирования текста
  formatted = formatted
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Жирный текст
    .replace(/\*(.*?)\*/g, '<em>$1</em>')  // Курсив

  // Обработка списков
  formatted = formatted
    // Маркированные списки
    .replace(/^\*\s+(.*?)$/gm, '<li>$1</li>')
    .replace(/^-\s+(.*?)$/gm, '<li>$1</li>')
    // Нумерованные списки
    .replace(/^(\d+)\.\s+(.*?)$/gm, '<li>$1. $2</li>')

  // Оборачиваем списки в <ul> или <ol>
  const lines = formatted.split('\n');
  let inList = false;
  const result = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('<li')) {
      if (!inList) {
        result.push('<ul>');
        inList = true;
      }
      result.push(line);
    } else {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      result.push(line);
    }
  }

  if (inList) {
    result.push('</ul>');
  }

  // Добавляем переводы строк и обрабатываем другие общие элементы форматирования
  return result.join('\n')
    .replace(/\n\n/g, '<br><br>')  // Пустые строки
    .replace(/`(.*?)`/g, '<code>$1</code>'); // Инлайн-код
}

/**
 * Обрабатывает markdown-таблицы и преобразует их в HTML
 */
function processMarkdownTables(content: string): string {
  // Регулярное выражение для поиска markdown-таблиц
  const tableRegex = /^(\|.*\|)\s*\n(\|[-\s|:]+\|)\s*\n((?:\|.*\|\s*\n?)*)/gm;

  return content.replace(tableRegex, (match, headerRow, separatorRow, bodyRows) => {
    // Обрабатываем заголовок таблицы
    const headers = headerRow.split('|')
      .map(cell => cell.trim())
      .filter(cell => cell !== '')
      .map(cell => `<th class="md-table-th">${cell}</th>`)
      .join('');

    // Обрабатываем строки тела таблицы
    const rows = bodyRows.trim().split('\n')
      .filter(row => row.trim() !== '')
      .map(row => {
        const cells = row.split('|')
          .map(cell => cell.trim())
          .filter(cell => cell !== '')
          .map(cell => `<td class="md-table-td">${cell}</td>`)
          .join('');
        return `<tr class="md-table-row">${cells}</tr>`;
      })
      .join('');

    // Возвращаем полную HTML-таблицу
    return `<div class="md-table-container">
      <table class="md-table">
        <thead class="md-table-header">
          <tr class="md-table-header-row">${headers}</tr>
        </thead>
        <tbody class="md-table-body">
          ${rows}
        </tbody>
      </table>
    </div>`;
  });
}

/**
 * CSS стили для отображения отформатированного Markdown
 */
export const markdownStyles = `
.md-content {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #ffffff;
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.md-content .md-heading {
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  color: #ffffff;
}

.md-content .md-list {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.md-content li {
  margin-bottom: 0.5rem;
  color: #f0f0f0;
}

.md-content strong {
  font-weight: bold;
  color: #ffffff;
}

.md-content em {
  font-style: italic;
  color: #e0e0e0;
}

.md-content code {
  font-family: monospace;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  color: #ffffff;
}

/* Стили для таблиц */
.md-table-container {
  overflow-x: auto;
  margin: 1rem 0;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.md-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #2d3748;
  font-size: 0.9rem;
}

.md-table-header {
  background-color: #1a202c;
}

.md-table-header-row {
  border-bottom: 2px solid #4a5568;
}

.md-table-th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #e2e8f0;
  border-right: 1px solid #4a5568;
}

.md-table-th:last-child {
  border-right: none;
}

.md-table-body {
  background-color: #2d3748;
}

.md-table-row {
  border-bottom: 1px solid #4a5568;
}

.md-table-row:hover {
  background-color: #4a5568;
}

.md-table-td {
  padding: 0.75rem;
  color: #e2e8f0;
  border-right: 1px solid #4a5568;
  vertical-align: top;
}

.md-table-td:last-child {
  border-right: none;
}

/* Адаптивные стили для мобильных устройств */
@media (max-width: 768px) {
  .md-table-container {
    font-size: 0.8rem;
  }

  .md-table-th,
  .md-table-td {
    padding: 0.5rem;
  }

  /* Для очень узких экранов делаем таблицу прокручиваемой */
  .md-table {
    min-width: 500px;
  }
}
`;