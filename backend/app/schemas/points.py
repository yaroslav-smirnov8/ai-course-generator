# app/schemas/points.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    GENERATION = "generation"
    PURCHASE = "purchase"
    REWARD = "reward"
    REFUND = "refund"
    INVITE_BONUS = "invite_bonus"
    ACHIEVEMENT = "achievement"
    ADMIN_CORRECTION = "admin_correction"


class PointTransactionCreate(BaseModel):
    amount: int = Field(gt=0, description="Amount of points")
    type: TransactionType
    description: Optional[str] = None
    meta_data: Optional[dict] = None


class PointTransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: int
    type: TransactionType
    description: Optional[str]
    created_at: datetime
    meta_data: Optional[dict]
    # Добавляем поле для отображения баланса после транзакции
    balance_after: int

    class Config:
        from_attributes = True


class PointBalanceResponse(BaseModel):
    user_id: int
    points: int
    last_updated: datetime

    # Добавляем дополнительную информацию о лимитах
    daily_generation_limit: Optional[int] = None
    daily_generations_used: Optional[int] = None
    daily_image_limit: Optional[int] = None
    daily_images_used: Optional[int] = None


class BulkPointTransactionCreate(BaseModel):
    transactions: list[PointTransactionCreate]
    description: Optional[str] = None


class TransactionStatistics(BaseModel):
    total_earned: int
    total_spent: int
    average_transaction: float
    most_common_type: TransactionType
    transactions_count: int
    first_transaction_date: Optional[datetime]
    last_transaction_date: Optional[datetime]