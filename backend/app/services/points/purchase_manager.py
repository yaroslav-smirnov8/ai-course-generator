# app/services/points/purchase_manager.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timedelta
import logging
import uuid
import json
import hashlib
import hmac
from typing import List, Optional, Dict, Any

from ...models import User, PointTransaction, PointPurchase
from ...core.cache import CacheService
from ...schemas.points_purchase import (
    PurchaseStatus,
    PaymentMethod,
    PurchaseRequest,
    PurchaseResponse,
    PurchaseHistory,
    PurchasePackage
)
from ...core.config import settings
from .manager import PointsManager
from ...core.exceptions import (
    PointsPurchaseError,
    InvalidAmountError,
    TransactionConflictError
)

logger = logging.getLogger(__name__)


class PointsPurchaseManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.points_manager = PointsManager(session)
        self.cache = CacheService()

    async def initialize_purchase(
            self,
            user_id: int,
            amount: int,
            price: float,
            bonus: int = 0,
            payment_method: PaymentMethod = PaymentMethod.TELEGRAM,
            meta_data: Optional[Dict] = None
    ) -> PurchaseResponse:
        """Инициализация покупки баллов"""
        try:
            # Проверяем валидность суммы
            if amount <= 0:
                raise InvalidAmountError("Purchase amount must be positive")

            # Создаем ID покупки
            payment_id = str(uuid.uuid4())

            # Создаем запись о покупке с timezone-naive datetime
            now = datetime.now().replace(tzinfo=None)
            purchase = PointPurchase(
                payment_id=payment_id,
                user_id=user_id,
                amount=amount,
                price=price,
                bonus=bonus,
                status=PurchaseStatus.PENDING,
                payment_method=payment_method,
                meta_data=meta_data or {},
                created_at=now,
                expires_at=now + timedelta(hours=1)
            )
            self.session.add(purchase)

            # Генерируем URL для оплаты в зависимости от метода
            payment_url = await self._generate_payment_url(
                payment_id=payment_id,
                amount=price,
                payment_method=payment_method,
                title=f"Purchase {amount} points",
                description=f"Purchase {amount} points" + (f" + {bonus} bonus" if bonus > 0 else "")
            )

            purchase.payment_url = payment_url
            await self.session.commit()
            await self.session.refresh(purchase)

            return PurchaseResponse(
                payment_id=payment_id,
                user_id=user_id,
                amount=amount,
                price=price,
                bonus=bonus,
                status=PurchaseStatus.PENDING,
                payment_url=payment_url,
                created_at=purchase.created_at,
                expires_at=purchase.expires_at,
                meta_data=purchase.meta_data
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error initializing purchase: {str(e)}")
            raise PointsPurchaseError(
                message=f"Failed to initialize purchase: {str(e)}",
                user_id=user_id
            )

    async def confirm_purchase(
            self,
            user_id: int,
            payment_id: str,
            payment_data: Optional[Dict[str, Any]] = None
    ) -> PurchaseResponse:
        """Подтверждение покупки баллов"""
        try:
            # Получаем информацию о покупке
            purchase = await self._get_purchase(payment_id)
            if not purchase:
                raise PointsPurchaseError("Purchase not found")

            if purchase.user_id != user_id:
                raise PointsPurchaseError("Purchase belongs to another user")

            if purchase.status != PurchaseStatus.PENDING:
                raise PointsPurchaseError(
                    f"Invalid purchase status: {purchase.status}"
                )

            # Рассчитываем общее количество баллов (с бонусом)
            total_points = purchase.amount + purchase.bonus

            # Начисляем баллы пользователю
            await self.points_manager.add_points(
                user_id=user_id,
                amount=total_points,
                transaction_type="purchase",
                description=f"Points purchase: {purchase.amount} + {purchase.bonus} bonus",
                meta_data=payment_data or {}
            )

            # Обновляем статус покупки
            purchase.status = PurchaseStatus.COMPLETED
            purchase.completed_at = datetime.now().replace(tzinfo=None)
            purchase.payment_data = payment_data or {}

            await self.session.commit()

            # Отслеживаем покупку в аналитике
            try:
                from ..analytics import OptimizedAnalyticsService
                analytics_service = OptimizedAnalyticsService(self.session)
                await analytics_service.track_purchase(
                    user_id=user_id,
                    purchase_type="points",
                    amount=purchase.price,
                    item_id=payment_id,
                    item_name=f"{purchase.amount} points",
                    payment_method=purchase.payment_method,
                    metadata={
                        "points_amount": purchase.amount,
                        "bonus_amount": purchase.bonus,
                        "total_points": total_points,
                        "payment_method": purchase.payment_method
                    }
                )
            except Exception as e:
                logger.error(f"Error tracking points purchase: {str(e)}")

            logger.info(f"Purchase {payment_id} confirmed for user {user_id}")

            return PurchaseResponse(
                payment_id=purchase.payment_id,
                user_id=purchase.user_id,
                amount=purchase.amount,
                bonus=purchase.bonus,
                price=purchase.price,
                currency=purchase.currency,
                status=PurchaseStatus.COMPLETED,
                payment_url=purchase.payment_url,
                created_at=purchase.created_at,
                completed_at=purchase.completed_at,
                expires_at=purchase.expires_at,
                meta_data=purchase.meta_data
            )

        except PointsPurchaseError:
            raise
        except Exception as e:
            logger.error(f"Error confirming purchase: {str(e)}")
            await self.session.rollback()
            raise PointsPurchaseError(
                message=f"Failed to confirm purchase: {str(e)}",
                code="confirm_error"
            )

    async def cancel_purchase(
            self,
            payment_id: str,
            user_id: int
    ) -> None:
        """Отмена покупки баллов"""
        try:
            purchase = await self._get_purchase(payment_id)
            if not purchase:
                raise PointsPurchaseError("Purchase not found")

            if purchase.user_id != user_id:
                raise TransactionConflictError("User ID mismatch")

            if purchase.status != PurchaseStatus.PENDING:
                raise TransactionConflictError(
                    f"Cannot cancel purchase with status: {purchase.status}"
                )

            # Обновляем статус покупки
            purchase.status = PurchaseStatus.CANCELLED
            purchase.completed_at = datetime.now().replace(tzinfo=None)

            await self.session.commit()

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cancelling purchase: {str(e)}")
            raise PointsPurchaseError(
                message=f"Failed to cancel purchase: {str(e)}",
                user_id=user_id,
                payment_id=payment_id
            )

    async def get_purchase_history(
            self,
            user_id: int,
            page: int = 1,
            limit: int = 10,
            status: Optional[PurchaseStatus] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[PurchaseHistory]:
        """Получение истории покупок баллов"""
        try:
            query = select(PointPurchase).where(PointPurchase.user_id == user_id)

            # Применяем фильтры
            if status:
                query = query.where(PointPurchase.status == status)
            if start_date:
                query = query.where(PointPurchase.created_at >= start_date)
            if end_date:
                query = query.where(PointPurchase.created_at <= end_date)

            # Пагинация
            query = query.order_by(PointPurchase.created_at.desc())
            query = query.offset((page - 1) * limit).limit(limit)

            result = await self.session.execute(query)
            purchases = result.scalars().all()

            # Преобразуем в схему для ответа
            return [
                PurchaseHistory(
                    id=p.payment_id,
                    user_id=p.user_id,
                    amount=p.amount,
                    price=p.price,
                    bonus=p.bonus,
                    status=p.status,
                    payment_method=p.payment_method,
                    created_at=p.created_at,
                    completed_at=p.completed_at,
                    meta_data=p.meta_data
                ) for p in purchases
            ]

        except Exception as e:
            logger.error(f"Error getting purchase history: {str(e)}")
            raise PointsPurchaseError(
                message=f"Failed to get purchase history: {str(e)}",
                user_id=user_id
            )

    async def get_available_packages(self, user_id: int) -> List[PurchasePackage]:
        """Получение доступных пакетов баллов"""
        try:
            # Проверяем кэш
            cache_key = "purchase_packages"
            cached_packages = await self.cache.get_cached_data(cache_key)

            if cached_packages:
                return cached_packages

            # Базовые пакеты
            packages = [
                PurchasePackage(
                    id=1,
                    points=100,
                    price=99,
                    bonus=0,
                    description="Starter package",
                    is_popular=False,
                    currency="USD"
                ),
                PurchasePackage(
                    id=2,
                    points=500,
                    price=449,
                    bonus=50,
                    description="Standard package",
                    is_popular=True,
                    currency="USD"
                ),
                PurchasePackage(
                    id=3,
                    points=1000,
                    price=849,
                    bonus=150,
                    description="Premium package",
                    is_popular=False,
                    currency="USD"
                ),
                PurchasePackage(
                    id=4,
                    points=2000,
                    price=1599,
                    bonus=400,
                    description="Ultimate package",
                    is_popular=False,
                    currency="USD"
                )
            ]

            # Кэшируем результат
            await self.cache.cache_data(cache_key, packages, ttl=3600)  # 1 час

            return packages

        except Exception as e:
            logger.error(f"Error getting available packages: {str(e)}")
            raise PointsPurchaseError(
                message=f"Failed to get available packages: {str(e)}",
                user_id=user_id
            )

    async def process_telegram_webhook(self, payment_data: Dict) -> None:
        """Обработка webhook от Telegram для подтверждения оплаты"""
        try:
            # Проверяем подпись
            if not self._verify_telegram_signature(payment_data):
                logger.error(f"Invalid Telegram payment signature: {payment_data}")
                return

            # Получаем данные платежа
            payment_id = payment_data.get("custom_data", {}).get("payment_id")
            if not payment_id:
                logger.error(f"Payment ID not found in webhook data: {payment_data}")
                return

            purchase = await self._get_purchase(payment_id)
            if not purchase:
                logger.error(f"Purchase not found for payment ID: {payment_id}")
                return

            # Проверяем статус платежа
            if payment_data.get("status") == "paid":
                # Обновляем статус покупки
                purchase.status = PurchaseStatus.COMPLETED
                now = datetime.now().replace(tzinfo=None)
                purchase.completed_at = now
                purchase.meta_data.update({
                    "telegram_payment_id": payment_data.get("telegram_payment_charge_id"),
                    "webhook_received_at": now.isoformat()
                })

                # Начисляем баллы пользователю
                total_points = purchase.amount + purchase.bonus
                transaction = await self.points_manager.add_points(
                    user_id=purchase.user_id,
                    amount=total_points,
                    transaction_type="purchase",
                    description=f"Points purchase: {purchase.amount} + {purchase.bonus} bonus",
                    meta_data={
                        "payment_id": payment_id,
                        "payment_method": purchase.payment_method,
                        "price": purchase.price,
                        "telegram_payment_id": payment_data.get("telegram_payment_charge_id")
                    }
                )

                purchase.transaction_id = transaction.id
                await self.session.commit()

                # Инвалидируем кэш
                await self._invalidate_user_cache(purchase.user_id)

            elif payment_data.get("status") in ["failed", "cancelled"]:
                # Обновляем статус покупки на соответствующий
                purchase.status = PurchaseStatus.FAILED if payment_data.get(
                    "status") == "failed" else PurchaseStatus.CANCELLED
                now = datetime.now().replace(tzinfo=None)
                purchase.completed_at = now
                purchase.meta_data.update({
                    "webhook_received_at": now.isoformat(),
                    "failure_reason": payment_data.get("error_message", "Unknown error")
                })
                await self.session.commit()

            logger.info(f"Successfully processed Telegram payment webhook: {payment_id}")

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error processing Telegram webhook: {str(e)}")
            raise

    async def refund_purchase(
            self,
            payment_id: str,
            admin_user_id: int,
            reason: str,
            meta_data: Optional[Dict] = None
    ) -> None:
        """Возврат средств за покупку (только для админов)"""
        try:
            purchase = await self._get_purchase(payment_id)
            if not purchase:
                raise PointsPurchaseError("Purchase not found")

            if purchase.status != PurchaseStatus.COMPLETED:
                raise TransactionConflictError(
                    f"Cannot refund purchase with status: {purchase.status}"
                )

            # Проверяем, был ли возврат ранее
            if purchase.refunded_at:
                raise TransactionConflictError("Purchase already refunded")

            # Снимаем баллы с пользователя если возможно
            total_points = purchase.amount + purchase.bonus
            current_balance = await self.points_manager.get_balance(purchase.user_id)

            if current_balance < total_points:
                raise InvalidAmountError(
                    f"Insufficient points balance: {current_balance}, required: {total_points}"
                )

            # Создаем транзакцию для снятия баллов
            deduct_transaction = await self.points_manager.deduct_points(
                user_id=purchase.user_id,
                amount=total_points,
                transaction_type="refund",
                description=f"Refund for purchase {payment_id}: {reason}",
                meta_data={
                    "payment_id": payment_id,
                    "refund_reason": reason,
                    "admin_user_id": admin_user_id,
                    **(meta_data or {})
                }
            )

            # Обновляем запись покупки
            purchase.status = PurchaseStatus.REFUNDED
            now = datetime.now().replace(tzinfo=None)
            purchase.refunded_at = now
            purchase.refund_transaction_id = deduct_transaction.id
            purchase.meta_data.update({
                "refund_reason": reason,
                "refunded_by": admin_user_id,
                "refunded_at": now.isoformat()
            })

            await self.session.commit()

            # Инвалидируем кэш
            await self._invalidate_user_cache(purchase.user_id)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error refunding purchase: {str(e)}")
            raise PointsPurchaseError(
                message=f"Failed to refund purchase: {str(e)}",
                payment_id=payment_id
            )

    async def _get_purchase(self, payment_id: str) -> Optional[PointPurchase]:
        """Получение покупки по ID"""
        query = select(PointPurchase).where(PointPurchase.payment_id == payment_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _generate_payment_url(
            self,
            payment_id: str,
            amount: float,
            payment_method: PaymentMethod,
            title: str,
            description: str
    ) -> str:
        """Генерация URL для оплаты в зависимости от метода"""
        if payment_method == PaymentMethod.TELEGRAM:
            # Генерируем Telegram Invoice URL
            provider_token = settings.TELEGRAM_PAYMENT_TOKEN

            # Формируем параметры для Telegram Payments API
            payload = {
                "title": title,
                "description": description,
                "payload": json.dumps({"payment_id": payment_id}),
                "provider_token": provider_token,
                "currency": "USD",
                "prices": [{"label": "Points Purchase", "amount": int(amount * 100)}],  # в центах
                "start_parameter": f"purchase_{payment_id}",
                "photo_url": "https://example.com/points_purchase.jpg",  # опционально
                "photo_width": 600,  # опционально
                "photo_height": 400  # опционально
            }

            # В реальности здесь будет вызов Telegram Bot API
            # Для тестирования возвращаем заглушку
            return f"https://t.me/bot/invoice?startapp=purchase_{payment_id}"

        elif payment_method == PaymentMethod.CARD:
            # Здесь будет интеграция с платежной системой
            return f"https://example.com/payment/card/{payment_id}"

        elif payment_method == PaymentMethod.CRYPTO:
            # Здесь будет интеграция с криптоплатежами
            return f"https://example.com/payment/crypto/{payment_id}"

        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    def _verify_telegram_signature(self, payment_data: Dict) -> bool:
        """Проверка подписи от Telegram"""
        if "hash" not in payment_data:
            return False

        received_hash = payment_data.pop("hash")
        secret_key = hmac.new(
            key=b"WebhookSecret",
            msg=settings.BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()

        # Сортируем поля в алфавитном порядке
        data_check_list = []
        for key in sorted(payment_data.keys()):
            value = payment_data[key]
            data_check_list.append(f"{key}={value}")

        data_check_string = "\n".join(data_check_list)

        # Вычисляем хеш
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Сравниваем хеши
        return calculated_hash == received_hash

    async def _invalidate_user_cache(self, user_id: int) -> None:
        """Инвалидация кэша пользователя"""
        await self.cache.invalidate_pattern(f"user:{user_id}:*")
        await self.cache.invalidate_pattern(f"balance:{user_id}")
        await self.cache.invalidate_pattern(f"user_stats:{user_id}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()