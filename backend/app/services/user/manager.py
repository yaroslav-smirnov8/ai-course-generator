# app/services/user/manager.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import logging
import json
from ...core.config import settings

from ...repositories.user import UserRepository
from ...models.user import User
from ..base import BaseService
from ...core.constants import UserRole
from ...core.exceptions import NotFoundException
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
from ...core.cache import cache_service
from ...core.memory import memory_optimized

logger = logging.getLogger(__name__)


class UserManager(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserRepository)
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session)
        self.cache_service = cache_service

    @memory_optimized()
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id с кэшированием"""
        try:
            # --- ВОЗВРАЩАЕМ КЭШИРОВАНИЕ ---
            cache_key = f"user:telegram:{telegram_id}"
            cached_user = await self.cache_service.get_cached_data(cache_key)
            if cached_user:
                 logger.info(f"Returning cached user for telegram_id: {telegram_id}")
                 return cached_user
            logger.info(f"Cache miss for user telegram_id: {telegram_id}")
            # --- КОНЕЦ ВОЗВРАТА КЭШИРОВАНИЯ ---

            # Если нет в кэше, получаем из БД
            query = select(User).where(User.telegram_id == telegram_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            # --- ВОЗВРАЩАЕМ КЭШИРОВАНИЕ ---
            if user:
                 # Кэшируем результат
                 logger.info(f"Caching user data for telegram_id: {telegram_id}")
                 await self.cache_service.cache_data(cache_key, user, ttl=3600)
            # --- КОНЕЦ ВОЗВРАТА КЭШИРОВАНИЯ ---

            return user

        except Exception as e:
            logger.error(f"Error getting user by telegram_id: {str(e)}")
            raise

    @memory_optimized()
    async def create_telegram_user(self, telegram_data: dict) -> User:
        """Создание пользователя через Telegram с оптимизацией"""
        try:
            logger.debug(f"Creating user with data: {telegram_data}")

            # Получаем telegram_id из данных (может быть как id, так и telegram_id)
            telegram_id = telegram_data.get('telegram_id') or telegram_data.get('id')

            if not telegram_id:
                raise ValueError("telegram_id is required")

            # Сначала проверяем в кэше
            cache_key = f"user:telegram:{telegram_id}"
            cached_user = await self.cache_service.get_cached_data(cache_key)
            if cached_user:
                return cached_user

            # Проверяем существующего пользователя в БД
            existing_user = await self.get_by_telegram_id(telegram_id)

            user_role = UserRole.USER  # По умолчанию
            if telegram_data["telegram_id"] == settings.ADMIN_ID:
                user_role = UserRole.ADMIN
            elif telegram_data["telegram_id"] == settings.MOD_ID:
                user_role = UserRole.MOD

            logger.debug(f"Existing user check result: {existing_user}")

            if existing_user:
                return existing_user

            try:
                # Генерируем уникальный инвайт-код
                invite_code = await self._generate_unique_invite_code()

                user = User(
                    telegram_id=telegram_id,
                    username=telegram_data.get("username"),
                    first_name=telegram_data.get("first_name", ""),
                    last_name=telegram_data.get("last_name"),
                    language_code=telegram_data.get("language_code"),
                    is_premium=telegram_data.get("is_premium", False),
                    platform=telegram_data.get("platform"),
                    webapp_version=telegram_data.get("webapp_version"),
                    role=user_role,
                    has_access=True,
                    invite_code=invite_code
                )

                self.session.add(user)
                await self.session.commit()
                await self.session.refresh(user)

                # Кэшируем нового пользователя
                await self.cache_service.cache_data(cache_key, user, ttl=3600)

                logger.info(f"Successfully created user with id: {user.id}")
                return user

            except Exception as e:
                logger.error(f"Database error creating user: {str(e)}")
                await self.session.rollback()
                raise

        except Exception as e:
            logger.error(f"Error in create_telegram_user: {str(e)}")
            raise

    async def update_last_active(self, user_id: int) -> None:
        """Обновление времени последней активности с оптимизацией"""
        try:
            user = await self.get(user_id)
            if not user:
                raise NotFoundException(f"User {user_id} not found")

            user.last_active = datetime.now(timezone.utc)
            await self.session.commit()

            # Инвалидируем кэш пользователя
            cache_key = f"user:telegram:{user.telegram_id}"
            await self.cache_service.invalidate_pattern(cache_key)
        except Exception as e:
            logger.error(f"Error updating last active: {str(e)}")
            await self.session.rollback()
            raise

    @memory_optimized()
    async def process_invite(self, invite_code: str, telegram_id: int) -> Optional[User]:
        """Обработка инвайт-кода с оптимизацией"""
        try:
            user = await self.get_by_telegram_id(telegram_id)
            if not user:
                return None

            if invite_code and not user.invited_by_code:
                user.invited_by_code = invite_code
                user.total_earned_discount += 1  # Бонус для приглашенного

                # Находим пригласившего пользователя
                inviter = await self.repository.get_by_field("invite_code", invite_code)
                if inviter:
                    inviter.invites_count += 1
                    inviter.total_earned_discount += 2  # Бонус для пригласившего

                    # Обновляем обоих пользователей одной транзакцией
                    await self.session.commit()

                    # Инвалидируем кэш для обоих пользователей
                    await self.cache_service.invalidate_pattern(f"user:telegram:{user.telegram_id}")
                    await self.cache_service.invalidate_pattern(f"user:telegram:{inviter.telegram_id}")

            return user
        except Exception as e:
            logger.error(f"Error processing invite: {str(e)}")
            await self.session.rollback()
            raise

    @memory_optimized()
    async def get_user_statistics(self, user_id: int) -> dict:
        """Получение статистики пользователя с оптимизацией"""
        try:
            # Проверяем кэш
            cache_key = f"user:stats:{user_id}"
            cached_stats = await self.cache_service.get_cached_data(cache_key)
            if cached_stats:
                return cached_stats

            user = await self.get(user_id)
            if not user:
                raise NotFoundException(f"User {user_id} not found")

            # Оптимизируем запросы с помощью QueryOptimizer
            stats_query = await self.query_optimizer.optimize_query(
                select([
                    func.count(User.id).label('total_invites'),
                    User.total_earned_discount,
                    User.tariff,
                    User.points,
                    User.has_access
                ]).where(User.id == user_id)
            )

            result = await self.session.execute(stats_query)
            stats = result.first()

            statistics = {
                "total_invites": stats.total_invites,
                "total_discount": stats.total_earned_discount,
                "current_tariff": stats.tariff.value if stats.tariff else None,
                "points": stats.points,
                "is_active": stats.has_access
            }

            # Кэшируем результат
            await self.cache_service.cache_data(cache_key, statistics, ttl=300)  # 5 минут

            return statistics
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            raise

    @memory_optimized()
    async def get_many(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение списка пользователей с пагинацией и логированием"""
        try:
            logger.info(f"UserManager.get_many called with skip={skip}, limit={limit}")

            # Проверяем кэш
            cache_key = f"users:list:{skip}:{limit}"
            cached_users = await self.cache_service.get_cached_data(cache_key)
            if cached_users:
                logger.info(f"Returning {len(cached_users)} users from cache")
                return cached_users

            # Оптимизируем запрос
            logger.info("Cache miss, executing database query")
            query = await self.query_optimizer.optimize_query(
                select(User)
                .order_by(User.id)
                .offset(skip)
                .limit(limit)
            )

            logger.info(f"Executing query: {str(query)}")
            result = await self.session.execute(query)
            users = result.scalars().all()

            # Логируем результаты
            logger.info(f"Query returned {len(users)} users")
            if users:
                logger.info(f"First user: id={users[0].id}, telegram_id={users[0].telegram_id}, role={users[0].role}")
                logger.info(f"User attributes: {dir(users[0])}")

            # Кэшируем результат
            await self.cache_service.cache_data(cache_key, users, ttl=300)  # 5 минут

            return users
        except Exception as e:
            logger.error(f"Error in get_many: {str(e)}", exc_info=True)
            raise

    async def get_active_users_count(self) -> int:
        """Получение количества активных пользователей с оптимизацией"""
        try:
            # Проверяем кэш
            cache_key = "users:active:count"
            cached_count = await self.cache_service.get_cached_data(cache_key)
            if cached_count is not None:
                logger.info(f"Returning active users count from cache: {cached_count}")
                return cached_count

            # Оптимизируем запрос
            logger.info("Cache miss for active users count, executing database query")
            query = await self.query_optimizer.optimize_query(
                select(func.count(User.id)).where(User.has_access == True)
            )
            result = await self.session.execute(query)
            count = result.scalar()

            logger.info(f"Active users count from database: {count}")

            # Кэшируем результат
            await self.cache_service.cache_data(cache_key, count, ttl=300)  # 5 минут

            return count
        except Exception as e:
            logger.error(f"Error getting active users count: {str(e)}", exc_info=True)
            raise

    @memory_optimized()
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Получение пользователей по роли с оптимизацией"""
        try:
            # Проверяем кэш
            cache_key = f"users:role:{role.value}"
            cached_users = await self.cache_service.get_cached_data(cache_key)
            if cached_users:
                return cached_users

            # Оптимизируем запрос
            query = await self.query_optimizer.optimize_query(
                select(User).where(User.role == role)
            )
            result = await self.session.execute(query)
            users = result.scalars().all()

            # Кэшируем результат
            await self.cache_service.cache_data(cache_key, users, ttl=300)

            return users
        except Exception as e:
            logger.error(f"Error getting users by role: {str(e)}")
            raise

    @memory_optimized()
    async def get_users_with_valid_tariff(self) -> List[User]:
        """Получение пользователей с активным тарифом"""
        try:
            # Проверяем кэш
            cache_key = "users:valid_tariff"
            cached_users = await self.cache_service.get_cached_data(cache_key)
            if cached_users:
                return cached_users

            # Оптимизируем запрос
            query = await self.query_optimizer.optimize_query(
                select(User).where(
                    and_(
                        User.tariff.isnot(None),
                        User.tariff_valid_until > datetime.now(timezone.utc)
                    )
                )
            )
            result = await self.session.execute(query)
            users = result.scalars().all()

            # Кэшируем результат
            await self.cache_service.cache_data(cache_key, users, ttl=300)

            return users
        except Exception as e:
            logger.error(f"Error getting users with valid tariff: {str(e)}")
            raise

    async def set_user_role(self, user_id: int, role: UserRole) -> Optional[User]:
        """Установка роли пользователя с оптимизацией"""
        try:
            user = await self.get(user_id)
            if not user:
                raise NotFoundException(f"User {user_id} not found")

            user.role = role
            await self.session.commit()

            # Инвалидируем связанные кэши
            await self.cache_service.invalidate_pattern(f"user:telegram:{user.telegram_id}")
            await self.cache_service.invalidate_pattern(f"user:stats:{user_id}") # Также инвалидируем кэш статистики
            await self.cache_service.invalidate_pattern("users:role:*")

            return user
        except Exception as e:
            logger.error(f"Error setting user role: {str(e)}")
            await self.session.rollback()
            raise

    async def has_unlimited_access(self, user_id: int) -> bool:
        """Проверка безлимитного доступа"""
        user = await self.get(user_id)
        if not user:
            return False

        return user.role in [UserRole.ADMIN, UserRole.FRIEND, UserRole.MOD]

    async def bulk_update_users(self, user_updates: List[dict]) -> None:
        """Массовое обновление пользователей с батч-процессингом"""
        try:
            await self.batch_processor.process_in_batches(
                user_updates,
                self._process_user_update_batch
            )

            # Инвалидируем все кэши пользователей
            await self.cache_service.invalidate_pattern("user:*")
        except Exception as e:
            logger.error(f"Error in bulk user update: {str(e)}")
            raise

    async def _process_user_update_batch(self, batch: List[dict]) -> None:
        """Обработка батча обновлений пользователей"""
        try:
            for update in batch:
                user_id = update.pop('id')
                user = await self.get(user_id)
                if user:
                    for key, value in update.items():
                        setattr(user, key, value)

            await self.session.commit()
        except Exception as e:
            logger.error(f"Error processing user update batch: {str(e)}")
            await self.session.rollback()
            raise

    async def update_telegram_data(self, user_id: int, telegram_data: dict):
        user = await self.get(user_id)
        if user:
            user.username = telegram_data.get('username')
            user.first_name = telegram_data.get('first_name')
            user.last_name = telegram_data.get('last_name')
            user.language_code = telegram_data.get("language_code")
            user.is_premium = telegram_data.get("is_premium")
            await self.session.commit()

    async def handle_telegram_revoke(self, telegram_id: int):
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.has_access = False
            await self.update(user.id, {"has_access": False})
            # Инвалидируем кэш при отзыве доступа
            await self.invalidate_cache_by_telegram_id(telegram_id)
            if user:
                 await self.cache_service.invalidate_pattern(f"user:stats:{user.id}")


    async def invalidate_cache_by_telegram_id(self, telegram_id: int):
        """Инвалидация кэша пользователя по telegram_id"""
        cache_key_user = f"user:telegram:{telegram_id}"
        await self.cache_service.invalidate(cache_key_user)
        logger.debug(f"Invalidated user cache for telegram_id: {telegram_id}")
        # Потенциально нужно инвалидировать и другие связанные кэши, если они есть
        # Например, кэш статистики, если он зависит от данных пользователя
        # user = await self.get_by_telegram_id(telegram_id) # Осторожно, рекурсия или лишний запрос
        # if user:
        #     cache_key_stats = f"user:stats:{user.id}"
        #     await self.cache_service.invalidate(cache_key_stats)


    async def _generate_unique_invite_code(self) -> str:
        """Генерирует уникальный инвайт-код"""
        import uuid
        max_attempts = 5

        for attempt in range(max_attempts):
            invite_code = str(uuid.uuid4())[:8]

            # Проверяем уникальность
            result = await self.session.execute(
                select(User).where(User.invite_code == invite_code)
            )
            if not result.scalar_one_or_none():
                return invite_code

        raise Exception("Failed to generate unique invite code")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
