# app/services/__init__.py

# Основные сервисы
from .content.generator import ContentGenerator
from .user.manager import UserManager
from .course.manager import CourseManager

# Трекинг и аналитика
from .tracking.usage import UsageTracker
from .tracking.tracking_service import TrackingService
from .analytics import AnalyticsService
from .analytics import FeatureUsageService

# Статистика
from .statistics.collector import StatisticsCollector

# Управление тарифами и оплатой
from .tariff.manager import TariffManager
from .pricing.manager import PricingManager

# Оптимизация и очереди
from .optimization.query_optimizer import QueryOptimizer
from .optimization.batch_processor import BatchProcessor
from .queue.generation_queue import GenerationQueue

# Реферальная система и достижения
from .referral.manager import ReferralManager
from .achievements.manager import AchievementManager
from .achievements.checker import AchievementChecker
from .achievements import RewardManager

# Очистка и обслуживание
from .cleanup.transcript_cleanup import CleanupService
from .cleanup.course_cleanup import CourseCleanupService

# Аутентификация и сессии
from .session import SessionService

__all__ = [
    # Основные сервисы
    'ContentGenerator',
    'UserManager',
    'CourseManager',

    # Трекинг и аналитика
    'UsageTracker',
    'TrackingService',
    'AnalyticsService',
    'FeatureUsageService',
    'StatisticsCollector',

    # Управление тарифами и оплатой
    'TariffManager',
    'PricingManager',

    # Оптимизация и очереди
    'QueryOptimizer',
    'BatchProcessor',
    'GenerationQueue',

    # Реферальная система и достижения
    'ReferralManager',
    'AchievementManager',
    'AchievementChecker',
    'RewardManager',

    # Очистка и обслуживание
    'CleanupService',
    'CourseCleanupService',

    # Аутентификация и сессии
    'SessionService'
]