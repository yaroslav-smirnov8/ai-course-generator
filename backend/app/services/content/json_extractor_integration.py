#!/usr/bin/env python3
"""
Модуль для интеграции улучшенного извлекателя JSON с существующим кодом.
Обеспечивает совместимость с текущими функциями и добавляет новую функциональность.
"""
import json
import logging
from typing import Dict, Any, Optional

# Импортируем улучшенный извлекатель JSON
try:
    from .improved_json_extractor import extract_json_from_api_response, process_api_response
    IMPROVED_EXTRACTOR_AVAILABLE = True
except ImportError:
    IMPROVED_EXTRACTOR_AVAILABLE = False

# Настройка логирования
logger = logging.getLogger(__name__)

def extract_json_safely(content: str, debug: bool = False, use_improved: bool = True) -> str:
    """
    Извлекает JSON-строку из контента, используя улучшенный извлекатель,
    если он доступен и включен.
    
    Args:
        content: Исходный контент
        debug: Включить подробное логирование
        use_improved: Использовать улучшенный извлекатель (если доступен)
        
    Returns:
        str: JSON-строка или исходный контент, если не удалось извлечь JSON
    """
    if not content or len(content.strip()) < 5:
        logger.warning("Контент слишком короткий для JSON")
        return ""
    
    if use_improved and IMPROVED_EXTRACTOR_AVAILABLE:
        logger.info("Используем улучшенный извлекатель JSON")
        return extract_json_from_api_response(content, debug=debug)
    else:
        # Если улучшенный извлекатель недоступен или отключен,
        # просто возвращаем исходный контент для дальнейшей обработки
        # стандартными методами
        logger.info("Используем стандартную обработку JSON")
        return content

def parse_json_safely(json_str: str, debug: bool = False, use_improved: bool = True) -> Optional[Dict[str, Any]]:
    """
    Безопасно парсит JSON строку в словарь, используя улучшенный извлекатель,
    если он доступен и включен.
    
    Args:
        json_str: JSON строка
        debug: Включить подробное логирование
        use_improved: Использовать улучшенный парсер (если доступен)
        
    Returns:
        Optional[Dict[str, Any]]: Распарсенный словарь или None в случае ошибки
    """
    if not json_str or len(json_str.strip()) < 2:
        logger.error("Получена пустая или слишком короткая JSON-строка")
        return None
    
    if use_improved and IMPROVED_EXTRACTOR_AVAILABLE:
        logger.info("Используем улучшенный парсер JSON")
        result, success = process_api_response(json_str, debug=debug)
        if success:
            return result
        else:
            logger.warning("Улучшенный парсер не смог обработать JSON, возвращаем None")
            return None
    else:
        logger.info("Используем стандартный парсер JSON")
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
            return None

def integrate_with_content_generator(generator_instance):
    """
    Интегрирует улучшенный извлекатель JSON с экземпляром ContentGenerator.
    
    Args:
        generator_instance: Экземпляр класса ContentGenerator
    """
    if not IMPROVED_EXTRACTOR_AVAILABLE:
        logger.warning("Улучшенный извлекатель JSON недоступен, интеграция невозможна")
        return
    
    # Сохраняем оригинальные методы
    original_extract = generator_instance._extract_json_from_content
    original_parse = generator_instance._parse_json_safely
    
    # Заменяем метод _extract_json_from_content
    def enhanced_extract_json_from_content(self, content: str) -> str:
        """
        Усиленная версия _extract_json_from_content, использующая улучшенный извлекатель.
        """
        logger.info("Вызов усиленного метода извлечения JSON")
        # Сначала пробуем использовать улучшенный извлекатель
        extracted = extract_json_safely(content, debug=True, use_improved=True)
        
        # Если улучшенный извлекатель вернул пустую строку, используем оригинальный метод
        if not extracted:
            logger.info("Улучшенный извлекатель не нашел JSON, используем оригинальный метод")
            return original_extract(self, content)
        
        return extracted
    
    # Заменяем метод _parse_json_safely
    async def enhanced_parse_json_safely(self, json_str: str) -> Dict[str, Any]:
        """
        Усиленная версия _parse_json_safely, использующая улучшенный парсер.
        """
        logger.info("Вызов усиленного метода парсинга JSON")
        # Сначала пробуем использовать улучшенный парсер
        parsed = parse_json_safely(json_str, debug=True, use_improved=True)
        
        # Если улучшенный парсер не смог обработать JSON, используем оригинальный метод
        if parsed is None:
            logger.info("Улучшенный парсер не смог обработать JSON, используем оригинальный метод")
            return await original_parse(self, json_str)
        
        return parsed
    
    # Заменяем методы
    import types
    generator_instance._extract_json_from_content = types.MethodType(enhanced_extract_json_from_content, generator_instance)
    generator_instance._parse_json_safely = types.MethodType(enhanced_parse_json_safely, generator_instance)
    
    logger.info("Улучшенный извлекатель JSON успешно интегрирован с ContentGenerator") 