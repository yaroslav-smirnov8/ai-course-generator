from fastapi import Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import hmac
import hashlib
import json
import urllib.parse
import logging
from datetime import datetime, timedelta, timezone

from .config import settings
from .database import get_db
from ..models import User
from ..services.user import UserManager
from ..core.constants import UserRole
from ..core.constants import UNLIMITED_ROLES
from app.core.cache import cache_service

logger = logging.getLogger(__name__)


class SecurityManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_manager = UserManager(session)
        self.cache_service = cache_service

    async def validate_init_data(self, init_data: str, max_age: int = 3600) -> Dict[str, Any]:
        """Валидация initData от Telegram WebApp"""
        try:
            # Логируем raw init_data
            # logger.error(f"Raw init_data: {init_data}")

            # Парсим все параметры из init_data
            parsed_data = dict(urllib.parse.parse_qsl(init_data))
            # logger.error(f"Parsed data: {parsed_data}")

            # Получаем и удаляем хеш для проверки подписи
            hash_ = parsed_data.pop('hash', None)
            # logger.error(f"Hash from data: {hash_}")
            if not hash_:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No hash in init data"
                )

            # Проверяем время
            auth_date = int(parsed_data.get('auth_date', 0))
            now = int(datetime.now(timezone.utc).timestamp())
            if now - auth_date > max_age:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Init data expired"
                )

            # Формируем data-check-string
            data_check_list = []
            for key in sorted(parsed_data.keys()):
                value = parsed_data[key]
                if value is not None:
                    data_check_list.append(f"{key}={value}")
            data_check_string = '\n'.join(data_check_list)

            # Создаем secret key
            secret_key = hmac.new(
                key=b"WebAppData",
                msg=settings.BOT_TOKEN.encode(),
                digestmod=hashlib.sha256
            ).digest()

            # Проверяем подпись
            signature = hmac.new(
                key=secret_key,
                msg=data_check_string.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()

            if signature != hash_:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid hash"
                )

            # Парсим данные пользователя
            user_data = json.loads(parsed_data.get('user', '{}'))
            # logger.error(f"Raw user data: {user_data}")
            theme_params = json.loads(parsed_data.get('theme_params', '{}'))

            if isinstance(user_data, str):
                try:
                    user_data = json.loads(user_data)
                    # logger.error(f"Parsed user data: {user_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse user data JSON: {e}")
                    # logger.error(f"Invalid user data string: {user_data}")
                    raise

            # logger.error(f"Final validated data: {parsed_data}")

            return {
                "user": user_data,
                "platform": parsed_data.get('platform'),
                "version": parsed_data.get('version'),
                "theme_params": theme_params,
                "start_param": parsed_data.get('start_param'),
                "auth_date": auth_date
            }

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in init data"
            )
        except Exception as e:
            logger.error(f"Error validating init data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid init data format"
            )

    async def authenticate_user(self, validated_data: Dict) -> User:
        """Аутентификация или создание пользователя"""
        # logger.error("=== User Authentication Debug ===")
        # logger.error(f"Validated data received: {validated_data}")
        user_data = validated_data.get('user')
        # logger.error(f"Extracted user data: {user_data}")
        # logger.error(f"User data type: {type(user_data)}")

        if isinstance(user_data, str):
            try:
                user_data = json.loads(user_data)
                logger.error(f"Parsed user data: {user_data}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse user data: {e}")
        if not user_data or 'id' not in user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user data in init data"
            )

        try:
            # Пытаемся найти пользователя
            user = await self.user_manager.get_by_telegram_id(user_data['id'])

            if not user:
                # Создаем нового пользователя
                user = await self.user_manager.create_telegram_user({
                    "telegram_id": user_data['id'],
                    "username": user_data.get('username'),
                    "first_name": user_data.get('first_name'),
                    "last_name": user_data.get('last_name'),
                    "language_code": user_data.get('language_code'),
                    "is_premium": user_data.get('is_premium', False),
                    "platform": validated_data.get('platform'),
                    "webapp_version": validated_data.get('version'),
                    "theme_params": validated_data.get('theme_params')
                })
            else:
                # Проверяем, должен ли пользователь быть админом или модератором
                if user_data['id'] == settings.ADMIN_ID and user.role != UserRole.ADMIN:
                    user.role = UserRole.ADMIN
                    await self.session.commit()
                elif user_data['id'] == settings.MOD_ID and user.role != UserRole.MOD:
                    user.role = UserRole.MOD
                    await self.session.commit()
                # Обновляем время последней активности
                await self.user_manager.update_last_active(user.id)

            return user

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )


