# app/services/points/manager.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging
from ...models import User, PointTransaction
from ...core.exceptions import InsufficientBalanceError
from ...schemas.points import PointTransactionResponse, TransactionType

logger = logging.getLogger(__name__)


class PointsManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_balance(self, user_id: int) -> int:
        """Получить текущий баланс пользователя"""
        try:
            query = select(User.points).where(User.id == user_id)
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting balance for user {user_id}: {str(e)}")
            raise

    async def check_sufficient_balance(self, user_id: int, amount: int) -> bool:
        """Проверить достаточно ли баллов для списания"""
        current_balance = await self.get_balance(user_id)
        return current_balance >= amount

    async def add_points(
            self,
            user_id: int,
            amount: int,
            transaction_type: TransactionType,
            description: Optional[str] = None,
            meta_data: Optional[dict] = None
    ) -> PointTransactionResponse:
        """Начислить баллы пользователю"""
        try:
            # Получаем пользователя
            query = select(User).where(User.id == user_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError(f"User {user_id} not found")

            # Создаем транзакцию
            transaction = PointTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                meta_data=meta_data
            )
            self.session.add(transaction)

            # Обновляем баланс пользователя
            user.points += amount
            transaction.balance_after = user.points

            await self.session.commit()
            await self.session.refresh(transaction)

            # Преобразуем SQLAlchemy модель в Pydantic модель ответа
            return PointTransactionResponse(
                id=transaction.id,
                user_id=transaction.user_id,
                amount=transaction.amount,
                type=transaction_type,
                description=transaction.description,
                created_at=transaction.created_at,
                meta_data=transaction.meta_data,
                balance_after=transaction.balance_after
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding points for user {user_id}: {str(e)}")
            raise

    async def deduct_points(
            self,
            user_id: int,
            amount: int,
            transaction_type: TransactionType,
            description: Optional[str] = None,
            meta_data: Optional[dict] = None
    ) -> PointTransactionResponse:
        """Списать баллы у пользователя"""
        try:
            if not await self.check_sufficient_balance(user_id, amount):
                raise InsufficientBalanceError(
                    f"Insufficient balance for user {user_id}. Required: {amount}"
                )

            # Получаем пользователя
            query = select(User).where(User.id == user_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            # Создаем транзакцию со знаком минус
            transaction = PointTransaction(
                user_id=user_id,
                amount=-amount,  # Отрицательное значение для списания
                transaction_type=transaction_type,
                description=description,
                meta_data=meta_data
            )
            self.session.add(transaction)

            # Обновляем баланс пользователя
            user.points -= amount
            transaction.balance_after = user.points

            await self.session.commit()
            await self.session.refresh(transaction)

            # Преобразуем SQLAlchemy модель в Pydantic модель ответа
            return PointTransactionResponse(
                id=transaction.id,
                user_id=transaction.user_id,
                amount=transaction.amount,
                type=transaction_type,
                description=transaction.description,
                created_at=transaction.created_at,
                meta_data=transaction.meta_data,
                balance_after=transaction.balance_after
            )

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deducting points for user {user_id}: {str(e)}")
            raise

    async def get_transactions(
            self,
            user_id: int,
            page: int = 1,
            limit: int = 10,
            transaction_type: Optional[TransactionType] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[PointTransactionResponse]:
        """Получить историю транзакций с фильтрацией"""
        try:
            query = select(PointTransaction).where(
                PointTransaction.user_id == user_id
            )

            # Применяем фильтры
            if transaction_type:
                query = query.where(PointTransaction.transaction_type == transaction_type)
            if start_date:
                query = query.where(PointTransaction.created_at >= start_date)
            if end_date:
                query = query.where(PointTransaction.created_at <= end_date)

            # Добавляем пагинацию
            query = query.order_by(PointTransaction.created_at.desc()) \
                .offset((page - 1) * limit) \
                .limit(limit)

            result = await self.session.execute(query)
            transactions = result.scalars().all()

            # Преобразуем SQLAlchemy модели в Pydantic модели ответа
            return [
                PointTransactionResponse(
                    id=transaction.id,
                    user_id=transaction.user_id,
                    amount=transaction.amount,
                    type=transaction.transaction_type,
                    description=transaction.description,
                    created_at=transaction.created_at,
                    meta_data=transaction.meta_data,
                    balance_after=getattr(transaction, 'balance_after', 0)
                )
                for transaction in transactions
            ]

        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {str(e)}")
            raise

    async def refund_points(
            self,
            user_id: int,
            amount: int,
            original_transaction_type: TransactionType,
            description: Optional[str] = None,
            meta_data: Optional[dict] = None
    ) -> PointTransactionResponse:
        """Вернуть баллы пользователю (например, при ошибке генерации)"""
        try:
            meta_data = meta_data or {}
            meta_data["refund_for"] = original_transaction_type

            return await self.add_points(
                user_id=user_id,
                amount=amount,
                transaction_type=TransactionType.REFUND,
                description=f"Refund for {original_transaction_type}: {description}",
                meta_data=meta_data
            )

        except Exception as e:
            logger.error(f"Error refunding points for user {user_id}: {str(e)}")
            raise

    async def get_transaction_statistics(
            self,
            user_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict:
        """Получить статистику транзакций"""
        try:
            query = select([
                func.sum(PointTransaction.amount).filter(PointTransaction.amount > 0).label('earned'),
                func.sum(PointTransaction.amount).filter(PointTransaction.amount < 0).label('spent'),
                func.count(PointTransaction.id).label('count'),
                func.avg(PointTransaction.amount).label('avg'),
                func.min(PointTransaction.created_at).label('first_date'),
                func.max(PointTransaction.created_at).label('last_date')
            ]).where(PointTransaction.user_id == user_id)

            if start_date:
                query = query.where(PointTransaction.created_at >= start_date)
            if end_date:
                query = query.where(PointTransaction.created_at <= end_date)

            result = await self.session.execute(query)
            stats = result.first()

            return {
                "total_earned": stats.earned or 0,
                "total_spent": abs(stats.spent) if stats.spent else 0,
                "transactions_count": stats.count or 0,
                "average_transaction": float(stats.avg) if stats.avg else 0,
                "first_transaction_date": stats.first_date,
                "last_transaction_date": stats.last_date
            }

        except Exception as e:
            logger.error(f"Error getting transaction statistics for user {user_id}: {str(e)}")
            raise

    async def get_daily_stats(self, user_id: int) -> Dict:
        """Получить статистику за текущий день"""
        try:
            today = datetime.now().replace(tzinfo=None).date()
            tomorrow = today + timedelta(days=1)

            query = select([
                func.count().filter(
                    and_(
                        PointTransaction.transaction_type == TransactionType.GENERATION,
                        PointTransaction.created_at >= today,
                        PointTransaction.created_at < tomorrow
                    )
                ).label('generations_today'),
                func.count().filter(
                    and_(
                        PointTransaction.transaction_type == TransactionType.GENERATION,
                        PointTransaction.meta_data['content_type'].astext == 'image',
                        PointTransaction.created_at >= today,
                        PointTransaction.created_at < tomorrow
                    )
                ).label('images_today')
            ]).where(PointTransaction.user_id == user_id)

            result = await self.session.execute(query)
            stats = result.first()

            return {
                "generations_today": stats.generations_today or 0,
                "images_today": stats.images_today or 0
            }

        except Exception as e:
            logger.error(f"Error getting daily stats for user {user_id}: {str(e)}")
            raise

    async def batch_add_points(
            self,
            user_ids: List[int],
            amount: int,
            transaction_type: TransactionType,
            description: Optional[str] = None,
            meta_data: Optional[dict] = None
    ) -> List[PointTransactionResponse]:
        """Массовое начисление баллов группе пользователей"""
        transactions = []
        try:
            # Получаем всех пользователей одним запросом
            query = select(User).where(User.id.in_(user_ids))
            result = await self.session.execute(query)
            users = result.scalars().all()

            for user in users:
                transaction = PointTransaction(
                    user_id=user.id,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=description,
                    meta_data=meta_data
                )
                self.session.add(transaction)
                user.points += amount
                transaction.balance_after = user.points
                transactions.append(transaction)

            await self.session.commit()

            # Обновляем transactions после коммита
            for transaction in transactions:
                await self.session.refresh(transaction)

            # Преобразуем SQLAlchemy модели в Pydantic модели ответа
            return [
                PointTransactionResponse(
                    id=transaction.id,
                    user_id=transaction.user_id,
                    amount=transaction.amount,
                    type=transaction_type,
                    description=transaction.description,
                    created_at=transaction.created_at,
                    meta_data=transaction.meta_data,
                    balance_after=transaction.balance_after
                )
                for transaction in transactions
            ]

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error in batch points addition: {str(e)}")
            raise

    async def transfer_points(
            self,
            from_user_id: int,
            to_user_id: int,
            amount: int,
            description: Optional[str] = None
    ) -> tuple[PointTransactionResponse, PointTransactionResponse]:
        """Перевод баллов между пользователями"""
        try:
            # Проверяем баланс отправителя
            if not await self.check_sufficient_balance(from_user_id, amount):
                raise InsufficientBalanceError(
                    f"Insufficient balance for transfer. User {from_user_id} needs {amount} points"
                )

            # Создаем транзакцию списания
            deduct_transaction = await self.deduct_points(
                user_id=from_user_id,
                amount=amount,
                transaction_type=TransactionType.TRANSFER,
                description=f"Transfer to user {to_user_id}: {description}"
            )

            # Создаем транзакцию начисления
            add_transaction = await self.add_points(
                user_id=to_user_id,
                amount=amount,
                transaction_type=TransactionType.TRANSFER,
                description=f"Transfer from user {from_user_id}: {description}"
            )

            return deduct_transaction, add_transaction

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error transferring points from user {from_user_id} to {to_user_id}: {str(e)}")
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()