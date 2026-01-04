# app/api/v1/pricing.py - обновленная версия
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ...core.database import get_db
from ...services.pricing.manager import PricingManager
from ...services.tariff.manager import TariffManager  # Добавляем новый менеджер
from ...schemas.pricing import (
    TariffCreate,
    TariffUpdate,
    TariffResponse,
    PriceChangeCreate,
    PriceChangeResponse
)
from ...schemas.pricing import (  # Импортируем новые схемы
    TariffInfo,
    UserTariffHistory,
    TariffExtension,
    TariffUpdate as UserTariffUpdate
)
from ...core.security import get_current_user, get_current_admin_user
from ...models.user import User

router = APIRouter()


# --- Существующие административные эндпоинты ---

@router.post("/admin/tariffs", response_model=TariffResponse)
async def create_tariff(
        tariff: TariffCreate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Создать новый тариф (только для админов)"""
    async with PricingManager(session) as manager:
        try:
            return await manager.create_tariff(tariff)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error creating tariff: {str(e)}"
            )


@router.put("/admin/tariffs/{tariff_id}", response_model=TariffResponse)
async def update_tariff(
        tariff_id: int,
        tariff: TariffUpdate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Обновить существующий тариф (только для админов)"""
    async with PricingManager(session) as manager:
        try:
            updated = await manager.update_tariff(tariff_id, tariff)
            if not updated:
                raise HTTPException(
                    status_code=404,
                    detail="Tariff not found"
                )
            return updated
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error updating tariff: {str(e)}"
            )


@router.post("/admin/price-changes", response_model=PriceChangeResponse)
async def schedule_price_change(
        change: PriceChangeCreate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Запланировать изменение цены (только для админов)"""
    async with PricingManager(session) as manager:
        try:
            return await manager.schedule_price_change(change)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error scheduling price change: {str(e)}"
            )


@router.get("/admin/tariffs/{tariff_id}/price-history", response_model=List[PriceChangeResponse])
async def get_price_history(
        tariff_id: int,
        from_date: Optional[datetime] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Получить историю изменения цен тарифа (только для админов)"""
    async with PricingManager(session) as manager:
        try:
            history = await manager.get_price_history(tariff_id, from_date)
            if not history and not await manager.tariff_exists(tariff_id):
                raise HTTPException(
                    status_code=404,
                    detail="Tariff not found"
                )
            return history
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting price history: {str(e)}"
            )


