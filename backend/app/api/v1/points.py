# app/api/v1/points.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_user
from ...services.points import PointsManager
from ...schemas.points import (
    PointTransactionCreate,
    PointTransactionResponse,
    PointBalanceResponse,
    TransactionType
)
from ...models.user import User

router = APIRouter(tags=["points"])

@router.get("/balance", response_model=PointBalanceResponse)
async def get_balance(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить текущий баланс баллов пользователя"""
    async with PointsManager(session) as points_manager:
        balance = await points_manager.get_balance(current_user.id)
        return {
            "points": balance,
            "user_id": current_user.id,
            "last_updated": datetime.now().replace(tzinfo=None)
        }

@router.post("/deduct", response_model=PointTransactionResponse)
async def deduct_points(
    transaction: PointTransactionCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Списание баллов"""
    async with PointsManager(session) as points_manager:
        # Проверяем достаточно ли баллов
        if not await points_manager.check_sufficient_balance(
            current_user.id,
            transaction.amount
        ):
            raise HTTPException(
                status_code=400,
                detail="Insufficient points balance"
            )

        result = await points_manager.deduct_points(
            user_id=current_user.id,
            amount=transaction.amount,
            transaction_type=transaction.type,
            description=transaction.description
        )
        return result

@router.post("/add", response_model=PointTransactionResponse)
async def add_points(
    transaction: PointTransactionCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Начисление баллов"""
    async with PointsManager(session) as points_manager:
        result = await points_manager.add_points(
            user_id=current_user.id,
            amount=transaction.amount,
            transaction_type=transaction.type,
            description=transaction.description
        )
        return result

@router.get("/transactions", response_model=List[PointTransactionResponse])
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить историю транзакций с пагинацией и фильтрацией"""
    async with PointsManager(session) as points_manager:
        transactions = await points_manager.get_transactions(
            user_id=current_user.id,
            page=page,
            limit=limit,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        return transactions

@router.post("/refund", response_model=PointTransactionResponse)
async def refund_points(
    transaction: PointTransactionCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Возврат баллов (например, при ошибке генерации)"""
    async with PointsManager(session) as points_manager:
        result = await points_manager.refund_points(
            user_id=current_user.id,
            amount=transaction.amount,
            original_transaction_type=transaction.type,
            description=transaction.description
        )
        return result