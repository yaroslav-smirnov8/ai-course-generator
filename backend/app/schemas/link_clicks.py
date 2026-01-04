from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LinkClickCreate(BaseModel):
    """Схема для создания записи о переходе по ссылке"""
    link_id: str = Field(..., description="Идентификатор ссылки")
    link_title: str = Field(..., description="Название ссылки")
    link_url: str = Field(..., description="URL ссылки")
    user_id: Optional[int] = Field(None, description="ID пользователя, который кликнул по ссылке")


class LinkClickResponse(BaseModel):
    """Схема для ответа с информацией о переходе по ссылке"""
    id: int
    link_id: str
    link_title: str
    link_url: str
    user_id: Optional[int] = None
    clicked_at: datetime

    class Config:
        orm_mode = True


class LinkClicksAnalyticsResponse(BaseModel):
    """Схема для ответа с аналитикой по переходам по ссылкам"""
    total_clicks: int = Field(..., description="Общее количество переходов")
    unique_users: int = Field(..., description="Количество уникальных пользователей")
    popular_links: List[Dict[str, Any]] = Field(..., description="Популярные ссылки")
    clicks_by_time: List[Dict[str, Any]] = Field(..., description="Переходы по времени")
    period: str = Field(..., description="Период анализа (week, month, year, all)")
