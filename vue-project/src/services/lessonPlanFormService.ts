import { apiClient } from '@/api'
import { API_ENDPOINTS } from '@/api'
import { useMainStore } from '@/store'
import { ContentType } from '@/core/constants'

export interface LessonPlanFormData {
  language: string
  topic: string
  level?: string
  age?: string
  previous_lesson?: string
  grammar?: string
  vocabulary?: string
  methodology?: string[]
  individual_group?: string
  online_offline?: string
  exam?: string
  duration?: number
}

export class LessonPlanFormService {
  async generateLessonPlan(formData: LessonPlanFormData): Promise<string> {
    try {
      console.log('Preparing to generate lesson plan with form data')

      // Получаем store только при вызове метода
      const store = useMainStore()

      // Проверяем лимиты генерации перед отправкой запроса
      const canGenerate = await store.checkAndTrackGenerationLessonPlanForm()
      if (!canGenerate) {
        throw new Error('Достигнут дневной лимит генераций плана урока')
      }

      console.log('Sending form data to backend:', JSON.stringify(formData, null, 2))

      // Создаем данные запроса на основе данных формы
      const requestData = {
        user_id: store.user?.id,
        ...formData,
        with_points: false // Явно указываем, что это обычная генерация
      }

      // Отправляем запрос на новый эндпоинт
      const response = await apiClient.post(API_ENDPOINTS.GENERATE_LESSON_PLAN_FORM, requestData)

      console.log('Received response from server:', JSON.stringify(response, null, 2))

      // Улучшенная обработка ответа с более подробным логированием
      if (response) {
        // Структура ответа должна быть: { status: "success", data: { content: "..." } }
        if (response.data && response.data.content) {
          console.log('Found content directly in response.data.content')
          return response.data.content
        }
        else if (response.data && typeof response.data === 'object') {
          // Просмотр всех возможных полей для диагностики
          console.log('Response data fields:', Object.keys(response.data))

          // Если ответ соответствует структуре ContentResponse с бэкенда
          // { status: "success", data: { id: number, content: string, ... } }
          if (response.data.content) {
            console.log('Found content field in response.data')
            return response.data.content
          }

          // В случае вложенной структуры
          if (response.data.data && typeof response.data.data === 'object') {
            console.log('Response data.data fields:', Object.keys(response.data.data))

            if (response.data.data.content) {
              console.log('Found content in response.data.data.content')
              return response.data.data.content
            }
          }
        }
        else if (typeof response === 'string') {
          console.log('Response is a string, returning directly')
          return response
        }

        // Если не нашли контент в ожидаемых местах, выводим структуру ответа
        console.error('Unable to locate content in response:', response)
        throw new Error(`Не удалось найти контент в ответе сервера. Структура ответа: ${JSON.stringify(response)}`)
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error('Error in lesson plan form generation:', error)
      throw error
    }
  }

  // Метод для генерации плана урока за баллы
  async generateLessonPlanWithPoints(formData: LessonPlanFormData, pointsCost: number = 8): Promise<string> {
    try {
      console.log('Preparing to generate lesson plan with points')

      // Получаем store только при вызове метода
      const store = useMainStore()

      // Проверяем возможность генерации за баллы
      const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN, pointsCost)
      if (!canGenerate) {
        throw new Error('Недостаточно баллов для генерации плана урока')
      }

      console.log('Sending form data to backend with points:', JSON.stringify(formData, null, 2))

      // Создаем данные запроса на основе данных формы
      const requestData = {
        user_id: store.user?.id,
        ...formData,
        with_points: true, // Указываем, что это генерация за баллы
        skip_tariff_check: true, // Пропускаем проверку тарифа
        skip_limits: true // Пропускаем проверку лимитов
      }

      // Отправляем запрос на эндпоинт
      const response = await apiClient.post(API_ENDPOINTS.GENERATE_LESSON_PLAN_FORM, requestData)

      console.log('Received response from server (points generation):', JSON.stringify(response, null, 2))

      // Улучшенная обработка ответа с более подробным логированием
      if (response) {
        // Структура ответа должна быть: { status: "success", data: { content: "..." } }
        if (response.data && response.data.content) {
          console.log('Found content directly in response.data.content')
          return response.data.content
        }
        else if (response.data && typeof response.data === 'object') {
          // Просмотр всех возможных полей для диагностики
          console.log('Response data fields:', Object.keys(response.data))

          // Если ответ соответствует структуре ContentResponse с бэкенда
          // { status: "success", data: { id: number, content: string, ... } }
          if (response.data.content) {
            console.log('Found content field in response.data')
            return response.data.content
          }

          // В случае вложенной структуры
          if (response.data.data && typeof response.data.data === 'object') {
            console.log('Response data.data fields:', Object.keys(response.data.data))

            if (response.data.data.content) {
              console.log('Found content in response.data.data.content')
              return response.data.data.content
            }
          }
        }
        else if (typeof response === 'string') {
          console.log('Response is a string, returning directly')
          return response
        }

        // Если не нашли контент в ожидаемых местах, выводим структуру ответа
        console.error('Unable to locate content in response:', response)
        throw new Error(`Не удалось найти контент в ответе сервера. Структура ответа: ${JSON.stringify(response)}`)
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error('Error in lesson plan form generation with points:', error)
      throw error
    }
  }
}

export const lessonPlanFormService = new LessonPlanFormService()