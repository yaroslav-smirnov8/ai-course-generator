import { apiClient } from '@/api'
import { API_ENDPOINTS } from '@/api'
import { useMainStore } from '@/store'
import { ContentType } from '@/core/constants'

export interface LessonPlanDetailRequest {
  content: string           // Содержимое плана урока
  content_type: string      // Тип детализации (например, teacher_script, homework, exercises, game)
  language: string          // Язык плана урока
  lesson_focus: string      // Тема урока
  age_group?: string        // Возрастная группа
  methodology?: string      // Методология
  is_individual?: boolean   // Индивидуальное или групповое занятие
  is_online?: boolean       // Онлайн или офлайн занятие
  duration?: number         // Продолжительность урока в минутах
  level?: string            // Уровень владения языком
  action?: string           // Текст инструкции для генератора
  instruction_language?: string // Язык инструкции
}

/**
 * Извлекает параметры урока из текста плана урока
 * @param planContent - содержимое плана урока
 * @returns объект с извлеченными параметрами
 */
export function extractParamsFromPlan(planContent: string): {
  language?: string;
  topic?: string;
  age?: string;
  methodology?: string;
  individual_group?: string;
  online_offline?: string;
  duration?: number;
  level?: string;
} {
  const result: any = {};

  // Проверяем, что planContent существует и является строкой
  if (!planContent || typeof planContent !== 'string') {
    console.log('Пустой или некорректный план урока для анализа');
    return result;
  }

  console.log('Извлечение параметров из плана урока...');

  // Язык
  const languageMatch = planContent.match(/(?:Language|Язык|Langue|Idioma):\s*([^\n]+)/i);
  if (languageMatch && languageMatch[1]) {
    result.language = languageMatch[1].trim();
    console.log(`Извлечен язык: ${result.language}`);
  }

  // Тема
  // Сначала ищем в заголовке
  const titleMatch = planContent.match(/(?:Lesson Plan|План урока|План занятия|Plan de cours|Plan de clase):\s*([^\n]+)/i);
  if (titleMatch && titleMatch[1]) {
    result.topic = titleMatch[1].trim();
    console.log(`Извлечена тема из заголовка: ${result.topic}`);
  }
  // Альтернативный поиск темы
  const topicMatch = planContent.match(/(?:Topic|Тема|Thème|Tema|Focus):\s*([^\n]+)/i);
  if (topicMatch && topicMatch[1]) {
    result.topic = topicMatch[1].trim();
    console.log(`Извлечена тема из явного указания: ${result.topic}`);
  }

  // Возрастная группа
  const ageMatch = planContent.match(/(?:Age|Age Group|Возраст|Âge|Edad):\s*([^\n]+)/i);
  if (ageMatch && ageMatch[1]) {
    result.age = ageMatch[1].trim();
    console.log(`Извлечена возрастная группа: ${result.age}`);
  }

  // Методология
  const methodologyMatch = planContent.match(/(?:Methodology|Методология|Méthodologie|Metodología):\s*([^\n]+)/i);
  if (methodologyMatch && methodologyMatch[1]) {
    result.methodology = methodologyMatch[1].trim();
    console.log(`Извлечена методология: ${result.methodology}`);
  }

  // Тип занятия: индивидуальный или групповой
  const typeMatch = planContent.match(/(?:Type|Тип|Format|Формат|Formato):\s*([^\n]+)/i);
  if (typeMatch && typeMatch[1]) {
    const typeText = typeMatch[1].toLowerCase();

    if (typeText.includes('individual') || typeText.includes('индивидуал') ||
        typeText.includes('one-to-one') || typeText.includes('one on one') ||
        typeText.includes('1-1') || typeText.includes('1:1')) {
      result.individual_group = 'individual';
      console.log('Определен индивидуальный тип занятия');
    } else if (typeText.includes('group') || typeText.includes('групп') ||
               typeText.includes('class') || typeText.includes('класс') ||
               typeText.includes('multiple') || typeText.includes('много')) {
      result.individual_group = 'group';
      console.log('Определен групповой тип занятия');
    }
  }

  // Формат: онлайн или оффлайн
  const formatMatch = planContent.match(/(?:Format|Формат|Formato):\s*([^\n]+)/i);
  if (formatMatch && formatMatch[1]) {
    const formatText = formatMatch[1].toLowerCase();

    if (formatText.includes('online') || formatText.includes('онлайн') ||
        formatText.includes('virtual') || formatText.includes('виртуал') ||
        formatText.includes('remote') || formatText.includes('дистанц')) {
      result.online_offline = 'online';
      console.log('Определен онлайн формат занятия');
    } else if (formatText.includes('offline') || formatText.includes('оффлайн') ||
               formatText.includes('in-person') || formatText.includes('в классе') ||
               formatText.includes('classroom') || formatText.includes('face-to-face')) {
      result.online_offline = 'offline';
      console.log('Определен оффлайн формат занятия');
    }
  }

  // Продолжительность
  const durationMatch = planContent.match(/(?:Duration|Продолжительность|Durée|Duración):\s*(\d+)/i);
  if (durationMatch && durationMatch[1]) {
    result.duration = parseInt(durationMatch[1]);
    console.log(`Извлечена продолжительность: ${result.duration} минут`);
  }

  // Уровень
  const levelMatch = planContent.match(/(?:Level|Уровень|Niveau|Nivel):\s*([^\n]+)/i);
  if (levelMatch && levelMatch[1]) {
    result.level = levelMatch[1].trim();
    console.log(`Извлечен уровень: ${result.level}`);
  }

  return result;
}

