# app/api/v1/points_purchase.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_user
from ...services.points.purchase_manager import PointsPurchaseManager
from ...schemas.points_purchase import (
    PurchaseRequest,
    PurchaseResponse,
    PurchaseConfirmation,
    PurchaseHistory,
    PaymentMethod,
    PurchaseStatus
)
from ...models.user import User

router = APIRouter(prefix="/points/purchase", tags=["points_purchase"])

@router.post("/init", response_model=PurchaseResponse)
async def initialize_purchase(
    request: PurchaseRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Инициализация покупки баллов"""
    async with PointsPurchaseManager(session) as manager:
        try:
            # Проверяем валидность запроса
            if request.amount <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Amount must be positive"
                )

            # Инициализируем покупку
            result = await manager.initialize_purchase(
                user_id=current_user.id,
                amount=request.amount,
                price=request.price,
                bonus=request.bonus,
                payment_method=request.payment_method
            )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize purchase: {str(e)}"
            )

@router.post("/confirm", response_model=PurchaseResponse)
async def confirm_purchase(
    confirmation: PurchaseConfirmation,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Подтверждение покупки баллов"""
    async with PointsPurchaseManager(session) as manager:
        try:
            result = await manager.confirm_purchase(
                payment_id=confirmation.payment_id,
                user_id=current_user.id
            )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to confirm purchase: {str(e)}"
            )

@router.post("/cancel")
async def cancel_purchase(
    payment_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отмена покупки баллов"""
    async with PointsPurchaseManager(session) as manager:
        try:
            await manager.cancel_purchase(
                payment_id=payment_id,
                user_id=current_user.id
            )
            return {"status": "cancelled"}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel purchase: {str(e)}"
            )

@router.get("/history", response_model=List[PurchaseHistory])
async def get_purchase_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[PurchaseStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение истории покупок баллов"""
    async with PointsPurchaseManager(session) as manager:
        try:
            history = await manager.get_purchase_history(
                user_id=current_user.id,
                page=page,
                limit=limit,
                status=status,
                start_date=start_date,
                end_date=end_date
            )
            return history

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get purchase history: {str(e)}"
            )

@router.get("/available-packages")
async def get_available_packages(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение доступных пакетов баллов"""
    async with PointsPurchaseManager(session) as manager:
        try:
            packages = await manager.get_available_packages(current_user.id)
            return packages

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get available packages: {str(e)}"
            )

@router.post("/webhook/telegram")
async def telegram_payment_webhook(
    payment_data: dict,
    session: AsyncSession = Depends(get_db)
):
    """Webhook для обработки уведомлений об оплате от Telegram"""
    async with PointsPurchaseManager(session) as manager:
        try:
            await manager.process_telegram_webhook(payment_data)
            return {"status": "success"}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process payment webhook: {str(e)}"
            )