from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PromoCodeType(str, Enum):
    """Тип промокода"""
    POINTS = "points"
    TARIFF = "tariff"
    DISCOUNT = "discount"


class PromoCodeUsageType(str, Enum):
    """Тип использования промокода"""
    UNLIMITED = "unlimited"
    LIMITED = "limited"
    SINGLE_USER = "single_user"


class PromoCodeBase(BaseModel):
    """Базовая схема промокода"""
    name: str = Field(..., min_length=1, max_length=100, description="Название промокода")
    description: Optional[str] = Field(None, max_length=500, description="Описание промокода")
    type: PromoCodeType = Field(..., description="Тип промокода")
    usage_type: PromoCodeUsageType = Field(..., description="Тип использования")
    
    # Значения
    points_amount: Optional[int] = Field(0, ge=0, description="Количество баллов")
    tariff_type: Optional[str] = Field(None, description="Тип тарифа")
    tariff_duration_months: Optional[int] = Field(1, ge=1, le=12, description="Длительность тарифа в месяцах")
    discount_percent: Optional[float] = Field(0.0, ge=0.0, le=100.0, description="Процент скидки")
    
    # Ограничения
    usage_limit: Optional[int] = Field(None, ge=1, description="Лимит использований")
    user_id: Optional[int] = Field(None, description="ID пользователя для персонального промокода")
    
    # Временные ограничения
    valid_until: Optional[datetime] = Field(None, description="Дата окончания действия")
    
    # Дополнительные условия
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные условия")

    @validator('tariff_type')
    def validate_tariff_type(cls, v, values):
        if values.get('type') == PromoCodeType.TARIFF and not v:
            raise ValueError('Для тарифного промокода необходимо указать тип тарифа')
        if v and v not in ['tariff_2', 'tariff_4', 'tariff_6']:
            raise ValueError('Недопустимый тип тарифа')
        return v

    @validator('points_amount')
    def validate_points_amount(cls, v, values):
        if values.get('type') == PromoCodeType.POINTS and v <= 0:
            raise ValueError('Для баллового промокода необходимо указать количество баллов больше 0')
        return v

    @validator('discount_percent')
    def validate_discount_percent(cls, v, values):
        if values.get('type') == PromoCodeType.DISCOUNT and v <= 0:
            raise ValueError('Для скидочного промокода необходимо указать процент скидки больше 0')
        return v

    @validator('user_id')
    def validate_user_id(cls, v, values):
        if values.get('usage_type') == PromoCodeUsageType.SINGLE_USER and not v:
            raise ValueError('Для персонального промокода необходимо указать ID пользователя')
        return v


class PromoCodeCreate(PromoCodeBase):
    """Схема для создания промокода"""
    code: Optional[str] = Field(None, min_length=3, max_length=50, description="Код промокода (если не указан, будет сгенерирован)")


class PromoCodeUpdate(BaseModel):
    """Схема для обновления промокода"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    usage_limit: Optional[int] = Field(None, ge=1)
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None


class PromoCodeResponse(PromoCodeBase):
    """Схема ответа промокода"""
    id: int
    code: str
    usage_count: int
    is_active: bool
    valid_from: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    # Вычисляемые поля
    is_valid: bool
    remaining_uses: Optional[int]

    class Config:
        from_attributes = True


class PromoCodeUsageBase(BaseModel):
    """Базовая схема использования промокода"""
    points_added: Optional[int] = 0
    tariff_activated: Optional[str] = None
    tariff_duration: Optional[int] = None
    discount_applied: Optional[float] = 0.0


class PromoCodeUsageCreate(BaseModel):
    """Схема для создания записи об использовании"""
    code: str = Field(..., description="Код промокода")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class PromoCodeUsageResponse(PromoCodeUsageBase):
    """Схема ответа использования промокода"""
    id: int
    promocode_id: int
    user_id: int
    used_at: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class PromoCodeApplyRequest(BaseModel):
    """Запрос на применение промокода"""
    code: str = Field(..., min_length=1, max_length=50, description="Код промокода")


class PromoCodeApplyResponse(BaseModel):
    """Ответ на применение промокода"""
    success: bool
    message: str
    promocode: Optional[PromoCodeResponse] = None
    usage: Optional[PromoCodeUsageResponse] = None
    
    # Что было применено
    points_added: Optional[int] = 0
    tariff_activated: Optional[str] = None
    tariff_duration: Optional[int] = None
    discount_applied: Optional[float] = 0.0


class PromoCodeListResponse(BaseModel):
    """Ответ со списком промокодов"""
    items: List[PromoCodeResponse]
    total: int
    page: int
    size: int
    pages: int


class PromoCodeStatsResponse(BaseModel):
    """Статистика промокодов"""
    total_promocodes: int
    active_promocodes: int
    expired_promocodes: int
    used_promocodes: int
    total_usages: int
    total_points_distributed: int
    total_tariffs_activated: int
    most_popular_promocodes: List[Dict[str, Any]]
    usage_by_type: Dict[str, int]
    usage_by_month: List[Dict[str, Any]]
