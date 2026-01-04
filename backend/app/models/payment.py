from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from ..core.database import Base

class Payment(AsyncAttrs, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    payment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "tariff", "points"
    status: Mapped[str] = mapped_column(String(50), default="pending")  # "pending", "completed", "failed", "cancelled"
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))  # "card", "yoomoney", "crypto", etc.
    external_payment_id: Mapped[Optional[str]] = mapped_column(String(255))  # ID платежа в платежной системе
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Дополнительные данные (тип тарифа, количество баллов и т.д.)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
