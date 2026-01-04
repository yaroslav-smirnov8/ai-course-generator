# app/schemas/base.py
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Базовый класс для всех схем с общей конфигурацией"""
    model_config = ConfigDict(
        from_attributes=True,  # Поддержка ORM
        validate_assignment=True,  # Валидация при присваивании
        extra='forbid',  # Запрещаем дополнительные поля
        str_strip_whitespace=True,  # Убираем пробелы в строках
        strict=True  # Строгая проверка типов
    )