from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Integer, Boolean, DateTime, JSON, Enum as SQLEnum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

from ..core.database import Base


class PromoCodeType(str, Enum):
    """Тип промокода"""
    POINTS = "points"  # Добавляет баллы
    TARIFF = "tariff"  # Активирует тариф
    DISCOUNT = "discount"  # Скидка на покупку


class PromoCodeUsageType(str, Enum):
    """Тип использования промокода"""
    UNLIMITED = "unlimited"  # Неограниченное использование
    LIMITED = "limited"  # Ограниченное количество использований
    SINGLE_USER = "single_user"  # Для конкретного пользователя


class PromoCode(AsyncAttrs, Base):
    __tablename__ = "promocodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # Тип промокода
    type: Mapped[PromoCodeType] = mapped_column(SQLEnum(PromoCodeType))
    usage_type: Mapped[PromoCodeUsageType] = mapped_column(SQLEnum(PromoCodeUsageType))

    # Значения
    points_amount: Mapped[Optional[int]] = mapped_column(Integer, default=0)  # Количество баллов
    tariff_type: Mapped[Optional[str]] = mapped_column(String(20))  # Тип тарифа
    tariff_duration_months: Mapped[Optional[int]] = mapped_column(Integer, default=1)  # Длительность тарифа
    discount_percent: Mapped[Optional[float]] = mapped_column(default=0.0)  # Процент скидки

    # Ограничения использования
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)  # Лимит использований (None = безлимит)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)  # Текущее количество использований
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))  # Для конкретного пользователя

    # Временные ограничения
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Дополнительные настройки
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # Дополнительные условия

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))  # Кто создал

    # Отношения будут добавлены позже для избежания циклических импортов

    @property
    def is_valid(self) -> bool:
        """Проверка валидности промокода"""
        now = datetime.now(timezone.utc)

        # Проверка активности
        if not self.is_active:
            return False

        # Проверка временных рамок
        if self.valid_until and now > self.valid_until:
            return False

        if now < self.valid_from:
            return False

        # Проверка лимита использований
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False

        return True

    @property
    def remaining_uses(self) -> Optional[int]:
        """Оставшееся количество использований"""
        if not self.usage_limit:
            return None
        return max(0, self.usage_limit - self.usage_count)


class PromoCodeUsage(AsyncAttrs, Base):
    __tablename__ = "promocode_usages"

    id: Mapped[int] = mapped_column(primary_key=True)
    promocode_id: Mapped[int] = mapped_column(ForeignKey("promocodes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Что было применено
    points_added: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    tariff_activated: Mapped[Optional[str]] = mapped_column(String(20))
    tariff_duration: Mapped[Optional[int]] = mapped_column(Integer)
    discount_applied: Mapped[Optional[float]] = mapped_column(default=0.0)

    # Метаданные
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv4/IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    # Отношения будут добавлены позже для избежания циклических импортов
