from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User
from ...schemas.tracking import AppUsageEvent
import logging

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/app-usage")
async def track_app_usage(
    event_data: AppUsageEvent = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Отслеживание использования приложения"""
    try:
        # Логируем событие
        logger.info(f"App usage event: {event_data.dict()}")

        # Здесь можно добавить сохранение события в базу данных
        # Например, через специальный сервис

        return {"status": "success", "message": "Event tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking app usage: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error tracking app usage: {str(e)}"
        )

@router.get("/app-usage/stats")
async def get_app_usage_stats(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение статистики использования приложения"""
    # Проверяем, что пользователь имеет права администратора
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )

    try:
        # Здесь можно добавить получение статистики из базы данных
        # Пока возвращаем заглушку
        return {
            "total_events": 0,
            "unique_users": 0,
            "events_by_type": {},
            "events_by_platform": {},
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting app usage stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting app usage stats: {str(e)}"
        )