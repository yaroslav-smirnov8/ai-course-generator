from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, registry
from sqlalchemy.pool import AsyncAdaptedQueuePool
from cachetools import LRUCache
from .config import settings
import logging
from ..core.constants import TariffType, TARIFF_LIMITS

logger = logging.getLogger(__name__)

# Создаем registry для маппинга
mapper_registry = registry()
Base = mapper_registry.generate_base()

# Создаем LRU кэш для SQL-запросов
compiled_cache = LRUCache(maxsize=500)


def get_async_db_url():
    url = settings.DATABASE_URL
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return url


# Создаем асинхронный движок
engine = create_async_engine(
    get_async_db_url(),
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    poolclass=AsyncAdaptedQueuePool,
    execution_options={"compiled_cache": compiled_cache}
)

# Создаем фабрику сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def create_database_if_not_exists():
    """Создает базу данных с правильной кодировкой UTF8, если она не существует"""
    try:
        import asyncpg
        from urllib.parse import urlparse

        # Парсим URL базы данных
        db_url = settings.DATABASE_URL
        parsed = urlparse(db_url)

        # Извлекаем параметры подключения
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432
        username = parsed.username or 'postgres'
        password = parsed.password
        database_name = parsed.path.lstrip('/')

        # Подключаемся к системной базе postgres для создания нашей БД
        system_conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database='postgres'
        )

        try:
            # Проверяем, существует ли база данных
            db_exists = await system_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", database_name
            )

            if not db_exists:
                # Создаем базу данных с кодировкой UTF8
                await system_conn.execute(f'''
                    CREATE DATABASE "{database_name}"
                    WITH
                    ENCODING = 'UTF8'
                    LC_COLLATE = 'en_US.UTF-8'
                    LC_CTYPE = 'en_US.UTF-8'
                    TEMPLATE = template0
                ''')
                logger.info(f"Database '{database_name}' created successfully with UTF8 encoding")
            else:
                logger.info(f"Database '{database_name}' already exists")

        finally:
            await system_conn.close()

    except Exception as e:
        logger.warning(f"Could not create database automatically: {e}")
        logger.info("Please create the database manually with UTF8 encoding")


async def init_db():
    """Инициализация базы данных"""
    try:
        # Создаем базу данных с правильной кодировкой, если она не существует
        await create_database_if_not_exists()

        # Явно импортируем все модели до создания таблиц
        from app.models import (
            User, Achievement, UserAchievement, UserAction,
            Generation, Image, VideoTranscript,
            UsageLog, DailyUsage, UsageStatistics, GenerationMetrics,
            UserActivityLog, TariffPlan, UserTariff, PriceChange,
            UserStatistics, ServerStatistics,
            FeatureUsage, FeatureUsageMetrics,
            AnalyticsData, DetailedGenerationMetrics,
            Course, Lesson, Activity, LessonTemplate,
            PricingRule, SpecialOffer, Discount, DiscountType,
            AppliedDiscount, RuleType, ScheduledMessage
        )

        async with engine.begin() as conn:
            # Конфигурируем маппинги
            mapper_registry.configure()

            # Сначала удаляем все таблицы с помощью DROP CASCADE
            # await conn.execute(text('DROP SCHEMA public CASCADE'))
            # await conn.execute(text('CREATE SCHEMA public'))

            # Затем создаем все таблицы заново
            await conn.run_sync(Base.metadata.create_all)

        # Применяем миграции
        await apply_migrations()

        # Create default tariffs
        await create_default_tariffs()

        # Create default achievements
        await create_default_achievements()

        # Добавляем проверку структуры после создания таблиц
        await validate_db_structure()

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def get_db():
    """Dependency для получения сессии базы данных"""
    session = None
    try:
        async with async_session() as session:
            # Проверяем подключение
            await session.execute(text("SELECT 1"))
            yield session
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        # Properly close the session if it exists and an error occurred
        if session:
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Error closing session after exception: {close_error}")
        raise


async def validate_db_structure():
    """Проверка структуры БД"""
    try:
        async with async_session() as session:
            # Проверяем подключение
            await session.execute(text("SELECT 1"))
            logger.info("Database connection successful")

            # Проверяем существование всех таблиц
            for table in Base.metadata.tables:
                result = await session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{table}'
                    );
                """))
                exists = result.scalar()
                logger.info(f"Table {table} exists: {exists}")

                if exists:
                    # Проверяем структуру таблицы
                    result = await session.execute(text(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = '{table}';
                    """))
                    columns = result.fetchall()
                    logger.info(f"Table structure for {table}:")
                    for col in columns:
                        logger.info(f"  - {col}")

    except Exception as e:
        logger.error(f"Database validation error: {str(e)}", exc_info=True)
        raise
    finally:
        await session.close()


