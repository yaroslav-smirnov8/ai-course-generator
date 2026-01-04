// src/services/courseGenerator.ts
import { apiClient } from '@/api/client';
import type { CourseFormData, CourseStructure, Lesson } from '../types/course';
import { useMainStore } from '@/store';
import { useCourseStore } from '@/store/course';
import { ContentType } from '@/core/constants';

// Добавляем новый интерфейс для расширенного ответа API
export interface ApiResponse<T> {
  data: T;
  metadata?: {
    recovery_status?: 'success' | 'partial' | 'failure' | 'none';
    recovered_fields?: string[];
    missing_fields?: string[];
    messages?: string[];
    recovery_time?: number;
  };
}

export class CourseGeneratorService {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = '/api/v1/course';
  }

  /**
   * Генерирует структуру курса на основе параметров
   */
  async generateCourseStructure(formData: CourseFormData): Promise<ApiResponse<CourseStructure | null>> { // <-- Изменяем тип здесь
    try {
      // Проверяем лимиты генераций
      const store = useMainStore();
      if (!await store.checkAndTrackGeneration(ContentType.COURSE)) {
        throw new Error('Достигнут дневной лимит генераций. Попробуйте завтра или обновите свой тариф.');
      }

      // Преобразуем данные формы в формат для API
      const apiRequestData = {
        name: formData.courseName,
        language: formData.language,
        level: formData.level,
        start_level: formData.startLevel,
        target_audience: formData.targetAudience,
        format: formData.format,
        exam_prep: formData.examPrep || '',
        description: `Курс изучения ${formData.language} языка для ${formData.targetAudience} ${formData.level} уровня`,

        // Добавляем дополнительные поля для нового функционала
        lessons_count: formData.lessonsCount,
        lesson_duration: formData.lessonDuration,
        main_topics: formData.mainTopics,
        grammar_focus: formData.grammarFocus,
        vocabulary_focus: formData.vocabularyFocus,

        // Навыки
        include_speaking: formData.includeSpeaking,
        include_listening: formData.includeListening,
        include_reading: formData.includeReading,
        include_writing: formData.includeWriting,
        include_games: formData.includeGames,

        // Методика и информация о студенте
        methodology: formData.methodology,
        student_age: formData.age || 'adults',
        student_interests: formData.interests || '',
        student_goals: formData.goals || '',
        common_mistakes: formData.commonMistakes || '',

        // Информация о подготовке к экзамену
        custom_exam: formData.customExam || '',
        exam_prep_lessons: formData.examPrepLessons || 0,

        // Пустые уроки, они будут сгенерированы на бэкенде
        lessons: []
      };

      // Добавляем подробное логирование для отладки
      const url = `/api/v1/course/courses/generate`;
      console.log(`Отправка запроса на URL: ${url}`);
      console.log('Данные запроса:', JSON.stringify(apiRequestData, null, 2));

      // Убрали логику с apiClient.defaults.baseURL

      // apiClient.post уже возвращает response.data
      const courseData = await apiClient.post<CourseStructure | null>(url, apiRequestData);
      // console.log('Получен ответ:', courseData); // Лог уже есть в ApiClient

      // Упрощенная обработка ответа: проверяем полученные данные курса
      if (courseData && typeof courseData === 'object' && courseData.id && Array.isArray(courseData.lessons)) {
        // Если ответ похож на структуру курса, возвращаем его
        return {
          data: courseData, // courseData уже имеет тип CourseStructure | null
          metadata: {
            recovery_status: 'none' // Предполагаем успешный ответ без восстановления
          }
        };
      } else {
        // Если формат неожиданный, логируем и возвращаем ошибку
        console.error('Неожиданный формат данных курса от API:', courseData);
        return {
          data: null, // Возвращаем null вместо данных
          metadata: {
            recovery_status: 'failure',
            messages: ['Получен неожиданный формат ответа от API']
          }
        };
      }
    } catch (error: any) {
      console.error('Error generating course structure:', error);
      // Добавляем подробное логирование ошибок
      // Добавляем подробное логирование ошибок
      if (error.response) {
        // Ошибка с ответом от сервера
        console.error('Ответ сервера:', error.response.status, error.response.data);
      } else if (error.request) {
        // Ошибка без ответа от сервера
        console.error('Запрос был отправлен, но ответ не получен', error.request);
      }
      throw error;
    }
  }

  /**
   * Генерирует отдельный план урока (старый метод, возможно, для другого контекста)
   */
  async generateLessonPlan(lessonData: Partial<Lesson>): Promise<Lesson> {
    console.warn("Вызван устаревший метод generateLessonPlan. Используйте generatePlanForCourseLesson для уроков курса.");
    try {
      // Предполагаем, что этот эндпоинт для генерации урока "с нуля"
      const response = await apiClient.post(`${this.baseUrl}/lessons/generate_standalone`, lessonData); // Изменен URL для ясности
      return response.data;
    } catch (error) {
      console.error('Error generating standalone lesson plan:', error);
      throw error;
    }
  }

  /**
   * Генерирует план для конкретного урока внутри существующего курса
   */
  async generatePlanForCourseLesson(lessonData: {
    id: number; // ID урока
    courseId: number; // ID курса для контекста
    title: string;
    level: string;
    duration: number;
    objectives: string[];
    grammar: string[];
    vocabulary: string[];
    // Можно добавить другие поля при необходимости
  }): Promise<any> { // Возвращаемый тип может быть Lesson или специфичный тип плана
    if (!lessonData.id) {
      throw new Error("Lesson ID is required to generate a plan for a course lesson.");
    }
    // Исправляем URL, добавляя префикс /course
    const url = `/api/v1/course/lessons/${lessonData.id}/generate_plan`;
    console.log(`Отправка запроса на генерацию плана урока: ${url}`);
    console.log('Данные для генерации плана:', lessonData);
    try {
      // Отправляем только необходимые данные для генерации плана
      const response = await apiClient.post(url, {
        course_id: lessonData.courseId,
        title: lessonData.title,
        level: lessonData.level,
        duration: lessonData.duration,
        objectives: lessonData.objectives,
        grammar: lessonData.grammar,
        vocabulary: lessonData.vocabulary
        // Добавьте другие поля, если бэкенд их ожидает
      });
      return response.data;
    } catch (error) {
      console.error('Error generating lesson plan:', error);
      throw error;
    }
  }

  /**
   * Генерирует материалы для урока (упражнения, игры и т.д.)
   */
  async generateLessonMaterials(lessonId: number, types: string[]): Promise<any> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/courses/lessons/${lessonId}/materials`, { types });
      return response.data;
    } catch (error) {
      console.error('Error generating lesson materials:', error);
      throw error;
    }
  }

  /**
   * Экспортирует курс в выбранном формате
   */
  async exportCourse(courseId: number, format: 'pdf' | 'docx'): Promise<Blob> {
    try {
      console.log(`Экспорт курса ${courseId} в формате ${format}`);

      // Используем правильный URL для экспорта курса
      const response = await apiClient.get(`${this.baseUrl}/courses/${courseId}/export`, {
        params: { format },
        responseType: 'blob'
      });

      // Проверяем, что получили ответ с данными
      if (response && response.data) {
        console.log(`Получен файл для экспорта курса ${courseId} в формате ${format}`);
        return response.data;
      }

      throw new Error('Не удалось получить данные для экспорта');
    } catch (error) {
      console.error('Error exporting course:', error);

      // Если произошла ошибка при экспорте, выводим сообщение пользователю
      alert(`Ошибка при экспорте курса: ${error.message || 'Неизвестная ошибка'}`);

      // Перебрасываем ошибку дальше
      throw error;
    }
  }

  /**
   * Сохраняет курс
   */
  async saveCourse(courseData: CourseStructure): Promise<CourseStructure> {
    try {
      // Очищаем объект курса от служебных полей
      const cleanedCourseData = this.cleanCourseDataForSaving(courseData);
      console.log('Cleaned course data for saving:', cleanedCourseData);

      // Проверяем, есть ли у курса ID
      const hasId = courseData.id !== undefined && courseData.id !== null;
      console.log(`Курс ${hasId ? 'имеет' : 'не имеет'} ID:`, hasId ? courseData.id : 'отсутствует');

      try {
        let response;

        // Если у курса есть ID, используем PUT для обновления
        if (hasId) {
          console.log(`Обновляем существующий курс с ID ${courseData.id}`);
          const url = `${this.baseUrl}/courses/${courseData.id}`;
          console.log('URL для обновления курса:', url);
          response = await apiClient.put(url, cleanedCourseData);
        } else {
          // Иначе используем POST для создания нового курса
          console.log('Создаем новый курс');
          const url = `${this.baseUrl}/courses`;
          console.log('URL для создания курса:', url);
          response = await apiClient.post(url, cleanedCourseData);
        }

        // Проверяем, что ответ существует
        if (response) {
          console.log('Запрос выполнен. Ответ:', response);

          // Проверяем, является ли response объектом с данными или объектом ответа Axios
          const responseData = response.data ? response.data : response;

          // Если ответ содержит данные и это не пустой объект
          if (responseData && typeof responseData === 'object' && Object.keys(responseData).length > 0) {
            console.log('Курс успешно сохранен:', responseData);

            // Получаем ID созданного/обновленного курса
            const courseId = responseData.id;
            if (!courseId) {
              console.warn('Сервер не вернул ID курса, но ответ содержит данные');
              // Не выбрасываем ошибку, а продолжаем выполнение
            }

            // Сохраняем курс в хранилище
            const store = useCourseStore();
            const savedCourse = responseData;

            // Обновляем список курсов в хранилище, если есть ID
            if (savedCourse.id) {
              const existingIndex = store.courses.findIndex(c => c.id === savedCourse.id);
              if (existingIndex >= 0) {
                console.log(`Обновляем курс с ID ${savedCourse.id} в хранилище`);
                store.courses[existingIndex] = savedCourse;
              } else {
                console.log(`Добавляем новый курс с ID ${savedCourse.id} в хранилище`);
                store.courses.push(savedCourse);
              }
            }

            // Возвращаем сохраненный курс
            return responseData;
          } else {
            console.log('Сервер вернул пустой ответ или пустой объект при сохранении курса');

            // Проверяем, есть ли у response поле status (для объекта ответа Axios)
            // или это сам ответ с кодом статуса
            const statusCode = response.status || 200; // Если статус не определен, считаем 200
            console.log('Статус ответа:', statusCode);

            // Если статус ответа успешный (2xx), считаем операцию успешной
            if (statusCode >= 200 && statusCode < 300) {
              console.log('Статус ответа успешный, считаем операцию успешной');

              // Если это было обновление существующего курса, возвращаем исходные данные
              if (hasId) {
                console.log('Возвращаем исходные данные курса после успешного обновления');

                // Обновляем список курсов в хранилище
                try {
                  console.log('Обновляем список курсов в хранилище после успешного обновления');
                  const store = useCourseStore();
                  const existingIndex = store.courses.findIndex(c => c.id === courseData.id);
                  if (existingIndex >= 0) {
                    console.log(`Обновляем курс с ID ${courseData.id} в хранилище`);
                    store.courses[existingIndex] = { ...store.courses[existingIndex], ...cleanedCourseData };
                  }
                } catch (storeError) {
                  console.warn('Не удалось обновить список курсов в хранилище:', storeError);
                }

                return courseData;
              }

              // Если у курса не было ID, но запрос был успешным, пробуем получить список курсов
              console.log('Пробуем получить список курсов после сохранения...');
              try {
                const courses = await this.getCourses();
                if (courses && courses.length > 0) {
                  // Предполагаем, что последний курс в списке - это только что созданный курс
                  const latestCourse = courses[courses.length - 1];
                  console.log('Получен последний курс из списка:', latestCourse);
                  return latestCourse;
                }
              } catch (listError) {
                console.warn('Не удалось получить список курсов после сохранения:', listError);
              }

              // Если это было создание нового курса, пробуем получить его по имени
              console.log('Пробуем получить созданный курс по имени:', courseData.name);
              try {
                const courses = await this.getCourses();
                const matchingCourse = courses.find(c => c.name === courseData.name);
                if (matchingCourse) {
                  console.log('Найден курс с таким же именем:', matchingCourse);
                  return matchingCourse;
                }
              } catch (error) {
                console.warn('Не удалось найти курс по имени:', error);
              }

              // Возвращаем исходные данные курса, если не удалось получить обновленные данные
              return courseData;
            } else {
              // Если статус ответа не успешный, выбрасываем ошибку
              throw new Error(`Сервер вернул статус ${statusCode} при сохранении курса`);
            }
          }
        } else {
          // Если ответ не существует, выбрасываем ошибку
          throw new Error('Сервер не вернул ответ при сохранении курса');
        }
      } catch (apiError: any) {
        console.error('Ошибка при сохранении курса:', apiError);

        // Если получили ошибку валидации, выводим подробную информацию
        if (apiError.response && apiError.response.status === 422 && apiError.response.data && apiError.response.data.detail) {
          console.error('Ошибки валидации:', apiError.response.data.detail);

          // Формируем более понятное сообщение об ошибке
          const validationErrors = apiError.response.data.detail;
          let errorMessage = 'Ошибки валидации:\n';

          // Собираем информацию о полях с ошибками
          const fieldsWithErrors = new Set<string>();

          for (const err of validationErrors) {
            if (err.loc && err.loc.length > 1) {
              const field = err.loc.slice(1).join('.');
              errorMessage += `- Поле "${field}": ${err.msg}\n`;

              // Добавляем поле в список полей с ошибками
              const topLevelField = err.loc[1];
              fieldsWithErrors.add(topLevelField);
            }
          }

          // Пробуем сохранить курс с минимальным набором полей
          console.log('Пробуем сохранить курс с минимальным набором полей...');

          // Создаем минимальный набор данных для сохранения
          const minimalData = {
            name: courseData.name,
            language: courseData.language,
            level: courseData.level,
            target_audience: courseData.targetAudience || 'adults',
            format: courseData.format || 'online',
            description: courseData.description || `Курс изучения ${courseData.language} языка`
            // Не добавляем уроки, так как они вызывают ошибку валидации
          };

          console.log('Минимальные данные для сохранения:', minimalData);

          try {
            let finalResponse;

            if (hasId) {
              // Если у курса есть ID, используем PUT для обновления
              const finalUrl = `${this.baseUrl}/courses/${courseData.id}`;
              console.log('URL для финальной попытки обновления курса:', finalUrl);
              finalResponse = await apiClient.put(finalUrl, minimalData);
            } else {
              // Иначе используем POST для создания нового курса
              const finalUrl = `${this.baseUrl}/courses`;
              console.log('URL для финальной попытки создания курса:', finalUrl);
              finalResponse = await apiClient.post(finalUrl, minimalData);
            }

            if (finalResponse && finalResponse.data) {
              console.log('Курс успешно сохранен с минимальным набором полей:', finalResponse.data);
              return finalResponse.data;
            }
          } catch (finalError) {
            console.error('Не удалось сохранить курс даже с минимальным набором полей:', finalError);

            // Если все попытки не удались, выбрасываем исходную ошибку
            const enhancedError = new Error(errorMessage);
            enhancedError.name = apiError.name;
            enhancedError.stack = apiError.stack;
            throw enhancedError;
          }
        }

        throw apiError;
      }

      // Если мы дошли до этой точки после повторной попытки, но не вернули данные,
      // возвращаем исходные данные курса
      return courseData;
    } catch (error: any) {
      console.error('Error saving course:', error);
      throw error;
    }
  }

  /**
   * Очищает объект курса от служебных полей перед сохранением
   */
  private cleanCourseDataForSaving(courseData: CourseStructure): any {
    // Проверяем наличие обязательных полей
    if (!courseData || !courseData.name || !courseData.language || !courseData.level) {
      console.error('Отсутствуют обязательные поля курса:', courseData);
      throw new Error('Отсутствуют обязательные поля курса (name, language, level)');
    }

    // Проверяем наличие уроков
    if (!courseData.lessons || !Array.isArray(courseData.lessons) || courseData.lessons.length === 0) {
      console.error('Курс не содержит уроков:', courseData);
      throw new Error('Курс должен содержать хотя бы один урок');
    }

    // Создаем новый объект только с полями, которые принимает API
    // Исключаем поля, которые вызывают ошибку "Extra inputs are not permitted"
    const cleanedData = {
      name: courseData.name,
      language: courseData.language,
      level: courseData.level,
      target_audience: courseData.targetAudience || 'adults', // Добавляем значение по умолчанию
      format: courseData.format || 'online', // Добавляем значение по умолчанию
      description: courseData.description || `Курс изучения ${courseData.language} языка для ${courseData.targetAudience || 'adults'} ${courseData.level} уровня`,
      prerequisites: courseData.prerequisites || [],
      learning_outcomes: courseData.learningOutcomes || []
      // Не добавляем поле lessons, так как оно вызывает ошибку валидации
      // Вместо этого будем создавать уроки отдельно после создания курса
    };

    // Не добавляем следующие поля, так как они вызывают ошибку валидации:
    // - methodology
    // - student_age
    // - student_interests
    // - student_goals
    // - common_mistakes
    // - lessons_count
    // - lesson_duration
    // - lessons (создаем уроки отдельно)
    // - id (если обновляем существующий курс, ID передается в URL)

    console.log('Очищенные данные курса для сохранения:', cleanedData);
    return cleanedData;
  }

  /**
   * Подготавливает данные уроков для сохранения
   */
  private prepareLessonsForSaving(lessons: any[]): any[] {
    if (!lessons || !Array.isArray(lessons)) {
      return [];
    }

    return lessons.map((lesson, index) => {
      // Проверяем наличие обязательных полей урока
      if (!lesson.title) {
        console.warn(`Урок ${index + 1} не содержит заголовка, используем значение по умолчанию`);
      }

      // Проверяем наличие activities
      const activities = Array.isArray(lesson.activities) ? lesson.activities : [];

      return {
        title: lesson.title || `Lesson ${index + 1}`,
        duration: lesson.duration || 60, // Если длительность не указана, берем 60 минут по умолчанию
        order: index + 1, // Добавляем порядковый номер урока
        objectives: Array.isArray(lesson.objectives) ? lesson.objectives : [],
        grammar: Array.isArray(lesson.grammar) ? lesson.grammar : [],
        vocabulary: Array.isArray(lesson.vocabulary) ? lesson.vocabulary : [],
        activities: activities.map((activity, actIndex) => {
          // Проверяем наличие обязательных полей активности
          if (!activity.name && !activity.title) {
            console.warn(`Активность ${actIndex + 1} в уроке ${index + 1} не содержит имени или заголовка, используем значение по умолчанию`);
          }

          // Создаем объект активности только с полями, которые ожидает бэкенд
          return {
            type: activity.type || 'activity',
            name: activity.name || activity.title || `Activity ${actIndex + 1}`, // Используем name или title, или создаем имя по умолчанию
            description: activity.description || '',
            duration: activity.duration || 15, // Если длительность не указана, берем 15 минут по умолчанию
            materials: Array.isArray(activity.materials) ? activity.materials : [],
            objectives: Array.isArray(activity.objectives) ? activity.objectives : []
          };
        })
      };
    });
  }

  /**
   * Обновляет существующий курс
   */
  async updateCourse(courseId: number, courseData: Partial<CourseStructure>): Promise<CourseStructure> {
    try {
      const response = await apiClient.put(`${this.baseUrl}/courses/${courseId}`, courseData);
      return response.data;
    } catch (error) {
      console.error('Error updating course:', error);
      throw error;
    }
  }

  /**
   * Получает список всех курсов
   */
  async getCourses(): Promise<CourseStructure[]> {
    try {
      // Получаем текущего пользователя
      const mainStore = useMainStore();
      const userId = mainStore.user?.id;

      if (!userId) {
        console.warn('Пользователь не авторизован, невозможно получить список курсов');
        return [];
      }

      console.log(`Получение списка курсов для пользователя ${userId}`);

      // Получаем список курсов из хранилища
      const store = useCourseStore();

      // Если в хранилище уже есть курсы, возвращаем их
      if (store.courses && store.courses.length > 0) {
        console.log('Возвращаем курсы из хранилища:', store.courses);
        return store.courses;
      }

      // Если в хранилище нет курсов, пробуем получить их с сервера
      console.log('В хранилище нет курсов, пробуем получить их с сервера');

      // Пробуем разные эндпоинты для получения списка курсов
      const endpoints = [
        // Эндпоинт для получения курсов пользователя
        `${this.baseUrl}/user-courses`,
        // Эндпоинт для получения всех курсов
        `${this.baseUrl}/courses`,
        // Эндпоинт для получения курсов пользователя через профиль
        `/api/v1/profile/courses`,
        // Эндпоинт для получения курсов пользователя через пользователя
        `/api/v1/users/me/courses`
      ];

      // Пробуем каждый эндпоинт по очереди
      for (const endpoint of endpoints) {
        try {
          console.log(`Пробуем получить список курсов через эндпоинт: ${endpoint}`);
          const response = await apiClient.get(endpoint);

          if (response && response.data) {
            const courses = Array.isArray(response.data) ? response.data :
                           (response.data.items ? response.data.items : []);

            if (courses.length > 0) {
              console.log(`Получено ${courses.length} курсов через эндпоинт ${endpoint}:`, courses);

              // Сохраняем курсы в хранилище
              store.courses = courses;

              return courses;
            } else {
              console.log(`Эндпоинт ${endpoint} вернул пустой список курсов`);
            }
          }
        } catch (error) {
          console.warn(`Не удалось получить список курсов через эндпоинт ${endpoint}:`, error);
        }
      }

      // Если не удалось получить список курсов через API, пробуем создать временный курс
      // и использовать его как единственный курс в списке
      console.log('Пробуем создать временный курс для получения доступа к API');

      try {
        // Используем эндпоинт /api/v1/course/courses/generate, который мы знаем, что работает
        const response = await apiClient.post(`${this.baseUrl}/courses/generate`, {
          // Отправляем минимальные данные, чтобы запрос был валидным
          name: "Временный курс для получения списка",
          language: "english",
          level: "beginner",
          target_audience: "adults",
          format: "online",
          lessons_count: 1
        });

        if (response && response.data && response.data.id) {
          const newCourse = response.data;
          console.log('Создан временный курс:', newCourse);

          // Сохраняем временный курс в базе данных
          try {
            console.log('Сохраняем временный курс в базе данных');
            const savedCourse = await this.saveCourse(newCourse);

            if (savedCourse && savedCourse.id) {
              console.log('Временный курс успешно сохранен:', savedCourse);

              // Сохраняем курс в хранилище
              store.courses = [savedCourse];

              return [savedCourse];
            }
          } catch (saveError) {
            console.warn('Не удалось сохранить временный курс:', saveError);

            // Если не удалось сохранить курс, но он был создан, возвращаем его
            store.courses = [newCourse];
            return [newCourse];
          }
        }
      } catch (generateError) {
        console.warn('Не удалось создать временный курс:', generateError);
      }

      // Если все запросы не сработали, возвращаем пустой массив
      console.warn('Не удалось получить список курсов');
      return [];
    } catch (error) {
      console.error('Error fetching courses:', error);
      // В случае ошибки возвращаем пустой массив, чтобы не блокировать UI
      return [];
    }
  }

  /**
   * Получает детальную информацию о курсе
   */
  async getCourseDetails(courseId: number): Promise<CourseStructure> {
    try {
      // Пробуем получить данные с сервера
      try {
        const response = await apiClient.get(`${this.baseUrl}/course/${courseId}`);
        if (response && response.data) {
          return response.data;
        }
      } catch (apiError) {
        console.warn(`Не удалось получить данные курса ${courseId} с сервера через /course/:`, apiError);

        // Пробуем другой эндпоинт
        try {
          const response = await apiClient.get(`${this.baseUrl}/courses/${courseId}`);
          if (response && response.data) {
            return response.data;
          }
        } catch (secondApiError) {
          console.warn(`Не удалось получить данные курса ${courseId} с сервера через /courses/:`, secondApiError);
        }
      }

      // Если не удалось получить данные с сервера, пробуем получить из хранилища
      const store = useCourseStore();

      // Если в хранилище есть текущий курс и его ID совпадает с запрашиваемым
      if (store.currentCourse && store.currentCourse.id === courseId) {
        console.log('Возвращаем курс из хранилища:', store.currentCourse);
        return store.currentCourse;
      }

      // Ищем курс в списке курсов
      const courseFromList = store.courses.find(c => c.id === courseId);
      if (courseFromList) {
        console.log('Возвращаем курс из списка курсов:', courseFromList);
        return courseFromList;
      }

      // Если курс не найден ни на сервере, ни в хранилище, выбрасываем ошибку
      throw new Error(`Курс с ID ${courseId} не найден`);
    } catch (error) {
      console.error('Error fetching course details:', error);
      throw error;
    }
  }

  /**
   * Удаляет курс
   */
  async deleteCourse(courseId: number): Promise<void> {
    try {
      await apiClient.delete(`${this.baseUrl}/courses/${courseId}`);
    } catch (error) {
      console.error('Error deleting course:', error);
      throw error;
    }
  }

  /**
   * Клонирует существующий курс
   */
  async cloneCourse(courseId: number, newName: string): Promise<CourseStructure> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/courses/${courseId}/clone`, { name: newName });
      return response.data;
    } catch (error) {
      console.error('Error cloning course:', error);
      throw error;
    }
  }

  /**
   * Обрабатывает свободный запрос к нейросети
   */
  async generateFreeQuery(queryData: { language: string, query: string }): Promise<string> {
    try {
      const response = await apiClient.post(`/api/v1/content/generate_free_query`, queryData);

      // Логируем полученный ответ для отладки
      console.log('Free query API response:', response);

      // Проверяем структуру ответа и извлекаем контент
      if (response && typeof response === 'object') {
        // Если ответ имеет структуру { status, data, message }
        if (response.status === 'success' && response.data && response.data.content) {
          // Убеждаемся, что контент - строка
          const content = typeof response.data.content === 'string'
            ? response.data.content
            : JSON.stringify(response.data.content);
          return content;
        }
        // Если ответ сам по себе содержит контент
        else if (response.content) {
          return typeof response.content === 'string'
            ? response.content
            : JSON.stringify(response.content);
        }
        // В случае, если response уже сам является контентом в виде строки
        else if (typeof response === 'string') {
          return response;
        }
        // Для обработки любых других форматов ответа
        else {
          console.warn('Unexpected response format:', response);
          return JSON.stringify(response);
        }
      }

      // Если все проверки не сработали, просто преобразуем ответ в строку
      return typeof response === 'string' ? response : JSON.stringify(response);
    } catch (error) {
      console.error('Error processing free query:', error);
      throw error;
    }
  }

  /**
   * Генерирует объяснение сложной концепции для ученика
   */
  async generateConceptExplanation(data: {
    language: string,
    concept: string,
    age: string,
    level: string,
    interests: string,
    style: string
  }): Promise<string> {
    try {
      const response = await apiClient.post(`/api/v1/content/generate_concept_explanation`, data);

      // Логируем полученный ответ для отладки
      console.log('Concept explanation API response:', response);

      // Проверяем структуру ответа
      if (response && typeof response === 'object') {
        // Если ответ имеет структуру { status, data, message }
        if (response.status === 'success' && response.data && typeof response.data.content === 'string') {
          return response.data.content;
        }
        // Если response.data сам является строкой
        else if (typeof response.data === 'string') {
          return response.data;
        }
        // Если content находится в другом месте структуры ответа
        else if (response.data && response.data.data && typeof response.data.data.content === 'string') {
          return response.data.data.content;
        }
        // Для всех остальных случаев преобразуем в строку
        else {
          console.warn('Необычный формат ответа от API объяснения концепции:', response);
          return JSON.stringify(response.data);
        }
      }

      // Если все проверки не сработали, преобразуем весь ответ в строку
      return typeof response === 'string' ? response : JSON.stringify(response);
    } catch (error) {
      console.error('Error generating concept explanation:', error);
      throw error;
    }
  }
}

export default new CourseGeneratorService();
