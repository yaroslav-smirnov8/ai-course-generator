"""
Декораторы для проверки премиум доступа
"""
import logging
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status
from ..core.constants import TariffType, UserRole

logger = logging.getLogger(__name__)

def check_premium_access(feature_name: str = "Premium feature"):
    """
    Декоратор для проверки доступа к премиум функциям.

    Разрешает доступ:
    - Админам (role = admin)
    - Пользователям с безлимитными ролями (friend, mod)
    - Пользователям с Premium тарифом (tariff_6)

    Args:
        feature_name: Название функции для сообщения об ошибке
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Получаем current_user из kwargs
            current_user = kwargs.get('current_user')

            if not current_user:
                logger.error(f"Premium access check failed: no current_user found for {feature_name}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Проверяем, является ли пользователь админом или имеет безлимитную роль
            unlimited_roles = [UserRole.ADMIN, UserRole.FRIEND, UserRole.MOD]
            is_unlimited_user = current_user.role in unlimited_roles

            # Проверяем, есть ли у пользователя Premium тариф
            has_premium_tariff = current_user.tariff == TariffType.PREMIUM.value

            if not is_unlimited_user and not has_premium_tariff:
                logger.warning(
                    f"Premium access denied for user {current_user.id} "
                    f"(role: {current_user.role}, tariff: {current_user.tariff}) "
                    f"to feature: {feature_name}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Premium tariff required to access {feature_name}. Please upgrade to Premium."
                )

            logger.info(
                f"Premium access granted for user {current_user.id} "
                f"(role: {current_user.role}, tariff: {current_user.tariff}) "
                f"to feature: {feature_name}"
            )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
