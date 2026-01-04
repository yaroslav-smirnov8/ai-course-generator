from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, ClassVar, Dict, Any, Union
from functools import lru_cache


class Settings(BaseSettings):
    # Debug и разработка
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    TESTING: bool = Field(default=False, description="Testing mode")

    # API настройки
    API_V1_STR: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="Learning Platform API")
    VERSION: str = Field(default="1.0.0")

    # Настройки безопасности WebApp
    MIN_WEBAPP_VERSION: str = Field(default="6.0")
    WEBAPP_AUTH_TIMEOUT: int = Field(default=3600)  # Таймаут авторизации (1 час)
    WEBAPP_HASH_ALGO: str = Field(default="SHA-256")
    WEBAPP_PUBLIC_KEY_PROD: str = Field(default="e7bf03a2fa4602af4580703d88dda5bb59f32ed8b02a56c187fe7d34caed242d")
    WEBAPP_PUBLIC_KEY_TEST: str = Field(default="40055058a4ee38156a06562e52eece92a771bcd8346a8c4615cb7376eddf72ec")
    WEBAPP_URL: str = Field(...)

    # Настройки бота и канала
    BOT_TOKEN: str = Field(...)  # Обязательное поле
    CHANNEL_ID: str = Field(...)
    EVO_CHANNEL_ID: Optional[str] = Field(default=None)  # Дополнительный канал приложения
    ADMIN_ID: int = Field(...)
    MOD_ID: int = Field(...)

    # Обязательные каналы для подписки (используем основной канал)
    @property
    def REQUIRED_CHANNEL_ID(self) -> Optional[str]:
        """Используем основной канал как обязательный для подписки"""
        return self.CHANNEL_ID

    @property
    def REQUIRED_CHANNEL_URL(self) -> Optional[str]:
        """Генерируем URL канала на основе CHANNEL_ID"""
        if self.CHANNEL_ID:
            # Если канал начинается с @, создаем t.me ссылку
            if self.CHANNEL_ID.startswith('@'):
                return f"https://t.me/{self.CHANNEL_ID[1:]}"  # Убираем @ из начала
            # Если это числовой ID, возвращаем None (приватный канал)
            return None
        return None

    @property
    def EVO_CHANNEL_URL(self) -> Optional[str]:
        """Генерируем URL канала приложения на основе EVO_CHANNEL_ID"""
        if self.EVO_CHANNEL_ID:
            # Если канал начинается с @, создаем t.me ссылку
            if self.EVO_CHANNEL_ID.startswith('@'):
                return f"https://t.me/{self.EVO_CHANNEL_ID[1:]}"  # Убираем @ из начала
            # Если это числовой ID, возвращаем None (приватный канал)
            return None
        return None

    # База данных
    DATABASE_URL: str = Field(...)
    DB_ECHO: bool = Field(default=False)  # SQL логи
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)

    # Redis настройки
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    # CORS настройки
    CORS_ORIGINS: list[str] = Field(default=[
        "http://localhost:5173",  # локальный фронтенд
        "https://aiteachers.ru.tuna.am"  # туннелированный фронтенд
    ])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: list[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"])

    # Настройки кэширования
    CACHE_TTL: int = Field(default=3600)  # 1 час
    STATS_CACHE_TTL: int = Field(default=300)  # 5 минут
    DAILY_CACHE_TTL: int = Field(default=86400)  # 24 часа

    # Настройки тарифов
    TARIFF_2_GENERATIONS: int = Field(default=6)
    TARIFF_4_GENERATIONS: int = Field(default=12)
    TARIFF_6_GENERATIONS: int = Field(default=18)
    TARIFF_2_IMAGES: int = Field(default=2)
    TARIFF_4_IMAGES: int = Field(default=5)
    TARIFF_6_IMAGES: int = Field(default=8)
    TARIFF_2_PRICE: int = Field(...)
    TARIFF_4_PRICE: int = Field(...)
    TARIFF_6_PRICE: int = Field(...)

    # Настройки для очистки данных
    TRANSCRIPT_CACHE_HOURS: int = Field(default=24)  # Время жизни транскрипта
    CLEANUP_HOUR: int = Field(default=3)  # Час для запуска очистки

    # Настройки приглашений
    REQUIRED_INVITES: int = Field(default=5)
    CONVERSATION_TIMEOUT: int = Field(default=300)

    # Настройки оптимизации
    BATCH_SIZE: int = Field(default=1000)
    MAX_MEMORY_USAGE: int = Field(default=1024)  # MB

    # Настройки логирования
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Настройки для оптимизации PostgreSQL
    POSTGRES_CONFIG: ClassVar[Dict[str, Union[str, int, float]]] = {
        # Настройки памяти
        "shared_buffers": "2GB",  # 25% от доступной RAM
        "work_mem": "16MB",       # Для сложных запросов
        "maintenance_work_mem": "128MB",  # Для обслуживания

        # Настройки дисковых операций
        "effective_io_concurrency": 200,  # Для SSD
        "random_page_cost": 1.1,          # Для SSD

        # Настройки планировщика
        "effective_cache_size": "6GB",  # ~50% от доступной RAM

        # Настройки журналирования
        "wal_buffers": "16MB",
        "checkpoint_timeout": "15min",
        "checkpoint_completion_target": 0.9,

        # Настройки автовакуума
        "autovacuum": "on",
        "autovacuum_max_workers": 3,
        "autovacuum_naptime": "1min",
        "autovacuum_vacuum_scale_factor": 0.1,
        "autovacuum_analyze_scale_factor": 0.05,

        # Настройки соединений
        "max_connections": 100
    }

    # Настройки для аналитики
    ANALYTICS_CONFIG: ClassVar[Dict[str, Any]] = {
        "enabled": True,  # Можно быстро отключить всю аналитику
        "batch_size": 200,  # Размер пакета для записи
        "cache_ttl": {
            "dashboard": 600,  # 10 минут
            "analytics": 1800,  # 30 минут
            "feature_usage": 3600,  # 1 час
        },
        "retention_days": {
            "detailed": 30,  # 30 дней для детальных данных
            "aggregated": 365  # 1 год для агрегированных данных
        },
        "scheduler": {
            "refresh_materialized_views": 3600,  # 1 час
            "cleanup_old_data": 86400,           # 1 день
            "save_analytics_snapshot": 43200,    # 12 часов
            "refresh_cache": 1800                # 30 минут
        }
    }

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='allow'
    )

    @property
    def is_development(self) -> bool:
        """Проверка режима разработки"""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Проверка production режима"""
        return self.ENVIRONMENT.lower() == "production"

    def get_database_url(self) -> str:
        """Получить URL базы данных с учетом окружения"""
        if self.TESTING:
            return f"{self.DATABASE_URL}_test"
        return self.DATABASE_URL

    # Валидация конфигурации
    def validate_config(self):
        # Проверяем BOT_TOKEN
        if not self.BOT_TOKEN or len(self.BOT_TOKEN) < 10:
            raise ValueError("Invalid BOT_TOKEN")

        # Проверяем версию WebApp
        try:
            major, minor = map(int, self.MIN_WEBAPP_VERSION.split('.'))
            if major < 6:
                raise ValueError("MIN_WEBAPP_VERSION must be at least 6.0")
        except:
            raise ValueError("Invalid MIN_WEBAPP_VERSION format")

        # Проверяем DATABASE_URL
        if not self.DATABASE_URL.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("DATABASE_URL must be PostgreSQL")

        # Проверяем CHANNEL_ID
        if not (self.CHANNEL_ID.startswith('-100') or self.CHANNEL_ID.startswith('@')):
            raise ValueError(
                "Invalid CHANNEL_ID format - must start with '-100' for private channels or '@' for public channels")


@lru_cache()
def get_settings() -> Settings:
    """
    Возвращает экземпляр настроек с кэшированием

    Returns:
        Settings: Объект настроек
    """
    settings = Settings()
    settings.validate_config()
    return settings


# Создаем экземпляр настроек
settings = get_settings()

# Для проверки конфигурации при запуске
if __name__ == "__main__":
    print(settings.model_dump())