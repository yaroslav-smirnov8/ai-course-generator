export function initTelegramWebApp() {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.ready();
  }
}

export function closeTelegramWebApp() {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.close();
  }
}

