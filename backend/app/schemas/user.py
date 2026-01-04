from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from ..core.constants import UserRole, TariffType
from .base import BaseSchema

class WebAppData(BaseModel):
    """Схема данных WebApp"""
    platform: Optional[str] = None
    version: Optional[str] = None
    theme_params: Optional[Dict] = None


class TelegramUserData(BaseSchema):
    """Данные пользователя из Telegram"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None


class UserBase(BaseSchema):
    """Базовая схема пользователя"""
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class UserCreate(UserBase):
    """Схема создания пользователя"""
    invited_by_code: Optional[str] = None
    is_premium: bool = False
    platform: Optional[str] = None
    webapp_version: Optional[str] = None
    theme_params: Optional[Dict] = None


class UserUpdate(BaseSchema):
    """Схема обновления пользователя"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_friend: Optional[bool] = None
    has_access: Optional[bool] = None
    tariff: Optional[TariffType] = None
    tariff_valid_until: Optional[datetime] = None
    points: Optional[int] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None
    platform: Optional[str] = None
    webapp_version: Optional[str] = None
    theme_params: Optional[Dict] = None


class UserInDB(UserBase):
    """Полная схема пользователя из БД"""
    id: int
    role: UserRole = Field(default=UserRole.USER)
    is_friend: bool = Field(default=False)
    has_access: bool = Field(default=False)
    is_premium: bool = Field(default=False)

    platform: Optional[str] = None
    webapp_version: Optional[str] = None
    theme_params: Optional[Dict] = None

    invite_code: Optional[str] = None
    invited_by_code: Optional[str] = None
    invites_count: int = Field(default=0)
    total_earned_discount: int = Field(default=0)

    tariff: Optional[TariffType] = None
    tariff_valid_until: Optional[datetime] = None
    points: int = Field(default=0)

    created_at: datetime
    last_active: datetime
    unsubscribed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserList(BaseSchema):
    """Список пользователей с пагинацией"""
    items: List[UserInDB]
    total: int

    class Config:
        from_attributes = True


class UserStats(BaseSchema):
    """User statistics for content generation"""
    daily_generations: int = Field(default=0)
    daily_images: int = Field(default=0)
    total_generations: int = Field(default=0)
    total_images: int = Field(default=0)
    points: int = Field(default=0)
    last_active: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserResponse(BaseSchema):
    """Ответ с данными пользователя и токеном"""
    access_token: str
    token_type: str = "bearer"
    user: UserInDB
    webapp_data: Optional[WebAppData] = None
    stats: Optional[UserStats] = None
    limits: Optional[Dict[str, int]] = None

    class Config:
        from_attributes = True

class UserSettings(BaseSchema):
    language: str = Field(default="en")
    notifications_enabled: bool = Field(default=True)
    theme: str = Field(default="default")

class UserProfile(BaseSchema):
    """Расширенный профиль пользователя"""
    user: UserInDB
    settings: UserSettings
    statistics: UserStats
    telegram_data: TelegramUserData

class UserSession(BaseSchema):
    """Сессия пользователя"""
    session_id: str
    created_at: datetime
    last_active: datetime
    platform: Optional[str] = None
    webapp_version: Optional[str] = None

