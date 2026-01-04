from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from datetime import datetime, timezone

from ...core.database import get_db
from ...core.security import SecurityManager
from ...services.session import SessionService
from ...services.telegram.subscription_checker import subscription_checker
from ...schemas.user import UserResponse, UserInDB
from ...models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/telegram", response_model=UserResponse)
async def telegram_auth(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Аутентификация через Telegram WebApp
    """
    try:
        # Получаем Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is required"
            )

        # Проверяем формат header
        scheme, init_data = auth_header.split(' ', 1)
        if scheme.lower() != "tma":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )

        # Валидируем init_data через SecurityManager
        security_manager = SecurityManager(session)
        validated_data = await security_manager.validate_init_data(init_data)

        # Создаем/обновляем сессию пользователя
        session_service = SessionService(session)
        user = await session_service.create_user_session(validated_data["user"])

        # Проверяем доступ пользователя (бан + подписка на канал)
        access_check = await subscription_checker.check_user_access(
            user_id=user.telegram_id,
            has_access=user.has_access
        )

        if not access_check["access_granted"]:
            # Возвращаем специальный ответ с информацией о блокировке
            error_response = {
                "access_denied": True,
                "reason": access_check["reason"],
                "channel_url": access_check.get("channel_url"),
                "error": access_check.get("error")
            }

            if access_check["reason"] == "banned":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response
                )
            elif access_check["reason"] == "not_subscribed":
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,  # Используем 402 для подписки
                    detail=error_response
                )
            elif access_check["reason"] == "evo_not_subscribed":
                # Специальный код для подписки на канал приложения
                error_response["reason"] = "evo_subscription_required"
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,  # Используем 402 для подписки
                    detail=error_response
                )

        # Собираем данные для ответа
        limits = {}
        if user.tariff:
            limits = {
                "daily_generations": 0,  # Будет заполнено из статистики
                "daily_images": 0,  # Будет заполнено из статистики
                "points": user.points
            }

        response = {
            "access_token": init_data,  # Используем initData как токен
            "token_type": "bearer",
            "user": UserInDB.model_validate(user),
            "limits": limits
        }

        return response

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.get("/me", response_model=UserInDB)
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Получение текущего пользователя
    """
    try:
        # Получаем пользователя из request state (установлен в middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        # Обновляем время последней активности
        user.last_active = datetime.now(timezone.utc)
        await session.commit()

        return user

    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """
    Выход из системы
    """
    try:
        user = getattr(request.state, "user", None)
        if user:
            # Можно добавить дополнительную логику при выходе
            user.last_active = datetime.now(timezone.utc)
            await session.commit()

        return {"status": "success", "message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during logout"
        )