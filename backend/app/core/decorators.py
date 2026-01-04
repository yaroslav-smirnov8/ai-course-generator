# app/core/decorators.py

from functools import wraps
from typing import Callable, Any, Optional
from enum import Enum
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from sqlalchemy import select

from .constants import ContentType, UserRole, TariffType, TARIFF_LIMITS
from .security import check_unlimited_access
from ..schemas.tracking import UsageLogCreate
from ..services import UsageTracker
from ..services.achievements import AchievementManager
from ..models import DailyUsage, User
import logging

logger = logging.getLogger(__name__)


def check_course_generation_limits(content_type: ContentType):
    """Decorator for checking generation limits specifically adapted for course generator (expects kwargs)"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any: # Изменено здесь
            # Извлекаем зависимости из kwargs
            request = kwargs.get('request')
            session = kwargs.get('session')
            current_user = kwargs.get('current_user')
            course_data = kwargs.get('course_data')

            if not request or not session or not current_user:
                logger.error("Missing required dependencies (request, session, or current_user) in kwargs for check_generation_limits")
                raise HTTPException(status_code=500, detail="Internal server error: Missing dependencies in decorator")

            # Проверяем, используются ли баллы для генерации или нужно пропустить проверку тарифа
            with_points = False
            skip_tariff_check = False
            skip_limits = False

            # Проверяем флаги в course_data, если он есть
            if course_data:
                if hasattr(course_data, 'with_points') and course_data.with_points:
                    with_points = True
                if hasattr(course_data, 'skip_tariff_check') and course_data.skip_tariff_check:
                    skip_tariff_check = True
                if hasattr(course_data, 'skip_limits') and course_data.skip_limits:
                    skip_limits = True

            # Также проверяем флаги в JSON-данных запроса, если это возможно
            if request and hasattr(request, 'json'):
                try:
                    request_data = await request.json()
                    if 'with_points' in request_data and request_data['with_points']:
                        with_points = True
                    if 'skip_tariff_check' in request_data and request_data['skip_tariff_check']:
                        skip_tariff_check = True
                    if 'skip_limits' in request_data and request_data['skip_limits']:
                        skip_limits = True
                except Exception as e:
                    logger.warning(f"Failed to parse request JSON: {e}")

            # Если генерация за баллы или нужно пропустить проверку тарифа/лимитов, пропускаем проверку
            if with_points or skip_tariff_check or skip_limits:
                logger.info(f"Generation with points or skip_tariff_check/skip_limits requested, skipping limit and tariff checks")
                return await func(*args, **kwargs)

            user_id = current_user.id

            # Check unlimited access (admins and friends)
            is_unlimited = await check_unlimited_access(user_id, session)

            if is_unlimited:
                # Вызываем оригинальную функцию, передавая все исходные аргументы
                return await func(*args, **kwargs) # Исправлено здесь
            # Get daily usage
            stmt = select(DailyUsage).where(
                DailyUsage.user_id == user_id,
                DailyUsage.date == datetime.now(timezone.utc).date()
            )
            result = await session.execute(stmt)
            daily_usage = result.scalar_one_or_none()

            if not daily_usage:
                daily_usage = DailyUsage(user_id=user_id) # Defaults should be 0
                session.add(daily_usage)
                await session.flush() # Flush to get potential defaults or trigger related logic


            # Check limits using the already available current_user object
            # Убираем повторный запрос к БД за пользователем
            # stmt = select(User).where(User.id == user_id)
            # result = await session.execute(stmt)
            # user = result.scalar_one_or_none()
            user = current_user # Используем пользователя, полученного из зависимости

            # Проверяем, что current_user - это объект User и у него есть тариф
            if not isinstance(user, User):
                 logger.error(f"current_user is not a User instance, but {type(user)}. Cannot check tariff.")
                 raise HTTPException(status_code=500, detail="Internal server error: Invalid user object")

            # --- ЛОГИРОВАНИЕ УДАЛЕНО ---

            if not user.tariff:
                logger.warning(f"No active tariff found for user {user_id} in current_user object.")
                raise HTTPException(status_code=403, detail="No active tariff")

            limit_key = user.tariff # Используем значение enum напрямую как ключ
            limits = TARIFF_LIMITS.get(limit_key) # Убрали default, чтобы увидеть None если ключа нет

            if not limits:
                 logger.error(f"Could not find limits for tariff key: {limit_key} (type: {type(limit_key)}). User tariff value: {user.tariff}")
                 # Пытаемся получить по строковому значению на всякий случай
                 limits = TARIFF_LIMITS.get(str(user.tariff))
                 if not limits:
                     logger.error(f"Still could not find limits for tariff string value: {str(user.tariff)}")
                     # Можно установить дефолтный лимит или выбросить ошибку
                     # limits = TARIFF_LIMITS[TariffType.BASIC] # Пример дефолта
                     raise HTTPException(status_code=500, detail=f"Tariff limits not configured for {user.tariff}")

            if content_type == ContentType.IMAGE:
                if daily_usage.images_count >= limits.daily_images:
                    logger.warning(f"Daily image limit exceeded for user {user_id}")
                    raise HTTPException(status_code=429, detail="Daily image limit exceeded")
            else:
                if daily_usage.generations_count >= limits.daily_generations:
                    logger.warning(f"Daily generation limit exceeded for user {user_id}")
                    raise HTTPException(status_code=429, detail="Daily generation limit exceeded")

            # Call the original function
            result = await func(*args, **kwargs) # Изменено здесь

            # --- УДАЛЕНА ЛОГИКА ПОВТОРНОЙ ЗАГРУЗКИ И ОБНОВЛЕНИЯ СЧЕТЧИКОВ ---
            # Декоратор теперь только проверяет лимиты ДО вызова функции

            return result # Возвращаем результат основной функции

        return wrapper

    return decorator


def check_course_achievements(action_type: str, content_type: ContentType):
    """Decorator for checking achievements specifically adapted for course generator (expects kwargs)"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any: # Изменено здесь
            # Извлекаем зависимости из kwargs
            request = kwargs.get('request')
            session = kwargs.get('session')
            current_user = kwargs.get('current_user')

            if not request or not session or not current_user:
                logger.error("Missing required dependencies (request, session, or current_user) in kwargs for check_achievements")
                raise HTTPException(status_code=500, detail="Internal server error: Missing dependencies in decorator")

            user_id = current_user.id

            # Call the original function
            result = await func(*args, **kwargs) # Изменено здесь

            # Check achievements
            try:
                async with AchievementManager(session) as achievement_manager:
                    await achievement_manager.check_achievements(
                        user_id=user_id,
                        action_type=action_type,
                        action_data={
                            'content_type': content_type.value,
                            'success': True
                        }
                    )
            except Exception as e:
                logger.error(f"Error checking achievements: {str(e)}")
                # Don't fail the request if achievements check fails

            return result

        return wrapper

    return decorator


