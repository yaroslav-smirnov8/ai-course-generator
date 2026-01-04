"""
Адаптер для обработки и улучшения данных курса.
Незаметно восстанавливает данные и возвращает чистую структуру курса без метаданных.
"""

import logging
from typing import Dict, Any, Optional
import time

from app.services.content.enhanced_json_extractor import extract_course_with_metadata

logger = logging.getLogger(__name__)


class CourseAdapter:
    """
    Класс для обработки данных курса.
    Восстанавливает данные при необходимости, но скрывает этот процесс от пользователя.
    """
    
    @staticmethod
    def process_course_content(raw_content: str, debug: bool = False) -> Dict[str, Any]:
        """
        Обрабатывает сырой контент и возвращает готовую структуру курса.
        
        Args:
            raw_content: Сырой контент, полученный от API языковой модели
            debug: Включить режим отладки (только для логирования)
            
        Returns:
            Dict[str, Any]: Готовая структура курса
        """
        start_time = time.time()
        
        # Извлекаем данные курса с использованием улучшенного обработчика JSON
        # (Метаданные сохраняем только для логирования)
        course_data, extraction_info = extract_course_with_metadata(raw_content, debug=debug)
        
        # Логируем информацию о процессе восстановления (только для отладки)
        if debug:
            execution_time = time.time() - start_time
            logger.info(f"Обработка курса заняла {execution_time:.2f} секунд")
            logger.info(f"Используемые методы восстановления: {extraction_info.get('recovery_methods_used', [])}")
            
            if extraction_info.get('recovered_fields'):
                logger.info(f"Восстановленные поля: {extraction_info.get('recovered_fields', [])}")
            
            if extraction_info.get('warnings'):
                logger.warning(f"Предупреждения при обработке: {extraction_info.get('warnings', [])}")
                
            if extraction_info.get('errors'):
                logger.error(f"Ошибки при обработке: {extraction_info.get('errors', [])}")
        
        # Проверяем корректность структуры курса и исправляем при необходимости
        course_data = CourseAdapter._ensure_complete_course(course_data)
        
        # Возвращаем только данные курса без метаданных
        return course_data
    
    @staticmethod
    def _ensure_complete_course(course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверяет полноту данных курса и при необходимости добавляет недостающие поля.
        
        Args:
            course_data: Данные курса
            
        Returns:
            Dict[str, Any]: Полная структура курса
        """
        # Проверяем, что курс имеет название
        if "name" not in course_data or not course_data["name"]:
            course_data["name"] = "Сгенерированный курс"
            logger.info("Добавлено отсутствующее название курса")
        
        # Проверяем, что курс имеет описание
        if "description" not in course_data or not course_data["description"]:
            course_data["description"] = "Автоматически сгенерированный курс"
            logger.info("Добавлено отсутствующее описание курса")
        
        # Проверяем, что курс имеет уроки
        if "lessons" not in course_data or not isinstance(course_data["lessons"], list):
            course_data["lessons"] = []
            logger.warning("В курсе отсутствуют уроки, создан пустой список уроков")
        
        # Проверяем каждый урок
        for i, lesson in enumerate(course_data.get("lessons", [])):
            if not isinstance(lesson, dict):
                # Если урок не является словарем, создаем пустой словарь
                course_data["lessons"][i] = {"title": f"Урок {i+1}"}
                continue
                
            # Проверяем, что урок имеет название
            if "title" not in lesson or not lesson["title"]:
                lesson["title"] = f"Урок {i+1}"
                logger.info(f"Добавлено отсутствующее название урока {i+1}")
            
            # Проверяем, что урок имеет цели
            if "objectives" not in lesson or not lesson["objectives"]:
                lesson["objectives"] = ["Изучение основных концепций"]
                logger.info(f"Добавлены отсутствующие цели для урока {i+1}")
            
            # Проверяем, что урок имеет словарь
            if "vocabulary" not in lesson:
                lesson["vocabulary"] = []
                
            # Проверяем, что урок имеет грамматику
            if "grammar" not in lesson:
                lesson["grammar"] = []
        
        return course_data


def process_course_content(raw_content: str, debug: bool = False) -> Dict[str, Any]:
    """
    Удобная функция для обработки сырых данных API и получения готовой структуры курса.
    
    Args:
        raw_content: Сырой контент, полученный от API языковой модели
        debug: Включить режим отладки (только для логирования)
        
    Returns:
        Dict[str, Any]: Готовая структура курса
    """
    return CourseAdapter.process_course_content(raw_content, debug=debug) 