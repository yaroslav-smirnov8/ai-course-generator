"""
Сервис для проверки лимитов генераций на основе тарифов пользователей.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc, func, text
from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any, Tuple, Union

from ...models import User, DailyUsage, TariffPlan
from ...core.constants import ContentType, TariffType, ActionType, TARIFF_LIMITS, UNLIMITED_ROLES
from ...core.utils import safe_content_type

logger = logging.getLogger(__name__)

class LimitsChecker:
    """
    Сервис для проверки лимитов генераций и других ограничений тарифов.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def can_generate(
        self,
        user_id: int,
        content_type: Union[str, ContentType],
        check_only: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет, может ли пользователь выполнить генерацию контента
        указанного типа в рамках своего тарифа.

        Args:
            user_id: ID пользователя
            content_type: Тип контента для генерации
            check_only: Только проверить, не обновлять счетчики

        Returns:
            Tuple[bool, str]: (может_генерировать, причина_отказа)
        """
        # Получаем пользователя и его тариф
        user_query = select(User).where(User.id == user_id)
        result = await self.session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return False, "Пользователь не найден"

        # Проверяем, имеет ли пользователь безлимитный доступ
        if user.role in UNLIMITED_ROLES:
            logger.info(f"Пользователь {user_id} имеет роль {user.role} с безлимитным доступом")
            return True, None

        # Проверяем, активен ли тариф
        if not user.tariff or not user.tariff_valid_until:
            return False, "У пользователя нет активного тарифа"

        if user.tariff_valid_until < datetime.now(timezone.utc):
            return False, "Срок действия тарифа истек"

        # Получаем дневное использование
        today = datetime.now(timezone.utc).date()
        usage_query = select(DailyUsage).where(
            DailyUsage.user_id == user_id,
            DailyUsage.date == today
        ).order_by(DailyUsage.id.desc())
        usage_result = await self.session.execute(usage_query)
        daily_usage = usage_result.scalar_one_or_none()

        # Проверяем, есть ли дублирующиеся записи
        count_stmt = select(func.count(DailyUsage.id)).where(
            DailyUsage.user_id == user_id,
            DailyUsage.date == today
        )
        count_result = await self.session.execute(count_stmt)
        count = count_result.scalar_one()

        if count > 1:
            logger.warning(f"Найдено {count} записей DailyUsage для пользователя {user_id} на сегодня. Используем самую последнюю.")

        if not daily_usage:
            try:
                # Создаем новую запись использования
                daily_usage = DailyUsage(user_id=user_id, date=today)
                self.session.add(daily_usage)
                if not check_only:
                    try:
                        await self.session.commit()
                    except exc.IntegrityError as e:
                        # Если произошла ошибка уникального ограничения, значит запись уже создана
                        # в другом потоке/процессе, делаем rollback и пробуем получить запись снова
                        logger.info(f"Запись DailyUsage для пользователя {user_id} уже существует, получаем её")
                        await self.session.rollback()

                        # Повторно запрашиваем запись
                        usage_query = select(DailyUsage).where(
                            DailyUsage.user_id == user_id,
                            DailyUsage.date == today
                        )
                        usage_result = await self.session.execute(usage_query)
                        daily_usage = usage_result.scalar_one_or_none()

                        if not daily_usage:
                            # Если запись все еще не найдена, это странно, логируем ошибку
                            logger.error(f"Не удалось получить запись DailyUsage после IntegrityError: {e}")
                            return False, "Ошибка при проверке лимитов"
                return True, None
            except Exception as e:
                logger.error(f"Ошибка при создании записи DailyUsage: {e}")
                await self.session.rollback()
                return False, "Ошибка при проверке лимитов"

        # Преобразуем content_type к правильному типу
        content_type_enum = safe_content_type(content_type)
        if not content_type_enum:
            logger.warning(f"Неизвестный тип контента: {content_type}")
            return False, f"Неизвестный тип контента: {content_type}"

        # Получаем лимиты для тарифа пользователя
        tariff_limits = TARIFF_LIMITS.get(user.tariff)
        if not tariff_limits:
            logger.warning(f"Не найдены лимиты для тарифа {user.tariff}")
            return False, "Не найдены лимиты для тарифа"

        # Проверяем лимит по типу контента
        if content_type_enum == ContentType.IMAGE:
            if daily_usage.images_count >= tariff_limits.daily_images:
                return False, f"Превышен дневной лимит изображений ({tariff_limits.daily_images})"
        else:
            # Для других типов контента проверяем общее количество генераций
            if daily_usage.generations_count >= tariff_limits.daily_generations:
                return False, f"Превышен дневной лимит генераций ({tariff_limits.daily_generations})"

        return True, None

    async def update_usage_counter(
        self,
        user_id: int,
        content_type: Union[str, ContentType]
    ) -> bool:
        """
        Обновляет счетчик использования после успешной генерации.

        Args:
            user_id: ID пользователя
            content_type: Тип контента

        Returns:
            bool: Успешно ли обновлен счетчик
        """
        try:
            # Получаем дневное использование
            today = datetime.now(timezone.utc).date()
            usage_query = select(DailyUsage).where(
                DailyUsage.user_id == user_id,
                DailyUsage.date == today
            ).order_by(DailyUsage.id.desc())
            usage_result = await self.session.execute(usage_query)
            daily_usage = usage_result.scalar_one_or_none()

            # Проверяем, есть ли дублирующиеся записи
            count_stmt = select(func.count(DailyUsage.id)).where(
                DailyUsage.user_id == user_id,
                DailyUsage.date == today
            )
            count_result = await self.session.execute(count_stmt)
            count = count_result.scalar_one()

            if count > 1:
                logger.warning(f"Найдено {count} записей DailyUsage для пользователя {user_id} на сегодня. Используем самую последнюю.")

            if not daily_usage:
                try:
                    # Создаем новую запись использования
                    daily_usage = DailyUsage(user_id=user_id, date=today)
                    self.session.add(daily_usage)

                    try:
                        # Пробуем сохранить новую запись
                        await self.session.flush()
                    except exc.IntegrityError as e:
                        # Если произошла ошибка уникального ограничения, значит запись уже создана
                        # в другом потоке/процессе, делаем rollback и пробуем получить запись снова
                        logger.info(f"Запись DailyUsage для пользователя {user_id} уже существует, получаем её")
                        await self.session.rollback()

                        # Повторно запрашиваем запись
                        usage_query = select(DailyUsage).where(
                            DailyUsage.user_id == user_id,
                            DailyUsage.date == today
                        )
                        usage_result = await self.session.execute(usage_query)
                        daily_usage = usage_result.scalar_one_or_none()

                        if not daily_usage:
                            # Если запись все еще не найдена, это странно, логируем ошибку
                            logger.error(f"Не удалось получить запись DailyUsage после IntegrityError: {e}")
                            return False
                except Exception as e:
                    logger.error(f"Ошибка при создании записи DailyUsage: {e}")
                    await self.session.rollback()
                    return False

            # Преобразуем content_type к правильному типу
            content_type_enum = safe_content_type(content_type)

            # Увеличиваем общий счетчик генераций
            daily_usage.generations_count += 1

            # Увеличиваем счетчик для конкретного типа
            if content_type_enum == ContentType.LESSON_PLAN or content_type_enum == ContentType.COURSE_LESSON_PLAN:
                daily_usage.lesson_plans_count += 1
            elif content_type_enum == ContentType.EXERCISE or content_type_enum == ContentType.COURSE_EXERCISE:
                daily_usage.exercises_count += 1
            elif content_type_enum == ContentType.GAME or content_type_enum == ContentType.COURSE_GAME:
                daily_usage.games_count += 1
            elif content_type_enum == ContentType.IMAGE:
                daily_usage.images_count += 1
            elif content_type_enum == ContentType.TRANSCRIPT:
                daily_usage.transcripts_count += 1
            elif content_type_enum == ContentType.COURSE:
                # Если нет специального счетчика для курсов, увеличиваем только общий
                pass

            try:
                await self.session.commit()
            except exc.IntegrityError as e:
                logger.error(f"Ошибка целостности при обновлении счетчика использования: {e}")
                await self.session.rollback()
                return False
            return True

        except Exception as e:
            logger.error(f"Ошибка при обновлении счетчика использования: {e}")
            await self.session.rollback()
            return False

    async def get_remaining_limits(self, user_id: int) -> Dict[str, Any]:
        """
        Получает оставшиеся лимиты пользователя на текущий день.

        Args:
            user_id: ID пользователя

        Returns:
            Dict: Информация об оставшихся лимитах
        """
        # Получаем пользователя и его тариф
        user_query = select(User).where(User.id == user_id)
        result = await self.session.execute(user_query)
        user = result.scalar_one_or_none()

        if not user:
            return {"error": "Пользователь не найден"}

        # Безлимитные роли
        if user.role in UNLIMITED_ROLES:
            return {
                "unlimited": True,
                "tariff": user.tariff.value if user.tariff else None,
                "valid_until": user.tariff_valid_until.isoformat() if user.tariff_valid_until else None,
                "is_active": True
            }

        # Проверяем, активен ли тариф
        if not user.tariff or not user.tariff_valid_until:
            return {
                "unlimited": False,
                "tariff": None,
                "valid_until": None,
                "is_active": False,
                "error": "У пользователя нет активного тарифа"
            }

        is_active = user.tariff_valid_until >= datetime.now(timezone.utc)

        # Получаем лимиты тарифа
        tariff_limits = TARIFF_LIMITS.get(user.tariff)
        if not tariff_limits:
            return {
                "unlimited": False,
                "tariff": user.tariff.value,
                "valid_until": user.tariff_valid_until.isoformat(),
                "is_active": is_active,
                "error": "Не найдены лимиты для тарифа"
            }

        # Получаем дневное использование
        today = datetime.now(timezone.utc).date()
        usage_query = select(DailyUsage).where(
            DailyUsage.user_id == user_id,
            DailyUsage.date == today
        ).order_by(DailyUsage.id.desc())
        usage_result = await self.session.execute(usage_query)
        daily_usage = usage_result.scalar_one_or_none()

        # Проверяем, есть ли дублирующиеся записи
        count_stmt = select(func.count(DailyUsage.id)).where(
            DailyUsage.user_id == user_id,
            DailyUsage.date == today
        )
        count_result = await self.session.execute(count_stmt)
        count = count_result.scalar_one()

        if count > 1:
            logger.warning(f"Найдено {count} записей DailyUsage для пользователя {user_id} на сегодня. Используем самую последнюю.")

            # Удаляем дублирующиеся записи
            try:
                # Находим дублирующиеся записи
                query = text("""
                WITH duplicates AS (
                    SELECT
                        id,
                        user_id,
                        date,
                        ROW_NUMBER() OVER (PARTITION BY user_id, date ORDER BY id DESC) as row_num
                    FROM daily_usage
                    WHERE user_id = :user_id AND date = :date
                )
                DELETE FROM daily_usage
                WHERE id IN (
                    SELECT id FROM duplicates WHERE row_num > 1
                )
                """)

                # Выполняем запрос
                await self.session.execute(query, {"user_id": user_id, "date": today})
                await self.session.commit()
                logger.info(f"Удалены дублирующиеся записи DailyUsage для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка при удалении дублирующихся записей: {e}")
                await self.session.rollback()

        if not daily_usage:
            # Если нет записи использования, значит все лимиты доступны полностью
            return {
                "unlimited": False,
                "tariff": user.tariff.value,
                "valid_until": user.tariff_valid_until.isoformat(),
                "is_active": is_active,
                "generations": {
                    "limit": tariff_limits.daily_generations,
                    "used": 0,
                    "remaining": tariff_limits.daily_generations
                },
                "images": {
                    "limit": tariff_limits.daily_images,
                    "used": 0,
                    "remaining": tariff_limits.daily_images
                }
            }

        # Рассчитываем оставшиеся лимиты
        generations_used = daily_usage.generations_count
        images_used = daily_usage.images_count

        generations_remaining = max(0, tariff_limits.daily_generations - generations_used)
        images_remaining = max(0, tariff_limits.daily_images - images_used)

        return {
            "unlimited": False,
            "tariff": user.tariff.value,
            "valid_until": user.tariff_valid_until.isoformat(),
            "is_active": is_active,
            "generations": {
                "limit": tariff_limits.daily_generations,
                "used": generations_used,
                "remaining": generations_remaining
            },
            "images": {
                "limit": tariff_limits.daily_images,
                "used": images_used,
                "remaining": images_remaining
            },
            "details": {
                "lesson_plans": daily_usage.lesson_plans_count,
                "exercises": daily_usage.exercises_count,
                "games": daily_usage.games_count,
                "transcripts": daily_usage.transcripts_count
            }
        }