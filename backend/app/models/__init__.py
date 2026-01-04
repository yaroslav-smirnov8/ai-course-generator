from .user import User
from .achievements import Achievement, UserAchievement, UserAction
from .tracking import (
    UsageLog,
    DailyUsage,
    UsageStatistics,  # Переименовываем для избежания конфликта
    GenerationMetrics,
    UserActivityLog
)
from .subscription import TariffPlan, UserTariff, PriceChange
from .statistics import (
    UserStatistics,
    ServerStatistics,
)
from .feature_usage import FeatureUsage, FeatureUsageMetrics
from .analytics_data import AnalyticsData, DetailedGenerationMetrics, PurchaseAnalytics # Добавлено PurchaseAnalytics
from .content import Generation, Image, VideoTranscript
from .point_transaction import PointTransaction
from .course import Course, Lesson, Activity, LessonTemplate
from .link_click import LinkClick
from .pricing import (
    PricingRule,
    SpecialOffer,
    Discount,
    DiscountType,
    AppliedDiscount,
    RuleType
)
from .point_purchase import PointPurchase
from .point_transaction import PointTransaction
from .promocode import PromoCode, PromoCodeUsage, PromoCodeType, PromoCodeUsageType
from .broadcast import ScheduledMessage
from .payment import Payment

__all__ = [
    # Пользователи
    'User',

    # Достижения
    'Achievement',
    'UserAchievement',
    'UserAction',

    # Контент
    'Generation',
    'Image',
    'VideoTranscript',

    # Трекинг и статистика
    'UsageLog',
    'DailyUsage',
    'UsageStatistics',  # Используем переименованный импорт
    'GenerationMetrics',
    'UserActivityLog',

    # Тарифы и подписки
    'TariffPlan',
    'UserTariff',
    'PriceChange',

    # Статистика
    'UserStatistics',
    'ServerStatistics',

    # Функциональное использование
    'FeatureUsage',
    'FeatureUsageMetrics',

    # Данные для аналитики
    'AnalyticsData',
    'DetailedGenerationMetrics',
    'PurchaseAnalytics', # Добавлено PurchaseAnalytics
    'PointTransaction',

    # Курсы
    'Course',
    'Lesson',
    'Activity',
    'LessonTemplate',

    # Прайсинг и акции
    'PricingRule',
    'SpecialOffer',
    'Discount',
    'DiscountType',
    'AppliedDiscount',
    'RuleType',

    # Покупка баллов
    'PointPurchase',
    'PointTransaction',

    # Переходы по ссылкам
    'LinkClick',

    # Промокоды
    'PromoCode',
    'PromoCodeUsage',
    'PromoCodeType',
    'PromoCodeUsageType',

    # Рассылка
    'ScheduledMessage',

    # Платежи
    'Payment'
]