/**
 * Объединяет параметры из формы с параметрами, извлеченными из плана урока
 * @param formData - данные из формы
 * @param planContent - содержимое плана урока
 * @returns объединенные параметры с учетом приоритетов
 */
export function mergeAndValidateParams(formData: any, planContent: string): any {
  console.log('mergeAndValidateParams - входные данные formData:', formData);

  // Извлекаем параметры из плана
  const extractedParams = extractParamsFromPlan(planContent);

  // Дефолтные значения
  const defaults = {
    language: 'English',
    age: 'teens',
    methodology: '',
    individual_group: 'individual',
    online_offline: 'online',
    duration: 60,
    level: 'intermediate'
  };

  // Объединяем параметры с приоритетом:
  // 1. Данные из формы (если они есть)
  // 2. Данные, извлеченные из плана
  // 3. Дефолтные значения
  const mergedParams: any = { ...defaults };

  // Предварительная проверка для вывода информации о формате занятия
  console.log(`Информация о формате занятия в плане: индивидуальное/групповое = ${extractedParams.individual_group || 'не указано'}`);

  // Применяем параметры в порядке приоритета (дефолтные -> извлеченные -> форма)
  for (const key of Object.keys(defaults)) {
    // Сначала проверяем, есть ли параметр в извлеченных данных
    if (extractedParams[key as keyof typeof extractedParams]) {
      mergedParams[key] = extractedParams[key as keyof typeof extractedParams];
      console.log(`Параметр ${key} взят из плана урока:`, extractedParams[key as keyof typeof extractedParams]);
    }

    // Затем проверяем, есть ли параметр в форме (перезаписываем, если есть)
    if (formData[key] !== undefined && formData[key] !== null && formData[key] !== '') {
      // Специальная обработка для методики - если это массив, преобразуем в строку
      if (key === 'methodology' && Array.isArray(formData[key])) {
        mergedParams[key] = formData[key].join(',');
        console.log(`Параметр ${key} (массив) взят из формы и преобразован в строку:`, mergedParams[key]);
      } else {
        mergedParams[key] = formData[key];
        console.log(`Параметр ${key} взят из формы:`, formData[key]);
      }
    }
  }

  // Дополнительно обрабатываем поля, которые могут отсутствовать в defaults
  const additionalFields = ['previous_lesson', 'grammar', 'vocabulary', 'exam'];
  for (const field of additionalFields) {
    if (formData[field] !== undefined && formData[field] !== null && formData[field] !== '') {
      mergedParams[field] = formData[field];
      console.log(`Дополнительный параметр ${field} взят из формы:`, formData[field]);
    }
  }

  // Отдельно обрабатываем тему, так как она не имеет дефолтного значения
  if (formData.topic && formData.topic !== '') {
    mergedParams.topic = formData.topic;
    console.log('Using topic from form data:', formData.topic);
  } else if (extractedParams.topic) {
    mergedParams.topic = extractedParams.topic;
    console.log('Using topic extracted from plan:', extractedParams.topic);
  } else {
    // Если тема не найдена ни в форме, ни в плане, создаем описательное сообщение
    mergedParams.topic = 'Lesson plan without specific topic';
    console.warn('No topic found in form data or plan content, using default');
  }

  console.log('Объединенные и проверенные параметры:', mergedParams);
  return mergedParams;
}

