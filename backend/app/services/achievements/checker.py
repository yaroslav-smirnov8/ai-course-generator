from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from ...models import Achievement, UserAchievement, UserAction, Generation, Image, User
from ...core.constants import ActionType, ContentType
import logging

logger = logging.getLogger(__name__)


class AchievementChecker:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_achievement_conditions(
            self,
            achievement: Achievement,
            user_id: int
    ) -> float:
        """Проверяет прогресс достижения по условиям"""
        try:
            conditions = achievement.conditions
            progress = 0.0

            # Проверяем по типу достижения
            if 'generation_count' in conditions:
                progress = await self._check_generation_count(user_id, conditions)
            elif 'image_count' in conditions:
                progress = await self._check_image_count(user_id, conditions)
            elif 'consecutive_days' in conditions:
                progress = await self._check_consecutive_days(user_id, conditions)
            elif 'invites_count' in conditions:
                progress = await self._check_invites_count(user_id, conditions)

            return min(progress, 100.0)

        except Exception as e:
            logger.error(f"Error checking achievement conditions: {str(e)}")
            return 0.0

    async def _check_generation_count(self, user_id: int, conditions: Dict) -> float:
        """Проверяет достижения, связанные с генерациями"""
        try:
            required_count = conditions.get('generation_count', 0)
            content_type = conditions.get('content_type')

            query = select(func.count()).select_from(Generation).where(
                Generation.user_id == user_id
            )

            if content_type:
                query = query.where(Generation.type == content_type)

            result = await self.session.execute(query)
            current_count = result.scalar() or 0
            return (current_count / required_count) * 100 if required_count > 0 else 0

        except Exception as e:
            logger.error(f"Error checking generation count: {str(e)}")
            return 0.0

    async def _check_image_count(self, user_id: int, conditions: Dict) -> float:
        """Проверяет достижения, связанные с изображениями"""
        try:
            required_count = conditions.get('image_count', 0)

            query = select(func.count()).select_from(Image).where(
                Image.user_id == user_id
            )

            result = await self.session.execute(query)
            current_count = result.scalar() or 0

            return (current_count / required_count) * 100 if required_count > 0 else 0

        except Exception as e:
            logger.error(f"Error checking image count: {str(e)}")
            return 0.0

    async def _check_consecutive_days(self, user_id: int, conditions: Dict) -> float:
        """Проверяет достижения за последовательные дни активности"""
        try:
            required_days = conditions.get('consecutive_days', 0)

            # Запрос для проверки активности по дням
            query = select(UserAction).where(
                UserAction.user_id == user_id
            ).order_by(UserAction.created_at.desc())

            # TODO: Реализовать логику проверки последовательных дней
            # Пример базовой структуры:
            result = await self.session.execute(query)
            actions = result.scalars().all()

            # Здесь должна быть логика подсчета последовательных дней
            return 0.0

        except Exception as e:
            logger.error(f"Error checking consecutive days: {str(e)}")
            return 0.0

    async def _check_invites_count(self, user_id: int, conditions: Dict) -> float:
        """Проверяет достижения, связанные с приглашениями"""
        try:
            required_count = conditions.get('invites_count', 0)

            # Предполагая, что у нас есть поле invites_count в модели User
            query = select(User.invites_count).where(User.id == user_id)
            result = await self.session.execute(query)
            current_invites = result.scalar() or 0

            # TODO: Реализовать полную проверку системы приглашений
            return (current_invites / required_count) * 100 if required_count > 0 else 0

        except Exception as e:
            logger.error(f"Error checking invites count: {str(e)}")
            return 0.0