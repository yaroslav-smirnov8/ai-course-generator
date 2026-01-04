# app/schemas/points_purchase.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PaymentMethod(str, Enum):
    TELEGRAM = "telegram"
    CARD = "card"
    CRYPTO = "crypto"

class PurchaseStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"

class PurchasePackage(BaseModel):
    id: int
    points: int
    price: float
    bonus: int = 0
    description: Optional[str] = None
    is_popular: bool = False
    currency: str = "USD"

class PurchaseRequest(BaseModel):
    amount: int = Field(gt=0, description="Amount of points to purchase")
    price: float = Field(gt=0, description="Price in specified currency")
    bonus: int = Field(ge=0, description="Bonus points")
    payment_method: PaymentMethod
    package_id: Optional[int] = None
    currency: str = "USD"
    meta_data: Optional[dict] = None

class PurchaseResponse(BaseModel):
    payment_id: str
    user_id: int
    amount: int
    price: float
    bonus: int
    status: PurchaseStatus
    payment_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    meta_data: Optional[dict] = None

    class Config:
        from_attributes = True

class PurchaseConfirmation(BaseModel):
    payment_id: str
    confirmation_data: Optional[dict] = None

class PurchaseHistory(BaseModel):
    id: str
    user_id: int
    amount: int
    price: float
    bonus: int
    status: PurchaseStatus
    payment_method: PaymentMethod
    created_at: datetime
    completed_at: Optional[datetime]
    meta_data: Optional[dict] = None

    class Config:
        from_attributes = True

class PurchaseStatistics(BaseModel):
    total_purchases: int
    total_points_purchased: int
    total_spent: float
    average_purchase_amount: float
    most_popular_package: Optional[PurchasePackage]
    purchase_by_method: dict[PaymentMethod, int]
    daily_stats: List[dict]
    monthly_stats: List[dict]

class PromotionalOffer(BaseModel):
    id: int
    title: str
    description: str
    bonus_percentage: float
    min_amount: int
    max_amount: Optional[int]
    valid_from: datetime
    valid_until: Optional[datetime]
    is_active: bool
    conditions: Optional[dict] = None

    class Config:
        from_attributes = True

class PurchaseRefund(BaseModel):
    payment_id: str
    reason: str
    refund_amount: Optional[float] = None
    partial: bool = False
    meta_data: Optional[dict] = None