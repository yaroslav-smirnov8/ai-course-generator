from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import asyncio
import logging

from ...models import TariffPlan, PriceChange, UserTariff, User, PointTransaction, DailyUsage
from ...core.constants import TariffType
from ...core.cache import CacheService
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
from ...schemas.pricing import TariffInfo
from ...services.user import UserManager
from ...services.points import PointsManager

logger = logging.getLogger(__name__)


class TariffManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache = CacheService()
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session, batch_size=100)
        self.user_service = UserManager(session)
        self.points_service = PointsManager(session)

        # Ключи кэширования
        self._cache_keys = {
            'tariff_list': 'tariffs:list',
            'user_tariff': 'user:{}:tariff',
            'tariff_stats': 'tariffs:stats',
            'price_history': 'tariff:{}:price_history'
        }
        self._cache_ttl = {
            'tariff_list': 3600,  # 1 час
            'user_tariff': 300,  # 5 минут
            'tariff_stats': 1800,  # 30 минут
            'price_history': 86400  # 24 часа
        }

    async def get_active_tariffs(self) -> List[TariffPlan]:
        """Получение списка активных тарифов с кэшированием"""
        cache_key = self._cache_keys['tariff_list']
        cached_tariffs = await self.cache.get_cached_data(cache_key)

        if cached_tariffs:
            return cached_tariffs

        try:
            # Используем оптимизированный запрос
            query = await self.query_optimizer.optimize_query(
                select(TariffPlan)
                .where(TariffPlan.is_active == True)
                .order_by(TariffPlan.price_points)
            )

            result = await self.session.execute(query)
            tariffs = result.scalars().all()

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                tariffs,
                ttl=self._cache_ttl['tariff_list']
            )

            return tariffs
        except Exception as e:
            logger.error(f"Error getting active tariffs: {e}")
            raise

    def _get_tariff_tier(self, tariff_type: TariffType) -> int:
        """Get numerical tier for tariff comparison"""
        tiers = {
            TariffType.FREE: 0,
            TariffType.BASIC: 1,
            TariffType.STANDARD: 2,
            TariffType.PREMIUM: 3
        }
        return tiers.get(tariff_type, 0)

    async def get_available_tariffs(self) -> List[TariffInfo]:
        """Получить список доступных тарифов"""
        try:
            tariffs = await self.get_active_tariffs()

            # Преобразуем к формату TariffInfo
            tariff_info_list = []
            for tariff in tariffs:
                tariff_info = TariffInfo(
                    type=tariff.type,
                    validUntil=None,
                    limits={
                        "generations": tariff.generations_limit,
                        "images": tariff.images_limit
                    },
                    pricePoints=tariff.price_points,
                    features=tariff.features,
                    name=tariff.name
                )
                tariff_info_list.append(tariff_info)

            return tariff_info_list
        except Exception as e:
            logger.error(f"Error getting available tariffs: {e}")
            raise

    async def purchase_tariff(self, user_id: int, tariff_type: TariffType) -> bool:
        """Purchase a tariff for the user"""
        try:
            # Получаем пользователя
            user = await self.user_service.get(user_id) # Исправлено: get_user_by_id -> get
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            # Получаем текущий тариф пользователя
            current_tariff = await self.get_tariff_info(user_id) # Исправлено: get_user_tariff -> get_tariff_info

            # Получаем новый тариф
            new_tariff_query = select(TariffPlan).where(TariffPlan.type == tariff_type) # Исправлено: get_tariff_by_type -> прямой запрос
            new_tariff_result = await self.session.execute(new_tariff_query)
            new_tariff = new_tariff_result.scalar_one_or_none()
            if not new_tariff:
                logger.error(f"Tariff {tariff_type} not found")
                return False

            # Проверяем, что новый тариф отличается от текущего
            # Проверяем, что новый тариф отличается от текущего
            if current_tariff and current_tariff.type == new_tariff.type: # Сравниваем по типу тарифа
                # Return a more specific error for duplicate purchase attempts
                logger.warning(f"User {user_id} already has tariff {tariff_type}")
                return False

            # Проверяем, что новый тариф выше текущего
            if current_tariff:
                # Используем метод _get_tariff_tier для сравнения уровней тарифов
                current_tier = self._get_tariff_tier(current_tariff.type)
                new_tier = self._get_tariff_tier(tariff_type)

                if current_tier >= new_tier:
                    logger.warning(f"User {user_id} trying to downgrade from {current_tariff.type} (tier {current_tier}) to {tariff_type} (tier {new_tier})")
                    # TODO: Consider raising a specific exception or returning a structured error
                    return False

            # Тарифы покупаются через кассу, проверка баллов НЕ требуется
            logger.info(f"Tariff purchase initiated for user {user_id}: {new_tariff.name} (will be paid via external cashier)")

            # Создаем запись о тарифе пользователя
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=30)

            # Временное решение: проверяем, поддерживает ли база данных timezone-aware значения для expires_at
            try:
                user_tariff = UserTariff(
                    user_id=user_id,
                    tariff_id=new_tariff.id,
                    started_at=now,
                    expires_at=expires_at,
                    is_active=True
                )
            except Exception as e:
                logger.warning(f"Error creating UserTariff with timezone-aware expires_at: {e}")
                logger.warning("Trying to create UserTariff with timezone-naive expires_at")

                # Если не поддерживает, преобразуем timezone-aware в timezone-naive
                user_tariff = UserTariff(
                    user_id=user_id,
                    tariff_id=new_tariff.id,
                    started_at=now,
                    expires_at=expires_at.replace(tzinfo=None),  # Удаляем информацию о часовом поясе
                    is_active=True
                )

            # Тарифы покупаются через кассу, баллы НЕ списываем

            # Обновляем поля пользователя
            user.tariff = tariff_type
            user.tariff_valid_until = user_tariff.expires_at # Исправлено: end_date -> expires_at

            # Сбрасываем счетчики дневного использования при покупке нового тарифа
            # Это позволит пользователю сразу начать использовать новый тариф с полными лимитами
            reset_success = False

            try:
                # Используем отдельную сессию для сброса счетчиков
                from sqlalchemy.ext.asyncio import AsyncSession
                from ...core.database import engine
                from ...core.limits import reset_daily_usage_counters

                # Создаем новую сессию для сброса счетчиков
                async with AsyncSession(engine) as reset_session:
                    logger.info(f"Resetting daily usage counters for user {user_id} in separate transaction")
                    reset_success = await reset_daily_usage_counters(user_id, reset_session)
                    if reset_success:
                        logger.info(f"Successfully reset daily usage counters for user {user_id} in separate transaction")
                    else:
                        logger.warning(f"Failed to reset daily usage counters for user {user_id} in separate transaction")
            except Exception as session_error:
                logger.error(f"Error creating session for counter reset: {str(session_error)}", exc_info=True)
                # Продолжаем выполнение даже при ошибке создания сессии

            # Если сброс счетчиков в отдельной транзакции не удался, пробуем сбросить их в текущей транзакции
            if not reset_success:
                logger.warning(f"Attempting to reset counters in main transaction for user {user_id}")
                try:
                    from ...core.limits import reset_daily_usage_counters
                    reset_success = await reset_daily_usage_counters(user_id, self.session)
                    if reset_success:
                        logger.info(f"Successfully reset daily usage counters for user {user_id} in main transaction")
                    else:
                        logger.warning(f"Failed to reset daily usage counters for user {user_id} in main transaction")
                except Exception as e:
                    logger.error(f"Error resetting counters in main transaction: {str(e)}", exc_info=True)
                    # Продолжаем выполнение даже при ошибке сброса счетчиков

            # Сохраняем запись о тарифе и обновляем пользователя
            self.session.add(user_tariff)
            await self.session.commit()
            await self.session.refresh(user) # Обновляем объект пользователя

            # Инвалидируем кэши пользователя ПОСЛЕ коммита
            await self.invalidate_user_cache(user_id) # Инвалидирует 'user:{}:tariff'
            if user.telegram_id: # Добавлено: Инвалидируем основной кэш пользователя по telegram_id
                await self.user_service.invalidate_cache_by_telegram_id(user.telegram_id)
                # Также инвалидируем кэш статистики, т.к. тариф изменился
                await self.cache.invalidate(f"user:stats:{user_id}")


            # Отслеживаем покупку в аналитике
            try:
                from ..analytics import OptimizedAnalyticsService
                analytics_service = OptimizedAnalyticsService(self.session)
                await analytics_service.track_purchase(
                    user_id=user_id,
                    purchase_type="tariff",
                    amount=new_tariff.price_points, # Исправлено: price -> price_points
                    item_id=str(new_tariff.id),
                    item_name=new_tariff.name,
                    metadata={
                        "tariff_type": tariff_type.value, # Исправлено: передаем строковое значение Enum
                        "tariff_level": self._get_tariff_tier(tariff_type),
                        "generations_limit": new_tariff.generations_limit,
                        "images_limit": new_tariff.images_limit
                    }
                )
            except Exception as e:
                logger.error(f"Error tracking tariff purchase: {str(e)}")

            logger.info(f"User {user_id} purchased tariff {tariff_type}")
            return True

        except Exception as e:
            logger.error(f"Error purchasing tariff: {str(e)}")
            await self.session.rollback()
            return False

    async def update_user_tariff(
            self,
            user_id: int,
            tariff_type: TariffType,
            admin_override: bool = False
    ) -> bool:
        """Обновить тариф пользователя (для админов или при покупке)"""
        try:
            # Получаем пользователя и тариф
            user = await self.session.get(User, user_id)
            if not user:
                return False

            tariff_query = select(TariffPlan).where(
                and_(
                    TariffPlan.type == tariff_type,
                    TariffPlan.is_active == True
                )
            )
            tariff_result = await self.session.execute(tariff_query)
            tariff = tariff_result.scalar_one_or_none()

            if not tariff:
                return False

            # Для админов позволяем обновлять без списания баллов
            if admin_override:
                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(days=30)

                # Временное решение: проверяем, поддерживает ли база данных timezone-aware значения для expires_at
                try:
                    user_tariff = UserTariff(
                        user_id=user_id,
                        tariff_id=tariff.id,
                        started_at=now,
                        expires_at=expires_at
                    )
                except Exception as e:
                    logger.warning(f"Error creating UserTariff with timezone-aware expires_at: {e}")
                    logger.warning("Trying to create UserTariff with timezone-naive expires_at")

                    # Если не поддерживает, преобразуем timezone-aware в timezone-naive
                    user_tariff = UserTariff(
                        user_id=user_id,
                        tariff_id=tariff.id,
                        started_at=now,
                        expires_at=expires_at.replace(tzinfo=None)  # Удаляем информацию о часовом поясе
                    )

                user.tariff = tariff_type
                user.tariff_valid_until = user_tariff.expires_at

                self.session.add(user_tariff)
                await self.session.commit()

                # Инвалидируем кэш
                await self.invalidate_user_cache(user_id)
                return True
            else:
                # Для обычных пользователей используем purchase_tariff
                return await self.purchase_tariff(user_id, tariff_type)

        except Exception as e:
            logger.error(f"Error updating user tariff: {e}")
            await self.session.rollback()
            raise

    async def get_tariff_info(self, user_id: int) -> Optional[TariffInfo]:
        """Получить информацию о тарифе пользователя"""
        cache_key = self._cache_keys['user_tariff'].format(user_id)
        cached_tariff = await self.cache.get_cached_data(cache_key)

        if cached_tariff:
            return cached_tariff

        try:
            query = select(User).where(User.id == user_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if not user or not user.tariff:
                return None

            # Получаем информацию о тарифе
            tariff_query = select(TariffPlan).where(TariffPlan.type == user.tariff)
            tariff_result = await self.session.execute(tariff_query)
            tariff = tariff_result.scalar_one_or_none()

            if not tariff:
                return None

            tariff_info = TariffInfo(
                type=tariff.type,
                validUntil=user.tariff_valid_until,
                limits={
                    "generations": tariff.generations_limit,
                    "images": tariff.images_limit
                },
                pricePoints=tariff.price_points,
                features=tariff.features,
                name=tariff.name
            )

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                tariff_info,
                ttl=self._cache_ttl['user_tariff']
            )

            return tariff_info

        except Exception as e:
            logger.error(f"Error getting tariff info: {e}")
            raise

    async def check_tariff_validity(self, user_id: int) -> bool:
        """Проверить активность тарифа пользователя"""
        try:
            query = select(User).where(User.id == user_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if not user or not user.tariff or not user.tariff_valid_until:
                return False

            return user.tariff_valid_until > datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Error checking tariff validity: {e}")
            return False

    async def get_tariff_history(self, user_id: int, limit: int = 10) -> List:
        """Получить историю тарифов пользователя"""
        try:
            query = select(UserTariff).where(
                UserTariff.user_id == user_id
            ).order_by(
                desc(UserTariff.started_at)
            ).limit(limit)

            result = await self.session.execute(query)
            history = result.scalars().all()

            return history
        except Exception as e:
            logger.error(f"Error getting tariff history: {e}")
            raise

    async def extend_tariff(self, user_id: int, months: int = 1) -> bool:
        """Продлить текущий тариф пользователя"""
        try:
            user = await self.session.get(User, user_id)
            if not user or not user.tariff or not user.tariff_valid_until:
                return False

            # Получаем тариф
            tariff_query = select(TariffPlan).where(TariffPlan.type == user.tariff)
            tariff_result = await self.session.execute(tariff_query)
            tariff = tariff_result.scalar_one_or_none()

            if not tariff:
                return False

            # Продление тарифа происходит через кассу, не через баллы
            logger.info(f"Tariff extension for user {user_id} for {months} months")

            # Обновляем срок действия тарифа
            now = datetime.now(timezone.utc)
            if user.tariff_valid_until < now:
                # Если тариф уже истек, начинаем с текущей даты
                user.tariff_valid_until = now + timedelta(days=30 * months)
            else:
                # Иначе добавляем к текущему сроку
                user.tariff_valid_until += timedelta(days=30 * months)

            # Создаем запись о продлении тарифа
            expires_at = user.tariff_valid_until

            # Временное решение: проверяем, поддерживает ли база данных timezone-aware значения для expires_at
            try:
                user_tariff = UserTariff(
                    user_id=user_id,
                    tariff_id=tariff.id,
                    started_at=now,
                    expires_at=expires_at
                )
            except Exception as e:
                logger.warning(f"Error creating UserTariff with timezone-aware expires_at: {e}")
                logger.warning("Trying to create UserTariff with timezone-naive expires_at")

                # Если не поддерживает, преобразуем timezone-aware в timezone-naive
                user_tariff = UserTariff(
                    user_id=user_id,
                    tariff_id=tariff.id,
                    started_at=now,
                    expires_at=expires_at.replace(tzinfo=None)  # Удаляем информацию о часовом поясе
                )

            # Выполняем обновления (без списания баллов)
            self.session.add(user_tariff)

            await self.session.commit()

            # Инвалидируем кэш
            await self.invalidate_user_cache(user_id)

            return True

        except Exception as e:
            logger.error(f"Error extending tariff: {e}")
            await self.session.rollback()
            raise

    async def process_price_changes(self) -> int:
        """Пакетная обработка изменений цен"""
        try:
            # Получаем все запланированные изменения цен
            now = datetime.now(timezone.utc)
            query = select(PriceChange).where(
                and_(
                    PriceChange.scheduled_date <= now,
                    PriceChange.is_applied == False
                )
            )

            changes = await self.session.execute(query)
            changes = changes.scalars().all()

            if not changes:
                return 0

            processed_count = 0

            # Обрабатываем изменения батчами
            async def process_batch(batch: List[PriceChange]):
                nonlocal processed_count
                for change in batch:
                    # Обновляем цену тарифа
                    tariff = await self.session.get(TariffPlan, change.tariff_id)
                    if tariff:
                        tariff.price_points = change.new_price
                        change.is_applied = True
                        change.applied_at = datetime.now(timezone.utc)
                        processed_count += 1

            await self.batch_processor.process_in_batches(changes, process_batch)
            await self.session.commit()

            # Инвалидируем кэш тарифов
            await self.cache.invalidate_pattern('tariffs:*')

            return processed_count

        except Exception as e:
            logger.error(f"Error processing price changes: {e}")
            await self.session.rollback()
            raise

    async def get_tariff_statistics(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получение статистики по тарифам с кэшированием"""
        cache_key = self._cache_keys['tariff_stats']
        cached_stats = await self.cache.get_cached_data(cache_key)

        if cached_stats:
            return cached_stats

        try:
            now = datetime.now(timezone.utc)
            if not start_date:
                start_date = now - timedelta(days=30)
            if not end_date:
                end_date = now

            # Используем оптимизированные запросы через QueryOptimizer
            purchases_query = await self.query_optimizer.get_tariff_purchases(
                start_date,
                end_date
            )

            distribution_query = await self.query_optimizer.get_tariff_distribution()

            revenue_query = await self.query_optimizer.get_tariff_revenue(
                start_date,
                end_date
            )

            # Выполняем запросы параллельно
            purchases, distribution, revenue = await asyncio.gather(
                purchases_query,
                distribution_query,
                revenue_query
            )

            stats = {
                'total_purchases': len(purchases),
                'distribution': distribution,
                'revenue': revenue,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                stats,
                ttl=self._cache_ttl['tariff_stats']
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting tariff statistics: {e}")
            raise

    async def get_price_history(
            self,
            tariff_id: int,
            limit: int = 10
    ) -> List[PriceChange]:
        """Получение истории изменения цен с кэшированием"""
        cache_key = self._cache_keys['price_history'].format(tariff_id)
        cached_history = await self.cache.get_cached_data(cache_key)

        if cached_history:
            return cached_history

        try:
            query = await self.query_optimizer.optimize_query(
                select(PriceChange)
                .where(PriceChange.tariff_id == tariff_id)
                .order_by(desc(PriceChange.change_date))
                .limit(limit)
            )

            result = await self.session.execute(query)
            history = result.scalars().all()

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                history,
                ttl=self._cache_ttl['price_history']
            )

            return history

        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            raise

    async def schedule_price_change(
            self,
            tariff_id: int,
            new_price: float,
            scheduled_date: datetime,
            reason: Optional[str] = None
    ) -> PriceChange:
        """Запланировать изменение цены"""
        try:
            # Получаем текущую цену тарифа
            tariff = await self.session.get(TariffPlan, tariff_id)
            if not tariff:
                raise ValueError(f"Tariff {tariff_id} not found")

            price_change = PriceChange(
                tariff_id=tariff_id,
                old_price=tariff.price_points,
                new_price=new_price,
                scheduled_date=scheduled_date,
                reason=reason
            )

            self.session.add(price_change)
            await self.session.commit()

            # Инвалидируем кэш истории цен
            await self.cache.invalidate(
                self._cache_keys['price_history'].format(tariff_id)
            )

            return price_change

        except Exception as e:
            logger.error(f"Error scheduling price change: {e}")
            await self.session.rollback()
            raise

    async def invalidate_user_cache(self, user_id: int) -> None:
        """Инвалидация кэша пользователя"""
        await self.cache.invalidate(
            self._cache_keys['user_tariff'].format(user_id)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
