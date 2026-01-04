// src/core/constants.ts

export enum ContentType {
  LESSON_PLAN = "lesson_plan",
  EXERCISE = "exercise",
  GAME = "game",
  IMAGE = "image",
  TRANSCRIPT = "transcript",
  FREE_QUERY = "free_query",
  CONCEPT_EXPLANATION = "concept_explanation",
  COURSE = "course",
  TEXT_ANALYSIS = "text_analysis"
}

export enum UserRole {
  USER = "user",
  ADMIN = "admin",
  FRIEND = "friend",
  MOD = "mod"
}

export enum TariffType {
  BASIC = "tariff_2",     // 400 баллов - 6 генераций, 2 картинки
  STANDARD = "tariff_4",   // 650 баллов - 12 генераций, 5 картинок
  PREMIUM = "tariff_6"    // 900 баллов - 25 генераций, 8 картинок
}

export enum ActionType {
  GENERATION = "generation",
  IMAGE = "image",
  POINTS_EARNED = "points_earned",
  POINTS_SPENT = "points_spent",
  TARIFF_PURCHASE = "tariff_purchase",
  INVITE_USED = "invite_used",
  REFERRAL_REWARD = "referral_reward"
}

export const TARIFF_LIMITS = {
  [TariffType.BASIC]: {
    generations: 6,
    images: 2,
    points_cost: 400
  },
  [TariffType.STANDARD]: {
    generations: 12,
    images: 5,
    points_cost: 650
  },
  [TariffType.PREMIUM]: {
    generations: 25,
    images: 8,
    points_cost: 900
  }
} as const

export const UNLIMITED_ROLES = [UserRole.ADMIN, UserRole.FRIEND, UserRole.MOD];

export const DAILY_RESET_HOUR = 0 // Сброс счетчиков в полночь

export const POINTS_REWARDS = {
  DAILY_LOGIN: 5,
  GENERATION_USED: 1,
  INVITE_FRIEND: 100
}

export interface UserStats {
  dailyGenerations: number;
  dailyImages: number;
  totalGenerations: number;
  totalImages: number;
  points: number;
  lastActive: Date;
}

export interface DailyLimits {
  generations: number;
  images: number;
}

export interface TariffInfo {
  type: TariffType;
  validUntil: Date | null;
  limits: DailyLimits;
}

export interface AchievementProgress {
  id: number;
  progress: number;
  unlocked: boolean;
  unlockedAt: Date | null;
}
