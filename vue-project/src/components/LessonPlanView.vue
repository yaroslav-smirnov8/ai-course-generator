<template>
  <div class="lesson-plan-view">
    <v-card class="mb-4">
      <v-card-title class="d-flex justify-space-between align-center">
        <div>
          <v-icon color="primary" class="mr-2">mdi-book-open-page-variant</v-icon>
          {{ lessonPlan.title || 'План урока' }}
        </div>
        <div>
          <v-btn 
            icon 
            variant="text" 
            color="primary" 
            @click="copyToClipboard"
            :disabled="!lessonPlan.content"
          >
            <v-icon>mdi-content-copy</v-icon>
            <v-tooltip activator="parent" location="bottom">Копировать содержимое</v-tooltip>
          </v-btn>
          <v-btn 
            icon 
            variant="text" 
            color="primary" 
            @click="downloadPDF"
            :disabled="!lessonPlan.content"
          >
            <v-icon>mdi-file-pdf-box</v-icon>
            <v-tooltip activator="parent" location="bottom">Скачать PDF</v-tooltip>
          </v-btn>
          <v-btn 
            icon 
            variant="text" 
            color="primary" 
            @click="downloadDocx"
            :disabled="!lessonPlan.content"
          >
            <v-icon>mdi-file-word</v-icon>
            <v-tooltip activator="parent" location="bottom">Скачать DOCX</v-tooltip>
          </v-btn>
        </div>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text>
        <div v-if="lessonPlan.content" class="lesson-plan-content">
          <div v-html="formattedContent"></div>
        </div>
        <div v-else class="text-center py-4">
          <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
          <div v-else class="text-subtitle-1">План урока не найден или еще не создан</div>
        </div>
      </v-card-text>
    </v-card>
    
    <!-- Интеграция компонента расширений -->
    <lesson-plan-extensions 
      v-if="lessonPlan.content" 
      :lesson-plan-data="lessonPlan"
    ></lesson-plan-extensions>
    
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script>
import { ref, computed, reactive } from 'vue';
import LessonPlanExtensions from './LessonPlanExtensions.vue';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import { Packer, Document, Paragraph, TextRun } from 'docx';
import { saveAs } from 'file-saver';

export default {
  name: 'LessonPlanView',
  components: {
    LessonPlanExtensions
  },
  props: {
    lessonPlan: {
      type: Object,
      required: true,
      default: () => ({
        id: null,
        title: '',
        content: '',
        metadata: {}
      })
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const snackbar = reactive({
      show: false,
      text: '',
      color: 'info'
    });
    
    // Форматирование содержимого плана урока для отображения
    const formattedContent = computed(() => {
      if (!props.lessonPlan.content) return '';
      
      // Заменяем переносы строк на <br>
      let formatted = props.lessonPlan.content.replace(/\n/g, '<br>');
      
      // Выделяем заголовки
      formatted = formatted.replace(/^(#+)\s+(.*?)$/gm, (match, hashes, title) => {
        const level = hashes.length;
        return `<h${level} class="mt-3 mb-2">${title}</h${level}>`;
      });
      
      // Выделяем важные инструкции
      formatted = formatted.replace(/\[([^\]]+)\]/g, '<strong class="highlight">[$1]</strong>');
      
      // Выделяем списки
      formatted = formatted.replace(/^(\s*)-\s+(.*?)$/gm, '<li>$2</li>');
      formatted = formatted.replace(/<li>.*?<\/li>/gs, '<ul>$&</ul>');
      
      // Удаляем дублирующиеся ul
      formatted = formatted.replace(/<\/ul>\s*<ul>/g, '');
      
      return formatted;
    });
    
    // Копирование содержимого в буфер обмена
    const copyToClipboard = () => {
      if (!props.lessonPlan.content) return;
      
      navigator.clipboard.writeText(props.lessonPlan.content)
        .then(() => {
          showSnackbar('Содержимое скопировано в буфер обмена', 'success');
        })
        .catch(err => {
          console.error('Ошибка при копировании: ', err);
          showSnackbar('Не удалось скопировать содержимое', 'error');
        });
    };
    
    // Скачивание плана урока в формате PDF
    const downloadPDF = async () => {
      if (!props.lessonPlan.content) return;
      
      try {
        const element = document.querySelector('.lesson-plan-content');
        const canvas = await html2canvas(element);
        const imgData = canvas.toDataURL('image/png');
        
        const pdf = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4'
        });
        
        const imgProps = pdf.getImageProperties(imgData);
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
        
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        pdf.save(`${props.lessonPlan.title || 'lesson_plan'}.pdf`);
        
        showSnackbar('PDF успешно скачан', 'success');
      } catch (error) {
        console.error('Ошибка при создании PDF: ', error);
        showSnackbar('Не удалось создать PDF', 'error');
      }
    };
    
    // Скачивание плана урока в формате DOCX
    const downloadDocx = async () => {
      if (!props.lessonPlan.content) return;
      
      try {
        const content = props.lessonPlan.content;
        const lines = content.split('\n');
        
        const doc = new Document({
          sections: [{
            properties: {},
            children: lines.map(line => {
              return new Paragraph({
                children: [new TextRun(line)]
              });
            })
          }]
        });
        
        const buffer = await Packer.toBlob(doc);
        saveAs(buffer, `${props.lessonPlan.title || 'lesson_plan'}.docx`);
        
        showSnackbar('DOCX успешно скачан', 'success');
      } catch (error) {
        console.error('Ошибка при создании DOCX: ', error);
        showSnackbar('Не удалось создать DOCX', 'error');
      }
    };
    
    // Показать уведомление
    const showSnackbar = (text, color = 'info') => {
      snackbar.text = text;
      snackbar.color = color;
      snackbar.show = true;
    };
    
    return {
      formattedContent,
      copyToClipboard,
      downloadPDF,
      downloadDocx,
      snackbar
    };
  }
};
</script>

<style scoped>
.lesson-plan-view {
  max-width: 100%;
}

.lesson-plan-content {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 1rem;
}

:deep(.highlight) {
  background-color: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 4px;
  border-radius: 4px;
}

:deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
  color: var(--v-primary-base);
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

:deep(ul) {
  padding-left: 20px;
  margin-bottom: 1em;
}

:deep(li) {
  margin-bottom: 0.5em;
}
</style> 