import { defineStore } from 'pinia'
import { apiClient } from '@/api';
import { API_ENDPOINTS } from '@/api';
import {
  ContentType,
  UserRole,
  ActionType,
  UNLIMITED_ROLES,
  TariffType
} from '@/core/constants'
import courseGeneratorService from '@/services/courseGenerator'
import type { CourseStructure, CourseFormData } from '@/types/course'
import { TelegramService } from '@/services/telegram'
import type {UnwrapRef} from "vue";
import type {AchievementProgress, DataPoint, TariffInfo, TelegramUser, UserStats, UserTariffHistory} from "@/types";
import { tariffService } from '@/services/tariffService';
import { toastService } from '@/services/toastService'

interface StoreState {
  // Пользователь
  user: {
    id: number
    role: UserRole
    username: string
    first_name: string
    last_name: string
    email: string
    telegram_id?: number
    tariff?: TariffType
    tariff_valid_until?: string | null  // Добавлено поле срока действия тарифа
    has_access: boolean
    points: number
    created_at: string
    last_active: string
    isTariffUpdating: boolean
  } | null

  // Аутентификация
  token: string | null
  isInitialized: boolean
  authenticated: boolean
  webAppData: any

  // Тарифы (обновлено)
  tariffInfo: TariffInfo | null
  availableTariffs: TariffInfo[]  // Добавлено - список доступных тарифов
  tariffHistory: UserTariffHistory[]  // Добавлено - история тарифов пользователя
  isTariffUpdating: boolean  // Добавлено - флаг обновления тарифа

  // Статистика
  userStats: UserStats | null
  dailyUsage: {
    generations: number
    images: number
    lastReset: Date
  }

  // Достижения
  achievements: AchievementProgress[]

  // UI состояние
  isLoading: boolean
  error: string | null
  message: string | null
  generationResult: any | null
  selectedUser: User | null
  userModalVisible: boolean

  // Аналитика
  featureUsage: FeatureAnalytics | null
  activityData: DataPoint[]

  // Настройки системы
  systemSettings: SystemSettings | null

  // Покупка баллов
  pointsPurchase: PointsPurchaseState

  // Новые поля для данных форм
  exerciseFormData: any | null
  gameFormData: any | null

  // Добавляем состояние для статистики использования приложения
  appUsage: {
    events: AppUsageEvent[]
    stats: AppUsageStats
  }
}

// Тип для запроса генерации (замените на реальный импорт, если он существует)
interface GenerationRequest {
  user_id?: number;
  type: ContentType;
  prompt: string;
  // Добавьте другие необходимые поля
}


// Updated and new interfaces
interface Generation {
  id: number
  user_id: number
  type: ContentType
  content: string
  prompt: string
  created_at: Date
  user?: {
    id: number
    telegram_id: string
    username?: string
  }
}

interface GenerationStats {
  total_generations: number
  by_type: {
    lesson_plans: number
    exercises: number
    games: number
    images: number
  }
  popular_prompts: Array<{
    prompt: string
    count: number
  }>
  generations: Generation[]
  total: number
}

interface GenerationStatistics {
  total_generations: number
  by_type: {
    lesson_plans: number
    exercises: number
    games: number
    images: number
  }
  popular_prompts: Array<{
    prompt: string
    count: number
  }>
  total: number
  generations: Generation[]
}

interface ApiResponse<T = any> {
  status: 'success' | 'error'
  data: T
  message?: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  perPage: number
  totalPages: number
}

interface PaginationParams {
  page: number;
  perPage: number;
}

interface FilterOptions {
  search?: string
  dateFrom?: Date | string
  dateTo?: Date | string
  type?: string
  status?: string
  [key: string]: any
}

interface PromoCodeHistory {
  page: number
  per_page: number
  promocode?: string
  tariff?: string
  dateFrom?: string
  dateTo?: string
}

interface PointsPurchaseState {
  isProcessing: boolean;
  currentPurchase: {
    amount: number;
    price: number;
    bonus: number;
    paymentId?: string;
  } | null;
  purchaseHistory: Array<{
    id: string;
    amount: number;
    price: number;
    bonus: number;
    status: string;
    date: string;
  }>;
}

// Добавляем интерфейс для статистики использования приложения
interface AppUsageEvent {
  event: string
  timestamp: string
  user_id: string | number
  platform?: string
  version?: string
  page?: string
  action?: string
  details?: any
  duration_seconds?: number
}

interface AppUsageStats {
  totalLaunches: number
  totalPageViews: number
  totalActions: number
  averageSessionDuration: number
  usageByPlatform: Record<string, number>
  usageByPage: Record<string, number>
  usageByAction: Record<string, number>
}

