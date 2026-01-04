# app/schemas/pricing.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import BaseSchema
from ..core.constants import TariffType

class TariffBase(BaseSchema):
    """Базовая схема тарифа"""
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(gt=0)
    generations_limit: int = Field(ge=0)
    images_limit: int = Field(ge=0)
    features: Dict[str, Any] = Field(default_factory=dict)


class TariffCreate(TariffBase):
    """Схема для создания тарифа.
    Наследует все поля от TariffBase:
    - name: str
    - price: float
    - generations_limit: int
    - images_limit: int
    - features: Dict[str, Any]
    """
    # Все поля наследуются от TariffBase
    # Можно добавить дополнительные валидаторы или метаданные если нужно
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Basic Plan",
                "price": 99.99,
                "generations_limit": 100,
                "images_limit": 50,
                "features": {
                    "priority_support": False,
                    "advanced_analytics": False
                }
            }
        }


class TariffUpdate(BaseModel):
    """Схема для обновления тарифа"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    generations_limit: Optional[int] = Field(None, ge=0)
    images_limit: Optional[int] = Field(None, ge=0)
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DailyLimits(BaseModel):
    """Дневные лимиты для тарифа"""
    generations: int = Field(..., description="Дневной лимит генераций")
    images: int = Field(..., description="Дневной лимит изображений")


class TariffInfo(BaseModel):
    """Информация о тарифе пользователя"""
    type: TariffType = Field(..., description="Тип тарифа")
    validUntil: Optional[datetime] = Field(None, description="Дата окончания тарифа")
    limits: DailyLimits = Field(..., description="Дневные лимиты")
    pricePoints: int = Field(..., description="Стоимость тарифа в баллах")
    features: Dict[str, Any] = Field(default_factory=dict, description="Особенности тарифа")
    name: str = Field(..., description="Название тарифа")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TariffResponse(BaseModel):
    """Ответ с информацией о тарифе"""
    status: str = Field(..., description="Статус операции")
    message: str = Field(..., description="Сообщение об операции")
    data: Optional[TariffInfo] = Field(None, description="Данные тарифа")


class UserTariffHistory(BaseModel):
    """История тарифов пользователя"""
    id: int = Field(..., description="ID записи")
    tariff_type: TariffType = Field(..., description="Тип тарифа")
    started_at: datetime = Field(..., description="Дата начала действия")
    expires_at: Optional[datetime] = Field(None, description="Дата окончания действия")
    is_active: bool = Field(..., description="Активен ли тариф")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TariffUpdate(BaseModel):
    """Обновление тарифа пользователя"""
    tariff_type: TariffType = Field(..., description="Новый тип тарифа")


class TariffExtension(BaseModel):
    """Продление тарифа"""
    months: int = Field(1, ge=1, le=12, description="Количество месяцев для продления")

    @validator("months")
    def validate_months(cls, v):
        if v <= 0:
            raise ValueError("Количество месяцев должно быть положительным")
        if v > 12:
            raise ValueError("Максимальное количество месяцев для продления - 12")
        return v


class PriceChangeBase(BaseModel):
    """Базовая схема изменения цены"""
    tariff_id: int
    new_price: float = Field(gt=0)
    scheduled_date: datetime
    reason: Optional[str] = None


class PriceChangeCreate(PriceChangeBase):
    """Схема для создания изменения цены.
    Наследует все поля от PriceChangeBase:
    - tariff_id: int
    - new_price: float
    - scheduled_date: datetime
    - reason: Optional[str]
    """
    # Дополнительная валидация, если нужна
    @validator('scheduled_date')
    def validate_scheduled_date(cls, v):
        if v < datetime.utcnow():
            raise ValueError('scheduled_date must be in the future')
        return v


class PriceChangeResponse(PriceChangeBase):
    """Полная схема изменения цены"""
    id: int
    old_price: float
    change_date: datetime
    is_applied: bool

    class Config:
        from_attributes = True

class SpecialOfferBase(BaseModel):
    """Базовая схема специального предложения"""
    tariff_id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    discount_percent: float = Field(..., ge=0, le=100)
    start_date: datetime
    end_date: datetime
    limitations: Dict[str, Any] = Field(default_factory=dict)

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class SpecialOfferCreate(BaseModel):
    """Схема для создания специального предложения"""
    tariff_id: int = Field(..., description="ID тарифного плана")
    name: str = Field(..., min_length=1, max_length=100, description="Название предложения")
    description: Optional[str] = Field(None, max_length=500, description="Описание предложения")
    discount_percent: float = Field(..., ge=0, le=100, description="Процент скидки")
    start_date: datetime = Field(..., description="Дата начала действия")
    end_date: datetime = Field(..., description="Дата окончания действия")
    limitations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Ограничения на использование предложения"
    )

class SpecialOfferUpdate(BaseModel):
    """Схема для обновления специального предложения"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    limitations: Optional[Dict[str, Any]] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values:
            start_date = values.get('start_date')
            if start_date and v <= start_date:
                raise ValueError('end_date must be after start_date')
        return v

