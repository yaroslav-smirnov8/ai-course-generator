declare global {
  namespace TelegramWebApp {
    interface PopupButton {
      id?: string;
      type?: 'ok' | 'close' | 'cancel' | 'default';
      text?: string;
    }

    interface PopupParams {
      message: string;
      title?: string;
      buttons?: PopupButton[];
      defaultButtonText?: string;
    }

    interface ViewportSettings {
      height?: number;
      is_expanded?: boolean;
      is_fullscreen?: boolean;
    }

    interface MainButton {
      text: string;
      color: string;
      textColor: string;
      isVisible: boolean;
      isActive: boolean;
      isProgressVisible: boolean;
      setText(text: string): void;
      onClick(callback: Function): void;
      offClick(callback: Function): void;
      show(): void;
      hide(): void;
      enable(): void;
      disable(): void;
      showProgress(leaveActive?: boolean): void;
      hideProgress(): void;
    }

    interface WebApp {
      initData: string;
      initDataUnsafe: WebAppInitData;
      platform: string;
      version: string;
      ready(): void;
      close(): void;
      expand(): void;
      isExpanded: boolean;
      isActive?: boolean;
      isFullscreen?: boolean;
      safeAreaInset?: {
        top: number;
        right: number;
        bottom: number;
        left: number;
      };
      contentSafeAreaInset?: {
        top: number;
        right: number;
        bottom: number;
        left: number;
      };
      setViewportSettings(settings: ViewportSettings): void;
      requestViewport?(settings: ViewportSettings): void;
      requestFullscreen?(): Promise<void>;
      exitFullscreen?(): Promise<void>;
      enableClosingConfirmation?(): void;
      disableClosingConfirmation?(): void;
      MainButton: MainButton;

      // Только методы, которые мы реально используем
      showAlert(message: string): Promise<void>;
      showPopup(params: PopupParams): Promise<string>;

      // Theme
      themeParams: {
        bg_color: string;
        text_color: string;
        hint_color: string;
        link_color: string;
        button_color: string;
        button_text_color: string;
      };
      colorScheme: 'light' | 'dark';

      // Events
      onEvent(eventType: string, callback: Function): void;
      offEvent(eventType: string, callback: Function): void;

      viewportHeight: number;
      viewportStableHeight: number;
      headerColor: string;
      backgroundColor: string;
      isClosingConfirmationEnabled: boolean;
      BackButton: BackButton;
      HapticFeedback: HapticFeedback;
      isVersionAtLeast: (version: string) => boolean;
      setHeaderColor: (color: string) => void;
      setBackgroundColor: (color: string) => void;
      sendData: (data: string) => void;
      openLink: (url: string) => void;
      openTelegramLink: (url: string) => void;
      showConfirm: (message: string) => Promise<boolean>;
    }

    interface WebAppInitData {
      query_id?: string;
      user?: WebAppUser;
      receiver?: WebAppUser;
      chat?: WebAppChat;
      chat_type?: string;
      chat_instance?: string;
      start_param?: string;
      auth_date?: number;
      hash?: string;
    }

    interface WebAppUser {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
      is_premium?: boolean;
      photo_url?: string;
    }

    interface WebAppChat {
      id: number;
      type: string;
      title: string;
      username?: string;
      photo_url?: string;
    }

    interface ThemeParams {
      bg_color: string;
      text_color: string;
      hint_color: string;
      link_color: string;
      button_color: string;
      button_text_color: string;
      secondary_bg_color?: string;
    }

    interface BackButton {
      isVisible: boolean;
      onClick: (callback: () => void) => void;
      offClick: (callback: () => void) => void;
      show: () => void;
      hide: () => void;
    }

    interface HapticFeedback {
      impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
      notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
      selectionChanged: () => void;
    }
  }

  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp.WebApp;
    };
  }
}

export {};
