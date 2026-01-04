// src/types/index.ts

import { ContentType, UserRole, TariffType } from '../core/constants'

export interface User {
  id: number;
  telegram_id: number;
  username?: string;
  first_name: string;
  last_name?: string;
  role: UserRole;
  invite_code: string;
  invites_count: number;
  has_access: boolean;
  unsubscribed_at?: Date | null;
  created_at: Date;
  last_active: Date;
  tariff: TariffType | null;
  tariff_valid_until?: Date | null;
  points: number;
}

export interface TariffInfo {
  type: TariffType;
  validUntil: Date | null;
  limits: DailyLimits;
  pricePoints: number;
  features: string[];
  name: string;
}

export interface Tariff {
  id: number
  type: TariffType
  name: string
  price_points: number
  generations_limit: number
  images_limit: number
  features: TariffFeature[]
  is_active: boolean
  created_at: Date
  updated_at?: Date | null
}

export interface TariffFeature {
  name: string
  description: string
  enabled: boolean
}

export interface UserTariffHistory {
  id: number;
  user_id: number;
  tariff_type: string;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
}

export interface Generation {
  id: number
  user_id: number
  type: ContentType
  content: string
  prompt: string
  created_at: Date
  updated_at?: Date | null
  status: 'success' | 'error'
  error_type?: string
  tokens_used?: number
}

export interface Image {
  id: number
  user_id: number
  prompt: string
  url: string
  created_at: Date
}

export interface Achievement {
  id: number
  code: string
  name: string
  description: string
  icon?: string
  conditions: AchievementConditions
  points_reward: number
}

export interface AchievementConditions {
  type: string
  required_count?: number
  content_type?: ContentType
  consecutive_days?: number
  invites_count?: number
}

export interface UserAchievement {
  id: number
  user_id: number
  achievement_id: number
  progress: number
  unlocked: boolean
  unlocked_at?: Date | null
  rewarded?: boolean
  rewarded_at?: Date | null
}

export interface AdminStats {
  totalUsers: number
  activeUsers: number
  newUsers: number
  totalGenerations: number
  generationsToday: number
  activeSubscriptions: number
  revenue: number
}


export interface UserStatistics {
  dailyGenerations: number
  dailyImages: number
  totalGenerations: number
  totalImages: number
  points: number
  lastActive: Date
}

export interface GenerationStatistics {
  totalCount: number
  byType: Record<ContentType, number>
  successRate: number
  averageTokens: number
  popularPrompts: Array<{prompt: string, count: number}>
}

export interface DailyLimits {
  generations: number;
  images: number;
}

export interface Activity {
  id: number
  type: string
  description: string
  timestamp: Date
  user_id?: number
  metadata?: Record<string, any>
}

export interface PopularQuery {
  id: number
  text: string
  count: number
  percentage: number
}

export interface ErrorStatistic {
  type: string
  count: number
  percentage: number
}

export interface Notification {
  id: number
  type: string
  message: string
  read: boolean
  created_at: Date
}

export interface ChartData {
  date: string | Date
  value: number
  [key: string]: any
}

// Вспомогательные типы для функций API
export interface APIResponse<T = any> {
  status: 'success' | 'error'
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  perPage: number
  totalPages: number
}

export interface FilterOptions {
  search?: string
  dateFrom?: Date | string
  dateTo?: Date | string
  type?: string
  status?: string
  [key: string]: any
}

// Типы для аналитики использования функций
export interface FeatureUsage {
  feature: string
  count: number
  uniqueUsers: number
  successRate: number
  averageTime: number
}

export interface FeatureAnalytics {
  totalUsage: number
  uniqueUsers: number
  featureDistribution: Record<string, any>
  userDistribution: {
    byRole: Record<string, number>
    byTariff: Record<string, number>
  }
  successRates: Record<string, number>
  mostPopular: Array<{feature: string, count: number, percentage: number}>
  leastUsed: Array<{feature: string, count: number, percentage: number}>
  period: string
  generatedAt: string
}

