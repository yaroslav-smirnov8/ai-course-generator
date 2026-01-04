# app/models/subscription.py
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON, String, Boolean, ForeignKey, DateTime
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..core.database import Base
from ..core.constants import TariffType
from .pricing import SpecialOffer, Discount


class TariffPlan(AsyncAttrs, Base):
    __tablename__ = "tariff_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(50))
    price_points: Mapped[int] = mapped_column(nullable=False)
    generations_limit: Mapped[int] = mapped_column(nullable=False)
    images_limit: Mapped[int] = mapped_column(nullable=False)
    features: Mapped[Dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Добавляем связь с историей цен
    price_history: Mapped[List["PriceChange"]] = relationship(
        "PriceChange",
        back_populates="tariff",
        lazy="selectin"
    )

    special_offers: Mapped[List["SpecialOffer"]] = relationship(
        "SpecialOffer",
        back_populates="tariff",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    discounts: Mapped[List["Discount"]] = relationship(
        "Discount",
        back_populates="tariff",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    @classmethod
    def get_default_features(cls, tariff_type: TariffType) -> dict:
        """Возвращает стандартный набор возможностей для тарифа"""
        features = {
            TariffType.BASIC: {
                "priority": "normal",
                "can_save_templates": False,
                "advanced_generation": False
            },
            TariffType.STANDARD: {
                "priority": "high",
                "can_save_templates": True,
                "advanced_generation": False
            },
            TariffType.PREMIUM: {
                "priority": "highest",
                "can_save_templates": True,
                "advanced_generation": True
            }
        }
        return features.get(tariff_type, features[TariffType.BASIC])


class UserTariff(AsyncAttrs, Base):
    __tablename__ = "user_tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariff_plans.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tariffs", lazy="selectin")
    tariff: Mapped["TariffPlan"] = relationship("TariffPlan", lazy="selectin")


class PriceChange(AsyncAttrs, Base):
    __tablename__ = "price_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariff_plans.id"))
    old_price: Mapped[int] = mapped_column(nullable=False)
    new_price: Mapped[int] = mapped_column(nullable=False)
    change_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    tariff: Mapped["TariffPlan"] = relationship(
        "TariffPlan",
        back_populates="price_history",
        lazy="selectin"
    )
    changed_by: Mapped["User"] = relationship("User", lazy="selectin")