from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, select, func
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from ..core.database import Base
from sqlalchemy import JSON


class PointTransaction(AsyncAttrs, Base):
    """Модель для транзакций с очками пользователей"""
    __tablename__ = "point_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column(
        nullable=False,
        comment="Положительное значение для начисления, отрицательное для списания"
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        comment="Тип транзакции: 'generation', 'reward', 'purchase' и т.д."
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now().replace(tzinfo=None))

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="point_transactions",
        lazy="selectin"
    )

    # Add this relationship property
    purchase = relationship(
        "PointPurchase",
        foreign_keys="PointPurchase.transaction_id",
        back_populates="transaction",
        lazy="selectin"
    )
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)

    @property
    def is_earning(self) -> bool:
        """Является ли транзакция начислением очков"""
        return self.amount > 0

    @property
    def is_spending(self) -> bool:
        """Является ли транзакция списанием очков"""
        return self.amount < 0

    @property
    def absolute_amount(self) -> int:
        """Абсолютное значение количества очков"""
        return abs(self.amount)

    @classmethod
    async def create_earning(
        cls,
        session,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None
    ) -> "PointTransaction":
        """Создает транзакцию начисления очков"""
        if amount <= 0:
            raise ValueError("Amount must be positive for earnings")

        transaction = cls(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description
        )
        session.add(transaction)
        await session.flush()
        return transaction

    @classmethod
    async def create_spending(
        cls,
        session,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None
    ) -> "PointTransaction":
        """Создает транзакцию списания очков"""
        if amount <= 0:
            raise ValueError("Amount must be positive for spending")

        transaction = cls(
            user_id=user_id,
            amount=-amount,  # Делаем значение отрицательным для списания
            transaction_type=transaction_type,
            description=description
        )
        session.add(transaction)
        await session.flush()
        return transaction

    @classmethod
    async def get_user_transactions(
        cls,
        session,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list["PointTransaction"]:
        """Получает список транзакций пользователя"""
        query = select(cls).where(cls.user_id == user_id)\
            .order_by(cls.created_at.desc())\
            .limit(limit).offset(offset)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_user_balance(cls, session, user_id: int) -> int:
        """Вычисляет текущий баланс пользователя"""
        query = select(func.sum(cls.amount))\
            .where(cls.user_id == user_id)
        result = await session.execute(query)
        return result.scalar() or 0