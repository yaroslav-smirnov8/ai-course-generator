import { api } from '@/api/client';
import type { TelegramWebAppTheme, TelegramUser, TelegramAppData } from '@/types';
import { ref, onMounted } from 'vue';

// Объявляем типы для глобальных методов
declare global {
  interface Window {
    Telegram?: any;
    debugTelegramWebApp?: () => void;
  }
}

export class TelegramService {
  private static webApp = window.Telegram?.WebApp;
  private static initData: string | null = null;
  private static platform: string | null = null;
  private static version: string | null = null;

  static initialize() {
    console.log('Telegram WebApp object:', window.Telegram?.WebApp);

    if (!this.webApp) {
      throw new Error('Telegram WebApp is not available');
    }

    try {
      const webAppData = this.webApp.initData;
      console.log('WebApp Data:', webAppData);

      if (!webAppData) {
        throw new Error('No init data available');
      }

      this.initData = webAppData;
      this.platform = this.webApp.platform;
      this.version = this.webApp.version;

      // Не устанавливаем заголовки здесь - они будут установлены в интерцепторе

      this.webApp.ready();
      this.webApp.expand();
      
      // Запускаем решение проблемы с черным блоком
      setTimeout(() => {
        // Включаем полноэкранный режим
        this.enableFullscreen();
        
        // Добавляем дополнительные обработчики для внешнего вида
        this.fixBlackScreenIssue();
      }, 200);

      return true;
    } catch (error) {
      console.error('Failed to initialize Telegram WebApp:', error);
      throw error;
    }
  }