# app/core/security.py
async def telegram_auth_middleware(request: Request) -> User:
    """Основной middleware для аутентификации через Telegram WebApp"""
    try:
        # Пропускаем OPTIONS запросы
        if request.method == "OPTIONS":
            return None

        # Пропускаем статику и health check
        if request.url.path.startswith(("/static", "/health", "/docs", "/openapi.json")):
            return None

        # logger.error("=== Telegram Auth Middleware Debug ===")
        # logger.error(f"Request headers: {dict(request.headers)}")
        auth_header = request.headers.get("Authorization")
        # logger.error(f"Auth header: {auth_header}")

        if auth_header:
            scheme, init_data = auth_header.split(' ', 1)
            # logger.error(f"Auth scheme: {scheme}")
            # logger.error(f"Init data: {init_data[:100]}...")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is required"
            )

        scheme, init_data = auth_header.split(' ', 1)

        # Логируем схему и данные
        # logger.error(f"Auth scheme: {scheme}")
        # logger.error(f"Init data: {init_data[:100]}...")  # Логируем первые 100 символов

        if scheme.lower() != "tma":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )

        async for session in get_db():
            try:
                security_manager = SecurityManager(session)
                validated_data = await security_manager.validate_init_data(init_data)

                # Логируем валидированные данные
                # logger.error(f"Validated data: {validated_data}")

                user = await security_manager.authenticate_user(validated_data)

                # Сохраняем пользователя в состоянии запроса
                request.state.user = user
                return user
            finally:
                await session.close()

    except Exception as e:
        logger.error(f"Auth middleware error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


async def get_current_user(request: Request) -> User:
    """Получение текущего пользователя из request state"""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user

async def check_unlimited_access(user_id: int, session: AsyncSession) -> bool:
    """
    Проверка безлимитного доступа пользователя (админ или друг)

    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Сессия базы данных

    Returns:
        bool: True если у пользователя безлимитный доступ
    """
    try:
        user_manager = UserManager(session)
        user = await user_manager.get(user_id)

        logger.debug(f"Checking unlimited access for user {user_id}")
        logger.debug(f"User role: {user.role if user else 'User not found'}")
        logger.debug(f"Is admin: {user.role == UserRole.ADMIN if user else False}")
        logger.debug(f"Is in unlimited roles: {user.role in UNLIMITED_ROLES if user else False}")

        if not user:
            return False

        return user.role in UNLIMITED_ROLES
    except Exception as e:
        logger.error(f"Error in check_unlimited_access: {str(e)}")
        return False

async def check_admin_rights(user_id: int, session: AsyncSession) -> bool:
    """
    Проверка прав администратора

    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Сессия базы данных

    Returns:
        bool: True если пользователь админ
    """
    logger.info(f"=== check_admin_rights ===")
    logger.info(f"Checking admin rights for user_id: {user_id}")

    try:
        user_manager = UserManager(session)
        user = await user_manager.get(user_id)

        if user is None:
            logger.warning(f"User with id {user_id} not found")
            return False

        is_admin = user.role == UserRole.ADMIN
        logger.info(f"User {user_id} role: {user.role}, is_admin: {is_admin}")
        logger.info(f"User details: telegram_id={user.telegram_id}, username={user.username}")

        # Проверяем, соответствует ли ID пользователя ID администратора из настроек
        if user.telegram_id == settings.ADMIN_ID:
            logger.info(f"User {user_id} has ADMIN_ID from settings: {settings.ADMIN_ID}")
            if not is_admin:
                logger.warning(f"User {user_id} has ADMIN_ID but role is {user.role}, not admin")

        return is_admin
    except Exception as e:
        logger.error(f"Error in check_admin_rights: {str(e)}", exc_info=True)
        return False

async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> User:
    """
    Проверка прав администратора с получением пользователя

    Args:
        current_user: Текущий пользователь
        session (AsyncSession): Сессия базы данных

    Returns:
        User: Текущий пользователь если он админ

    Raises:
        HTTPException: если пользователь не админ
    """
    logger.info(f"=== get_current_admin_user ===")
    logger.info(f"Checking admin rights for current_user: id={current_user.id}, telegram_id={current_user.telegram_id}, role={current_user.role}")

    try:
        # Проверяем, является ли пользователь администратором
        is_admin = await check_admin_rights(current_user.id, session)

        # Если пользователь не администратор, но его telegram_id соответствует ADMIN_ID из настроек,
        # обновляем его роль на администратора
        if not is_admin and current_user.telegram_id == settings.ADMIN_ID:
            logger.info(f"User {current_user.id} has ADMIN_ID from settings but not admin role. Updating role to ADMIN.")
            current_user.role = UserRole.ADMIN
            await session.commit()
            is_admin = True

        if not is_admin:
            logger.warning(f"User {current_user.id} is not an admin. Access denied.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )

        logger.info(f"Admin access granted for user {current_user.id}")
        return current_user
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        logger.error(f"Error in get_current_admin_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking admin rights: {str(e)}"
        )

def admin_required(session: AsyncSession = Depends(get_db)):
    """
    Декоратор для проверки прав администратора

    Args:
        session (AsyncSession): Сессия базы данных

    Returns:
        Callable: Декоратор проверки прав
    """
    async def check_admin(current_user: User = Depends(get_current_user)):
        if not await check_admin_rights(current_user.id, session):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator rights required"
            )
        return True
    return check_admin

def require_roles(*allowed_roles: UserRole):
    """
    Декоратор для проверки ролей пользователя

    Args:
        *allowed_roles: Список разрешенных ролей

    Returns:
        Callable: Декоратор проверки ролей
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role} not allowed"
            )
        return current_user
    return role_checker

def get_current_user_with_permissions(permissions: list[str]):
    """
    Декоратор для проверки разрешений пользователя

    Args:
        permissions: Список необходимых разрешений

    Returns:
        Callable: Декоратор проверки разрешений
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db)
    ) -> User:
        # Проверка на админа
        if "admin" in permissions and not await check_admin_rights(current_user.id, session):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator rights required"
            )

        # Здесь можно добавить проверку других разрешений

        # Возвращаем данные пользователя в формате TokenData
        from ..schemas.auth import TokenData
        return TokenData(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            role=current_user.role
        )

    return permission_checker