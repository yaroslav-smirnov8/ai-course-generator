# app/api/v1/tariff.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from datetime import datetime, timezone
from ...models import DailyUsage

logger = logging.getLogger(__name__)

from ...core.database import get_db
from ...services.tariff.manager import TariffManager
from ...schemas.pricing import (
    TariffInfo,
    UserTariffHistory,
    TariffExtension,
    TariffUpdate as UserTariffUpdate,
    TariffResponse
)
from ...core.security import get_current_user
from ...models.user import User

router = APIRouter()


@router.get("/{user_id}/tariff", response_model=TariffInfo)
async def get_user_tariff(
        user_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить информацию о текущем тарифе пользователя"""
    # Проверяем, что текущий пользователь запрашивает свой тариф или является администратором
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    async with TariffManager(session) as tariff_manager:
        tariff_info = await tariff_manager.get_tariff_info(user_id)
        if not tariff_info:
            logger.warning(f"Tariff info not found for user {user_id}, returning basic tariff")
            # Возвращаем базовый тариф вместо ошибки
            from ...core.constants import TariffType
            from ...schemas.pricing import TariffInfo
            tariff_info = TariffInfo(
                type=TariffType.BASIC,
                validUntil=None,
                limits={
                    "generations": 6,
                    "images": 2
                },
                pricePoints=400,  # Цена в рублях для совместимости
                features={},
                name="Базовый"
            )
        # Добавлено детальное логирование возвращаемых данных
        logger.info(f"Returning tariff info for user {user_id}: {tariff_info.dict() if hasattr(tariff_info, 'dict') else tariff_info}")
        return tariff_info


@router.post("/{user_id}/tariff", response_model=TariffResponse)
async def update_user_tariff(
        tariff_update: UserTariffUpdate,
        user_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить тариф пользователя"""
    logger.info(f"Updating tariff for user {user_id} to {tariff_update.tariff_type}")

    # Проверяем, что текущий пользователь обновляет свой тариф или является администратором
    if current_user.id != user_id and current_user.role != "admin":
        logger.warning(f"Permission denied: User {current_user.id} tried to update tariff for user {user_id}")
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    async with TariffManager(session) as tariff_manager:
        try:
            # Получаем текущую статистику использования перед обновлением тарифа
            try:
                # Получаем текущую запись дневного использования
                today = datetime.now(timezone.utc).date()
                daily_usage_query = select(DailyUsage).where(
                    and_(
                        DailyUsage.user_id == user_id,
                        DailyUsage.date == today
                    )
                )
                daily_usage_result = await session.execute(daily_usage_query)
                daily_usage_before = daily_usage_result.scalar_one_or_none()

                if daily_usage_before:
                    logger.info(f"Current daily usage before tariff update: user_id={user_id}, "
                               f"generations={daily_usage_before.generations_count}, "
                               f"images={daily_usage_before.images_count}")
                else:
                    logger.info(f"No daily usage record found for user {user_id} before tariff update")
            except Exception as e:
                logger.warning(f"Error getting daily usage before tariff update: {str(e)}")

            # Обновляем тариф
            logger.info(f"Calling purchase_tariff for user {user_id} with tariff {tariff_update.tariff_type}")
            result = await tariff_manager.purchase_tariff(
                user_id=user_id,
                tariff_type=tariff_update.tariff_type
            )

            if not result:
                logger.warning(f"Failed to purchase tariff {tariff_update.tariff_type} for user {user_id}")
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось приобрести тариф. Проверьте баланс баллов."
                )

            # Получаем статистику использования после обновления тарифа
            try:
                # Получаем текущую запись дневного использования
                daily_usage_query = select(DailyUsage).where(
                    and_(
                        DailyUsage.user_id == user_id,
                        DailyUsage.date == today
                    )
                )
                daily_usage_result = await session.execute(daily_usage_query)
                daily_usage_after = daily_usage_result.scalar_one_or_none()

                if daily_usage_after:
                    logger.info(f"Daily usage after tariff update: user_id={user_id}, "
                               f"generations={daily_usage_after.generations_count}, "
                               f"images={daily_usage_after.images_count}")
                else:
                    logger.info(f"No daily usage record found for user {user_id} after tariff update")
            except Exception as e:
                logger.warning(f"Error getting daily usage after tariff update: {str(e)}")

            # Получаем информацию о тарифе
            tariff_info = await tariff_manager.get_tariff_info(user_id)
            logger.info(f"Tariff updated successfully for user {user_id}. New tariff info: {tariff_info}")

            return {
                "status": "success",
                "message": "Тариф успешно обновлен",
                "data": tariff_info
            }

        except ValueError as e:
            # Handle validation errors like downgrade attempt
            logger.warning(f"Validation error updating tariff for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except HTTPException as e:
            # Re-raise HTTP exceptions without changing the status code
            logger.warning(f"HTTP exception updating tariff for user {user_id}: {str(e)}")
            raise e
        except Exception as e:
            # For other exceptions, raise a 500 error
            logger.error(f"Error updating tariff for user {user_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обновлении тарифа: {str(e)}"
            )


@router.get("/{user_id}/tariff/history", response_model=List[UserTariffHistory])
async def get_tariff_history(
        user_id: int = Path(..., ge=1),
        limit: int = Query(10, ge=1, le=100),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить историю тарифов пользователя"""
    # Проверяем, что текущий пользователь запрашивает свою историю или является администратором
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    async with TariffManager(session) as tariff_manager:
        history = await tariff_manager.get_tariff_history(user_id, limit)
        return history


@router.get("/{user_id}/tariff/check")
async def check_tariff_validity(
        user_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Проверить активность тарифа пользователя"""
    # Проверяем, что текущий пользователь запрашивает свой тариф или является администратором
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    async with TariffManager(session) as tariff_manager:
        is_valid = await tariff_manager.check_tariff_validity(user_id)
        return {"is_valid": is_valid}


@router.post("/{user_id}/tariff/extend", response_model=TariffResponse)
async def extend_tariff(
        extension: TariffExtension,
        user_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Продлить текущий тариф пользователя"""
    # Проверяем, что текущий пользователь продлевает свой тариф или является администратором
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    async with TariffManager(session) as tariff_manager:
        try:
            # Проверяем, есть ли у пользователя активный тариф
            tariff_info = await tariff_manager.get_tariff_info(user_id)
            if not tariff_info:
                raise HTTPException(
                    status_code=400,
                    detail="Нет активного тарифа для продления"
                )

            # Продлеваем тариф
            result = await tariff_manager.extend_tariff(
                user_id=user_id,
                months=extension.months
            )

            if not result:
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось продлить тариф. Проверьте баланс баллов."
                )

            # Получаем обновленную информацию о тарифе
            updated_tariff = await tariff_manager.get_tariff_info(user_id)
            return {
                "status": "success",
                "message": f"Тариф успешно продлен на {extension.months} месяц(ев)",
                "data": updated_tariff
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при продлении тарифа: {str(e)}"
            )
