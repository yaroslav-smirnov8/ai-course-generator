"""
Адаптер для добавления метаданных о восстановлении JSON в ответы API.

Этот модуль добавляет метаданные о процессе восстановления данных из ответов API языковых моделей
в структуру ответа API для фронтенда. Это позволяет фронтенду отображать информацию о том,
насколько успешно были восстановлены данные и какие поля могут отсутствовать.
"""
import logging
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union

T = TypeVar('T')

logger = logging.getLogger(__name__)

class APIResponse(Generic[T]):
    """
    Обертка для ответа API с добавлением метаданных о восстановлении JSON.
    
    Attributes:
        data: Данные ответа API
        metadata: Метаданные о восстановлении JSON
    """
    
    def __init__(
        self, 
        data: T, 
        recovery_status: str = 'none',
        recovered_fields: Optional[List[str]] = None,
        missing_fields: Optional[List[str]] = None,
        messages: Optional[List[str]] = None,
        recovery_time: Optional[float] = None
    ):
        self.data = data
        self.metadata = {
            'recovery_status': recovery_status,
            'recovered_fields': recovered_fields or [],
            'missing_fields': missing_fields or [],
            'messages': messages or [],
        }
        
        if recovery_time is not None:
            self.metadata['recovery_time'] = recovery_time
            
    def dict(self) -> Dict[str, Any]:
        """
        Преобразует объект в словарь для сериализации JSON.
        
        Returns:
            Dict[str, Any]: Словарь с данными и метаданными
        """
        return {
            'data': self.data,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_course_data(cls, course_data: Dict[str, Any], debug_info: Optional[Dict[str, Any]] = None) -> 'APIResponse':
        """
        Создает объект APIResponse из данных курса с анализом полноты данных.
        
        Args:
            course_data: Данные курса
            debug_info: Отладочная информация из обработчика JSON
            
        Returns:
            APIResponse: Объект ответа API с метаданными
        """
        if debug_info is None:
            debug_info = {}
        
        # Определяем статус восстановления по наличию обязательных полей
        required_fields = ['name', 'description', 'lessons']
        missing = [field for field in required_fields if field not in course_data]
        
        # Проверяем уроки на полноту данных
        lesson_missing_fields = []
        if 'lessons' in course_data and course_data['lessons']:
            for lesson in course_data['lessons']:
                lesson_required = ['title', 'objectives']
                lesson_missing = [field for field in lesson_required if field not in lesson]
                if lesson_missing:
                    lesson_title = lesson.get('title', 'Неизвестный урок')
                    lesson_missing_fields.extend([f"{lesson_title}: {field}" for field in lesson_missing])
        
        # Добавляем отсутствующие поля уроков в общий список
        missing.extend(lesson_missing_fields)
        
        # Определяем статус восстановления
        recovery_status = 'success'
        if missing:
            recovery_status = 'partial' if 'name' in course_data and 'lessons' in course_data else 'failure'
        
        # Извлекаем сообщения из debug_info
        messages = []
        if 'warnings' in debug_info:
            messages.extend(debug_info['warnings'])
        if 'errors' in debug_info:
            messages.extend(debug_info['errors'])
        
        # Получаем восстановленные поля
        recovered_fields = debug_info.get('recovered_fields', [])
        
        # Время восстановления
        recovery_time = debug_info.get('execution_time')
        
        return cls(
            data=course_data,
            recovery_status=recovery_status,
            recovered_fields=recovered_fields,
            missing_fields=missing,
            messages=messages,
            recovery_time=recovery_time
        )


def enrich_json_extractor_output(data: Dict[str, Any], extraction_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Обогащает вывод улучшенного обработчика JSON метаданными о восстановлении.
    
    Args:
        data: Данные, полученные от обработчика JSON
        extraction_info: Информация о процессе извлечения данных
        
    Returns:
        Dict[str, Any]: Обогащенные данные с метаданными
    """
    if extraction_info is None:
        extraction_info = {}
    
    # Создаем APIResponse
    response = APIResponse.from_course_data(data, extraction_info)
    
    # Возвращаем словарь для сериализации
    return response.dict()


def validate_course_structure(course: Dict[str, Any]) -> Dict[str, Any]:
    """
    Проверяет структуру курса на полноту данных.
    
    Args:
        course: Данные курса
        
    Returns:
        Dict[str, Any]: Результаты валидации
    """
    result = {
        "isValid": True,
        "missingFields": [],
        "lessonValidation": {
            "validLessons": 0,
            "invalidLessons": 0,
            "missingFields": {}
        },
        "score": 100  # По умолчанию ставим 100%
    }
    
    # Проверяем обязательные поля курса
    required_course_fields = ["name", "description", "lessons"]
    missing_course_fields = [field for field in required_course_fields if field not in course]
    
    if missing_course_fields:
        result["isValid"] = False
        result["missingFields"] = missing_course_fields
        result["score"] -= len(missing_course_fields) * 20  # Снижаем оценку на 20% за каждое отсутствующее поле курса
    
    # Проверяем каждый урок
    if "lessons" in course and isinstance(course["lessons"], list):
        for i, lesson in enumerate(course["lessons"]):
            # Проверяем обязательные поля урока
            required_lesson_fields = ["title", "objectives"]
            missing_lesson_fields = [field for field in required_lesson_fields if field not in lesson]
            
            if missing_lesson_fields:
                result["lessonValidation"]["invalidLessons"] += 1
                result["lessonValidation"]["missingFields"][i] = missing_lesson_fields
                result["score"] -= len(missing_lesson_fields) * 5  # Снижаем оценку на 5% за каждое отсутствующее поле урока
            else:
                result["lessonValidation"]["validLessons"] += 1
                
            # Проверяем содержимое полей
            if "objectives" in lesson and not lesson["objectives"]:
                if i not in result["lessonValidation"]["missingFields"]:
                    result["lessonValidation"]["missingFields"][i] = []
                result["lessonValidation"]["missingFields"][i].append("objectives (empty)")
                result["score"] -= 2  # Снижаем оценку на 2% за пустое поле
    
    # Ограничиваем оценку снизу до 0%
    result["score"] = max(0, result["score"])
    
    return result 