# app/models/broadcast.py
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from datetime import datetime
from ..core.database import Base


class ScheduledMessage(AsyncAttrs, Base):
    """Модель для запланированных сообщений рассылки"""
    __tablename__ = 'scheduled_messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=True)
    message_photo_path: Mapped[str] = mapped_column(String(500), nullable=True)
    message_photo_caption: Mapped[str] = mapped_column(Text, nullable=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Admin telegram_id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    recipients_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
