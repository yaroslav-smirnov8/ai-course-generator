from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from ..core.constants import ActionType, ContentType
from .base import BaseSchema


class AchievementCheckRequest(BaseModel):
    user_id: int
    action_type: str  # Changed from ActionType to str
    action_data: dict


class AchievementBase(BaseSchema):
    """Базовая схема достижения"""
    code: str
    name: str
    description: str
    icon: Optional[str] = None
    points_reward: int = Field(default=0, ge=0)
    conditions: Dict[str, Any] = Field(default_factory=dict)


class AchievementCreate(AchievementBase):
    """Схема для создания достижения"""
    pass


class AchievementUpdate(BaseSchema):
    """Схема для обновления достижения"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    points_reward: Optional[int] = Field(None, ge=0)
    conditions: Optional[Dict[str, Any]] = None


class AchievementResponse(AchievementBase):
    """Схема для ответа с достижением"""
    id: int

    class Config:
        from_attributes = True


class UserAchievementBase(BaseSchema):
    """Базовая схема достижения пользователя"""
    achievement_id: int
    progress: int = Field(default=0, ge=0, le=100)
    unlocked: bool = False


class UserAchievementCreate(UserAchievementBase):
    """Схема для создания достижения пользователя"""
    user_id: int


class UserAchievementUpdate(BaseSchema):
    """Схема для обновления достижения пользователя"""
    progress: Optional[int] = Field(None, ge=0, le=100)
    unlocked: Optional[bool] = None


class UserAchievementResponse(BaseSchema):
    """Схема для ответа с достижением пользователя"""
    achievement: AchievementResponse
    unlocked_at: Optional[datetime]
    progress: int
    unlocked: bool
    last_updated: datetime

    class Config:
        from_attributes = True


class UserActionBase(BaseSchema):
    """Базовая схема действия пользователя"""
    user_id: int
    action_type: ActionType
    content_type: Optional[ContentType] = None


class UserActionCreate(UserActionBase):
    """Схема для создания действия пользователя"""
    pass


class UserActionResponse(UserActionBase):
    """Схема для ответа с действием пользователя"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementProgress(BaseSchema):
    """Схема для отображения прогресса по достижениям"""
    total_achievements: int
    unlocked_achievements: int
    total_points_earned: int
    next_achievements: List[AchievementResponse]
    recent_unlocks: List[UserAchievementResponse]

    class Config:
        from_attributes = True


class AchievementUnlockStat(BaseSchema):
    """Статистика разблокировки достижения"""
    achievement_id: int
    name: str
    description: str
    icon: Optional[str] = None
    unlock_count: int
    points_reward: int


class AchievementTimePoint(BaseSchema):
    """Точка данных для графика разблокировки достижений"""
    date: str
    count: int


class AchievementAnalyticsResponse(BaseSchema):
    """Схема для ответа с аналитикой достижений"""
    total_achievements: int
    unlocked_achievements: int
    total_points_earned: int
    active_users: int
    popular_achievements: List[AchievementUnlockStat]
    unlocks_over_time: List[AchievementTimePoint]
    period: str