export class LessonPlanDetailService {
  async detailLessonPlanScript(planContent: string, formData: any, skipLimits: boolean = false): Promise<string> {
    try {
      console.log('Preparing to generate teacher script for lesson plan')

      // Получаем store только при вызове метода
      const store = useMainStore()

      // Проверяем лимиты генерации перед отправкой запроса, если не указано пропустить проверку
      if (!skipLimits) {
        const canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN)
        if (!canGenerate) {
          throw new Error('Достигнут дневной лимит генераций')
        }
      }

      // Получаем объединенные и проверенные параметры
      const validatedParams = mergeAndValidateParams(formData, planContent);

      // Создаем данные для промпта в формате JSON
      const promptData = {
        content: planContent,
        content_type: 'teacher_script',
        language: validatedParams.language,
        age_group: validatedParams.age,
        methodology: Array.isArray(validatedParams.methodology) ? validatedParams.methodology.join(',') : (validatedParams.methodology || ''),
        is_individual: validatedParams.individual_group === 'individual',
        is_online: validatedParams.online_offline === 'online',
        lesson_focus: validatedParams.topic,
        duration: validatedParams.duration || 60,
        level: validatedParams.level,
        // Явное указание формата занятия в инструкции
        action: `ВАЖНО: Это запрос на создание скрипта учителя для плана урока на тему "${validatedParams.topic}" на ${validatedParams.language} языке.

        НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА ИЛИ ЕГО ПЕРЕСКАЗ.
        НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${validatedParams.topic}".

        ЗАДАЧА:
        Создай подробный скрипт учителя с точными фразами и инструкциями для проведения ИМЕННО ЭТОГО урока.
        Скрипт должен включать:
        1. Фактические слова, которые учитель говорит на каждом этапе
        2. Четкие инструкции к заданиям для учеников
        3. Вопросы для проверки понимания и вовлечения учеников
        4. Переходы между этапами урока
        5. Комментарии о взаимодействии с учениками

        ОБРАТИ ВНИМАНИЕ: Это ${validatedParams.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${validatedParams.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
        Адаптируй скрипт именно под ${validatedParams.individual_group === 'individual' ? 'работу с одним учеником' : 'работу с группой учеников'}.

        ВАЖНО: Скрипт должен быть на ${validatedParams.language} языке и содержать конкретные фразы и формулировки, которые учитель использует в классе.
        Тема урока: ${validatedParams.topic} - СТРОГО ПРИДЕРЖИВАЙСЯ ЭТОЙ ТЕМЫ.

        ФОРМАТ ОТВЕТА:
        Предоставь готовый скрипт учителя, не спрашивая дополнительной информации.
        Не начинай ответ с фраз типа "Вот скрипт учителя для урока".
        Просто предоставь содержательный скрипт.`,
        instruction_language: validatedParams.language
      }

      // Создаем запрос в формате, ожидаемом API
      const requestData = {
        user_id: store.user?.id,
        type: ContentType.LESSON_PLAN,
        prompt: JSON.stringify(promptData),
        with_points: skipLimits // Если skipLimits=true, значит это генерация за баллы
      }

      console.log('Отправка запроса на создание скрипта учителя:', requestData)

      // Отправляем запрос
      const response = await apiClient.post(API_ENDPOINTS.DETAIL_LESSON_PLAN, requestData)

      console.log('Получен ответ от сервера:', response)

      // Обработка ответа с подробным логированием
      if (response) {
        if (response.data && response.data.content) {
          console.log('Скрипт учителя успешно создан')
          return response.data.content
        }
        else if (response.content) {
          return response.content
        }
        else if (typeof response === 'string') {
          return response
        }
        else {
          console.error('Неожиданная структура ответа:', response)
          throw new Error('Неверный формат ответа от сервера')
        }
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error('Error in lesson plan script generation:', error)
      throw error
    }
  }

