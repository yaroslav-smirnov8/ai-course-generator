from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from ..core.database import Base


class LinkClick(Base):
    """Модель для хранения данных о переходах по ссылкам"""
    __tablename__ = "link_clicks"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(String(50), index=True, nullable=False)
    link_title = Column(String(255), nullable=False)
    link_url = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Используем timezone-naive datetime для совместимости с базой данных
    clicked_at = Column(DateTime, default=lambda: datetime.now().replace(microsecond=0), nullable=False)

    # Отношения
    user = relationship("User", back_populates="link_clicks")


# Обратное отношение уже добавлено в модель User
