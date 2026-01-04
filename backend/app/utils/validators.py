# app/utils/validators.py
from typing import Optional
from datetime import datetime

def validate_telegram_id(telegram_id: int) -> bool:
    return isinstance(telegram_id, int) and telegram_id > 0

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    return start_date < end_date

def validate_generation_limit(current_count: int, max_limit: int) -> bool:
    return current_count < max_limit