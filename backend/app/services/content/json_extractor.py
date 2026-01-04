"""
Улучшенный обработчик JSON-ответов от языковых моделей API.
Умеет распознавать различные форматы ответов, включая:
- Полные структуры курса
- Отдельные уроки без обертки курса
- Массивы уроков
"""
import json
import re
import logging
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger(__name__)

class ImprovedJsonExtractor:
    """
    Улучшенный обработчик JSON для извлечения структурированных данных
    из ответов языковых моделей, с фокусом на форматах курсов и уроков.
    """
    
    def __init__(self, debug: bool = False):
        """
        Инициализация обработчика
        
        Args:
            debug: Включить подробное логирование
        """
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        
    def extract_course_data(self, content: str) -> Dict[str, Any]:
        """
        Основной метод для извлечения данных курса из контента.
        
        Args:
            content: Текстовый ответ от API
            
        Returns:
            Dict: Структура курса или заглушка в случае ошибки
        """
        if not content or not isinstance(content, str):
            logger.warning("Пустой или некорректный ответ API")
            return {"name": "Generated Course", "lessons": []}
            
        # Логируем детали исходного контента
        logger.info(f"Исходный контент перед очисткой длиной {len(content)} символов")
        logger.info(f"ПЕРВЫЕ 100 СИМВОЛОВ ИСХОДНОГО КОНТЕНТА: {content[:100]}")
        logger.info(f"ПОСЛЕДНИЕ 100 СИМВОЛОВ ИСХОДНОГО КОНТЕНТА: {content[-100:]}")
        
        # Очищаем контент от markdown и других артефактов
        cleaned_content = self._clean_content(content)
        
        # Извлекаем JSON-строку из контента
        json_str = self._extract_json_string(cleaned_content)
        
        if not json_str:
            logger.warning("Не удалось извлечь JSON из контента")
            return {"name": "Generated Course", "lessons": []}
            
        # Парсим JSON с обработкой ошибок
        parsed_json = self._parse_json_safely(json_str)
        
        # Определяем тип данных и адаптируем к структуре курса
        return self._adapt_to_course_structure(parsed_json)
        
    def _clean_content(self, content: str) -> str:
        """
        Очищает контент от markdown-блоков и других артефактов
        
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
                return content
        
        # Проверяем наличие JSON в структуре ответа API Gemini (candidates/content/parts/text)
        gemini_pattern = r'"candidates":\s*\[\s*\{\s*"content":\s*\{\s*"parts":\s*\[\s*\{\s*"text":\s*"(.*?)"\s*\}'
        gemini_match = re.search(gemini_pattern, content, re.DOTALL)
        if gemini_match:
            extracted_text = gemini_match.group(1)
            # Убираем экранирование
            extracted_text = extracted_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            logger.info(f"Найден ответ API Gemini, извлечен текст длиной {len(extracted_text)}")
            
            # Логируем содержимое извлеченного текста для отладки
            if self.debug:
                start_preview = extracted_text[:100].replace('\n', '\\n') if len(extracted_text) > 100 else extracted_text.replace('\n', '\\n')
                end_preview = extracted_text[-100:].replace('\n', '\\n') if len(extracted_text) > 100 else extracted_text.replace('\n', '\\n')
                logger.info(f"Начало извлеченного текста из Gemini: {start_preview}")
                logger.info(f"Конец извлеченного текста из Gemini: {end_preview}")
            
            # Пробуем найти JSON-блок в извлеченном тексте
            if '```json' in extracted_text:
                json_blocks = re.findall(r'```json\s*([\s\S]*?)\s*```', extracted_text)
                if json_blocks:
                    # Берем самый длинный блок
                    longest_block = max(json_blocks, key=len)
                    # Проверяем, что это валидный JSON
                    if longest_block.strip().startswith('{') and longest_block.strip().endswith('}'):
                        logger.info(f"Извлечен JSON-блок из ответа Gemini, длина: {len(longest_block)}")
                        return longest_block.strip()
                    else:
                        logger.warning("Найденный JSON-блок не имеет правильной структуры")
            
            # Если не нашли блок с явной JSON-меткой, проверяем обычный блок кода
            if '```' in extracted_text:
                code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', extracted_text)
                if code_blocks:
                    # Фильтруем блоки, ищем те, которые начинаются с { и заканчиваются на }
                    json_like_blocks = [block.strip() for block in code_blocks 
                                      if block.strip().startswith('{') and block.strip().endswith('}')]
                    if json_like_blocks:
                        # Берем самый длинный блок
                        longest_block = max(json_like_blocks, key=len)
                        logger.info(f"Извлечен JSON-подобный блок из ответа Gemini, длина: {len(longest_block)}")
                        return longest_block
            
            # Если в извлеченном тексте есть JSON-структуры, извлекаем их
            if '{' in extracted_text and '}' in extracted_text:
                # Находим все фрагменты между { и }
                json_matches = re.findall(r'(\{[\s\S]*?\})', extracted_text)
                if json_matches:
                    # Фильтруем только сбалансированные фрагменты
                    balanced_jsons = [j for j in json_matches if self._is_balanced(j)]
                    if balanced_jsons:
                        # Берем самый длинный сбалансированный JSON
                        longest_json = max(balanced_jsons, key=len)
                        logger.info(f"Извлечен сбалансированный JSON из ответа Gemini, длина: {len(longest_json)}")
                        return longest_json
            
            # Продолжаем очистку извлеченного текста
            content = extracted_text
        
        # Удаляем markdown-обозначения блоков кода
        if '```json' in content or '```' in content:
            logger.info("Найдены markdown-блоки, пытаемся извлечь JSON")
            json_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_blocks:
                # Берем самый длинный блок, который похож на валидный JSON
                valid_blocks = []
                for block in json_blocks:
                    if block.strip().startswith('{') and block.strip().endswith('}'):
                        valid_blocks.append(block.strip())
                
                if valid_blocks:
                    content = max(valid_blocks, key=len)
                    logger.info(f"Извлечен JSON из markdown-блока, длина: {len(content)}")
                    return content
        
        # Если не удалось извлечь JSON из markdown-блоков, очищаем стандартным способом
        content = re.sub(r'```(?:json)?\s*([\s\S]*?)\s*```', r'\1', content)
        logger.info("Удалены markdown-обозначения блоков кода")
        
        # Удаляем однострочные комментарии
        content = re.sub(r'//.*?(?:\n|$)', '\n', content)
        content = re.sub(r'(?m)^\s*//.*$', '', content)
        
        # Удаляем многострочные комментарии
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        # Удаляем метакомментарии
        content = re.sub(r'(?m)^\s*(?://)?\s*\.\.\..*$', '', content)
        content = re.sub(r'(?m)^\s*(?://)?\s*\w+ так далее.*$', '', content)
        
        # Очищаем пробелы в начале и конце
        content = content.strip()
        
        # Проверяем наличие полной JSON структуры после очистки
        if content.startswith('{') and content.endswith('}'):
            if self._is_balanced(content):
                logger.info(f"Найдена полная JSON структура после очистки, длиной {len(content)} символов")
        
        return content
    
    def _is_balanced(self, s: str) -> bool:
        """
        Проверяет балансировку скобок в строке
        
        Args:
            s: Строка для проверки
            
        Returns:
            bool: True если скобки сбалансированы
        """
        stack = []
        brackets = {'(': ')', '[': ']', '{': '}'}
        for char in s:
            if char in brackets.keys():
                stack.append(char)
            elif char in brackets.values():
                if not stack:
                    return False
                last_open = stack.pop()
                if char != brackets[last_open]:
                    return False
        return len(stack) == 0
        
    def _extract_json_string(self, content: str) -> str:
        """
        Извлекает JSON-строку из очищенного контента
        
        Args:
            content: Очищенный контент
            
        Returns:
            str: Извлеченная JSON-строка или пустая строка
        """
        if not content or len(content) < 5:
            return ""
        
        # Проверяем наличие полного JSON объекта
        if content.startswith('{') and content.endswith('}') and self._is_balanced(content):
            # Уже полный сбалансированный JSON
            logger.info(f"Найден полный JSON объект длиной {len(content)}")
            
            # Проверяем, содержит ли он структуру курса
            if any(marker in content for marker in ['"lessons"', '"name"', '"description"']):
                # Это может быть структура курса, проверяем подробнее
                try:
                    json_obj = json.loads(content)
                    if isinstance(json_obj, dict):
                        # Проверка на полную структуру курса
                        if "lessons" in json_obj and isinstance(json_obj["lessons"], list):
                            logger.info("Полный JSON содержит структуру курса с уроками")
                            return content
                        # Проверка на структуру в формате "lesson X"
                        lesson_keys = [key for key in json_obj.keys() if key.lower().startswith("lesson")]
                        if lesson_keys:
                            logger.info(f"Полный JSON содержит уроки в формате 'lesson X'. Количество: {len(lesson_keys)}")
                            return content
                except json.JSONDecodeError:
                    # Если не удалось распарсить, продолжаем поиск
                    pass
                
                # Даже если не удалось подтвердить через парсинг, возвращаем полный JSON
                logger.info("Найден полный JSON, предположительно содержащий структуру курса")
                return content
                
        # Ищем структуру курса с массивом уроков (расширенный паттерн)
        course_patterns = [
            r'(\{\s*"name".*?"lessons"\s*:\s*\[[\s\S]*?\]\s*\})',  # Стандартный шаблон
            r'(\{\s*"name".*?"learning_outcomes".*?"lessons"\s*:\s*\[[\s\S]*?\]\s*\})',  # С learning_outcomes
            r'(\{\s*"name".*?"description".*?"lessons"\s*:\s*\[[\s\S]*?\]\s*\})'  # С description
        ]
        
        for pattern in course_patterns:
            course_match = re.search(pattern, content, re.DOTALL)
            if course_match:
                json_str = course_match.group(0)
                
                # Проверяем, что структура курса содержит массив уроков
                if '"lessons"' in json_str and '[' in json_str and ']' in json_str:
                    logger.info(f"Извлечена структура курса с массивом уроков, длина: {len(json_str)}")
                    # Проверяем балансировку скобок
                    if self._is_balanced(json_str):
                        return json_str
                    else:
                        logger.warning("Найденная структура курса имеет несбалансированные скобки")
                        break  # Переходим к следующему методу
        
        # Ищем структуру в формате "lesson X"
        lesson_x_pattern = r'(\{\s*"lesson\s*\d+".*?\}\s*\})'
        lesson_x_match = re.search(lesson_x_pattern, content, re.DOTALL)
        if lesson_x_match:
            json_str = lesson_x_match.group(0)
            if self._is_balanced(json_str):
                logger.info(f"Извлечена структура в формате 'lesson X', длина: {len(json_str)}")
                return json_str
        
        # Ищем корневой JSON объект
        try:
            # Находим первую открывающую и последнюю закрывающую скобку
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx + 1]
                # Проверяем, действительно ли это JSON объект
                try:
                    json.loads(json_str)
                    logger.info(f"Извлечен полный JSON, длина: {len(json_str)}")
                    return json_str
                except json.JSONDecodeError:
                    logger.info("Найденный полный текст между {} и } не является валидным JSON")
                    # Логируем начало и конец для отладки
                    logger.info(f"Начало JSON: {json_str[:50]}...")
                    logger.info(f"Конец JSON: ...{json_str[-50:]}")
                    
                    # Пробуем найти более узкую структуру курса
                    course_pattern = r'(\{\s*"name".*?"lessons"\s*:\s*\[\s*\{\s*"title"[\s\S]*?\]\s*\})'
                    course_match = re.search(course_pattern, content, re.DOTALL)
                    if course_match:
                        json_str = course_match.group(0)
                        logger.info(f"Извлечена структура курса через паттерн, длина: {len(json_str)}")
                        return json_str
        except Exception as e:
            logger.error(f"Ошибка при поиске JSON: {str(e)}")
        
        # Если всё вышеперечисленное не помогло, ищем любой JSON
        try:
            # Пробуем найти структуру урока
            lesson_pattern = r'(\{\s*"title".*?"objectives"[\s\S]*?\})'
            lesson_match = re.search(lesson_pattern, content, re.DOTALL)
            if lesson_match:
                json_str = lesson_match.group(0)
                # Если это похоже на отдельный урок, а не на весь курс, проверяем следующий подход
                if len(json_str) < len(content) / 2 and '"lessons"' not in json_str:
                    logger.warning("Получен JSON, но без поля 'lessons': " + str(json.loads(json_str).keys()))
                    logger.info("Извлечение JSON из контента длиной " + str(len(content)) + " символов")
                    logger.info("Первые 50 символов контента: " + content[:50])
                    logger.info("Последние 50 символов контента: " + content[-50:])
                    # Если найденный урок слишком мал по сравнению с полным контентом,
                    # то, вероятно, мы нашли только первый урок вместо всего курса
                    logger.warning("Не удалось найти структуру курса, но контент похож на JSON. Возвращаем исходный контент.")
                    logger.info("=== ПОЛНЫЙ ОТВЕТ API ДЛЯ ОТЛАДКИ ===")
                    logger.info("JSON полностью: " + json_str)
                    logger.info("=== КОНЕЦ ПОЛНОГО ОТВЕТА API ===")
                    
                    # Ищем в полном контенте, сначала проверяем, есть ли там массив lessons
                    if '"lessons"' in content and ']' in content:
                        # Пытаемся найти весь текст от начала до конца массива lessons
                        full_course_pattern = r'(\{\s*"name".*?"lessons"\s*:\s*\[[\s\S]*?\]\s*\})'
                        full_course_match = re.search(full_course_pattern, content, re.DOTALL)
                        if full_course_match:
                            full_json = full_course_match.group(0)
                            logger.info(f"Найдена полная структура курса, длина: {len(full_json)}")
                            return full_json
                
                # Если мы не нашли более полную структуру, вернем то, что уже нашли
                logger.info(f"Извлечена структура урока, длина: {len(json_str)}")
                return json_str
                
            # Ищем API ответы от Gemini, Claude и т.д.
            api_patterns = [
                r'(\{\s*"name".*?"lessons"\s*:\s*\[.*?\]\s*\})',
                r'(\{\s*"title".*?"activities"\s*:\s*\[.*?\]\s*\})'
            ]
            
            for pattern in api_patterns:
                api_match = re.search(pattern, content, re.DOTALL)
                if api_match:
                    json_str = api_match.group(0)
                    logger.info(f"Извлечена структура через API паттерн, длина: {len(json_str)}")
                    return json_str
        except Exception as e:
            logger.error(f"Ошибка при поиске специфических JSON структур: {str(e)}")
        
        # Ищем JSON-блоки в markdown, если они остались
        if "```json" in content or "```" in content:
            json_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if json_blocks:
                # Выбираем самый длинный блок
                longest_block = max(json_blocks, key=len)
                logger.info(f"Извлечен JSON из markdown блока, длина: {len(longest_block)}")
                return longest_block

        # Последняя попытка - ищем всё между первыми фигурными скобками
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx >= 0 and end_idx > start_idx:
            logger.warning("Последняя попытка: извлекаем весь контент между {} и }")
            return content[start_idx:end_idx + 1]
                
        logger.error("Не удалось найти JSON структуру в контенте")
        return ""
        
    def _parse_json_safely(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        Безопасный парсинг JSON с обработкой ошибок
        
        Args:
            json_str: JSON-строка
            
        Returns:
            Optional[Dict[str, Any]]: Распарсенный JSON или None
        """
        if not json_str:
            return None
            
        # Логируем для отладки начало и конец JSON
        logger.info("=== НАЧАЛО И КОНЕЦ JSON ДЛЯ ОТЛАДКИ ===")
        start_preview = json_str[:50].replace('\n', '\\n')
        end_preview = json_str[-50:].replace('\n', '\\n')
        logger.info(f"Начало JSON: '{start_preview}...'")
        logger.info(f"Конец JSON: '...{end_preview}'")
        logger.info(f"Длина JSON: {len(json_str)} символов")
        logger.info("=== КОНЕЦ ПРЕДПРОСМОТРА JSON ===")
        
        # Шаг 1: Попытка стандартного парсинга
        try:
            logger.info("Попытка стандартного парсинга JSON")
            parsed_json = json.loads(json_str)
            logger.info("Стандартный парсинг JSON успешен")
            
            # Логируем структуру
            if isinstance(parsed_json, dict):
                logger.info(f"Структура JSON: объект с ключами {list(parsed_json.keys())}")
                # Проверяем наличие поля lessons
                if "lessons" in parsed_json and isinstance(parsed_json["lessons"], list):
                    logger.info(f"JSON содержит {len(parsed_json['lessons'])} уроков")
            elif isinstance(parsed_json, list):
                logger.info(f"Структура JSON: массив длиной {len(parsed_json)}")
                
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
            # Запоминаем позицию ошибки
            error_pos = e.pos
            error_msg = str(e)
            logger.info(f"Ошибка декодирования JSON на позиции {error_pos}: {error_msg}")
            
            # Шаг 2: Исправляем типичные ошибки JSON
            try:
                logger.info("Попытка исправить типичные ошибки в JSON")
                
                # Исправляем лишние запятые
                fixed_json = re.sub(r',(\s*[\]}])', r'\1', json_str)
                # Добавляем запятые между объектами
                fixed_json = re.sub(r'([}\]])(\s*){', r'\1,\2{', fixed_json)
                # Исправляем ключи без кавычек (например, {key: "value"})
                fixed_json = re.sub(r'(?<!["\\])(\b[a-zA-Z_][a-zA-Z0-9_]*\b)(?=\s*:)', r'"\1"', fixed_json)
                # Исправляем одинарные кавычки на двойные
                fixed_json = re.sub(r"(?<!\\)'([^']*?)(?<!\\)'", r'"\1"', fixed_json)
                # Исправляем экранированные двойные кавычки внутри значений
                fixed_json = re.sub(r'\\"', '"', fixed_json)
                
                # Пробуем парсить исправленный JSON
                logger.info("Попытка парсинга исправленного JSON")
                parsed_json = json.loads(fixed_json)
                logger.info("JSON успешно исправлен и распарсен")
                
                # Проверяем структуру исправленного JSON
                if isinstance(parsed_json, dict):
                    if "lessons" in parsed_json and isinstance(parsed_json["lessons"], list):
                        logger.info(f"Исправленный JSON содержит {len(parsed_json['lessons'])} уроков")
                        
                return parsed_json
                
            except json.JSONDecodeError as e2:
                logger.error(f"Не удалось исправить JSON: {str(e2)}")
                
                # Шаг 3: Попытаемся восстановить структуру курса
                try:
                    logger.info("Попытка восстановить структуру курса из JSON")
                    
                    # Ищем паттерн структуры курса
                    course_pattern = r'{\s*"name"\s*:\s*"[^"]+"\s*,\s*(?:"description"\s*:\s*"[^"]*"\s*,\s*)??"lessons"\s*:\s*\['
                    course_match = re.search(course_pattern, json_str)
                    
                    if course_match:
                        # Пытаемся найти и извлечь массив уроков
                        lessons_pattern = r'"lessons"\s*:\s*(\[[\s\S]*?\])'
                        lessons_match = re.search(lessons_pattern, json_str)
                        
                        if lessons_match:
                            lessons_str = lessons_match.group(1)
                            try:
                                # Извлекаем имя курса
                                name_match = re.search(r'"name"\s*:\s*"([^"]+)"', json_str)
                                course_name = name_match.group(1) if name_match else "Recovered Course"
                                
                                # Извлекаем описание курса
                                desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', json_str)
                                course_desc = desc_match.group(1) if desc_match else "Recovered course description"
                                
                                # Пробуем исправить массив уроков
                                fixed_lessons = re.sub(r',(\s*[\]}])', r'\1', lessons_str)
                                lessons_data = json.loads(fixed_lessons)
                                
                                # Создаем восстановленную структуру курса
                                recovered_course = {
                                    "name": course_name,
                                    "description": course_desc,
                                    "lessons": lessons_data
                                }
                                
                                logger.info(f"Восстановлена структура курса с {len(lessons_data)} уроками")
                                return recovered_course
                            except Exception as e3:
                                logger.error(f"Не удалось восстановить массив уроков: {str(e3)}")
                
                except Exception as e4:
                    logger.error(f"Ошибка при восстановлении структуры курса: {str(e4)}")
            
            # Шаг 4: Последняя попытка - разбор по частям
            try:
                logger.info("Попытка найти и извлечь отдельные уроки из JSON")
                
                # Ищем все структуры, похожие на уроки
                lessons = []
                lesson_patterns = [
                    r'{\s*"title"\s*:\s*"([^"]*)"\s*,[\s\S]*?(?:"objectives"|"grammar"|"vocabulary"|"activities")[\s\S]*?}'
                ]
                
                for pattern in lesson_patterns:
                    lesson_matches = re.finditer(pattern, json_str)
                    for match in lesson_matches:
                        try:
                            lesson_json = match.group(0)
                            # Исправляем ошибки
                            lesson_json = re.sub(r',(\s*[\]}])', r'\1', lesson_json)
                            lesson_data = json.loads(lesson_json)
                            lessons.append(lesson_data)
                            logger.info(f"Извлечен урок: {lesson_data.get('title', 'Untitled')}")
                        except Exception as e5:
                            logger.error(f"Не удалось распарсить урок: {str(e5)}")
                
                if lessons:
                    logger.info(f"Извлечено {len(lessons)} уроков из JSON")
                    return {
                        "name": "Recovered Course",
                        "description": "Course recovered from extracted lessons",
                        "lessons": lessons
                    }
            
            except Exception as e6:
                logger.error(f"Ошибка при извлечении отдельных уроков: {str(e6)}")
        
        # Если все попытки не удались
        logger.error("Все попытки обработки JSON не удались")
        return None
        
    def _adapt_to_course_structure(self, data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]) -> Dict[str, Any]:
        """
        Адаптирует распарсенный JSON к структуре курса
        
        Args:
            data: Распарсенный JSON
            
        Returns:
            Dict[str, Any]: Структура курса
        """
        if data is None:
            logger.warning("Пустые данные, возвращаем базовый шаблон курса")
            return {"name": "Generated Course", "lessons": []}
            
        # Если это словарь
        if isinstance(data, dict):
            # Проверяем существующую структуру курса
            if "lessons" in data and isinstance(data["lessons"], list):
                logger.info(f"Найдена структура курса с {len(data['lessons'])} уроками")
                # Проверка на обязательное поле name
                if "name" not in data:
                    logger.warning("В структуре курса отсутствует обязательное поле: name")
                    data["name"] = "Generated Course"
                return data
                
            # Проверяем, не является ли это отдельным уроком
            if "title" in data and any(key in data for key in ["objectives", "grammar", "vocabulary"]):
                logger.info(f"Найден отдельный урок: {data.get('title')}, преобразуем в структуру курса")
                return {
                    "name": f"Course with {data.get('title', 'Untitled Lesson')}",
                    "description": f"Course generated from individual lesson: {data.get('title', 'Untitled')}",
                    "lessons": [data]
                }
                
            # Проверяем структуру, где уроки определены как "lesson X" на верхнем уровне
            lesson_keys = [key for key in data.keys() if key.lower().startswith("lesson")]
            if lesson_keys:
                logger.info(f"Найдена структура с уроками в формате 'lesson X'. Количество уроков: {len(lesson_keys)}")
                lessons = []
                
                for key in lesson_keys:
                    lesson_data = data[key]
                    if isinstance(lesson_data, dict):
                        # Добавляем номер урока в данные урока, если он еще не имеет поля "number"
                        if "number" not in lesson_data:
                            # Пытаемся извлечь номер из ключа (например, "lesson 1" -> 1)
                            try:
                                lesson_number = int(re.search(r'\d+', key).group(0))
                                lesson_data["number"] = lesson_number
                            except (AttributeError, ValueError):
                                # Если не удалось извлечь номер, используем порядковый номер
                                lesson_data["number"] = lesson_keys.index(key) + 1
                        
                        lessons.append(lesson_data)
                    else:
                        logger.warning(f"Урок {key} не является словарем, пропускаем")
                
                return {
                    "name": "Generated Language Course",
                    "description": f"Auto-generated course with {len(lessons)} lessons",
                    "lessons": lessons
                }
                
            # Другой формат - берем то, что можем
            logger.warning(f"Неизвестная структура данных с ключами: {list(data.keys())}")
            return {
                "name": data.get("name", "Generated Course"),
                "description": data.get("description", "Auto-generated course"),
                "lessons": data.get("lessons", [])
            }
            
        # Если это список
        elif isinstance(data, list):
            # Проверяем, похоже ли это на список уроков
            if all(isinstance(item, dict) and "title" in item for item in data):
                logger.info(f"Найден массив из {len(data)} уроков, преобразуем в структуру курса")
                return {
                    "name": "Course with multiple lessons",
                    "description": f"Course generated from {len(data)} lessons",
                    "lessons": data
                }
            else:
                logger.warning("Получен список, но не похож на список уроков")
                return {"name": "Generated Course", "lessons": []}
                
        # Неизвестный формат
        logger.error(f"Неизвестный формат данных: {type(data)}")
        return {"name": "Generated Course", "lessons": []}

# Функция для удобного использования
def extract_course_from_api_response(content: str, debug: bool = False) -> Dict[str, Any]:
    """
    Извлекает структуру курса из ответа API
    
    Args:
        content: Текстовый ответ от API
        debug: Включить подробное логирование
        
    Returns:
        Dict[str, Any]: Структура курса
    """
    extractor = ImprovedJsonExtractor(debug=debug)
    return extractor.extract_course_data(content) 