  async detailLessonPlanHomework(planContent: string, formData: any, skipLimits: boolean = false): Promise<string> {
    try {
      console.log('Preparing to generate homework for lesson plan')

      const store = useMainStore()

      // Проверяем лимиты генерации перед отправкой запроса, если не указано пропустить проверку
      if (!skipLimits) {
        const canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN)
        if (!canGenerate) {
          throw new Error('Достигнут дневной лимит генераций')
        }
      }

      // Получаем объединенные и проверенные параметры
      const validatedParams = mergeAndValidateParams(formData, planContent);

      // Создаем данные для промпта в формате JSON
      const promptData = {
        content: planContent,
        content_type: 'homework',
        language: validatedParams.language,
        age_group: validatedParams.age,
        methodology: Array.isArray(validatedParams.methodology) ? validatedParams.methodology.join(',') : (validatedParams.methodology || ''),
        is_individual: validatedParams.individual_group === 'individual',
        is_online: validatedParams.online_offline === 'online',
        lesson_focus: validatedParams.topic,
        duration: validatedParams.duration || 60,
        level: validatedParams.level,
        // Явное указание запроса на создание домашнего задания, сохраняющего тему исходного плана урока
        action: `ВАЖНО: Это запрос на создание домашнего задания для плана урока на тему "${validatedParams.topic}" на ${validatedParams.language} языке.

        НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
        НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${validatedParams.topic}".

        ЗАДАЧА:
        Создай подробное и детальное домашнее задание для исходного плана урока.
        Задание должно соответствовать теме, целям и содержанию плана.
        Включи конкретные инструкции, вопросы, упражнения или задачи.

        ОБРАТИ ВНИМАНИЕ: Это ${validatedParams.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${validatedParams.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
        Адаптируй домашнее задание именно для ${validatedParams.individual_group === 'individual' ? 'одного ученика' : 'группы учеников'}.

        Учитывай указанные уровень учеников и тип занятия из исходного плана.
        ВАЖНО: Задание должно быть на ${validatedParams.language} языке.
        Тема урока: ${validatedParams.topic} - СТРОГО ПРИДЕРЖИВАЙСЯ ЭТОЙ ТЕМЫ.

        ФОРМАТ ОТВЕТА:
        Предоставь готовое домашнее задание, не спрашивая дополнительной информации.
        Не начинай ответ с фраз типа "Вот домашнее задание для урока".
        Просто предоставь содержательное домашнее задание.`,
        instruction_language: validatedParams.language
      }

      // Создаем запрос в формате, ожидаемом API
      const requestData = {
        user_id: store.user?.id,
        type: ContentType.LESSON_PLAN,
        prompt: JSON.stringify(promptData),
        with_points: skipLimits // Если skipLimits=true, значит это генерация за баллы
      }

      console.log('Отправка запроса на создание домашнего задания:', requestData)

      // Отправляем запрос
      const response = await apiClient.post(API_ENDPOINTS.DETAIL_LESSON_PLAN, requestData)

      console.log('Получен ответ от сервера:', response)

      // Обработка ответа
      if (response) {
        if (response.data && response.data.content) {
          console.log('Домашнее задание успешно создано')
          return response.data.content
        }
        else if (response.content) {
          return response.content
        }
        else if (typeof response === 'string') {
          return response
        }
        else {
          console.error('Неожиданная структура ответа:', response)
          throw new Error('Неверный формат ответа от сервера')
        }
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error('Error in lesson plan homework generation:', error)
      throw error
    }
  }