interface GenerationWithUser extends Generation {
  username?: string;         // опциональное поле для username из Telegram
  user_full_name?: string;   // опционально можем добавить полное имя
}

export interface Promocode {
  code: string
  tariff_type: string
  duration_months: number
  usage_limit: number
  usage_count: number
  expires_at: string
  is_active: boolean
}

export interface PromoUsage {
  id: number
  code: string
  user: {
    id: number
    name: string
  }
  tariff_type: string
  duration_months: number
  used_at: string
}

export interface GenerationRequest {
  user_id: number | undefined;
  type: ContentType;
  prompt: string;
}

export interface LessonPlanFormData {
  language: string;
  level: string;
  topic: string;
  duration: number;
  methodologies: {
    mainMethod: string;
    supportMethods: string[];
  };
  objectives: string[];
  materials: string[];
  assessment: 'formative' | 'summative' | 'none';
  format: 'online' | 'offline' | 'hybrid';
  culturalElements: boolean;
}

export interface LessonPlanFormData {
  language: string;
  level: string;
  topic: string;
  duration: number;
  methodologies: {
    mainMethod: string;
    supportMethods: string[];
  };
  objectives: string[];
  materials: string[];
  assessment: 'formative' | 'summative' | 'none';
  format: 'online' | 'offline' | 'hybrid';
  culturalElements: boolean;
}

// Интерфейс для методики преподавания
export interface TeachingMethod {
  id: string;
  name: string;
  description: string;
  features: string[];
  applicableLanguages?: string[];
}

// Типы для способов оценивания
export type AssessmentType = 'formative' | 'summative' | 'none';
export type AssessmentMode = 'written' | 'oral' | 'practical' | 'combined';

// Уровни владения языком
export type LanguageLevel = 'beginner' | 'intermediate' | 'advanced';

// Интерфейс для валидации формы
export interface FormValidation {
  errors: string[];
  warnings: string[];
}

// Интерфейс для настроек генерации
export interface GenerationSettings {
  temperature: number;
  maxTokens: number;
  includeCulturalElements: boolean;
  includeAssessment: boolean;
}

// Типы форматов урока
export type LessonFormat = 'online' | 'offline' | 'hybrid';
export type GroupSize = 'individual' | 'small' | 'medium' | 'large' | 'classroom';

// Интерфейс для результата генерации
export interface GenerationResult {
  plan: string;
  metadata: {
    generatedAt: Date;
    model: string;
    prompt: string;
    settings: GenerationSettings;
  };
}

// Интерфейс для статистики использования
export interface UsageStatistics {
  generatedLessons: number;
  uniqueMethods: number;
  remainingGenerations: number;
  lastGenerated?: Date;
}

// Типы для методических компонентов
export interface MethodComponent {
  type: 'activity' | 'assessment' | 'material' | 'interaction';
  name: string;
  description: string;
  duration: number;
  requiredMaterials?: string[];
}

// Интерфейс для шаблона урока
export interface LessonTemplate {
  id: string;
  name: string;
  description: string;
  structure: MethodComponent[];
  defaultDuration: number;
  targetLevel: LanguageLevel;
  applicableFormats: LessonFormat[];
}

// Типы результатов проверки совместимости
export interface MethodologyCompatibility {
  compatible: string[];
  conflicting: string[];
  recommended: string[];
}

// Интерфейс для сохранённого плана
export interface SavedLessonPlan {
  id: string;
  userId: number;
  formData: LessonPlanFormData;
  generatedPlan: string;
  createdAt: Date;
  lastModified: Date;
  tags: string[];
  isTemplate: boolean;
}

// Типы событий генерации
export type GenerationEvent = {
  type: 'started' | 'completed' | 'failed';
  timestamp: Date;
  data: {
    planId?: string;
    error?: string;
    duration?: number;
  };
}

