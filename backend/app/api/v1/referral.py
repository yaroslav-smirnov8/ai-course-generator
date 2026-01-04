# app/api/v1/referral.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User
from ...models.point_transaction import PointTransaction
from ...services.points.manager import PointsManager
from ...schemas.points import TransactionType
from typing import Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/link")
async def get_referral_link(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить реферальную ссылку пользователя"""
    try:
        # Если у пользователя нет инвайт-кода, генерируем его
        if not current_user.invite_code:
            # Генерируем уникальный код
            max_attempts = 5
            for attempt in range(max_attempts):
                invite_code = str(uuid.uuid4())[:8]

                # Проверяем уникальность
                result = await session.execute(
                    select(User).where(User.invite_code == invite_code)
                )
                if not result.scalar_one_or_none():
                    current_user.invite_code = invite_code
                    await session.commit()
                    break
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate unique invite code"
                )

        # Формируем ссылку (можно настроить домен в конфиге)
        base_url = "https://t.me/neuro_teacher_bot?start="
        referral_link = f"{base_url}{current_user.invite_code}"

        return {
            "link": referral_link,
            "invite_code": current_user.invite_code
        }

    except Exception as e:
        logger.error(f"Error getting referral link: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting referral link: {str(e)}"
        )


@router.get("/stats")
async def get_referral_stats(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить статистику приглашений текущего пользователя"""
    try:
        # Получаем количество приглашенных пользователей
        invited_users_query = select(func.count(User.id)).where(
            User.invited_by_code == current_user.invite_code
        )
        result = await session.execute(invited_users_query)
        total_invites = result.scalar_one() or 0

        # Получаем количество активных приглашенных пользователей
        active_invites_query = select(func.count(User.id)).where(
            and_(
                User.invited_by_code == current_user.invite_code,
                User.has_access == True
            )
        )
        result = await session.execute(active_invites_query)
        active_invites = result.scalar_one() or 0

        # Получаем заработанные баллы от рефералов
        referral_points_query = select(func.sum(PointTransaction.amount)).where(
            and_(
                PointTransaction.user_id == current_user.id,
                PointTransaction.transaction_type == TransactionType.INVITE_BONUS
            )
        )
        result = await session.execute(referral_points_query)
        earned_points = result.scalar_one() or 0

        return {
            "invite_code": current_user.invite_code,
            "total_invites": total_invites,
            "active_invites": active_invites,
            "earned_points": earned_points,
            "effective_discount": getattr(current_user, 'effective_discount', 0)
        }

    except Exception as e:
        logger.error(f"Error getting referral stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting referral stats: {str(e)}"
        )


@router.post("/use/{invite_code}")
async def use_invite_code(
    invite_code: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Использовать пригласительный код"""
    try:
        # Проверяем, что пользователь еще не использовал инвайт-код
        if current_user.invited_by_code:
            raise HTTPException(
                status_code=400,
                detail="User has already used an invite code"
            )

        # Находим пригласившего пользователя
        inviter_query = select(User).where(User.invite_code == invite_code)
        result = await session.execute(inviter_query)
        inviter = result.scalar_one_or_none()

        if not inviter:
            raise HTTPException(
                status_code=400,
                detail="Invalid invite code"
            )

        if inviter.id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Cannot use your own invite code"
            )

        # Обновляем данные нового пользователя
        current_user.invited_by_code = invite_code

        # Обновляем статистику пригласившего
        inviter.invites_count += 1

        # Начисляем баллы пригласившему
        async with PointsManager(session) as points_manager:
            await points_manager.add_points(
                user_id=inviter.id,
                amount=100,  # Награда за приглашение
                transaction_type=TransactionType.INVITE_BONUS,
                description=f"Referral bonus for inviting user {current_user.id}",
                meta_data={
                    "invited_user_id": current_user.id,
                    "invite_code": invite_code
                }
            )

        await session.commit()

        return {
            "status": "success",
            "message": "Invite code applied successfully",
            "bonus_points": 100
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing invite code: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing invite code: {str(e)}"
        )