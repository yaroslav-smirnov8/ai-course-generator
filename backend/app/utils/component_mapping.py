"""
Модуль для маппинга типов контента на компоненты прокси.
Определяет, какой component_id использовать для разных типов генерации.
"""

from typing import Dict, Optional
from ..core.constants import ContentType

# Маппинг типов контента на Gemini компоненты
CONTENT_TYPE_TO_GEMINI_COMPONENT: Dict[ContentType, str] = {
    ContentType.EXERCISE: "exercises",
    ContentType.LESSON_PLAN: "lesson-plan",  # Обычные планы уроков через старый воркер
    ContentType.COURSE: "course-generator",
    ContentType.TEXT_ANALYSIS: "text-analyzer",
    ContentType.GAME: "games",
    ContentType.IMAGE: "exercises",  # Пока используем exercises для изображений
    ContentType.TRANSCRIPT: "text-analyzer",
    ContentType.STRUCTURED_DATA: "course-generator",
    # Новые типы для контента в курсе:
    ContentType.COURSE_LESSON_PLAN: "course-lesson-plan",   # Планы уроков в курсе
    ContentType.COURSE_EXERCISE: "course-exercises",        # Упражнения в курсе  
    ContentType.COURSE_GAME: "course-games"                 # Игры в курсе
}

# Маппинг типов контента на реальные воркеры (убрали groq- префиксы)
CONTENT_TYPE_TO_GROQ_COMPONENT: Dict[ContentType, str] = {
    ContentType.EXERCISE: "exercises",
    ContentType.LESSON_PLAN: "lesson-plan", 
    ContentType.COURSE: "course-generator",
    ContentType.TEXT_ANALYSIS: "text-analyzer",
    ContentType.GAME: "games",
    ContentType.IMAGE: "exercises",  # Пока используем exercises для изображений
    ContentType.TRANSCRIPT: "text-analyzer",
    ContentType.STRUCTURED_DATA: "course-generator",
    # Новые типы для контента в курсе используют специальные курсовые воркеры:
    ContentType.COURSE_LESSON_PLAN: "course-lesson-plan",   # Планы уроков в курсе
    ContentType.COURSE_EXERCISE: "course-exercises",        # Упражнения в курсе  
    ContentType.COURSE_GAME: "course-games"                 # Игры в курсе
}

# Дополнительный маппинг для строковых значений (обратная совместимость)
STRING_TO_GEMINI_COMPONENT: Dict[str, str] = {
    'exercise': "exercises",
    'lesson_plan': "lesson-plan",  # Обычные планы уроков через старый воркер
    'course': "course-generator", 
    'text_analysis': "text-analyzer",
    'game': "games",
    'image': "exercises",
    'transcript': "text-analyzer",
    'structured_data': "course-generator",
    # Новые типы для курсов:
    'course_lesson_plan': "course-lesson-plan",
    'course_exercise': "course-exercises", 
    'course_game': "course-games"
}

STRING_TO_GROQ_COMPONENT: Dict[str, str] = {
    'exercise': "exercises",
    'lesson_plan': "lesson-plan",
    'course': "course-generator",
    'text_analysis': "text-analyzer", 
    'game': "games",
    'image': "exercises",
    'transcript': "text-analyzer",
    'structured_data': "course-generator",
    # Новые типы для курсов используют специальные курсовые воркеры:
    'course_lesson_plan': "course-lesson-plan",
    'course_exercise': "course-exercises", 
    'course_game': "course-games"
}

def get_gemini_component_id(content_type) -> str:
    """
    Определяет Gemini component_id в зависимости от типа контента
    
    Args:
        content_type: Тип контента (ContentType enum или строка)
        
    Returns:
        str: Идентификатор Gemini компонента
    """
    # Если это enum ContentType
    if hasattr(content_type, 'value'):
        return CONTENT_TYPE_TO_GEMINI_COMPONENT.get(content_type, "exercises")
    
    # Если это строка
    if isinstance(content_type, str):
        return STRING_TO_GEMINI_COMPONENT.get(content_type, "exercises")
    
    # По умолчанию
    return "exercises"

