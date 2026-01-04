from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, JSON, Enum, String
from datetime import datetime, timezone
from typing import Optional, Dict
from ..core.database import Base
from ..core.constants import ActionType, ContentType


class Achievement(AsyncAttrs, Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255))
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    conditions: Mapped[Dict] = mapped_column(JSON)
    points_reward: Mapped[int] = mapped_column(default=0)

    # Связи
    user_achievements = relationship("UserAchievement", back_populates="achievement", lazy="selectin")


class UserAchievement(AsyncAttrs, Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"), nullable=False)
    progress: Mapped[int] = mapped_column(default=0)
    unlocked: Mapped[bool] = mapped_column(default=False)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_updated: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Связи
    user = relationship("User", back_populates="achievements", lazy="selectin")
    achievement = relationship("Achievement", back_populates="user_achievements", lazy="selectin")


class UserAction(AsyncAttrs, Base):
    __tablename__ = "user_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType))
    content_type: Mapped[Optional[ContentType]] = mapped_column(Enum(ContentType), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Связи
    user = relationship("User", back_populates="actions", lazy="selectin")