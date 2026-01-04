#!/usr/bin/env python3
"""
Улучшенный экстрактор JSON для обработки обрезанных или некорректных JSON-строк.
Предоставляет функции для исправления и извлечения структурированных данных из текста.
"""
import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple, Union

# Настройка логирования
logger = logging.getLogger(__name__)

def fix_json_brackets(json_str: str, debug: bool = False) -> str:
    """
    Балансирует открывающие и закрывающие скобки в JSON-строке.
    
    Args:
        json_str: Исходная JSON-строка
        debug: Включить подробное логирование
        
    Returns:
        str: JSON-строка с исправленными скобками
    """
    if debug:
        logger.debug(f"Балансировка скобок для строки длиной {len(json_str)}")
    
    # Считаем открывающие и закрывающие скобки
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    if debug:
        logger.debug(f"Обнаружено: {{ = {open_braces}, }} = {close_braces}, [ = {open_brackets}, ] = {close_brackets}")
    
    # Добавляем закрывающие фигурные скобки
    if open_braces > close_braces:
        if debug:
            logger.debug(f"Добавляем {open_braces - close_braces} закрывающих }}")
        json_str += '}' * (open_braces - close_braces)
    
    # Добавляем закрывающие квадратные скобки
    if open_brackets > close_brackets:
        if debug:
            logger.debug(f"Добавляем {open_brackets - close_brackets} закрывающих ]")
        json_str += ']' * (open_brackets - close_brackets)
    
    return json_str

def fix_common_json_errors(json_str: str, debug: bool = False) -> str:
    """
    Исправляет распространенные ошибки в JSON-строках.
    
    Args:
        json_str: Исходная JSON-строка
        debug: Включить подробное логирование
        
    Returns:
        str: Исправленная JSON-строка
    """
    if debug:
        logger.debug("Исправление распространенных ошибок в JSON")
    
    # Сохраняем оригинальную строку
    original_str = json_str
    
    # 1. Удаляем запятые перед закрывающими скобками
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # 2. Исправляем неправильные кавычки (русские, типографские)
    json_str = json_str.replace('"', '"').replace('"', '"')
    json_str = json_str.replace('«', '"').replace('»', '"')
    json_str = json_str.replace("'", '"')  # Одинарные кавычки на двойные
    
    # 3. Исправляем двойные запятые
    json_str = re.sub(r',\s*,', ',', json_str)
    
    # 4. Исправляем запятые после открывающих скобок
    json_str = re.sub(r'{\s*,', '{', json_str)
    json_str = re.sub(r'\[\s*,', '[', json_str)
    
    # 5. Исправляем отсутствующие запятые между элементами массива
    json_str = re.sub(r'}\s*{', '},{', json_str)
    
    # 6. Исправляем отсутствующие запятые между ключами объекта
    json_str = re.sub(r'"\s+(?=")(?![:,}])', '",', json_str)
    
    # 7. Исправляем незакрытые строки
    # Находим строки без закрывающих кавычек перед запятой или закрывающей скобкой
    json_str = re.sub(r'"([^"]*?)(?=,|}|])', r'"\1"', json_str)
    
    if debug and json_str != original_str:
        logger.debug("Исправлены распространенные ошибки в JSON")
    
    return json_str

def extract_json_object(text: str, debug: bool = False) -> Tuple[str, bool]:
    """
    Извлекает JSON-объект из текста.
    
    Args:
        text: Исходный текст
        debug: Включить подробное логирование
        
    Returns:
        Tuple[str, bool]: (извлеченный JSON, успешно ли извлечен полный объект)
    """
    if debug:
        logger.debug(f"Извлечение JSON-объекта из текста длиной {len(text)}")
    
    # Находим первую открывающую фигурную скобку
    start_idx = text.find('{')
    if start_idx < 0:
        if debug:
            logger.debug("Не найдена открывающая фигурная скобка")
        return text, False
    
    # Получаем текст от начала JSON до конца
    json_text = text[start_idx:]
    
    # Пытаемся найти сбалансированный JSON объект, учитывая строки
    bracket_level = 0
    end_idx = -1
    in_string = False
    escaped = False

    for i, char in enumerate(json_text):
        if char == '"' and not escaped:
            in_string = not in_string
        elif char == '\\' and in_string:
            escaped = not escaped # Учитываем экранирование кавычек
        else:
            escaped = False # Сбрасываем флаг экранирования

        if not in_string: # Игнорируем скобки внутри строк
            if char == '{':
                bracket_level += 1
            elif char == '}':
                bracket_level -= 1
                if bracket_level == 0 and start_idx == 0: # Убеждаемся, что это закрытие самого внешнего объекта
                     # (start_idx == 0 гарантирует, что мы начали с самой первой скобки)
                    end_idx = i
                    break # Нашли соответствующую закрывающую скобку

    if end_idx >= 0:
        # Извлекаем полный JSON объект
        extracted = json_text[:end_idx + 1]
        if debug:
            logger.debug(f"Найден полный JSON-объект с учетом вложенности. Длина: {len(extracted)}")
        return extracted, True
    else:
        # Объект не закрыт или структура нарушена
        if debug:
            logger.debug("Не найдена соответствующая закрывающая скобка '}'. Возвращаем частичный JSON.")
        return json_text, False # Возвращаем то, что есть, для возможного восстановления