def track_course_usage(content_type: ContentType):
    """Decorator for tracking usage specifically adapted for course generator (expects kwargs)"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any: # Изменено здесь
            # Извлекаем зависимости из kwargs
            request = kwargs.get('request')
            session = kwargs.get('session')
            current_user = kwargs.get('current_user')
            course_data = kwargs.get('course_data')

            if not request or not session or not current_user:
                logger.error("Missing required dependencies (request, session, or current_user) in kwargs for track_usage")
                raise HTTPException(status_code=500, detail="Internal server error: Missing dependencies in decorator")

            user_id = current_user.id

            # Проверяем, используются ли баллы для генерации или нужно пропустить проверку тарифа
            with_points = False
            skip_tariff_check = False
            skip_limits = False

            # Проверяем флаги в course_data, если он есть
            if course_data:
                if hasattr(course_data, 'with_points') and course_data.with_points:
                    with_points = True
                if hasattr(course_data, 'skip_tariff_check') and course_data.skip_tariff_check:
                    skip_tariff_check = True
                if hasattr(course_data, 'skip_limits') and course_data.skip_limits:
                    skip_limits = True

            # Также проверяем флаги в JSON-данных запроса, если это возможно
            if request and hasattr(request, 'json'):
                try:
                    request_data = await request.json()
                    if 'with_points' in request_data and request_data['with_points']:
                        with_points = True
                    if 'skip_tariff_check' in request_data and request_data['skip_tariff_check']:
                        skip_tariff_check = True
                    if 'skip_limits' in request_data and request_data['skip_limits']:
                        skip_limits = True
                except Exception as e:
                    logger.warning(f"Failed to parse request JSON: {e}")

            # Call the original function
            result = await func(*args, **kwargs) # Изменено здесь

            # Log usage
            try:
                # Подготавливаем extra_data
                extra_data = kwargs.get('extra_data', {})

                # Добавляем информацию о генерации за баллы и пропуске проверки тарифа в extra_data
                if with_points:
                    extra_data['with_points'] = True
                if skip_limits:
                    extra_data['skip_limits'] = True
                if skip_tariff_check:
                    extra_data['skip_tariff_check'] = True

                async with UsageTracker(session) as usage_tracker:
                    # Исправлено: гарантируем, что передается правильное значение enum
                    # Проверяем тип content_type для безопасного преобразования
                    if isinstance(content_type, Enum):
                        # Если это перечисление, используем его value
                        content_type_value = content_type.value
                    elif isinstance(content_type, str):
                        # Если это строка, просто приводим к нижнему регистру
                        content_type_value = content_type.lower()
                    else:
                        # Для других типов - преобразуем в строку и приводим к нижнему регистру
                        content_type_value = str(content_type).lower()

                    await usage_tracker.log_usage(UsageLogCreate(
                        user_id=user_id,
                        action_type="generation",
                        content_type=content_type_value,
                        extra_data=extra_data,
                        skip_limits=skip_limits or with_points or skip_tariff_check  # Пропускаем лимиты, если генерация за баллы или пропуск проверки тарифа
                    ))
            except Exception as e:
                logger.error(f"Error tracking usage: {str(e)}", exc_info=True)
                # Don't fail the request if usage tracking fails

            return result

        return wrapper

    return decorator


def track_course_feature_usage(feature_type: str, content_type: Optional[ContentType] = None):
    """Decorator for tracking feature usage specifically adapted for course generator (expects kwargs)"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any: # Изменено здесь
            # Извлекаем зависимости из kwargs
            request = kwargs.get('request')
            session = kwargs.get('session')
            current_user = kwargs.get('current_user')

            if not request or not session or not current_user:
                logger.error("Missing required dependencies (request, session, or current_user) in kwargs for track_feature_usage")
                raise HTTPException(status_code=500, detail="Internal server error: Missing dependencies in decorator")

            user_id = current_user.id

            # Convert ContentType enum to string value if provided
            content_type_str = content_type.value if content_type else None

            try:
                # Call the original function
                result = await func(*args, **kwargs) # Изменено здесь

                # Record successful usage
                try:
                    # Import inside to avoid circular imports
                    from ..services.analytics import FeatureUsageService
                    # Create the service directly with the session
                    feature_service = FeatureUsageService(session)
                    # Используем отдельную сессию для логирования, чтобы не влиять на основную транзакцию
                    await feature_service.track_feature_usage(
                        user_id=user_id,
                        feature_type=feature_type,
                        content_type=content_type_str,
                        success=True,
                        usage_data={
                            "request_data": request.dict() if hasattr(request, 'dict') else {"message": "Request has no dict method"},
                            "response_status": "success"
                        }
                    )
                except Exception as tracking_error:
                    logger.error(f"Error tracking successful feature usage: {str(tracking_error)}")

                return result
            except Exception as e: # This is the outer exception handler
                # Record failed usage
                if session: # Check if session exists before using it
                    try:
                        # Import inside to avoid circular imports
                        from ..services.analytics import FeatureUsageService
                        # Create the service directly with the session
                        feature_service = FeatureUsageService(session)
                        # Используем отдельную сессию для логирования, чтобы не влиять на основную транзакцию
                        await feature_service.track_feature_usage(
                            user_id=user_id,
                            feature_type=feature_type,
                            content_type=content_type_str,
                            success=False,
                            usage_data={
                                "request_data": request.dict() if hasattr(request, 'dict') else {"message": "Request has no dict method"},
                                "response_status": "error",
                                "error": str(e)
                            }
                        )
                    except Exception as tracking_error:
                        logger.error(f"Error recording feature usage failure: {str(tracking_error)}")
                        # Don't swallow the original exception

                # Re-raise the original exception 'e' after attempting to log
                raise # Correctly aligned with the 'if session:' block (level 2 indentation)

        return wrapper

    return decorator


