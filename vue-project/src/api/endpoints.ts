// src/api/endpoints.ts
export const API_ENDPOINTS = {
  // Content Generation
  GENERATE_LESSON_PLAN: '/api/v1/content/generate_lesson_plan',
  GENERATE_LESSON_PLAN_FORM: '/api/v1/content/generate_lesson_plan_form',
  DETAIL_LESSON_PLAN: '/api/v1/content/detail_lesson_plan',
  GENERATE_EXERCISES: '/api/v1/content/generate_exercises',
  GENERATE_GAME: '/api/v1/content/generate_game',
  GENERATE_IMAGE: '/api/v1/content/generate_image',
  PROCESS_TRANSCRIPT: '/api/v1/content/process_video_transcript',
  GENERATE_FREE_QUERY: '/api/v1/content/generate_free_query',
  GENERATE_CONCEPT_EXPLANATION: '/api/v1/content/generate_concept_explanation',

  // Text Analyzer Endpoints
  DETECT_TEXT_LEVEL: '/api/v1/content/detect_text_level',
  REGENERATE_TEXT: '/api/v1/content/regenerate_text',
  CHANGE_TEXT_LEVEL: '/api/v1/content/change_text_level',
  GENERATE_QUESTIONS: '/api/v1/content/generate_questions',
  GENERATE_SUMMARY: '/api/v1/content/generate_summary',
  GENERATE_SUMMARIES: '/api/v1/content/generate_summaries',
  GENERATE_TITLES: '/api/v1/content/generate_titles',
  GENERATE_COMPREHENSION_TEST: '/api/v1/content/generate_comprehension_test',

  // User Management
  USERS: '/api/v1/users',
  USER_DETAIL: (id: number) => `/api/v1/users/${id}`,
  USERS_ME: '/api/v1/users/me',

  // Authentication
  AUTH: {
    TELEGRAM: '/api/v1/auth/telegram',
    ME: '/api/v1/auth/me',
  },

  // Achievements
  ACHIEVEMENTS: '/api/v1/achievements',
  ACHIEVEMENT_DETAIL: (id: string) => `/api/v1/achievements/${id}`,
  CHECK_ACHIEVEMENTS: '/api/v1/achievements/check',

  // Tariffs
  TARIFFS: '/api/v1/tariffs',
  TARIFF_DETAIL: (id: number) => `/api/v1/tariffs/${id}`,

  // Analytics
  ANALYTICS_GENERATIONS: '/api/v1/statistics/generations',
  ANALYTICS_USERS: '/api/v1/statistics/users',
  ANALYTICS_FEATURES: '/api/v1/admin/analytics/features',
  ANALYTICS_POINTS: '/api/v1/analytics/points',
  ANALYTICS_TARIFFS: '/api/v1/analytics/tariffs',
  ANALYTICS_ACHIEVEMENTS: '/api/v1/admin/analytics/achievements',
  ANALYTICS_LINKS: '/api/v1/analytics/links',
  LOG_LINK_CLICK: '/api/v1/analytics/link_click',

  // Promocodes
  PROMOCODES: '/api/v1/admin/promocodes',
  PROMOCODE_DETAIL: (code: string) => `/api/v1/admin/promocodes/code/${code}`,
  PROMOCODE_STATS: '/api/v1/admin/promocodes/stats',
  PROMOCODE_HISTORY: '/api/v1/admin/promocodes/history',

  // System Settings
  SYSTEM_SETTINGS: '/api/v1/admin/settings',

  // Usage Tracking
  TRACK_USAGE: '/api/v1/tracking/usage',

  // Course Management
  COURSES: '/api/v1/courses',
  COURSE_DETAIL: (id: number) => `/api/v1/courses/${id}`,

  // Statistics
  USER_STATISTICS: '/api/v1/statistics/user',
  GENERATION_STATISTICS: '/api/v1/statistics/generations',

  USERS_TARIFF: (id: number) => `/api/v1/users/${id}/tariff`,
  USERS_USAGE_STATS: (id: number) => `/api/v1/users/${id}/usage-stats`,
  USERS_RESET_COUNTERS: (id: number) => `/api/v1/users/${id}/reset-usage-counters`,
  USER_TARIFF_CHECK: (id: number) => `/api/v1/users/${id}/tariff/check`,
};
