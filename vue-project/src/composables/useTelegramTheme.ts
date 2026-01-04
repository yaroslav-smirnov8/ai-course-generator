// src/composables/useTelegramTheme.ts
import { ref, onMounted, computed } from 'vue';
import { TelegramService } from '@/services/telegram';

export function useTelegramTheme() {
  const theme = ref(TelegramService.getTheme());

  // Добавляем синхронизацию с CSS переменными
  const applyTheme = (themeParams: any) => {
    const root = document.documentElement;

    root.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
    root.style.setProperty('--tg-theme-text-color', themeParams.text_color);
    root.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
    root.style.setProperty('--tg-theme-link-color', themeParams.link_color);
    root.style.setProperty('--tg-theme-button-color', themeParams.button_color);
    root.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
    root.style.setProperty('--tg-theme-secondary-bg-color', themeParams.secondary_bg_color);
  };

  onMounted(() => {
    // Применяем тему при монтировании
    applyTheme(theme.value);

    // Слушаем изменения темы
    window.Telegram?.WebApp?.onEvent('themeChanged', () => {
      theme.value = TelegramService.getTheme();
      applyTheme(theme.value);
    });
  });

  return {
    theme,
    applyTheme
  };
}