def memory_optimized():
    """Memory optimization decorator that preserves function signature"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Optionally perform memory cleanup here
                # import gc
                # gc.collect()
                pass

        return wrapper

    return decorator

def check_generation_limits(content_type: ContentType):
    """Decorator for checking generation limits that works with request objects"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request, session: AsyncSession, *args: Any, **kwargs: Any) -> Any:
            # Проверяем, используются ли баллы для генерации или нужно пропустить проверку тарифа/лимитов
            with_points = False
            skip_tariff_check = False
            skip_limits = False

            # Проверяем флаги в request
            if hasattr(request, 'with_points'):
                with_points = request.with_points
            if hasattr(request, 'skip_tariff_check'):
                skip_tariff_check = request.skip_tariff_check
            if hasattr(request, 'skip_limits'):
                skip_limits = request.skip_limits

            # Также проверяем флаги в JSON-данных запроса, если это возможно
            if hasattr(request, 'dict') and callable(request.dict):
                request_data = request.dict()
                if 'with_points' in request_data:
                    with_points = request_data['with_points']
                if 'skip_tariff_check' in request_data:
                    skip_tariff_check = request_data['skip_tariff_check']
                if 'skip_limits' in request_data:
                    skip_limits = request_data['skip_limits']

            # Если генерация за баллы или нужно пропустить проверку тарифа/лимитов, пропускаем проверку лимитов и тарифа
            if with_points or skip_tariff_check or skip_limits:
                logger.info(f"Generation with points or skip_tariff_check/skip_limits requested, skipping limit and tariff checks")
                return await func(request, session, *args, **kwargs)

            # Extract user_id from the request object or from current_user
            user_id = None

            # Пытаемся получить current_user из kwargs
            current_user = kwargs.get('current_user')
            if current_user and hasattr(current_user, 'id'):
                # Если есть current_user, используем его id
                user_id = current_user.id
            elif hasattr(request, 'user_id') and request.user_id is not None:
                # Если нет current_user, но есть request.user_id
                user_id = request.user_id
            else:
                logger.error("No user_id available in request and no current_user found")
                raise HTTPException(status_code=401, detail="User authentication required")

            # Check unlimited access (admins and friends)
            is_unlimited = await check_unlimited_access(user_id, session)

            if is_unlimited:
                return await func(request, session, *args, **kwargs)
            # Get daily usage
            stmt = select(DailyUsage).where(
                DailyUsage.user_id == user_id,
                DailyUsage.date == datetime.now(timezone.utc).date()
            )
            result = await session.execute(stmt)
            daily_usage = result.scalar_one_or_none()

            if not daily_usage:
                daily_usage = DailyUsage(user_id=user_id)
                session.add(daily_usage)
                await session.flush()


            # Check limits using the current_user object from kwargs
            user = current_user # Используем пользователя, полученного из зависимости/kwargs

            # Проверяем, что current_user - это объект User и у него есть тариф
            if not user:
                logger.error(f"ORIGINAL DECORATOR - current_user is None. Cannot check tariff.")
                # Если current_user отсутствует, пытаемся получить пользователя из базы данных
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    logger.error(f"ORIGINAL DECORATOR - Failed to get user from database for user_id {user_id}")
                    raise HTTPException(status_code=500, detail="Internal server error: User not found")

            if not isinstance(user, User):
                logger.error(f"ORIGINAL DECORATOR - current_user is not a User instance, but {type(user)}. Cannot check tariff.")
                raise HTTPException(status_code=500, detail="Internal server error: Invalid user object")

            # --- ЛОГИРОВАНИЕ УДАЛЕНО ---


            if not user.tariff:
                logger.warning(f"ORIGINAL DECORATOR - No active tariff found for user {user_id} in current_user object.")
                raise HTTPException(status_code=403, detail="No active tariff")

            # Используем user.tariff (из current_user) для получения лимитов
            limit_key = user.tariff
            limits = TARIFF_LIMITS.get(limit_key)

            if not limits:
                 logger.error(f"ORIGINAL DECORATOR - Could not find limits for tariff key: {limit_key} (type: {type(limit_key)}). User tariff value: {user.tariff}")
                 limits = TARIFF_LIMITS.get(str(user.tariff)) # Попытка со строкой
                 if not limits:
                     logger.error(f"ORIGINAL DECORATOR - Still could not find limits for tariff string value: {str(user.tariff)}")
                     raise HTTPException(status_code=500, detail=f"Tariff limits not configured for {user.tariff}")

            if content_type == ContentType.IMAGE:
                if daily_usage.images_count >= limits.daily_images:
                    logger.warning(f"Daily image limit exceeded for user {user_id}")
                    raise HTTPException(status_code=429, detail="Daily image limit exceeded")
            else:
                if daily_usage.generations_count >= limits.daily_generations:
                    logger.warning(f"Daily generation limit exceeded for user {user_id}")
                    raise HTTPException(status_code=429, detail="Daily generation limit exceeded")

            # Call the original function
            result = await func(request, session, *args, **kwargs)

            # --- УДАЛЕНА ЛОГИКА ОБНОВЛЕНИЯ СЧЕТЧИКОВ ---
            # Декоратор теперь только проверяет лимиты ДО вызова функции

            return result # Возвращаем результат основной функции

        return wrapper

    return decorator


