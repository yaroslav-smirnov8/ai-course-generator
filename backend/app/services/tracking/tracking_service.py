from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from ...models import (
    UsageLog,
    DailyUsage,
    UsageStatistics,
    GenerationMetrics,
    UserActivityLog
)
from ...core.constants import ActionType, ContentType
import logging
from sqlalchemy import select, func, text

logger = logging.getLogger(__name__)


class TrackingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def track_action(
            self,
            user_id: int,
            action_type: str,  # Changed from ActionType to str
            content_type: Optional[str] = None,  # Changed from ContentType to str
            points_change: int = 0,
            extra_data: Dict[str, Any] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ):
        """Записывает действие пользователя"""
        try:
            # Convert string values to Enum instances
            action_type_enum = None
            content_type_enum = None

            try:
                action_type_enum = ActionType(action_type)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid action_type: {action_type}. Error: {str(e)}")
                # Fallback to a default value or continue with None

            if content_type:
                try:
                    content_type_enum = ContentType(content_type)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid content_type: {content_type}. Error: {str(e)}")
                    # Fallback to a default value or continue with None

            # Создаем запись в логе использования
            usage_log = UsageLog(
                user_id=user_id,
                action_type=action_type_enum,
                content_type=content_type_enum,
                points_change=points_change,
                extra_data=extra_data or {}
            )
            self.session.add(usage_log)

            # Обновляем дневное использование
            await self._update_daily_usage(
                user_id,
                action_type_enum,
                content_type_enum,
                points_change
            )

            # Логируем активность пользователя
            activity_log = UserActivityLog(
                user_id=user_id,
                action_type=action_type_enum,
                content_type=content_type_enum,
                ip_address=ip_address,
                user_agent=user_agent,
                activity_metadata=extra_data or {}
            )
            self.session.add(activity_log)

            await self.session.commit()

        except Exception as e:
            logger.error(f"Error tracking action: {str(e)}")
            await self.session.rollback()
            raise

    async def _update_daily_usage(
            self,
            user_id: int,
            action_type: Optional[ActionType],
            content_type: Optional[ContentType],
            points_change: int
    ):
        """
        Обновляет статистику дневного использования.
        Использует INSERT ... ON CONFLICT для предотвращения дублирующихся записей.
        Работает независимо от наличия активной транзакции.
        """
        # Используем точную дату в UTC без времени для предотвращения проблем с часовыми поясами
        today = datetime.now(timezone.utc).date()

        try:
            # Определяем инкременты для разных типов контента
            generations_increment = 1 if action_type == ActionType.GENERATION else 0
            lesson_plans_increment = 1 if action_type == ActionType.GENERATION and (content_type == ContentType.LESSON_PLAN or content_type == ContentType.COURSE_LESSON_PLAN) else 0
            exercises_increment = 1 if action_type == ActionType.GENERATION and (content_type == ContentType.EXERCISE or content_type == ContentType.COURSE_EXERCISE) else 0
            games_increment = 1 if action_type == ActionType.GENERATION and (content_type == ContentType.GAME or content_type == ContentType.COURSE_GAME) else 0
            images_increment = 1 if action_type == ActionType.GENERATION and content_type == ContentType.IMAGE else 0
            transcripts_increment = 1 if action_type == ActionType.GENERATION and content_type == ContentType.TRANSCRIPT else 0

            # Определяем изменения баллов
            points_earned_increment = points_change if points_change > 0 else 0
            points_spent_increment = abs(points_change) if points_change < 0 else 0

            # Используем INSERT ... ON CONFLICT для атомарного обновления
            query = text("""
            INSERT INTO daily_usage (user_id, date, generations_count, lesson_plans_count, exercises_count, games_count, images_count, transcripts_count, points_earned, points_spent)
            VALUES (:user_id, :date, :generations_increment, :lesson_plans_increment, :exercises_increment, :games_increment, :images_increment, :transcripts_increment, :points_earned_increment, :points_spent_increment)
            ON CONFLICT (user_id, date) DO UPDATE SET
                generations_count = daily_usage.generations_count + :generations_increment,
                lesson_plans_count = daily_usage.lesson_plans_count + :lesson_plans_increment,
                exercises_count = daily_usage.exercises_count + :exercises_increment,
                games_count = daily_usage.games_count + :games_increment,
                images_count = daily_usage.images_count + :images_increment,
                transcripts_count = daily_usage.transcripts_count + :transcripts_increment,
                points_earned = daily_usage.points_earned + :points_earned_increment,
                points_spent = daily_usage.points_spent + :points_spent_increment
            WHERE daily_usage.user_id = :user_id AND daily_usage.date = :date
            RETURNING id, user_id, date, generations_count, lesson_plans_count, exercises_count, games_count, images_count, transcripts_count, points_earned, points_spent
            """)

            # Выполняем запрос без начала новой транзакции
            result = await self.session.execute(query, {
                "user_id": user_id,
                "date": today,
                "generations_increment": generations_increment,
                "lesson_plans_increment": lesson_plans_increment,
                "exercises_increment": exercises_increment,
                "games_increment": games_increment,
                "images_increment": images_increment,
                "transcripts_increment": transcripts_increment,
                "points_earned_increment": points_earned_increment,
                "points_spent_increment": points_spent_increment
            })

            # Если транзакция не была начата извне, фиксируем изменения
            need_commit = not self.session.in_transaction()

            # Получаем обновленную запись из результата запроса
            row = result.fetchone()
            if row:
                # Создаем объект DailyUsage из результата запроса
                daily_usage = DailyUsage(
                    id=row[0],
                    user_id=row[1],
                    date=row[2],
                    generations_count=row[3],
                    lesson_plans_count=row[4],
                    exercises_count=row[5],
                    games_count=row[6],
                    images_count=row[7],
                    transcripts_count=row[8],
                    points_earned=row[9],
                    points_spent=row[10]
                )

                if need_commit:
                    await self.session.commit()

                return daily_usage

            # Если запрос не вернул результат, попробуем получить запись напрямую
            stmt = select(DailyUsage).where(
                DailyUsage.user_id == user_id,
                DailyUsage.date == today
            )
            result = await self.session.execute(stmt)
            daily_usage = result.scalar_one_or_none()

            if need_commit:
                await self.session.commit()

            return daily_usage

        except Exception as e:
            logger.error(f"Ошибка при обновлении дневного использования: {e}", exc_info=True)

            # Если транзакция не была начата извне, откатываем изменения
            if not self.session.in_transaction():
                await self.session.rollback()

            # Попробуем получить текущую запись
            try:
                stmt = select(DailyUsage).where(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date == today
                )
                result = await self.session.execute(stmt)
                daily_usage = result.scalar_one_or_none()
                return daily_usage
            except Exception as inner_e:
                logger.error(f"Ошибка при получении текущей записи после сбоя: {inner_e}", exc_info=True)
                return None

    async def get_user_statistics(
            self,
            user_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> UsageStatistics:
        """Получает статистику использования за период"""
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # Получаем или создаем запись статистики
        stmt = select(UsageStatistics).where(
            UsageStatistics.user_id == user_id,
            UsageStatistics.period_start == start_date,
            UsageStatistics.period_end == end_date
        )
        result = await self.session.execute(stmt)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = await self._calculate_statistics(user_id, start_date, end_date)
            self.session.add(stats)
            await self.session.commit()

        return stats

    async def _calculate_statistics(
            self,
            user_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> UsageStatistics:
        """Рассчитывает статистику за период"""
        # Получаем все логи за период
        stmt = select(UsageLog).where(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at <= end_date
        )
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        # Считаем статистику
        stats = UsageStatistics(
            user_id=user_id,
            period_start=start_date,
            period_end=end_date
        )

        generations_by_type = {}
        popular_prompts = {}
        points_earned = 0
        points_spent = 0

        for log in logs:
            if log.action_type == ActionType.GENERATION:
                stats.total_generations += 1
                if log.content_type:
                    content_type_key = log.content_type.value
                    generations_by_type[content_type_key] = \
                        generations_by_type.get(content_type_key, 0) + 1

                    # Сохраняем популярные запросы
                    if log.extra_data and 'prompt' in log.extra_data:
                        prompt_list = popular_prompts.get(content_type_key, [])
                        prompt_list.append(log.extra_data['prompt'])
                        popular_prompts[content_type_key] = prompt_list[:10]

            elif log.action_type == ActionType.IMAGE:
                stats.total_images += 1

            if log.points_change > 0:
                points_earned += log.points_change
            else:
                points_spent += abs(log.points_change)

        # Заполняем статистику
        stats.generations_by_type = generations_by_type
        stats.popular_prompts = popular_prompts
        stats.points_earned = points_earned
        stats.points_spent = points_spent

        # Считаем средние показатели
        days = (end_date - start_date).days or 1
        stats.avg_daily_generations = stats.total_generations / days
        stats.avg_daily_images = stats.total_images / days

        return stats

    async def track_generation_metrics(
            self,
            user_id: int,
            content_type: str,  # Changed from ContentType to str
            prompt: str,
            tokens_used: int,
            generation_time: float,
            success: bool = True,
            error_type: Optional[str] = None
    ):
        """Записывает метрики генерации"""
        try:
            # Convert string to ContentType Enum if possible
            content_type_enum = None
            try:
                content_type_enum = ContentType(content_type)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid content_type: {content_type}. Error: {str(e)}")

            metrics = GenerationMetrics(
                user_id=user_id,
                content_type=content_type_enum,
                prompt=prompt,
                tokens_used=tokens_used,
                generation_time=generation_time,
                success=success,
                error_type=error_type
            )
            self.session.add(metrics)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error tracking generation metrics: {str(e)}")
            await self.session.rollback()
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def remove_duplicate_daily_usage(self):
        """
        Удаляет дублирующиеся записи в таблице daily_usage, оставляя только самую последнюю запись
        для каждой комбинации user_id и date.
        """
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
            )
            DELETE FROM daily_usage
            WHERE id IN (
                SELECT id FROM duplicates WHERE row_num > 1
            )
            """)

            # Выполняем запрос
            result = await self.session.execute(query)

            # Если транзакция не была начата извне, фиксируем изменения
            if not self.session.in_transaction():
                await self.session.commit()

            # Получаем количество удаленных записей
            deleted_count = result.rowcount if hasattr(result, 'rowcount') else 0
            logger.info(f"Удалено {deleted_count} дублирующихся записей в таблице daily_usage")

            return deleted_count
        except Exception as e:
            logger.error(f"Ошибка при удалении дублирующихся записей: {e}")

            # Если транзакция не была начата извне, откатываем изменения
            if not self.session.in_transaction():
                await self.session.rollback()

            return 0