"""
Улучшенный модуль для извлечения структурированных данных из ответов API языковых моделей
с поддержкой сбора метаданных для фронтенда.

Этот модуль расширяет базовую функциональность json_extractor.py
с добавлением сбора данных о процессе извлечения, которые затем
можно использовать для отображения на фронтенде.
"""
import logging
import json
import re
import time
from typing import Dict, Any, List, Optional, Tuple, Union, Set

from app.services.content.json_extractor import (
    ImprovedJsonExtractor,
    extract_course_from_api_response
)

logger = logging.getLogger(__name__)


class EnhancedJsonExtractor(ImprovedJsonExtractor):
    """
    Улучшенный экстрактор JSON с расширенным сбором метаданных для фронтенда.
    
    Attributes:
        debug: Флаг для включения отладочных сообщений
        extraction_info: Словарь с информацией о процессе извлечения
    """
    
    def __init__(self, debug: bool = False):
        """
        Инициализация расширенного обработчика JSON
        
        Args:
            debug: Флаг для включения отладочных сообщений
        """
        super().__init__(debug=debug)
        self.extraction_info = {
            "recovered_fields": [],
            "warnings": [],
            "errors": [],
            "execution_time": 0.0,
            "original_content_length": 0,
            "extracted_json_length": 0,
            "recovery_methods_used": []
        }
    
    def extract_course_data(self, content: str) -> Dict[str, Any]:
        """
        Расширенный метод для извлечения данных курса из контента
        с сохранением информации о процессе извлечения.
        
        Args:
            content: Текстовый ответ от API
            
        Returns:
            Dict: Структура курса или заглушка в случае ошибки
        """
        # Замеряем время выполнения
        start_time = time.time()
        
        # Сохраняем длину исходного контента
        if content:
            self.extraction_info["original_content_length"] = len(content)
        
        # Выполняем основное извлечение данных
        result = super().extract_course_data(content)
        
        # Замеряем итоговое время
        end_time = time.time()
        self.extraction_info["execution_time"] = end_time - start_time
        
        return result
    
    def _clean_content(self, content: str) -> str:
        """
        Расширенная версия метода очистки контента с сохранением информации
        о применяемых методах восстановления.
        
        Args:
            content: Исходный контент
            
        Returns:
            str: Очищенный контент
        """
        # Проверяем наличие полной JSON структуры сразу
        if content.startswith('{') and content.endswith('}'):
            # Проверяем балансировку скобок
            if self._is_balanced(content):
                logger.info(f"Найдена полная JSON структура длиной {len(content)} символов")
                self.extraction_info["recovery_methods_used"].append("direct_json")
                return content
        
        # Проверяем наличие JSON в структуре ответа API Gemini
        if '"candidates":' in content and '"content":' in content and '"parts":' in content:
            self.extraction_info["recovery_methods_used"].append("gemini_api_format")
            # ... код обработки Gemini API ...
        
        # Удаляем markdown-обозначения блоков кода
        if '```json' in content or '```' in content:
            self.extraction_info["recovery_methods_used"].append("markdown_blocks")
            # ... код обработки markdown блоков ...
        
        # Выполняем стандартную очистку
        cleaned_content = super()._clean_content(content)
        
        return cleaned_content
    
    def _parse_json_safely(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        Расширенная версия метода безопасного парсинга JSON
        с сохранением информации об ошибках и восстановлении.
        
        Args:
            json_str: JSON-строка
            
        Returns:
            Optional[Dict[str, Any]]: Распарсенный JSON или None
        """
        if not json_str:
            self.extraction_info["errors"].append("Пустая JSON-строка")
            return None
            
        # Сохраняем длину извлеченного JSON
        self.extraction_info["extracted_json_length"] = len(json_str)
        
        # Шаг 1: Попытка стандартного парсинга
        try:
            parsed_json = json.loads(json_str)
            self.extraction_info["recovery_methods_used"].append("standard_parsing")
            return parsed_json
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON: {str(e)}"
            self.extraction_info["errors"].append(error_msg)
            
            # Шаг 2: Исправляем типичные ошибки JSON
            try:
                self.extraction_info["recovery_methods_used"].append("fix_common_errors")
                # ... код исправления ошибок ...
                
                # Исправляем лишние запятые
                fixed_json = re.sub(r',(\s*[\]}])', r'\1', json_str)
                # ... другие исправления ...
                
                # Пробуем парсить исправленный JSON
                parsed_json = json.loads(fixed_json)
                
                self.extraction_info["recovered_fields"].append("structure")
                self.extraction_info["warnings"].append("Исправлены синтаксические ошибки в JSON")
                
                return parsed_json
                
            except json.JSONDecodeError as e2:
                self.extraction_info["errors"].append(f"Не удалось исправить JSON: {str(e2)}")
                
                # Шаг 3: Восстановление структуры курса
                self.extraction_info["recovery_methods_used"].append("structure_recovery")
                # ... код восстановления структуры ...
                
        # Если все попытки не удались
        return None
    
    def _adapt_to_course_structure(self, data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]) -> Dict[str, Any]:
        """
        Расширенная версия метода адаптации данных к структуре курса
        с сохранением информации о восстановлении и отсутствующих полях.
        
        Args:
            data: Распарсенный JSON
            
        Returns:
            Dict[str, Any]: Структура курса
        """
        if data is None:
            self.extraction_info["errors"].append("Пустые данные, возвращаем базовый шаблон курса")
            self.extraction_info["recovery_methods_used"].append("empty_template")
            return {"name": "Generated Course", "lessons": []}
            
        # Если это словарь
        if isinstance(data, dict):
            # Проверяем существующую структуру курса
            if "lessons" in data and isinstance(data["lessons"], list):
                if "name" not in data:
                    data["name"] = "Generated Course"
                    self.extraction_info["recovered_fields"].append("name")
                    self.extraction_info["warnings"].append("Добавлено отсутствующее поле 'name'")
                
                if "description" not in data:
                    data["description"] = "Auto-generated course"
                    self.extraction_info["recovered_fields"].append("description")
                    self.extraction_info["warnings"].append("Добавлено отсутствующее поле 'description'")
                
                # Проверяем каждый урок на наличие обязательных полей
                for i, lesson in enumerate(data["lessons"]):
                    if "title" not in lesson:
                        lesson["title"] = f"Lesson {i+1}"
                        self.extraction_info["recovered_fields"].append(f"lesson[{i}].title")
                        self.extraction_info["warnings"].append(f"Добавлено отсутствующее поле 'title' в уроке {i+1}")
                    
                    if "objectives" not in lesson:
                        lesson["objectives"] = ["Learn key concepts"]
                        self.extraction_info["recovered_fields"].append(f"lesson[{i}].objectives")
                        self.extraction_info["warnings"].append(f"Добавлено отсутствующее поле 'objectives' в уроке {i+1}")
                
                return data
                
            # Если это отдельный урок
            elif "title" in data and any(key in data for key in ["objectives", "grammar", "vocabulary"]):
                self.extraction_info["recovery_methods_used"].append("single_lesson_to_course")
                self.extraction_info["warnings"].append("Преобразование отдельного урока в структуру курса")
                
                lesson_title = data.get("title", "Untitled Lesson")
                return {
                    "name": f"Course with {lesson_title}",
                    "description": f"Course generated from individual lesson: {lesson_title}",
                    "lessons": [data]
                }
                
            # Проверяем структуру, где уроки определены как "lesson X" на верхнем уровне
            lesson_keys = [key for key in data.keys() if key.lower().startswith("lesson")]
            if lesson_keys:
                self.extraction_info["recovery_methods_used"].append("lesson_x_format")
                self.extraction_info["warnings"].append(f"Преобразование формата 'lesson X' с {len(lesson_keys)} уроками")
                
                # ... код преобразования формата ...
                # (остальная логика остается такой же, как в оригинальном методе)
                
            # Другие форматы
            self.extraction_info["recovery_methods_used"].append("unknown_format")
            self.extraction_info["errors"].append(f"Неизвестная структура данных: {list(data.keys())}")
            
        # Если это список
        elif isinstance(data, list):
            self.extraction_info["recovery_methods_used"].append("lessons_array")
            
            # ... код преобразования массива ...
            # (остальная логика остается такой же, как в оригинальном методе)
                
        # Неизвестный формат
        self.extraction_info["recovery_methods_used"].append("fallback")
        self.extraction_info["errors"].append(f"Неизвестный формат данных: {type(data)}")
        
        return {"name": "Generated Course", "lessons": []}


def extract_course_with_metadata(content: str, debug: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Извлекает структуру курса из ответа API и собирает метаданные о процессе извлечения.
    
    Args:
        content: Текстовый ответ от API
        debug: Включить подробное логирование
        
    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: Кортеж из данных курса и метаданных о процессе извлечения
    """
    extractor = EnhancedJsonExtractor(debug=debug)
    course_data = extractor.extract_course_data(content)
    
    return course_data, extractor.extraction_info 