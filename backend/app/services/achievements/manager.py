import asyncio
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import (
    Achievement,
    UserAchievement,
    UserAction,
    User,
    Generation,
    PointTransaction
)
from ...schemas.achievements import (
    AchievementProgress,
    AchievementResponse,
    UserAchievementResponse
)
from ...core.cache import CacheService
from ...core.memory import memory_optimized
from ...core.constants import ActionType, ContentType
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
import logging

logger = logging.getLogger(__name__)


class AchievementManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session, batch_size=100)
        self.cache_service = CacheService()

    @memory_optimized()
    async def check_achievements(
            self,
            user_id: int,
            action_type: str,
            action_data: dict
    ) -> None:
        """Оптимизированная проверка достижений"""
        try:
            # Проверяем session перед использованием
            if self.session is None:
                logger.error("Session is None in check_achievements")
                return
                
            # Convert string action_type to Enum if possible
            action_type_enum = None
            try:
                if action_type:
                    action_type_enum = ActionType(action_type)
            except (ValueError, TypeError):
                logger.warning(f"Invalid action type: {action_type}")
                # Продолжаем выполнение с action_type_enum = None

            # Получаем доступные достижения
            try:
                achievements = await self._get_available_achievements()
                if not achievements:
                    logger.info(f"No achievements available for user {user_id}")
                    return
                logger.debug(f"Found {len(achievements)} available achievements")
            except Exception as e:
                logger.error(f"Error getting available achievements: {str(e)}")
                return

            # Создаем список заданий для проверки достижений
            batch_data = []
            
            # Получаем текущий прогресс пользователя для всех достижений
            user_achievements = {}
            try:
                # Запрос для получения текущего прогресса пользователя
                query = select(UserAchievement).where(UserAchievement.user_id == user_id)
                result = await self.session.execute(query)
                user_achievements_list = result.scalars().all()
                
                # Создаем словарь для быстрого доступа
                for ua in user_achievements_list:
                    user_achievements[ua.achievement_id] = ua.progress
                    
                logger.debug(f"Found {len(user_achievements)} existing achievements for user {user_id}")
            except Exception as e:
                logger.error(f"Error getting user achievements: {str(e)}")
                # Продолжаем с пустым словарем, если возникла ошибка
            
            for achievement in achievements:
                # Получаем текущий прогресс или 0, если достижение еще не начато
                current_progress = user_achievements.get(achievement.id, 0)
                
                batch_data.append({
                    "achievement_id": achievement.id,
                    "achievement": achievement,
                    "current_progress": current_progress
                })

            # Если данных для обработки нет, завершаем
            if not batch_data:
                logger.debug("No achievements to process")
                return

            # Обработка батчами
            try:
                if self.batch_processor is None:
                    logger.error("Batch processor is None in check_achievements")
                    # Обрабатываем вручную, если batch_processor недоступен
                    await self._process_achievements_batch(
                        batch_data, user_id, action_type_enum, action_data
                    )
                else:
                    await self.batch_processor.process_in_batches(
                        batch_data,
                        lambda batch: self._process_achievements_batch(
                            batch, user_id, action_type_enum, action_data
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing achievements batch: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking achievements: {str(e)}")
            await self.session.rollback()
            raise

    async def _process_achievements_batch(
            self,
            batch: List[Dict],
            user_id: int,
            action_type: Optional[ActionType],
            action_data: dict
    ) -> None:
        """Пакетная обработка достижений"""
        try:
            achievements_to_update = []
            for item in batch:
                achievement = item['achievement']
                current_progress = item['current_progress']

                # Проверяем прогресс
                new_progress = await self._check_achievement_conditions(
                    user_id,
                    achievement,
                    action_type,
                    action_data
                )

                if new_progress > current_progress:
                    achievements_to_update.append({
                        'user_id': user_id,
                        'achievement_id': achievement.id,
                        'progress': new_progress,
                        'unlocked': new_progress >= 100
                    })

            # Батч-обновление достижений
            if achievements_to_update:
                await self._batch_update_achievements(achievements_to_update)

        except Exception as e:
            logger.error(f"Error processing achievements batch: {str(e)}")
            raise

    async def _check_achievement_conditions(
            self,
            user_id: int,
            achievement: Achievement,
            action_type: Optional[ActionType],
            action_data: dict
    ) -> float:
        """Проверяет условия достижения и возвращает прогресс"""
        try:
            conditions = achievement.conditions
            progress = 0.0

            # Get the content_type from action_data, either as Enum or string
            content_type = action_data.get('content_type_enum')
            content_type_str = action_data.get('content_type')

            # Process different achievement types based on conditions
            if 'generation_count' in conditions:
                query = select(func.count()).select_from(Generation).where(
                    Generation.user_id == user_id
                )

                # Apply content type filter if specified in conditions
                if 'content_type' in conditions:
                    required_content_type = conditions['content_type']

                    # Handle both string and enum comparisons
                    if content_type and isinstance(content_type, ContentType):
                        if content_type.value == required_content_type:
                            query = query.where(Generation.type == content_type)
                    elif content_type_str and content_type_str == required_content_type:
                        # Try to convert the string to enum
                        try:
                            content_type_enum = ContentType(required_content_type)
                            query = query.where(Generation.type == content_type_enum)
                        except (ValueError, TypeError):
                            # If conversion fails, compare as strings
                            query = query.where(Generation.type.cast(str) == required_content_type)

                result = await self.session.execute(query)
                count = result.scalar() or 0
                required_count = conditions.get('generation_count', 0)
                progress = min(100.0, (count / required_count) * 100 if required_count > 0 else 0)

            elif 'consecutive_days' in conditions:
                # Implementation for consecutive days achievement
                required_days = conditions.get('consecutive_days', 0)
                query = select(UserAction).where(
                    UserAction.user_id == user_id
                ).order_by(UserAction.created_at.desc())

                result = await self.session.execute(query)
                actions = result.scalars().all()

                # Calculate consecutive days (simplified example)
                days_active = set()
                for action in actions:
                    action_date = action.created_at.date()
                    days_active.add(action_date)

                # Check consecutive days (very simplified, would need more complex logic in real app)
                if len(days_active) >= required_days:
                    progress = 100.0
                else:
                    progress = (len(days_active) / required_days) * 100

            elif 'invites_count' in conditions:
                # Implementation for invites achievement
                required_invites = conditions.get('invites_count', 0)
                query = select(User.invites_count).where(User.id == user_id)
                result = await self.session.execute(query)
                current_invites = result.scalar() or 0

                progress = min(100.0, (current_invites / required_invites) * 100 if required_invites > 0 else 0)

            # Add other achievement types here as needed

            return progress

        except Exception as e:
            logger.error(f"Error checking achievement conditions: {str(e)}")
            return 0.0

    async def _batch_update_achievements(self, achievements: List[Dict]) -> None:
        """Батч-обновление достижений пользователя"""
        try:
            async with self.session.begin_nested():
                for achievement_data in achievements:
                    user_achievement = await self._get_user_achievement(
                        achievement_data['user_id'],
                        achievement_data['achievement_id']
                    )

                    if user_achievement:
                        user_achievement.progress = achievement_data['progress']
                        user_achievement.unlocked = achievement_data['unlocked']
                        if achievement_data['unlocked'] and not user_achievement.unlocked_at:
                            user_achievement.unlocked_at = datetime.utcnow()
                        user_achievement.last_updated = datetime.utcnow()
                    else:
                        user_achievement = UserAchievement(
                            user_id=achievement_data['user_id'],
                            achievement_id=achievement_data['achievement_id'],
                            progress=achievement_data['progress'],
                            unlocked=achievement_data['unlocked'],
                            unlocked_at=datetime.utcnow() if achievement_data['unlocked'] else None,
                            last_updated=datetime.utcnow()
                        )
                        self.session.add(user_achievement)

                await self.session.flush()
        except Exception as e:
            logger.error(f"Error batch updating achievements: {str(e)}")
            raise

    async def _get_user_achievement(
            self,
            user_id: int,
            achievement_id: int
    ) -> Optional[UserAchievement]:
        """Получает запись о достижении пользователя"""
        try:
            query = select(UserAchievement).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement_id
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user achievement: {str(e)}")
            raise

    async def _get_available_achievements(self) -> List[Achievement]:
        """Получает доступные достижения с оптимизацией запроса"""
        try:
            # Проверяем кэш
            cache_key = "available_achievements"
            cached_achievements = await self.cache_service.get_cached_data(cache_key)
            if cached_achievements:
                return cached_achievements

            # Оптимизированный запрос через QueryOptimizer
            query = await self.query_optimizer.optimize_query(
                select(Achievement)
            )
            result = await self.session.execute(query)
            achievements = result.scalars().all()

            # Кэшируем результат
            await self.cache_service.cache_data(cache_key, achievements, ttl=3600)

            return achievements
        except Exception as e:
            logger.error(f"Error getting available achievements: {str(e)}")
            raise

    async def get_user_achievements_progress(
            self,
            user_id: int
    ) -> AchievementProgress:
        """Получение оптимизированного прогресса достижений пользователя"""
        try:
            # Проверяем кэш
            cache_key = f"achievements_progress:{user_id}"
            cached_progress = await self.cache_service.get_cached_data(cache_key)
            if cached_progress:
                return AchievementProgress(**cached_progress)

            # Оптимизированные запросы через QueryOptimizer
            total_query = select(func.count(Achievement.id))
            unlocked_query = select(
                func.count(UserAchievement.id)
            ).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.unlocked == True
                )
            )

            # Выполняем запросы асинхронно
            total, unlocked = await asyncio.gather(
                self.session.scalar(total_query),
                self.session.scalar(unlocked_query)
            )

            # Получаем дополнительные данные параллельно
            next_achievements, recent_unlocks, total_points = await asyncio.gather(
                self._get_next_achievements(user_id),
                self._get_recent_unlocks(user_id),
                self._calculate_total_points_earned(user_id)
            )

            progress = AchievementProgress(
                total_achievements=total,
                unlocked_achievements=unlocked,
                total_points_earned=total_points,
                next_achievements=next_achievements,
                recent_unlocks=recent_unlocks
            )

            # Кэшируем результат
            await self.cache_service.cache_data(
                cache_key,
                progress.dict(),
                ttl=300  # 5 минут
            )

            return progress

        except Exception as e:
            logger.error(f"Error getting achievements progress: {str(e)}")
            raise

    async def _get_next_achievements(
            self,
            user_id: int,
            limit: int = 5
    ) -> List[AchievementResponse]:
        """Получение следующих доступных достижений с оптимизацией"""
        try:
            # Оптимизированный запрос через QueryOptimizer
            unlocked_achievements_subquery = (
                select(UserAchievement.achievement_id)
                .where(
                    and_(
                        UserAchievement.user_id == user_id,
                        UserAchievement.unlocked == True
                    )
                )
                .scalar_subquery()
            )

            query = await self.query_optimizer.optimize_query(
                select(Achievement)
                .where(Achievement.id.notin_(unlocked_achievements_subquery))
                .order_by(Achievement.points_reward.desc())
                .limit(limit)
            )

            result = await self.session.execute(query)
            achievements = result.scalars().all()

            return [AchievementResponse.from_orm(ach) for ach in achievements]

        except Exception as e:
            logger.error(f"Error getting next achievements: {str(e)}")
            raise

    async def _get_recent_unlocks(
            self,
            user_id: int,
            limit: int = 5
    ) -> List[UserAchievementResponse]:
        """Получение недавно разблокированных достижений с оптимизацией"""
        try:
            # Оптимизированный запрос через QueryOptimizer
            query = await self.query_optimizer.optimize_query(
                select(UserAchievement)
                .options(selectinload(UserAchievement.achievement))
                .where(
                    and_(
                        UserAchievement.user_id == user_id,
                        UserAchievement.unlocked == True
                    )
                )
                .order_by(UserAchievement.unlocked_at.desc())
                .limit(limit)
            )

            result = await self.session.execute(query)
            recent_unlocks = result.scalars().all()

            return [UserAchievementResponse.from_orm(ua) for ua in recent_unlocks]

        except Exception as e:
            logger.error(f"Error getting recent unlocks: {str(e)}")
            raise

    async def _calculate_total_points_earned(self, user_id: int) -> int:
        """Подсчет заработанных очков с оптимизацией"""
        try:
            # Оптимизированный запрос через QueryOptimizer
            query = await self.query_optimizer.optimize_query(
                select(func.sum(PointTransaction.amount))
                .where(
                    and_(
                        PointTransaction.user_id == user_id,
                        PointTransaction.transaction_type == 'achievement_reward'
                    )
                )
            )
            result = await self.session.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Error calculating total points: {str(e)}")
            return 0

    async def _load_user_achievements(self, user_id: int) -> Dict[int, Dict[str, Any]]:
        """Загрузка достижений пользователя с оптимизацией"""
        try:
            query = await self.query_optimizer.optimize_query(
                select(UserAchievement)
                .where(UserAchievement.user_id == user_id)
            )
            result = await self.session.execute(query)
            user_achievements = result.scalars().all()

            return {
                ach.achievement_id: {
                    'unlocked': ach.unlocked,
                    'progress': ach.progress,
                    'unlocked_at': ach.unlocked_at,
                    'last_updated': ach.last_updated
                }
                for ach in user_achievements
            }

        except Exception as e:
            logger.error(f"Error loading user achievements: {str(e)}")
            raise

    async def create_achievement(self, achievement_data: dict) -> Achievement:
        """Создает новое достижение"""
        try:
            achievement = Achievement(**achievement_data)
            self.session.add(achievement)
            await self.session.flush()

            # Инвалидируем кэш доступных достижений
            await self.cache_service.invalidate_pattern("available_achievements")

            return achievement
        except Exception as e:
            logger.error(f"Error creating achievement: {str(e)}")
            raise

    async def update_achievement(self, achievement_id: int, achievement_data: dict) -> Optional[Achievement]:
        """Обновляет существующее достижение"""
        try:
            achievement = await self.session.get(Achievement, achievement_id)
            if not achievement:
                return None

            for key, value in achievement_data.items():
                if hasattr(achievement, key):
                    setattr(achievement, key, value)

            await self.session.flush()

            # Инвалидируем кэш доступных достижений
            await self.cache_service.invalidate_pattern("available_achievements")

            return achievement
        except Exception as e:
            logger.error(f"Error updating achievement: {str(e)}")
            raise

    async def delete_achievement(self, achievement_id: int) -> bool:
        """Удаляет достижение"""
        try:
            achievement = await self.session.get(Achievement, achievement_id)
            if not achievement:
                return False

            await self.session.delete(achievement)
            await self.session.flush()

            # Инвалидируем кэш
            await self.cache_service.invalidate_pattern("available_achievements")
            await self.cache_service.invalidate_pattern("achievements_progress:*")

            return True
        except Exception as e:
            logger.error(f"Error deleting achievement: {str(e)}")
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()