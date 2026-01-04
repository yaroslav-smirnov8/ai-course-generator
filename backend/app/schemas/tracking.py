from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from ..core.constants import ActionType, ContentType

class UsageLogBase(BaseModel):
    """Базовая схема для лога использования"""
    user_id: int
    action_type: str  # Changed from ActionType to str
    content_type: Optional[str] = None  # Changed from ContentType to str
    extra_data: Dict[str, Any] = Field(default_factory=dict)

class UsageLogCreate(UsageLogBase):
    """Схема для создания лога использования"""
    points_change: int = Field(default=0)
    daily_usage_count: int = Field(default=1)
    skip_limits: bool = Field(default=False)  # Флаг для пропуска лимитов (генерация за баллы)

class UsageLogResponse(UsageLogBase):
    """Схема для ответа с логом использования"""
    id: int
    points_change: int
    daily_usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class DailyUsageBase(BaseModel):
    """Базовая схема для дневного использования"""
    user_id: int
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generations_count: int = Field(default=0)
    lesson_plans_count: int = Field(default=0)
    exercises_count: int = Field(default=0)
    games_count: int = Field(default=0)
    images_count: int = Field(default=0)
    transcripts_count: int = Field(default=0)
    points_earned: int = Field(default=0)
    points_spent: int = Field(default=0)

class DailyUsageCreate(DailyUsageBase):
    """Схема для создания дневного использования"""
    pass

class DailyUsageResponse(DailyUsageBase):
    """Схема для ответа с дневным использованием"""
    id: int

    class Config:
        from_attributes = True

class GenerationMetricsBase(BaseModel):
    """Базовая схема для метрик генерации"""
    user_id: int
    content_type: str  # Changed from ContentType to str
    prompt: str
    tokens_used: int
    generation_time: float
    success: bool = Field(default=True)
    error_type: Optional[str] = None

class GenerationMetricsCreate(GenerationMetricsBase):
    """Схема для создания метрик генерации"""
    pass

class GenerationMetricsResponse(GenerationMetricsBase):
    """Схема для ответа с метриками генерации"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserActivityLogBase(BaseModel):
    """Базовая схема для лога активности пользователя"""
    user_id: int
    action_type: str  # Changed from ActionType to str
    content_type: Optional[str] = None  # Changed from ContentType to str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    activity_metadata: Dict[str, Any] = Field(default_factory=dict)

class UserActivityLogCreate(UserActivityLogBase):
    """Схема для создания лога активности"""
    pass

class UserActivityLogResponse(UserActivityLogBase):
    """Схема для ответа с логом активности"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UsageStatisticsBase(BaseModel):
    """Базовая схема для статистики использования"""
    user_id: int
    period_start: datetime
    period_end: datetime
    total_generations: int = Field(default=0)
    total_images: int = Field(default=0)
    active_days: int = Field(default=0)
    points_earned: int = Field(default=0)
    points_spent: int = Field(default=0)
    generations_by_type: Dict[str, int] = Field(default_factory=dict)
    popular_prompts: Dict[str, list] = Field(default_factory=dict)
    avg_daily_generations: float = Field(default=0.0)
    avg_daily_images: float = Field(default=0.0)

class UsageStatisticsCreate(UsageStatisticsBase):
    """Схема для создания статистики использования"""
    pass

class UsageStatisticsResponse(UsageStatisticsBase):
    """Схема для ответа со статистикой использования"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AppUsageEvent(BaseModel):
    event: str
    user_id: Optional[Union[str, int]] = None
    platform: Optional[str] = None
    version: Optional[str] = None
    timestamp: str
    page: Optional[str] = None
    action: Optional[str] = None
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    duration_seconds: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "event": "app_launch",
                "user_id": "123456789",
                "platform": "WebApp",
                "version": "8.0",
                "timestamp": "2025-03-16T15:38:17.098535",
                "details": {}
            }
        }