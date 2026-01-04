/**
 * Сервис для предзагрузки изображений и других ресурсов
 */

// Импортируем основные изображения
import backgroundImage from '@/assets/images/home/black_sky_pinkish_space_milky_way_background_gf9zyhoy9vn0sm4hqt4l.svg'
import planetBg from '@/assets/images/lesson_plan/plan-backgroud-image.svg'
import homeBackground from '@/assets/images/home/home-backgroud-image.svg'

// Список изображений для предзагрузки
const criticalImages = [
  backgroundImage,
  planetBg,
  homeBackground
]

// Список некритичных изображений, которые можно загрузить после основного контента
const nonCriticalImages: string[] = [
  // Здесь можно добавить пути к другим изображениям
]

/**
 * Предзагрузка одного изображения
 * @param src Путь к изображению
 * @returns Promise, который разрешается, когда изображение загружено
 */
const preloadImage = (src: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = () => {
      console.warn(`Failed to preload image: ${src}`)
      resolve() // Разрешаем промис даже при ошибке, чтобы не блокировать загрузку других изображений
    }
    img.src = src
  })
}

/**
 * Предзагрузка критических изображений
 * @returns Promise, который разрешается, когда все критические изображения загружены
 */
export const preloadCriticalImages = async (): Promise<void> => {
  try {
    await Promise.all(criticalImages.map(preloadImage))
    console.log('Critical images preloaded successfully')
  } catch (error) {
    console.error('Error preloading critical images:', error)
  }
}

/**
 * Предзагрузка некритичных изображений
 * Вызывается после загрузки основного контента
 */
export const preloadNonCriticalImages = (): void => {
  // Используем requestIdleCallback для загрузки в фоновом режиме, когда браузер не занят
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(() => {
      nonCriticalImages.forEach(src => {
        const img = new Image()
        img.src = src
      })
      console.log('Non-critical images queued for preload')
    })
  } else {
    // Fallback для браузеров, которые не поддерживают requestIdleCallback
    setTimeout(() => {
      nonCriticalImages.forEach(src => {
        const img = new Image()
        img.src = src
      })
      console.log('Non-critical images queued for preload (setTimeout fallback)')
    }, 1000)
  }
}

/**
 * Инициализация предзагрузки всех изображений
 */
export const initPreload = (): void => {
  preloadCriticalImages()
  
  // Добавляем слушатель события загрузки страницы для загрузки некритичных изображений
  window.addEventListener('load', () => {
    preloadNonCriticalImages()
  })
}

export default {
  initPreload,
  preloadCriticalImages,
  preloadNonCriticalImages
} 