def get_groq_component_id(content_type) -> str:
    """
    Определяет Groq component_id в зависимости от типа контента
    
    Args:
        content_type: Тип контента (ContentType enum или строка)
        
    Returns:
        str: Идентификатор Groq компонента
    """
    # Если это enum ContentType
    if hasattr(content_type, 'value'):
        return CONTENT_TYPE_TO_GROQ_COMPONENT.get(content_type, "exercises")
    
    # Если это строка
    if isinstance(content_type, str):
        return STRING_TO_GROQ_COMPONENT.get(content_type, "exercises")
    
    # По умолчанию
    return "exercises"

def get_component_id_for_provider(content_type, provider: str = "gemini") -> str:
    """
    Универсальная функция для получения component_id для любого провайдера
    
    Args:
        content_type: Тип контента
        provider: Провайдер ("gemini" или "groq")
        
    Returns:
        str: Идентификатор компонента
    """
    if provider.lower() == "groq":
        return get_groq_component_id(content_type)
    else:
        return get_gemini_component_id(content_type)

def is_groq_component(component_id: str) -> bool:
    """
    Проверяет, является ли компонент Groq компонентом
    
    Args:
        component_id: Идентификатор компонента
        
    Returns:
        bool: True если это Groq компонент
    """
    # Теперь у нас нет groq- префиксов, все воркеры одинаковые
    # Но оставляем функцию для совместимости
    return False

def get_provider_from_component_id(component_id: str) -> str:
    """
    Определяет провайдера по component_id
    
    Args:
        component_id: Идентификатор компонента
        
    Returns:
        str: "groq" или "gemini"
    """
    return "groq" if is_groq_component(component_id) else "gemini"

def get_base_component_name(component_id: str) -> str:
    """
    Получает базовое имя компонента без префикса провайдера
    
    Args:
        component_id: Идентификатор компонента
        
    Returns:
        str: Базовое имя компонента
    """
    # Теперь у нас нет префиксов, возвращаем как есть
    return component_id

def get_all_component_mappings() -> Dict[str, Dict[str, str]]:
    """
    Возвращает все маппинги компонентов для отладки
    
    Returns:
        Dict: Словарь со всеми маппингами
    """
    return {
        "gemini_enum_mapping": {str(k): v for k, v in CONTENT_TYPE_TO_GEMINI_COMPONENT.items()},
        "groq_enum_mapping": {str(k): v for k, v in CONTENT_TYPE_TO_GROQ_COMPONENT.items()},
        "gemini_string_mapping": STRING_TO_GEMINI_COMPONENT,
        "groq_string_mapping": STRING_TO_GROQ_COMPONENT
    }

# Функции для валидации
def validate_component_id(component_id: str) -> bool:
    """
    Проверяет, является ли component_id валидным
    
    Args:
        component_id: Идентификатор компонента
        
    Returns:
        bool: True если component_id валиден
    """
    valid_gemini_components = set(CONTENT_TYPE_TO_GEMINI_COMPONENT.values())
    valid_groq_components = set(CONTENT_TYPE_TO_GROQ_COMPONENT.values())
    
    return component_id in valid_gemini_components or component_id in valid_groq_components

def get_supported_content_types() -> Dict[str, list]:
    """
    Возвращает список поддерживаемых типов контента
    
    Returns:
        Dict: Словарь с поддерживаемыми типами
    """
    return {
        "enum_types": [str(ct) for ct in CONTENT_TYPE_TO_GEMINI_COMPONENT.keys()],
        "string_types": list(STRING_TO_GEMINI_COMPONENT.keys())
    }

# Экспортируем основные функции
__all__ = [
    'get_gemini_component_id',
    'get_groq_component_id', 
    'get_component_id_for_provider',
    'is_groq_component',
    'get_provider_from_component_id',
    'get_base_component_name',
    'validate_component_id',
    'get_all_component_mappings',
    'get_supported_content_types'
]
