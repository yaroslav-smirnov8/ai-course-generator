from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, JSON, Enum, func, String, DateTime # Добавлен импорт String
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..core.database import Base
from ..core.constants import ContentType
from .user import User

class AnalyticsData(AsyncAttrs, Base):
    __tablename__ = "analytics_data"

    # Основные поля
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))

    # Метрики пользователей
    total_users: Mapped[int] = mapped_column(default=0)
    active_users: Mapped[int] = mapped_column(default=0)
    new_users: Mapped[int] = mapped_column(default=0)
    users_with_tariffs: Mapped[int] = mapped_column(default=0)
    tariff_distribution: Mapped[Dict] = mapped_column(JSON, default=dict)

    # Метрики генераций
    total_generations: Mapped[int] = mapped_column(default=0)
    generations_by_type: Mapped[Dict] = mapped_column(JSON, default=dict)
    average_generations_per_user: Mapped[float] = mapped_column(default=0.0)

    # Метрики баллов
    total_points_spent: Mapped[int] = mapped_column(default=0)
    total_points_earned: Mapped[int] = mapped_column(default=0)
    average_user_balance: Mapped[float] = mapped_column(default=0.0)

    @classmethod
    async def create_daily_snapshot(cls, session, date: Optional[datetime] = None):
        """Создает снапшот аналитики за указанную дату"""
        if date is None:
            date = datetime.now(timezone.utc).date()

        # Вычисляем метрики асинхронно
        total_users = await session.scalar(
            func.count(User.id)
        )

        active_users = await session.scalar(
            func.count(User.id).filter(User.last_active >= date)
        )

        new_users = await session.scalar(
            func.count(User.id).filter(func.date(User.created_at) == date)
        )

        # Создаем снапшот
        snapshot = cls(
            date=date,
            total_users=total_users,
            active_users=active_users,
            new_users=new_users
        )

        return snapshot


class DetailedGenerationMetrics(AsyncAttrs, Base):
    __tablename__ = "detailed_generation_metrics"

    # Основные поля
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    content_type: Mapped[ContentType] = mapped_column()

    # Метрики
    total_count: Mapped[int] = mapped_column(default=0)
    success_count: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)
    average_time: Mapped[float] = mapped_column(default=0.0)

    # Анализ контента
    popular_prompts: Mapped[List] = mapped_column(JSON, default=list)
    error_types: Mapped[Dict] = mapped_column(JSON, default=dict)
    average_content_length: Mapped[int] = mapped_column(default=0)

    @classmethod
    async def calculate_metrics(cls, session, date: datetime, content_type: ContentType):
        """Вычисляет детальные метрики для типа контента за указанную дату"""
        from .content import Generation  # Импорт здесь во избежание циклических зависимостей

        # Базовый запрос для фильтрации по дате и типу контента
        base_query = (
            Generation.__table__.select()
            .where(func.date(Generation.created_at) == date)
            .where(Generation.type == content_type)
        )

        # Подсчет общего количества
        total_count = await session.scalar(
            func.count().select().select_from(base_query)
        )

        if not total_count:
            return None

        # Подсчет успешных и ошибочных генераций
        success_count = await session.scalar(
            func.count()
            .select()
            .select_from(base_query.where(Generation.status == 'success'))
        )

        error_count = await session.scalar(
            func.count()
            .select()
            .select_from(base_query.where(Generation.status == 'error'))
        )

        # Среднее время генерации
        avg_time = await session.scalar(
            func.avg(func.extract('epoch', Generation.updated_at - Generation.created_at))
            .select()
            .select_from(base_query.where(Generation.status == 'success'))
        ) or 0.0

        # Создаем объект с метриками
        metrics = cls(
            date=date,
            content_type=content_type,
            total_count=total_count,
            success_count=success_count,
            error_count=error_count,
            average_time=avg_time
        )

        return metrics


class PurchaseAnalytics(AsyncAttrs, Base):
    __tablename__ = "purchase_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purchase_type: Mapped[str] = mapped_column(String(50), index=True)  # e.g., 'tariff', 'points'
    amount: Mapped[float] = mapped_column() # Сумма покупки (может быть цена тарифа или кол-во баллов)
    item_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True) # ID тарифа или пакета баллов
    item_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Название тарифа или пакета
    discount: Mapped[Optional[float]] = mapped_column(nullable=True) # Примененная скидка
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Метод оплаты
    purchase_metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True) # Исправлено: metadata -> purchase_metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Отношения (если нужны)
    # user: Mapped["User"] = relationship(back_populates="purchases") # Добавить back_populates в User, если нужно
