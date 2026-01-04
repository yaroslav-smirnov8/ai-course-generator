# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone
from ...core import UserRole
from ...core.database import get_db
from ...services.user import UserManager
from ...schemas.user import UserCreate, UserUpdate, UserInDB, UserList, UserStats
from ...core.security import get_current_user, get_current_admin_user
from ...models.user import User
from ...models import DailyUsage, Generation, Image
from ...services.tariff import TariffManager
from ...schemas.pricing import TariffUpdate as UserTariffUpdate, TariffResponse
import logging
from typing import Optional

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/me", response_model=UserInDB)
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db)
):
    """Получить информацию о текущем пользователе"""
    logger.error("=== Get Current User Debug ===")
    logger.error(f"Current user ID: {current_user.id}")

    try:
        user_service = UserManager(session)
        await user_service.update_last_active(current_user.id)
        logger.error(f"User data: {current_user.__dict__}")
        return current_user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise


@router.post("/telegram-auth", response_model=UserInDB)
async def authenticate_telegram_user(
        telegram_data: dict,
        session: AsyncSession = Depends(get_db)
):
    """Аутентификация/регистрация пользователя через Telegram"""
    user_service = UserManager(session)
    user = await user_service.create_telegram_user(telegram_data)
    return user


@router.get("/", response_model=UserList)
async def get_users(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Получить список пользователей (только для админов)"""
    logger.info(f"=== GET /api/v1/users/ ===")
    logger.info(f"Request params: skip={skip}, limit={limit}")
    logger.info(f"Current admin user: id={current_user.id}, telegram_id={current_user.telegram_id}, role={current_user.role}")

    try:
        user_service = UserManager(session)
        users = await user_service.get_many(skip=skip, limit=limit)
        total = await user_service.get_active_users_count()

        logger.info(f"Retrieved {len(users)} users out of {total} total")
        logger.info(f"First few users: {[{'id': u.id, 'telegram_id': u.telegram_id, 'role': u.role} for u in users[:3]]}")

        response = {"items": users, "total": total}
        logger.info(f"Response structure: {list(response.keys())}")
        logger.info(f"Items type: {type(response['items'])}, Items length: {len(response['items'])}")

        return response
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")


@router.get("/users/{user_id}", response_model=UserInDB)
async def get_user(
        user_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить информацию о пользователе"""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user_service = UserManager(session)
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserInDB)
async def update_user(
        user_id: int,
        user_data: UserUpdate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Обновить информацию о пользователе (только для админов)"""
    user_service = UserManager(session)
    try:
        updated_user = await user_service.update(user_id, user_data.dict(exclude_unset=True))
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/achievements")
async def get_user_achievements(
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить достижения пользователя"""
    try:
        from ...services.achievements.manager import AchievementManager
        achievement_manager = AchievementManager(session)
        
        # Получаем прогресс достижений пользователя
        progress = await achievement_manager.get_user_achievements_progress(current_user.id)
        
        return {
            "total_achievements": progress.total_achievements,
            "unlocked_achievements": progress.unlocked_achievements,
            "total_points_earned": progress.total_points_earned,
            "next_achievements": progress.next_achievements,
            "recent_unlocks": progress.recent_unlocks
        }
    except Exception as e:
        logger.error(f"Error getting user achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/referral")
async def get_user_referral_link(
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить реферальную ссылку пользователя"""
    try:
        # Если у пользователя нет инвайт-кода, генерируем его
        if not current_user.invite_code:
            import uuid
            # Генерируем уникальный код
            max_attempts = 5
            for attempt in range(max_attempts):
                invite_code = str(uuid.uuid4())[:8]

                # Проверяем уникальность
                from sqlalchemy import select
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

        # Формируем ссылку
        base_url = "https://t.me/neuro_teacher_bot?start="
        referral_link = f"{base_url}{current_user.invite_code}"

        return {
            "link": referral_link,
            "invite_code": current_user.invite_code
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/invite/{invite_code}")
async def use_invite_code(
        invite_code: str,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Использовать пригласительный код"""
    user_service = UserManager(session)
    try:
        user = await user_service.process_invite(invite_code, current_user.telegram_id)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid invite code")
        return {"status": "success", "message": "Invite code applied successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/tariff", response_model=TariffResponse)
async def update_user_tariff(
        tariff_update: UserTariffUpdate,
        user_id: int = Path(..., ge=1),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Обновить тариф пользователя"""
    # Проверяем, что текущий пользователь обновляет свой тариф или является администратором
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    async with TariffManager(session) as tariff_manager:
        try:
            # Админы могут обновлять тарифы без списания баллов
            admin_override = current_user.role == "admin"

            result = await tariff_manager.update_user_tariff(
                user_id=user_id,
                tariff_type=tariff_update.tariff_type,
                admin_override=admin_override
            )

            if not result:
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось обновить тариф."
                )

            tariff_info = await tariff_manager.get_tariff_info(user_id)
            return {
                "status": "success",
                "message": "Тариф успешно обновлен",
                "data": tariff_info
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обновлении тарифа: {str(e)}"
            )


@router.get("/{user_id}/usage-stats")
async def get_user_usage_stats(
        user_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Get user's generation usage statistics"""
    logger.info(f"Getting usage stats for user {user_id}")

    # Check if the user is requesting their own stats or is an admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        logger.warning(f"Permission denied: User {current_user.id} tried to access stats for user {user_id}")
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        # Get daily usage with timezone-aware date
        today = datetime.now(timezone.utc).date()
        logger.info(f"Querying daily usage for user {user_id} on date {today}")

        daily_usage_query = select(DailyUsage).where(
            and_(
                DailyUsage.user_id == user_id,
                DailyUsage.date == today
            )
        )
        result = await session.execute(daily_usage_query)
        daily_usage = result.scalar_one_or_none()

        if daily_usage:
            logger.info(f"Found daily usage for user {user_id}: generations={daily_usage.generations_count}, images={daily_usage.images_count}")
        else:
            logger.info(f"No daily usage found for user {user_id} on date {today}")

        # Count total generations and images
        gen_query = select(func.count(Generation.id)).where(Generation.user_id == user_id)
        img_query = select(func.count(Image.id)).where(Image.user_id == user_id)

        total_gens = await session.execute(gen_query)
        total_imgs = await session.execute(img_query)

        total_generations = total_gens.scalar_one() or 0
        total_images = total_imgs.scalar_one() or 0

        logger.info(f"Total generations for user {user_id}: {total_generations}, total images: {total_images}")

        # Get user for last_active time
        user = await session.get(User, user_id)

        # Prepare response
        response = {
            "daily_generations": daily_usage.generations_count if daily_usage else 0,
            "daily_images": daily_usage.images_count if daily_usage else 0,
            "total_generations": total_generations,
            "total_images": total_images,
            "last_active": user.last_active if user else datetime.now(timezone.utc)
        }

        logger.info(f"Returning usage stats for user {user_id}: {response}")
        return response

    except Exception as e:
        logger.error(f"Error getting usage stats for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting usage statistics: {str(e)}")


@router.post("/{user_id}/reset-usage-counters")
async def reset_usage_counters(
        user_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Reset daily usage counters for a user (admin only or self)"""
    logger.info(f"Resetting usage counters for user {user_id}")

    # Check if the user is resetting their own counters or is an admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        logger.warning(f"Permission denied: User {current_user.id} tried to reset counters for user {user_id}")
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        # Get daily usage with timezone-aware date
        today = datetime.now(timezone.utc).date()
        logger.info(f"Querying daily usage for user {user_id} on date {today}")

        daily_usage_query = select(DailyUsage).where(
            and_(
                DailyUsage.user_id == user_id,
                DailyUsage.date == today
            )
        )
        result = await session.execute(daily_usage_query)
        daily_usage = result.scalar_one_or_none()

        if daily_usage:
            logger.info(f"Found daily usage for user {user_id}: generations={daily_usage.generations_count}, images={daily_usage.images_count}")

            # Reset counters
            daily_usage.generations_count = 0
            daily_usage.images_count = 0

            # Save changes
            session.add(daily_usage)
            await session.commit()

            logger.info(f"Reset daily usage counters for user {user_id}")

            return {
                "status": "success",
                "message": "Daily usage counters reset successfully",
                "data": {
                    "daily_generations": 0,
                    "daily_images": 0
                }
            }
        else:
            logger.info(f"No daily usage found for user {user_id}, creating new record with zero counters")

            # Create new record with zero counters
            new_daily_usage = DailyUsage(
                user_id=user_id,
                date=today,
                generations_count=0,
                images_count=0
            )

            # Save new record
            session.add(new_daily_usage)
            await session.commit()

            return {
                "status": "success",
                "message": "Created new daily usage record with zero counters",
                "data": {
                    "daily_generations": 0,
                    "daily_images": 0
                }
            }

    except Exception as e:
        logger.error(f"Error resetting usage counters for user {user_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting usage counters: {str(e)}")


@router.post("/{user_id}/add-points")
async def add_points_to_user(
        user_id: int,
        points: int = Query(..., ge=1, le=10000),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    """Add points to user (admin only, for testing)"""
    logger.info(f"Adding {points} points to user {user_id}")

    try:
        # Get user
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Add points
        old_points = user.points
        user.points += points

        # Save changes
        session.add(user)
        await session.commit()

        logger.info(f"Added {points} points to user {user_id}. Old balance: {old_points}, new balance: {user.points}")

        return {
            "status": "success",
            "message": f"Added {points} points to user",
            "data": {
                "old_points": old_points,
                "new_points": user.points,
                "added_points": points
            }
        }

    except Exception as e:
        logger.error(f"Error adding points to user {user_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding points: {str(e)}")