// Вспомогательные типы для валидации
export type ValidationRule = {
  field: keyof LessonPlanFormData;
  check: (value: any) => boolean;
  message: string;
  severity: 'error' | 'warning';
}

// Типы для истории изменений
export interface PlanRevision {
  id: string;
  planId: string;
  changes: Partial<LessonPlanFormData>;
  timestamp: Date;
  userId: number;
}

// Интерфейс для метаданных генерации
export interface GenerationMetadata {
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  duration: number;
  settings: GenerationSettings;
}

// Экспорт констант
export const DEFAULT_GENERATION_SETTINGS: GenerationSettings = {
  temperature: 0.7,
  maxTokens: 2048,
  includeCulturalElements: true,
  includeAssessment: true
};

export const MAX_OBJECTIVES = 5;
export const MAX_MATERIALS = 10;
export const MIN_DURATION = 15;
export const MAX_DURATION = 180;
export const MAX_SUPPORT_METHODS = 3;


export interface Exercise {
  id: string
  type: string
  content: string
  answers?: string
  instructions?: string
}

export interface Theme {
  value: string
  label: string
  icon: string
}

export interface ExerciseType {
  id: string
  label: string
  icon: string
  description: string
}

export interface InteractiveFeature {
  id: string
  label: string
  icon: string
  description: string
}

export interface MultimediaType {
  id: string
  label: string
  icon: string
  subtypes: Array<{
    id: string
    label: string
  }>
}

export interface ExerciseFormData {
  language: string;
  topic: string;
  type: string;
  exercise_type: string;
  difficulty: string;
  quantity: number;
  individual_group?: string;
  online_offline?: string;
  meta?: {
    proficiency?: string;
    selectedTypes?: string[];
    interactiveFeatures?: string[];
    gamification?: string[];
    multimedia?: Record<string, any>;
    includeAnswers?: boolean;
    includeInstructions?: boolean;
    adaptiveDifficulty?: boolean;
  };
}

// Telegram-specific types
export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

export interface TelegramWebAppTheme {
  bg_color: string;
  text_color: string;
  hint_color: string;
  link_color: string;
  button_color: string;
  button_text_color: string;
}

export interface TelegramAppData {
  user: TelegramUser;
  startParam?: string;
  platform: string;
  version: string;
  themeParams: TelegramWebAppTheme;
}

// Добавляем недостающие типы
export interface GameFormData {
  language: string;
  topic: string;
  type: string;
  game_type: string;
  level: string;
  duration: number;
  difficulty: string;
  players: {
    min: number;
    max: number;
  };
  [key: string]: any;
}

export interface ImageFormData {
  user_id?: number;
  prompt: string;
  with_points?: boolean;
}

export interface VideoTranscriptFormData {
  video_id: string;
  subtitle_language: string;
  user_id: number;
}

export interface PromoCodeHistory {
  page: number;
  per_page: number;
  promocode?: string;
  tariff?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface Promocode {
  code: string;
  tariff_type: string;
  duration_months: number;
  usage_limit: number;
  usage_count: number;
  expires_at: string;
  is_active: boolean;
}

export interface UserStats {
  dailyGenerations: number;
  dailyImages: number;
  totalGenerations: number;
  totalImages: number;
  points: number;
  lastActive: Date;
  generations_by_type?: Record<string, number>; // Добавляем опциональное свойство для статистики по типам
}

export interface AchievementProgress {
  id: string;
  user_id: number;
  achievement_id: string;
  progress: number;
  completed: boolean;
  completed_at: string | null;
}

export interface DataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface SystemSettings {
  tariffs: Array<{
    type: string;
    name: string;
    settings: {
      generations_limit: number;
      images_limit: number;
      price_points: number;
    }
  }>;
  referral: {
    new_user_discount: number;
    referrer_discount: number;
    max_discount: number;
  };
}
