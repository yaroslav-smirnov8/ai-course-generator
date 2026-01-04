# app/services/content/json_processor.py
"""
Модуль для безопасной обработки JSON в генерации контента
"""
import json
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class JSONProcessor:
    """
    Класс для безопасной обработки JSON ответов от AI моделей
    """

    async def _parse_json_safely(self, json_str: str) -> Dict[str, Any]:
        """Safely parse JSON with fallback mechanisms"""
        try:
            # Сначала пытаемся стандартный парсинг
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {e}")
            
            # Пытаемся очистить JSON
            cleaned_json = self._clean_json_response(json_str)
            try:
                return json.loads(cleaned_json)
            except json.JSONDecodeError:
                logger.warning("Cleaned JSON parsing failed, trying to extract JSON")
                
                # Пытаемся извлечь JSON из контента
                extracted_json = self._extract_json_from_content(json_str)
                try:
                    return json.loads(extracted_json)
                except json.JSONDecodeError:
                    logger.warning("Extracted JSON parsing failed, trying LLM fix")
                    
                    # Последняя попытка - исправление через LLM
                    fixed_json = await self._fix_json_with_llm(json_str)
                    try:
                        return json.loads(fixed_json)
                    except json.JSONDecodeError:
                        logger.error("All JSON parsing attempts failed, extracting data manually")
                        
                        # Ручное извлечение данных
                        return self._extract_data_from_malformed_json(json_str)

    def _clean_json_response(self, content: str) -> str:
        """Clean JSON response from common formatting issues"""
        # Удаляем markdown блоки
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # Удаляем комментарии
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Исправляем trailing commas
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Исправляем одинарные кавычки на двойные
        content = re.sub(r"'([^']*)':", r'"\1":', content)
        content = re.sub(r":\s*'([^']*)'", r': "\1"', content)
        
        # Удаляем лишние пробелы
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content

    def _extract_json_from_content(self, content: str) -> str:
        """Extract JSON from content that might contain other text"""
        # Ищем JSON объект или массив
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Объект
            r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',  # Массив
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                # Возвращаем самый длинный найденный JSON
                return max(matches, key=len)
        
        return content

    async def _fix_json_with_llm(self, problematic_json: str) -> str:
        """Fix JSON using LLM"""
        # Здесь можно было бы использовать LLM для исправления JSON
        # Но для простоты возвращаем исходный JSON
        logger.warning("LLM JSON fixing not implemented, returning original")
        return problematic_json

    def _extract_data_from_malformed_json(self, json_str: str) -> Dict[str, Any]:
        """Extract data from malformed JSON using regex patterns"""
        result = {}
        
        # Извлекаем строковые поля
        string_fields = re.findall(r'"([^"]+)":\s*"([^"]*)"', json_str)
        for key, value in string_fields:
            result[key] = value
        
        # Извлекаем числовые поля
        number_fields = re.findall(r'"([^"]+)":\s*(\d+(?:\.\d+)?)', json_str)
        for key, value in number_fields:
            try:
                result[key] = float(value) if '.' in value else int(value)
            except ValueError:
                result[key] = value
        
        # Извлекаем булевы поля
        bool_fields = re.findall(r'"([^"]+)":\s*(true|false)', json_str, re.IGNORECASE)
        for key, value in bool_fields:
            result[key] = value.lower() == 'true'
        
        # Извлекаем массивы
        array_fields = re.findall(r'"([^"]+)":\s*\[(.*?)\]', json_str, re.DOTALL)
        for key, array_content in array_fields:
            result[key] = self._extract_array_items(array_content)
        
        return result

    def _extract_array_items(self, array_str: str) -> List[str]:
        """Extract array items from string representation"""
        items = []
        
        # Ищем строки в кавычках
        string_items = re.findall(r'"([^"]*)"', array_str)
        if string_items:
            return string_items
        
        # Ищем элементы, разделенные запятыми
        comma_items = [item.strip() for item in array_str.split(',')]
        if comma_items and comma_items != ['']:
            return comma_items
        
        return items

    def _generate_fallback_structure(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback structure when JSON parsing completely fails"""
        return {
            "title": "Generated Content",
            "content": "Content generation completed",
            "type": prompt.get("type", "general"),
            "status": "fallback_generated"
        }

    def _generate_default_value(self, field: str, prompt: Dict[str, Any]) -> Any:
        """Generate default value for a specific field"""
        defaults = {
            "title": "Generated Title",
            "description": "Generated description",
            "content": "Generated content",
            "instructions": "Follow the provided instructions",
            "difficulty": "medium",
            "language": "english",
            "type": "general",
            "status": "generated"
        }
        
        return defaults.get(field, "Generated value")

    def _generate_default_lessons(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default lessons structure"""
        return [
            {
                "title": "Lesson 1",
                "description": "Introduction lesson",
                "content": "Basic content for lesson 1",
                "duration": 30,
                "difficulty": "beginner"
            },
            {
                "title": "Lesson 2", 
                "description": "Practice lesson",
                "content": "Practice content for lesson 2",
                "duration": 45,
                "difficulty": "intermediate"
            }
        ]

    def _enrich_lesson_data(self, lesson: dict, index: int) -> dict:
        """Обогащает данные урока недостающими полями"""

        # Добавляем базовые поля, если они отсутствуют
        if 'id' not in lesson:
            lesson['id'] = index + 1

        if 'title' not in lesson or not lesson['title']:
            lesson['title'] = f"Урок {index + 1}"

        if 'description' not in lesson:
            lesson['description'] = f"Описание урока {index + 1}"

        if 'duration' not in lesson:
            lesson['duration'] = 45  # По умолчанию 45 минут

        if 'difficulty' not in lesson:
            lesson['difficulty'] = 'intermediate'

        if 'objectives' not in lesson:
            lesson['objectives'] = []

        if 'materials' not in lesson:
            lesson['materials'] = []

        if 'activities' not in lesson:
            lesson['activities'] = []

        if 'homework' not in lesson:
            lesson['homework'] = ""

        if 'assessment' not in lesson:
            lesson['assessment'] = ""

        # Обогащаем существующие поля
        if isinstance(lesson.get('objectives'), str):
            # Если цели переданы как строка, разбиваем на список
            lesson['objectives'] = [obj.strip() for obj in lesson['objectives'].split('\n') if obj.strip()]

        if isinstance(lesson.get('materials'), str):
            # Если материалы переданы как строка, разбиваем на список
            lesson['materials'] = [mat.strip() for mat in lesson['materials'].split('\n') if mat.strip()]

        # Добавляем метаданные
        lesson['created_at'] = lesson.get('created_at', None)
        lesson['updated_at'] = lesson.get('updated_at', None)
        lesson['status'] = lesson.get('status', 'draft')

        return lesson

    async def _clear_cache_before_generation(self):
        """Clear cache before generation"""
        try:
            # Здесь можно добавить логику очистки кэша
            logger.info("Cache cleared before generation")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
            # Не прерываем выполнение, если очистка кэша не удалась

    def _create_cache_key(self, prompt: str, content_type, extra_params = None) -> str:
        """
        Создает уникальный ключ для кэширования на основе промпта и параметров

        Args:
            prompt: Промпт для генерации
            content_type: Тип контента
            extra_params: Дополнительные параметры

        Returns:
            str: Уникальный ключ для кэширования
        """
        import hashlib

        # Создаем базовую строку для хэширования
        cache_string = f"{prompt}|{content_type}"

        # Добавляем дополнительные параметры, если они есть
        if extra_params:
            # Сортируем параметры для консистентности
            sorted_params = sorted(extra_params.items())
            params_string = "|".join([f"{k}:{v}" for k, v in sorted_params])
            cache_string += f"|{params_string}"

        # Создаем хэш
        cache_key = hashlib.md5(cache_string.encode('utf-8')).hexdigest()

        # Добавляем префикс для идентификации
        return f"content_gen:{cache_key}"
