/**
 * Сервис для оптимизации изображений
 */

/**
 * Проверяет поддержку WebP браузером
 * @returns Promise<boolean> - true, если браузер поддерживает WebP
 */
export const checkWebpSupport = async (): Promise<boolean> => {
  if (!window.createImageBitmap) return false;

  const webpData = 'data:image/webp;base64,UklGRh4AAABXRUJQVlA4TBEAAAAvAAAAAAfQ//73v/+BiOh/AAA=';
  const blob = await fetch(webpData).then(r => r.blob());
  
  try {
    return await createImageBitmap(blob).then(() => true, () => false);
  } catch (e) {
    return false;
  }
}

/**
 * Проверяет поддержку AVIF браузером
 * @returns Promise<boolean> - true, если браузер поддерживает AVIF
 */
export const checkAvifSupport = async (): Promise<boolean> => {
  if (!window.createImageBitmap) return false;

  const avifData = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgANogQEAwgMg8f8D///8WfhwB8+ErK42A=';
  const blob = await fetch(avifData).then(r => r.blob());
  
  try {
    return await createImageBitmap(blob).then(() => true, () => false);
  } catch (e) {
    return false;
  }
}

/**
 * Получает оптимальный формат изображения для текущего браузера
 * @returns Promise<string> - оптимальный формат изображения ('avif', 'webp', 'jpg', 'png')
 */
export const getOptimalImageFormat = async (): Promise<string> => {
  const avifSupported = await checkAvifSupport();
  if (avifSupported) return 'avif';
  
  const webpSupported = await checkWebpSupport();
  if (webpSupported) return 'webp';
  
  return 'jpg'; // Fallback на jpg
}

/**
 * Получает оптимизированный URL изображения
 * @param originalUrl Оригинальный URL изображения
 * @returns Promise<string> - оптимизированный URL изображения
 */
export const getOptimizedImageUrl = async (originalUrl: string): Promise<string> => {
  // Если URL уже содержит параметры оптимизации, возвращаем его как есть
  if (originalUrl.includes('format=') || originalUrl.includes('quality=')) {
    return originalUrl;
  }
  
  // Получаем оптимальный формат
  const format = await getOptimalImageFormat();
  
  // Если URL содержит параметры запроса, добавляем новые параметры
  if (originalUrl.includes('?')) {
    return `${originalUrl}&format=${format}&quality=80`;
  }
  
  // Иначе добавляем параметры запроса
  return `${originalUrl}?format=${format}&quality=80`;
}

/**
 * Создает оптимизированный элемент изображения
 * @param src Исходный URL изображения
 * @param alt Альтернативный текст
 * @param className CSS классы
 * @returns HTMLImageElement - оптимизированный элемент изображения
 */
export const createOptimizedImage = async (
  src: string, 
  alt: string = '', 
  className: string = ''
): Promise<HTMLImageElement> => {
  const img = document.createElement('img');
  img.alt = alt;
  if (className) img.className = className;
  
  // Добавляем lazy loading
  img.loading = 'lazy';
  
  // Устанавливаем оптимизированный URL
  img.src = await getOptimizedImageUrl(src);
  
  return img;
}

/**
 * Инициализирует оптимизацию изображений на странице
 */
export const initImageOptimization = (): void => {
  // Проверяем поддержку форматов
  Promise.all([checkWebpSupport(), checkAvifSupport()]).then(([webpSupported, avifSupported]) => {
    // Добавляем классы к body для CSS-селекторов
    if (webpSupported) document.body.classList.add('webp-support');
    if (avifSupported) document.body.classList.add('avif-support');
    
    console.log(`Image format support: WebP: ${webpSupported}, AVIF: ${avifSupported}`);
  });
  
  // Добавляем IntersectionObserver для ленивой загрузки изображений
  if ('IntersectionObserver' in window) {
    const lazyImageObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const lazyImage = entry.target as HTMLImageElement;
          
          // Если есть data-src, загружаем изображение
          if (lazyImage.dataset.src) {
            getOptimizedImageUrl(lazyImage.dataset.src).then(optimizedUrl => {
              lazyImage.src = optimizedUrl;
              delete lazyImage.dataset.src;
            });
          }
          
          lazyImageObserver.unobserve(lazyImage);
        }
      });
    });
    
    // Наблюдаем за всеми изображениями с атрибутом data-src
    document.querySelectorAll('img[data-src]').forEach(img => {
      lazyImageObserver.observe(img);
    });
  }
}

export default {
  checkWebpSupport,
  checkAvifSupport,
  getOptimalImageFormat,
  getOptimizedImageUrl,
  createOptimizedImage,
  initImageOptimization
} 