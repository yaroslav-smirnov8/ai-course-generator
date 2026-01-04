# app/core/enums.py
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    FRIEND = "friend"
    MOD = "mod"

class TransactionType(str, Enum):
    """Типы транзакций с баллами"""
    GENERATION = "generation"  # Списание за генерацию контента
    REWARD = "reward"  # Начисление за достижения/активность
    PURCHASE = "purchase"  # Покупка баллов
    ADMIN_ADD = "admin_add"  # Начисление администратором
    ADMIN_SUBTRACT = "admin_subtract"  # Списание администратором
    REFERRAL = "referral"  # Начисление за реферала
    DAILY_BONUS = "daily_bonus"  # Ежедневный бонус