  async detailLessonPlanExercises(planContent: string, formData: any, skipLimits: boolean = false): Promise<string> {
    try {
      console.log('Preparing to generate exercises for lesson plan')

      const store = useMainStore()

      // Проверяем лимиты генерации перед отправкой запроса, если не указано пропустить проверку
      if (!skipLimits) {
        const canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN)
        if (!canGenerate) {
          throw new Error('Достигнут дневной лимит генераций')
        }
      }

      // Получаем объединенные и проверенные параметры
      const validatedParams = mergeAndValidateParams(formData, planContent);

      // Создаем данные для промпта в формате JSON
      const promptData = {
        content: planContent,
        content_type: 'exercises',
        language: validatedParams.language,
        age_group: validatedParams.age,
        methodology: Array.isArray(validatedParams.methodology) ? validatedParams.methodology.join(',') : (validatedParams.methodology || ''),
        is_individual: validatedParams.individual_group === 'individual',
        is_online: validatedParams.online_offline === 'online',
        lesson_focus: validatedParams.topic,
        duration: validatedParams.duration || 60,
        level: validatedParams.level,
        // Явное указание запроса на создание упражнений, сохраняющих тему исходного плана урока
        action: `ВАЖНО: Это запрос на создание дополнительных упражнений для плана урока на тему "${validatedParams.topic}" на ${validatedParams.language} языке.

        НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
        НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${validatedParams.topic}".

        ЗАДАЧА:
        Создай набор конкретных упражнений для приведенного плана урока.
        Упражнения должны:
        1. Соответствовать теме урока "${validatedParams.topic}", целям и уровню учеников из исходного плана
        2. Быть подробно описаны с инструкциями по выполнению
        3. Включать различные типы заданий (письменные, устные, интерактивные)
        4. Быть готовыми к использованию без дополнительной подготовки
        5. Учитывать формат проведения урока (${validatedParams.online_offline === 'online' ? 'онлайн' : 'оффлайн'}, ${validatedParams.individual_group === 'individual' ? 'индивидуальный' : 'групповой'})

        ОБРАТИ ВНИМАНИЕ: Это ${validatedParams.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${validatedParams.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
        Адаптируй упражнения именно для ${validatedParams.individual_group === 'individual' ? 'работы с одним учеником' : 'работы с группой учеников'}.

        ВАЖНО: Упражнения должны быть на ${validatedParams.language} языке и строго соответствовать теме "${validatedParams.topic}".

        ФОРМАТ ОТВЕТА:
        Предоставь готовый набор упражнений, не спрашивая дополнительной информации.
        Не начинай ответ с фраз типа "Вот упражнения для урока".
        Просто предоставь содержательные упражнения.`,
        instruction_language: validatedParams.language
      }

      // Создаем запрос в формате, ожидаемом API
      const requestData = {
        user_id: store.user?.id,
        type: ContentType.LESSON_PLAN,
        prompt: JSON.stringify(promptData),
        with_points: skipLimits // Если skipLimits=true, значит это генерация за баллы
      }

      console.log('Отправка запроса на создание упражнений:', requestData)

      // Отправляем запрос
      const response = await apiClient.post(API_ENDPOINTS.DETAIL_LESSON_PLAN, requestData)

      console.log('Получен ответ от сервера:', response)

      // Обработка ответа
      if (response) {
        if (response.data && response.data.content) {
          console.log('Упражнения успешно созданы')
          return response.data.content
        }
        else if (response.content) {
          return response.content
        }
        else if (typeof response === 'string') {
          return response
        }
        else {
          console.error('Неожиданная структура ответа:', response)
          throw new Error('Неверный формат ответа от сервера')
        }
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error('Error in lesson plan exercises generation:', error)
      throw error
    }
  }

  async detailLessonPlanGame(planContent: string, formData: any, skipLimits: boolean = false): Promise<string> {
    try {
      console.log('Preparing to generate game for lesson plan')

      const store = useMainStore()

      // Проверяем лимиты генерации перед отправкой запроса, если не указано пропустить проверку
      if (!skipLimits) {
        const canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN)
        if (!canGenerate) {
          throw new Error('Достигнут дневной лимит генераций')
        }
      }

      // Получаем объединенные и проверенные параметры
      const validatedParams = mergeAndValidateParams(formData, planContent);

      // Создаем данные для промпта в формате JSON
      const promptData = {
        content: planContent,
        content_type: 'game',
        language: validatedParams.language,
        age_group: validatedParams.age,
        methodology: Array.isArray(validatedParams.methodology) ? validatedParams.methodology.join(',') : (validatedParams.methodology || ''),
        is_individual: validatedParams.individual_group === 'individual',
        is_online: validatedParams.online_offline === 'online',
        lesson_focus: validatedParams.topic,
        duration: validatedParams.duration || 60,
        level: validatedParams.level,
        // Явное указание запроса на создание игры, сохраняющей тему исходного плана урока
        action: `ВАЖНО: Это запрос на создание игровой активности для плана урока на тему "${validatedParams.topic}" на ${validatedParams.language} языке.

        НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
        НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${validatedParams.topic}".

        ЗАДАЧА:
        Создай детальное описание игры или интерактивной активности, которую можно использовать в рамках данного урока.
        Описание должно включать:
        1. Название игры
        2. Необходимые материалы
        3. Подробные правила
        4. Пошаговые инструкции для учителя
        5. Примерную продолжительность
        6. Варианты адаптации (для разных уровней/возрастов)

        ОБРАТИ ВНИМАНИЕ: Это ${validatedParams.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${validatedParams.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
        Создай игру именно для ${validatedParams.individual_group === 'individual' ? 'одного ученика' : 'группы учеников'},
        которая подходит для ${validatedParams.online_offline === 'online' ? 'онлайн' : 'оффлайн'} формата.

        ВАЖНО: Описание игры должно быть на ${validatedParams.language} языке и строго соответствовать теме "${validatedParams.topic}".

        ФОРМАТ ОТВЕТА:
        Предоставь готовое описание игры, не спрашивая дополнительной информации.
        Не начинай ответ с фраз типа "Вот игра для урока".
        Просто предоставь содержательное описание игры.`,
        instruction_language: validatedParams.language
      }

      // Создаем запрос в формате, ожидаемом API
      const requestData = {
        user_id: store.user?.id,
        type: ContentType.LESSON_PLAN,
        prompt: JSON.stringify(promptData),
        with_points: skipLimits // Если skipLimits=true, значит это генерация за баллы
      }

      console.log('Отправка запроса на создание игры:', requestData)

      // Отправляем запрос
      const response = await apiClient.post(API_ENDPOINTS.DETAIL_LESSON_PLAN, requestData)

      console.log('Получен ответ от сервера:', response)

      // Обработка ответа
      if (response) {
        if (response.data && response.data.content) {
          console.log('Игра успешно создана')
          return response.data.content
        }
        else if (response.content) {
          return response.content
        }
        else if (typeof response === 'string') {
          return response
        }
        else {
          console.error('Неожиданная структура ответа:', response)
          throw new Error('Неверный формат ответа от сервера')
        }
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error('Error in lesson plan game generation:', error)
      throw error
    }
  }

