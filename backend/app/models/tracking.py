from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, JSON, Enum, String, UniqueConstraint, DateTime, Boolean # <-- Добавлены импорты
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..core.database import Base
from ..core.constants import ActionType, ContentType


class UsageLog(AsyncAttrs, Base):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType))
    content_type: Mapped[Optional[ContentType]] = mapped_column(Enum(ContentType), nullable=True)
    points_change: Mapped[int] = mapped_column(default=0)
    daily_usage_count: Mapped[int] = mapped_column(default=1)
    extra_data: Mapped[Dict] = mapped_column(JSON)
    skip_limits: Mapped[bool] = mapped_column(Boolean, default=False)  # Флаг для пропуска лимитов (генерация за баллы)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Отношения
    user = relationship("User", back_populates="usage_logs", lazy="selectin")

class DailyUsage(AsyncAttrs, Base):
    __tablename__ = "daily_usage"
    # --- ДОБАВЛЕНО УНИКАЛЬНОЕ ОГРАНИЧЕНИЕ ---
    __table_args__ = (UniqueConstraint('user_id', 'date', name='uq_daily_usage_user_date'),)
    # --- КОНЕЦ ДОБАВЛЕНИЯ ---

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Счетчики генераций
    generations_count: Mapped[int] = mapped_column(default=0)
    lesson_plans_count: Mapped[int] = mapped_column(default=0)
    exercises_count: Mapped[int] = mapped_column(default=0)
    games_count: Mapped[int] = mapped_column(default=0)
    images_count: Mapped[int] = mapped_column(default=0)
    transcripts_count: Mapped[int] = mapped_column(default=0)

    # Баллы
    points_earned: Mapped[int] = mapped_column(default=0)
    points_spent: Mapped[int] = mapped_column(default=0)

    # Отношения
    user = relationship("User", back_populates="daily_usage", lazy="selectin")


class UsageStatistics(AsyncAttrs, Base):
    __tablename__ = "usage_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Общая статистика
    total_generations: Mapped[int] = mapped_column(default=0)
    total_images: Mapped[int] = mapped_column(default=0)
    active_days: Mapped[int] = mapped_column(default=0)
    points_earned: Mapped[int] = mapped_column(default=0)
    points_spent: Mapped[int] = mapped_column(default=0)

    # Статистика по типам
    generations_by_type: Mapped[Dict] = mapped_column(JSON, default=dict)
    popular_prompts: Mapped[Dict] = mapped_column(JSON, default=dict)

    # Средние показатели
    avg_daily_generations: Mapped[float] = mapped_column(default=0.0)
    avg_daily_images: Mapped[float] = mapped_column(default=0.0)

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Отношения
    user = relationship("User", back_populates="usage_statistics", lazy="selectin")


class GenerationMetrics(AsyncAttrs, Base):
    __tablename__ = "generation_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    prompt: Mapped[str] = mapped_column(String(500))
    tokens_used: Mapped[int] = mapped_column()
    generation_time: Mapped[float] = mapped_column()  # в секундах
    success: Mapped[bool] = mapped_column(default=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Отношения
    user = relationship("User", back_populates="generation_metrics", lazy="selectin")


class UserActivityLog(AsyncAttrs, Base):
    __tablename__ = "user_activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType))
    content_type: Mapped[Optional[ContentType]] = mapped_column(Enum(ContentType), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    activity_metadata: Mapped[Dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Отношения
    user = relationship("User", back_populates="activity_logs", lazy="selectin")