def check_achievements(action_type: str, content_type: ContentType):
    """Decorator for checking achievements after generation that works with request objects"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request, session: AsyncSession, *args: Any, **kwargs: Any) -> Any:
            # Extract user_id from the request object or from current_user
            user_id = None

            # Пытаемся получить current_user из kwargs
            current_user = kwargs.get('current_user')
            if current_user and hasattr(current_user, 'id'):
                # Если есть current_user, используем его id
                user_id = current_user.id
            elif hasattr(request, 'user_id') and request.user_id is not None:
                # Если нет current_user, но есть request.user_id
                user_id = request.user_id
            else:
                logger.error("No user_id available in request and no current_user found")
                raise HTTPException(status_code=401, detail="User authentication required")

            # Call the original function
            result = await func(request, session, *args, **kwargs)

            # Check achievements
            try:
                async with AchievementManager(session) as achievement_manager:
                    await achievement_manager.check_achievements(
                        user_id=user_id,
                        action_type=action_type,
                        action_data={
                            'content_type': content_type.value,
                            'success': True
                        }
                    )
            except Exception as e:
                logger.error(f"Error checking achievements: {str(e)}")
                # Don't fail the request if achievements check fails

            return result

        return wrapper

    return decorator


def track_usage(content_type: ContentType):
    """Decorator for tracking usage that works with request objects"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request, session: AsyncSession, *args: Any, **kwargs: Any) -> Any:
            # Extract user_id from the request object or from current_user
            user_id = None

            # Пытаемся получить current_user из kwargs
            current_user = kwargs.get('current_user')
            if current_user and hasattr(current_user, 'id'):
                # Если есть current_user, используем его id
                user_id = current_user.id
            elif hasattr(request, 'user_id') and request.user_id is not None:
                # Если нет current_user, но есть request.user_id
                user_id = request.user_id
            else:
                logger.error("No user_id available in request and no current_user found")
                raise HTTPException(status_code=401, detail="User authentication required")

            # Проверяем, используются ли баллы для генерации или нужно пропустить проверку тарифа
            with_points = False
            skip_limits = False
            skip_tariff_check = False

            # Проверяем флаги в request
            if hasattr(request, 'with_points'):
                with_points = request.with_points
            if hasattr(request, 'skip_limits'):
                skip_limits = request.skip_limits
            if hasattr(request, 'skip_tariff_check'):
                skip_tariff_check = request.skip_tariff_check

            # Также проверяем флаги в JSON-данных запроса, если это возможно
            if hasattr(request, 'dict') and callable(request.dict):
                request_data = request.dict()
                if 'with_points' in request_data:
                    with_points = request_data['with_points']
                if 'skip_tariff_check' in request_data:
                    skip_tariff_check = request_data['skip_tariff_check']

            # Если указан skip_tariff_check, то также пропускаем лимиты
            if skip_tariff_check:
                skip_limits = True
                if 'skip_limits' in request_data:
                    skip_limits = request_data['skip_limits']

            # Call the original function
            result = await func(request, session, *args, **kwargs)

            # Log usage
            try:
                extra_data = kwargs.get('extra_data', {})

                # Добавляем информацию о генерации за баллы и пропуске проверки тарифа в extra_data
                if with_points:
                    extra_data['with_points'] = True
                if skip_limits:
                    extra_data['skip_limits'] = True
                if skip_tariff_check:
                    extra_data['skip_tariff_check'] = True

                async with UsageTracker(session) as usage_tracker:
                    await usage_tracker.log_usage(UsageLogCreate(
                        user_id=user_id,
                        action_type="generation",
                        content_type=content_type.value,
                        extra_data=extra_data,
                        skip_limits=skip_limits or with_points or skip_tariff_check  # Пропускаем лимиты, если генерация за баллы или пропуск проверки тарифа
                    ))
            except Exception as e:
                logger.error(f"Error tracking usage: {str(e)}")
                # Don't fail the request if usage tracking fails

            return result

        return wrapper

    return decorator


