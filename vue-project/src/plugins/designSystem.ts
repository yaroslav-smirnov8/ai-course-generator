/**
 * Плагин для интеграции дизайн-системы в Vue
 */

// Типы переменных дизайн-системы
export interface DesignSystemVars {
  colors: {
    primary: string;
    primaryDark: string;
    primaryLight: string;
    primaryBg: string;
    secondary: string;
    secondaryLight: string;
    secondaryDark: string;
    background: string;
    backgroundLight: string;
    surface: string;
    surfaceLight: string;
    text: string;
    textSecondary: string;
    textDark: string;
    error: string;
    success: string;
    warning: string;
    info: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    primary: string;
  };
  zIndices: {
    background: number;
    content: number;
    header: number;
    modal: number;
    toast: number;
    navbar: number;
  };
  radius: {
    sm: string;
    md: string;
    lg: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  fontSize: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  transitions: {
    fast: string;
    normal: string;
    slow: string;
  };
}

// Получение значения CSS-переменной
export function getCssVar(name: string, fallback?: string): string {
  if (typeof document === 'undefined') {
    return fallback || '';
  }
  
  const varName = name.startsWith('--') ? name : `--${name}`;
  const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  
  return value || fallback || '';
}

// Установка CSS-переменной
export function setCssVar(name: string, value: string): void {
  if (typeof document === 'undefined') {
    return;
  }
  
  const varName = name.startsWith('--') ? name : `--${name}`;
  document.documentElement.style.setProperty(varName, value);
}

// Добавление класса глобального фона
export function addGlobalBackground(element: HTMLElement): void {
  if (!element) return;
  
  element.classList.add('global-background');
}

// Удаление класса глобального фона
export function removeGlobalBackground(element: HTMLElement): void {
  if (!element) return;
  
  element.classList.remove('global-background');
}

// Проверка наличия CSS-файлов для дизайн-системы
function checkCssFiles(): boolean {
  if (typeof document === 'undefined') {
    return false;
  }
  
  const styleSheets = Array.from(document.styleSheets);
  
  // Проверяем, загружены ли наши файлы CSS
  const designSystemCssLoaded = styleSheets.some(sheet => {
    try {
      const rules = Array.from(sheet.cssRules);
      return rules.some(rule => 
        rule.cssText && (
          rule.cssText.includes('--color-primary') || 
          rule.cssText.includes('ds-button') ||
          rule.cssText.includes('ds-card')
        )
      );
    } catch (e) {
      // Ошибка CORS при доступе к cssRules из внешних таблиц стилей
      return false;
    }
  });
  
  return designSystemCssLoaded;
}

// Динамическая загрузка CSS-файлов
function loadCssFile(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    
    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`Не удалось загрузить CSS: ${url}`));
    
    document.head.appendChild(link);
  });
}

// Создание глобального фона
function createGlobalBackground(): HTMLElement | null {
  if (typeof document === 'undefined') {
    return null;
  }
  
  // Проверка, существует ли уже элемент фона
  let bgElement = document.querySelector('.global-background') as HTMLElement;
  
  // Если фона нет, создаем его
  if (!bgElement) {
    bgElement = document.createElement('div');
    bgElement.className = 'global-background';
    document.body.appendChild(bgElement);
  }
  
  return bgElement;
}

// Инициализация дизайн-системы
export async function initDesignSystem(): Promise<void> {
  // Проверка, загружены ли CSS-файлы
  const cssLoaded = checkCssFiles();
  
  // Если CSS не загружены, загружаем их
  if (!cssLoaded) {
    try {
      await Promise.all([
        loadCssFile('./src/styles/design-system.css'),
        loadCssFile('./src/styles/form-components.css'),
        loadCssFile('./src/styles/content-components.css')
      ]);
      
      console.log('Дизайн-система: CSS-файлы успешно загружены');
    } catch (error) {
      console.error('Дизайн-система: Ошибка при загрузке CSS-файлов', error);
    }
  }
  
  // Создаем глобальный фон, если он еще не существует
  createGlobalBackground();
  
  console.log('Дизайн-система инициализирована');
} 