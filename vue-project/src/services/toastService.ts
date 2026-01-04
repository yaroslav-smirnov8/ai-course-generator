// Сервис для работы с тостами
export const toastService = {
  /**
   * Показать успешное сообщение
   * @param message Текст сообщения
   * @param duration Длительность в миллисекундах (по умолчанию 3000ms)
   */
  success(message: string, duration?: number) {
    if (window.__SIMPLE_TOAST__) {
      return window.__SIMPLE_TOAST__.success(message, duration);
    }
    return console.log('SUCCESS:', message);
  },

  /**
   * Показать сообщение об ошибке
   * @param message Текст сообщения
   * @param duration Длительность в миллисекундах (по умолчанию 4000ms)
   */
  error(message: string, duration?: number) {
    if (window.__SIMPLE_TOAST__) {
      return window.__SIMPLE_TOAST__.error(message, duration);
    }
    return console.error('ERROR:', message);
  },

  /**
   * Показать информационное сообщение
   * @param message Текст сообщения
   * @param duration Длительность в миллисекундах (по умолчанию 3000ms)
   */
  info(message: string, duration?: number) {
    if (window.__SIMPLE_TOAST__) {
      return window.__SIMPLE_TOAST__.info(message, duration);
    }
    return console.info('INFO:', message);
  },

  /**
   * Показать предупреждение
   * @param message Текст сообщения
   * @param duration Длительность в миллисекундах (по умолчанию 3500ms)
   */
  warning(message: string, duration?: number) {
    if (window.__SIMPLE_TOAST__) {
      return window.__SIMPLE_TOAST__.warning(message, duration);
    }
    return console.warn('WARNING:', message);
  },

  /**
   * Удалить все активные тосты
   */
  removeAll() {
    if (window.__SIMPLE_TOAST__) {
      window.__SIMPLE_TOAST__.removeAll();
    }
  }
}; 