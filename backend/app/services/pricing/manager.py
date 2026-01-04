from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import asyncio
import logging

from ...models import (
    TariffPlan,
    PriceChange,
    SpecialOffer,
    Discount,
    UserTariff,
    User,
    PointTransaction
)
from ...core.constants import TariffType
from ...core.cache import CacheService
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
from ...schemas.pricing import (
    TariffCreate,
    TariffUpdate,
    PriceChangeCreate,
    SpecialOfferCreate
)

logger = logging.getLogger(__name__)


class PricingManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache = CacheService()
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session, batch_size=100)

        # Кэш-ключи и TTL
        self._cache_keys = {
            'pricing_rules': 'pricing:rules',
            'special_offers': 'pricing:offers',
            'discounts': 'pricing:discounts',
            'price_analytics': 'pricing:analytics:{}',  # С параметром периода
            'user_discounts': 'pricing:user:{}:discounts'  # С ID пользователя
        }
        self._cache_ttl = {
            'pricing_rules': 3600,  # 1 час
            'special_offers': 1800,  # 30 минут
            'discounts': 1800,  # 30 минут
            'price_analytics': 3600,  # 1 час
            'user_discounts': 300  # 5 минут
        }

    async def create_tariff(self, tariff_data: TariffCreate) -> TariffPlan:
        """Создание нового тарифного плана"""
        try:
            # Проверяем существование тарифа с таким названием
            existing = await self.session.execute(
                select(TariffPlan).where(TariffPlan.name == tariff_data.name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Tariff with name {tariff_data.name} already exists")

            tariff = TariffPlan(**tariff_data.dict())
            self.session.add(tariff)
            await self.session.commit()
            await self.session.refresh(tariff)

            # Инвалидируем кэш тарифов
            await self.cache.invalidate_pattern('tariffs:*')

            return tariff

        except Exception as e:
            logger.error(f"Error creating tariff: {e}")
            await self.session.rollback()
            raise

    async def update_tariff(
            self,
            tariff_id: int,
            tariff_data: TariffUpdate
    ) -> Optional[TariffPlan]:
        """Обновление существующего тарифа"""
        try:
            tariff = await self.session.get(TariffPlan, tariff_id)
            if not tariff:
                return None

            # Если меняется цена, создаем запись об изменении
            if tariff_data.price and tariff_data.price != tariff.price_points:
                price_change = PriceChange(
                    tariff_id=tariff.id,
                    old_price=tariff.price_points,
                    new_price=tariff_data.price,
                    change_date=datetime.utcnow()
                )
                self.session.add(price_change)

            # Обновляем данные тарифа
            update_data = tariff_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(tariff, key, value)

            await self.session.commit()
            await self.session.refresh(tariff)

            # Инвалидируем кэш
            await self.cache.invalidate_pattern('tariffs:*')

            return tariff

        except Exception as e:
            logger.error(f"Error updating tariff: {e}")
            await self.session.rollback()
            raise

    async def create_special_offer(
            self,
            offer_data: SpecialOfferCreate
    ) -> SpecialOffer:
        """Создание специального предложения"""
        try:
            # Проверяем пересечение с существующими предложениями
            existing_offers = await self.get_active_special_offers(
                offer_data.tariff_id
            )

            for offer in existing_offers:
                if self._check_date_overlap(
                        offer_data.start_date,
                        offer_data.end_date,
                        offer.start_date,
                        offer.end_date
                ):
                    raise ValueError("Offer dates overlap with existing offer")

            offer = SpecialOffer(**offer_data.dict())
            self.session.add(offer)
            await self.session.commit()
            await self.session.refresh(offer)

            # Инвалидируем кэш предложений
            await self.cache.invalidate(self._cache_keys['special_offers'])

            return offer

        except Exception as e:
            logger.error(f"Error creating special offer: {e}")
            await self.session.rollback()
            raise

    async def get_active_special_offers(
            self,
            tariff_id: Optional[int] = None
    ) -> List[SpecialOffer]:
        """Получение активных специальных предложений"""
        cache_key = self._cache_keys['special_offers']
        cached_offers = await self.cache.get_cached_data(cache_key)

        if cached_offers is not None:
            # Фильтруем закэшированные предложения по tariff_id если нужно
            if tariff_id:
                return [o for o in cached_offers if o.tariff_id == tariff_id]
            return cached_offers

        try:
            now = datetime.utcnow()
            query = await self.query_optimizer.optimize_query(
                select(SpecialOffer).where(
                    and_(
                        SpecialOffer.start_date <= now,
                        SpecialOffer.end_date >= now,
                        SpecialOffer.is_active == True
                    )
                )
            )

            if tariff_id:
                query = query.where(SpecialOffer.tariff_id == tariff_id)

            result = await self.session.execute(query)
            offers = result.scalars().all()

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                offers,
                ttl=self._cache_ttl['special_offers']
            )

            return offers

        except Exception as e:
            logger.error(f"Error getting active special offers: {e}")
            raise

    async def calculate_user_price(
            self,
            user_id: int,
            tariff_id: int
    ) -> Tuple[float, Dict[str, float]]:
        """Расчет цены для пользователя с учетом всех скидок"""
        try:
            # Получаем базовую цену тарифа
            tariff = await self.session.get(TariffPlan, tariff_id)
            if not tariff:
                raise ValueError(f"Tariff {tariff_id} not found")

            base_price = tariff.price_points

            # Получаем все применимые скидки
            discounts = await self.get_applicable_discounts(user_id, tariff_id)

            # Рассчитываем финальную цену
            final_price = base_price
            applied_discounts = {}

            for discount in discounts:
                if discount.discount_type == 'percentage':
                    discount_amount = base_price * (discount.value / 100)
                else:
                    discount_amount = discount.value

                final_price -= discount_amount
                applied_discounts[discount.name] = discount_amount

            # Не даем цене уйти в минус
            final_price = max(0, final_price)

            return final_price, applied_discounts

        except Exception as e:
            logger.error(f"Error calculating user price: {e}")
            raise

    async def get_applicable_discounts(
            self,
            user_id: int,
            tariff_id: int
    ) -> List[Discount]:
        """Получение всех применимых скидок для пользователя"""
        cache_key = self._cache_keys['user_discounts'].format(user_id)
        cached_discounts = await self.cache.get_cached_data(cache_key)

        if cached_discounts is not None:
            return [d for d in cached_discounts if d.tariff_id == tariff_id]

        try:
            now = datetime.utcnow()

            # Оптимизированный запрос для получения всех типов скидок
            query = await self.query_optimizer.optimize_query(
                select(Discount).where(
                    and_(
                        or_(
                            Discount.user_id == user_id,
                            Discount.user_id.is_(None)
                        ),
                        or_(
                            Discount.tariff_id == tariff_id,
                            Discount.tariff_id.is_(None)
                        ),
                        Discount.start_date <= now,
                        or_(
                            Discount.end_date >= now,
                            Discount.end_date.is_(None)
                        ),
                        Discount.is_active == True
                    )
                )
            )

            result = await self.session.execute(query)
            discounts = result.scalars().all()

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                discounts,
                ttl=self._cache_ttl['user_discounts']
            )

            return discounts

        except Exception as e:
            logger.error(f"Error getting applicable discounts: {e}")
            raise

    async def get_pricing_analytics(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получение аналитики по ценообразованию"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        period_key = f"{start_date.date()}_{end_date.date()}"
        cache_key = self._cache_keys['price_analytics'].format(period_key)

        cached_analytics = await self.cache.get_cached_data(cache_key)
        if cached_analytics:
            return cached_analytics

        try:
            # Получаем различные метрики параллельно
            conversion_query = self.query_optimizer.get_price_conversion_rates(
                start_date,
                end_date
            )

            revenue_query = self.query_optimizer.get_revenue_by_tariff(
                start_date,
                end_date
            )

            discount_query = self.query_optimizer.get_discount_effectiveness(
                start_date,
                end_date
            )

            conversion_rates, revenue_data, discount_stats = await asyncio.gather(
                conversion_query,
                revenue_query,
                discount_query
            )

            analytics = {
                'conversion_rates': conversion_rates,
                'revenue_by_tariff': revenue_data,
                'discount_effectiveness': discount_stats,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                analytics,
                ttl=self._cache_ttl['price_analytics']
            )

            return analytics

        except Exception as e:
            logger.error(f"Error getting pricing analytics: {e}")
            raise

    async def process_expired_offers(self) -> int:
        """Пакетная обработка истекших специальных предложений"""
        try:
            now = datetime.utcnow()

            # Получаем все истекшие предложения
            query = select(SpecialOffer).where(
                and_(
                    SpecialOffer.end_date < now,
                    SpecialOffer.is_active == True
                )
            )

            expired_offers = await self.session.execute(query)
            expired_offers = expired_offers.scalars().all()

            if not expired_offers:
                return 0

            processed_count = 0

            # Обрабатываем истекшие предложения батчами
            async def process_batch(batch: List[SpecialOffer]):
                nonlocal processed_count
                for offer in batch:
                    offer.is_active = False
                    processed_count += 1

            await self.batch_processor.process_in_batches(
                expired_offers,
                process_batch
            )

            await self.session.commit()

            # Инвалидируем кэш предложений
            await self.cache.invalidate(self._cache_keys['special_offers'])

            return processed_count

        except Exception as e:
            logger.error(f"Error processing expired offers: {e}")
            await self.session.rollback()
            raise

    def _check_date_overlap(
            self,
            start1: datetime,
            end1: datetime,
            start2: datetime,
            end2: datetime
    ) -> bool:
        """Проверка пересечения дат"""
        return (start1 <= end2) and (end1 >= start2)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()