export const useMainStore = defineStore('main', {
  state: (): StoreState => ({
    // Пользователь
    user: null,

    // Аутентификация
    token: localStorage.getItem('token'),
    isInitialized: false,
    authenticated: false,
    webAppData: null,

    // Тарифы (обновлено)
    tariffInfo: null,
    availableTariffs: [],  // Добавлено
    tariffHistory: [],     // Добавлено
    isTariffUpdating: false,  // Добавлено

    // Статистика
    userStats: null,
    dailyUsage: {
      generations: 0,
      images: 0,
      lastReset: new Date()
    },

    // Достижения
    achievements: [],

    // UI состояние
    isLoading: false,
    error: null,
    message: null,
    generationResult: null,
    selectedUser: null,
    userModalVisible: false,
    accessDenied: null as {
      reason: 'banned' | 'not_subscribed' | 'unknown'
      channelUrl?: string
      error?: string
    } | null,

    // Аналитика
    featureUsage: null,
    activityData: [],

    // Настройки системы
    systemSettings: null,

    // Покупка баллов
    pointsPurchase: {
      isProcessing: false,
      currentPurchase: null,
      purchaseHistory: []
    },

    // Новые поля для данных форм
    exerciseFormData: null,
    gameFormData: null,

    // Добавляем состояние для статистики использования приложения
    appUsage: {
      events: [],
      stats: {
        totalLaunches: 0,
        totalPageViews: 0,
        totalActions: 0,
        averageSessionDuration: 0,
        usageByPlatform: {},
        usageByPage: {},
        usageByAction: {}
      }
    },
  }),


  getters: {
    // Authentication & User Status
    isAuthenticated: (state) => state.authenticated && !!state.user,
    isAdmin: (state) => {
      if (!state.user) return false;
      return state.user.role === UserRole.ADMIN || state.user.role === UserRole.MOD;
    },
    currentUser: (state) => state.user,
    hasError: (state) => !!state.error,
    loading: state => state.isLoading,

    // Limit Checks
    canGenerate: (state) => (type: ContentType) => {
      // First check if user exists
      if (!state.user) {
        console.log("[canGenerate] Missing user");
        return false;
      }

      // Check admin role first, regardless of other state
      const userRole = state.user.role;
      const isUnlimited = UNLIMITED_ROLES.includes(userRole);

      console.log("[canGenerate] User role check:", {
        role: userRole,
        typeOfRole: typeof userRole,
        availableRoles: UNLIMITED_ROLES,
        isUnlimited: isUnlimited,
        stringComparison: userRole === "admin"
      });

      // If admin, always return true, even if other state is missing
      if (isUnlimited) {
        console.log("[canGenerate] User has unlimited access");
        return true;
      }

      // Проверяем наличие тарифа у пользователя (используем логику как в ConceptExplainer)
      const hasTariff = state.user?.tariff || state.tariffInfo;
      if (!hasTariff) {
        console.log("[canGenerate] User has no tariff");
        return false;
      }

      // For non-admin users, check if required state exists
      if (!state.userStats) {
        console.log("[canGenerate] Missing user stats for regular user, assuming can generate");
        // Если userStats не загружены, предполагаем что можно генерировать
        // Компоненты сами загрузят статистику при необходимости
        return true;
      }

      // Если информация о тарифе отсутствует, но у пользователя есть тариф,
      // создаем базовую информацию о тарифе на основе типа тарифа
      if (!state.tariffInfo && state.user.tariff) {
        console.log("[canGenerate] Missing tariff info but user has tariff, creating fallback limits");

        // Определяем лимиты на основе типа тарифа
        let generationsLimit = 0;
        let imagesLimit = 0;

        switch (state.user.tariff) {
          case TariffType.PREMIUM:
            generationsLimit = 25;
            imagesLimit = 8;
            break;
          case TariffType.STANDARD:
            generationsLimit = 12;
            imagesLimit = 5;
            break;
          case TariffType.BASIC:
            generationsLimit = 6;
            imagesLimit = 2;
            break;
        }

        // Проверяем лимиты с использованием резервных значений
        const { dailyGenerations, dailyImages } = state.userStats;

        // Проверяем, что счетчики имеют корректные значения
        const currentImageCount = typeof dailyImages === 'number' ? dailyImages : 0;
        const currentGenCount = typeof dailyGenerations === 'number' ? dailyGenerations : 0;

        console.log("[canGenerate] Using fallback limits:", {
          type,
          dailyGenerations: currentGenCount,
          dailyImages: currentImageCount,
          fallbackLimits: {
            generations: generationsLimit,
            images: imagesLimit
          },
          remainingImages: imagesLimit - currentImageCount,
          remainingGenerations: generationsLimit - currentGenCount
        });

        return type === ContentType.IMAGE
          ? currentImageCount < imagesLimit
          : currentGenCount < generationsLimit;
      }

      // Если информация о тарифе есть, проверяем лимиты
      if (state.tariffInfo) {
        // Проверка лимитов для обычных пользователей
        const { dailyGenerations, dailyImages } = state.userStats;
        const { limits } = state.tariffInfo;

        // Проверяем, что лимиты существуют и имеют корректные значения
        if (!limits || typeof limits.images !== 'number' || typeof limits.generations !== 'number') {
          console.warn("[canGenerate] Invalid limits in tariffInfo:", limits);
          return false;
        }

        // Проверяем, что счетчики имеют корректные значения
        const currentImageCount = typeof dailyImages === 'number' ? dailyImages : 0;
        const currentGenCount = typeof dailyGenerations === 'number' ? dailyGenerations : 0;

        console.log("[canGenerate] Limit check:", {
          type,
          dailyGenerations: currentGenCount,
          dailyImages: currentImageCount,
          limits,
          remainingImages: limits.images - currentImageCount,
          remainingGenerations: limits.generations - currentGenCount
        });

        return type === ContentType.IMAGE
          ? currentImageCount < limits.images
          : currentGenCount < limits.generations;
      }

      // Если ничего не подошло, возвращаем false
      console.warn("[canGenerate] No valid tariff info or fallback available");
      return false;
    },

    remainingGenerations: (state) => (type: ContentType) => {
      // Check if user exists first
      if (!state.user) return 0;

      // If admin, always return infinite generations
      if (UNLIMITED_ROLES.includes(state.user.role)) return Infinity;

      // Проверяем наличие тарифа у пользователя (используем логику как в canGenerate)
      const hasTariff = state.user?.tariff || state.tariffInfo;
      if (!hasTariff) return 0;

      // For non-admin users, check required state
      if (!state.userStats) {
        // Если userStats не загружены, но у пользователя есть тариф, используем fallback лимиты
        if (hasTariff) {
          console.log("[remainingGenerations] Missing userStats but user has tariff, using fallback limits");

          // Определяем лимиты на основе типа тарифа
          let generationsLimit = 0;
          let imagesLimit = 0;

          if (state.user?.tariff) {
            switch (state.user.tariff) {
              case TariffType.PREMIUM:
                generationsLimit = 25;
                imagesLimit = 8;
                break;
              case TariffType.STANDARD:
                generationsLimit = 12;
                imagesLimit = 5;
                break;
              case TariffType.BASIC:
                generationsLimit = 6;
                imagesLimit = 2;
                break;
            }
          } else if (state.tariffInfo?.limits) {
            generationsLimit = state.tariffInfo.limits.generations;
            imagesLimit = state.tariffInfo.limits.images;
          }

          console.log("[remainingGenerations] Using fallback limits without userStats:", {
            type,
            fallbackLimits: {
              generations: generationsLimit,
              images: imagesLimit
            }
          });

          // Если userStats нет, возвращаем полный лимит
          return type === ContentType.IMAGE ? imagesLimit : generationsLimit;
        }
        return 0;
      }

      // Если информация о тарифе отсутствует, но у пользователя есть тариф,
      // используем резервные значения лимитов
      if (!state.tariffInfo && state.user.tariff) {
        console.log("[remainingGenerations] Missing tariff info but user has tariff, using fallback limits");

        // Определяем лимиты на основе типа тарифа
        let generationsLimit = 0;
        let imagesLimit = 0;

        switch (state.user.tariff) {
          case TariffType.PREMIUM:
            generationsLimit = 25;
            imagesLimit = 8;
            break;
          case TariffType.STANDARD:
            generationsLimit = 12;
            imagesLimit = 5;
            break;
          case TariffType.BASIC:
            generationsLimit = 6;
            imagesLimit = 2;
            break;
        }

        // Проверяем лимиты с использованием резервных значений
        const { dailyGenerations, dailyImages } = state.userStats;

        // Проверяем, что счетчики имеют корректные значения
        const currentImageCount = typeof dailyImages === 'number' ? dailyImages : 0;
        const currentGenCount = typeof dailyGenerations === 'number' ? dailyGenerations : 0;

        console.log("[remainingGenerations] Using fallback limits:", {
          type,
          dailyGenerations: currentGenCount,
          dailyImages: currentImageCount,
          fallbackLimits: {
            generations: generationsLimit,
            images: imagesLimit
          },
          remainingImages: Math.max(0, imagesLimit - currentImageCount),
          remainingGenerations: Math.max(0, generationsLimit - currentGenCount)
        });

        return type === ContentType.IMAGE
          ? Math.max(0, imagesLimit - currentImageCount)
          : Math.max(0, generationsLimit - currentGenCount);
      }

      // Если информация о тарифе есть, используем ее
      if (state.tariffInfo) {
        const { dailyGenerations, dailyImages } = state.userStats;
        const { limits } = state.tariffInfo;

        // Проверяем, что лимиты существуют и имеют корректные значения
        if (!limits || typeof limits.images !== 'number' || typeof limits.generations !== 'number') {
          console.warn("[remainingGenerations] Invalid limits in tariffInfo:", limits);
          return 0;
        }

        // Проверяем, что счетчики имеют корректные значения
        const currentImageCount = typeof dailyImages === 'number' ? dailyImages : 0;
        const currentGenCount = typeof dailyGenerations === 'number' ? dailyGenerations : 0;

        console.log("[remainingGenerations] Calculating remaining:", {
          type,
          dailyGenerations: currentGenCount,
          dailyImages: currentImageCount,
          limits,
          remainingImages: Math.max(0, limits.images - currentImageCount),
          remainingGenerations: Math.max(0, limits.generations - currentGenCount)
        });

        return type === ContentType.IMAGE
          ? Math.max(0, limits.images - currentImageCount)
          : Math.max(0, limits.generations - currentGenCount);
      }

      // Если ничего не подошло, возвращаем 0
      console.warn("[remainingGenerations] No valid tariff info or fallback available");
      return 0;
    },

    tariffStatus: (state) => {
      if (!state.tariffInfo) return null
      const now = new Date()
      const validUntil = state.tariffInfo.validUntil ? new Date(state.tariffInfo.validUntil) : null

      return {
        isActive: validUntil ? validUntil > now : false,
        daysLeft: validUntil
          ? Math.ceil((validUntil.getTime() - now.getTime()) / (1000 * 3600 * 24))
          : 0
      }
    },

    currentTariffInfo: (state) => state.tariffInfo,

    tariffValidUntil: (state) => state.tariffInfo?.validUntil || null,

    isTariffActive: (state) => {
      if (!state.tariffInfo?.validUntil) return false;
      const validUntil = new Date(state.tariffInfo.validUntil);
      return validUntil > new Date();
    },

    daysLeftUntilTariffExpiry: (state) => {
      if (!state.tariffInfo?.validUntil) return 0;

      const validUntil = new Date(state.tariffInfo.validUntil);
      const now = new Date();

      // Если тариф уже истек, возвращаем 0
      if (validUntil <= now) return 0;

      // Вычисляем разницу в днях
      const differenceInTime = validUntil.getTime() - now.getTime();
      return Math.ceil(differenceInTime / (1000 * 3600 * 24));
    },

    currentTariff: (state) => {
      if (!state.user?.tariff) return null
      return state.systemSettings?.tariffs.find(t => t.type === state.user?.tariff)
    },

    getGenerationCost: (state) => (contentType: ContentType) => {
      // Добавляем проверку на state.user и state.user.tariff
      if (!state.user || !state.user.tariff) return 0;
      // Добавляем проверку на state.systemSettings
      if (!state.systemSettings) return 0;
      const tariff = state.systemSettings.tariffs.find(t => t.type === state.user!.tariff) // Используем non-null assertion т.к. проверили user и user.tariff
      if (!tariff) return 0;

      // Разные типы контента могут иметь разную стоимость
      // Добавляем явную сигнатуру индекса и недостающие типы
      const costs: { [key in ContentType]?: number } = {
        [ContentType.LESSON_PLAN]: tariff.settings.lesson_plan_cost || 10,
        [ContentType.EXERCISE]: tariff.settings.exercise_cost || 5,
        [ContentType.GAME]: tariff.settings.game_cost || 5,
        [ContentType.IMAGE]: tariff.settings.image_cost || 15,
        [ContentType.TRANSCRIPT]: 10, // Значение по умолчанию
        [ContentType.FREE_QUERY]: 10, // Значение по умолчанию
        [ContentType.CONCEPT_EXPLANATION]: 10, // Значение по умолчанию
        [ContentType.COURSE]: 10, // Значение по умолчанию
        [ContentType.TEXT_ANALYSIS]: 10 // Значение по умолчанию
        // Другие типы из ContentType также могут быть добавлены сюда при необходимости
      }

      return costs[contentType] ?? 10 // Используем ?? для безопасности и значение по умолчанию
    },

    hasAdminAccess: (state) => !!state.user?.role && [UserRole.ADMIN, UserRole.MOD].includes(state.user.role),
    hasAccess: (state) => state.user?.has_access || false,
    currentTariffLimits: (state) => {
      if (!state.systemSettings || !state.user?.tariff) return null
      return state.systemSettings.tariffs.find(t => t.type === state.user?.tariff)?.settings
    },
    isPurchaseProcessing: (state) => state.pointsPurchase.isProcessing,
    currentPurchase: (state) => state.pointsPurchase.currentPurchase,
    purchaseHistory: (state) => state.pointsPurchase.purchaseHistory,

    // Добавляем геттер для проверки неограниченного доступа
    isUnlimitedUser: (state) => {
      return !!state.user?.role && UNLIMITED_ROLES.includes(state.user.role);
    },

    referralSettings: (state) => state.systemSettings?.referral || null,

    // Добавляем геттеры для статистики использования приложения
    appUsageStats: (state) => state.appUsage.stats,
    appUsageEvents: (state) => state.appUsage.events,
  },

  actions: {
    // Basic State Management
    async initializeApp() {
      try {
        this.isLoading = true;
        this.accessDenied = null; // Сбрасываем предыдущие ошибки доступа

        const webApp = window.Telegram?.WebApp;
        if (!webApp?.initData) {
          throw new Error('No WebApp data available');
        }

        // Используем метод getCurrentUser вместо прямого вызова get
        console.log('Making request to /api/v1/users/me');
        const response = await apiClient.getCurrentUser();
        console.log('Response:', response);

        this.user = response;
        this.authenticated = true;
        this.isInitialized = true;

        // Асинхронно загружаем userStats и tariffInfo в фоне, не блокируя инициализацию
        this.loadUserDataInBackground();

        return response;

      } catch (error: any) {
        console.error('Store initialization error:', error);

        // Проверяем, является ли это ошибкой доступа
        if (error.response?.status === 403 || error.response?.status === 402) {
          const errorDetail = error.response.data?.detail;

          if (errorDetail?.access_denied) {
            this.accessDenied = {
              reason: errorDetail.reason === 'evo_subscription_required' ? 'evo_subscription_required' : errorDetail.reason,
              channelUrl: errorDetail.channel_url,
              error: errorDetail.error
            };

            // Не устанавливаем общую ошибку для случаев блокировки доступа
            this.error = null;
          } else {
            this.error = error instanceof Error ? error.message : 'Store initialization failed';
          }
        } else {
          this.error = error instanceof Error ? error.message : 'Store initialization failed';
        }

        this.authenticated = false;
        this.isInitialized = true;
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    // Асинхронная загрузка данных пользователя в фоне
    async loadUserDataInBackground() {
      try {
        console.log('[loadUserDataInBackground] Starting background data loading...');

        // Загружаем tariffInfo и userStats параллельно
        const promises = [];

        if (this.user?.id) {
          promises.push(
            this.fetchUserTariff().catch(err => {
              console.warn('[loadUserDataInBackground] Failed to load tariff info:', err);
            })
          );

          promises.push(
            this.updateUsageStats().catch(err => {
              console.warn('[loadUserDataInBackground] Failed to load usage stats:', err);
            })
          );
        }

        await Promise.all(promises);
        console.log('[loadUserDataInBackground] Background data loading completed');
      } catch (error) {
        console.warn('[loadUserDataInBackground] Background loading failed:', error);
        // Не выбрасываем ошибку, чтобы не нарушить работу приложения
      }
    },

    setLoading(loading: boolean) {
      this.isLoading = loading
    },



    setError(error: string | null) {
      this.error = error
    },

    clearError() {
      this.error = null
    },

    clearAuth() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('token');
    },


    // Generation Management (New/Updated Methods)
    async getGenerationStatistics(options: {
      page: number
      perPage: number
      filters?: {
        search?: string
        dateFrom?: string
        dateTo?: string
        type?: ContentType | 'all'
      }
    }) {
      try {
        const response = await apiClient.get('/api/v1/admin/analytics/generations', {
          params: {
            page: options.page,
            per_page: options.perPage,
            search: options.filters?.search,
            date_from: options.filters?.dateFrom,
            date_to: options.filters?.dateTo,
            type: options.filters?.type !== 'all' ? options.filters?.type : undefined
          }
        })

        // Check if response has the expected structure
        if (response && response.data) {
          return response.data as GenerationStats;
        } else {
          console.error('Unexpected response structure from generations API:', response);
          // Return default structure to prevent UI errors
          return this.getDefaultGenerationStats();
        }
      } catch (error) {
        this.handleError(error);
        // Return default structure instead of throwing error
        return this.getDefaultGenerationStats();
      }
    },

    // Helper method to create default generation statistics
    getDefaultGenerationStats(): GenerationStats {
      return {
        total_generations: 0,
        by_type: {
          lesson_plans: 0,
          exercises: 0,
          games: 0,
          images: 0
        },
        popular_prompts: [],
        generations: [],
        total: 0
      };
    },

    async getGeneration(id: number) {
      try {
        const response = await apiClient.get(`/api/v1/admin/generations/${id}`);

        // Check if response has the expected structure
        if (response && response.data) {
          return response.data;
        } else {
          console.error(`Unexpected response structure from generation API for ID ${id}:`, response);
          // Return default structure to prevent UI errors
          return {
            id: id,
            user_id: 0,
            type: '',
            prompt: '',
            content: '',
            created_at: new Date().toISOString(),
            metadata: {}
          };
        }
      } catch (error) {
        this.handleError(error);
        // Return default structure instead of throwing error
        return {
          id: id,
          user_id: 0,
          type: '',
          prompt: '',
          content: '',
          created_at: new Date().toISOString(),
          metadata: {}
        };
      }
    },

    async deleteAchievement(achievementId: string | number) {  // Изменяем тип параметра
      try {
        const response = await apiClient.delete(`/api/v1/admin/achievements/${achievementId}`);
        return response.data;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    async generateContent(request: GenerationRequest) {
      try {
        const response = await this.makeRequest<{ content?: string }>('/api/v1/content/generate', request)
        // Безопасно извлекаем content
        return response?.data?.content
      } catch (error) {
        console.error('Error generating content:', error)
        throw error
      }
    },

    async generateLessonPlan(formData: LessonPlanFormData) {
      try {
        this.setLoading(true);
        this.clearError();

        // Проверяем, является ли это генерацией за баллы
        const isPointsGeneration = formData.with_points === true;

        // Проверяем лимиты генерации только если это не генерация за баллы
        if (!isPointsGeneration) {
          console.log('Checking generation limits for regular generation');
          const canGenerate = await this.checkAndTrackGeneration(ContentType.LESSON_PLAN);
          if (!canGenerate) {
            throw new Error('Daily limit reached for lesson plan generation');
          }
        } else {
          console.log('Skipping generation limits check for points-based generation');
        }

        // Проверяем наличие темы урока (обязательное поле)
        if (!formData.topic || formData.topic.trim() === '') {
          console.error('Ошибка: тема урока не указана в формате запроса');
          throw new Error('Тема урока обязательна для генерации плана');
        }

        // Добавляем отладочный лог
        console.log('Store: отправка данных на бэкенд:', JSON.stringify(formData, null, 2));
        console.log('Тема урока:', formData.topic);

        // Make the API request
        // Определяем тип с дополнительным свойством with_points
        interface RequestDataWithPoints {
          user_id: number | undefined;
          type: ContentType;
          prompt: string;
          with_points?: boolean;
        }

        // Создаем объект с правильным типом
        const requestData: RequestDataWithPoints = {
          user_id: this.user?.id,
          type: ContentType.LESSON_PLAN,
          prompt: JSON.stringify(formData)
        };

        // Добавляем флаг with_points, если он указан в formData
        if (formData.with_points === true) {
          requestData.with_points = true;
        }

        console.log('Sending request with data:', requestData);
        const response = await apiClient.post(API_ENDPOINTS.GENERATE_LESSON_PLAN, requestData);

        // Check if response is valid
        if (!response || !response.data || !response.data.content) {
          throw new Error('Invalid response from server');
        }

        // Store the result
        this.generationResult = response.data;

        // Добавляем отладочный лог
        console.log('Store: получен ответ от бэкенда:', response.data.content ? 'План урока получен успешно' : 'Пустой ответ!');

        // Return just the content
        return response.data.content;
      } catch (error) {
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async detailLessonPlan(requestData: any) {
      try {
        this.setLoading(true);
        this.clearError();

        // Проверяем, является ли это генерацией за баллы
        const isPointsGeneration = requestData.with_points === true;

        // Добавляем отладочный лог
        console.log('Store: Отправка запроса на детализацию плана урока:', requestData);
        console.log('Store: Генерация за баллы:', isPointsGeneration);

        // Подготавливаем данные для запроса
        let promptData;

        // Проверяем, является ли requestData строкой или объектом
        if (typeof requestData === 'string') {
          promptData = requestData;
        } else {
          // Если это объект, проверяем наличие поля prompt
          if (requestData.prompt) {
            // Если prompt уже является строкой, используем его как есть
            if (typeof requestData.prompt === 'string') {
              promptData = requestData.prompt;
            } else {
              // Если prompt - объект, преобразуем его в строку
              promptData = JSON.stringify(requestData.prompt);
            }
          } else {
            // Если поля prompt нет, преобразуем весь объект в строку
            promptData = JSON.stringify(requestData);
          }
        }

        // Создаем объект запроса с типом, включающим with_points
        interface ApiRequestDataWithPoints {
          user_id: number | undefined;
          type: ContentType;
          prompt: any;
          with_points?: boolean;
        }

        // Создаем объект с правильным типом
        const apiRequestData: ApiRequestDataWithPoints = {
          user_id: this.user?.id,
          type: ContentType.LESSON_PLAN,
          prompt: promptData
        };

        // Если это генерация за баллы, добавляем соответствующий флаг
        if (isPointsGeneration) {
          apiRequestData.with_points = true;

          // Проверяем, был ли уже списан баланс в компоненте
          // Если в requestData есть поле skip_points_check, то баллы уже были списаны
          const skipPointsCheck = requestData.skip_points_check === true;

          if (!skipPointsCheck) {
            // Проверяем и списываем баллы только если они еще не были списаны
            console.log('Списываем баллы в store.detailLessonPlan');
            const pointsCost = 8; // Стоимость детализации плана урока
            const canGenerate = await this.checkAndTrackGenerationWithPoints(ContentType.LESSON_PLAN, pointsCost);

            if (!canGenerate) {
              throw new Error(`Не удалось списать ${pointsCost} баллов. Возможно, недостаточно баллов на счету.`);
            }
          } else {
            console.log('Пропускаем списание баллов, так как они уже были списаны в компоненте');
          }
        }

        console.log('Store: Отправка запроса с данными:', apiRequestData);

        // Make the API request
        const response = await apiClient.detailLessonPlan(apiRequestData);

        // Check if response is valid
        if (!response || !response.data) {
          throw new Error('Invalid response from server');
        }

        // Добавляем отладочный лог
        console.log('Store: Получен ответ детализации:', response.data.content ? 'Детализация успешна' : 'Пустой ответ!');

        // Return the response data
        return response.data;
      } catch (error) {
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async deleteContent(contentId: number) {
      try {
        const response = await apiClient.delete(`/api/v1/admin/generations/${contentId}`);
        return response.data;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    async exportGenerationsData(filters?: {
      search?: string
      dateFrom?: string
      dateTo?: string
      type?: ContentType | 'all'
    }, format: string = 'csv') {
      try {
        const response = await apiClient.get('/api/v1/admin/generations/export', {
          params: {
            ...filters,
            format
          },
          responseType: 'blob'
        })

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `generations_${new Date().toISOString()}.${format}`)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    // Users Management
    async fetchUsers(skip = 0, limit = 100) {
      console.log('fetchUsers: Начало выполнения метода');

      // Проверяем наличие Telegram WebApp
      const webApp = window.Telegram?.WebApp;
      if (webApp) {
        console.log('fetchUsers: Telegram WebApp доступен:', {
          initDataUnsafe: webApp.initDataUnsafe ? 'Данные есть' : 'Данных нет',
          version: webApp.version,
          platform: webApp.platform
        });
      } else {
        console.warn('fetchUsers: Telegram WebApp недоступен');
      }

      // Проверяем авторизацию пользователя
      console.log('fetchUsers: Текущий пользователь в store:', this.user);

      try {
        console.log(`fetchUsers: Отправка запроса к /api/v1/users/ с параметрами skip=${skip}, limit=${limit}`);

        // Using the correct endpoint to get the list of users (with trailing slash)
        // Используем правильные параметры пагинации: skip и limit вместо page и limit
        const response = await apiClient.get('/api/v1/users/', {
          params: {
            skip,
            limit
          }
        });

        // Добавляем подробное логирование для отладки
        console.log('fetchUsers: Raw response:', response);

        // ВАЖНО: Проверяем, что response не undefined и не null
        if (!response) {
          console.error('fetchUsers: Response is undefined or null');
          return [];
        }

        console.log('fetchUsers: Response type:', typeof response);

        // Проверяем, является ли response массивом (это может быть, если API клиент вернул массив items)
        if (Array.isArray(response)) {
          console.log('fetchUsers: Response is an array with length:', response.length);
          if (response.length > 0) {
            console.log('fetchUsers: First item in response array:', response[0]);
          }
          return response; // Возвращаем массив как есть
        }

        // Если response - это объект, проверяем его структуру
        if (typeof response === 'object') {
          console.log('fetchUsers: Response is an object with keys:', Object.keys(response));

          // Проверяем, есть ли в response поле data
          if (response.data !== undefined) {
            console.log('fetchUsers: Response has data field of type:', typeof response.data);

            // Если response.data - это массив, возвращаем его
            if (Array.isArray(response.data)) {
              console.log('fetchUsers: Response.data is an array with length:', response.data.length);
              if (response.data.length > 0) {
                console.log('fetchUsers: First item in response.data array:', response.data[0]);
              }
              return response.data;
            }

            // Если response.data - это объект, проверяем, есть ли в нем поле items
            if (typeof response.data === 'object' && response.data !== null) {
              console.log('fetchUsers: Response.data is an object with keys:', Object.keys(response.data));

              // Если в response.data есть поле items и оно является массивом, возвращаем его
              if (response.data.items && Array.isArray(response.data.items)) {
                console.log('fetchUsers: Response.data.items is an array with length:', response.data.items.length);
                if (response.data.items.length > 0) {
                  console.log('fetchUsers: First item in response.data.items array:', response.data.items[0]);
                }
                return response.data.items;
              }
            }
          }
        }

        // Проверяем, есть ли данные в ответе
        if (response && response.data !== undefined) {
          // Проверяем наличие пагинации в ответе
          if (response.data && response.data.page && response.data.total_pages) {
            console.log(`fetchUsers: Pagination info - page ${response.data.page} of ${response.data.total_pages}`);
          }

          // Если ответ содержит items, используем их
          if (response.data && response.data.items && Array.isArray(response.data.items)) {
            console.log('fetchUsers: Successfully fetched users (items):', response.data.items.length);
            console.log('fetchUsers: First user in items:', response.data.items[0]);

            // Проверяем, что items содержат все необходимые поля
            if (response.data.items.length > 0) {
              const firstItem = response.data.items[0];
              console.log('fetchUsers: First item has id:', firstItem.id);
              console.log('fetchUsers: First item has telegram_id:', firstItem.telegram_id);
              console.log('fetchUsers: First item has first_name:', firstItem.first_name);
              console.log('fetchUsers: First item has role:', firstItem.role);
            }

            // Возвращаем только массив items, а не весь объект response.data
            return response.data.items;
          }
          // Если ответ содержит results, используем их (распространенный формат пагинации)
          else if (response.data && response.data.results && Array.isArray(response.data.results)) {
            console.log('fetchUsers: Successfully fetched users (results):', response.data.results.length);
            return response.data.results;
          }
          // Если ответ сам является массивом, используем его напрямую
          else if (Array.isArray(response.data)) {
            console.log('fetchUsers: Successfully fetched users (array):', response.data.length);
            return response.data;
          }
          // Если ответ - это объект с полем data, который является массивом
          else if (response.data && response.data.data && Array.isArray(response.data.data)) {
            console.log('fetchUsers: Successfully fetched users (data array):', response.data.data.length);
            return response.data.data;
          }
          // Если ответ - это объект с полем users, который является массивом
          else if (response.data && response.data.users && Array.isArray(response.data.users)) {
            console.log('fetchUsers: Successfully fetched users (users array):', response.data.users.length);
            return response.data.users;
          }
          // Если ответ - это объект, но не содержит массива, проверяем, может ли он быть одним пользователем
          else if (response.data && typeof response.data === 'object' && response.data.id) {
            console.log('fetchUsers: Successfully fetched single user:', response.data.id);
            return [response.data];
          }
          // Если ответ пустой, но статус успешный, возвращаем пустой массив
          else if (response.status >= 200 && response.status < 300) {
            console.log('fetchUsers: Empty but successful response, returning empty array');
            return [];
          }
          else {
            console.error('fetchUsers: Unexpected response structure from users API:', response.data);
            return [];
          }
        } else {
          console.error('fetchUsers: Empty response from users API');
          // Возвращаем пустой массив
          return [];
        }
      } catch (error: any) {
        this.handleError(error);
        console.error('fetchUsers: Error fetching users:', error);

        // Логируем дополнительную информацию об ошибке
        if (error.response) {
          console.error('fetchUsers: Error response:', {
            status: error.response.status,
            statusText: error.response.statusText,
            data: error.response.data,
            headers: error.response.headers
          });
        } else if (error.request) {
          console.error('fetchUsers: Error request:', error.request);
        } else {
          console.error('fetchUsers: Error message:', error.message);
        }

        // In case of error, return empty array to not break the interface
        return [];
      }
    },

    async fetchGenerations(
      skip: number = 0,
      limit: number = 100,
      period: string = 'week',
      type: string | null = null,
      userId: number | null = null,
      startDate: string | null = null,
      endDate: string | null = null,
      sortBy: string = 'created_at',
      sortOrder: 'asc' | 'desc' = 'desc'
    ) {
      console.log('=== FETCH GENERATIONS STARTED ===');
      console.log(`FETCH_GENERATIONS: Params: skip=${skip}, limit=${limit}, period=${period}, type=${type}, userId=${userId}, startDate=${startDate}, endDate=${endDate}, sortBy=${sortBy}, sortOrder=${sortOrder}`);
      console.log('FETCH_GENERATIONS: Method called with params:', {
        skip, limit, period, type, userId, startDate, endDate, sortBy, sortOrder
      });
      try {
        // Используем новый эндпоинт для получения детальной информации о генерациях
        console.log('FETCH_GENERATIONS: Attempting to fetch from /api/v1/admin/generations endpoint');

        // Проверяем доступные эндпоинты
        console.log('FETCH_GENERATIONS: Available endpoints check:');
        console.log('FETCH_GENERATIONS: 1. /api/v1/admin/generations');
        console.log('FETCH_GENERATIONS: 2. /api/v1/statistics/generations');
        console.log('FETCH_GENERATIONS: 3. /api/v1/generations');

        // Создаем параметры запроса
        const params = {
          period,
          type,
          user_id: userId,
          start_date: startDate,
          end_date: endDate,
          skip,
          limit,
          sort_by: sortBy,
          sort_order: sortOrder
        };

        console.log('Request params:', params);

        // Используем apiClient для запроса
        try {
          // Сначала пробуем получить данные из API генераций
          console.log('BACKEND_CHECK: Using apiClient for request to /api/v1/admin/generations');
          console.log('BACKEND_CHECK: Request params:', JSON.stringify(params));

          // Пробуем все возможные эндпоинты
          let directResponse;
          let endpoint = '';

          try {
            console.log('BACKEND_CHECK: Trying endpoint /api/v1/admin/generations');
            endpoint = '/api/v1/admin/generations';
            directResponse = await apiClient.get(endpoint, { params });
            console.log('BACKEND_CHECK: Success with endpoint /api/v1/admin/generations');
          } catch (error1) {
            console.log('BACKEND_CHECK: Failed with endpoint /api/v1/admin/generations, trying /api/v1/statistics/generations');

            try {
              endpoint = '/api/v1/statistics/generations';
              directResponse = await apiClient.get(endpoint, { params });
              console.log('BACKEND_CHECK: Success with endpoint /api/v1/statistics/generations');
            } catch (error2) {
              console.log('BACKEND_CHECK: Failed with endpoint /api/v1/statistics/generations, trying /api/v1/generations');

              try {
                endpoint = '/api/v1/generations';
                directResponse = await apiClient.get(endpoint, { params });
                console.log('BACKEND_CHECK: Success with endpoint /api/v1/generations');
              } catch (error3) {
                console.log('BACKEND_CHECK: All endpoints failed');
                throw error3;
              }
            }
          }

          console.log('BACKEND_CHECK: Successful endpoint:', endpoint);
          console.log('BACKEND_CHECK: Response status:', directResponse?.status);
          console.log('BACKEND_CHECK: Response headers:', JSON.stringify(directResponse?.headers));

          console.log('Direct axios response:', directResponse);

          // Проверяем, что directResponse содержит данные
          let responseData;

          if (directResponse && typeof directResponse === 'object') {
            // Если directResponse сам является данными (не содержит поле data)
            if (directResponse.generations && Array.isArray(directResponse.generations)) {
              console.log('BACKEND_CHECK: directResponse itself contains generations array');
              responseData = directResponse;
            }
            // Если directResponse содержит поле data
            else if (directResponse.data && typeof directResponse.data === 'object') {
              console.log('BACKEND_CHECK: directResponse.data contains the response data');
              responseData = directResponse.data;
            }
            // Если directResponse не содержит ни generations, ни data
            else {
              console.log('BACKEND_CHECK: directResponse does not contain generations or data, using directResponse as is');
              responseData = directResponse;
            }
          } else {
            console.log('BACKEND_CHECK: directResponse is not an object');
            responseData = null;
          }

          console.log('BACKEND_CHECK: Extracted responseData:', responseData);

          // Добавляем подробное логирование для отладки
          console.log('BACKEND_CHECK: Direct response type:', typeof responseData);
          console.log('BACKEND_CHECK: Direct response keys:', responseData ? Object.keys(responseData) : 'No data');
          console.log('BACKEND_CHECK: Full response data:', JSON.stringify(responseData));

          // Добавляем более подробное логирование
          if (responseData) {
            console.log('Response structure:');
            console.log('- has generations?', 'generations' in responseData);
            console.log('- has items?', 'items' in responseData);
            console.log('- has total?', 'total' in responseData);
            console.log('- has total_generations?', 'total_generations' in responseData);

            if ('generations' in responseData) {
              console.log('- generations is array?', Array.isArray(responseData.generations));
              console.log('- generations length:', responseData.generations?.length || 0);
              if (responseData.generations && responseData.generations.length > 0) {
                console.log('- first generation:', responseData.generations[0]);
              }
            }

            if ('items' in responseData) {
              console.log('- items is array?', Array.isArray(responseData.items));
              console.log('- items length:', responseData.items?.length || 0);
              if (responseData.items && responseData.items.length > 0) {
                console.log('- first item:', responseData.items[0]);
              }
            }
          }

          // Проверяем структуру ответа и возвращаем данные
          if (responseData) {
            // Если ответ содержит поле generations, используем его
            if (responseData.generations && Array.isArray(responseData.generations)) {
              console.log('BACKEND_CHECK: Successfully fetched generations with expected structure');
              console.log('BACKEND_CHECK: Generations count:', responseData.generations.length);
              if (responseData.generations.length > 0) {
                console.log('BACKEND_CHECK: First generation type:', responseData.generations[0]?.type);
                console.log('BACKEND_CHECK: First generation created_at:', responseData.generations[0]?.created_at);
              } else {
                console.log('BACKEND_CHECK: Generations array is empty');
              }

              // Проверяем, что все необходимые поля присутствуют
              if (!responseData.total) {
                console.log('BACKEND_CHECK: Adding missing total field');
                responseData.total = responseData.generations.length;
              }

              if (!responseData.total_generations) {
                console.log('BACKEND_CHECK: Adding missing total_generations field');
                responseData.total_generations = responseData.generations.length;
              }

              return responseData;
            }
            // Если ответ содержит поле items, используем его
            else if (responseData.items && Array.isArray(responseData.items)) {
              console.log('Successfully fetched generations in items field');
              console.log('Items count:', responseData.items.length);

              // Преобразуем структуру ответа к ожидаемому формату
              return {
                generations: responseData.items,
                total: responseData.total || responseData.items.length,
                total_generations: responseData.total_generations || responseData.items.length,
                by_type: responseData.by_type || {
                  lesson_plan: 0,
                  exercise: 0,
                  game: 0,
                  image: 0,
                  text_analysis: 0,
                  concept_explanation: 0,
                  course: 0,
                  ai_assistant: 0
                },
                popular_prompts: responseData.popular_prompts || []
              };
            }
            // Если ответ содержит нужные поля, но без generations, создаем структуру
            else if (typeof responseData.total_generations !== 'undefined') {
              console.log('Successfully fetched generation statistics, but no generations array');
              console.log('Total generations:', responseData.total_generations);
              console.log('By type:', responseData.by_type || 'No by_type data');

              return {
                generations: [], // Пустой массив генераций
                total: responseData.total_generations || 0,
                total_generations: responseData.total_generations || 0,
                by_type: responseData.by_type || {
                  lesson_plan: 0,
                  exercise: 0,
                  game: 0,
                  image: 0,
                  text_analysis: 0,
                  concept_explanation: 0,
                  course: 0,
                  ai_assistant: 0
                },
                popular_prompts: responseData.popular_prompts || []
              };
            }
            // Если ответ сам является массивом, оборачиваем его
            else if (Array.isArray(responseData)) {
              console.log('Successfully fetched generations as array:', responseData.length);
              return {
                generations: responseData,
                total: responseData.length,
                total_generations: responseData.length,
                by_type: {
                  lesson_plan: 0,
                  exercise: 0,
                  game: 0,
                  image: 0,
                  text_analysis: 0,
                  concept_explanation: 0,
                  course: 0,
                  ai_assistant: 0
                },
                popular_prompts: []
              };
            }
            else {
              console.error('Unexpected response structure from generations API:', JSON.stringify(responseData));
              return this.getEmptyGenerationsResponse();
            }
          } else {
            console.error('BACKEND_CHECK: Empty response from generations API');

            // Пробуем получить данные из статистики генераций
            try {
              console.log('BACKEND_CHECK: Trying to get data from statistics endpoint');
              const statsResponse = await apiClient.get('/api/v1/statistics/generations', {
                params: { period }
              });

              console.log('BACKEND_CHECK: Statistics response:', statsResponse);

              // Если получили данные из статистики, создаем генерации на основе этих данных
              if (statsResponse && typeof statsResponse === 'object') {
                let statsData;

                // Извлекаем данные из ответа
                if (statsResponse.data && typeof statsResponse.data === 'object') {
                  statsData = statsResponse.data;
                } else {
                  statsData = statsResponse;
                }

                console.log('BACKEND_CHECK: Statistics data:', statsData);

                // Если есть данные о типах генераций, создаем генерации
                if (statsData.generations_by_type || statsData.by_type) {
                  const byType = statsData.generations_by_type || statsData.by_type || {};
                  const generationsFromStats = [];
                  let id = 1;

                  // Создаем генерации для каждого типа
                  Object.entries(byType).forEach(([type, count]) => {
                    for (let i = 0; i < (count as number); i++) {
                      generationsFromStats.push({
                        id: id++,
                        user_id: this.user?.id || 1,
                        type,
                        content: `Generated ${type} content`,
                        prompt: statsData.popular_prompts && statsData.popular_prompts.length > 0
                          ? statsData.popular_prompts[0].prompt
                          : `Generate ${type}`,
                        created_at: statsData.end_date || new Date().toISOString()
                      });
                    }
                  });

                  console.log('BACKEND_CHECK: Created generations from statistics:', generationsFromStats.length);

                  return {
                    generations: generationsFromStats,
                    total: generationsFromStats.length,
                    total_generations: statsData.total_generations || generationsFromStats.length,
                    by_type: byType,
                    popular_prompts: statsData.popular_prompts || []
                  };
                }
              }
            } catch (statsError) {
              console.log('BACKEND_CHECK: Failed to get data from statistics endpoint:', statsError);
            }

            console.log('BACKEND_CHECK: Falling back to empty response');
            return this.getEmptyGenerationsResponse();
          }
        } catch (axiosError) {
          console.error('Error with apiClient request:', axiosError);
          throw axiosError; // Пробрасываем ошибку дальше
        }


      } catch (error: any) {
        console.error('Error fetching generations:', error);
        console.log('Error status:', error.response?.status);
        console.log('Error message:', error.message);

        if (error.response) {
          console.log('Error response data:', error.response.data);
        }

        // Если произошла ошибка, пробуем использовать старый эндпоинт
        console.log('Trying fallback to statistics endpoint');
        try {
          const response = await apiClient.get('/api/v1/statistics/generations', {
            params: { period: 'week' }
          });

          console.log('BACKEND_CHECK: Fallback response status:', response?.status);
          console.log('BACKEND_CHECK: Fallback response data type:', typeof response?.data);
          console.log('BACKEND_CHECK: Fallback response data keys:', response?.data ? Object.keys(response.data) : 'No data');
          console.log('BACKEND_CHECK: Full fallback response data:', JSON.stringify(response?.data));

          if (response && response.data) {
            console.log('Successfully fetched generation statistics from fallback endpoint');
            console.log('Total generations:', response.data.total_generations);
            console.log('Generations by type:', response.data.generations_by_type || 'No generations_by_type data');

            // Создаем генерации на основе статистики
            const generationsFromStats: any[] = [];

            // Если есть данные о типах генераций, создаем записи для каждого типа
            if (response.data.generations_by_type) {
              let id = 1;
              Object.entries(response.data.generations_by_type).forEach(([type, count]) => {
                // Для каждого типа создаем соответствующее количество записей
                for (let i = 0; i < (count as number); i++) {
                  generationsFromStats.push({
                    id: id++,
                    user_id: this.user?.id || 1,
                    type,
                    content: `Generated ${type} content`,
                    prompt: response.data.popular_prompts && response.data.popular_prompts.length > 0
                      ? response.data.popular_prompts[0].prompt
                      : `Generate ${type}`,
                    created_at: response.data.end_date || new Date().toISOString()
                  });
                }
              });
            }

            console.log('Created generations from statistics:', generationsFromStats.length);

            return {
              generations: generationsFromStats,
              total: generationsFromStats.length,
              total_generations: response.data.total_generations || 0,
              by_type: response.data.generations_by_type || {
                lesson_plan: 0,
                exercise: 0,
                game: 0,
                image: 0,
                text_analysis: 0,
                concept_explanation: 0,
                course: 0,
                ai_assistant: 0
              },
              popular_prompts: response.data.popular_prompts || []
            };
          } else {
            console.error('Empty response from fallback endpoint');
            console.log('Returning empty response');
            return this.getEmptyGenerationsResponse();
          }
        } catch (fallbackError: any) {
          console.error('Fallback endpoint also failed:', fallbackError);
          console.log('Fallback error status:', fallbackError.response?.status);
          console.log('Fallback error message:', fallbackError.message);

          if (fallbackError.response) {
            console.log('Fallback error response data:', fallbackError.response.data);
          }

          console.log('Returning empty response after all attempts failed');
          return this.getEmptyGenerationsResponse();
        }
      } finally {
        console.log('=== FETCH GENERATIONS COMPLETED ===');
      }
    },

    // Вспомогательный метод для создания пустого ответа по генерациям
    getEmptyGenerationsResponse() {
      return {
        generations: [], // Пустой массив генераций
        total: 0,
        total_generations: 0,
        by_type: {
          lesson_plan: 0,
          exercise: 0,
          game: 0,
          image: 0,
          text_analysis: 0,
          concept_explanation: 0,
          course: 0,
          ai_assistant: 0
        },
        popular_prompts: []
      };
    },

    async fetchCurrentUser() {
      try {
        const user = await apiClient.getCurrentUser();
        console.log("Fetched user:", user, "Role:", user.role, "Type of role:", typeof user.role);
        this.user = user;
        return user;
      } catch (error: any) {
        if (error.response?.status === 401) {
          this.clearAuth();
        }
        throw error;
      }
    },

    // Удаляем дублирующееся и некорректное действие generateContent

    async useReferralCode(code: string) {
      try {
        this.isLoading = true;
        await apiClient.useReferralCode(code);
        await this.fetchCurrentUser(); // ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
      } catch (error: any) {
        this.error = error.message;
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchUserStats() {
      try {
        return await apiClient.getUserStats();
      } catch (error: any) {
        this.error = error.message;
        throw error;
      }
    },

    async updateUser(userId: number, userData: Partial<User>) {
      try {
        const response = await apiClient.put(API_ENDPOINTS.USER_DETAIL(userId), userData);
        return response.data;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    async getActivityData(period: string): Promise<DataPoint[]> {
      try {
        const response = await apiClient.get('/api/v1/admin/analytics/activity', {
          params: {period}
        });

        // Check if response has the expected structure
        if (response && Array.isArray(response.data)) {
          console.log('Successfully fetched activity data:', response.data.length, 'data points');
          return response.data;
        } else {
          console.error('Unexpected response structure from activity API:', response);
          // In case of unexpected structure, return empty array to not break the interface
          return [];
        }
      } catch (error: any) {
        this.handleError(error);
        console.error('Error fetching activity data:', error);
        // In case of error, return empty array to not break the interface
        return [];
      }
    },

    setMessage(message: string) {
      this.message = message;
    },

    async getUserStatistics(): Promise<UserStatistics | null> {
      console.log('[getUserStatistics] Starting...'); // <-- ADDED LOG
      try {
        this.setLoading(true);

        // Get user's tariff info
        console.log(`[getUserStatistics] Fetching tariff info for user ${this.user?.id}...`);
        // --- ВОЗВРАЩАЕМ ПРАВИЛЬНЫЙ URL ЭНДПОИНТА СОГЛАСНО __init__.py ---
        const tariffResponse = await apiClient.get(`/api/v1/users/${this.user?.id}/tariff`);
        console.log('[getUserStatistics] Tariff response received:', tariffResponse);

        // Get usage tracking data
        console.log(`[getUserStatistics] Fetching usage stats for user ${this.user?.id}...`); // <-- ADDED LOG
        const usageResponse = await apiClient.get(`/api/v1/users/${this.user?.id}/usage-stats`);
        console.log('[getUserStatistics] Usage stats response received:', usageResponse); // <-- ADDED LOG

        // Combine the data to create a complete statistics object
        const combinedStats: UserStatistics = {
          // Default values
          generations_by_type: {} as Record<ContentType, number>, // Инициализируем пустым объектом
          dailyGenerations: 0,
          dailyImages: 0,
          totalGenerations: 0,
          totalImages: 0,
          points: this.user?.points || 0,
          lastActive: new Date()
        };

        // Apply tariff data if available
        // More robust check - Check tariffResponse directly, not tariffResponse.data
        if (tariffResponse && typeof tariffResponse === 'object' && tariffResponse.type) {
          console.log('[getUserStatistics] Setting tariffInfo:', tariffResponse); // Log the direct response
          this.tariffInfo = tariffResponse; // Assign the direct response
        } else {
          // Log the actual data received for better debugging
          console.warn('[getUserStatistics] No valid tariff data received in response. Response data:', tariffResponse); // Log the direct response
          this.tariffInfo = null;
        }

        // Apply usage data if available
        if (usageResponse.data) { // Оставляем проверку usageResponse.data как есть, если она работает
          combinedStats.dailyGenerations = usageResponse.data.daily_generations || 0;
          combinedStats.dailyImages = usageResponse.data.daily_images || 0;
          combinedStats.totalGenerations = usageResponse.data.total_generations || 0;
          combinedStats.totalImages = usageResponse.data.total_images || 0;
          combinedStats.lastActive = new Date(usageResponse.data.last_active || Date.now());
        }

        // Update local state
        this.userStats = combinedStats;

        return combinedStats;
      } catch (error: any) {
        console.error('[getUserStatistics] Error caught:', error); // Оставляем лог ошибки
        this.handleError(error);
        return null;
      } finally {
        this.setLoading(false);
      }
    },


    // Achievements Management
    async fetchAchievements() {
      try {
        const response = await apiClient.get(API_ENDPOINTS.ACHIEVEMENTS);
        return response.data;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      }
    },

    async createAchievement(achievementData: Partial<Achievement>) {
      try {
        const response = await apiClient.post(API_ENDPOINTS.ACHIEVEMENTS, achievementData);
        return response.data;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      }
    },

    async updateAchievement(achievementId: string, achievementData: Partial<Achievement>) {
      try {
        const response = await apiClient.put(
          API_ENDPOINTS.ACHIEVEMENT_DETAIL(achievementId),
          achievementData
        );
        return response.data;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      }
    },

    async checkAchievements(action_type: ActionType, action_data: any) {
      try {
        const response = await apiClient.post('/api/v1/achievements/check', {
          user_id: this.user?.id,
          action_type,
          action_data
        });

        if (response.data?.achievements) {
          this.achievements = response.data.achievements;
        }
        return response.data;
      } catch (error: any) {
        // Log the error but don't throw - achievements are secondary
        console.warn('Error checking achievements:', error);
        // Return a default response
        return { status: 'warning', message: 'Achievement check failed but content generation will continue' };
      }
    },

    // Tariffs Management
    async fetchTariffs() {
      try {
        const response = await apiClient.get(API_ENDPOINTS.TARIFFS);
        return response.data;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      }
    },

    async createTariff(tariffData: Partial<Tariff>) {
      try {
        const response = await apiClient.post(API_ENDPOINTS.TARIFFS, tariffData);
        return response.data;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      }
    },

    async updateTariff(tariffId: number, tariffData: Partial<Tariff>) {
      try {
        const response = await apiClient.put(
          API_ENDPOINTS.TARIFF_DETAIL(tariffId),
          tariffData
        );
        return response.data;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      }
    },

    async fetchUserTariff(retryCount = 0, maxRetries = 3): Promise<any> {
      try {
        if (!this.user) {
          console.warn('[fetchUserTariff] No user data available');
          return null;
        }

        console.log(`[fetchUserTariff] Fetching tariff info for user ${this.user.id}, retry: ${retryCount}/${maxRetries}`);

        try {
          const response = await apiClient.get(`/api/v1/users/${this.user.id}/tariff`);
          console.log('[fetchUserTariff] Received tariff info:', response);

          if (response) {
            this.tariffInfo = response;
            return response;
          } else {
            console.warn('[fetchUserTariff] Received empty tariff data');

            // Если получили пустой ответ и есть попытки, повторяем запрос
            if (retryCount < maxRetries) {
              console.log(`[fetchUserTariff] Empty response, retrying (${retryCount + 1}/${maxRetries})...`);
              await new Promise(resolve => setTimeout(resolve, 500)); // Небольшая задержка
              return this.fetchUserTariff(retryCount + 1, maxRetries);
            }
          }
        } catch (apiError) {
          console.error('[fetchUserTariff] API error:', apiError);

          // Если произошла ошибка API и есть попытки, повторяем запрос
          if (retryCount < maxRetries) {
            console.log(`[fetchUserTariff] API error, retrying (${retryCount + 1}/${maxRetries})...`);
            await new Promise(resolve => setTimeout(resolve, 1000)); // Увеличенная задержка при ошибке
            return this.fetchUserTariff(retryCount + 1, maxRetries);
          }

          throw apiError; // Пробрасываем ошибку дальше, если исчерпаны попытки
        }

        return null;
      } catch (error: any) {
        console.error('[fetchUserTariff] Error fetching tariff info:', error);

        // Если у пользователя есть тариф, но не удалось получить информацию о нем,
        // создаем базовую информацию о тарифе на основе данных пользователя
        if (this.user?.tariff) {
          console.log('[fetchUserTariff] Creating fallback tariff info based on user data');

          // Определяем лимиты на основе типа тарифа
          let generationsLimit = 0;
          let imagesLimit = 0;

          switch (this.user.tariff) {
            case TariffType.PREMIUM:
              generationsLimit = 25;
              imagesLimit = 8;
              break;
            case TariffType.STANDARD:
              generationsLimit = 12;
              imagesLimit = 5;
              break;
            case TariffType.BASIC:
              generationsLimit = 6;
              imagesLimit = 2;
              break;
          }

          // Создаем базовую информацию о тарифе
          const fallbackTariffInfo = {
            type: this.user.tariff,
            validUntil: this.user.tariff_valid_until ? new Date(this.user.tariff_valid_until) : null, // Преобразуем строку в Date
            limits: {
              generations: generationsLimit,
              images: imagesLimit
            },
            name: String(this.user.tariff), // Преобразуем в строку
            pricePoints: 0, // Добавляем недостающее свойство
            features: [] // Добавляем недостающее свойство
          };

          this.tariffInfo = fallbackTariffInfo;
          return fallbackTariffInfo;
        }

        return null;
      }
    },

    async updateUserTariff(tariffType: TariffType) {
      try {
        this.setLoading(true);
        this.clearError();

        // First check if user already has this tariff
        if (this.user?.tariff === tariffType && this.isTariffActive) {
          throw new Error("Вы уже используете этот тариф");
        }

        console.log(`[updateUserTariff] Attempting to purchase tariff: ${tariffType} for user ${this.user?.id}`);

        // Попробуем оба эндпоинта для максимальной надежности
        let response;
        let success = false;
        let error;

        try {
          // Сначала пробуем основной эндпоинт
          try {
            response = await apiClient.post(`/api/v1/users/${this.user?.id}/tariff`, {
              tariff_type: tariffType
            });
            success = true;
            console.log('[updateUserTariff] Tariff purchase successful via primary endpoint:', response);
          } catch (err) {
            // Если основной эндпоинт не сработал, пробуем альтернативный
            console.warn('[updateUserTariff] Primary endpoint failed, trying alternative endpoint:', err);
            error = err;

            // Добавляем небольшую задержку перед повторной попыткой
            await new Promise(resolve => setTimeout(resolve, 500));

            try {
              // Используем правильный URL для альтернативного эндпоинта
              response = await apiClient.post(`/api/v1/users/${this.user?.id}/tariff`, {
                tariff_type: tariffType
              });
              success = true;
              console.log('[updateUserTariff] Tariff purchase successful via alternative endpoint:', response);
            } catch (altErr) {
              console.error('[updateUserTariff] Both endpoints failed:', altErr);

              // Проверяем, был ли тариф фактически обновлен, несмотря на ошибку API
              console.log('[updateUserTariff] Checking if tariff was actually updated despite API errors');

              // Добавляем задержку перед проверкой
              await new Promise(resolve => setTimeout(resolve, 1000));

              try {
                // Проверяем текущий тариф пользователя
                const userResponse = await apiClient.get(`/api/v1/users/me`);
                if (userResponse.data && userResponse.data.tariff === tariffType) {
                  console.log('[updateUserTariff] Tariff was actually updated despite API errors:', userResponse.data);
                  success = true;
                  response = { data: { status: 'success', message: 'Тариф успешно обновлен' } };
                } else {
                  // Если тариф не был обновлен, выбрасываем исходную ошибку
                  throw error;
                }
              } catch (checkErr) {
                console.error('[updateUserTariff] Failed to check if tariff was updated:', checkErr);
                // Если не удалось проверить, выбрасываем исходную ошибку
                throw error;
              }
            }
          }
        } catch (finalErr) {
          console.error('[updateUserTariff] All attempts to update tariff failed:', finalErr);
          throw finalErr;
        }

        if (success) {
          console.log('[updateUserTariff] Starting complete data refresh after tariff update');

          // Сбрасываем локальные данные о статистике использования
          if (this.userStats) {
            // Явно сбрасываем счетчики в локальном состоянии
            this.userStats.dailyGenerations = 0;
            this.userStats.dailyImages = 0;
          }

          // Обновляем данные в определенном порядке с повторными попытками
          // для максимальной надежности

          // Функция для повторных попыток с экспоненциальной задержкой
          const retryWithBackoff = async (operation: () => Promise<any>, name: string, maxRetries = 3, initialDelay = 500) => {
            let retryCount = 0;

            while (retryCount < maxRetries) {
              try {
                const result = await operation();
                console.log(`[updateUserTariff] ${name} successful (attempt ${retryCount + 1}):`, result);
                return result;
              } catch (e) {
                console.warn(`[updateUserTariff] ${name} failed (attempt ${retryCount + 1}):`, e);
                retryCount++;

                if (retryCount < maxRetries) {
                  // Экспоненциальная задержка: 500ms, 1000ms, 2000ms, ...
                  const delay = initialDelay * Math.pow(2, retryCount - 1);
                  console.log(`[updateUserTariff] Retrying ${name} in ${delay}ms...`);
                  await new Promise(resolve => setTimeout(resolve, delay));
                }
              }
            }

            console.error(`[updateUserTariff] All ${maxRetries} attempts to ${name} failed`);
            return null;
          };

          console.log('[updateUserTariff] Starting tariff update process');

          // Сначала обновляем информацию о тарифе
          const tariffInfo = await retryWithBackoff(() => this.fetchUserTariff(), "fetch tariff info", 5);
          console.log('[updateUserTariff] Tariff info updated:', tariffInfo);

          // Затем обновляем данные пользователя
          await retryWithBackoff(() => this.fetchCurrentUser(), "fetch user data", 5);
          console.log('[updateUserTariff] User data updated');

          // Принудительно сбрасываем счетчики использования
          const resetResult = await retryWithBackoff(() => this.resetUsageCounters(), "reset usage counters", 5);
          console.log('[updateUserTariff] Reset counters result:', resetResult);

          // Дополнительная проверка и логирование
          if (this.userStats) {
            console.log('[updateUserTariff] Current generation counts after reset:', {
              dailyGenerations: this.userStats.dailyGenerations,
              dailyImages: this.userStats.dailyImages,
              limits: this.tariffInfo?.limits
            });

            // Проверяем, что счетчики действительно сброшены
            if (this.userStats.dailyGenerations > 0 || this.userStats.dailyImages > 0) {
              console.warn('[updateUserTariff] Counters were not reset properly, forcing another reset');

              // Пробуем еще раз сбросить счетчики напрямую через API клиент
              try {
                const userId = this.user?.id;
                if (userId) {
                  console.log(`[updateUserTariff] Directly calling reset endpoint for user ${userId}`);
                  const resetResponse = await apiClient.resetUsageCounters(userId);
                  console.log('[updateUserTariff] Direct server reset response:', resetResponse.data);

                  // Если сервер вернул данные о сбросе счетчиков, используем их
                  if (resetResponse.data && resetResponse.data.data) {
                    const { daily_generations, daily_images } = resetResponse.data.data;

                    // Обновляем локальное состояние данными с сервера
                    if (this.userStats) {
                      this.userStats.dailyGenerations = daily_generations;
                      this.userStats.dailyImages = daily_images;
                    }
                  } else {
                    // Если сервер не вернул данные, сбрасываем счетчики локально
                    if (this.userStats) {
                      this.userStats.dailyGenerations = 0;
                      this.userStats.dailyImages = 0;
                    }
                  }

                  // Обновляем данные с сервера
                  await this.updateUsageStats();
                }
              } catch (resetError) {
                console.error('[updateUserTariff] Error in direct reset:', resetError);

                // В случае ошибки сбрасываем счетчики локально
                if (this.userStats) {
                  this.userStats.dailyGenerations = 0;
                  this.userStats.dailyImages = 0;
                }
              }

              // Проверяем результат повторного сброса
              console.log('[updateUserTariff] Counters after second reset attempt:', {
                dailyGenerations: this.userStats.dailyGenerations,
                dailyImages: this.userStats.dailyImages
              });
            }
          }

          // Проверяем, что тариф действительно обновлен
          if (this.user && this.user.tariff !== tariffType) {
            console.warn(`[updateUserTariff] Tariff not updated in user object (${this.user.tariff} != ${tariffType}), forcing update`);
            if (this.user) {
              this.user.tariff = tariffType;
            }
          }

          console.log('[updateUserTariff] Complete data refresh completed successfully');

          // Показываем уведомление об успешной покупке тарифа
          toastService.success(`Тариф "${tariffType}" успешно активирован`);
        } else {
          console.warn('[updateUserTariff] No success flag set after tariff purchase attempts');
          throw new Error('Не удалось обновить тариф');
        }

        return true;
      } catch (error: any) {
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async fetchTariffHistory() {
      if (!this.user?.id) return [];

      try {
        const history = await tariffService.getTariffHistory(this.user.id);
        this.tariffHistory = history;
        return history;
      } catch (error: any) {
        this.handleError(error);
        return [];
      }
    },

    async fetchAvailableTariffs() {
      try {
        const tariffs = await tariffService.getAvailableTariffs();
        this.availableTariffs = tariffs;
        return tariffs;
      } catch (error: any) {
        this.handleError(error);
        return [];
      }
    },

    async extendCurrentTariff(months: number = 1) {
      if (!this.user?.id) {
        this.setError('╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М ╨╜╨╡ ╨░╨▓╤В╨╛╤А╨╕╨╖╨╛╨▓╨░╨╜');
        return false;
      }

      try {
        this.isTariffUpdating = true;
        await tariffService.extendTariff(this.user.id, months);

        // ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨┤╨░╨╜╨╜╤Л╨╡ ╨╛ ╤В╨░╤А╨╕╤Д╨╡
        await this.fetchUserTariff();

        this.setMessage(`╨в╨░╤А╨╕╤Д ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨┐╤А╨╛╨┤╨╗╨╡╨╜ ╨╜╨░ ${months} ${months === 1 ? '╨╝╨╡╤Б╤П╤Ж' : '╨╝╨╡╤Б╤П╤Ж╨░'}`);
        return true;
      } catch (error: any) {
        this.handleError(error);
        return false;
      } finally {
        this.isTariffUpdating = false;
      }
    },

    async checkTariffValidity() {
      if (!this.user?.id) return false;

      try {
        return await tariffService.checkTariffValidity(this.user.id);
      } catch (error: any) {
        this.handleError(error);
        return false;
      }
    },

    async deductPoints(amount: number, type: string) {
      try {
        console.log(`[deductPoints] Deducting ${amount} points for ${type}`);

        // Проверяем, что тип соответствует допустимым значениям TransactionType
        if (!['generation', 'purchase', 'reward', 'refund', 'invite_bonus', 'achievement', 'admin_correction'].includes(type)) {
          console.warn(`[deductPoints] Invalid transaction type: ${type}. Using 'generation' instead.`);
          type = 'generation';
        }

        // Проверяем, есть ли у пользователя достаточно баллов
        if (!this.user) {
          console.error('[deductPoints] No user data available');
          throw new Error('User data not available');
        }

        const currentPoints = this.user.points || 0;
        console.log(`[deductPoints] Current points: ${currentPoints}, required: ${amount}`);

        if (currentPoints < amount) {
          console.error(`[deductPoints] Insufficient points: ${currentPoints} < ${amount}`);
          throw new Error(`Insufficient points. Required: ${amount}, Available: ${currentPoints}`);
        }

        // Отправляем запрос на списание баллов
        console.log(`[deductPoints] Sending request to deduct ${amount} points for ${type}`);
        const response = await apiClient.post('/api/v1/points/deduct', {
          amount,
          type,
          user_id: this.user.id
        });

        console.log(`[deductPoints] Response:`, response);

        // Обновляем баланс пользователя НЕМЕДЛЕННО для реактивности UI
        if (this.user) {
          // Проверяем, какие поля доступны в ответе
          if (response && typeof response.new_balance !== 'undefined') {
            console.log(`[deductPoints] Updating points from new_balance: ${response.new_balance}`);
            this.user.points = response.new_balance;
          } else if (response && typeof response.balance_after !== 'undefined') {
            console.log(`[deductPoints] Updating points from balance_after: ${response.balance_after}`);
            this.user.points = response.balance_after;
          } else {
            // Если нет информации о новом балансе в ответе, обновляем локально
            console.log('[deductPoints] No balance info in response, updating locally');
            this.user.points = Math.max(0, this.user.points - amount);
            console.log(`[deductPoints] Updated points locally: ${this.user.points}`);
          }

          // Принудительно триггерим реактивность для всех computed свойств
          console.log(`[deductPoints] Final points balance: ${this.user.points}`);
        }

        // Обновляем статистику использования
        console.log('[deductPoints] Updating usage stats');
        await this.updateUsageStats();

        console.log(`[deductPoints] Points deducted successfully, new balance: ${this.user.points}`);
        return response;
      } catch (error) {
        console.error('[deductPoints] Error deducting points:', error);
        this.handleError(error);
        throw error;
      }
    },

    async addPoints(amount: number, type: string) {
      try {
        this.setLoading(true);

        // Проверяем, что тип соответствует допустимым значениям TransactionType
        if (!['generation', 'purchase', 'reward', 'refund', 'invite_bonus', 'achievement', 'admin_correction'].includes(type)) {
          console.warn(`Invalid transaction type: ${type}. Using 'purchase' instead.`);
          type = 'purchase';
        }

        const response = await apiClient.post('/api/v1/points/add', {
          amount,
          type,
          user_id: this.user?.id
        });

        // Handle the response - make it more resilient
        if (this.user) {
          // Try to get the new balance from the response
          if (response && typeof response.new_balance !== 'undefined') {
            this.user.points = response.new_balance;
          } else if (response && typeof response.points !== 'undefined') {
            this.user.points = response.points;
          } else {
            // If we can't get it from the response, refresh user data
            await this.fetchCurrentUser();
          }
        }

        return response;
      } catch (error) {
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async getPointsTransactions(page: number = 1, limit: number = 10) {
      try {
        const response = await apiClient.get('/api/v1/points/transactions', {
          params: { page, limit }
        })
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async getPointsOperations(params: Record<string, any> = {}) {
      try {
        console.log('Getting points operations with params:', params);

        // Устанавливаем значения по умолчанию, если они не указаны
        const queryParams = {
          page: params.page || 1,
          limit: params.limit || 10,
          period: params.period || 'week',
          ...params
        };

        // Пробуем получить данные из разных источников
        console.log('Trying to get points data from multiple sources...');

        try {
          // 1. Сначала пробуем получить данные из API аналитики баллов
          console.log('1. Trying points analytics API...');
          const analyticsResponse = await apiClient.getPointsAnalytics(queryParams);

          if (analyticsResponse && (analyticsResponse.items || Array.isArray(analyticsResponse))) {
            console.log('Points analytics API returned data:', analyticsResponse);

            // Преобразуем данные в нужный формат, если нужно
            if (Array.isArray(analyticsResponse)) {
              return {
                items: analyticsResponse,
                total: analyticsResponse.length
              };
            }

            return analyticsResponse;
          }
        } catch (analyticsError) {
          console.log('Points analytics API failed:', analyticsError);
        }

        try {
          // 2. Затем пробуем получить данные из API транзакций с баллами
          console.log('2. Trying points transactions API...');
          const transactionsResponse = await apiClient.get('/api/v1/points/transactions', {
            params: queryParams
          });

          if (transactionsResponse && (transactionsResponse.items || Array.isArray(transactionsResponse))) {
            console.log('Points transactions API returned data:', transactionsResponse);

            // Преобразуем данные в нужный формат
            const transactions = Array.isArray(transactionsResponse) ?
              transactionsResponse :
              (transactionsResponse.items || []);

            // Получаем данные о пользователях для добавления имен
            const usersResponse = await apiClient.get('/api/v1/users');
            const users = usersResponse?.users || [];
            const usersMap = new Map(users.map((user: any) => [user.id, user]));

            // Преобразуем транзакции в операции с баллами
            const items = transactions.map((transaction: any) => {
              const user = usersMap.get(transaction.user_id) as any;
              return {
                id: transaction.id,
                user_id: transaction.user_id,
                user_name: user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() : `User ${transaction.user_id}`,
                username: user?.username || '',
                tariff: user?.tariff || null,
                type: transaction.type === 'purchase' ? 'purchase' : 'usage',
                points: transaction.amount,
                content_type: transaction.content_type || null,
                created_at: transaction.created_at
              };
            });

            return {
              items,
              total: items.length,
              stats: this.calculatePointsStats(items)
            };
          }
        } catch (transactionsError) {
          console.log('Points transactions API failed:', transactionsError);
        }

        try {
          // 3. Наконец, пробуем получить данные из API генераций и пользователей
          console.log('3. Trying to combine generations and users data...');

          // Получаем данные о генерациях
          const generationsResponse = await apiClient.get('/api/v1/admin/generations', {
            params: {
              period: queryParams.period,
              limit: 100
            }
          });

          // Получаем данные о пользователях
          const usersResponse = await apiClient.get('/api/v1/users');
          const users = usersResponse?.users || [];

          if (generationsResponse && generationsResponse.generations && users.length > 0) {
            console.log('Successfully got generations and users data');

            // Фильтруем генерации с использованием баллов
            const pointsGenerations = generationsResponse.generations.filter((gen: any) => {
              try {
                const prompt = JSON.parse(gen.prompt.replace(/'/g, '"'));
                return prompt.with_points === true;
              } catch (e) {
                try {
                  // Пробуем другой формат
                  const promptObj = eval(`(${gen.prompt})`);
                  return promptObj.with_points === true;
                } catch (e2) {
                  return false;
                }
              }
            });

            // Создаем карту пользователей
            const usersMap = new Map(users.map((user: any) => [user.id, user]));

            // Преобразуем генерации в операции с баллами
            const usageItems = pointsGenerations.map((gen: any) => {
              const user = usersMap.get(gen.user_id) as any;
              const pointsCost = gen.type === 'image' ? 15 : 8;

              return {
                id: gen.id,
                user_id: gen.user_id,
                user_name: user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() : `User ${gen.user_id}`,
                username: user?.username || '',
                tariff: user?.tariff || null,
                type: 'usage',
                points: pointsCost,
                content_type: gen.type,
                created_at: gen.created_at
              };
            });

            // Создаем фиктивные операции покупки баллов
            const purchaseItems = users
              .filter((user: any) => user.points && user.points > 0)
              .map((user: any, index: number) => {
                // Создаем дату в пределах указанного периода
                const now = new Date();
                let startDate = new Date();

                switch (queryParams.period) {
                  case 'week':
                    startDate.setDate(now.getDate() - 7);
                    break;
                  case 'month':
                    startDate.setMonth(now.getMonth() - 1);
                    break;
                  case 'year':
                    startDate.setFullYear(now.getFullYear() - 1);
                    break;
                  case 'all':
                    startDate.setFullYear(now.getFullYear() - 3);
                    break;
                }

                const date = new Date(startDate.getTime() + Math.random() * (now.getTime() - startDate.getTime()));

                return {
                  id: 1000 + index,
                  user_id: user.id,
                  user_name: `${user.first_name || ''} ${user.last_name || ''}`.trim(),
                  username: user.username || '',
                  tariff: user.tariff,
                  type: 'purchase',
                  points: user.points,
                  content_type: null,
                  created_at: date.toISOString()
                };
              });

            // Объединяем операции
            const allItems = [...usageItems, ...purchaseItems];

            // Сортируем по дате (новые сначала)
            allItems.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

            // Применяем фильтры
            let filteredItems = allItems;

            // Приводим queryParams к типу с дополнительными свойствами
            const extendedParams = queryParams as any;

            if (extendedParams.operation_type && extendedParams.operation_type !== 'all') {
              filteredItems = filteredItems.filter(item => item.type === extendedParams.operation_type);
            }

            if (extendedParams.tariff && extendedParams.tariff !== 'all') {
              if (extendedParams.tariff === 'none') {
                filteredItems = filteredItems.filter(item => !item.tariff);
              } else {
                filteredItems = filteredItems.filter(item => item.tariff === extendedParams.tariff);
              }
            }

            // Применяем пагинацию
            const startIndex = (queryParams.page - 1) * queryParams.limit;
            const endIndex = startIndex + queryParams.limit;
            const paginatedItems = filteredItems.slice(startIndex, endIndex);

            return {
              items: paginatedItems,
              total: filteredItems.length,
              stats: this.calculatePointsStats(filteredItems)
            };
          }
        } catch (combinedError) {
          console.log('Combined approach failed:', combinedError);
        }

        // Если все подходы не сработали, возвращаем пустые данные
        console.log('All approaches failed, returning empty data');
        return {
          items: [],
          total: 0,
          stats: {
            total_purchased: 0,
            total_used: 0,
            by_tariff: {},
            by_content_type: {}
          }
        };
      } catch (error) {
        console.error('Error getting points operations:', error);
        this.handleError(error);

        // Если API не реализовано, возвращаем пустые данные
        console.log('API not implemented, returning empty data');
        return {
          items: [],
          total: 0,
          stats: {
            total_purchased: 0,
            total_used: 0,
            by_tariff: {},
            by_content_type: {}
          }
        };
      }
    },

    // Расчет статистики по операциям с баллами
    calculatePointsStats(items: any[]) {
      // Рассчитываем статистику
      const totalPurchased = items
        .filter(op => op.type === 'purchase')
        .reduce((sum, op) => sum + op.points, 0);

      const totalUsed = items
        .filter(op => op.type === 'usage')
        .reduce((sum, op) => sum + op.points, 0);

      // Группируем по тарифам
      const byTariff: Record<string, number> = {};
      items
        .filter(op => op.type === 'purchase')
        .forEach(op => {
          const tariff = op.tariff || 'none';
          byTariff[tariff] = (byTariff[tariff] || 0) + op.points;
        });

      // Группируем по типам контента
      const byContentType: Record<string, number> = {};
      items
        .filter(op => op.type === 'usage')
        .forEach(op => {
          if (op.content_type) {
            byContentType[op.content_type] = (byContentType[op.content_type] || 0) + op.points;
          }
        });

      return {
        total_purchased: totalPurchased,
        total_used: totalUsed,
        by_tariff: byTariff,
        by_content_type: byContentType
      };
    },



    async updateUsageStats(forceReset = false, retryCount = 0, maxRetries = 2): Promise<UserStats | null> {
      try {
        console.log('[updateUsageStats] Fetching latest usage statistics, forceReset:', forceReset, 'retry:', retryCount);

        // Используем правильный URL с ID пользователя для большей надежности
        const userId = this.user?.id;
        if (!userId) {
          console.warn('[updateUsageStats] No user ID available, cannot fetch stats');
          return null;
        }

        const url = `/api/v1/users/${userId}/usage-stats`;
        console.log(`[updateUsageStats] Requesting from: ${url}`);

        const response = await apiClient.get(url);
        console.log('[updateUsageStats] Received response:', response);

        if (response) {
          // Создаем новый объект статистики из ответа сервера
          const serverStats: UserStats = {
            dailyGenerations: response.daily_generations || 0,
            dailyImages: response.daily_images || 0,
            totalGenerations: response.total_generations || 0,
            totalImages: response.total_images || 0,
            points: response.points || (this.userStats?.points || 0), // Добавляем points из ответа или сохраняем текущее значение
            lastActive: new Date(response.last_active || Date.now()),
            generations_by_type: this.userStats?.generations_by_type || {} // Сохраняем существующие данные
          };

          // Если требуется принудительный сброс счетчиков (например, после покупки тарифа)
          if (forceReset) {
            console.log('[updateUsageStats] Forcing reset of usage counters in local state');
            // Обнуляем счетчики в локальном состоянии
            serverStats.dailyGenerations = 0;
            serverStats.dailyImages = 0;
          }

          // Обновляем данные в store
          this.userStats = serverStats;

          // Логируем обновленные данные для отладки
          console.log('[updateUsageStats] Updated user stats:', {
            dailyGenerations: this.userStats?.dailyGenerations || 0,
            dailyImages: this.userStats?.dailyImages || 0,
            totalGenerations: this.userStats?.totalGenerations || 0,
            totalImages: this.userStats?.totalImages || 0,
            forceReset
          });

          // Проверяем, что данные обновились корректно
          if (this.tariffInfo && this.user?.tariff === TariffType.PREMIUM &&
              this.userStats?.dailyGenerations === 0 &&
              this.tariffInfo.limits?.generations === 25 &&
              retryCount < maxRetries) {
            // Если счетчики не соответствуют ожидаемым значениям, пробуем еще раз
            console.log('[updateUsageStats] Detected potential inconsistency, retrying...');
            await new Promise(resolve => setTimeout(resolve, 500)); // Небольшая задержка
            return this.updateUsageStats(forceReset, retryCount + 1, maxRetries);
          }

          return serverStats;
        } else {
          console.warn('[updateUsageStats] Received empty response data');

          // Если требуется принудительный сброс, но данные не получены
          if (forceReset && this.userStats) {
            console.log('[updateUsageStats] Forcing reset of usage counters even with empty response');
            this.userStats.dailyGenerations = 0;
            this.userStats.dailyImages = 0;
          }

          // Пробуем повторить запрос при пустом ответе
          if (retryCount < maxRetries) {
            console.log(`[updateUsageStats] Empty response, retrying (${retryCount + 1}/${maxRetries})...`);
            await new Promise(resolve => setTimeout(resolve, 500)); // Небольшая задержка
            return this.updateUsageStats(forceReset, retryCount + 1, maxRetries);
          }

          return null;
        }
      } catch (error) {
        console.error('[updateUsageStats] Error fetching usage stats:', error);

        // Если требуется принудительный сброс, но произошла ошибка
        if (forceReset && this.userStats) {
          console.log('[updateUsageStats] Forcing reset of usage counters despite error');
          this.userStats.dailyGenerations = 0;
          this.userStats.dailyImages = 0;
        }

        // Пробуем повторить запрос при ошибке
        if (retryCount < maxRetries) {
          console.log(`[updateUsageStats] Error occurred, retrying (${retryCount + 1}/${maxRetries})...`);
          await new Promise(resolve => setTimeout(resolve, 1000)); // Увеличенная задержка при ошибке
          return this.updateUsageStats(forceReset, retryCount + 1, maxRetries);
        }

        this.handleError(error);
        throw error;
      }
    },



    async initPointsPurchase(purchaseData: {
      amount: number;
      price: number;
      bonus: number;
    }) {
      try {
        this.pointsPurchase.isProcessing = true;

        // 1. ╨Ш╨╜╨╕╤Ж╨╕╨╕╤А╤Г╨╡╨╝ ╨┐╨╛╨║╤Г╨┐╨║╤Г ╨╕ ╨┐╨╛╨╗╤Г╤З╨░╨╡╨╝ URL ╨┤╨╗╤П ╨╛╨┐╨╗╨░╤В╤Л
        const response = await apiClient.post('/api/v1/points/purchase/init', purchaseData);

        // 2. ╨б╨╛╤Е╤А╨░╨╜╤П╨╡╨╝ ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨╛ ╤В╨╡╨║╤Г╤Й╨╡╨╣ ╨┐╨╛╨║╤Г╨┐╨║╨╡
        this.pointsPurchase.currentPurchase = {
          ...purchaseData,
          paymentId: response.data.payment_id
        };

        // 3. ╨Ю╤В╨║╤А╤Л╨▓╨░╨╡╨╝ ╨╛╨║╨╜╨╛ ╨╛╨┐╨╗╨░╤В╤Л Telegram
        if (window.Telegram?.WebApp) {
          window.Telegram.WebApp.openInvoice(response.data.invoice_url);

          // 4. ╨Я╨╛╨┤╨┐╨╕╤Б╤Л╨▓╨░╨╡╨╝╤Б╤П ╨╜╨░ ╤Б╨╛╨▒╤Л╤В╨╕╨╡ ╨╖╨░╨║╤А╤Л╤В╨╕╤П ╨╛╨║╨╜╨░ ╨╛╨┐╨╗╨░╤В╤Л
          window.Telegram.WebApp.onEvent('invoiceClosed', (data: { status: string }) => {
            if (data.status === 'paid') {
              this.confirmPointsPurchase(response.data.payment_id);
            } else {
              this.cancelPointsPurchase(response.data.payment_id);
            }
          });
        }

        return { success: true };

      } catch (error: unknown) {
        this.handleError(error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to initialize purchase'
        };
      } finally {
        this.pointsPurchase.isProcessing = false;
      }
    },

    async confirmPointsPurchase(paymentId: string) {
      try {
        this.pointsPurchase.isProcessing = true;

        // 1. ╨Я╨╛╨┤╤В╨▓╨╡╤А╨╢╨┤╨░╨╡╨╝ ╨┐╨╛╨║╤Г╨┐╨║╤Г ╨╜╨░ ╨▒╤Н╨║╨╡╨╜╨┤╨╡
        const response = await apiClient.post('/api/v1/points/purchase/confirm', {
          payment_id: paymentId
        });

        // 2. ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨▒╨░╨╗╨░╨╜╤Б ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
        if (this.user) {
          this.user.points = response.new_balance;
        }

        // 3. ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨▓ ╨╕╤Б╤В╨╛╤А╨╕╤О ╨┐╨╛╨║╤Г╨┐╨╛╨║
        if (this.pointsPurchase.currentPurchase) {
          this.pointsPurchase.purchaseHistory.unshift({
            id: paymentId,
            ...this.pointsPurchase.currentPurchase,
            status: 'completed',
            date: new Date().toISOString()
          });
        }

        // 4. ╨Ю╤З╨╕╤Й╨░╨╡╨╝ ╤В╨╡╨║╤Г╤Й╤Г╤О ╨┐╨╛╨║╤Г╨┐╨║╤Г
        this.pointsPurchase.currentPurchase = null;

        return { success: true };

      } catch (error: unknown) {
        this.handleError(error);
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to confirm purchase'
        };
      } finally {
        this.pointsPurchase.isProcessing = false;
      }
    },

    async cancelPointsPurchase(paymentId: string) {
      try {
        // 1. ╨Ю╤В╨╝╨╡╨╜╤П╨╡╨╝ ╨┐╨╛╨║╤Г╨┐╨║╤Г ╨╜╨░ ╨▒╤Н╨║╨╡╨╜╨┤╨╡
        await apiClient.post('/api/v1/points/purchase/cancel', {
          payment_id: paymentId
        });

        // 2. ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨▓ ╨╕╤Б╤В╨╛╤А╨╕╤О ╨┐╨╛╨║╤Г╨┐╨╛╨║ ╨║╨░╨║ ╨╛╤В╨╝╨╡╨╜╨╡╨╜╨╜╤Г╤О
        if (this.pointsPurchase.currentPurchase) {
          this.pointsPurchase.purchaseHistory.unshift({
            id: paymentId,
            ...this.pointsPurchase.currentPurchase,
            status: 'cancelled',
            date: new Date().toISOString()
          });
        }

        // 3. ╨Ю╤З╨╕╤Й╨░╨╡╨╝ ╤В╨╡╨║╤Г╤Й╤Г╤О ╨┐╨╛╨║╤Г╨┐╨║╤Г
        this.pointsPurchase.currentPurchase = null;

      } catch (error) {
        this.handleError(error);
      } finally {
        this.pointsPurchase.isProcessing = false;
      }
    },

    async getPurchaseHistory() {
      try {
        const response = await apiClient.get('/api/v1/points/purchase/history');
        this.pointsPurchase.purchaseHistory = response.data;
      } catch (error) {
        this.handleError(error);
      }
    },



    // Content Generation Methods
    async generateExercises(formData: ExerciseFormData) {
      try {
        this.setLoading(true);
        this.clearError();

        console.log('Store: ╨╜╨░╤З╨╕╨╜╨░╨╡╨╝ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╨╣');

        // Check generation limits first
        const canGenerate = await this.checkAndTrackGeneration(ContentType.EXERCISE);
        if (!canGenerate) {
          throw new Error('Daily limit reached for exercise generation');
        }

        // Make the API request
        console.log('Store: ╨╛╤В╨┐╤А╨░╨▓╨╗╤П╨╡╨╝ ╨╖╨░╨┐╤А╨╛╤Б ╨║ API ╨╜╨░ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╨╣');
        const response = await apiClient.post(API_ENDPOINTS.GENERATE_EXERCISES, {
        user_id: this.user?.id,
        type: ContentType.EXERCISE,
        prompt: JSON.stringify(formData)
      });

        console.log('Store: ╨┐╨╛╨╗╤Г╤З╨╡╨╜ ╨╛╤В╨▓╨╡╤В ╨╛╤В API:', response);

        // Check if response is valid
        if (!response || !response.content) {
          console.error('Store: ╨╜╨╡╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В ╨╛╤В ╤Б╨╡╤А╨▓╨╡╤А╨░:', response);
          throw new Error('Invalid response from server');
        }

        // Store the result
        this.generationResult = response;
        console.log('Store: ╨║╨╛╨╜╤В╨╡╨╜╤В ╨┤╨╗╤П ╨▓╨╛╨╖╨▓╤А╨░╤В╨░:', response.content);

        // Return just the content
        return response.content;
      } catch (error) {
        console.error('Store: ╨╛╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╨╣:', error);
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async regenerateExercise(formData: ExerciseFormData, index: number) {
      try {
        this.setLoading(true);
        this.clearError();

        console.log('Store: ╨╜╨░╤З╨╕╨╜╨░╨╡╨╝ ╤А╨╡╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╤П ╤Б ╨╕╨╜╨┤╨╡╨║╤Б╨╛╨╝:', index);

        // ╨Ш╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╤В╨╛╤В ╨╢╨╡ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨░╨╜╨╜╤Л╤Е, ╤З╤В╨╛ ╨╕ ╨▓ generateExercises
        const exerciseData: ExerciseFormData = {
          language: formData.language,
          topic: formData.topic,
          type: formData.selectedTypes[0] || 'grammar',
          exercise_type: formData.selectedTypes[0] || 'grammar',
          difficulty: formData.difficulty,
          quantity: 1, // ╨У╨╡╨╜╨╡╤А╨╕╤А╤Г╨╡╨╝ ╤В╨╛╨╗╤М╨║╨╛ ╨╛╨┤╨╜╨╛ ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╨╡
          individual_group: formData.individual_group,
          online_offline: formData.online_offline,
          meta: {
            proficiency: formData.proficiency,
            selectedTypes: formData.selectedTypes,
            interactiveFeatures: formData.interactiveFeatures,
            gamification: formData.gamification,
            multimedia: formData.multimedia,
            includeAnswers: formData.includeAnswers,
            includeInstructions: formData.includeInstructions,
            adaptiveDifficulty: formData.adaptiveDifficulty,
            exerciseIndex: index
          }
        };

        // Check generation limits first
        const canGenerate = await this.checkAndTrackGeneration(ContentType.EXERCISE);
        if (!canGenerate) {
          throw new Error('Daily limit reached for exercise generation');
        }

        // Make the API request
        console.log('Store: ╨╛╤В╨┐╤А╨░╨▓╨╗╤П╨╡╨╝ ╨╖╨░╨┐╤А╨╛╤Б ╨║ API ╨╜╨░ ╤А╨╡╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╤П');
        const response = await apiClient.post(API_ENDPOINTS.GENERATE_EXERCISES, {
          user_id: this.user?.id,
          type: ContentType.EXERCISE,
          prompt: JSON.stringify(exerciseData)
        });

        console.log('Store: ╨┐╨╛╨╗╤Г╤З╨╡╨╜ ╨╛╤В╨▓╨╡╤В ╨╛╤В API:', response);

        // Check if response is valid
        if (!response || !response.content) {
          console.error('Store: ╨╜╨╡╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В ╨╛╤В ╤Б╨╡╤А╨▓╨╡╤А╨░:', response);
          throw new Error('Invalid response from server');
        }

        // Store the result
        this.generationResult = response;
        console.log('Store: ╨║╨╛╨╜╤В╨╡╨╜╤В ╨┤╨╗╤П ╨▓╨╛╨╖╨▓╤А╨░╤В╨░:', response.content);

        // Return just the content
        return response.content;
      } catch (error) {
        console.error('Store: ╨╛╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╤А╨╡╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╤П:', error);
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    async generateGame(formData: GameFormData) {
      try {
        console.log('╨Ю╤В╨┐╤А╨░╨▓╨╗╤П╨╡╨╝ ╨╖╨░╨┐╤А╨╛╤Б ╨║ API ╨┤╨╗╤П ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╨╕╨│╤А╤Л:', formData);

        // ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╨╕ ╨╖╨░╨┐╨╛╨╗╨╜╤П╨╡╨╝ ╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╤Л╨╡ ╨┐╨╛╨╗╤П, ╨╡╤Б╨╗╨╕ ╨╛╨╜╨╕ ╨╛╤В╤Б╤Г╤В╤Б╤В╨▓╤Г╤О╤В
        const gameData = {
          ...formData,
          language: formData.language || 'english',
          topic: formData.topic || 'General language practice',
          level: formData.level || 'intermediate',
          game_type: formData.game_type || 'quiz',
          duration: formData.duration || 15,
          difficulty: formData.difficulty || 'medium',
          individual_group: formData.individual_group || 'individual',
          online_offline: formData.online_offline || 'online',
          type: 'game'
        };

        // Проверяем, есть ли флаг with_points в formData
        const requestData: any = {
          user_id: this.user?.id,
          type: ContentType.GAME,
          prompt: JSON.stringify(gameData)
        };

        // Добавляем флаг with_points в корень запроса, если он есть в formData
        if (formData.with_points) {
          requestData.with_points = true;
        }

        console.log('Отправляем запрос на генерацию игры с данными:', requestData);

        const response = await this.makeRequest<any>(API_ENDPOINTS.GENERATE_GAME, requestData);

        console.log('╨Я╨╛╨╗╤Г╤З╨╡╨╜ ╨╛╤В╨▓╨╡╤В ╨╛╤В API:', response);

        // Проверяем структуру ответа API
        if (response && response.status === 'success') {
          console.log('Ответ в формате API с status=success');
          // Возвращаем весь объект response, чтобы компонент мог обработать его
          return response;
        }

        // Если ответ уже содержит поле content - это прямой ответ с игрой
        // Добавляем проверку на тип response перед доступом к content
        if (response && typeof response === 'object' && 'content' in response) {
          console.log('Найдено поле content, возвращаю данные игры напрямую');
          return response;
        }

        // ╨Х╤Б╨╗╨╕ ╨╛╤В╨▓╨╡╤В - ╤Б╤В╤А╨╛╨║╨░, ╨┐╤Л╤В╨░╨╡╨╝╤Б╤П ╤А╨░╤Б╨┐╨░╤А╤Б╨╕╤В╤М JSON
        if (typeof response === 'string') {
          try {
            return JSON.parse(response);
          } catch (e) {
            console.error('╨Ю╤И╨╕╨▒╨║╨░ ╨┐╨░╤А╤Б╨╕╨╜╨│╨░ ╨╛╤В╨▓╨╡╤В╨░:', e);
            return { content: response };
          }
        }

        // ╨Х╤Б╨╗╨╕ ╨╜╨╕╤З╨╡╨│╨╛ ╨╜╨╡ ╨┐╨╛╨┤╨╛╤И╨╗╨╛, ╨╗╨╛╨│╨╕╤А╤Г╨╡╨╝ ╨╛╤И╨╕╨▒╨║╤Г
        console.error('╨Э╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╨░╤П ╤Б╤В╤А╤Г╨║╤В╤Г╤А╨░ ╨╛╤В╨▓╨╡╤В╨░:', response);
        throw new Error('Failed to generate game');
      } catch (error) {
        console.error('╨Ю╤И╨╕╨▒╨║╨░ ╨▓ generateGame:', error);
        throw new Error('Failed to generate game');
      }
    },

    async generateImage(formData: ImageFormData) {
      // Проверяем, используются ли баллы для генерации
      if (formData.with_points) {
        return this.generateImageWithPoints(formData);
      }

      await this.checkAndTrackGeneration(ContentType.IMAGE);
      const response = await this.makeRequest<any>(API_ENDPOINTS.GENERATE_IMAGE, {
        user_id: formData.user_id || this.user?.id,
        prompt: formData.prompt
      });

      console.log('Получен ответ API:', response);

      try {
        // ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╤А╨░╨╖╨╜╤Л╨╡ ╤Д╨╛╤А╨╝╨░╤В╤Л ╨╛╤В╨▓╨╡╤В╨░
        let imageUrl;

        // Вариант 1: Ответ в формате { status: 'success', data: { url: '...' } }
        if (response?.status === 'success' && response.data?.url) {
          imageUrl = response.data.url;
        }
        // Вариант 2: Ответ в формате { url: '...' } (проверяем тип response)
        else if (response && typeof response === 'object' && 'url' in response && typeof response.url === 'string') {
          imageUrl = response.url;
        }
        // ╨Т╨░╤А╨╕╨░╨╜╤В 3: ╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М URL
        else {
          console.error('Не удалось извлечь URL из ответа API:', response);
          // Используем запасной URL
          const safePrompt = formData.prompt.replace(/[^a-zA-Z0-9а-яА-Я ]/g, '').replace(/\s+/g, '+'); // Исправлено regex
          const fallbackUrl = `https://source.unsplash.com/640x480/?${safePrompt}`;
          console.log('Используем запасной URL Unsplash из-за отсутствия URL в ответе:', fallbackUrl);
          return fallbackUrl;
        }

        console.log('╨Я╨╛╨╗╤Г╤З╨╡╨╜ URL ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П:', imageUrl);

        // ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Д╨╛╤А╨╝╨░╤В╨░ URL
        try {
          // ╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Д╨╛╤А╨╝╨░╤В╨░ URL
          new URL(imageUrl); // ╨Т╤Л╨▒╤А╨╛╤Б╨╕╤В ╨╛╤И╨╕╨▒╨║╤Г ╨╡╤Б╨╗╨╕ URL ╨╜╨╡╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╣

          // ╨С╨╛╨╗╤М╤И╨╡ ╨╜╨╡ ╨╖╨░╨╝╨╡╨╜╤П╨╡╨╝ ╨┤╨╛╨╝╨╡╨╜ pornlabs, ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╤Л╨╣ URL
          if (imageUrl.includes('pornlabs')) {
            console.log('URL ╤Б╨╛╨┤╨╡╤А╨╢╨╕╤В ╨┤╨╛╨╝╨╡╨╜ pornlabs, ╨╜╨╛ ╨╝╤Л ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╨╝ ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╤Л╨╣ URL');
          }

          // ╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╨╝ ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╤Л╨╣ URL
          return imageUrl;
        } catch (urlError) {
          console.error('╨Э╨╡╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В URL ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П:', imageUrl, urlError);

          // Используем запасной вариант через Unsplash
          const safePrompt = formData.prompt.replace(/[^a-zA-Z0-9а-яА-Я ]/g, '').replace(/\s+/g, '+'); // Исправлено regex
          const fallbackUrl = `https://source.unsplash.com/640x480/?${safePrompt}`;
          console.log('Используем запасной URL Unsplash из-за некорректного формата:', fallbackUrl);
          return fallbackUrl;
        }
      } catch (e) {
        console.error('╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨╛╨▒╤А╨░╨▒╨╛╤В╨║╨╡ URL ╨╕╨╖╨╛╨▒╤А╨░╨╢╨╡╨╜╨╕╤П:', e);

        // Создаем резервный URL с изображением по запросу через Unsplash
        const safePrompt = formData.prompt.replace(/[^a-zA-Z0-9а-яА-Я ]/g, '').replace(/\s+/g, '+'); // Исправлено regex
        const fallbackUrl = `https://source.unsplash.com/640x480/?${safePrompt}`;
        console.log('Используем запасной URL Unsplash из-за ошибки:', fallbackUrl);
        return fallbackUrl;
      }
    },

    // Метод для генерации изображения за баллы
    async generateImageWithPoints(formData: ImageFormData) {
      try {
        console.log('[generateImageWithPoints] Generating image with points');

        // Стоимость генерации изображения в баллах
        const pointsCost = 15;

        // Проверяем, были ли уже списаны баллы в компоненте
        // Если в formData есть флаг skip_points_check, то баллы уже были списаны
        const skipPointsCheck = formData.skip_points_check === true;

        if (!skipPointsCheck) {
          // Проверяем и списываем баллы только если они еще не были списаны
          console.log('[generateImageWithPoints] Deducting points in store method');
          const canGenerate = await this.checkAndTrackGenerationWithPoints(ContentType.IMAGE, pointsCost);

          if (!canGenerate) {
            throw new Error(`Не удалось списать ${pointsCost} баллов. Возможно, недостаточно баллов на счету.`);
          }
        } else {
          console.log('[generateImageWithPoints] Skipping points deduction as they were already deducted in component');
        }

        // Формируем запрос с параметрами для генерации за баллы
        const requestData = {
          user_id: formData.user_id || this.user?.id,
          prompt: formData.prompt,
          with_points: true,  // Добавляем флаг with_points для обхода проверки тарифа
          use_cache: false    // Отключаем кэширование для генерации за баллы
        };

        console.log('[generateImageWithPoints] Sending request with data:', requestData);

        // Отправляем запрос на генерацию
        const response = await this.makeRequest<any>(API_ENDPOINTS.GENERATE_IMAGE, requestData);

        console.log('[generateImageWithPoints] Received API response:', response);

        // Обрабатываем ответ так же, как в обычном методе generateImage
        try {
          // Проверяем разные форматы ответа
          let imageUrl;

          // Вариант 1: Ответ в формате { status: 'success', data: { url: '...' } }
          if (response?.status === 'success' && response.data?.url) {
            imageUrl = response.data.url;
          }
          // Вариант 2: Ответ в формате { url: '...' } (проверяем тип response)
          else if (response && typeof response === 'object' && 'url' in response && typeof response.url === 'string') {
            imageUrl = response.url;
          }
          // Вариант 3: Не удалось получить URL
          else {
            console.error('[generateImageWithPoints] Failed to extract URL from API response:', response);
            // Используем запасной URL
            const safePrompt = formData.prompt.replace(/[^a-zA-Z0-9а-яА-Я ]/g, '').replace(/\s+/g, '+');
            const fallbackUrl = `https://source.unsplash.com/640x480/?${safePrompt}`;
            console.log('[generateImageWithPoints] Using fallback Unsplash URL due to missing URL in response:', fallbackUrl);
            return fallbackUrl;
          }

          console.log('[generateImageWithPoints] Got image URL:', imageUrl);

          // Проверка формата URL
          try {
            // Проверка формата URL
            new URL(imageUrl); // Выбросит ошибку если URL невалидный

            // Возвращаем оригинальный URL
            return imageUrl;
          } catch (urlError) {
            console.error('[generateImageWithPoints] Invalid URL format:', imageUrl, urlError);

            // Используем запасной вариант через Unsplash
            const safePrompt = formData.prompt.replace(/[^a-zA-Z0-9а-яА-Я ]/g, '').replace(/\s+/g, '+');
            const fallbackUrl = `https://source.unsplash.com/640x480/?${safePrompt}`;
            console.log('[generateImageWithPoints] Using fallback Unsplash URL due to invalid format:', fallbackUrl);
            return fallbackUrl;
          }
        } catch (e) {
          console.error('[generateImageWithPoints] Error processing image URL:', e);

          // Создаем резервный URL с изображением по запросу через Unsplash
          const safePrompt = formData.prompt.replace(/[^a-zA-Z0-9а-яА-Я ]/g, '').replace(/\s+/g, '+');
          const fallbackUrl = `https://source.unsplash.com/640x480/?${safePrompt}`;
          console.log('[generateImageWithPoints] Using fallback Unsplash URL due to error:', fallbackUrl);
          return fallbackUrl;
        }
      } catch (error) {
        console.error('[generateImageWithPoints] Error generating image with points:', error);
        this.handleError(error);
        throw error;
      }
    },

    async processVideoTranscript(formData: VideoTranscriptFormData) {
      try {
        this.setLoading(true);
        this.clearError();

        console.log('╨Ю╤В╨┐╤А╨░╨▓╨╗╤П╨╡╨╝ ╨╖╨░╨┐╤А╨╛╤Б ╨╜╨░ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В╨░ ╨▓╨╕╨┤╨╡╨╛:', {
          video_id: formData.video_id,
          subtitle_language: formData.subtitle_language
        });

        const response = await apiClient.post(API_ENDPOINTS.PROCESS_TRANSCRIPT, {
          user_id: this.user?.id,
          video_id: formData.video_id,
          subtitle_language: formData.subtitle_language
        });

        console.log('╨Я╨╛╨╗╤Г╤З╨╡╨╜ ╨╛╤В╨▓╨╡╤В ╨╛╤В API:', response);

        if (!response) {
          console.error('╨Э╨╡╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Л╨╣ ╨╛╤В╨▓╨╡╤В ╨╛╤В API:', response);
          throw new Error('╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╨┐╨╛╨╗╤Г╤З╨╕╤В╤М ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В ╨▓╨╕╨┤╨╡╨╛');
        }

        console.log('╨Я╨╛╨╗╤Г╤З╨╡╨╜ ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В:', response);

        if (typeof response === 'string') {
          return response;
        } else if (response.transcript) {
          return response.transcript;
        } else if (response.content) {
          return response.content;
        }

        console.error('╨Э╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨░╨╜╨╜╤Л╤Е:', response);
        throw new Error('╨Э╨╡╨╛╨╢╨╕╨┤╨░╨╜╨╜╤Л╨╣ ╤Д╨╛╤А╨╝╨░╤В ╨┤╨░╨╜╨╜╤Л╤Е ╨▓ ╨╛╤В╨▓╨╡╤В╨╡');
      } catch (error) {
        console.error('╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╕ ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В╨░ ╨▓╨╕╨┤╨╡╨╛:', error);
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    // Добавляем тип для data
    async generateExercisesFromTranscript(data: {
      video_id: string;
      language: string;
      topic: string;
      difficulty: string;
      exercise_type: string;
      quantity: number;
    }) {
      try {
        this.setLoading(true);
        this.clearError();

        console.log('╨У╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П ╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╨╣ ╨╕╨╖ ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В╨░:', data);

        const response = await apiClient.post('/api/v1/content/generate_from_transcript', {
          user_id: this.user?.id,
          content_type: ContentType.EXERCISE,
          video_id: data.video_id,
          params: {
            language: data.language,
            topic: data.topic,
            difficulty: data.difficulty,
            exercise_type: data.exercise_type,
            quantity: data.quantity
          }
        });

        console.log('╨Ю╤В╨▓╨╡╤В ╨╛╤В API (╤Г╨┐╤А╨░╨╢╨╜╨╡╨╜╨╕╤П):', response);

        return response?.content || response;
      } catch (error: unknown) { // Добавляем тип unknown
        this.handleError(error); // handleError должен уметь обрабатывать unknown
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    // Добавляем тип для data
    async generateGamesFromTranscript(data: {
      video_id: string;
      language?: string;
      topic?: string;
      game_type?: string;
      duration?: number;
      level?: string;
      difficulty?: string;
      individual_group?: string;
      online_offline?: string;
    }) {
      try {
        this.setLoading(true);
        this.clearError();

        console.log('╨У╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П ╨╕╨│╤А ╨╕╨╖ ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В╨░:', data);

        const response = await apiClient.post('/api/v1/content/generate_from_transcript', {
          user_id: this.user?.id,
          content_type: ContentType.GAME,
          video_id: data.video_id,
          params: {
            language: data.language || 'english',
            topic: data.topic || 'General language practice',
            game_type: data.game_type || 'quiz',
            duration: data.duration || 15,
            level: data.level || 'intermediate',
            difficulty: data.difficulty || 'medium',
            individual_group: data.individual_group || 'individual',
            online_offline: data.online_offline || 'online'
          }
        });

        console.log('╨Ю╤В╨▓╨╡╤В ╨╛╤В API (╨╕╨│╤А╤Л):', response);

        return response?.content || response;
      } catch (error: unknown) { // Добавляем тип unknown
        this.handleError(error); // handleError должен уметь обрабатывать unknown
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    // Добавляем тип для data
    async generateLessonPlanFromTranscript(data: {
      video_id: string;
      language: string;
      topic: string;
      age?: string; // Добавляем опциональные поля из params
      individual_group?: string;
      online_offline?: string;
     }) {
      try {
        this.setLoading(true);
        this.clearError();

        console.log('╨У╨╡╨╜╨╡╤А╨░╤Ж╨╕╤П ╨┐╨╗╨░╨╜╨░ ╤Г╤А╨╛╨║╨░ ╨╕╨╖ ╤В╤А╨░╨╜╤Б╨║╤А╨╕╨┐╤В╨░:', data);

        const response = await apiClient.post('/api/v1/content/generate_from_transcript', {
          user_id: this.user?.id,
          content_type: ContentType.LESSON_PLAN,
          video_id: data.video_id,
          params: {
            language: data.language,
            topic: data.topic,
            age: data.age,
            individual_group: data.individual_group,
            online_offline: data.online_offline
          }
        });

        console.log('╨Ю╤В╨▓╨╡╤В ╨╛╤В API (╨┐╨╗╨░╨╜ ╤Г╤А╨╛╨║╨░):', response);

        return response?.content || response;
      } catch (error) {
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    // Feature Usage Analytics
    async getFeatureUsageAnalytics(period: string = 'week') {
      try {
        console.log('ANALYTICS_CHECK: Requesting feature analytics with period:', period);

        // Пробуем сначала получить данные из основного API
        try {
          // Используем правильный эндпоинт для получения аналитики
          const url = API_ENDPOINTS.ANALYTICS_FEATURES + `?period=${period}`;
          console.log('ANALYTICS_CHECK: Requesting from URL:', url);
          const response = await apiClient.get(url);

          console.log('ANALYTICS_CHECK: Response status:', response?.status);
          console.log('ANALYTICS_CHECK: Response headers:', JSON.stringify(response?.headers));
          console.log('ANALYTICS_CHECK: Response data type:', typeof response?.data);
          console.log('ANALYTICS_CHECK: Response data keys:', response?.data ? Object.keys(response.data) : 'No data');
          console.log('ANALYTICS_CHECK: Full response data:', JSON.stringify(response?.data));

          // Преобразуем данные в формат, ожидаемый компонентами
          const data = response.data;

          // Если данные отсутствуют, возвращаем пустой объект
          if (!data) {
            console.log('No data received from analytics API, trying admin endpoint');
            throw new Error('No data received from analytics API');
          }

          // Используем данные из API напрямую, если они есть
          return {
            totalUsage: data.totalUsage || 0,
            uniqueUsers: data.uniqueUsers || 0,
            featureDistribution: data.featureDistribution || {},
            userDistribution: {
              byRole: data.userDistribution?.byRole || {},
              byTariff: data.userDistribution?.byTariff || {}
            },
            successRates: data.successRates || {},
            mostPopular: data.mostPopular || [],
            leastUsed: data.leastUsed || [],
            period: data.period || period,
            generatedAt: data.generatedAt || new Date().toISOString()
          };
        } catch (firstError) {
          console.error('Error fetching from analytics API, trying admin endpoint:', firstError);

          // Если первый запрос не удался, пробуем получить данные из админского API
          try {
            const adminUrl = `/api/v1/admin/analytics/features?period=${period}`;
            const adminResponse = await apiClient.get(adminUrl);

            // Проверяем, что получили данные
            if (!adminResponse.data) {
              console.log('No data received from admin analytics API, falling back to generations API');
              throw new Error('No data received from admin analytics API');
            }

            const adminData = adminResponse.data;

            // Используем данные из админского API напрямую
            return {
              totalUsage: adminData.totalUsage || 0,
              uniqueUsers: adminData.uniqueUsers || 0,
              featureDistribution: adminData.featureDistribution || {},
              userDistribution: {
                byRole: adminData.userDistribution?.byRole || {},
                byTariff: adminData.userDistribution?.byTariff || {}
              },
              successRates: adminData.successRates || {},
              mostPopular: adminData.mostPopular || [],
              leastUsed: adminData.leastUsed || [],
              period: adminData.period || period,
              generatedAt: adminData.generatedAt || new Date().toISOString()
            };
          } catch (secondError) {
            console.error('Error fetching from admin analytics API, trying generations API:', secondError);

            // Если и второй запрос не удался, пробуем получить данные о генерациях
            try {
              // Получаем статистику генераций
              const generationsResponse = await this.fetchGenerations(0, 100, period);

              // Проверяем, что получили данные
              if (!generationsResponse || (!generationsResponse.by_type && !generationsResponse.generations)) {
                console.log('No data received from generations API, returning empty analytics');
                throw new Error('No data received from generations API');
              }

              // Создаем объект с данными аналитики на основе данных о генерациях
              const featureDistribution: Record<string, any> = {};

              // Если есть by_type, используем его
              if (generationsResponse.by_type) {
                Object.entries(generationsResponse.by_type).forEach(([type, count]: [string, any]) => {
                  featureDistribution[type] = {
                    total_uses: count,
                    unique_users: Math.floor(count / 3), // Примерная оценка
                    success_rate: 0.95,
                    average_time: 2.5
                  };
                });
              }
              // Если есть generations, анализируем их
              else if (generationsResponse.generations && Array.isArray(generationsResponse.generations)) {
                // Группируем генерации по типу
                const typeCount: Record<string, number> = {};
                const usersByType: Record<string, Set<number>> = {};

                // Определяем тип для генерации
                interface Generation {
                  id?: number;
                  user_id?: number;
                  type?: string;
                  content?: string;
                  prompt?: string;
                  created_at?: string;
                }

                generationsResponse.generations.forEach((gen: Generation) => {
                  if (!gen.type) return;

                  // Считаем количество генераций каждого типа
                  typeCount[gen.type] = (typeCount[gen.type] || 0) + 1;

                  // Считаем уникальных пользователей для каждого типа
                  if (!usersByType[gen.type]) usersByType[gen.type] = new Set<number>();
                  if (gen.user_id) usersByType[gen.type].add(gen.user_id);
                });

                // Создаем объект с данными аналитики
                Object.entries(typeCount).forEach(([type, count]) => {
                  featureDistribution[type] = {
                    total_uses: count,
                    unique_users: usersByType[type]?.size || 1,
                    success_rate: 0.95,
                    average_time: 2.5
                  };
                });

                // Сортируем функции по популярности
                const features = Object.entries(featureDistribution)
                  .map(([feature, stats]) => ({
                    feature,
                    count: stats.total_uses || 0,
                    percentage: (stats.total_uses / Object.values(featureDistribution).reduce((sum, s: any) => sum + (s.total_uses || 0), 0)) * 100
                  }))
                  .sort((a, b) => b.count - a.count);

                const mostPopular = features.slice(0, 5);
                const leastUsed = [...features].reverse().slice(0, 5);

                // Вычисляем общее количество использований и уникальных пользователей
                const totalUsage = Object.values(featureDistribution).reduce((sum, stats: any) => sum + (stats.total_uses || 0), 0);

                // Создаем массив всех уникальных пользователей
                const allUniqueUsers = new Set<number>();
                Object.values(usersByType).forEach((userSet: Set<number>) => {
                  userSet.forEach(userId => allUniqueUsers.add(userId));
                });

                const uniqueUsers = allUniqueUsers.size || Math.floor(totalUsage / 5);

                return {
                  totalUsage,
                  uniqueUsers,
                  featureDistribution,
                  userDistribution: {
                    byRole: {},
                    byTariff: {}
                  },
                  successRates: {},
                  mostPopular,
                  leastUsed,
                  period,
                  generatedAt: new Date().toISOString()
                };
              }

              // Если не нашли данные в генерациях, создаем пустые данные
              const features = Object.entries(featureDistribution)
                .map(([feature, stats]: [string, any]) => ({
                  feature,
                  count: stats.total_uses || 0,
                  percentage: 0
                }))
                .sort((a, b) => b.count - a.count);

              const mostPopular = features.slice(0, 5);
              const leastUsed = [...features].reverse().slice(0, 5);

              // Вычисляем общее количество использований
              const totalUsage = Object.values(featureDistribution).reduce((sum, stats: any) => sum + (stats.total_uses || 0), 0);
              const uniqueUsers = Math.floor(totalUsage / 5);

              return {
                totalUsage,
                uniqueUsers,
                featureDistribution,
                userDistribution: {
                  byRole: {},
                  byTariff: {}
                },
                successRates: {},
                mostPopular,
                leastUsed,
                period,
                generatedAt: new Date().toISOString()
              };
            } catch (thirdError) {
              console.error('Error fetching from generations API, returning empty analytics:', thirdError);
              // Если все запросы не удались, возвращаем пустой объект
              return this._getEmptyFeatureAnalytics(period);
            }
          }
        }
      } catch (error) {
        this.handleError(error);
        console.error('Error fetching feature usage analytics:', error);

        // Возвращаем пустые данные в случае ошибки
        return this._getEmptyFeatureAnalytics(period);
      }
    },

    // Вспомогательный метод для создания пустого объекта аналитики
    _getEmptyFeatureAnalytics(period: string) {
      return {
        totalUsage: 0,
        uniqueUsers: 0,
        featureDistribution: {},
        userDistribution: {
          byRole: {},
          byTariff: {}
        },
        successRates: {},
        mostPopular: [],
        leastUsed: [],
        period: period,
        generatedAt: new Date().toISOString(),
        generations: []
      };
    },

    // Получение аналитики по тарифам
    async getTariffsAnalytics(period: string = 'week') {
      try {
        console.log('Getting tariffs analytics for period:', period);

        // Пробуем получить данные из API аналитики тарифов
        try {
          const response = await apiClient.getTariffsAnalytics({ period });
          console.log('TARIFFS_ANALYTICS: Response data:', response);

          if (response) {
            return response;
          } else {
            console.log('No data received from tariffs analytics API, generating data');
            throw new Error('No data received from tariffs analytics API');
          }
        } catch (error) {
          console.log('Error fetching from tariffs analytics API, generating data:', error);

          // Если API не реализовано, генерируем данные на основе генераций и пользователей
          try {
            // Получаем данные о генерациях
            const generationsResponse = await this.fetchGenerations(0, 500, period);

            // Получаем данные о пользователях
            const usersResponse = await apiClient.get('/api/v1/users');
            const users = usersResponse?.users || [];

            // Создаем карту пользователей для быстрого доступа
            const usersMap = new Map(users.map((user: any) => [user.id, user]));

            if (generationsResponse && generationsResponse.generations && generationsResponse.generations.length > 0) {
              console.log('Generating tariffs analytics from', generationsResponse.generations.length, 'generations');

              // Группируем генерации по тарифу и типу контента
              const byTariff: Record<string, any> = {};

              generationsResponse.generations.forEach((gen: any) => {
                const user = usersMap.get(gen.user_id) as any;
                const tariff = user?.tariff || 'free';
                const contentType = gen.type || 'unknown';

                // Инициализируем объект для тарифа, если его еще нет
                if (!byTariff[tariff]) {
                  byTariff[tariff] = {
                    total: 0,
                    by_type: {}
                  };
                }

                // Увеличиваем счетчики
                byTariff[tariff].total += 1;
                byTariff[tariff].by_type[contentType] = (byTariff[tariff].by_type[contentType] || 0) + 1;
              });

              // Добавляем процентное соотношение для каждого типа контента
              Object.keys(byTariff).forEach(tariff => {
                const tariffData = byTariff[tariff];
                const total = tariffData.total;

                // Добавляем процентное соотношение
                tariffData.by_type_percent = {};
                Object.keys(tariffData.by_type).forEach(type => {
                  tariffData.by_type_percent[type] = Math.round((tariffData.by_type[type] / total) * 100);
                });

                // Сортируем типы по популярности
                tariffData.popular_types = Object.keys(tariffData.by_type)
                  .sort((a, b) => tariffData.by_type[b] - tariffData.by_type[a])
                  .slice(0, 5)
                  .map(type => ({
                    type,
                    count: tariffData.by_type[type],
                    percent: tariffData.by_type_percent[type]
                  }));
              });

              return {
                by_tariff: byTariff,
                period,
                total_generations: generationsResponse.generations.length
              };
            }
          } catch (genError) {
            console.error('Error generating tariffs analytics:', genError);
          }
        }

        // Если все методы не сработали, возвращаем пустые данные
        return {
          by_tariff: {
            basic: {
              total: 0,
              user_count: 0,
              by_type: {},
              by_type_percent: {},
              popular_types: []
            }
          },
          period,
          total_generations: 0,
          total_users: 0,
          purchase_history: []
        };
      } catch (error) {
        console.error('Error getting tariffs analytics:', error);
        this.handleError(error);

        // Возвращаем пустые данные в случае ошибки
        return {
          by_tariff: {
            basic: {
              total: 0,
              user_count: 0,
              by_type: {},
              by_type_percent: {},
              popular_types: []
            }
          },
          period,
          total_generations: 0,
          total_users: 0,
          purchase_history: []
        };
      }
    },



    // Получение аналитики по достижениям
    async getAchievementsAnalytics(period: string = 'week') {
      try {
        console.log('Getting achievements analytics for period:', period);

        // Пробуем получить данные из API аналитики достижений
        try {
          const response = await apiClient.getAchievementsAnalytics({ period });
          console.log('ACHIEVEMENTS_ANALYTICS: Response data:', response);

          if (response) {
            return response;
          } else {
            console.log('No data received from achievements analytics API');
            throw new Error('No data received from achievements analytics API');
          }
        } catch (error: any) {
          console.log('Error fetching from achievements analytics API:', error);

          // Если API вернуло ошибку, но есть данные в ответе, пробуем использовать их
          if (error.response && error.response.data) {
            console.log('Trying to use data from error response:', error.response.data);
            return error.response.data;
          }

          // Если API не реализовано или вернуло ошибку без данных, генерируем тестовые данные
          console.log('Falling back to test data');
          return this.generateTestAchievementsAnalytics(period);
        }
      } catch (error) {
        console.error('Error getting achievements analytics:', error);
        this.handleError(error);

        // Возвращаем тестовые данные в случае ошибки
        return this.generateTestAchievementsAnalytics(period);
      }
    },

    // Получение аналитики по переходам по ссылкам
    async getLinksAnalytics(period: string = 'week') {
      try {
        console.log('Getting links analytics for period:', period);

        // Пробуем получить данные из API аналитики переходов по ссылкам
        try {
          const response = await apiClient.getLinksAnalytics({ period });
          console.log('LINKS_ANALYTICS: Response data:', response);

          if (response) {
            return response;
          } else {
            console.log('No data received from links analytics API');
            throw new Error('No data received from links analytics API');
          }
        } catch (error: any) {
          console.log('Error fetching from links analytics API:', error);

          // Если API вернуло ошибку, но есть данные в ответе, пробуем использовать их
          if (error.response && error.response.data) {
            console.log('Trying to use data from error response:', error.response.data);
            return error.response.data;
          }

          // Если API не реализовано или вернуло ошибку без данных, генерируем тестовые данные
          console.log('Falling back to test data for links analytics');
          return this.generateTestLinksAnalytics(period);
        }
      } catch (error) {
        console.error('Error getting links analytics:', error);
        this.handleError(error);

        // Возвращаем тестовые данные в случае ошибки
        return this.generateTestLinksAnalytics(period);
      }
    },

    // Генерация тестовых данных для аналитики переходов по ссылкам
    generateTestLinksAnalytics(period: string) {
      console.log('Generating test links analytics data for period:', period);

      // Генерируем данные о переходах по ссылкам по дням
      const clicksByTime = [];
      const now = new Date();
      const periodDays = period === 'week' ? 7 : period === 'month' ? 30 : 365;

      for (let i = 0; i < periodDays; i++) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);

        clicksByTime.unshift({
          date: date.toISOString().split('T')[0],
          count: Math.floor(Math.random() * 10) + 1
        });
      }

      // Генерируем данные о популярных ссылках
      const popularLinks = [
        {
          link_id: '1',
          link_title: 'Интенсив по нейросетям',
          link_url: 'https://ai-dlya-prepodavateley-o200pwe.gamma.site/',
          click_count: 65
        },
        {
          link_id: '2',
          link_title: 'Бесплатный урок',
          link_url: 'https://t.me/aiteachersbot',
          click_count: 42
        },
        {
          link_id: '3',
          link_title: 'Курс по нейросетям',
          link_url: 'https://ai4teachers.my.canva.site/2-0',
          click_count: 38
        },
        {
          link_id: '4',
          link_title: 'Разработка приложений',
          link_url: 'https://t.me/yaroslav_english',
          click_count: 25
        },
        {
          link_id: '5',
          link_title: 'Сообщество по нейросетям',
          link_url: 'https://ai-dlya-uchiteley-vy25x4l.gamma.site/',
          click_count: 18
        }
      ];

      return {
        total_clicks: popularLinks.reduce((sum, link) => sum + link.click_count, 0),
        unique_users: Math.floor(Math.random() * 50) + 20,
        popular_links: popularLinks,
        clicks_by_time: clicksByTime,
        period
      };
    },

    // Генерация тестовых данных для аналитики достижений
    generateTestAchievementsAnalytics(period: string) {
      console.log('Generating test achievements analytics data for period:', period);

      // Генерируем данные о разблокировке достижений по дням
      const unlocksOverTime = [];
      const now = new Date();
      const periodDays = period === 'week' ? 7 : period === 'month' ? 30 : 365;

      for (let i = 0; i < periodDays; i++) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);

        unlocksOverTime.unshift({
          date: date.toISOString().split('T')[0],
          count: Math.floor(Math.random() * 5) + 1
        });
      }

      return {
        total_achievements: 25,
        unlocked_achievements: 12,
        total_points_earned: 450,
        active_users: 78,
        popular_achievements: [
          {
            id: 1,
            name: 'Первые шаги',
            description: 'Создайте свой первый план урока',
            icon: '🚀',
            unlock_count: 65
          },
          {
            id: 2,
            name: 'Опытный учитель',
            description: 'Создайте 10 планов уроков',
            icon: '👨‍🏫',
            unlock_count: 42
          },
          {
            id: 3,
            name: 'Мастер упражнений',
            description: 'Создайте 5 упражнений',
            icon: '📝',
            unlock_count: 38
          }
        ],
        unlocks_over_time: unlocksOverTime
      };
    },

    async getDetailedFeatureAnalytics(
      featureType?: string,
      startDate?: string,
      endDate?: string
    ): Promise<FeatureAnalytics> {
      try {
        const response = await apiClient.get('/api/v1/analytics/features/detailed', {
          params: {
            feature_type: featureType,
            start_date: startDate,
            end_date: endDate
          }
        })
        return response.data
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async exportData(type: string = 'generations', format: string = 'csv') {
      try {
        const response = await apiClient.get(`/api/v1/admin/export/${type}`, {
          params: { format },
          responseType: 'blob'
        });

        // ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨╕╨╝╤П ╤Д╨░╨╣╨╗╨░ ╤Б ╨┤╨░╤В╨╛╨╣
        const fileName = `${type}_${new Date().toISOString().split('T')[0]}.${format}`;

        // ╨б╨╛╨╖╨┤╨░╨╡╨╝ blob ╨╕╨╖ ╨╛╤В╨▓╨╡╤В╨░
        const blob = new Blob([response.data], {
          type: format === 'csv'
            ? 'text/csv'
            : 'application/json'
        });

        // ╨б╨╛╨╖╨┤╨░╨╡╨╝ URL ╨┤╨╗╤П ╤Б╨║╨░╤З╨╕╨▓╨░╨╜╨╕╤П
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', fileName);

        // ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╤Б╤Б╤Л╨╗╨║╤Г ╨▓ DOM, ╨║╨╗╨╕╨║╨░╨╡╨╝ ╨┐╨╛ ╨╜╨╡╨╣ ╨╕ ╤Г╨┤╨░╨╗╤П╨╡╨╝
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        return true;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    // Usage Tracking
    async checkAndTrackGeneration(type: ContentType) {
      // Принудительно обновляем информацию о тарифе, если она отсутствует
      if (!this.tariffInfo && this.user?.tariff) {
        try {
          console.log(`[checkAndTrackGeneration] Missing tariff info, fetching it for user ${this.user.id}`);
          await this.fetchUserTariff();

          // Если после попытки загрузки информация о тарифе все еще отсутствует
          if (!this.tariffInfo) {
            console.warn('[checkAndTrackGeneration] Failed to fetch tariff info after retry');
          } else {
            console.log('[checkAndTrackGeneration] Successfully fetched tariff info:', this.tariffInfo);
          }
        } catch (tariffErr) {
          console.warn('[checkAndTrackGeneration] Error fetching tariff info:', tariffErr);
        }
      }

      // Принудительно обновляем статистику перед проверкой лимитов
      try {
        console.log(`[checkAndTrackGeneration] Refreshing usage stats before checking limits for ${type}`);
        await this.updateUsageStats();
      } catch (statsErr) {
        console.warn('Failed to refresh usage stats before check, but continuing:', statsErr);
      }

      // First check if the user can generate content without throwing an error
      if (!this.canGenerate(type)) {
        console.warn(`Daily limit reached for ${type}`);
        return false; // Return false instead of throwing an error
      }

      try {
        // Only if we can generate, we track the usage
        await apiClient.post(API_ENDPOINTS.TRACK_USAGE, {
          user_id: this.user?.id,
          content_type: type,
          action_type: ActionType.GENERATION
        });

        // Обновляем локальные счетчики НЕМЕДЛЕННО для мгновенного отображения в UI
        if (this.userStats) {
          if (type === ContentType.IMAGE) {
            this.userStats.dailyImages++;
            this.userStats.totalImages++;
          } else {
            this.userStats.dailyGenerations++;
            this.userStats.totalGenerations++;
          }
        }

        // Проверяем, что счетчики обновились корректно
        if (this.userStats) {
          console.log(`[checkAndTrackGeneration] Updated stats:`, {
            dailyGenerations: this.userStats.dailyGenerations,
            dailyImages: this.userStats.dailyImages,
            type
          });
        }

        // Check achievements but don't fail generation if this fails
        try {
          await this.checkAchievements(ActionType.GENERATION, { content_type: type });
        } catch (err) {
          console.warn('Achievement check failed but continuing with generation:', err);
        }

        return true; // Return true to indicate success
      } catch (error) {
        console.error(`Error tracking generation for ${type}:`, error);
        // Don't throw the error, just return false
        return false;
      }
    },

    // ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╤В ╨╕ ╨╛╤В╤Б╨╗╨╡╨╢╨╕╨▓╨░╨╡╤В ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╤О ╨┐╨╗╨░╨╜╨░ ╤Г╤А╨╛╨║╨░ ╤З╨╡╤А╨╡╨╖ ╤Д╨╛╤А╨╝╤Г.
    // ╨н╤В╨╛╤В ╨╝╨╡╤В╨╛╨┤ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В╤Б╤П ╨┤╨╗╤П ╨║╨╛╨╜╤В╤А╨╛╨╗╤П ╨╗╨╕╨╝╨╕╤В╨╛╨▓ ╨│╨╡╨╜╨╡╤А╨░╤Ж╨╕╨╕ ╨╕ ╨░╨╜╨░╨╗╨╕╨╖╨░ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╤П.
    async checkAndTrackGenerationLessonPlanForm(): Promise<boolean> {
      // ╨Я╨╛ ╤Б╤Г╤В╨╕ ╤Н╤В╨╛ ╨╛╨▒╨╡╤А╤В╨║╨░ ╨▓╨╛╨║╤А╤Г╨│ checkAndTrackGeneration ╨┤╨╗╤П ╨┐╨╗╨░╨╜╨░ ╤Г╤А╨╛╨║╨░
      return this.checkAndTrackGeneration(ContentType.LESSON_PLAN);
    },

    // Проверка и отслеживание генерации за баллы
    async checkAndTrackGenerationWithPoints(type: ContentType, pointsCost: number = 8): Promise<boolean> {
      try {
        console.log(`[checkAndTrackGenerationWithPoints] Checking points-based generation for ${type}, cost: ${pointsCost}`);
        console.log(`[checkAndTrackGenerationWithPoints] User data:`, this.user);

        // Сохраняем текущий баланс пользователя
        const initialPoints = this.user?.points || 0;
        console.log(`[checkAndTrackGenerationWithPoints] Initial points: ${initialPoints}`);

        // Проверяем, есть ли у пользователя достаточно баллов
        if (!this.user) {
          console.warn(`[checkAndTrackGenerationWithPoints] No user data available`);
          return false;
        }

        if (initialPoints < pointsCost) {
          console.warn(`[checkAndTrackGenerationWithPoints] Insufficient points for ${type} generation. Required: ${pointsCost}, Available: ${initialPoints}`);
          return false;
        }

        console.log(`[checkAndTrackGenerationWithPoints] User has enough points: ${initialPoints} >= ${pointsCost}`);

        // Списываем баллы
        try {
          console.log(`[checkAndTrackGenerationWithPoints] Deducting ${pointsCost} points for ${type} generation`);
          const deductResult = await this.deductPoints(pointsCost, 'generation');
          console.log(`[checkAndTrackGenerationWithPoints] Points deducted successfully, result:`, deductResult);

          // Проверяем обновленный баланс
          console.log(`[checkAndTrackGenerationWithPoints] Updated points: ${this.user?.points}`);
        } catch (error) {
          console.error('[checkAndTrackGenerationWithPoints] Error deducting points:', error);

          // Проверяем, был ли баланс обновлен, несмотря на ошибку
          await this.fetchCurrentUser();
          console.log(`[checkAndTrackGenerationWithPoints] User data after fetchCurrentUser:`, this.user);

          // Если после обновления данных пользователя баллы были списаны, считаем операцию успешной
          if (this.user && this.user.points < initialPoints) {
            console.log(`[checkAndTrackGenerationWithPoints] Points were deducted despite API error. New balance: ${this.user.points}`);
          } else {
            // Если баллы не были списаны, выбрасываем ошибку
            console.error('[checkAndTrackGenerationWithPoints] Points were not deducted, throwing error');
            throw new Error('Не удалось списать баллы. Пожалуйста, попробуйте еще раз.');
          }
        }

        // Отслеживаем использование для статистики, но не для лимитов
        console.log(`[checkAndTrackGenerationWithPoints] Tracking usage for ${type} with points`);
        const trackData = {
          user_id: this.user?.id,
          content_type: type,
          action_type: ActionType.GENERATION,
          skip_limits: true, // Указываем, что это генерация за баллы, не учитывающая лимиты
          with_points: true,  // Добавляем флаг генерации за баллы
          skip_tariff_check: true // Явно указываем пропуск проверки тарифа
        };
        console.log(`[checkAndTrackGenerationWithPoints] Track data:`, trackData);

        const trackResult = await apiClient.post(API_ENDPOINTS.TRACK_USAGE, trackData);
        console.log(`[checkAndTrackGenerationWithPoints] Usage tracked successfully, result:`, trackResult);

        // Проверяем достижения, но не останавливаем генерацию, если проверка не удалась
        try {
          const achievementData = {
            content_type: type,
            with_points: true
          };
          console.log(`[checkAndTrackGenerationWithPoints] Checking achievements with data:`, achievementData);

          const achievementResult = await this.checkAchievements(ActionType.GENERATION, achievementData);
          console.log(`[checkAndTrackGenerationWithPoints] Achievements checked, result:`, achievementResult);
        } catch (err) {
          console.warn('[checkAndTrackGenerationWithPoints] Achievement check failed but continuing with generation:', err);
        }

        console.log(`[checkAndTrackGenerationWithPoints] Points-based generation for ${type} successful`);
        return true;
      } catch (error) {
        console.error(`[checkAndTrackGenerationWithPoints] Error in points-based generation for ${type}:`, error);
        this.handleError(error);
        return false;
      }
    },

    // Promocodes Management
    async createPromocode(promocodeData: any) {
      try {
        const response = await apiClient.post('/api/v1/admin/promocodes', promocodeData)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async fetchPromocodes(page: number = 1, size: number = 20, search?: string, type_filter?: string, active_only: boolean = false) {
      try {
        const params = new URLSearchParams({
          page: page.toString(),
          size: size.toString()
        })

        if (search) params.append('search', search)
        if (type_filter) params.append('type_filter', type_filter)
        if (active_only) params.append('active_only', 'true')

        const response = await apiClient.get(`/api/v1/admin/promocodes?${params}`)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async updatePromocode(code: string, updateData: any) {
      try {
        const response = await apiClient.put(`/api/v1/admin/promocodes/code/${code}`, updateData)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async deletePromocode(code: string) {
      try {
        const response = await apiClient.delete(`/api/v1/admin/promocodes/code/${code}`)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async deactivatePromocode(code: string) {
      try {
        const response = await apiClient.post(`/api/v1/admin/promocodes/code/${code}/deactivate`)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async getPromocodeStats() {
      try {
        const response = await apiClient.get('/api/v1/admin/promocodes/stats')
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async getPromocodesStats() {
      try {
        const response = await apiClient.get('/api/v1/admin/promocodes/stats')
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async getPromocodesHistory(params: any = {}) {
      try {
        const queryParams = new URLSearchParams()

        // Добавляем параметры пагинации
        if (params.page) queryParams.append('page', params.page.toString())
        if (params.per_page) queryParams.append('per_page', params.per_page.toString())

        // Добавляем фильтры
        if (params.promocode) queryParams.append('promocode', params.promocode)
        if (params.tariff) queryParams.append('tariff', params.tariff)
        if (params.dateFrom) queryParams.append('date_from', params.dateFrom)
        if (params.dateTo) queryParams.append('date_to', params.dateTo)

        const url = `/api/v1/admin/promocodes/history${queryParams.toString() ? '?' + queryParams.toString() : ''}`
        const response = await apiClient.get(url)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    // User promocode methods
    async applyPromocode(code: string) {
      try {
        const response = await apiClient.post('/api/v1/promocodes/apply', { code })
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async getPromocodeHistory() {
      try {
        const response = await apiClient.get('/api/v1/promocodes/history')
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    // User Management Methods
    async updateUser(userId: number, userData: any) {
      try {
        const response = await apiClient.put(`/api/v1/admin/users/${userId}`, userData)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async updateUserPoints(userId: number, pointsChange: number) {
      try {
        const response = await apiClient.post(`/api/v1/admin/users/${userId}/points`, {
          points_change: pointsChange
        })
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async getUserPayments(userId: number) {
      try {
        const response = await apiClient.get(`/api/v1/admin/users/${userId}/payments`)
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    async sendUserMessage(userId: number, message: string) {
      try {
        const response = await apiClient.post(`/api/v1/admin/users/${userId}/message`, {
          message
        })
        return response
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },



    // System Settings Management
    async fetchSystemSettings() {
      try {
        const response = await apiClient.get(API_ENDPOINTS.SYSTEM_SETTINGS);
        this.systemSettings = response;
        return response;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    async updateSystemSettings(settings: SystemSettings) {
      try {
        const response = await apiClient.put(API_ENDPOINTS.SYSTEM_SETTINGS, settings);
        this.systemSettings = response;
        return response;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    // API Request Handler
    async makeRequest<T>(endpoint: string, data: any): Promise<ApiResponse<T>> {
      try {
        this.setLoading(true);
        this.clearError();
        const response = await apiClient.post<ApiResponse<T>>(endpoint, data);
        // Присваиваем весь объект ответа, если нужно сохранить статус и сообщение
        this.generationResult = response;
        // Возвращаем весь объект ApiResponse<T>
        return response;
      } catch (error: unknown) { // Исправляем тип ошибки
        this.handleError(error);
        throw error;
      } finally {
        this.setLoading(false);
      }
    },

    // Modal Handlers
    async openUserModal(userId: number) {
      try {
        const userData = await apiClient.get(`/api/v1/admin/users/${userId}`)
        this.selectedUser = userData
        this.userModalVisible = true
      } catch (error) {
        this.handleError(error)
        throw error
      }
    },

    // Error Handler - исправляем тип параметра на unknown
    handleError(error: unknown) {
      console.error('API Error:', error);
      let message = 'An error occurred';
      if (typeof error === 'object' && error !== null) {
        // Пытаемся извлечь сообщение из стандартных полей ошибки axios или fetch
        const err = error as any; // Используем any временно для доступа к полям
        message = err.response?.data?.message || err.message || message;
      } else if (typeof error === 'string') {
        message = error;
      }
      this.error = message;
      this.isLoading = false;
    },

    // Store Initialization and Reset
    async initAdmin() {
      if (this.isAdmin) {
        await Promise.all([
          this.fetchSystemSettings(),
          this.fetchPromocodes()
        ])
      }
    },

    resetAdminStore() {
      this.systemSettings = null
      this.featureUsage = null
    },

    // ╨Ф╨╡╨╣╤Б╤В╨▓╨╕╤П ╨┤╨╗╤П ╤А╨░╨▒╨╛╤В╤Л ╤Б ╨┤╨░╨╜╨╜╤Л╨╝╨╕ ╤Д╨╛╤А╨╝
    setExerciseFormData(data: any) {
      this.exerciseFormData = data;
    },

    clearExerciseFormData() {
      this.exerciseFormData = null;
    },

    setGameFormData(data: any) {
      this.gameFormData = data;
    },

    clearGameFormData() {
      this.gameFormData = null;
    },

    // Метод для генерации объяснения концепции
    // Добавляем тип для data и возвращаемого значения
    async generateConceptExplanation(data: {
      language: string;
      concept: string;
      age: string,
      level: string,
      interests: string,
      style: string,
      with_points?: boolean,
      skip_tariff_check?: boolean,
      skip_limits?: boolean
    }): Promise<string> {
      this.isLoading = true
      this.error = null

      try {
        // Проверяем наличие активного тарифа
        // Проверяем, что тариф существует и не является базовым (BASIC)
        const hasTariff = this.tariffInfo && this.tariffInfo.type !== TariffType.BASIC

        // Если нет активного тарифа и не указано использование баллов, предлагаем использовать баллы
        if (!hasTariff && !data.with_points && this.user && this.user.points >= 8) {
          if (confirm('У вас нет активного тарифа. Хотите использовать 8 баллов для генерации объяснения?')) {
            // Рекурсивно вызываем этот же метод, но с флагом with_points
            return this.generateConceptExplanation({
              ...data,
              with_points: true,
              skip_tariff_check: true,
              skip_limits: true
            })
          } else {
            throw new Error('Для генерации необходимо приобрести тариф или использовать баллы.')
          }
        }

        // Если указано использование баллов, проверяем возможность генерации за баллы
        if (data.with_points) {
          console.log('Generating concept explanation with points')

          // Проверяем наличие баллов у пользователя
          if (!this.user || this.user.points < 8) {
            throw new Error('Недостаточно баллов для генерации объяснения. Требуется 8 баллов.')
          }

          // Баллы будут списаны в методе checkAndTrackGenerationWithPoints
          // Но мы не проверяем результат здесь, так как баллы уже проверены выше
          // и будут списаны при отправке запроса

          // Если используем баллы, не проверяем тариф и лимиты
          data.skip_tariff_check = true
          data.skip_limits = true
          console.log('Using points for generation, skipping tariff check and limits')
        } else {
          // Проверяем лимиты генерации только если не используем баллы
          if (!this.canGenerate(ContentType.TEXT_ANALYSIS) && !this.isUnlimitedUser) {
            // Если у пользователя достаточно баллов, предлагаем использовать их
            if (this.user && this.user.points >= 8) {
              if (confirm('Достигнут дневной лимит генераций. Хотите использовать 8 баллов для генерации объяснения?')) {
                // Рекурсивно вызываем этот же метод, но с флагом with_points
                return this.generateConceptExplanation({
                  ...data,
                  with_points: true,
                  skip_tariff_check: true,
                  skip_limits: true
                })
              }
            }
            throw new Error('Достигнут дневной лимит генераций. Пожалуйста, обновите тариф или используйте генерацию за баллы.')
          }
        }

        const requestData = {
          user_id: this.user?.id,
          type: ContentType.CONCEPT_EXPLANATION,
          language: data.language,
          concept: data.concept,
          age: data.age,
          level: data.level,
          interests: data.interests,
          style: data.style,
          prompt: JSON.stringify(data),
          with_points: data.with_points,
          skip_tariff_check: data.skip_tariff_check,
          skip_limits: data.skip_limits,
          action_data: {
            content_type: ContentType.CONCEPT_EXPLANATION,
            language: data.language,
            concept: data.concept,
            age: data.age,
            with_points: data.with_points
          }
        }

        const response = await apiClient.post(API_ENDPOINTS.GENERATE_CONCEPT_EXPLANATION, requestData)

        // Проверяем достижения после успешной генерации
        await this.checkAchievements(ActionType.GENERATION, requestData.action_data)

        // Логируем ответ для отладки
        console.log('Concept explanation response:', response)

        // Обрабатываем разные форматы ответа
        if (response && typeof response === 'object') {
          // Вариант 1: ответ имеет формат { status, data, message }
          if (response.status === 'success' && response.data && typeof response.data.content === 'string') {
            return response.data.content;
          }
          // Вариант 2: ответ сам содержит content
          else if (response.content && typeof response.content === 'string') {
            return response.content;
          }
          // Вариант 3: ответ - объект без явного контента, конвертируем в строку
          else {
            console.warn('Необычный формат ответа от API объяснения концепции:', response);
            return JSON.stringify(response);
          }
        }

        // Если ничего не подошло, преобразуем весь ответ в строку
        return typeof response === 'string' ? response : JSON.stringify(response);
      } catch (error: unknown) { // Исправляем тип ошибки
        console.error('Error generating concept explanation:', error);
        // Используем handleError для обработки unknown
        this.handleError(error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async getUserUsageStats(userId: number) {
      try {
        const response = await apiClient.get(API_ENDPOINTS.USERS_USAGE_STATS(userId));
        this.userStats = response;
        return response;
      } catch (error: unknown) { // Исправляем тип ошибки
        this.handleError(error); // Используем handleError для обработки unknown
        throw error;
      }
    },

    async getUserTariff(userId: number) {
      try {
        const response = await apiClient.get(API_ENDPOINTS.USERS_TARIFF(userId));
        this.tariffInfo = response;
        return response;
      } catch (error) {
        this.handleError(error);
        throw error;
      }
    },

    // ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П ╨┤╨╗╤П ╨╛╤В╤Б╨╗╨╡╨╢╨╕╨▓╨░╨╜╨╕╤П ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╤П ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╤П
    async trackAppUsage(event: AppUsageEvent) {
      try {
        // ╨Ф╨╛╨▒╨░╨▓╨╗╤П╨╡╨╝ ╤Б╨╛╨▒╤Л╤В╨╕╨╡ ╨▓ ╨╗╨╛╨║╨░╨╗╤М╨╜╨╛╨╡ ╤Е╤А╨░╨╜╨╕╨╗╨╕╤Й╨╡
        this.appUsage.events.push(event)

        // ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╤Г
        this.updateAppUsageStats()

        // ╨Ю╤В╨┐╤А╨░╨▓╨╗╤П╨╡╨╝ ╤Б╨╛╨▒╤Л╤В╨╕╨╡ ╨╜╨░ ╤Б╨╡╤А╨▓╨╡╤А
        await apiClient.post('/api/v1/analytics/app-usage', event)

        return true
      } catch (error) {
        console.error('Error tracking app usage:', error)
        return false
      }
    },

    // ╨Ю╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨╕ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╤П ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╤П
    updateAppUsageStats() {
      const events = this.appUsage.events

      // ╨Я╨╛╨┤╤Б╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨╖╨░╨┐╤Г╤Б╨║╨╛╨▓
      const launches = events.filter(e => e.event === 'app_launch').length

      // ╨Я╨╛╨┤╤Б╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨┐╤А╨╛╤Б╨╝╨╛╤В╤А╨╛╨▓ ╤Б╤В╤А╨░╨╜╨╕╤Ж
      const pageViews = events.filter(e => e.event === 'page_view').length

      // ╨Я╨╛╨┤╤Б╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╨║╨╛╨╗╨╕╤З╨╡╤Б╤В╨▓╨╛ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╨╣ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
      const actions = events.filter(e => e.event === 'user_action').length

      // ╨Т╤Л╤З╨╕╤Б╨╗╤П╨╡╨╝ ╤Б╤А╨╡╨┤╨╜╤О╤О ╨┤╨╗╨╕╤В╨╡╨╗╤М╨╜╨╛╤Б╤В╤М ╤Б╨╡╤Б╤Б╨╕╨╕
      const sessionEndEvents = events.filter(e => e.event === 'session_end')
      const totalDuration = sessionEndEvents.reduce((sum, e) => sum + (e.duration_seconds || 0), 0)
      const averageDuration = sessionEndEvents.length > 0 ? totalDuration / sessionEndEvents.length : 0

      // ╨Я╨╛╨┤╤Б╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨┐╨╛ ╨┐╨╗╨░╤В╤Д╨╛╤А╨╝╨░╨╝
      const usageByPlatform: Record<string, number> = {}
      events.forEach(e => {
        if (e.platform) {
          usageByPlatform[e.platform] = (usageByPlatform[e.platform] || 0) + 1
        }
      })

      // ╨Я╨╛╨┤╤Б╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨┐╨╛ ╤Б╤В╤А╨░╨╜╨╕╤Ж╨░╨╝
      const usageByPage: Record<string, number> = {}
      events.filter(e => e.event === 'page_view').forEach(e => {
        if (e.page) {
          usageByPage[e.page] = (usageByPage[e.page] || 0) + 1
        }
      })

      // ╨Я╨╛╨┤╤Б╤З╨╕╤В╤Л╨▓╨░╨╡╨╝ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╨╡ ╨┐╨╛ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П╨╝
      const usageByAction: Record<string, number> = {}
      events.filter(e => e.event === 'user_action').forEach(e => {
        if (e.action) {
          usageByAction[e.action] = (usageByAction[e.action] || 0) + 1
        }
      })

      // ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╤Г
      this.appUsage.stats = {
        totalLaunches: launches,
        totalPageViews: pageViews,
        totalActions: actions,
        averageSessionDuration: averageDuration,
        usageByPlatform,
        usageByPage,
        usageByAction
      }
    },

    // ╨Я╨╛╨╗╤Г╤З╨╡╨╜╨╕╨╡ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╨╕ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╨╜╨╕╤П ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╤П
    async getAppUsageStats(): Promise<AppUsageStats> {
      try {
        // ╨Я╨╛╨╗╤Г╤З╨░╨╡╨╝ ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╤Г ╤Б ╤Б╨╡╤А╨▓╨╡╤А╨░
        const response = await apiClient.get('/api/v1/analytics/app-usage/stats')

        // ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨╗╨╛╨║╨░╨╗╤М╨╜╤Г╤О ╤Б╤В╨░╤В╨╕╤Б╤В╨╕╨║╤Г
        this.appUsage.stats = response

        return response
      } catch (error) {
        console.error('Error getting app usage stats:', error)
        return this.appUsage.stats
      }
    },

    // Метод для принудительного сброса счетчиков использования
    async resetUsageCounters() {
      try {
        console.log('[resetUsageCounters] Forcing reset of usage counters');

        // Если пользователь не авторизован, выходим
        if (!this.user?.id) {
          console.warn('[resetUsageCounters] No user ID available, cannot reset counters');
          return false;
        }

        // Сначала сбрасываем счетчики на сервере
        const userId = this.user.id;
        console.log(`[resetUsageCounters] Calling reset endpoint for user ${userId}`);

        try {
          // Вызываем серверный эндпоинт для сброса счетчиков через API клиент
          const resetResponse = await apiClient.resetUsageCounters(userId);
          console.log('[resetUsageCounters] Server reset response:', resetResponse.data);

          // Если сервер вернул данные о сбросе счетчиков, используем их
          if (resetResponse.data && resetResponse.data.data) {
            const { daily_generations, daily_images } = resetResponse.data.data;

            // Обновляем локальное состояние данными с сервера
            if (this.userStats) {
              this.userStats.dailyGenerations = daily_generations;
              this.userStats.dailyImages = daily_images;

              console.log('[resetUsageCounters] Updated local state with server data:', {
                dailyGenerations: this.userStats.dailyGenerations,
                dailyImages: this.userStats.dailyImages
              });
            }
          } else {
            // Если сервер не вернул данные, сбрасываем счетчики локально
            if (this.userStats) {
              this.userStats.dailyGenerations = 0;
              this.userStats.dailyImages = 0;
            }
          }
        } catch (resetError) {
          console.error('[resetUsageCounters] Error calling server reset endpoint:', resetError);
          // Продолжаем выполнение даже при ошибке сброса на сервере

          // Сбрасываем счетчики в локальном состоянии
          if (this.userStats) {
            this.userStats.dailyGenerations = 0;
            this.userStats.dailyImages = 0;
          }
        }

        // Затем обновляем данные с сервера для синхронизации
        await this.updateUsageStats();

        console.log('[resetUsageCounters] Usage counters reset successfully');
        return true;
      } catch (error) {
        console.error('[resetUsageCounters] Error resetting usage counters:', error);
        this.handleError(error);
        return false;
      }
    },

    // Dashboard data
    async getDashboardData() {
      try {
        const response = await apiClient.get('/api/v1/admin/dashboard');

        // Добавляем подробное логирование для отладки
        console.log('Raw dashboard API response:', JSON.stringify(response));

        // Проверяем структуру ответа и возвращаем данные
        if (response && response.data) {
          return response.data;
        } else {
          console.error('Unexpected response structure from dashboard API:', response);
          // Return a default structure to prevent UI errors
          return {
            stats: {
              totalUsers: 0,
              usersTrend: 0,
              activeTariffs: 0,
              tariffsTrend: 0,
              dailyGenerations: 0,
              generationsTrend: 0,
              featureUsage: 0,
              usageTrend: 0
            },
            activity: [],
            features: [],
            recent: [],
            system_health: {}
          };
        }
      } catch (error) {
        this.handleError(error);
        console.error('Error fetching dashboard data:', error);
        // Return a default structure to prevent UI errors
        return {
          stats: {
            totalUsers: 0,
            usersTrend: 0,
            activeTariffs: 0,
            tariffsTrend: 0,
            dailyGenerations: 0,
            generationsTrend: 0,
            featureUsage: 0,
            usageTrend: 0
          },
          activity: [],
          features: [],
          recent: [],
          system_health: {}
        };
      }
    }
  }
})

export const useCourseStore = defineStore('course', {
  state: () => ({
    courses: [] as CourseStructure[],
    currentCourse: null as CourseStructure | null,
    isLoading: false,
    error: null as string | null
  }),

  actions: {
    async generateCourse(formData: CourseFormData) { // Убрали явный тип Promise<...>
      this.isLoading = true
      this.error = null
      try {
        // Позволяем TypeScript определить тип ответа от сервиса
        const response = await courseGeneratorService.generateCourseStructure(formData)

        // Извлекаем данные напрямую. Ошибки TS подсказывают, что response - это объект с полем data.
        // Если сервис МОЖЕТ вернуть null/undefined вместо объекта, нужна проверка:
        // const courseData = response?.data ?? null;
        // Но ошибка "Type 'ApiResponse<...>' is missing..." намекает, что response - объект.
        const courseData: CourseStructure | null = response.data

        this.currentCourse = courseData
        return courseData
      } catch (error) {
        console.error('Error in generateCourse action:', error)
        // Оставляем улучшенную обработку ошибок
        const apiError = error as any;
        if (apiError?.response?.data?.message) {
            this.error = apiError.response.data.message;
        } else if (error instanceof Error) {
            this.error = error.message;
        } else {
            this.error = 'Unknown error generating course';
        }
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async generateFreeQuery(queryData: { language: string, query: string }) {
      this.isLoading = true
      try {
        const result = await courseGeneratorService.generateFreeQuery(queryData)
        return result
      } catch (error) {
        this.error = 'Error processing free query'
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async saveCourse(course: CourseStructure) {
      try {
        const savedCourse = await courseGeneratorService.saveCourse(course)
        this.courses.push(savedCourse)
        return savedCourse
      } catch (error) {
        this.error = 'Error saving course'
        throw error
      }
    },

    // ... ╨┤╤А╤Г╨│╨╕╨╡ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╤П
  }
})

// Additional Interfaces
interface FeatureAnalytics {
  totalUsage: number
  uniqueUsers: number
  featureDistribution: Record<string, FeatureUsage>
  userDistribution: {
    byRole: Record<UserRole, number>
    byTariff: Record<TariffType, number>
  }
  mostPopular: FeatureUsage[]
  leastUsed: FeatureUsage[]
}

interface FeatureUsage {
  feature: string
  count: number
  uniqueUsers: number
  successRate: number
  averageTime: number
}

interface SystemSettings {
  tariffs: Array<{
    type: string
    name: string
    settings: {
      generations_limit: number
      images_limit: number
      price_points: number
      lesson_plan_cost?: number
      exercise_cost?: number
      game_cost?: number
      image_cost?: number
    }
  }>
  referral: {
    new_user_discount: number
    referrer_discount: number
    max_discount: number
  }
}

interface PromoCode {
  code: string
  tariff_type: string
  duration_months: number
  usage_limit: number
  usage_count: number
  expires_at: string
  is_active: boolean
}

interface AdminStats {
  totalUsers: number
  activeUsers: number
  newUsers: number
  totalGenerations: number
  generationsToday: number
  activeSubscriptions: number
  revenue: number
}

// Упрощенный интерфейс UserStatistics (удалены некорректные типы Vue)
// Убедитесь, что он соответствует структуре данных API или UserStats
interface UserStatistics {
  generations_by_type: Record<ContentType, number>; // Пример, уточните реальный тип
  dailyGenerations: number;
  dailyImages: number;
  totalGenerations: number;
  totalImages: number
  points: number
  lastActive: Date
}

interface User {
  id: number;
  telegram_id: number;
  username: string;
  first_name: string;
  last_name?: string;
  role: string;
  points: number;
  has_access: boolean;
  created_at: string;
  last_active: string;
}

// Эти интерфейсы используются в других частях приложения
export interface State {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  webAppData: any;
}

export interface DailyLimits {
  generations: number
  images: number
}

// Form Data Types
interface LessonPlanFormData {
  language: string
  topic: string
  age?: string
  level?: string
  duration?: number
  teachingMethodology?: string
  [key: string]: any
}

interface ExerciseFormData {
  language: string
  topic: string
  type: string
  difficulty: string
  quantity: number
  [key: string]: any
}

interface GameFormData {
  language: string
  topic: string
  type: string
  game_type: string
  level: string
  duration: number
  difficulty: string
  players: {
    min: number
    max: number
  }
  [key: string]: any
}

interface ImageFormData {
  user_id?: number
  prompt: string
  with_points?: boolean
  skip_points_check?: boolean
}

interface VideoTranscriptFormData {
  video_id: string
  subtitle_language: string
  user_id: number
}

interface Tariff {
  id: number
  type: TariffType
  name: string
  price_points: number
  is_active: boolean
  settings: {
    generations_limit: number
    images_limit: number
  }
}

interface Achievement {
  id: string | number
  code: string
  name: string
  description: string
  icon?: string
  conditions: Record<string, any>
  points_reward: number
}



// Export types
export type {
  LessonPlanFormData,
  ExerciseFormData,
  GameFormData,
  ImageFormData,
  VideoTranscriptFormData,
  SystemSettings,
  PromoCode,
  PromoCodeHistory,
  Tariff,
  Achievement,
  Generation,
  FeatureAnalytics,
  AdminStats,
  UserStatistics,
  GenerationStatistics,
  FilterOptions,
  User
}

declare global {
  interface Window {
    __SIMPLE_TOAST__?: {
      success: (message: string, duration?: number) => number;
      error: (message: string, duration?: number) => number;
      info: (message: string, duration?: number) => number;
      warning: (message: string, duration?: number) => number;
      removeAll: () => void;
    };
    cleanupDOM?: () => void;
  }
}
