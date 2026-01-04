from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TelegramUserData(BaseModel):
    id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    language_code: Optional[str]

class UserSettings(BaseModel):
    language: str
    notifications_enabled: bool = True
    theme: str = "default"

class UserStatistics(BaseModel):
    total_generations: int = 0
    daily_generations: int = 0
    total_images: int = 0
    achievements_count: int = 0
    last_active: datetime

class UserProfile(BaseModel):
    telegram_data: TelegramUserData
    settings: UserSettings
    statistics: UserStatistics