def track_feature_usage(feature_type: str, content_type: Optional[ContentType] = None):
    """Decorator for tracking feature usage that works with request objects"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request, session: AsyncSession, *args: Any, **kwargs: Any) -> Any:
            # Extract user_id from the request object or from current_user
            user_id = None

            # Пытаемся получить current_user из kwargs
            current_user = kwargs.get('current_user')
            if current_user and hasattr(current_user, 'id'):
                # Если есть current_user, используем его id
                user_id = current_user.id
            elif hasattr(request, 'user_id') and request.user_id is not None:
                # Если нет current_user, но есть request.user_id
                user_id = request.user_id
            else:
                logger.error("No user_id available in request and no current_user found")
                raise HTTPException(status_code=401, detail="User authentication required")

            # Convert ContentType enum to string value if provided
            content_type_str = content_type.value if content_type else None

            try:
                # Call the original function
                result = await func(request, session, *args, **kwargs)

                # Record successful usage
                try:
                    # Import inside to avoid circular imports
                    from ..services.analytics import FeatureUsageService
                    # Create the service directly with the session
                    feature_service = FeatureUsageService(session)
                    # Используем отдельную сессию для логирования, чтобы не влиять на основную транзакцию
                    await feature_service.track_feature_usage(
                        user_id=user_id,
                        feature_type=feature_type,
                        content_type=content_type_str,
                        success=True,
                        usage_data={
                            "request_data": request.dict() if hasattr(request, 'dict') else {"message": "Request has no dict method"},
                            "response_status": "success"
                        }
                    )
                except Exception as tracking_error: # Changed variable name for clarity
                    logger.error(f"Error tracking successful feature usage: {str(tracking_error)}")
                    # Don't fail the request if feature tracking fails

                return result
            except Exception as e: # This is the outer exception handler
                # Record failed usage
                if session: # Check if session exists before using it
                    try:
                        # Import inside to avoid circular imports
                        from ..services.analytics import FeatureUsageService
                        # Create the service directly with the session
                        feature_service = FeatureUsageService(session)
                        # Используем отдельную сессию для логирования, чтобы не влиять на основную транзакцию
                        await feature_service.track_feature_usage(
                            user_id=user_id,
                            feature_type=feature_type,
                            content_type=content_type_str,
                            success=False,
                            usage_data={
                                "request_data": request.dict() if hasattr(request, 'dict') else {"message": "Request has no dict method"},
                                "response_status": "error",
                                "error": str(e)
                            }
                        )
                    except Exception as tracking_error:
                        logger.error(f"Error recording feature usage failure: {str(tracking_error)}")
                        # Don't swallow the original exception

                # Re-raise the original exception 'e' after attempting to log
                raise # Correctly aligned with the 'except Exception as e:' line

        return wrapper

    return decorator
