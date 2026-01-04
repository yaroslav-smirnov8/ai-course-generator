# app/services/rewards/manager.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, Dict, Any
from ...models import User, Achievement, UserAchievement
import logging

logger = logging.getLogger(__name__)


class RewardManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_achievement_reward(
            self,
            user_id: int,
            achievement_id: int
    ) -> Optional[int]:
        """Обрабатывает награду за достижение"""
        try:
            # Получаем пользователя
            user_query = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_query)
            user = user_result.scalar_one_or_none()

            # Получаем достижение
            achievement_query = select(Achievement).where(Achievement.id == achievement_id)
            achievement_result = await self.session.execute(achievement_query)
            achievement = achievement_result.scalar_one_or_none()

            if not user or not achievement:
                return None

            # Получаем достижение пользователя
            user_achievement_query = select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id
            )
            user_achievement_result = await self.session.execute(user_achievement_query)
            user_achievement = user_achievement_result.scalar_one_or_none()

            if not user_achievement or user_achievement.rewarded:
                return None

            # Начисляем награду
            reward_points = achievement.points_reward
            user.points += reward_points

            # Отмечаем награду как выданную
            user_achievement.rewarded = True
            user_achievement.rewarded_at = datetime.utcnow()

            await self.session.commit()
            return reward_points

        except Exception as e:
            logger.error(f"Error processing achievement reward: {str(e)}")
            await self.session.rollback()
            return None

    async def calculate_total_rewards(self, user_id: int) -> Dict[str, int]:
        """Подсчитывает общее количество наград пользователя"""
        try:
            # Получаем награжденные достижения пользователя
            achievements_query = select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.rewarded == True
            )
            achievements_result = await self.session.execute(achievements_query)
            user_achievements = achievements_result.scalars().all()

            achievements_count = len(user_achievements)
            total_points = 0

            if achievements_count > 0:
                # Получаем все связанные достижения одним запросом
                achievement_ids = [ua.achievement_id for ua in user_achievements]
                rewards_query = select(Achievement).where(
                    Achievement.id.in_(achievement_ids)
                )
                rewards_result = await self.session.execute(rewards_query)
                achievements = {
                    ach.id: ach.points_reward
                    for ach in rewards_result.scalars().all()
                }

                # Подсчитываем сумму наград
                total_points = sum(
                    achievements.get(ua.achievement_id, 0)
                    for ua in user_achievements
                )

            return {
                "total_points": total_points,
                "achievements_count": achievements_count
            }

        except Exception as e:
            logger.error(f"Error calculating total rewards: {str(e)}")
            return {"total_points": 0, "achievements_count": 0}

    async def get_user_rewards_summary(self, user_id: int) -> Dict[str, Any]:
        """Получает сводку по наградам пользователя"""
        try:
            # Получаем статистику одним запросом
            query = select(
                func.count(UserAchievement.id).label('total_achievements'),
                func.sum(Achievement.points_reward).label('total_points')
            ).join(
                Achievement,
                UserAchievement.achievement_id == Achievement.id
            ).where(
                UserAchievement.user_id == user_id,
                UserAchievement.rewarded == True
            )

            result = await self.session.execute(query)
            row = result.one()

            # Получаем последние награды
            recent_query = select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.rewarded == True
            ).order_by(
                UserAchievement.rewarded_at.desc()
            ).limit(5)

            recent_result = await self.session.execute(recent_query)
            recent_rewards = recent_result.scalars().all()

            return {
                "total_achievements": row.total_achievements or 0,
                "total_points": row.total_points or 0,
                "recent_rewards": [
                    {
                        "achievement_id": reward.achievement_id,
                        "rewarded_at": reward.rewarded_at
                    }
                    for reward in recent_rewards
                ]
            }

        except Exception as e:
            logger.error(f"Error getting user rewards summary: {str(e)}")
            return {
                "total_achievements": 0,
                "total_points": 0,
                "recent_rewards": []
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()