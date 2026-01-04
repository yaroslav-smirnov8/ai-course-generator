# app/core/__init__.py
from .config import settings
from .database import get_db, Base
from .security import (
    SecurityManager,
    telegram_auth_middleware,
    get_current_user,
    get_current_admin_user,
    admin_required,
)
from .enums import UserRole
from .constants import (
    ActionType,
    StatisticsPeriod,
    StatisticsMetric,
    GenerationLimit,
    TARIFF_LIMITS,
    INVITE_REWARDS,
    ACHIEVEMENT_TYPES,
    ACHIEVEMENT_THRESHOLDS,
    MAX_DISCOUNT,
    UNLIMITED_LIMITS
)
from .types import ContentType, TariffType
from .decorators import (
    check_generation_limits,
    track_usage,
    check_achievements
)
from .optimization import RequestOptimizer
from .memory import MemoryOptimizer
from .exceptions import (
    NotFoundException,
    ValidationError,
    InsufficientBalanceError,
    DailyLimitExceededError,
    InvalidTransactionError,
    TransactionTimeoutError,
    TransactionConflictError,
    InvalidAmountError,
    RefundError,
    TariffLimitError,
    PointsPurchaseError
)
from .cache import CacheService, get_cache_service
from app.schemas.points import TransactionType

__all__ = [
    # Конфигурация
    'settings',

    # База данных
    'get_db',
    'Base',

    # Безопасность и аутентификация
    'SecurityManager',
    'telegram_auth_middleware',
    'get_current_user',
    'get_current_admin_user',
    'admin_required',

    # Константы и перечисления
    'ContentType',
    'UserRole',
    'TariffType',
    'ActionType',
    'StatisticsPeriod',
    'StatisticsMetric',
    'GenerationLimit',
    'TransactionType',

    # Конфигурационные словари
    'TARIFF_LIMITS',
    'INVITE_REWARDS',
    'ACHIEVEMENT_TYPES',
    'ACHIEVEMENT_THRESHOLDS',
    'MAX_DISCOUNT',
    'UNLIMITED_LIMITS',

    # Декораторы
    'check_generation_limits',
    'track_usage',
    'check_achievements',

    # Оптимизация запросов и памяти
    'RequestOptimizer',
    'MemoryOptimizer',

    # Обработка исключений
    'NotFoundException',
    'ValidationError',
    'InsufficientBalanceError',
    'DailyLimitExceededError',
    'InvalidTransactionError',
    'TransactionTimeoutError',
    'TransactionConflictError',
    'InvalidAmountError',
    'RefundError',
    'TariffLimitError',
    'PointsPurchaseError',

    # Кэширование
    'CacheService',
    'get_cache_service',
]