class SpecialOffer(SpecialOfferBase):
    """Полная схема специального предложения"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DiscountCreate(BaseModel):
    """Схема для создания скидки"""
    name: str = Field(..., min_length=1, max_length=100, description="Название скидки")
    description: Optional[str] = Field(None, max_length=500, description="Описание скидки")
    discount_type: str = Field(
        ..., 
        pattern='^(percentage|fixed)$',
        description="Тип скидки: процент или фиксированная сумма"
    )
    value: float = Field(..., gt=0, description="Значение скидки")
    user_id: Optional[int] = Field(None, description="ID пользователя, если скидка персональная")
    tariff_id: Optional[int] = Field(None, description="ID тарифа, если скидка для конкретного тарифа")
    start_date: Optional[datetime] = Field(None, description="Дата начала действия")
    end_date: Optional[datetime] = Field(None, description="Дата окончания действия")
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Условия применения скидки"
    )

    @validator('value')
    def validate_value(cls, v, values):
        if values.get('discount_type') == 'percentage' and v > 100:
            raise ValueError('Percentage discount cannot exceed 100%')
        return v

    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class DiscountUpdate(BaseModel):
    """Схема для обновления скидки"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discount_type: Optional[str] = Field(None, pattern='^(percentage|fixed)$')
    value: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None

    @validator('value')
    def validate_value(cls, v, values):
        if v is not None and values.get('discount_type') == 'percentage' and v > 100:
            raise ValueError('Percentage discount cannot exceed 100%')
        return v

class Discount(BaseModel):
    """Полная схема скидки"""
    id: int
    name: str
    description: Optional[str]
    discount_type: str
    value: float
    user_id: Optional[int]
    tariff_id: Optional[int]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool
    conditions: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PricingRuleCreate(BaseModel):
    """Схема для создания правила ценообразования"""
    name: str = Field(..., min_length=1, max_length=100, description="Название правила")
    rule_type: str = Field(
        ..., 
        pattern='^(markup|discount|fixed|dynamic)$',
        description="Тип правила ценообразования"
    )
    parameters: Dict[str, Any] = Field(..., description="Параметры правила")
    priority: int = Field(
        ..., 
        ge=0,
        description="Приоритет правила (чем выше значение, тем важнее правило)"
    )
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Условия применения правила"
    )

class PricingRuleUpdate(BaseModel):
    """Схема для обновления правила ценообразования"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0)
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class PricingRule(BaseModel):
    """Полная схема правила ценообразования"""
    id: int
    name: str
    rule_type: str
    parameters: Dict[str, Any]
    priority: int
    conditions: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PriceCalculation(BaseModel):
    """Схема результата расчета цены"""
    base_price: float = Field(..., description="Базовая цена до применения скидок")
    final_price: float = Field(..., description="Финальная цена после всех скидок")
    applied_discounts: Dict[str, float] = Field(
        ...,
        description="Примененные скидки и их значения"
    )
    applied_rules: List[Dict[str, Any]] = Field(
        ...,
        description="Примененные правила ценообразования"
    )

    class Config:
        from_attributes = True

class AppliedDiscountCreate(BaseModel):
    """Схема для создания записи о примененной скидке"""
    user_id: int = Field(..., description="ID пользователя")
    discount_id: int = Field(..., description="ID скидки")
    amount: float = Field(..., gt=0, description="Сумма скидки")
    purchase_id: int = Field(..., description="ID транзакции покупки")

class AppliedDiscount(BaseModel):
    """Полная схема примененной скидки"""
    id: int
    user_id: int
    discount_id: int
    amount: float
    applied_at: datetime
    purchase_id: int

    class Config:
        from_attributes = True