async def create_default_tariffs():
    """Create default tariffs in the database based on constants"""
    try:
        # Import here to avoid circular import
        from ..models.subscription import TariffPlan
        from ..core.constants import TariffType, TARIFF_LIMITS

        async with async_session() as session:
            for tariff_type in TariffType:
                # Check if tariff exists
                query = select(TariffPlan).where(TariffPlan.type == tariff_type.value)
                result = await session.execute(query)
                if result.scalar_one_or_none():
                    continue

                # Create tariff plan
                limits = TARIFF_LIMITS[tariff_type]
                tariff = TariffPlan(
                    type=tariff_type.value,
                    name=tariff_type.name.capitalize() + " Plan",
                    price_points=limits.points_cost,
                    generations_limit=limits.daily_generations,
                    images_limit=limits.daily_images,
                    features=TariffPlan.get_default_features(tariff_type),
                    is_active=True
                )
                session.add(tariff)

            await session.commit()
            logger.info("Default tariffs created successfully")
    except Exception as e:
        logger.error(f"Error creating default tariffs: {e}")
        raise


async def create_default_achievements():
    """Create default achievements in the database"""
    try:
        # Import here to avoid circular import
        from ..models.achievements import Achievement
        from ..core.constants import ActionType, ContentType

        # Определяем достижения по умолчанию
        default_achievements = [
            {
                "code": "first_generation",
                "name": "First Generation",
                "description": "Create your first content",
                "icon": "🚀",
                "conditions": {
                    "action_type": ActionType.GENERATION.value,
                    "count": 1
                },
                "points_reward": 10
            },
            {
                "code": "content_creator",
                "name": "Content Creator",
                "description": "Create 10 content items",
                "icon": "✍️",
                "conditions": {
                    "action_type": ActionType.GENERATION.value,
                    "count": 10
                },
                "points_reward": 50
            },
            {
                "code": "game_master",
                "name": "Game Master",
                "description": "Create 5 games",
                "icon": "🎮",
                "conditions": {
                    "action_type": ActionType.GENERATION.value,
                    "content_type": ContentType.GAME.value,
                    "count": 5
                },
                "points_reward": 30
            },
            {
                "code": "lesson_planner",
                "name": "Lesson Planner",
                "description": "Create 5 lesson plans",
                "icon": "📚",
                "conditions": {
                    "action_type": ActionType.GENERATION.value,
                    "content_type": ContentType.LESSON_PLAN.value,
                    "count": 5
                },
                "points_reward": 30
            }
        ]

        async with async_session() as session:
            for achievement_data in default_achievements:
                # Проверяем, существует ли достижение с таким кодом
                query = select(Achievement).where(Achievement.code == achievement_data["code"])
                result = await session.execute(query)
                if result.scalar_one_or_none():
                    continue

                # Создаем достижение
                achievement = Achievement(**achievement_data)
                session.add(achievement)

            await session.commit()
            logger.info("Default achievements created successfully")
    except Exception as e:
        logger.error(f"Error creating default achievements: {e}")
        raise


async def apply_migrations():
    """Применяет миграции к базе данных"""
    try:
        logger.info("Applying database migrations...")

        # Список миграций для выполнения
        migrations = [
            # Добавление столбца error_type в таблицу feature_usage
            """
            DO $$
            BEGIN
                -- Проверяем, существует ли столбец error_type в таблице feature_usage
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'feature_usage' AND column_name = 'error_type'
                ) THEN
                    -- Добавляем столбец error_type
                    ALTER TABLE feature_usage ADD COLUMN error_type VARCHAR(100);
                    RAISE NOTICE 'Column error_type added to feature_usage table';
                ELSE
                    RAISE NOTICE 'Column error_type already exists in feature_usage table';
                END IF;
            END $$;
            """,

            # Добавление поддержки timezone-aware объектов datetime
            """
            DO $$
            DECLARE
                table_rec RECORD;
            BEGIN
                -- Для каждой таблицы с datetime столбцами без timezone
                FOR table_rec IN
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE data_type = 'timestamp without time zone'
                LOOP
                    -- Изменяем тип столбца на timestamp with time zone
                    EXECUTE format('ALTER TABLE %I ALTER COLUMN %I TYPE timestamp with time zone;',
                                  table_rec.table_name, table_rec.column_name);

                    -- Обновляем значения, добавляя UTC timezone
                    EXECUTE format('UPDATE %I SET %I = %I AT TIME ZONE ''UTC'';',
                                  table_rec.table_name, table_rec.column_name, table_rec.column_name);

                    RAISE NOTICE 'Column % in table % updated to support timezones',
                                table_rec.column_name, table_rec.table_name;
                END LOOP;
            END $$;
            """
        ]

        # Выполняем каждую миграцию
        async with engine.begin() as conn:
            for migration in migrations:
                await conn.execute(text(migration))

        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        raise


async def cleanup_db():
    """Очистка подключений при выключении"""
    compiled_cache.clear()
    await engine.dispose()
    logger.info("Database connections closed")