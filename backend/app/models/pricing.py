from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, JSON, Enum as SQLEnum
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..core.database import Base
import enum

class DiscountType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class RuleType(str, enum.Enum):
    MARKUP = "markup"
    DISCOUNT = "discount"
    FIXED = "fixed"
    DYNAMIC = "dynamic"

class SpecialOffer(AsyncAttrs, Base):
    __tablename__ = "special_offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariff_plans.id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    discount_percent: Mapped[float] = mapped_column()
    start_date: Mapped[datetime] = mapped_column()
    end_date: Mapped[datetime] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    limitations: Mapped[Dict] = mapped_column(type_=JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tariff: Mapped["TariffPlan"] = relationship(
        back_populates="special_offers",
        lazy="selectin"
    )

class Discount(AsyncAttrs, Base):
    __tablename__ = "discounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType))
    value: Mapped[float] = mapped_column()
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    tariff_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tariff_plans.id"))
    start_date: Mapped[Optional[datetime]] = mapped_column()
    end_date: Mapped[Optional[datetime]] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    conditions: Mapped[Dict] = mapped_column(type_=JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        back_populates="discounts",
        lazy="selectin"
    )
    tariff: Mapped[Optional["TariffPlan"]] = relationship(
        back_populates="discounts",
        lazy="selectin"
    )

class PricingRule(AsyncAttrs, Base):
    __tablename__ = "pricing_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    rule_type: Mapped[RuleType] = mapped_column(SQLEnum(RuleType))
    parameters: Mapped[Dict] = mapped_column(type_=JSON)
    priority: Mapped[int] = mapped_column(default=0)
    conditions: Mapped[Dict] = mapped_column(type_=JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=lambda: datetime.now(timezone.utc))

class AppliedDiscount(AsyncAttrs, Base):
    __tablename__ = "applied_discounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    discount_id: Mapped[int] = mapped_column(ForeignKey("discounts.id"))
    amount: Mapped[float] = mapped_column()
    applied_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    purchase_id: Mapped[int] = mapped_column(ForeignKey("point_transactions.id"))

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="applied_discounts",
        lazy="selectin"
    )
    discount: Mapped["Discount"] = relationship(lazy="selectin")
    purchase: Mapped["PointTransaction"] = relationship(lazy="selectin")