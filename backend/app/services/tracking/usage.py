# app/services/tracking/usage.py
from sqlalchemy.ext.asyncio import AsyncSession
from ...models import UsageLog
from ...schemas.tracking import UsageLogCreate
from ...core.constants import ActionType, ContentType
from datetime import datetime, timezone
import logging
from sqlalchemy import select, func, and_, exc

logger = logging.getLogger(__name__)


class UsageTracker:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Инициализируем query_optimizer
        from ...services.optimization.query_optimizer import QueryOptimizer
        self.query_optimizer = QueryOptimizer(session)

    async def log_usage(self, usage_data: UsageLogCreate) -> UsageLog:
        """Log usage action and update daily counters"""
        try:
            log = UsageLog(
                user_id=usage_data.user_id,
                action_type=usage_data.action_type,
                points_change=usage_data.points_change,
                extra_data=usage_data.extra_data or {},
                daily_usage_count=1  # Will be updated below
            )

            # Обработка content_type - преобразуем в enum если передана строка
            if usage_data.content_type:
                try:
                    from ...core.constants import ContentType
                    # Если передан Enum, используем его значение (value)
                    if isinstance(usage_data.content_type, ContentType):
                        log.content_type = usage_data.content_type.value
                    # Если передана строка, проверяем разные варианты
                    elif isinstance(usage_data.content_type, str):
                        # Преобразуем строку в нижний регистр для дальнейшей обработки
                        content_type_lower = usage_data.content_type.lower()
                        content_type_upper = usage_data.content_type.upper()

                        # Проверяем, может быть это уже название в правильном формате
                        for ct in ContentType:
                            if ct.value == content_type_lower:
                                log.content_type = ct.value
                                break
                            # Проверяем, может это имя перечисления в верхнем регистре
                            elif ct.name == content_type_upper:
                                log.content_type = ct.value
                                break
                        else:
                            # Если не нашли подходящий тип, используем преобразованное к нижнему регистру значение
                            # Это позволит избежать ошибок с отправкой "COURSE" вместо "course"
                            log.content_type = content_type_lower
                    else:
                        # Для других типов, пытаемся преобразовать в строку и привести к нижнему регистру
                        log.content_type = str(usage_data.content_type).lower()
                except Exception as e:
                    logger.error(f"Error processing content_type: {e}", exc_info=True)
                    # При ошибке пытаемся безопасно установить тип, преобразуя к нижнему регистру
                    if isinstance(usage_data.content_type, str):
                        log.content_type = usage_data.content_type.lower()
                    else:
                        # В крайнем случае - не устанавливаем content_type
                        pass

            # Get current daily usage count for this type
            count_query = await self.query_optimizer.optimize_query(
                select(func.count())
                .select_from(UsageLog)
                .where(
                    and_(
                        UsageLog.user_id == usage_data.user_id,
                        UsageLog.action_type == usage_data.action_type,
                        UsageLog.content_type == log.content_type,
                        func.date(UsageLog.created_at) == func.date(func.now())
                    )
                )
            )
            result = await self.session.execute(count_query)
            current_count = result.scalar() or 0

            # Set accurate count
            log.daily_usage_count = current_count + 1

            self.session.add(log)
            await self.session.flush()

            # Update daily usage statistics only if skip_limits is False
            # Если skip_limits=True (генерация за баллы), не обновляем счетчики дневного использования
            if not usage_data.skip_limits:
                await self._update_daily_usage(usage_data.user_id, log)
            else:
                logger.info(f"Skipping daily usage update for user {usage_data.user_id} (skip_limits=True)")

            return log

        except Exception as e:
            logger.error(f"Error logging usage: {e}", exc_info=True)
            raise

    async def _update_daily_usage(self, user_id: int, log: UsageLog) -> None:
        """
        Обновляет статистику ежедневного использования.
        Использует INSERT ... ON CONFLICT для предотвращения дублирующихся записей.
        Работает независимо от наличия активной транзакции.
        """
        from ...models.tracking import DailyUsage
        from sqlalchemy import func, text

        # Используем точную дату в UTC без времени для предотвращения проблем с часовыми поясами
        today = datetime.now(timezone.utc).date()

        try:
            # Определяем инкременты для разных типов контента
            generations_increment = 0
            lesson_plans_increment = 0
            exercises_increment = 0
            games_increment = 0
            images_increment = 0
            transcripts_increment = 0

            # Обновляем специфичные счетчики И общий счетчик в зависимости от типа контента
            if log.content_type:
                # Используем ContentType enum для надежного сравнения
                try:
                    content_type_enum = ContentType(log.content_type) # Преобразуем строку/value обратно в Enum

                    if content_type_enum == ContentType.LESSON_PLAN or content_type_enum == ContentType.COURSE_LESSON_PLAN:
                        lesson_plans_increment = 1
                        generations_increment = 1
                    elif content_type_enum == ContentType.EXERCISE or content_type_enum == ContentType.COURSE_EXERCISE:
                        exercises_increment = 1
                        generations_increment = 1
                    elif content_type_enum == ContentType.GAME or content_type_enum == ContentType.COURSE_GAME:
                        games_increment = 1
                        generations_increment = 1
                    elif content_type_enum == ContentType.IMAGE:
                        images_increment = 1
                        # Не увеличиваем generations_count для картинок, если они считаются отдельно
                    elif content_type_enum == ContentType.TRANSCRIPT:
                        transcripts_increment = 1
                        generations_increment = 1
                    elif content_type_enum == ContentType.COURSE:
                        # Генерация самого курса - увеличиваем только общий счетчик
                        generations_increment = 1
                except ValueError:
                    logger.warning(f"Unknown content_type '{log.content_type}' received in _update_daily_usage. Only updating general generations_count.")
                    # Если тип неизвестен, на всякий случай увеличим общий счетчик
                    generations_increment = 1

            # Определяем изменения баллов
            points_earned_increment = log.points_change if log.points_change > 0 else 0
            points_spent_increment = abs(log.points_change) if log.points_change < 0 else 0

            # Используем INSERT ... ON CONFLICT для атомарного обновления
            # Обязательно указываем все поля с NOT NULL ограничениями
            query = text("""
            INSERT INTO daily_usage (
                user_id,
                date,
                generations_count,
                lesson_plans_count,
                exercises_count,
                games_count,
                images_count,
                transcripts_count,
                points_earned,
                points_spent
            )
            VALUES (
                :user_id,
                :date,
                :generations_increment,
                :lesson_plans_increment,
                :exercises_increment,
                :games_increment,
                :images_increment,
                :transcripts_increment,
                :points_earned_increment,
                :points_spent_increment
            )
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
            """)

            # Выполняем запрос без начала новой транзакции
            await self.session.execute(query, {
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
            if not self.session.in_transaction():
                await self.session.commit()

        except Exception as e:
            logger.error(f"Error updating daily usage: {e}", exc_info=True)
            # Если транзакция не была начата извне, откатываем изменения
            if not self.session.in_transaction():
                await self.session.rollback()
            # Не вызываем исключение, чтобы не прерывать основной поток

    async def get_user_logs(self, user_id: int, limit: int = 100):
        """Получает логи использования для пользователя"""
        from sqlalchemy import select, desc

        query = (
            select(UsageLog)
            .where(UsageLog.user_id == user_id)
            .order_by(desc(UsageLog.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
