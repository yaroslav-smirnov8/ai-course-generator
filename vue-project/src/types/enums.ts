// src/types/enums.ts
export enum UserRole {
  USER = "user",
  ADMIN = "admin",
  FRIEND = "friend",
  MOD = "mod"
}

export enum ContentType {
  LESSON_PLAN = "lesson_plan",
  EXERCISE = "exercise",
  GAME = "game",
  IMAGE = "image",
  TRANSCRIPT = "transcript"
}

export enum TariffType {
  BASIC = "tariff_2",
  STANDARD = "tariff_4",
  PREMIUM = "tariff_6"
}

export enum ActionType {
  GENERATION = "generation",
  IMAGE = "image",
  POINTS_EARNED = "points_earned",
  POINTS_SPENT = "points_spent"
}
