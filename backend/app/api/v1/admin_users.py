"""
API endpoints для управления пользователями (админ панель)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.user import User
from app.models.point_transaction import PointTransaction
from app.core.security import get_current_admin_user
from app.schemas.user import UserUpdate, UserInDB
from app.core.enums import TransactionType

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить данные пользователя"""

    # Получаем пользователя
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Обновляем данные
    update_data = user_data.model_dump(exclude_unset=True)
    if update_data:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(user)

    return user


from pydantic import BaseModel

class PointsChangeRequest(BaseModel):
    points_change: int

@router.post("/{user_id}/points")
async def update_user_points(
    user_id: int,
    request: PointsChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Изменить баллы пользователя"""

    # Получаем пользователя
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    points_change = request.points_change

    # Проверяем, что баллы не станут отрицательными
    new_points = user.points + points_change
    if new_points < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно баллов для списания"
        )

    # Обновляем баллы
    user.points = new_points

    # Создаем транзакцию
    transaction = PointTransaction(
        user_id=user_id,
        amount=points_change,  # Используем исходное значение (может быть отрицательным)
        transaction_type=TransactionType.ADMIN_ADD if points_change > 0 else TransactionType.ADMIN_SUBTRACT,
        description=f"Изменение баллов администратором (ID: {current_user.id})",
        created_at=datetime.now(timezone.utc)
    )

    db.add(transaction)
    await db.commit()

    return {
        "success": True,
        "new_points": user.points,
        "change": points_change
    }


@router.get("/{user_id}/payments")
async def get_user_payments(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить историю платежей пользователя"""

    # Проверяем существование пользователя
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # TODO: Реализовать получение платежей из таблицы payments
    # Пока возвращаем заглушку
    return [
        {
            "id": 1,
            "amount": 299,
            "status": "completed",
            "type": "tariff",
            "description": "Стандарт тариф",
            "external_id": "pay_123456",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": 2,
            "amount": 100,
            "status": "completed",
            "type": "points",
            "description": "100 баллов",
            "external_id": "pay_789012",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]


class MessageRequest(BaseModel):
    message: str

@router.post("/{user_id}/message")
async def send_user_message(
    user_id: int,
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Отправить сообщение пользователю через Telegram"""

    # Проверяем существование пользователя
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # TODO: Реализовать отправку сообщения через Telegram бота
    # Пока просто логируем
    print(f"Sending message to user {user_id} (telegram_id: {user.telegram_id}): {request.message}")

    return {
        "success": True,
        "message": "Сообщение будет отправлено через Telegram бота"
    }
