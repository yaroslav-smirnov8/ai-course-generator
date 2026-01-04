from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from ..core.database import Base
from sqlalchemy import JSON

class UserStatistics(AsyncAttrs, Base):
    __tablename__ = "user_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)

    # Общая статистика по пользователям
    total_users: Mapped[int] = mapped_column(default=0)
    new_users: Mapped[int] = mapped_column(default=0)
    active_users: Mapped[int] = mapped_column(default=0)
    users_with_tariffs: Mapped[int] = mapped_column(default=0)

    # Распределение по тарифам
    tariff_distribution: Mapped[Dict] = mapped_column(JSON, default=dict)

    # Распределение скидок
    discount_distribution: Mapped[Dict] = mapped_column(JSON, default=dict)


class GenerationStatistics(AsyncAttrs, Base):
    __tablename__ = "generation_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)

    # Общее количество генераций
    total_generations: Mapped[int] = mapped_column(default=0)

    # Количество по типам
    lesson_plans: Mapped[int] = mapped_column(default=0)
    exercises: Mapped[int] = mapped_column(default=0)
    games: Mapped[int] = mapped_column(default=0)
    images: Mapped[int] = mapped_column(default=0)

    # Популярные запросы по каждому типу
    popular_requests: Mapped[Dict] = mapped_column(JSON, default=dict)


class TariffStatistics(AsyncAttrs, Base):
    __tablename__ = "tariff_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)

    # Покупки тарифов
    total_purchases: Mapped[int] = mapped_column(default=0)
    points_spent: Mapped[int] = mapped_column(default=0)
    average_discount: Mapped[float] = mapped_column(default=0.0)

    # Распределение по тарифам
    tariff_purchases: Mapped[Dict] = mapped_column(JSON, default=dict)


class ServerStatistics(AsyncAttrs, Base):
    __tablename__ = "server_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)

    # Нагрузка
    cpu_usage: Mapped[float] = mapped_column(default=0.0)  # в процентах
    memory_usage: Mapped[float] = mapped_column(default=0.0)  # в процентах
    disk_usage: Mapped[float] = mapped_column(default=0.0)  # в процентах

    # Производительность
    response_time: Mapped[float] = mapped_column(default=0.0)  # в миллисекундах
    requests_per_minute: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)

    # Детали ошибок
    error_details: Mapped[Dict] = mapped_column(JSON, default=dict)


class AggregatedStatistics(AsyncAttrs, Base):
    __tablename__ = "aggregated_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_start: Mapped[datetime] = mapped_column(index=True)
    period_end: Mapped[datetime]
    period_type: Mapped[str] = mapped_column()  # 'week' или 'month'

    # Агрегированные данные
    user_stats: Mapped[Dict] = mapped_column(JSON)
    generation_stats: Mapped[Dict] = mapped_column(JSON)
    tariff_stats: Mapped[Dict] = mapped_column(JSON)
    server_stats: Mapped[Dict] = mapped_column(JSON)


# Enums оставляем как есть, т.к. они не нуждаются в асинхронной адаптации
from enum import Enum

class StatisticsPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class StatisticsMetric(str, Enum):
    USERS = "users"
    GENERATIONS = "generations"
    TARIFFS = "tariffs"
    SERVER = "server"