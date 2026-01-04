"""
Утилиты для работы с различными типами данных и преобразованиями.
"""
import logging
from typing import Optional, TypeVar, Type, Any, Union
from enum import Enum

from .constants import ContentType, ActionType

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Enum)

def safe_enum_convert(value: Any, enum_class: Type[T], default: Optional[T] = None) -> Optional[T]:
    """
    Безопасно конвертирует строку или другое значение в экземпляр Enum.
    Пробует различные способы конвертации, включая учет регистра.
    
    Args:
        value: Значение для конвертации
        enum_class: Класс перечисления (Enum)
        default: Значение по умолчанию, если конвертация не удалась
        
    Returns:
        Экземпляр Enum или default, если конвертация не удалась
    """
    if value is None:
        return default
        
    # Если уже правильный тип, вернуть как есть
    if isinstance(value, enum_class):
        return value
        
    try:
        # Пробуем точное совпадение
        return enum_class(value)
    except (ValueError, TypeError):
        if isinstance(value, str):
            try:
                # Пробуем верхний регистр
                return enum_class(value.upper())
            except (ValueError, TypeError):
                try:
                    # Пробуем по имени enum (LESSON_PLAN для "lesson_plan")
                    enum_name = value.upper()
                    return enum_class[enum_name]
                except (KeyError, ValueError):
                    # Ищем неточные совпадения (с игнорированием регистра)
                    for item in enum_class:
                        if isinstance(item.value, str) and item.value.lower() == value.lower():
                            return item
    
    # Если не удалось сконвертировать, логируем и возвращаем значение по умолчанию
    logger.warning(f"Не удалось сконвертировать '{value}' в {enum_class.__name__}")
    return default

def safe_content_type(value: Any) -> Optional[ContentType]:
    """
    Безопасно конвертирует значение в ContentType.
    
    Args:
        value: Значение для конвертации
        
    Returns:
        Экземпляр ContentType или None, если конвертация не удалась
    """
    return safe_enum_convert(value, ContentType)

def safe_action_type(value: Any) -> Optional[ActionType]:
    """
    Безопасно конвертирует значение в ActionType.
    
    Args:
        value: Значение для конвертации
        
    Returns:
        Экземпляр ActionType или None, если конвертация не удалась
    """
    return safe_enum_convert(value, ActionType) 