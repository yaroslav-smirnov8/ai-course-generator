import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...core.database import get_db
from ...core.security import get_current_admin_user, get_current_user
from ...services.achievements.manager import AchievementManager
from ...schemas.achievements import (
    AchievementResponse,
    UserAchievementResponse,
    AchievementCreate,
    AchievementUpdate,
    AchievementCheckRequest,
    AchievementAnalyticsResponse
)
from ...models.user import User
from ...models.achievements import Achievement, UserAchievement
from ...core.constants import ActionType

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/achievements")
async def get_achievements(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список всех достижений"""
    try:
        # Создаем экземпляр AchievementManager
        from ...services.analytics.feature_usage import AchievementManager
        achievement_manager = AchievementManager()

        # Получаем список достижений
        achievements = await achievement_manager.get_available_achievements(current_user.id)

        return achievements
    except Exception as e:
        logger.error(f"Error getting achievements: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting achievements: {str(e)}"
        )


@router.get("/achievements/user/{user_id}", response_model=List[UserAchievementResponse])
async def get_user_achievements(
        user_id: int,
        session: AsyncSession = Depends(get_db)
):
    """Получить достижения конкретного пользователя"""
    try:
        manager = AchievementManager(session)
        achievements = await manager.get_user_achievements(user_id)
        return achievements
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting user achievements: {str(e)}"
        )


@router.post("/achievements/check")
async def check_achievement(
        request: AchievementCheckRequest,
        session: AsyncSession = Depends(get_db)
):
    """Проверить достижения после действия пользователя"""
    try:
        # Convert string to enum if needed
        action_type_enum = None
        try:
            action_type_enum = ActionType(request.action_type)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid action_type: {request.action_type}. Error: {str(e)}")
            # Fall back to treating it as a string
            action_type_enum = request.action_type

        manager = AchievementManager(session)
        await manager.check_achievements(
            request.user_id,
            action_type_enum,
            request.action_data
        )
        await session.commit()

        return {
            "status": "success",
            "message": "Achievements checked successfully"
        }
    except Exception as e:
        await session.rollback()
        logger.error(f"Error checking achievements: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Error checking achievements: {str(e)}"
        )


@router.post("/admin/achievements", response_model=AchievementResponse)
async def create_achievement(
        achievement: AchievementCreate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Создать новое достижение (только для админов)"""
    try:
        manager = AchievementManager(session)
        new_achievement = await manager.create_achievement(achievement)
        await session.commit()
        return new_achievement
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating achievement: {str(e)}"
        )


@router.put("/admin/achievements/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(
        achievement_id: int,
        achievement_data: AchievementUpdate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Обновить достижение (только для админов)"""
    try:
        manager = AchievementManager(session)
        updated_achievement = await manager.update_achievement(achievement_id, achievement_data)
        if not updated_achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")
        await session.commit()
        return updated_achievement
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error updating achievement: {str(e)}"
        )


@router.delete("/admin/achievements/{achievement_id}")
async def delete_achievement(
        achievement_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Удалить достижение (только для админов)"""
    try:
        manager = AchievementManager(session)
        result = await manager.delete_achievement(achievement_id)
        if not result:
            raise HTTPException(status_code=404, detail="Achievement not found")
        await session.commit()

        return {
            "status": "success",
            "message": "Achievement deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error deleting achievement: {str(e)}"
        )


@router.get("/admin/analytics/achievements", response_model=AchievementAnalyticsResponse)
async def get_achievements_analytics(
    period: str = Query("week", description="Период анализа: week, month, year, all"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить аналитику по достижениям (только для админов)"""
    try:
        # Определяем временной интервал на основе выбранного периода
        now = datetime.now(datetime.timezone.utc)

        # 1. Получаем общее количество достижений
        total_achievements_query = select(func.count(Achievement.id))
        total_achievements = await session.scalar(total_achievements_query)

        # 2. Получаем количество разблокированных достижений
        unlocked_achievements_query = select(func.count(UserAchievement.id)).where(
            UserAchievement.unlocked == True
        )
        unlocked_achievements = await session.scalar(unlocked_achievements_query)

        # 3. Получаем общее количество заработанных баллов
        total_points_query = select(
            func.sum(Achievement.points_reward)
        ).select_from(
            UserAchievement
        ).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).where(
            UserAchievement.unlocked == True
        )
        total_points = await session.scalar(total_points_query) or 0

        # 4. Получаем количество активных пользователей (тех, кто разблокировал хотя бы одно достижение)
        active_users_query = select(
            func.count(func.distinct(UserAchievement.user_id))
        ).where(
            UserAchievement.unlocked == True
        )
        active_users = await session.scalar(active_users_query) or 0

        # 5. Получаем популярные достижения (топ-5 по количеству разблокировок)
        popular_achievements_query = select(
            Achievement.id,
            Achievement.name,
            Achievement.description,
            Achievement.icon,
            Achievement.points_reward,
            func.count(UserAchievement.id).label("unlock_count")
        ).join(
            UserAchievement, Achievement.id == UserAchievement.achievement_id
        ).where(
            UserAchievement.unlocked == True
        ).group_by(
            Achievement.id
        ).order_by(
            desc("unlock_count")
        ).limit(5)

        popular_achievements_result = await session.execute(popular_achievements_query)
        popular_achievements = [
            {
                "achievement_id": row.id,
                "name": row.name,
                "description": row.description,
                "icon": row.icon,
                "points_reward": row.points_reward,
                "unlock_count": row.unlock_count
            }
            for row in popular_achievements_result
        ]

        # 6. Получаем данные о разблокировке достижений по дням
        # Определяем количество дней для группировки
        days_count = 7 if period == "week" else 30 if period == "month" else 365 if period == "year" else 30

        # Создаем список дат для графика
        unlocks_over_time = []
        for i in range(days_count):
            date = now - timedelta(days=days_count - i - 1)
            date_str = date.strftime("%Y-%m-%d")

            # Получаем количество разблокировок за этот день
            day_start = datetime(date.year, date.month, date.day, 0, 0, 0)
            day_end = datetime(date.year, date.month, date.day, 23, 59, 59)

            unlocks_count_query = select(
                func.count(UserAchievement.id)
            ).where(
                and_(
                    UserAchievement.unlocked == True,
                    UserAchievement.unlocked_at >= day_start,
                    UserAchievement.unlocked_at <= day_end
                )
            )

            unlocks_count = await session.scalar(unlocks_count_query) or 0

            unlocks_over_time.append({
                "date": date_str,
                "count": unlocks_count
            })

        # Формируем ответ
        return {
            "total_achievements": total_achievements,
            "unlocked_achievements": unlocked_achievements,
            "total_points_earned": total_points,
            "active_users": active_users,
            "popular_achievements": popular_achievements,
            "unlocks_over_time": unlocks_over_time,
            "period": period
        }
    except Exception as e:
        logger.error(f"Error getting achievements analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting achievements analytics: {str(e)}"
        )