def process_truncated_json(text: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """
    Обрабатывает обрезанный JSON и пытается восстановить его структуру.
    
    Args:
        text: Исходный текст
        debug: Включить подробное логирование
        
    Returns:
        Optional[Dict[str, Any]]: Восстановленная структура JSON или None
    """
    if not text:
        if debug:
            logger.debug("Пустой входной текст")
        return None
    
    if debug:
        logger.debug(f"Обработка текста длиной {len(text)}")
    
    # Шаг 1: Извлекаем JSON из текста
    json_text, is_complete = extract_json_object(text, debug)
    
    if not json_text:
        if debug:
            logger.debug("Не удалось извлечь JSON из текста")
        return None
    
    # Шаг 2: Если JSON не закрыт, исправляем скобки
    if not is_complete:
        if debug:
            logger.debug("JSON не закрыт, исправляем скобки")
        json_text = fix_json_brackets(json_text, debug)
    
    # Шаг 3: Исправляем распространенные ошибки
    json_text = fix_common_json_errors(json_text, debug)
    
    # Шаг 4: Пытаемся распарсить исправленный JSON
    try:
        result = json.loads(json_text)
        if debug:
            logger.debug("JSON успешно распарсен после исправлений")
        return result
    except json.JSONDecodeError as e:
        if debug:
            logger.debug(f"Ошибка при парсинге исправленного JSON: {str(e)}")
    
    # Шаг 5: Если не удалось распарсить, используем регулярные выражения для извлечения данных
    try:
        if debug:
            logger.debug("Использование регулярных выражений для извлечения структуры")
        
        # Создаем базовую структуру
        course_structure = {"name": "", "description": "", "lessons": []}
        
        # Извлекаем название курса
        name_match = re.search(r'"name"\s*:\s*"([^"]*)"', json_text)
        if name_match:
            course_structure["name"] = name_match.group(1)
            if debug:
                logger.debug(f"Извлечено название курса: {course_structure['name']}")
        
        # Извлекаем описание курса
        desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', json_text)
        if desc_match:
            course_structure["description"] = desc_match.group(1)
            if debug:
                logger.debug("Извлечено описание курса")
        
        # Извлекаем уроки
        lessons_extracted = extract_lessons_from_json_text(json_text, debug)
        
        if lessons_extracted:
            course_structure["lessons"] = lessons_extracted
            if debug:
                logger.debug(f"Извлечено {len(lessons_extracted)} уроков")
            return course_structure
        else:
            if debug:
                logger.debug("Не удалось извлечь уроки")
            
            # Если не удалось извлечь уроки, но есть название курса, возвращаем структуру
            if course_structure["name"]:
                if debug:
                    logger.debug("Возвращаем частичную структуру курса (без уроков)")
                return course_structure
            else:
                if debug:
                    logger.debug("Недостаточно данных для создания структуры курса")
                return None
    
    except Exception as e:
        if debug:
            logger.debug(f"Ошибка при извлечении структуры: {str(e)}")
        return None

def extract_activities_from_text(activities_text: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Извлекает активности из текста с помощью регулярных выражений.
    
    Args:
        activities_text: Текст с описанием активностей
        debug: Включить подробное логирование
        
    Returns:
        List[Dict[str, Any]]: Список активностей
    """
    activities = []
    
    # Паттерн для поиска активностей
    activity_pattern = r'{\s*"type"\s*:\s*"([^"]+)"(.*?)}'
    activity_matches = re.finditer(activity_pattern, activities_text, re.DOTALL)
    
    for i, match in enumerate(activity_matches):
        activity_text = match.group(0)
        activity_type = match.group(1)
        
        # Создаем базовую структуру активности
        activity = {"type": activity_type}
        
        # Извлекаем заголовок, если есть
        title_match = re.search(r'"title"\s*:\s*"([^"]*)"', activity_text)
        if title_match:
            activity["title"] = title_match.group(1)
        
        # Извлекаем контент, если есть
        content_match = re.search(r'"content"\s*:\s*"([^"]*)"', activity_text)
        if content_match:
            activity["content"] = content_match.group(1)
        
        # Для quiz активностей, извлекаем вопросы
        if activity_type == "quiz":
            questions = extract_questions_from_activity(activity_text, debug)
            if questions:
                activity["questions"] = questions
        
        activities.append(activity)
        
        if debug and (i + 1) % 5 == 0:
            logger.debug(f"Извлечено {i + 1} активностей")
    
    if debug:
        logger.debug(f"Всего извлечено {len(activities)} активностей")
    
    return activities

def extract_questions_from_activity(activity_text: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Извлекает вопросы из текста активности типа quiz.
    
    Args:
        activity_text: Текст активности
        debug: Включить подробное логирование
        
    Returns:
        List[Dict[str, Any]]: Список вопросов
    """
    questions = []
    
    # Ищем массив вопросов
    questions_pattern = r'"questions"\s*:\s*\[(.*?)\]'
    questions_match = re.search(questions_pattern, activity_text, re.DOTALL)
    
    if not questions_match:
        return questions
    
    questions_text = questions_match.group(1)
    
    # Извлекаем отдельные вопросы
    question_pattern = r'{\s*"text"\s*:\s*"([^"]*)"(.*?)}'
    question_matches = re.finditer(question_pattern, questions_text, re.DOTALL)
    
    for match in question_matches:
        question_text = match.group(0)
        question = {"text": match.group(1)}
        
        # Извлекаем варианты ответов
        options = extract_options_from_question(question_text, debug)
        if options:
            question["options"] = options
        
        # Извлекаем правильный ответ
        correct_match = re.search(r'"correct"\s*:\s*(\d+)', question_text)
        if correct_match:
            try:
                question["correct"] = int(correct_match.group(1))
            except ValueError:
                pass
        
        questions.append(question)
    
    return questions

def extract_options_from_question(question_text: str, debug: bool = False) -> List[str]:
    """
    Извлекает варианты ответов из текста вопроса.
    
    Args:
        question_text: Текст вопроса
        debug: Включить подробное логирование
        
    Returns:
        List[str]: Список вариантов ответов
    """
    options = []
    
    # Ищем массив вариантов
    options_pattern = r'"options"\s*:\s*\[(.*?)\]'
    options_match = re.search(options_pattern, question_text, re.DOTALL)
    
    if not options_match:
        return options
    
    options_text = options_match.group(1)
    
    # Извлекаем отдельные варианты
    option_pattern = r'"([^"]*)"'
    option_matches = re.finditer(option_pattern, options_text)
    
    for match in option_matches:
        options.append(match.group(1))
    
    return options

def extract_lessons_from_json_text(json_text: str, debug: bool = False) -> List[Dict[str, Any]]:
    """
    Извлекает уроки из текста JSON.
    
    Args:
        json_text: Текст JSON
        debug: Включить подробное логирование
        
    Returns:
        List[Dict[str, Any]]: Список уроков
    """
    lessons = []
    
    # Паттерн для поиска массива уроков
    lessons_array_pattern = r'"lessons"\s*:\s*\[(.*?)(?:\]\s*}|\Z)'
    lessons_array_match = re.search(lessons_array_pattern, json_text, re.DOTALL)
    
    if not lessons_array_match:
        if debug:
            logger.debug("Не найден массив уроков")
        return lessons
    
    lessons_text = lessons_array_match.group(1)
    
    # Паттерн для поиска отдельных уроков
    lesson_pattern = r'{\s*"title"\s*:\s*"([^"]*)"(.*?)(?:},|\}\Z)'
    lesson_matches = re.finditer(lesson_pattern, lessons_text, re.DOTALL)
    
    for i, match in enumerate(lesson_matches):
        lesson_text = match.group(0)
        lesson_title = match.group(1)
        
        # Создаем структуру урока
        lesson = {
            "title": lesson_title,
            "activities": []
        }
        
        # Извлекаем дополнительные поля
        desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', lesson_text)
        if desc_match:
            lesson["description"] = desc_match.group(1)
        
        # Извлекаем активности
        activities_pattern = r'"activities"\s*:\s*\[(.*?)(?:\],|\]\Z)'
        activities_match = re.search(activities_pattern, lesson_text, re.DOTALL)
        
        if activities_match:
            activities_text = activities_match.group(1)
            lesson["activities"] = extract_activities_from_text(activities_text, debug)
            
            if debug:
                logger.debug(f"Извлечен урок '{lesson_title}' с {len(lesson['activities'])} активностями")
        else:
            if debug:
                logger.debug(f"Извлечен урок '{lesson_title}' без активностей")
        
        lessons.append(lesson)
        
        if debug and (i + 1) % 5 == 0:
            logger.debug(f"Извлечено {i + 1} уроков")
    
    if debug:
        logger.debug(f"Всего извлечено {len(lessons)} уроков")
    
    return lessons
