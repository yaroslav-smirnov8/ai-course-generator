// src/store/course.ts
import { defineStore } from 'pinia'
import courseGeneratorService from '@/services/courseGenerator'
import type { ApiResponse } from '@/services/courseGenerator'
import type { CourseFormData, CourseStructure, Lesson, GeneratedExercisesResponse, GeneratedGameResponse } from '@/types/course' // Импортируем GeneratedExercisesResponse и GeneratedGameResponse
import { useMainStore } from '@/store'
import { apiClient } from '@/api/client'; // <-- Добавляем импорт
import { ContentType, ActionType } from '@/types/enums'; // Добавляем импорт ActionType

// Расширяем интерфейс состояния
interface CourseState {
  courses: CourseStructure[]
  currentCourse: CourseStructure | null
  isLoading: boolean
  error: string | null
  // Добавляем метаданные восстановления
  recoveryStatus: 'success' | 'partial' | 'failure' | 'none'
  recoveryDetails: {
    recoveredFields: string[]
    missingFields: string[]
    messages: string[]
    timestamp: string
  }
}

// Расширенный тип для данных урока
interface LessonData extends Partial<Lesson> {
  courseId?: number
  [key: string]: any
}

export const useCourseStore = defineStore('course', {
  state: (): CourseState => ({
    courses: [],
    currentCourse: null,
    isLoading: false,
    error: null,
    // Инициализируем метаданные восстановления
    recoveryStatus: 'none',
    recoveryDetails: {
      recoveredFields: [],
      missingFields: [],
      messages: [],
      timestamp: ''
    }
  }),

  actions: {
    // Получение списка курсов пользователя
    async fetchUserCourses() {
      this.isLoading = true
      this.error = null

      try {
        console.log('Запрос на получение списка курсов пользователя');
        const courses = await courseGeneratorService.getCourses()

        // Проверяем, что courses - это массив
        if (Array.isArray(courses)) {
          console.log(`Получено ${courses.length} курсов`);

          // Если курсы получены, сохраняем их в хранилище
          this.courses = courses

          // Если список курсов пуст, но ошибки нет, это нормально
          if (courses.length === 0) {
            console.log('Список курсов пуст, но это не ошибка');
          }

          return courses
        } else {
          console.warn('Неожиданный формат данных курсов:', courses)

          // Если данные не являются массивом, но не null/undefined, пробуем преобразовать
          if (courses) {
            // Если courses - объект с полем items, используем его
            if (typeof courses === 'object' && 'items' in courses && Array.isArray(courses.items)) {
              console.log('Извлекаем курсы из поля items:', courses.items);
              this.courses = courses.items
              return courses.items
            }

            // Если courses - объект, пробуем преобразовать его в массив
            if (typeof courses === 'object') {
              const coursesArray = Object.values(courses).filter(item =>
                typeof item === 'object' && item !== null && 'id' in item
              );

              if (coursesArray.length > 0) {
                console.log('Преобразовали объект в массив курсов:', coursesArray);
                this.courses = coursesArray
                return coursesArray
              }
            }
          }

          // Если не удалось преобразовать данные, возвращаем пустой массив
          console.warn('Не удалось преобразовать данные в массив курсов, возвращаем пустой массив');
          this.courses = []
          return []
        }
      } catch (error: any) {
        console.error('Ошибка при загрузке курсов:', error)

        // Формируем понятное сообщение об ошибке
        let errorMessage = 'Не удалось загрузить список курсов';

        if (error.response) {
          // Ошибка от сервера
          const status = error.response.status;
          const data = error.response.data;

          errorMessage += `: Сервер вернул ошибку ${status}`;

          if (data && data.detail) {
            errorMessage += ` - ${data.detail}`;
          }
        } else if (error.message) {
          // Ошибка с сообщением
          errorMessage += `: ${error.message}`;
        }

        this.error = errorMessage;

        // Сохраняем пустой массив в хранилище
        this.courses = []

        // Выбрасываем ошибку для обработки в компоненте
        throw new Error(errorMessage)
      } finally {
        this.isLoading = false
      }
    },

    async generateCourse(formData: CourseFormData) {
      this.isLoading = true
      // Сбрасываем предыдущую информацию о восстановлении
      this.resetRecoveryInfo()

      try {
        const response = await courseGeneratorService.generateCourseStructure(formData)

        // Обрабатываем метаданные восстановления, если они есть
        if (response.metadata) {
          this.recoveryStatus = response.metadata.recovery_status || 'none'
          this.recoveryDetails = {
            recoveredFields: response.metadata.recovered_fields || [],
            missingFields: response.metadata.missing_fields || [],
            messages: response.metadata.messages || [],
            timestamp: new Date().toISOString()
          }
        }

        // Обрабатываем данные курса
        this.currentCourse = response.data
        return response.data
      } catch (error) {
        this.error = 'Ошибка при генерации курса'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    // Метод для генерации курса за баллы
    async generateCourseWithPoints(formData: CourseFormData): Promise<CourseStructure | null> {
      console.log('[generateCourseWithPoints] Входящие данные:', formData);
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации курса';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем возможность генерации за баллы
      const canGenerate = await mainStore.checkAndTrackGenerationWithPoints(ContentType.COURSE, 8);
      if (!canGenerate) {
        const errorMsg = 'Недостаточно баллов для генерации курса. Требуется 8 баллов.';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      this.error = null;
      try {
        console.log(`[generateCourseWithPoints] Запрос на генерацию курса за баллы "${formData.courseName}"`);

        // Формируем payload для API с параметрами для генерации за баллы
        const payload = {
          name: formData.courseName,
          language: formData.language,
          level: formData.level,
          start_level: formData.startLevel || formData.level,
          target_audience: formData.targetAudience,
          format: formData.format,
          methodology: formData.methodology,
          duration: formData.duration,
          lessons_count: formData.lessonsCount,
          student_age: formData.age,
          student_goals: formData.goals,
          student_interests: formData.interests,
          additional_requirements: formData.additionalRequirements,
          with_points: true,
          skip_tariff_check: true,
          skip_limits: true
        };
        console.log('[generateCourseWithPoints] Payload для API:', payload);

        // Вызываем API endpoint
        const response = await apiClient.post<CourseStructure>('/api/v1/course/courses/generate', payload);
        console.log('[generateCourseWithPoints] Тело ответа API:', response);

        // Проверяем, что ответ содержит id и lessons
        if (response && response.id && response.lessons) {
          console.log(`[generateCourseWithPoints] Извлеченные данные курса за баллы "${formData.courseName}":`, response);

          // Отслеживаем достижение
          try {
            await mainStore.checkAchievements(ActionType.GENERATION, {
              content_type: ContentType.COURSE,
              language: formData.language,
              level: formData.level,
              with_points: true
            });
          } catch (achievementError) {
            console.warn('Ошибка при проверке достижений:', achievementError);
            // Продолжаем выполнение, даже если проверка достижений не удалась
          }

          return response;
        } else {
          console.warn(`API не вернул ожидаемую структуру курса. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить структуру курса из ответа API.");
        }

      } catch (error: any) {
        console.error(`[generateCourseWithPoints] Ошибка при генерации курса за баллы "${formData.courseName}":`);
        console.error("Full error object:", error);

        let errorMessage = 'Неизвестная ошибка при генерации курса за баллы';
        if (error.response) {
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          console.error("No response received. Network error or timeout?");
          errorMessage = 'Сетевая ошибка или таймаут при запросе курса за баллы.';
        } else {
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }
        console.error("Final error message set:", errorMessage);
        this.error = errorMessage;
        return null; // Возвращаем null в случае ошибки
      }
    },

    // Новый метод для сброса информации о восстановлении
    resetRecoveryInfo() {
      this.recoveryStatus = 'none'
      this.recoveryDetails = {
        recoveredFields: [],
        missingFields: [],
        messages: [],
        timestamp: ''
      }
    },

    async saveCourse(course: CourseStructure) {
      this.isLoading = true
      try {
        const savedCourse = await courseGeneratorService.saveCourse(course)

        // Проверяем, что savedCourse не null и имеет необходимые поля
        if (savedCourse && typeof savedCourse === 'object') {
          // Если savedCourse не содержит всех полей CourseStructure,
          // создаем объект, который объединяет исходный курс и полученные данные
          const mergedCourse = {
            ...course,
            ...savedCourse,
            // Если id есть только в savedCourse, используем его
            id: savedCourse.id || course.id,
            // Если name есть только в savedCourse, используем его
            name: savedCourse.name || course.name,
          };

          // Обновляем текущий курс
          this.currentCourse = mergedCourse

          // Обновляем список курсов
          const existingIndex = this.courses.findIndex(c => c.id === mergedCourse.id)
          if (existingIndex >= 0) {
            this.courses[existingIndex] = mergedCourse
          } else {
            this.courses.push(mergedCourse)
          }

          return mergedCourse
        } else {
          // Если savedCourse не содержит данных, возвращаем исходный курс
          console.warn('Сервер вернул неожиданный формат данных при сохранении курса:', savedCourse);
          return course;
        }
      } catch (error) {
        this.error = 'Ошибка при сохранении курса'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    // Старое действие, возможно, для генерации отдельного урока
    async generateLessonPlan(lessonData: LessonData) {
      console.warn("Вызвано устаревшее действие generateLessonPlan. Используйте generatePlanForCourseLesson для уроков курса.");
      this.isLoading = true
      try {
        // Вызываем старый метод сервиса
        const lesson = await courseGeneratorService.generateLessonPlan(lessonData)

        // Обновляем урок в текущем курсе (логика может отличаться для отдельного урока)
        if (this.currentCourse) {
          const lessonIndex = this.currentCourse.lessons.findIndex(l => l.id === lesson.id)
          if (lessonIndex >= 0) {
            this.currentCourse.lessons[lessonIndex] = lesson
          }
        }

        return lesson
      } catch (error) {
        this.error = 'Ошибка при генерации плана урока'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    // Новое действие для генерации плана урока внутри курса
    async generatePlanForCourseLesson(lessonData: LessonData) {
      this.isLoading = true;
      this.error = null;
      try {
        // Проверяем наличие необходимых данных
        if (!lessonData.id || !this.currentCourse) {
           throw new Error("Недостаточно данных для генерации плана урока (ID урока или текущий курс отсутствуют).");
        }

        // Формируем данные для сервиса, включая ID курса и уровень из текущего курса
        const servicePayload = {
          id: lessonData.id,
          courseId: this.currentCourse.id, // Берем из текущего курса
          title: lessonData.title || '', // Используем пустую строку, если нет
          level: this.currentCourse.level, // Берем из текущего курса
          duration: lessonData.duration || 60, // Значение по умолчанию, если нет
          objectives: lessonData.objectives || [],
          grammar: lessonData.grammar || [],
          vocabulary: lessonData.vocabulary || []
        };

        // Вызываем новый метод сервиса с полным набором данных
        const generatedPlan = await courseGeneratorService.generatePlanForCourseLesson(servicePayload);

        // TODO: Обработать ответ (generatedPlan) и обновить состояние урока в this.currentCourse
        // Например, если API возвращает обновленный объект урока:
        if (this.currentCourse && generatedPlan && generatedPlan.id) {
           const lessonIndex = this.currentCourse.lessons.findIndex(l => l.id === generatedPlan.id);
           if (lessonIndex !== -1) {
             // Обновляем конкретный урок новыми данными плана
             // Важно: структура generatedPlan должна соответствовать ожиданиям
             // Возможно, потребуется слияние данных, а не полная замена
             this.currentCourse.lessons[lessonIndex] = { ...this.currentCourse.lessons[lessonIndex], ...generatedPlan };
             console.log(`План для урока ${generatedPlan.id} обновлен в store.`);
           }
        } else {
          console.warn("Не удалось обновить план урока в store. Курс или план не найдены.", this.currentCourse, generatedPlan);
        }

        // Можно вернуть результат для показа уведомления в компоненте
        return generatedPlan;

      } catch (error: any) {
        console.error('Ошибка в действии generatePlanForCourseLesson:', error);
        this.error = error.message || 'Ошибка при генерации плана урока в store';
        throw error; // Пробрасываем ошибку дальше
      } finally {
        this.isLoading = false;
      }
    },

    // --- НОВЫЙ МЕТОД ДЛЯ ПОЛУЧЕНИЯ ТЕКСТА ПЛАНА УРОКА ---
    async fetchGeneratedLessonPlanText(lessonData: LessonData, courseContext: CourseFormData): Promise<string | null> {
      console.log('[fetchGeneratedLessonPlanText] Входящие данные:', { lessonData, courseContext }); // ЛОГ 1: Входящие данные
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации плана урока';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      if (!lessonData.id) {
        const errorMsg = 'Отсутствует ID урока для генерации плана';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем и отслеживаем генерацию плана урока
      const canGenerate = await mainStore.checkAndTrackGeneration(ContentType.LESSON_PLAN);
      if (!canGenerate) {
        const errorMsg = 'Достигнут дневной лимит генераций планов уроков';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Не устанавливаем isLoading здесь, так как это делает вызывающий компонент (CourseGenerator)
      // this.isLoading = true;
      this.error = null;
      try {
        console.log(`[fetchGeneratedLessonPlanText] Запрос на генерацию текстового плана для урока ${lessonData.id}`);

        // Формируем payload для API
        // Включаем детали урока и контекст курса
        const payload = {
          lesson_details: {
            id: lessonData.id,
            title: lessonData.title,
            objectives: lessonData.objectives,
            grammar: lessonData.grammar,
            vocabulary: lessonData.vocabulary,
            activities: lessonData.activities,
            duration: lessonData.duration,
            // Добавьте другие поля урока, если они нужны API
          },
          course_context: {
            language: courseContext.language,
            level: courseContext.level,
            target_audience: courseContext.targetAudience,
            methodology: courseContext.methodology,
            age: courseContext.age,
            goals: courseContext.goals,
            interests: courseContext.interests,
            // Добавьте другие поля контекста курса, если они нужны API
          }
        };
        console.log('[fetchGeneratedLessonPlanText] Payload для API:', payload); // ЛОГ 2: Payload

        // Вызываем API endpoint (убедитесь, что эндпоинт правильный)
        // Используем apiClient, который уже импортирован
        const response = await apiClient.post(`/api/v1/course/lessons/${lessonData.id}/generate_plan`, payload); // Добавлен префикс /course
        // ВАЖНО: apiClient.post возвращает response.data, поэтому 'response' здесь - это уже тело ответа.
        console.log('[fetchGeneratedLessonPlanText] Тело ответа API:', response); // ЛОГ 3: Тело ответа API

        // Проверяем, что тело ответа содержит поле plan_content и оно является строкой
        if (response && typeof response.plan_content === 'string') {
           const planText = response.plan_content; // Извлекаем текст из поля plan_content тела ответа
           console.log(`[fetchGeneratedLessonPlanText] Извлеченный текст плана для урока ${lessonData.id}:`, planText); // ЛОГ 4: Извлеченный текст
           return planText;
        } else {
          // Логируем, что именно пришло в теле ответа, если plan_content отсутствует или не строка
          console.warn(`API не вернул ожидаемый текст плана в поле 'plan_content'. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить текст плана урока из ответа API (поле 'plan_content' отсутствует или не является строкой в теле ответа).");
        }

      } catch (error: any) {
        console.error(`[fetchGeneratedLessonPlanText] Ошибка при получении текстового плана для урока ${lessonData.id}:`);
        console.error("Full error object:", error); // Логируем весь объект ошибки

        let errorMessage = 'Неизвестная ошибка при генерации текстового плана';

        if (error.response) {
          // Ошибка пришла от сервера (статус 4xx или 5xx)
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          // Запрос был сделан, но ответ не был получен (сетевая ошибка, таймаут и т.д.)
          console.error("No response received. Network error or timeout?");
          console.error("Error request object:", error.request);
          errorMessage = 'Сетевая ошибка или таймаут при запросе плана урока.';
        } else {
          // Ошибка произошла при настройке запроса
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }

        console.error("Final error message set:", errorMessage);
        console.error("Error stack:", error?.stack); // Логируем стек вызовов

        this.error = errorMessage; // Устанавливаем более точное сообщение об ошибке
        // Не пробрасываем ошибку, чтобы вызывающий компонент мог обработать null
        // throw error;
        return null; // Возвращаем null в случае ошибки
      } finally {
        // Не сбрасываем isLoading здесь
        // this.isLoading = false;
      }
    },
    // --- КОНЕЦ НОВОГО МЕТОДА ---

    // --- МЕТОД ДЛЯ ПОЛУЧЕНИЯ ТЕКСТА ПЛАНА УРОКА ЗА БАЛЛЫ ---
    async fetchGeneratedLessonPlanTextWithPoints(lessonData: LessonData, courseContext: CourseFormData): Promise<string | null> {
      console.log('[fetchGeneratedLessonPlanTextWithPoints] Входящие данные:', { lessonData, courseContext });
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации плана урока';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      if (!lessonData.id) {
        const errorMsg = 'Отсутствует ID урока для генерации плана';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем возможность генерации за баллы
      const canGenerate = await mainStore.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN, 8);
      if (!canGenerate) {
        const errorMsg = 'Недостаточно баллов для генерации плана урока. Требуется 8 баллов.';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      this.error = null;
      try {
        console.log(`[fetchGeneratedLessonPlanTextWithPoints] Запрос на генерацию текстового плана за баллы для урока ${lessonData.id}`);

        // Формируем payload для API с параметрами для генерации за баллы
        const payload = {
          lesson_details: {
            id: lessonData.id,
            title: lessonData.title,
            objectives: lessonData.objectives,
            grammar: lessonData.grammar,
            vocabulary: lessonData.vocabulary,
            activities: lessonData.activities,
            duration: lessonData.duration,
          },
          course_context: {
            language: courseContext.language,
            level: courseContext.level,
            target_audience: courseContext.targetAudience,
            methodology: courseContext.methodology,
            age: courseContext.age,
            goals: courseContext.goals,
            interests: courseContext.interests,
          },
          with_points: true,
          skip_tariff_check: true,
          skip_limits: true
        };
        console.log('[fetchGeneratedLessonPlanTextWithPoints] Payload для API:', payload);

        // Вызываем API endpoint
        const response = await apiClient.post(`/api/v1/course/lessons/${lessonData.id}/generate_plan`, payload);
        console.log('[fetchGeneratedLessonPlanTextWithPoints] Тело ответа API:', response);

        // Проверяем, что тело ответа содержит поле plan_content и оно является строкой
        if (response && typeof response.plan_content === 'string') {
           const planText = response.plan_content;
           console.log(`[fetchGeneratedLessonPlanTextWithPoints] Извлеченный текст плана за баллы для урока ${lessonData.id}:`, planText);

           // Отслеживаем достижение
           try {
             await mainStore.checkAchievements(ActionType.GENERATION, {
               content_type: ContentType.LESSON_PLAN,
               language: courseContext.language,
               level: courseContext.level,
               with_points: true
             });
           } catch (achievementError) {
             console.warn('Ошибка при проверке достижений:', achievementError);
             // Продолжаем выполнение, даже если проверка достижений не удалась
           }

           return planText;
        } else {
          console.warn(`API не вернул ожидаемый текст плана в поле 'plan_content'. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить текст плана урока из ответа API (поле 'plan_content' отсутствует или не является строкой в теле ответа).");
        }

      } catch (error: any) {
        console.error(`[fetchGeneratedLessonPlanTextWithPoints] Ошибка при получении текстового плана за баллы для урока ${lessonData.id}:`);
        console.error("Full error object:", error);

        let errorMessage = 'Неизвестная ошибка при генерации текстового плана за баллы';

        if (error.response) {
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          console.error("No response received. Network error or timeout?");
          errorMessage = 'Сетевая ошибка или таймаут при запросе плана урока за баллы.';
        } else {
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }

        console.error("Final error message set:", errorMessage);
        this.error = errorMessage;
        return null; // Возвращаем null в случае ошибки
      }
    },
    // --- КОНЕЦ МЕТОДА ДЛЯ ПЛАНА УРОКА ЗА БАЛЛЫ ---

    // --- НОВОЕ ДЕЙСТВИЕ ДЛЯ ГЕНЕРАЦИИ УПРАЖНЕНИЙ ---
    async fetchGeneratedExercises(lessonData: LessonData, courseContext: CourseFormData): Promise<string | null> {
      console.log('[fetchGeneratedExercises] Входящие данные:', { lessonData, courseContext });
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации упражнений';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      if (!lessonData.id) {
        const errorMsg = 'Отсутствует ID урока для генерации упражнений';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем и отслеживаем генерацию упражнений
      const canGenerate = await mainStore.checkAndTrackGeneration(ContentType.EXERCISE);
      if (!canGenerate) {
        const errorMsg = 'Достигнут дневной лимит генераций упражнений';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      this.error = null;
      try {
        console.log(`[fetchGeneratedExercises] Запрос на генерацию упражнений для урока ${lessonData.id}`);

        // Формируем payload для нового API
        const payload = {
          lesson_details: {
            title: lessonData.title,
            objectives: lessonData.objectives,
            grammar: lessonData.grammar,
            vocabulary: lessonData.vocabulary,
            duration: lessonData.duration,
          },
          course_context: {
            language: courseContext.language,
            level: courseContext.level,
            target_audience: courseContext.targetAudience, // Добавляем недостающее поле
            methodology: courseContext.methodology,
            age: courseContext.age, // Используем age из courseContext (переданный из CourseView)
            goals: courseContext.goals,
            interests: courseContext.interests,
          }
        };
        console.log('[fetchGeneratedExercises] Payload для API:', payload);

        // Вызываем новый API endpoint
        // Предполагаем, что apiClient имеет метод post, который возвращает тело ответа
        const response = await apiClient.post<GeneratedExercisesResponse>(`/api/v1/course/lessons/${lessonData.id}/generate_exercises`, payload); // Исправлен путь
        console.log('[fetchGeneratedExercises] Тело ответа API:', response);

        // Проверяем, что ответ содержит exercises_content
        if (response && typeof response.exercises_content === 'string') {
           const exercisesText = response.exercises_content;
           console.log(`[fetchGeneratedExercises] Извлеченный текст упражнений для урока ${lessonData.id}:`, exercisesText);
           return exercisesText;
        } else {
          console.warn(`API не вернул ожидаемый текст упражнений в поле 'exercises_content'. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить текст упражнений из ответа API.");
        }

      } catch (error: any) {
        console.error(`[fetchGeneratedExercises] Ошибка при получении упражнений для урока ${lessonData.id}:`);
        console.error("Full error object:", error);

        let errorMessage = 'Неизвестная ошибка при генерации упражнений';
        if (error.response) {
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          console.error("No response received. Network error or timeout?");
          errorMessage = 'Сетевая ошибка или таймаут при запросе упражнений.';
        } else {
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }
        console.error("Final error message set:", errorMessage);
        this.error = errorMessage;
        return null; // Возвращаем null в случае ошибки
      }
      // finally блок не нужен, т.к. isLoading управляется в компоненте
    },
    // --- КОНЕЦ НОВОГО ДЕЙСТВИЯ ДЛЯ УПРАЖНЕНИЙ ---

    // --- ДЕЙСТВИЕ ДЛЯ ГЕНЕРАЦИИ УПРАЖНЕНИЙ ЗА БАЛЛЫ ---
    async fetchGeneratedExercisesWithPoints(lessonData: LessonData, courseContext: CourseFormData): Promise<string | null> {
      console.log('[fetchGeneratedExercisesWithPoints] Входящие данные:', { lessonData, courseContext });
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации упражнений';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      if (!lessonData.id) {
        const errorMsg = 'Отсутствует ID урока для генерации упражнений';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем возможность генерации за баллы
      const canGenerate = await mainStore.checkAndTrackGenerationWithPoints(ContentType.EXERCISE, 8);
      if (!canGenerate) {
        const errorMsg = 'Недостаточно баллов для генерации упражнений. Требуется 8 баллов.';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      this.error = null;
      try {
        console.log(`[fetchGeneratedExercisesWithPoints] Запрос на генерацию упражнений за баллы для урока ${lessonData.id}`);

        // Формируем payload для API с параметрами для генерации за баллы
        const payload = {
          lesson_details: {
            title: lessonData.title,
            objectives: lessonData.objectives,
            grammar: lessonData.grammar,
            vocabulary: lessonData.vocabulary,
            duration: lessonData.duration,
          },
          course_context: {
            language: courseContext.language,
            level: courseContext.level,
            target_audience: courseContext.targetAudience,
            methodology: courseContext.methodology,
            age: courseContext.age,
            goals: courseContext.goals,
            interests: courseContext.interests,
          },
          with_points: true,
          skip_tariff_check: true,
          skip_limits: true
        };
        console.log('[fetchGeneratedExercisesWithPoints] Payload для API:', payload);

        // Вызываем API endpoint
        const response = await apiClient.post<GeneratedExercisesResponse>(`/api/v1/course/lessons/${lessonData.id}/generate_exercises`, payload);
        console.log('[fetchGeneratedExercisesWithPoints] Тело ответа API:', response);

        // Проверяем, что ответ содержит exercises_content
        if (response && typeof response.exercises_content === 'string') {
           const exercisesText = response.exercises_content;
           console.log(`[fetchGeneratedExercisesWithPoints] Извлеченный текст упражнений за баллы для урока ${lessonData.id}:`, exercisesText);

           // Отслеживаем достижение
           try {
             await mainStore.checkAchievements(ActionType.GENERATION, {
               content_type: ContentType.EXERCISE,
               language: courseContext.language,
               level: courseContext.level,
               with_points: true
             });
           } catch (achievementError) {
             console.warn('Ошибка при проверке достижений:', achievementError);
             // Продолжаем выполнение, даже если проверка достижений не удалась
           }

           return exercisesText;
        } else {
          console.warn(`API не вернул ожидаемый текст упражнений в поле 'exercises_content'. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить текст упражнений из ответа API.");
        }

      } catch (error: any) {
        console.error(`[fetchGeneratedExercisesWithPoints] Ошибка при получении упражнений за баллы для урока ${lessonData.id}:`);
        console.error("Full error object:", error);

        let errorMessage = 'Неизвестная ошибка при генерации упражнений за баллы';
        if (error.response) {
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          console.error("No response received. Network error or timeout?");
          errorMessage = 'Сетевая ошибка или таймаут при запросе упражнений за баллы.';
        } else {
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }
        console.error("Final error message set:", errorMessage);
        this.error = errorMessage;
        return null; // Возвращаем null в случае ошибки
      }
    },
    // --- КОНЕЦ ДЕЙСТВИЯ ДЛЯ УПРАЖНЕНИЙ ЗА БАЛЛЫ ---

    // --- НОВОЕ ДЕЙСТВИЕ ДЛЯ ГЕНЕРАЦИИ ИГРЫ ---
    async fetchGeneratedGame(lessonData: LessonData, courseContext: CourseFormData, gameType?: string): Promise<GeneratedGameResponse | null> {
      console.log('[fetchGeneratedGame] Входящие данные:', { lessonData, courseContext, gameType });
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации игры';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      if (!lessonData.id) {
        const errorMsg = 'Отсутствует ID урока для генерации игры';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем и отслеживаем генерацию игры
      const canGenerate = await mainStore.checkAndTrackGeneration(ContentType.GAME);
      if (!canGenerate) {
        const errorMsg = 'Достигнут дневной лимит генераций игр';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      this.error = null;
      try {
        console.log(`[fetchGeneratedGame] Запрос на генерацию игры для урока ${lessonData.id}`);

        // Формируем payload для нового API
        const payload = {
          lesson_details: {
            title: lessonData.title,
            objectives: lessonData.objectives,
            grammar: lessonData.grammar,
            vocabulary: lessonData.vocabulary,
            duration: lessonData.duration,
          },
          course_context: {
            language: courseContext.language,
            level: courseContext.level,
            target_audience: courseContext.targetAudience,
            methodology: courseContext.methodology,
            age: courseContext.age,
            goals: courseContext.goals,
            interests: courseContext.interests,
          },
          game_type: gameType // Передаем опциональный тип игры
        };
        console.log('[fetchGeneratedGame] Payload для API:', payload);

        // Вызываем новый API endpoint
        const response = await apiClient.post<GeneratedGameResponse>(`/api/v1/course/lessons/${lessonData.id}/generate_game`, payload); // Исправлен путь
        console.log('[fetchGeneratedGame] Тело ответа API:', response);

        // Проверяем, что ответ содержит game_content (строку Markdown)
        if (response && typeof response.game_content === 'string') {
           console.log(`[fetchGeneratedGame] Извлеченные данные игры (Markdown) для урока ${lessonData.id}:`, response);
           return response; // Возвращаем весь объект ответа { game_content: string, game_type?: string }
        } else {
          console.warn(`API не вернул ожидаемый контент игры в поле 'game_content'. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить контент игры из ответа API.");
        }

      } catch (error: any) {
        console.error(`[fetchGeneratedGame] Ошибка при получении игры для урока ${lessonData.id}:`);
        console.error("Full error object:", error);

        let errorMessage = 'Неизвестная ошибка при генерации игры';
        if (error.response) {
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          console.error("No response received. Network error or timeout?");
          errorMessage = 'Сетевая ошибка или таймаут при запросе игры.';
        } else {
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }
        console.error("Final error message set:", errorMessage);
        this.error = errorMessage;
        return null; // Возвращаем null в случае ошибки
      }
    },
    // --- КОНЕЦ НОВОГО ДЕЙСТВИЯ ДЛЯ ИГРЫ ---

    // --- ДЕЙСТВИЕ ДЛЯ ГЕНЕРАЦИИ ИГРЫ ЗА БАЛЛЫ ---
    async fetchGeneratedGameWithPoints(lessonData: LessonData, courseContext: CourseFormData, gameType?: string): Promise<GeneratedGameResponse | null> {
      console.log('[fetchGeneratedGameWithPoints] Входящие данные:', { lessonData, courseContext, gameType });
      const mainStore = useMainStore();
      if (!mainStore.user) {
        const errorMsg = 'Пользователь не авторизован для генерации игры';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      if (!lessonData.id) {
        const errorMsg = 'Отсутствует ID урока для генерации игры';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      // Проверяем возможность генерации за баллы
      const canGenerate = await mainStore.checkAndTrackGenerationWithPoints(ContentType.GAME, 8);
      if (!canGenerate) {
        const errorMsg = 'Недостаточно баллов для генерации игры. Требуется 8 баллов.';
        this.error = errorMsg;
        console.error(errorMsg);
        throw new Error(errorMsg);
      }

      this.error = null;
      try {
        console.log(`[fetchGeneratedGameWithPoints] Запрос на генерацию игры за баллы для урока ${lessonData.id}`);

        // Формируем payload для API с параметрами для генерации за баллы
        const payload = {
          lesson_details: {
            title: lessonData.title,
            objectives: lessonData.objectives,
            grammar: lessonData.grammar,
            vocabulary: lessonData.vocabulary,
            duration: lessonData.duration,
          },
          course_context: {
            language: courseContext.language,
            level: courseContext.level,
            target_audience: courseContext.targetAudience,
            methodology: courseContext.methodology,
            age: courseContext.age,
            goals: courseContext.goals,
            interests: courseContext.interests,
          },
          game_type: gameType, // Передаем опциональный тип игры
          with_points: true,
          skip_tariff_check: true,
          skip_limits: true
        };
        console.log('[fetchGeneratedGameWithPoints] Payload для API:', payload);

        // Вызываем API endpoint
        const response = await apiClient.post<GeneratedGameResponse>(`/api/v1/course/lessons/${lessonData.id}/generate_game`, payload);
        console.log('[fetchGeneratedGameWithPoints] Тело ответа API:', response);

        // Проверяем, что ответ содержит game_content
        if (response && typeof response.game_content === 'string') {
           console.log(`[fetchGeneratedGameWithPoints] Извлеченные данные игры за баллы (Markdown) для урока ${lessonData.id}:`, response);

           // Отслеживаем достижение
           try {
             await mainStore.checkAchievements(ActionType.GENERATION, {
               content_type: ContentType.GAME,
               language: courseContext.language,
               level: courseContext.level,
               with_points: true
             });
           } catch (achievementError) {
             console.warn('Ошибка при проверке достижений:', achievementError);
             // Продолжаем выполнение, даже если проверка достижений не удалась
           }

           return response; // Возвращаем весь объект ответа { game_content: string, game_type?: string }
        } else {
          console.warn(`API не вернул ожидаемый контент игры в поле 'game_content'. Полученное тело ответа:`, response);
          throw new Error("Не удалось получить контент игры из ответа API.");
        }

      } catch (error: any) {
        console.error(`[fetchGeneratedGameWithPoints] Ошибка при получении игры за баллы для урока ${lessonData.id}:`);
        console.error("Full error object:", error);

        let errorMessage = 'Неизвестная ошибка при генерации игры за баллы';
        if (error.response) {
          console.error("Server responded with error status:", error.response.status);
          console.error("Error response data:", error.response.data);
          errorMessage = error.response.data?.detail || `Ошибка сервера: ${error.response.status}`;
        } else if (error.request) {
          console.error("No response received. Network error or timeout?");
          errorMessage = 'Сетевая ошибка или таймаут при запросе игры за баллы.';
        } else {
          console.error("Error setting up request:", error.message);
          errorMessage = `Ошибка настройки запроса: ${error.message}`;
        }
        console.error("Final error message set:", errorMessage);
        this.error = errorMessage;
        return null; // Возвращаем null в случае ошибки
      }
    },
    // --- КОНЕЦ ДЕЙСТВИЯ ДЛЯ ИГРЫ ЗА БАЛЛЫ ---

    /** @deprecated Используйте fetchGeneratedExercises */
    async generateLessonExercises(lessonData: LessonData) {
      console.warn("Вызвано устаревшее действие generateLessonExercises. Используйте fetchGeneratedExercises.");
      this.isLoading = true
      try {
        // Старый вызов через сервис материалов
        const materials = await courseGeneratorService.generateLessonMaterials(
          lessonData.id as number,
          ['exercises']
        )

        // Обновляем материалы урока в текущем курсе
        if (this.currentCourse) {
          const lessonIndex = this.currentCourse.lessons.findIndex(l => l.id === lessonData.id)
          if (lessonIndex >= 0) {
            this.currentCourse.lessons[lessonIndex].materials = [
              ...this.currentCourse.lessons[lessonIndex].materials,
              ...materials.exercises
            ]
          }
        }

        return materials
      } catch (error) {
        this.error = 'Ошибка при генерации упражнений'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async exportCourse(courseId: number, format: 'pdf' | 'docx') {
      this.isLoading = true
      try {
        const blob = await courseGeneratorService.exportCourse(courseId, format)

        // Создаем ссылку для скачивания файла
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `course_${courseId}.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)

        return true
      } catch (error) {
        this.error = 'Ошибка при экспорте курса'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async loadCourses() {
      this.isLoading = true
      try {
        const courses = await courseGeneratorService.getCourses()
        this.courses = courses
        return courses
      } catch (error) {
        this.error = 'Ошибка при загрузке курсов'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async loadCourse(courseId: number) {
      this.isLoading = true
      try {
        const course = await courseGeneratorService.getCourseDetails(courseId)
        this.currentCourse = course
        return course
      } catch (error) {
        this.error = 'Ошибка при загрузке курса'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async deleteCourse(courseId: number) {
      this.isLoading = true
      try {
        await courseGeneratorService.deleteCourse(courseId)

        // Удаляем курс из списка
        this.courses = this.courses.filter(c => c.id !== courseId)

        // Если удаляемый курс был текущим, сбрасываем текущий курс
        if (this.currentCourse && this.currentCourse.id === courseId) {
          this.currentCourse = null
        }

        return true
      } catch (error) {
        this.error = 'Ошибка при удалении курса'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    // --- ДЕЙСТВИЕ ДЛЯ ДОБАВЛЕНИЯ НОВЫХ УРОКОВ В СОСТОЯНИЕ ---
    appendLessons(courseId: number, newLessons: Lesson[]) {
      // Находим курс в массиве courses или используем currentCourse
      const courseRef = this.currentCourse?.id === courseId
        ? this.currentCourse
        : this.courses.find(c => c.id === courseId);

      if (courseRef) {
        // Убедимся, что добавляем только уникальные уроки (на всякий случай)
        const existingLessonIds = new Set(courseRef.lessons.map(l => l.id));
        const lessonsToAdd = newLessons.filter(nl => !existingLessonIds.has(nl.id));

        if (lessonsToAdd.length > 0) {
          courseRef.lessons.push(...lessonsToAdd);
          console.log(`Добавлено ${lessonsToAdd.length} новых уроков в курс ${courseId}`);
        } else {
          console.log(`Новые уроки для курса ${courseId} уже присутствуют.`);
        }
      } else {
        console.warn(`Курс с ID ${courseId} не найден в store для добавления уроков.`);
        // Возможно, стоит загрузить курс, если его нет?
        // this.loadCourse(courseId).then(() => this.appendLessons(courseId, newLessons));
      }
    },
    // --- КОНЕЦ ДЕЙСТВИЯ appendLessons ---

    // --- ДЕЙСТВИЕ ДЛЯ ЗАГРУЗКИ СЛЕДУЮЩЕЙ ЧАСТИ УРОКОВ ---
    async loadNextLessonsBatch(courseId: number) {
      // Получаем текущее количество уроков из состояния
      const course = this.currentCourse?.id === courseId
        ? this.currentCourse
        : this.courses.find(c => c.id === courseId);

      if (!course) {
        const errorMsg = `Курс с ID ${courseId} не найден в store.`;
        this.error = errorMsg;
        // toastService.error(errorMsg); // Предполагаем, что toastService импортирован
        console.error(errorMsg); // Используем console.error если toastService не доступен глобально
        throw new Error(errorMsg);
      }
      const currentLessonCount = course.lessons.length;

      // Получаем user ID из useMainStore (предполагается, что он импортирован)
      // import { useMainStore } from './index'; // Добавить импорт вверху файла
      const mainStore = useMainStore();
      if (!mainStore.user) {
         const errorMsg = 'Пользователь не авторизован';
         this.error = errorMsg;
         // toastService.error(errorMsg);
         console.error(errorMsg);
         throw new Error(errorMsg);
      }

      this.isLoading = true;
      this.error = null;
      try {
        console.log(`Запрос на бэкенд: /api/v1/courses/${courseId}/lessons/next_batch`, { current_lesson_count: currentLessonCount });

        // Вызываем API endpoint
        // import { apiClient } from '@/api'; // Добавить импорт вверху файла
        const response = await apiClient.post(`/api/v1/courses/${courseId}/lessons/next_batch`, {
          current_lesson_count: currentLessonCount
        });

        // Проверяем структуру ответа перед типизацией
        const newLessons = (response.data && Array.isArray(response.data)) ? response.data as Lesson[] : [];

        if (newLessons.length > 0) {
          // Вызываем другое действие этого же стора для обновления состояния
          this.appendLessons(courseId, newLessons);
        } else {
          console.log("Больше уроков для загрузки нет или API вернул пустой список.");
          // toastService.info("Все уроки курса загружены.");
          console.info("Все уроки курса загружены."); // Используем console.info
        }

        return newLessons; // Возвращаем новые уроки

      } catch (error: any) { // Явно указываем тип any
        console.error('Ошибка при загрузке следующей части уроков:', error);
        const message = error?.response?.data?.detail || error?.message || 'Ошибка при загрузке уроков';
        this.error = message;
        // toastService.error(message);
        console.error(message);
        throw error; // Пробрасываем ошибку для обработки в компоненте
      } finally {
        this.isLoading = false;
      }
    },
    // --- КОНЕЦ ДЕЙСТВИЯ loadNextLessonsBatch ---

    // --- ДЕЙСТВИЕ ДЛЯ ЗАГРУЗКИ МАТЕРИАЛОВ УРОКА ---
    async generateLessonMaterials(lessonId: number, types: string[] = ["exercises", "presentation", "handouts"]) { // Добавляем параметр types
       const mainStore = useMainStore(); // Убедитесь, что useMainStore импортирован
       if (!mainStore.user) {
         const errorMsg = 'Пользователь не авторизован';
         this.error = errorMsg;
         // toastService.error(errorMsg);
         console.error(errorMsg);
         throw new Error(errorMsg);
       }

       this.isLoading = true;
       this.error = null;
       try {
         console.log(`Запрос на генерацию/загрузку материалов (${types.join(', ')}) для урока ${lessonId}`);

         // Вызываем API endpoint
         const response = await apiClient.get(`/api/v1/lessons/${lessonId}/materials`, {
           params: { types: types } // Передаем типы как query параметры
         });

         // TODO: Реализовать обработку ответа в зависимости от формата данных с бэкенда
         if (response.data) {
            console.log("Получены данные материалов:", response.data);
            // Пример обновления состояния:
            if (this.currentCourse) {
               const lessonIndex = this.currentCourse.lessons.findIndex(l => l.id === lessonId);
               if (lessonIndex !== -1) {
                  // Мержим новые материалы с существующими (если они есть)
                  // Добавляем поле generatedMaterials в интерфейс Lesson, если его нет
                  const existingMaterials = (this.currentCourse.lessons[lessonIndex] as any).generatedMaterials || {};
                  (this.currentCourse.lessons[lessonIndex] as any).generatedMaterials = { ...existingMaterials, ...response.data };
                  console.log(`Материалы добавлены/обновлены для урока ${lessonId}`);
               }
            }
            // toastService.success("Материалы для урока сгенерированы/получены.");
            console.info("Материалы для урока сгенерированы/получены.");
            return response.data; // Возвращаем полученные данные
         } else {
           throw new Error("Не получен ответ от сервера при запросе материалов.");
         }

       } catch (error: any) {
         console.error(`Ошибка при загрузке материалов для урока ${lessonId}:`, error);
         const message = error?.response?.data?.detail || error?.message || 'Ошибка при загрузке материалов';
         this.error = message;
         // toastService.error(message);
         console.error(message);
         throw error;
       } finally {
         this.isLoading = false;
       }
    }
    // --- КОНЕЦ ДЕЙСТВИЯ generateLessonMaterials ---

    // --- ОБНОВЛЕННОЕ ДЕЙСТВИЕ ДЛЯ ЭКСПОРТА КУРСА ---
    // async exportCourse(courseId: number, format: 'pdf' | 'docx') { ... }
    // Оставляем существующее действие exportCourse, т.к. оно уже использует courseGeneratorService,
    // который, вероятно, является оберткой над apiClient для экспорта.
    // Если нужно использовать apiClient напрямую, раскомментируйте и адаптируйте код ниже:
    /*
    async exportCourse(courseId: number, format: 'pdf' | 'docx') {
      const mainStore = useMainStore();
      if (!mainStore.user) {
         const errorMsg = 'Пользователь не авторизован';
         this.error = errorMsg;
         toastService.error(errorMsg);
         throw new Error(errorMsg);
      }

      this.isLoading = true;
      this.error = null;
      try {
        console.log(`Запрос на экспорт курса ${courseId} в формате ${format}`);

        const response = await apiClient.get(`/api/v1/courses/${courseId}/export`, {
          params: { format },
          responseType: 'blob' // Ожидаем файл
        });

        if (response.data) {
           const url = window.URL.createObjectURL(new Blob([response.data]));
           const link = document.createElement('a');
           const contentDisposition = response.headers['content-disposition'];
           let filename = `course_${courseId}.${format}`;
           if (contentDisposition) {
               const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
               if (filenameMatch && filenameMatch.length === 2) filename = filenameMatch[1];
           }
           link.href = url;
           link.setAttribute('download', filename);
           document.body.appendChild(link);
           link.click();
           link.remove();
           window.URL.revokeObjectURL(url);
           toastService.success(`Курс экспортируется в ${format}...`);
           return true; // Возвращаем успех

        } else {
          throw new Error("Не получен файл от сервера при экспорте курса.");
        }

      } catch (error: any) {
        console.error(`Ошибка при экспорте курса ${courseId} в ${format}:`, error);
        const message = error?.response?.data?.detail || error?.message || `Ошибка при экспорте в ${format}`;
        this.error = message;
        toastService.error(message);
        throw error;
      } finally {
        this.isLoading = false;
      }
    }
    */
    // --- КОНЕЦ ДЕЙСТВИЯ exportCourse ---
  }
})
