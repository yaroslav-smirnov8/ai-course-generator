"""
API для проверки и управления лимитами генераций.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.tariff.limits_checker import LimitsChecker
from ...core.database import get_db
from ...core.security import get_current_user

router = APIRouter()

@router.get("/limits", name="limits:check-remaining", summary="Проверить оставшиеся лимиты генераций")
async def check_remaining_limits(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Проверяет, сколько генераций и других действий осталось у пользователя на текущий день.
    
    Returns:
        dict: Информация об оставшихся лимитах и их использовании
    """
    limits_checker = LimitsChecker(db)
    limits_info = await limits_checker.get_remaining_limits(current_user.id)
    
    return limits_info

@router.get("/limits/can-generate/{content_type}", name="limits:can-generate", summary="Проверить возможность генерации")
async def can_generate(
    content_type: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Проверяет, может ли пользователь сгенерировать контент указанного типа.
    
    Args:
        content_type: Тип контента (lesson_plan, exercise, game, image, etc.)
        
    Returns:
        dict: Результат проверки и причина отказа, если есть
    """
    limits_checker = LimitsChecker(db)
    can_gen, reason = await limits_checker.can_generate(
        user_id=current_user.id,
        content_type=content_type,
        check_only=True
    )
    
    return {
        "can_generate": can_gen,
        "reason": reason
    }

@router.post("/limits/track/{content_type}", name="limits:track-usage", summary="Отметить использование лимита")
async def track_usage(
    content_type: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Отмечает использование лимита генерации указанного типа контента.
    
    Args:
        content_type: Тип контента (lesson_plan, exercise, game, image, etc.)
        
    Returns:
        dict: Результат операции
    """
    limits_checker = LimitsChecker(db)
    
    # Сначала проверяем, можно ли выполнить генерацию
    can_gen, reason = await limits_checker.can_generate(
        user_id=current_user.id,
        content_type=content_type
    )
    
    if not can_gen:
        raise HTTPException(status_code=403, detail=reason)
    
    # Обновляем счетчик использования
    success = await limits_checker.update_usage_counter(
        user_id=current_user.id,
        content_type=content_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось обновить счетчик использования")
    
    # Получаем обновленные лимиты
    limits_info = await limits_checker.get_remaining_limits(current_user.id)
    
    return {
        "success": True,
        "message": f"Использование типа '{content_type}' успешно учтено",
        "remaining_limits": limits_info
    } 