# app/api/v1/tariffs.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...core.database import get_db
from ...services.tariff.manager import TariffManager
from ...schemas.pricing import TariffInfo
from ...core.security import get_current_user
from ...models.user import User

# Create a new router just for the general tariffs endpoints
router = APIRouter()

@router.get("", response_model=List[TariffInfo])
async def get_available_tariffs(
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список доступных тарифов"""
    async with TariffManager(session) as tariff_manager:
        tariffs = await tariff_manager.get_available_tariffs()
        return tariffs