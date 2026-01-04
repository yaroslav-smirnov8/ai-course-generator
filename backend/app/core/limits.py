from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import check_unlimited_access
from app.core.constants import TariffType, TARIFF_LIMITS
from app.models import DailyUsage, User
from sqlalchemy import select, text
from datetime import datetime, timezone
from app.core.types import ContentType
import logging

logger = logging.getLogger(__name__)

async def check_generation_limit(user_id: int, session: AsyncSession, content_type: ContentType = None) -> bool:
    """
    Проверяет, доступна ли генерация для пользователя (в рамках его лимитов)

    Args:
        user_id: ID пользователя
        session: Сессия базы данных
        content_type: Тип контента для генерации (опционально)

    Returns:
        bool: True если генерация доступна, False если лимит исчерпан
    """
    # Сначала проверяем, есть ли у пользователя неограниченный доступ
    is_unlimited = await check_unlimited_access(user_id, session)
    if is_unlimited:
        return True

    # Проверяем дневное использование
    today = datetime.now(timezone.utc).date()
    stmt = select(DailyUsage).where(
        DailyUsage.user_id == user_id,
        DailyUsage.date == today
    )
    result = await session.execute(stmt)
    daily_usage = result.scalar_one_or_none()

    # Проверяем тариф пользователя для определения лимита
    user_stmt = select(User).where(User.id == user_id)
    user_result = await session.execute(user_stmt)
    user_db = user_result.scalar_one_or_none()

    # Получаем лимиты на основе тарифа
    tariff = user_db.tariff if user_db else TariffType.FREE
    limits = TARIFF_LIMITS.get(tariff, TARIFF_LIMITS[TariffType.FREE])

    # Если записи о дневном использовании нет, значит лимит не исчерпан
    if not daily_usage:
        return True

    # Проверяем лимит в зависимости от типа контента
    if content_type == ContentType.IMAGE:
        # Для изображений проверяем отдельный лимит
        if daily_usage.images_count >= limits.daily_images:
            logger.warning(f"User {user_id} reached daily image limit: {daily_usage.images_count}/{limits.daily_images}")
            return False
    else:
        # Для всех остальных типов контента проверяем общий лимит генераций
        if daily_usage.generations_count >= limits.daily_generations:
            logger.warning(f"User {user_id} reached daily generation limit: {daily_usage.generations_count}/{limits.daily_generations}")
            return False

    return True

async def reset_daily_usage_counters(user_id: int, session: AsyncSession) -> bool:
    """
    Сбрасывает счетчики дневного использования для пользователя

    Args:
        user_id: ID пользователя
        session: Сессия базы данных

    Returns:
        bool: True если сброс успешен, False в случае ошибки
    """
    try:
        today = datetime.now(timezone.utc).date()

        # Используем прямой SQL запрос с указанием всех необходимых полей
        reset_query = text("""
        INSERT INTO daily_usage
            (user_id, date, generations_count, images_count, lesson_plans_count,
             exercises_count, games_count, transcripts_count, points_earned, points_spent)
        VALUES
            (:user_id, :date, 0, 0, 0, 0, 0, 0, 0, 0)
        ON CONFLICT (user_id, date)
        DO UPDATE SET
            generations_count = 0,
            images_count = 0,
            lesson_plans_count = 0,
            exercises_count = 0,
            games_count = 0,
            transcripts_count = 0
        """)

        await session.execute(
            reset_query,
            {
                "user_id": user_id,
                "date": today
            }
        )

        # Проверяем, что счетчики действительно сброшены
        verify_query = select(DailyUsage).where(
            DailyUsage.user_id == user_id,
            DailyUsage.date == today
        )
        verify_result = await session.execute(verify_query)
        verify_usage = verify_result.scalar_one_or_none()

        if verify_usage:
            logger.info(f"Verified reset counters for user {user_id}: " +
                       f"generations={verify_usage.generations_count}, " +
                       f"images={verify_usage.images_count}")

            # Проверяем, что все счетчики действительно равны нулю
            if (verify_usage.generations_count > 0 or
                verify_usage.images_count > 0 or
                verify_usage.lesson_plans_count > 0 or
                verify_usage.exercises_count > 0 or
                verify_usage.games_count > 0 or
                verify_usage.transcripts_count > 0):

                logger.warning(f"Some counters were not reset properly for user {user_id}! Forcing reset with direct SQL.")

                # Используем прямой SQL запрос для принудительного сброса
                force_reset_query = text("""
                UPDATE daily_usage
                SET generations_count = 0,
                    images_count = 0,
                    lesson_plans_count = 0,
                    exercises_count = 0,
                    games_count = 0,
                    transcripts_count = 0
                WHERE user_id = :user_id AND date = :date
                """)

                await session.execute(
                    force_reset_query,
                    {
                        "user_id": user_id,
                        "date": today
                    }
                )

        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Error resetting daily usage counters: {str(e)}", exc_info=True)
        await session.rollback()
        return False