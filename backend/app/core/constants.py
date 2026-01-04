# app/core/constants.py
from enum import Enum
from pydantic import BaseModel, Field


class UserSettings:
    DEFAULT_THEME = "default"
    DEFAULT_LANGUAGE = "en"
    AVAILABLE_THEMES = ["default", "dark", "light"]
    AVAILABLE_LANGUAGES = ["en", "ru"]

class CacheTTL:
    PROFILE = 300  # 5 minutes
    SETTINGS = 600  # 10 minutes

class ContentType(str, Enum):
    LESSON_PLAN = "lesson_plan"
    EXERCISE = "exercise"
    GAME = "game"
    IMAGE = "image"
    TRANSCRIPT = "transcript"  # Добавили тип для транскриптов
    TEXT_ANALYSIS = "text_analysis"  # Добавили тип для анализа текста
    CONCEPT_EXPLANATION = "concept_explanation"  # Добавили тип для объяснения концепций
    FREE_QUERY = "free_query"  # Добавили тип для свободных запросов AI-ассистента
    COURSE = "course"  # Добавили тип для генерации курсов
    STRUCTURED_DATA = "structured_data"  # Тип для структурированных данных JSON
    # Добавляем новые типы:
    LESSON_MATERIAL = "lesson_material" # Для отслеживания генерации материалов урока
    COURSE_EXPORT = "course_export"     # Для отслеживания экспорта курса
    # Новые типы для контента в курсе:
    COURSE_LESSON_PLAN = "course_lesson_plan"   # Планы уроков в рамках курса
    COURSE_EXERCISE = "course_exercise"         # Упражнения в рамках курса  
    COURSE_GAME = "course_game"                 # Игры в рамках курса

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    FRIEND = "friend"  # Добавили роль для друзей с безлимитом
    MOD = "mod"  # Добавили роль для модераторов с безлимитом

class TariffType(str, Enum):
    FREE = "free"          # Бесплатный тариф - 3 генерации, 1 картинка
    BASIC = "tariff_2"     # 400 баллов - 10 генераций, 5 картинок
    STANDARD = "tariff_4"   # 600 баллов - 20 генераций, 10 картинок
    PREMIUM = "tariff_6"    # 800 баллов - 30 генераций, 15 картинок

class ActionType(str, Enum):
    GENERATION = "generation"
    IMAGE = "image"
    POINTS_EARNED = "points_earned"
    POINTS_SPENT = "points_spent"
    TARIFF_PURCHASE = "tariff_purchase"
    INVITE_USED = "invite_used"
    REFERRAL_REWARD = "referral_reward"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"  # Добавили тип для достижений
    LESSON_PLAN_GENERATION = "lesson_plan_generation"  # Тип для генерации плана урока
    EXERCISE_GENERATION = "exercise_generation"  # Тип для генерации упражнений
    GAME_GENERATION = "game_generation"  # Тип для генерации игр
    IMAGE_GENERATION = "image_generation"  # Тип для генерации изображений
    VIDEO_TRANSCRIPT = "video_transcript"  # Тип для обработки транскрипта видео
    LESSON_PLAN_FROM_TRANSCRIPT = "lesson_plan_from_transcript"  # Тип для генерации плана урока из транскрипта
    EXERCISES_FROM_TRANSCRIPT = "exercises_from_transcript"  # Тип для генерации упражнений из транскрипта
    GAMES_FROM_TRANSCRIPT = "games_from_transcript"  # Тип для генерации игр из транскрипта
    TEXT_ANALYSIS_GENERATION = "text_analysis_generation"  # Тип для анализа текста
    PURCHASE = "purchase"  # Тип для покупки баллов
    REFUND = "refund"  # Тип для возврата денег
    INVITE_REWARD = "invite_reward"  # Тип для награды за приглашение

class StatisticsPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class StatisticsMetric(str, Enum):
    USERS = "users"
    GENERATIONS = "generations"
    TARIFFS = "tariffs"
    SERVER = "server"

# Модель для лимитов генераций
class GenerationLimit(BaseModel):
    daily_generations: int = Field(ge=0)  # Changed from float to int
    daily_images: int = Field(ge=0)  # Changed from float to int
    points_cost: int = Field(ge=0)


class CourseLevel(str, Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"

class CourseFormat(str, Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"

class TargetAudience(str, Enum):
    KIDS = "kids"
    TEENS = "teens"
    ADULTS = "adults"
    BUSINESS = "business"
    ACADEMIC = "academic"


# Константы для лимитов тарифов
TARIFF_LIMITS = {
    TariffType.FREE: GenerationLimit(
        daily_generations=3,
        daily_images=1,
        points_cost=0
    ),
    TariffType.BASIC: GenerationLimit(
        daily_generations=6,
        daily_images=2,
        points_cost=400
    ),
    TariffType.STANDARD: GenerationLimit(
        daily_generations=12,
        daily_images=5,
        points_cost=650
    ),
    TariffType.PREMIUM: GenerationLimit(
        daily_generations=25,
        daily_images=8,
        points_cost=900
    )
}

# Константы для системы достижений
ACHIEVEMENT_TYPES = {
    "FIRST_GENERATION": "first_generation",
    "GENERATION_MASTER": "generation_master",
    "INVITATION_MASTER": "invitation_master",
    "DAILY_STREAK": "daily_streak"
}

# Константы для системы приглашений
INVITE_REWARDS = {
    "new_user": 1,  # % скидки для нового пользователя
    "inviter": 2    # % скидки для пригласившего
}

# Общие константы
MAX_DISCOUNT = 20  # Максимальная скидка в процентах
MIN_POINTS_REWARD = 10  # Минимальная награда за достижение
MAX_POINTS_REWARD = 100  # Максимальная награда за достижение

# Константы для очистки данных
TRANSCRIPT_CACHE_HOURS = 24  # Время жизни кэша транскриптов
CLEANUP_HOUR = 3  # Час запуска очистки (03:00)

# Лимиты генераций для пользователей с безлимитом
MAX_LIMIT = 9999999  # Or any other reasonable high number

UNLIMITED_LIMITS = GenerationLimit(
    daily_generations=MAX_LIMIT,
    daily_images=MAX_LIMIT,
    points_cost=0
)

# Константы для проверки достижений
ACHIEVEMENT_THRESHOLDS = {
    "generations": {
        "bronze": 10,
        "silver": 50,
        "gold": 100
    },
    "invites": {
        "bronze": 5,
        "silver": 15,
        "gold": 30
    },
    "streak": {
        "bronze": 7,
        "silver": 30,
        "gold": 90
    }
}

# Временные константы
ACHIEVEMENT_CHECK_INTERVAL = 60  # Интервал проверки достижений в секундах
SESSION_TIMEOUT = 3600  # Время жизни сессии в секундах
RATE_LIMIT_RESET = 86400  # Время сброса лимитов (24 часа в секундах)

# Роли с безлимитным доступом
UNLIMITED_ROLES = [UserRole.ADMIN, UserRole.FRIEND, UserRole.MOD]
