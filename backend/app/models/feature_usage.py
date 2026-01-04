from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum, JSON, ForeignKey, select, func
from datetime import datetime, timezone
from typing import Optional, Dict, List
from ..core.database import Base
from ..core.constants import ContentType, UserRole


class FeatureUsage(AsyncAttrs, Base):
    __tablename__ = "feature_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    feature_type: Mapped[str] = mapped_column(String(50))  # lesson_plan, exercise, game, image, etc.
    content_type: Mapped[Optional[ContentType]] = mapped_column(Enum(ContentType), nullable=True)  # Для генераций
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    success: Mapped[bool] = mapped_column(default=True)
    usage_data: Mapped[Dict] = mapped_column(JSON, default=dict)  # Дополнительные данные о использовании
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Тип ошибки, если success=False

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="feature_usage",
        lazy="selectin"
    )


class FeatureUsageMetrics(AsyncAttrs, Base):
    __tablename__ = "feature_usage_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Общая статистика
    total_usage: Mapped[int] = mapped_column(default=0)
    unique_users: Mapped[int] = mapped_column(default=0)

    # Статистика по функциям
    feature_distribution: Mapped[Dict] = mapped_column(
        JSON,
        default=dict,
        comment="Distribution of feature usage {feature: count}"
    )
    feature_success_rate: Mapped[Dict] = mapped_column(
        JSON,
        default=dict,
        comment="Success rate for each feature {feature: success_rate}"
    )

    # Статистика по пользователям
    user_role_distribution: Mapped[Dict] = mapped_column(
        JSON,
        default=dict,
        comment="Usage by user role {role: {feature: count}}"
    )
    tariff_distribution: Mapped[Dict] = mapped_column(
        JSON,
        default=dict,
        comment="Usage by tariff type {tariff: {feature: count}}"
    )

    # Средние показатели
    average_features_per_user: Mapped[float] = mapped_column(default=0.0)
    most_popular_features: Mapped[List] = mapped_column(
        JSON,
        default=list,
        comment="List of most used features [{feature, count, percentage}]"
    )
    least_used_features: Mapped[List] = mapped_column(
        JSON,
        default=list,
        comment="List of least used features [{feature, count, percentage}]"
    )

    @classmethod
    async def create_metrics(cls, session, date: Optional[datetime] = None) -> "FeatureUsageMetrics":
        """Создает метрики за указанную дату"""
        if not date:
            date = datetime.now(timezone.utc)

        metrics = cls(date=date)
        session.add(metrics)
        await session.flush()
        return metrics

    @classmethod
    async def get_by_date(cls, session, date: datetime) -> Optional["FeatureUsageMetrics"]:
        """Получает метрики за указанную дату"""
        stmt = select(cls).where(func.date(cls.date) == date.date())
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_metrics(self, metrics_data: Dict) -> None:
        """Обновляет метрики новыми данными"""
        for field, value in metrics_data.items():
            if hasattr(self, field):
                setattr(self, field, value)

    @property
    def total_success_rate(self) -> float:
        """Вычисляет общий процент успешных использований"""
        if not self.feature_success_rate:
            return 0.0

        total_success = sum(rate for rate in self.feature_success_rate.values())
        return total_success / len(self.feature_success_rate) if self.feature_success_rate else 0.0

    @property
    def active_features_count(self) -> int:
        """Возвращает количество активно используемых функций"""
        return len([f for f, count in self.feature_distribution.items() if count > 0])

    def get_feature_usage_trend(self, feature: str) -> Dict:
        """Возвращает статистику использования конкретной функции"""
        return {
            "total_usage": self.feature_distribution.get(feature, 0),
            "success_rate": self.feature_success_rate.get(feature, 0),
            "by_role": {
                role: data.get(feature, 0)
                for role, data in self.user_role_distribution.items()
            },
            "by_tariff": {
                tariff: data.get(feature, 0)
                for tariff, data in self.tariff_distribution.items()
            }
        }