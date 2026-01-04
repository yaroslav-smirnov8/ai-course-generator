interface NotificationOptions {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  text: string;
}

export function useNotification() {
  const notify = (options: NotificationOptions) => {
    // Здесь можно использовать любую библиотеку уведомлений
    // Например, vue-notification или toast
    console.log('Notification:', options);
  };

  return {
    notify
  };
} 