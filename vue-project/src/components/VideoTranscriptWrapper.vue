<template>
  <div class="video-transcript-wrapper">
    <!-- Оригинальный компонент VideoTranscript -->
    <video-transcript ref="transcriptComponent" @transcript-ready="onTranscriptReady"></video-transcript>
    
    <!-- Компонент расширений для транскрипта -->
    <video-transcript-extensions 
      v-if="transcriptData && transcript"
      :transcript-data="transcriptData"
      :video-id="videoId"
      :transcript="transcript"
    ></video-transcript-extensions>
  </div>
</template>

<script>
import { ref, reactive } from 'vue';
import VideoTranscript from './VideoTranscript.vue';
import VideoTranscriptExtensions from './VideoTranscriptExtensions.vue';

export default {
  name: 'VideoTranscriptWrapper',
  components: {
    VideoTranscript,
    VideoTranscriptExtensions
  },
  setup() {
    const transcriptComponent = ref(null);
    const transcript = ref(null);
    const videoId = ref('');
    const transcriptData = reactive({
      title: '',
      language: 'English'
    });
    
    // Обработчик события получения транскрипта
    const onTranscriptReady = (data) => {
      transcript.value = data.transcript;
      videoId.value = data.videoId;
      
      // Заполняем данные для компонента расширений
      transcriptData.title = data.title || `Video ${data.videoId}`;
      transcriptData.language = data.language || 'English';
    };
    
    return {
      transcriptComponent,
      transcript,
      videoId,
      transcriptData,
      onTranscriptReady
    };
  }
};
</script>

<style scoped>
.video-transcript-wrapper {
  width: 100%;
}
</style> 