"""
Сервис для ежедневного обслуживания системы - сброс лимитов, очистка устаревших данных, и т.д.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_, func, exc
from typing import List, Dict, Any, Optional

from ...models import DailyUsage, UsageLog, UserTariff, User
from ...core.database import async_session
from ...core.config import settings

logger = logging.getLogger(__name__)

class DailyMaintenanceService:
    """
    Сервис для выполнения ежедневных задач обслуживания системы.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session or async_session()

    async def reset_daily_usage(self) -> int:
        """
        Сбрасывает счетчики дневного использования для всех пользователей.
        """
        try:
            today = datetime.now(timezone.utc).date()
            yesterday = today - timedelta(days=1)

            # Удаляем записи дневного использования старше определенного срока (кроме вчерашнего дня)
            delete_stmt = delete(DailyUsage).where(
                and_(
                    DailyUsage.date < yesterday,
                    DailyUsage.date < today - timedelta(days=settings.USAGE_HISTORY_DAYS)
                )
            )

            result = await self.session.execute(delete_stmt)
            deleted_count = result.rowcount

            # Создаем новые записи для активных пользователей
            # Получаем активных пользователей (заходивших за последние 7 дней)
            active_date = datetime.now(timezone.utc) - timedelta(days=7)
            active_users_query = select(User.id).where(
                or_(
                    User.last_active >= active_date,
                    User.tariff_valid_until >= datetime.now(timezone.utc)
                )
            )

            result = await self.session.execute(active_users_query)
            active_user_ids = [row[0] for row in result.fetchall()]

            # Проверяем, у каких пользователей нет записи на сегодня
            existing_query = select(DailyUsage.user_id).where(
                DailyUsage.date == today
            )
            result = await self.session.execute(existing_query)
            existing_user_ids = [row[0] for row in result.fetchall()]

            # Создаем записи для пользователей, у которых их нет
            users_to_create = set(active_user_ids) - set(existing_user_ids)
            created_count = 0

            if users_to_create:
                # Используем INSERT ... ON CONFLICT для атомарного создания записей
                from sqlalchemy import text

                # Создаем запрос для массового добавления записей
                query = text("""
                INSERT INTO daily_usage (user_id, date, generations_count, lesson_plans_count, exercises_count, games_count, images_count, transcripts_count, points_earned, points_spent)
                VALUES (:user_id, :date, 0, 0, 0, 0, 0, 0, 0, 0)
                ON CONFLICT (user_id, date) DO NOTHING
                """)

                try:
                    # Выполняем запрос для каждого пользователя
                    for user_id in users_to_create:
                        try:
                            await self.session.execute(query, {"user_id": user_id, "date": today})
                            created_count += 1
                        except Exception as e:
                            logger.error(f"Ошибка при создании записи DailyUsage для пользователя {user_id}: {e}")

                    # Финальный коммит для сохранения всех успешно созданных записей
                    await self.session.commit()
                except Exception as e:
                    logger.error(f"Ошибка при массовом создании записей DailyUsage: {e}")
                    await self.session.rollback()

            logger.info(f"Удалено {deleted_count} устаревших записей DailyUsage")
            logger.info(f"Создано {created_count} из {len(users_to_create)} новых записей DailyUsage для активных пользователей")

            return created_count

        except Exception as e:
            logger.error(f"Ошибка при сбросе дневного использования: {e}")
            await self.session.rollback()
            raise

    async def cleanup_usage_logs(self, days_to_keep: int = 30) -> int:
        """
        Удаляет старые записи из логов использования.
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            # Удаляем записи старше указанного срока
            delete_stmt = delete(UsageLog).where(
                UsageLog.created_at < cutoff_date
            )

            result = await self.session.execute(delete_stmt)
            deleted_count = result.rowcount

            await self.session.commit()

            logger.info(f"Удалено {deleted_count} устаревших записей UsageLog")

            return deleted_count

        except Exception as e:
            logger.error(f"Ошибка при очистке логов использования: {e}")
            await self.session.rollback()
            raise

    async def check_expired_tariffs(self) -> int:
        """
        Проверяет истекшие тарифы и обновляет статус пользователей.
        """
        try:
            now = datetime.now(timezone.utc)

            # Находим пользователей с истекшими тарифами
            expired_query = select(User).where(
                and_(
                    User.tariff_valid_until < now,
                    User.tariff != None
                )
            )

            result = await self.session.execute(expired_query)
            expired_users = result.scalars().all()

            count = 0
            for user in expired_users:
                # Помечаем тарифные записи как неактивные
                tariff_query = select(UserTariff).where(
                    and_(
                        UserTariff.user_id == user.id,
                        UserTariff.is_active == True
                    )
                )
                tariff_result = await self.session.execute(tariff_query)
                tariffs = tariff_result.scalars().all()

                for tariff in tariffs:
                    tariff.is_active = False

                count += 1

            await self.session.commit()

            logger.info(f"Обработано {count} пользователей с истекшими тарифами")

            return count

        except Exception as e:
            logger.error(f"Ошибка при проверке истекших тарифов: {e}")
            await self.session.rollback()
            raise

    async def run_all_maintenance_tasks(self) -> Dict[str, Any]:
        """
        Запускает все задачи обслуживания.

        Returns:
            Dict: Результаты выполнения задач
        """
        try:
            # Сброс дневного использования
            reset_count = await self.reset_daily_usage()

            # Очистка логов использования
            cleanup_count = await self.cleanup_usage_logs()

            # Проверка истекших тарифов
            expired_count = await self.check_expired_tariffs()

            return {
                "success": True,
                "reset_daily_usage": reset_count,
                "cleanup_usage_logs": cleanup_count,
                "expired_tariffs": expired_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Ошибка при выполнении задач обслуживания: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def __aenter__(self):
        if not self.session:
            self.session = async_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


# Функция для запуска обслуживания из скрипта или планировщика
async def run_maintenance():
    """
    Запускает все задачи обслуживания.
    """
    async with DailyMaintenanceService() as service:
        return await service.run_all_maintenance_tasks()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Запуск обслуживания
    results = asyncio.run(run_maintenance())

    # Вывод результатов
    logger.info(f"Результаты обслуживания: {results}")