  async detailLessonPlanPoint(planContent: string, formData: any, pointNumber: number, skipLimits: boolean = false): Promise<string> {
    try {
      console.log(`Preparing to detail point ${pointNumber} of lesson plan`)
      console.log('Form data for detailLessonPlanPoint:', formData);
      console.log('Plan content exists:', !!planContent);

      const store = useMainStore()

      // Проверяем лимиты генерации перед отправкой запроса, если не указано пропустить проверку
      if (!skipLimits) {
        const canGenerate = await store.checkAndTrackGeneration(ContentType.LESSON_PLAN)
        if (!canGenerate) {
          throw new Error('Достигнут дневной лимит генераций')
        }
      }

      // Проверяем наличие темы урока
      if (!formData.topic || formData.topic.trim() === '') {
        console.error('Ошибка: тема урока не указана в формате запроса');
        throw new Error('Тема урока обязательна для детализации плана');
      }

      console.log('Topic for lesson plan detailing:', formData.topic);

      // Получаем объединенные и проверенные параметры
      const validatedParams = mergeAndValidateParams(formData, planContent);

      // Улучшенный алгоритм извлечения пункта плана
      // Ищем пункт по различным паттернам, которые могут встречаться в плане урока
      const patterns = [
        // Формат "5. Заголовок"
        new RegExp(`${pointNumber}\\.(\\s+)?([^\\n]+)(\\n|$)`, 'i'),
        // Формат "5) Заголовок"
        new RegExp(`${pointNumber}\\)(\\s+)?([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Пункт 5: Заголовок"
        new RegExp(`[Пп]ункт\\s+${pointNumber}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Stage 5: Заголовок"
        new RegExp(`[Ss]tage\\s+${pointNumber}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "Activity 5: Заголовок"
        new RegExp(`[Aa]ctivity\\s+${pointNumber}[:\\s]+([^\\n]+)(\\n|$)`, 'i'),
        // Формат "5. Заголовок" и следующие за ним строки до следующего пункта
        new RegExp(`${pointNumber}\\.(\\s+)?([^\\n]+)(\\n(?!\\d+\\.)[^\\n]+)*`, 'i')
      ];

      // Ищем содержимое пункта
      let pointContent = '';
      let pointTitle = '';

      for (const pattern of patterns) {
        const match = planContent.match(pattern);
        if (match && match[0]) {
          pointContent = match[0].trim();
          // Извлекаем заголовок пункта (первая строка)
          const titleMatch = pointContent.split('\n')[0].trim();
          if (titleMatch) {
            pointTitle = titleMatch;
            break;
          }
        }
      }

      // Если не нашли пункт по паттернам, попробуем найти по номеру раздела
      if (!pointContent) {
        // Разбиваем план на разделы
        const sections = planContent.split(/\n\s*\n/);

        // Ищем раздел, который может соответствовать нужному пункту
        if (sections.length >= pointNumber && pointNumber > 0) {
          // Берем раздел с индексом (pointNumber - 1), так как массивы начинаются с 0
          pointContent = sections[pointNumber - 1].trim();
          pointTitle = pointContent.split('\n')[0].trim();
        }
      }

      // Если все еще не нашли, используем общий подход - ищем по номеру в начале строки
      if (!pointContent) {
        const lines = planContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].trim().startsWith(`${pointNumber}.`) ||
              lines[i].trim().startsWith(`${pointNumber})`) ||
              lines[i].trim().match(new RegExp(`^\\s*${pointNumber}[.:\\s)]`))) {
            pointTitle = lines[i].trim();

            // Собираем содержимое пункта до следующего пункта или пустой строки
            let j = i + 1;
            pointContent = pointTitle;

            while (j < lines.length) {
              const nextLine = lines[j].trim();
              // Останавливаемся, если нашли следующий пункт или пустую строку
              if (nextLine === '' || /^\d+[.:]/.test(nextLine)) {
                break;
              }
              pointContent += '\n' + lines[j];
              j++;
            }
            break;
          }
        }
      }

      console.log(`Извлеченный пункт ${pointNumber}:`, pointContent || 'Не найден');

      // Создаем данные для промпта в формате JSON
      const promptData = {
        content: planContent,
        content_type: `point_${pointNumber}`,
        language: validatedParams.language,
        age_group: validatedParams.age,
        methodology: Array.isArray(validatedParams.methodology) ? validatedParams.methodology.join(',') : (validatedParams.methodology || ''),
        is_individual: validatedParams.individual_group === 'individual',
        is_online: validatedParams.online_offline === 'online',
        lesson_focus: validatedParams.topic,
        duration: validatedParams.duration || 60,
        level: validatedParams.level,
        // Явное указание запроса на детализацию пункта, сохраняющего тему исходного плана урока
        action: `ВАЖНО: Это запрос на детализацию пункта ${pointNumber} плана урока на тему "${validatedParams.topic}" на ${validatedParams.language} языке.

        НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
        НЕ МЕНЯЙ ТЕМУ УРОКА - сохрани оригинальную тему: "${validatedParams.topic}".

        ИСХОДНЫЙ ПУНКТ ПЛАНА:
        ${pointContent || `Пункт ${pointNumber} (не найден явно в плане урока)`}

        ЗАДАЧА:
        Детализируй пункт ${pointNumber} исходного плана урока, предоставив подробное описание, включающее:
        1. Конкретные инструкции по проведению данного этапа урока
        2. Примеры и методические рекомендации для учителя
        3. Возможные сложности и способы их преодоления
        4. Конкретные вопросы, задания и упражнения (если применимо)

        ОБРАТИ ВНИМАНИЕ: Это ${validatedParams.individual_group === 'individual' ? 'ИНДИВИДУАЛЬНОЕ' : 'ГРУППОВОЕ'} занятие в формате ${validatedParams.online_offline === 'online' ? 'ОНЛАЙН' : 'ОФФЛАЙН'}.
        Адаптируй инструкции именно для ${validatedParams.individual_group === 'individual' ? 'работы с одним учеником' : 'работы с группой учеников'}.

        ВАЖНО: Детализация должна быть на ${validatedParams.language} языке и строго соответствовать теме "${validatedParams.topic}".

        ФОРМАТ ОТВЕТА:
        Предоставь детальное описание пункта ${pointNumber}, не спрашивая дополнительной информации.
        Не начинай ответ с фраз типа "Вот детализация пункта ${pointNumber}".
        Просто предоставь содержательную детализацию.`,
        instruction_language: validatedParams.language,
        original_point: pointContent || `Пункт ${pointNumber}`
      }

      // Создаем запрос в формате, ожидаемом API
      const requestData = {
        user_id: store.user?.id,
        type: ContentType.LESSON_PLAN,
        prompt: JSON.stringify(promptData),
        with_points: skipLimits // Если skipLimits=true, значит это генерация за баллы
      }

      console.log(`Отправка запроса на детализацию пункта ${pointNumber}:`, requestData)

      // Отправляем запрос
      const response = await apiClient.post(API_ENDPOINTS.DETAIL_LESSON_PLAN, requestData)

      console.log('Получен ответ от сервера:', response)

      // Обработка ответа
      if (response) {
        if (response.data && response.data.content) {
          console.log(`Пункт ${pointNumber} успешно детализирован`)
          return response.data.content
        }
        else if (response.content) {
          return response.content
        }
        else if (typeof response === 'string') {
          return response
        }
        else {
          console.error('Неожиданная структура ответа:', response)
          throw new Error('Неверный формат ответа от сервера')
        }
      }

      throw new Error('Сервер вернул пустой ответ')
    } catch (error) {
      console.error(`Error in lesson plan point ${pointNumber} detailing:`, error)
      throw error
    }
  }

  // Методы для генерации за баллы
  async detailLessonPlanPointWithPoints(planContent: string, formData: any, pointNumber: number): Promise<string> {
    try {
      console.log(`Preparing to detail point ${pointNumber} of lesson plan using points`)
      console.log('Form data received:', formData);
      console.log('Plan content received:', planContent ? 'Plan content exists' : 'No plan content');

      const store = useMainStore()
      const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN)
      if (!canGenerate) {
        throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.')
      }

      // Проверяем наличие темы урока
      if (!formData.topic || formData.topic.trim() === '') {
        console.error('Ошибка: тема урока не указана в формате запроса');
        throw new Error('Тема урока обязательна для детализации плана');
      }

      console.log('Topic for lesson plan detailing:', formData.topic);

      // Добавляем флаг skip_points_check в formData
      const updatedFormData = {
        ...formData,
        skip_points_check: true // Указываем, что баллы уже были списаны
      };

      // Используем тот же метод, что и для обычной генерации, но с другой проверкой лимитов
      return await this.detailLessonPlanPoint(planContent, updatedFormData, pointNumber, true)
    } catch (error) {
      console.error(`Error in lesson plan point ${pointNumber} detailing with points:`, error)
      throw error
    }
  }

  async detailLessonPlanScriptWithPoints(planContent: string, formData: any): Promise<string> {
    try {
      console.log('Preparing to generate teacher script for lesson plan using points')

      const store = useMainStore()
      const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN)
      if (!canGenerate) {
        throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.')
      }

      // Добавляем флаг skip_points_check в formData
      const updatedFormData = {
        ...formData,
        skip_points_check: true // Указываем, что баллы уже были списаны
      };

      // Используем тот же метод, что и для обычной генерации
      return await this.detailLessonPlanScript(planContent, updatedFormData, true)
    } catch (error) {
      console.error('Error in lesson plan script generation with points:', error)
      throw error
    }
  }

  async detailLessonPlanHomeworkWithPoints(planContent: string, formData: any): Promise<string> {
    try {
      console.log('Preparing to generate homework for lesson plan using points')

      const store = useMainStore()
      const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN)
      if (!canGenerate) {
        throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.')
      }

      // Добавляем флаг skip_points_check в formData
      const updatedFormData = {
        ...formData,
        skip_points_check: true // Указываем, что баллы уже были списаны
      };

      // Используем тот же метод, что и для обычной генерации
      return await this.detailLessonPlanHomework(planContent, updatedFormData, true)
    } catch (error) {
      console.error('Error in lesson plan homework generation with points:', error)
      throw error
    }
  }

  async detailLessonPlanExercisesWithPoints(planContent: string, formData: any): Promise<string> {
    try {
      console.log('Preparing to generate exercises for lesson plan using points')

      const store = useMainStore()
      const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN)
      if (!canGenerate) {
        throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.')
      }

      // Добавляем флаг skip_points_check в formData
      const updatedFormData = {
        ...formData,
        skip_points_check: true // Указываем, что баллы уже были списаны
      };

      // Используем тот же метод, что и для обычной генерации
      return await this.detailLessonPlanExercises(planContent, updatedFormData, true)
    } catch (error) {
      console.error('Error in lesson plan exercises generation with points:', error)
      throw error
    }
  }

  async detailLessonPlanGameWithPoints(planContent: string, formData: any): Promise<string> {
    try {
      console.log('Preparing to generate game for lesson plan using points')

      const store = useMainStore()
      const canGenerate = await store.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN)
      if (!canGenerate) {
        throw new Error('Недостаточно баллов для генерации. Требуется 8 баллов.')
      }

      // Добавляем флаг skip_points_check в formData
      const updatedFormData = {
        ...formData,
        skip_points_check: true // Указываем, что баллы уже были списаны
      };

      // Используем тот же метод, что и для обычной генерации
      return await this.detailLessonPlanGame(planContent, updatedFormData, true)
    } catch (error) {
      console.error('Error in lesson plan game generation with points:', error)
      throw error
    }
  }
}

export const lessonPlanDetailService = new LessonPlanDetailService()