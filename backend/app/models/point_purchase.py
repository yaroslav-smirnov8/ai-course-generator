# app/models/point_purchase.py
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, Boolean, DateTime, JSON, ForeignKey, Enum
from datetime import datetime
from typing import Optional, Dict, Any
from ..core.database import Base
from ..schemas.points_purchase import PurchaseStatus, PaymentMethod


class PointPurchase(AsyncAttrs, Base):
    __tablename__ = "point_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column()
    price: Mapped[float] = mapped_column(Float)
    bonus: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus))
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    payment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transaction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("point_transactions.id"), nullable=True)
    refund_transaction_id: Mapped[Optional[int]] = mapped_column(ForeignKey("point_transactions.id"), nullable=True)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow().replace(tzinfo=None))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Отношения
    user = relationship("User", back_populates="point_purchases")
    transaction = relationship(
        "PointTransaction",
        foreign_keys=[transaction_id],
        back_populates="purchase",
        lazy="selectin"
    )
    refund_transaction = relationship(
        "PointTransaction",
        foreign_keys=[refund_transaction_id],
        lazy="selectin"
    )

    @property
    def total_points(self) -> int:
        """Общее количество баллов (включая бонусные)"""
        return self.amount + self.bonus

    @property
    def is_expired(self) -> bool:
        """Проверка, истекла ли покупка"""
        if not self.expires_at:
            return False
        current_time = datetime.now().replace(tzinfo=None)
        return current_time > self.expires_at

    @property
    def is_refundable(self) -> bool:
        """Проверка, можно ли вернуть средства"""
        if not self.completed_at:
            return False

        current_time = datetime.now().replace(tzinfo=None)
        return (
                self.status == PurchaseStatus.COMPLETED and
                not self.refunded_at and
                (current_time - self.completed_at).days < 30  # 30 дней на возврат
        )