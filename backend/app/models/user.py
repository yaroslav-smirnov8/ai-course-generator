from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Enum, Float, JSON
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..core.database import Base
from ..core.constants import UserRole, TariffType, TARIFF_LIMITS, UNLIMITED_ROLES
from .pricing import Discount, AppliedDiscount


class User(AsyncAttrs, Base):
    __tablename__ = "users"

    # Основные поля
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    theme: Mapped[str] = mapped_column(String(50), default="default")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[Dict] = mapped_column(JSON, default=dict)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Роль и доступ
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    is_friend: Mapped[bool] = mapped_column(Boolean, default=False)
    has_access: Mapped[bool] = mapped_column(Boolean, default=False)

    # WebApp данные
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    webapp_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    theme_params: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    # Система приглашений
    invite_code: Mapped[Optional[str]] = mapped_column(String(36), unique=True, nullable=True)
    invited_by_code: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    invites_count: Mapped[int] = mapped_column(Integer, default=0)
    total_earned_discount: Mapped[int] = mapped_column(Integer, default=0)

    # Тариф и баллы
    tariff: Mapped[Optional[TariffType]] = mapped_column(Enum(TariffType), nullable=True)
    tariff_valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)



    # Связи с использованием Mapped
    actions = relationship("UserAction", back_populates="user", lazy="selectin")
    usage_statistics = relationship("UsageStatistics", back_populates="user", lazy="selectin",
                                    cascade="all, delete-orphan")
    generation_metrics = relationship("GenerationMetrics", back_populates="user", lazy="selectin",
                                      cascade="all, delete-orphan")
    generations = relationship("Generation", back_populates="user", lazy="selectin")
    images = relationship("Image", back_populates="user", lazy="selectin")
    achievements = relationship("UserAchievement", back_populates="user", lazy="selectin")
    usage_logs = relationship("UsageLog", back_populates="user", lazy="selectin")
    activity_logs = relationship("UserActivityLog", back_populates="user", lazy="selectin")  # Добавили этот
    daily_usage = relationship("DailyUsage", back_populates="user", lazy="selectin")
    tariff_history = relationship("UserTariff", back_populates="user", lazy="selectin")
    point_transactions = relationship("PointTransaction", back_populates="user", lazy="selectin")
    tariffs: Mapped[List["UserTariff"]] = relationship(
        "UserTariff",
        back_populates="user",
        lazy="selectin",
        overlaps="tariff_history"  # Добавляем этот параметр
    )

    feature_usage: Mapped[List["FeatureUsage"]] = relationship(
        "FeatureUsage",
        back_populates="user",
        lazy="selectin"
    )

    # Relationships for pricing
    discounts: Mapped[List["Discount"]] = relationship(
        "Discount",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    applied_discounts: Mapped[List["AppliedDiscount"]] = relationship(
        "AppliedDiscount",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


    # Связь для courses
    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="creator",
        lazy="selectin"
    )

    # Связь с покупками баллов
    point_purchases: Mapped[List["PointPurchase"]] = relationship(
        "PointPurchase",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Связь с переходами по ссылкам
    link_clicks: Mapped[List["LinkClick"]] = relationship(
        "LinkClick",
        back_populates="user",
        lazy="selectin"
    )

    # Связь с платежами
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        lazy="selectin"
    )


    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def effective_discount(self) -> int:
        """Эффективная скидка с учетом ограничений"""
        MAX_DISCOUNT = 20  # Максимальная скидка 20%
        return min(self.total_earned_discount, MAX_DISCOUNT)

    @property
    def has_unlimited_access(self) -> bool:
        """Проверка на безлимитный доступ"""
        return self.role in UNLIMITED_ROLES

    @property
    def is_active(self) -> bool:
        """Проверка активности пользователя"""
        return self.has_access and not self.unsubscribed_at

    def get_daily_limits(self) -> Dict[str, int]:
        """Получение дневных лимитов генераций"""
        if self.has_unlimited_access:
            return {
                "generations": float('inf'),
                "images": float('inf')
            }

        if not self.tariff:
            return {
                "generations": 0,
                "images": 0
            }

        limits = TARIFF_LIMITS[self.tariff]
        return {
            "generations": limits.daily_generations,
            "images": limits.daily_images
        }

    def check_tariff_validity(self) -> bool:
        """Проверка активности тарифа"""
        if not self.tariff or not self.tariff_valid_until:
            return False
        return datetime.now(timezone.utc) < self.tariff_valid_until

        # Бонус за статус постоянного клиента
        if self.is_regular_customer:
            base_multiplier += 0.05  # +5% для постоянных клиентов

        # Бонус за общую сумму покупок
        if self.total_spent >= 1000:
            base_multiplier += 0.1  # +10% для крупных клиентов

        # Дополнительный бонус за достижения
        if hasattr(self, 'achievements'):
            unlocked_achievements = len([
                a for a in self.achievements if a.unlocked
            ])
            if unlocked_achievements >= 5:
                base_multiplier += 0.03  # +3% за достижения

        return min(base_multiplier, 1.5)  # Максимальный бонус 50%

