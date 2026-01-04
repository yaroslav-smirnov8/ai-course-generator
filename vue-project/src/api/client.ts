import axios from 'axios';
import type { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import type { CourseFormData } from '@/types/course';
import type { GenerationRequest } from '@/types';
import type { ContentType } from '@/core/constants';
import { API_ENDPOINTS } from './endpoints';

export class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'https://aiteachers-api.ru.tuna.am',
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        if (config.method?.toLowerCase() === 'options') {
          console.log('OPTIONS request - skipping auth header');
          return config;
        }

        const webApp = window.Telegram?.WebApp;
        const webAppData = webApp?.initData;

        // Не переопределяем baseURL, так как он уже установлен в конструкторе
        // config.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        config.withCredentials = true;

        // Подробное логирование для отладки
        console.log('API Client - setupInterceptors:', {
          webApp: webApp ? 'доступен' : 'недоступен',
          webAppData: webAppData ? 'данные есть' : 'данных нет',
          webAppInitDataUnsafe: webApp?.initDataUnsafe ? 'данные есть' : 'данных нет',
          webAppUser: webApp?.initDataUnsafe?.user ? 'пользователь есть' : 'пользователя нет'
        });

        if (webAppData) {
          config.headers['Authorization'] = `tma ${webAppData}`;
          console.log('Setting Authorization header:', `tma ${webAppData.substring(0, 20)}...`);
        } else {
          console.warn('No WebApp data available');

          // Проверяем, есть ли данные в localStorage
          const storedWebAppData = localStorage.getItem('tg_web_app_data');
          if (storedWebAppData) {
            console.log('Using stored WebApp data from localStorage');
            config.headers['Authorization'] = `tma ${storedWebAppData}`;
          }
        }

        console.log('Request config:', {
          method: config.method,
          url: config.url,
          headers: {
            ...config.headers,
            Authorization: config.headers['Authorization'] ?
              `${config.headers['Authorization'].substring(0, 20)}...` : 'not set'
          },
          withCredentials: config.withCredentials
        });

        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log('Response received:', {
          status: response.status,
          headers: response.headers,
          data: response.data
        });
        return response;
      },
      async (error: AxiosError) => {
        // Логируем детали ошибки
        console.error('Response error:', {
          status: error.response?.status,
          data: error.response?.data,
          headers: error.response?.headers,
          error: error
        });

        if (error.response?.status === 401) {
          // Показываем сообщение в Telegram
          if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.showAlert('Session expired. Please reopen the app.');
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Базовые HTTP методы
  async get<T = any>(url: string, params?: any): Promise<T> {
    try {
      console.log('Making GET request to:', url, 'with params:', params);

      // Проверяем, запрашивается ли blob
      const isBlob = params && params.responseType === 'blob';

      let response;
      // Проверяем, что params - это объект с параметрами, а не объект с опциями axios
      if (params && !params.params && !params.headers && !params.responseType) {
        response = await this.client.get<T>(url, { params });
      } else {
        response = await this.client.get<T>(url, params);
      }

      // Подробное логирование ответа
      console.log('GET Response received:', response);
      console.log('GET Response data type:', typeof response.data);
      console.log('GET Response data:', response.data);

      // Дополнительное логирование для отладки
      console.log('GET Response status:', response.status);
      console.log('GET Response headers:', response.headers);

      // Для всех запросов добавляем подробное логирование
      console.log('=== DETAILED API RESPONSE DEBUG ===');
      console.log('URL:', url);
      console.log('Raw response object:', JSON.stringify(response));
      console.log('Response data stringified:', JSON.stringify(response.data));

      // Если это запрос к /api/v1/users/, добавляем еще больше логов
      if (url.includes('/api/v1/users/') && !url.includes('/me')) {
        console.log('=== USERS API RESPONSE DEBUG ===');

        if (response.data && response.data.items) {
          console.log('Items in response:', response.data.items);
          console.log('Items type:', typeof response.data.items);
          console.log('Is items array:', Array.isArray(response.data.items));
          console.log('Items length:', response.data.items.length);
          if (response.data.items.length > 0) {
            console.log('First item:', JSON.stringify(response.data.items[0]));
          }
        } else {
          console.log('No items field in response data');
          console.log('Response data keys:', Object.keys(response.data));

          // Проверяем, может быть ответ сам по себе является массивом
          if (Array.isArray(response.data)) {
            console.log('Response data is an array with length:', response.data.length);
            if (response.data.length > 0) {
              console.log('First item in array:', JSON.stringify(response.data[0]));
            }
          }
        }
      }

      // Проверка на пустой ответ
      if (response.data === undefined || response.data === null) {
        console.warn('GET Response data is empty or undefined');
      } else if (typeof response.data === 'object' && Object.keys(response.data).length === 0) {
        console.warn('GET Response data is an empty object');
      }

      // Проверка на наличие данных в ответе
      if (Array.isArray(response.data)) {
        console.log('GET Response data is an array with length:', response.data.length);
      } else if (typeof response.data === 'object' && response.data !== null) {
        console.log('GET Response data is an object with keys:', Object.keys(response.data));
      }

      // Если запрашивается blob, возвращаем весь ответ, а не только data
      if (isBlob) {
        return response as unknown as T;
      }

      // Проверяем, что ответ содержит данные
      if (response && response.data) {
        console.log('=== API CLIENT RETURN DEBUG ===');
        console.log('Returning response.data:', response.data);
        console.log('URL:', url);

        // Для запросов к /api/v1/users/ проверяем, что ответ содержит items
        if (url.includes('/api/v1/users/') && !url.includes('/me')) {
          console.log('Processing users API response');

          // Если ответ содержит items, возвращаем их
          if (response.data.items && Array.isArray(response.data.items)) {
            console.log('Returning items from response:', response.data.items);
            console.log('Items length:', response.data.items.length);
            console.log('First item:', response.data.items[0]);

            // Проверяем, что items содержат все необходимые поля
            if (response.data.items.length > 0) {
              const firstItem = response.data.items[0];
              console.log('First item has id:', firstItem.id);
              console.log('First item has telegram_id:', firstItem.telegram_id);
              console.log('First item has first_name:', firstItem.first_name);
              console.log('First item has role:', firstItem.role);
            }

            return response.data.items as unknown as T;
          } else {
            console.log('No items in response, returning full response.data');
            return response.data;
          }
        } else {
          // Для других запросов возвращаем response.data как есть
          return response.data;
        }
      } else if (response && response.status >= 200 && response.status < 300) {
        // Если ответ успешный, но не содержит данных или содержит пустой объект
        console.log('GET request successful but no data returned, status:', response.status);

        // Проверяем URL запроса, чтобы вернуть правильный тип данных
        if (url.includes('/api/v1/users/') && !url.includes('/me')) {
          console.log('GET request to users endpoint, returning empty array');
          return [] as unknown as T;
        } else {
          console.log('GET request successful but no data returned, returning empty object');
          return {} as T;
        }
      } else {
        // Если ответ не успешный, выбрасываем ошибку
        throw new Error(`GET request failed with status ${response?.status}`);
      }
    } catch (error) {
      console.error('Error in GET request:', error);
      throw error;
    }
  }

  async post<T = any>(url: string, data?: any): Promise<T> {
    try {
      const response = await this.client.post<T>(url, data);
      console.log('POST Response received:', response);

      // Проверяем, что ответ содержит данные
      if (response && response.data && Object.keys(response.data).length > 0) {
        return response.data;
      } else if (response && response.status >= 200 && response.status < 300) {
        // Если ответ успешный, но не содержит данных или содержит пустой объект, возвращаем пустой объект
        console.log('POST request successful but no data returned, status:', response.status);
        return {} as T;
      } else {
        // Если ответ не успешный, выбрасываем ошибку
        throw new Error(`POST request failed with status ${response?.status}`);
      }
    } catch (error) {
      console.error('Error in POST request:', error);
      throw error;
    }
  }

  async put<T = any>(url: string, data?: any): Promise<T> {
    try {
      const response = await this.client.put<T>(url, data);
      console.log('Response received:', response);

      // Проверяем, что ответ содержит данные
      if (response && response.data && Object.keys(response.data).length > 0) {
        return response.data;
      } else if (response && response.status >= 200 && response.status < 300) {
        // Если ответ успешный, но не содержит данных или содержит пустой объект, возвращаем пустой объект
        console.log('PUT request successful but no data returned, status:', response.status);
        return {} as T;
      } else {
        // Если ответ не успешный, выбрасываем ошибку
        throw new Error(`PUT request failed with status ${response?.status}`);
      }
    } catch (error) {
      console.error('Error in PUT request:', error);
      throw error;
    }
  }

  async delete<T = any>(url: string): Promise<T> {
    try {
      const response = await this.client.delete<T>(url);
      console.log('DELETE Response received:', response);

      // Проверяем, что ответ содержит данные
      if (response && response.data && Object.keys(response.data).length > 0) {
        return response.data;
      } else if (response && response.status >= 200 && response.status < 300) {
        // Если ответ успешный, но не содержит данных или содержит пустой объект, возвращаем пустой объект
        console.log('DELETE request successful but no data returned, status:', response.status);
        return {} as T;
      } else {
        // Если ответ не успешный, выбрасываем ошибку
        throw new Error(`DELETE request failed with status ${response?.status}`);
      }
    } catch (error) {
      console.error('Error in DELETE request:', error);
      throw error;
    }
  }

  // API методы
  // Аутентификация
  async authenticateTelegram(telegramData: any) {
    return this.post('/api/v1/auth/telegram', telegramData);
  }

  // Пользователи
  async getCurrentUser() {
    return this.get('/api/v1/users/me');
  }

  async getUserStats() {
    return this.get('/api/v1/users/stats');
  }

  async saveUserSettings(settings: any) {
    return this.post('/api/v1/users/settings', settings);
  }

  // Генерация контента
  async generateLessonPlan(data: GenerationRequest) {
    return this.post('/api/v1/content/generate_lesson_plan', data);
  }

  async detailLessonPlan(data: GenerationRequest) {
    return this.post(API_ENDPOINTS.DETAIL_LESSON_PLAN, data);
  }

  async generateExercises(data: GenerationRequest) {
    return this.post('/api/v1/content/generate_exercises', data);
  }

  async generateGame(data: GenerationRequest) {
    return this.post('/api/v1/content/generate_game', data);
  }

  async generateImage(data: GenerationRequest) {
    return this.post('/api/v1/content/generate_image', data);
  }

  async processVideoTranscript(data: any) {
    console.log('API Client: Отправка запроса на получение транскрипта видео:', data);
    const response = await this.post(API_ENDPOINTS.PROCESS_TRANSCRIPT, data);
    console.log('API Client: Получен ответ:', response);
    return response;
  }

  async generateConceptExplanation(data: any) {
    console.log('API Client: Отправка запроса на генерацию объяснения концепции:', data);
    const response = await this.post(API_ENDPOINTS.GENERATE_CONCEPT_EXPLANATION, data);
    console.log('API Client: Получен ответ:', response);
    return response;
  }

  // Text Analyzer методы
  async detectTextLevel(data: any) {
    return this.post(API_ENDPOINTS.DETECT_TEXT_LEVEL, data);
  }

  async regenerateText(data: any) {
    return this.post(API_ENDPOINTS.REGENERATE_TEXT, data);
  }

  async changeTextLevel(data: any) {
    return this.post(API_ENDPOINTS.CHANGE_TEXT_LEVEL, data);
  }

  async generateQuestions(data: any) {
    return this.post(API_ENDPOINTS.GENERATE_QUESTIONS, data);
  }

  async generateSummary(data: any) {
    return this.post(API_ENDPOINTS.GENERATE_SUMMARY, data);
  }

  async generateTitles(data: any) {
    return this.post(API_ENDPOINTS.GENERATE_TITLES, data);
  }

  async generateComprehensionTest(data: any) {
    return this.post(API_ENDPOINTS.GENERATE_COMPREHENSION_TEST, data);
  }

  // Курсы
  async createCourse(data: CourseFormData) {
    return this.post('/api/v1/courses', data);
  }

  async getCourse(id: number) {
    return this.get(`/api/v1/courses/${id}`);
  }

  async updateCourse(id: number, data: Partial<CourseFormData>) {
    return this.put(`/api/v1/courses/${id}`, data);
  }

  // Реферальная система
  async useReferralCode(code: string) {
    return this.post(`/api/v1/users/invite/${code}`);
  }

  async getReferralLink() {
    return this.get('/api/v1/users/referral');
  }

  async getReferralStats() {
    return this.get('/api/v1/referral/stats');
  }

  // Аналитика
  async getFeatureAnalytics(period: string = 'week') {
    return this.get(`/api/v1/admin/analytics/features?period=${period}`);
  }

  async getGenerationStats(type?: ContentType) {
    const params = type ? { type } : undefined;
    return this.get('/api/v1/analytics/generations', { params });
  }

  async getPointsAnalytics(params: Record<string, any> = {}) {
    console.log('API Client: Запрос аналитики баллов с параметрами:', params);
    return this.get(API_ENDPOINTS.ANALYTICS_POINTS, { params });
  }

  async getTariffsAnalytics(params: Record<string, any> = {}) {
    console.log('API Client: Запрос аналитики тарифов с параметрами:', params);
    return this.get(API_ENDPOINTS.ANALYTICS_TARIFFS, { params });
  }

  async getAchievementsAnalytics(params: Record<string, any> = {}) {
    console.log('API Client: Запрос аналитики достижений с параметрами:', params);
    return this.get(API_ENDPOINTS.ANALYTICS_ACHIEVEMENTS, { params });
  }

  // Логирование переходов по ссылкам
  async logLinkClick(data: {
    link_id: string;
    link_title: string;
    link_url: string;
    user_id: number | null;
  }) {
    console.log('API Client: Логирование перехода по ссылке:', data);
    return this.post(API_ENDPOINTS.LOG_LINK_CLICK, data);
  }

  // Получение аналитики по переходам по ссылкам
  async getLinksAnalytics(params: Record<string, any> = {}) {
    console.log('API Client: Запрос аналитики переходов по ссылкам с параметрами:', params);
    console.log('API Client: URL запроса:', API_ENDPOINTS.ANALYTICS_LINKS);

    try {
      const response = await this.get(API_ENDPOINTS.ANALYTICS_LINKS, { params });
      console.log('API Client: Получен ответ от сервера:', response);
      return response;
    } catch (error) {
      console.error('API Client: Ошибка при получении аналитики переходов:', error);
      console.error('API Client: Детали ошибки:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      throw error;
    }
  }

  // Администрирование
  async exportData(type: string, format: 'csv' | 'json' = 'csv') {
    return this.get(`/api/v1/admin/export/${type}`, {
      params: { format },
      responseType: 'blob'
    });
  }

  async getDashboardData() {
    return this.get('/api/v1/admin/dashboard');
  }

  async getSystemSettings() {
    return this.get('/api/v1/admin/settings');
  }

  async updateSystemSettings(settings: any) {
    return this.put('/api/v1/admin/settings', settings);
  }

  async getUserTariff(userId: number) {
    return this.get(API_ENDPOINTS.USERS_TARIFF(userId));
  }

  async getUserUsageStats(userId: number) {
    return this.get(API_ENDPOINTS.USERS_USAGE_STATS(userId));
  }

  async resetUsageCounters(userId: number) {
    return this.post(API_ENDPOINTS.USERS_RESET_COUNTERS(userId));
  }

  getUserStatistics(userId: number) {
    return this.get(API_ENDPOINTS.USER_STATISTICS, { params: { user_id: userId } });
  }
}

// Создаем и экспортируем единый экземпляр клиента
export const apiClient = new ApiClient();

// Для обратной совместимости экспортируем методы напрямую
export const api = {
  // Auth
  authenticateTelegram: apiClient.authenticateTelegram.bind(apiClient),

  // Users
  getCurrentUser: apiClient.getCurrentUser.bind(apiClient),
  getUserStats: apiClient.getUserStats.bind(apiClient),

  // Content generation
  generateLessonPlan: apiClient.generateLessonPlan.bind(apiClient),
  detailLessonPlan: apiClient.detailLessonPlan.bind(apiClient),
  generateExercises: apiClient.generateExercises.bind(apiClient),
  generateGame: apiClient.generateGame.bind(apiClient),
  generateImage: apiClient.generateImage.bind(apiClient),
  processVideoTranscript: apiClient.processVideoTranscript.bind(apiClient),
  generateConceptExplanation: apiClient.generateConceptExplanation.bind(apiClient),

  // Text Analyzer
  detectTextLevel: apiClient.detectTextLevel.bind(apiClient),
  regenerateText: apiClient.regenerateText.bind(apiClient),
  changeTextLevel: apiClient.changeTextLevel.bind(apiClient),
  generateQuestions: apiClient.generateQuestions.bind(apiClient),
  generateSummary: apiClient.generateSummary.bind(apiClient),
  generateTitles: apiClient.generateTitles.bind(apiClient),
  generateComprehensionTest: apiClient.generateComprehensionTest.bind(apiClient),

  // Courses
  createCourse: apiClient.createCourse.bind(apiClient),
  getCourse: apiClient.getCourse.bind(apiClient),
  updateCourse: apiClient.updateCourse.bind(apiClient),

  // Referral
  useReferralCode: apiClient.useReferralCode.bind(apiClient),
  getReferralLink: apiClient.getReferralLink.bind(apiClient),
  getReferralStats: apiClient.getReferralStats.bind(apiClient),

  // Analytics
  getFeatureAnalytics: apiClient.getFeatureAnalytics.bind(apiClient),
  getGenerationStats: apiClient.getGenerationStats.bind(apiClient),
  getPointsAnalytics: apiClient.getPointsAnalytics.bind(apiClient),
  getTariffsAnalytics: apiClient.getTariffsAnalytics.bind(apiClient),
  getAchievementsAnalytics: apiClient.getAchievementsAnalytics.bind(apiClient),
  logLinkClick: apiClient.logLinkClick.bind(apiClient),
  getLinksAnalytics: apiClient.getLinksAnalytics.bind(apiClient),

  // Admin
  exportData: apiClient.exportData.bind(apiClient),
  getDashboardData: apiClient.getDashboardData.bind(apiClient),
  getSystemSettings: apiClient.getSystemSettings.bind(apiClient),
  updateSystemSettings: apiClient.updateSystemSettings.bind(apiClient),

  getUserTariff: apiClient.getUserTariff.bind(apiClient),
  getUserUsageStats: apiClient.getUserUsageStats.bind(apiClient),
  getUserStatistics: apiClient.getUserStatistics.bind(apiClient),
};

export type { AxiosInstance, AxiosResponse, AxiosError };