  /**
   * Фикс проблемы с черным блоком
   */
  static fixBlackScreenIssue() {
    if (!this.isAvailable()) {
      return;
    }

    // Проверяем, есть ли черный прямоугольник
    const fixBlackBlock = () => {
      // Находим все элементы с классом telegram-header-spacer
      const spacers = document.querySelectorAll('.telegram-header-spacer');
      if (spacers.length > 0) {
        spacers.forEach(spacer => {
          // Устанавливаем правильную высоту
          const spacerElement = spacer as HTMLElement;
          spacerElement.style.height = '190px';
          spacerElement.style.minHeight = '190px';
          spacerElement.style.maxHeight = '190px';
          spacerElement.style.backgroundColor = 'transparent';
          spacerElement.style.display = 'block';
          spacerElement.style.position = 'relative';
          spacerElement.style.zIndex = '5';
          spacerElement.style.margin = '0';
          spacerElement.style.padding = '0';
        });
      }

      // Устанавливаем стили для html, body
      document.documentElement.style.margin = '0';
      document.documentElement.style.padding = '0';
      document.documentElement.style.overflowX = 'hidden';
      document.documentElement.style.width = '100%';
      document.documentElement.style.height = '100%';
      document.documentElement.style.background = 'transparent';

      document.body.style.margin = '0';
      document.body.style.padding = '0';
      document.body.style.overflowX = 'hidden';
      document.body.style.width = '100%';
      document.body.style.height = '100%';
      document.body.style.background = 'transparent';

      // Устанавливаем стили для контейнера приложения
      const appElement = document.getElementById('app');
      if (appElement) {
        appElement.style.margin = '0';
        appElement.style.padding = '0';
        appElement.style.width = '100%';
        appElement.style.minHeight = '100vh';
        appElement.style.background = 'transparent';
      }
    };

    // Запускаем фикс сразу
    fixBlackBlock();

    // Затем запускаем периодически для уверенности
    setTimeout(fixBlackBlock, 500);
    setTimeout(fixBlackBlock, 1000);
    setTimeout(fixBlackBlock, 2000);

    // Добавляем наблюдатель за DOM, чтобы применить стили к новым элементам
    if (window.MutationObserver) {
      const observer = new MutationObserver((mutations) => {
        let needsFix = false;
        
        mutations.forEach(mutation => {
          if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            for (let i = 0; i < mutation.addedNodes.length; i++) {
              const node = mutation.addedNodes[i];
              if (node.nodeType === 1) { // ELEMENT_NODE
                if ((node as Element).classList?.contains('telegram-header-spacer') || 
                    (node as Element).querySelector('.telegram-header-spacer')) {
                  needsFix = true;
                  break;
                }
              }
            }
          }
        });
        
        if (needsFix) {
          fixBlackBlock();
        }
      });
      
      observer.observe(document.body, { 
        childList: true, 
        subtree: true 
      });
    }
  }

  /**
   * Включение полноэкранного режима
   */
  static enableFullscreen() {
    const webApp = this.webApp;
    
    if (!webApp) {
      console.warn('Telegram WebApp is not available');
      return;
    }
    
    try {
      // Базовые стили для полноэкранного режима
      document.documentElement.style.margin = '0';
      document.documentElement.style.padding = '0';
      document.documentElement.style.overflowX = 'hidden';
      document.body.style.margin = '0';
      document.body.style.padding = '0';
      document.body.style.overflowX = 'hidden';
      
      // Проверяем поддержку нового API для полноэкранного режима (Bot API 8.0+)
      if (webApp.requestFullscreen) {
        console.log('Using requestFullscreen API (Bot API 8.0+)');
        try {
          // Вызываем метод без обработки Promise, так как в некоторых версиях
          // Telegram WebApp API этот метод может не возвращать Promise
          webApp.requestFullscreen();
          console.log('Fullscreen requested');
        } catch (error) {
          console.error('Error requesting fullscreen:', error);
          // Если не удалось активировать полноэкранный режим, используем обычное расширение
          webApp.expand();
        }
      } else {
        console.log('Fullscreen API not available, using expand() instead');
        // Пытаемся максимально расширить приложение
        webApp.expand();
      }
      
      // Устанавливаем обработчик изменения размера окна
      this.setupViewportHandler();
    } catch (error) {
      console.error('Error setting up fullscreen mode:', error);
    }
  }

  /**
   * Проверка доступности WebApp
   */
  static isAvailable(): boolean {
    return Boolean(this.webApp);
  }

  /**
   * Получение данных пользователя
   */
  static getUser(): TelegramUser | undefined {
    return this.isAvailable() ? this.webApp!.initDataUnsafe.user : undefined;
  }

  /**
   * Получение initData
   */
  static getInitData(): string {
    return this.initData || '';
  }

  /**
   * Получение платформы
   */
  static getPlatform(): string | undefined {
    return this.isAvailable() ? this.webApp!.platform : undefined;
  }

  /**
   * Получение версии
   */
  static getVersion(): string {
    return this.version || '';
  }

  /**
   * Получение параметров темы
   */
  static getTheme(): TelegramWebAppTheme {
    return this.webApp?.themeParams || {
      bg_color: '',
      text_color: '',
      hint_color: '',
      link_color: '',
      button_color: '',
      button_text_color: ''
    };
  }

  /**
   * Получение всех данных WebApp
   */
  static getAppData(): Partial<TelegramAppData> {
    return {
      user: this.getUser(),
      platform: this.getPlatform(),
      version: this.getVersion(),
      themeParams: this.getTheme()
    };
  }

  /**
   * Показать всплывающее сообщение
   */
  static async showAlert(message: string): Promise<void> {
    return this.webApp?.showAlert(message);
  }

  /**
   * Показать модальное окно с кнопками
   */
  static showConfirm(message: string, callback: (confirmed: boolean) => void): void {
    if (this.isAvailable()) {
      this.webApp!.showPopup({
        message,
        buttons: [
          { type: 'ok', text: 'Да' },
          { type: 'cancel', text: 'Нет' }
        ]
      }).then((buttonId) => {
        callback(buttonId === 'ok');
      });
    }
  }

  /**
   * Показать модальное окно
   */
  static async showPopup(params: TelegramWebApp.PopupParams): Promise<string> {
    return this.webApp?.showPopup(params);
  }

  /**
   * Закрыть WebApp
   */
  static close(): void {
    this.webApp?.close();
  }

  /**
   * Развернуть WebApp на весь экран
   */
  static expand(): void {
    if (this.isAvailable()) {
      this.webApp!.expand();
    }
  }

  /**
   * Установить основной цвет кнопки
   */
  static setMainButtonColor(color: string): void {
    if (this.webApp?.MainButton) {
      this.webApp.MainButton.color = color;
    }
  }

  /**
   * Установить текст основной кнопки
   */
  static setMainButtonText(text: string): void {
    if (this.webApp?.MainButton) {
      this.webApp.MainButton.text = text;
    }
  }

  /**
   * Показать основную кнопку
   */
  static showMainButton(): void {
    this.webApp?.MainButton?.show();
  }

  /**
   * Скрыть основную кнопку
   */
  static hideMainButton(): void {
    this.webApp?.MainButton?.hide();
  }

  /**
   * Установить обработчик для основной кнопки
   */
  static onMainButtonClick(callback: () => void): void {
    if (this.webApp?.MainButton) {
      this.webApp.MainButton.onClick(callback);
    }
  }

  /**
   * Добавить обработчик события
   */
  static onEvent(eventType: string, callback: Function): void {
    this.webApp?.onEvent(eventType, callback);
  }

  /**
   * Удалить обработчик события
   */
  static offEvent(eventType: string, callback: Function): void {
    this.webApp?.offEvent(eventType, callback);
  }

  /**
   * Проверка поддержки версии
   */
  static isVersionSupported(minVersion: string): boolean {
    if (!this.version) return false;

    const current = this.version.split('.').map(Number);
    const minimum = minVersion.split('.').map(Number);

    for (let i = 0; i < Math.max(current.length, minimum.length); i++) {
      const a = current[i] || 0;
      const b = minimum[i] || 0;
      if (a > b) return true;
      if (a < b) return false;
    }
    return true;
  }

  /**
   * Получить параметр запуска
   */
  static getStartParam(): string {
    if (this.isAvailable() && this.webApp!.initDataUnsafe.start_param) {
      return this.webApp!.initDataUnsafe.start_param;
    }
    return '';
  }

  /**
   * Получить язык
   */
  static getLanguage(): string {
    if (this.isAvailable() && this.webApp!.initDataUnsafe.user?.language_code) {
      return this.webApp!.initDataUnsafe.user.language_code;
    }
    return 'en'; // Возвращаем английский по умолчанию
  }

  /**
   * Получить цветовую схему
   */
  static getColorScheme(): string {
    return this.isAvailable() ? this.webApp!.colorScheme : 'light';
  }

  /**
   * Проверить, открыто ли приложение в Telegram
   */
  static isInTelegram(): boolean {
    return Boolean(this.webApp);
  }

  /**
   * Отправить данные в Telegram
   */
  static sendData(data: any): void {
    if (!this.isAvailable()) {
      throw new Error('Telegram WebApp is not available');
    }
    
    try {
      // Преобразуем данные в строку JSON
      const jsonData = typeof data === 'string' ? data : JSON.stringify(data);
      
      // Отправляем данные в Telegram
      this.webApp!.sendData(jsonData);
      console.log('Data sent to Telegram:', data);
    } catch (error) {
      console.error('Error sending data to Telegram:', error);
      throw error;
    }
  }

  /**
   * Метод для отладки DOM в контексте Telegram WebApp
   * Позволяет найти проблемные элементы, которые могут перекрывать контент
   */
  static debugWebApp(): void {
    if (!window.Telegram?.WebApp) {
      console.error('TelegramService: WebApp не инициализирован');
      return;
    }
    
    console.log('TelegramService: Начинаем отладку WebApp');
    
    // Анализируем WebApp container
    const webAppContainer = window.Telegram.WebApp.viewportStableHeight;
    console.log('WebApp viewport height:', webAppContainer);
    
    // Находим все fixed элементы
    const fixedElements = Array.from(document.querySelectorAll('*')).filter(el => {
      const style = window.getComputedStyle(el);
      return style.position === 'fixed' || style.position === 'absolute';
    });
    
    console.log('Найдено fixed/absolute элементов:', fixedElements.length);
    
    // Проверяем перекрытие WebApp элементами
    const suspects = fixedElements.filter(el => {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      
      // Элемент должен быть видимым и перекрывать значительную часть экрана
      return (
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        parseFloat(style.opacity) > 0 &&
        rect.width > window.innerWidth / 3 &&
        rect.height > window.innerHeight / 3
      );
    });
    
    // Выводим подозрительные элементы
    if (suspects.length > 0) {
      console.log('Подозрительные элементы:', suspects);
      
      // Временно подсвечиваем их для визуальной отладки
      suspects.forEach(el => {
        const htmlEl = el as HTMLElement;
        const originalBg = htmlEl.style.backgroundColor;
        const originalOutline = htmlEl.style.outline;
        
        htmlEl.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
        htmlEl.style.outline = '2px solid red';
        
        setTimeout(() => {
          htmlEl.style.backgroundColor = originalBg;
          htmlEl.style.outline = originalOutline;
        }, 5000);
      });
      
      // Создаем кнопку для принудительной очистки
      const cleanupButton = document.createElement('button');
      cleanupButton.textContent = 'Очистить перекрывающие элементы';
      cleanupButton.style.position = 'fixed';
      cleanupButton.style.bottom = '100px';
      cleanupButton.style.left = '50%';
      cleanupButton.style.transform = 'translateX(-50%)';
      cleanupButton.style.zIndex = '9999';
      cleanupButton.style.padding = '10px 15px';
      cleanupButton.style.backgroundColor = '#f44336';
      cleanupButton.style.color = 'white';
      cleanupButton.style.border = 'none';
      cleanupButton.style.borderRadius = '4px';
      cleanupButton.style.fontSize = '14px';
      
      cleanupButton.onclick = () => {
        suspects.forEach(el => {
          try {
            (el as HTMLElement).style.display = 'none';
            (el as HTMLElement).style.opacity = '0';
            (el as HTMLElement).style.visibility = 'hidden';
            (el as HTMLElement).style.zIndex = '-1';
            (el as HTMLElement).style.pointerEvents = 'none';
          } catch (error: unknown) {
            console.error('Ошибка при скрытии элемента:', error);
          }
        });
        
        cleanupButton.remove();
        alert('Элементы скрыты. Попробуйте навигацию теперь.');
      };
      
      document.body.appendChild(cleanupButton);
    } else {
      console.log('Подозрительных элементов не найдено');
    }
    
    // Проверяем WebApp на блокировку кликов
    const clickTest = document.createElement('div');
    clickTest.style.position = 'fixed';
    clickTest.style.top = '0';
    clickTest.style.left = '0';
    clickTest.style.width = '100%';
    clickTest.style.height = '100%';
    clickTest.style.backgroundColor = 'rgba(0,0,0,0.01)';
    clickTest.style.zIndex = '9998';
    clickTest.style.pointerEvents = 'auto';
    
    clickTest.addEventListener('click', (e: MouseEvent) => {
      clickTest.remove();
      console.log('Клик обработан:', e);
    });
    
    document.body.appendChild(clickTest);
    
    setTimeout(() => {
      if (document.body.contains(clickTest)) {
        clickTest.remove();
      }
    }, 5000);
  }

  /**
   * Устанавливает обработчик изменения размера окна
   */
  private static setupViewportHandler() {
    const webApp = this.webApp;
    
    if (!webApp) {
      return;
    }
    
    // Добавляем обработчик для поддержания полноэкранного режима
    const handleViewportChanged = () => {
      console.log('Viewport changed, checking fullscreen status');
      
      // Проверяем, не потерян ли полноэкранный режим
      if (webApp.isFullscreen === false && webApp.requestFullscreen) {
        console.log('Fullscreen mode lost, attempting to restore');
        try {
          webApp.requestFullscreen();
        } catch (e) {
          console.error('Failed to restore fullscreen:', e);
        }
      } 
      // Проверяем, не потеряно ли расширение
      else if (!webApp.isExpanded) {
        console.log('App not expanded, re-expanding');
        webApp.expand();
      }
    };
    
    // Добавляем обработчик события изменения viewport
    webApp.onEvent('viewportChanged', handleViewportChanged);
    
    // Выводим информацию о текущем состоянии
    console.log('Viewport handler setup completed. Current state:', {
      isExpanded: webApp.isExpanded,
      isFullscreen: webApp.isFullscreen,
      version: webApp.version
    });
  }

  /**
   * Обрабатывает нажатие на кнопку в Telegram WebApp
   * @param buttonId Идентификатор кнопки
   */
  static handleButtonClick(buttonId: string): void {
    if (!this.isAvailable()) {
      console.warn('Telegram WebApp is not available');
      return;
    }
    
    const webApp = this.webApp;
    
    if (!webApp) {
      return;
    }
    
    console.log(`Handling button click: ${buttonId}`);
    
    // Обработка различных кнопок
    switch (buttonId) {
      case 'main':
        if (webApp.MainButton && webApp.MainButton.isVisible) {
          webApp.MainButton.onClick(webApp.MainButton.text);
        }
        break;
      case 'back':
        if (webApp.BackButton && webApp.BackButton.isVisible) {
          webApp.BackButton.onClick();
        }
        break;
      case 'close':
        webApp.close();
        break;
      default:
        console.log(`Unknown button: ${buttonId}`);
    }
  }

  // Метод для принудительного отображения кнопки "Назад"
  static forceShowBackButton(): void {
    if (!this.isAvailable()) {
      console.warn('Telegram WebApp is not available');
      return;
    }
    
    const webApp = this.webApp;
    
    if (!webApp || !webApp.BackButton) {
      console.warn('BackButton is not available');
      return;
    }
    
    try {
      console.log('Принудительно показываем кнопку "Назад"');
      webApp.BackButton.show();
    } catch (err) {
      console.error('Ошибка при отображении кнопки "Назад":', err);
    }
  }
  
  // Метод для принудительного скрытия кнопки "Назад"
  static forceHideBackButton(): void {
    if (!this.isAvailable()) {
      console.warn('Telegram WebApp is not available');
      return;
    }
    
    const webApp = this.webApp;
    
    if (!webApp || !webApp.BackButton) {
      console.warn('BackButton is not available');
      return;
    }
    
    try {
      console.log('Принудительно скрываем кнопку "Назад"');
      webApp.BackButton.hide();
    } catch (err) {
      console.error('Ошибка при скрытии кнопки "Назад":', err);
    }
  }
  
  // Метод для настройки обработчика нажатия на кнопку "Назад"
  static setupBackButtonHandler(callback: () => void): void {
    if (!this.isAvailable()) {
      console.warn('Telegram WebApp is not available');
      return;
    }
    
    const webApp = this.webApp;
    
    if (!webApp || !webApp.BackButton) {
      console.warn('BackButton is not available');
      return;
    }
    
    try {
      console.log('Настраиваем обработчик нажатия на кнопку "Назад"');
      
      // Сначала удаляем все предыдущие обработчики
      try {
        webApp.BackButton.offClick(() => {});
      } catch (e) {
        console.log('Ошибка при удалении предыдущих обработчиков:', e);
      }
      
      // Устанавливаем новый обработчик
      webApp.BackButton.onClick(callback);
    } catch (err) {
      console.error('Ошибка при настройке обработчика кнопки "Назад":', err);
    }
  }
}

// Добавляем метод отладки в глобальный объект
window.debugTelegramWebApp = TelegramService.debugWebApp;

// Хук для использования в компонентах Vue
export function useTelegramApp() {
  const isInitialized = ref(false);
  const error = ref<string | null>(null);
  const user = ref<TelegramUser | null>(null);

  onMounted(() => {
    try {
      TelegramService.initialize();
      isInitialized.value = true;
      const telegramUser = TelegramService.getUser();
      user.value = telegramUser || null;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to initialize WebApp';
      console.error('Telegram WebApp initialization error:', err);
    }
  });

  return {
    isInitialized,
    error,
    user,
    showAlert: TelegramService.showAlert.bind(TelegramService),
    showConfirm: TelegramService.showConfirm.bind(TelegramService),
    close: TelegramService.close.bind(TelegramService),
    getTheme: TelegramService.getTheme.bind(TelegramService),
    getAppData: TelegramService.getAppData.bind(TelegramService)
  };
}

export type { TelegramWebAppTheme, TelegramUser, TelegramAppData };
