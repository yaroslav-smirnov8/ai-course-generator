# app/services/generator/__init__.py
from .manager import CourseManager
from typing import Dict, Any

# Common constants
DEFAULT_RETENTION_DAYS = 7
MAX_COURSE_SIZE = 50
MIN_LESSON_DURATION = 30
MAX_LESSON_DURATION = 180

# Common utilities
def format_duration(minutes: int) -> str:
    """Форматирует длительность из минут в читаемый формат"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}ч {mins}мин" if mins > 0 else f"{hours}ч"
    return f"{mins}мин"

def validate_course_structure(course_data: Dict[str, Any]) -> bool:
    """Проверяет корректность структуры курса"""
    if not course_data.get('lessons'):
        return False
    if len(course_data['lessons']) > MAX_COURSE_SIZE:
        return False
    for lesson in course_data['lessons']:
        duration = lesson.get('duration', 0)
        if not MIN_LESSON_DURATION <= duration <= MAX_LESSON_DURATION:
            return False
    return True

__all__ = [
    'CourseManager',
    'DEFAULT_RETENTION_DAYS',
    'MAX_COURSE_SIZE',
    'MIN_LESSON_DURATION',
    'MAX_LESSON_DURATION',
    'format_duration',
    'validate_course_structure'
]