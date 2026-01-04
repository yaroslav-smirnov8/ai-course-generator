#!/usr/bin/env python3
"""
Улучшенный извлекатель JSON из ответов API с использованием библиотек demjson3 и json-repair.
"""
import json
import re
import logging
from typing import Dict, Any, Tuple, List, Optional

# Импортируем специализированные библиотеки для работы с JSON
try:
    import demjson3 as demjson
except ImportError:
    demjson = None

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

# Настройка логирования
logger = logging.getLogger(__name__)

def extract_json_from_api_response(content: str, debug: bool = False) -> str:
    """
    Извлекает JSON-строку из контента ответа API с использованием
    специализированных библиотек и собственных алгоритмов.
    
    Args:
        content: Исходный текст ответа API
        debug: Включить подробное логирование
        
    Returns:
        str: Извлеченная JSON-строка или исходный контент, если нет специальной обработки
    """
    if debug:
        logger.info(f"Извлечение JSON из контента длиной {len(content)} символов")
        if len(content) > 100:
            logger.info(f"Первые 50 символов контента: {content[:50]}")
            logger.info(f"Последние 50 символов контента: {content[-50:]}")
    
    # Если контент пустой или слишком короткий
    if not content or len(content.strip()) < 5:
        logger.warning("Контент слишком короткий для JSON")
        return ""

    # Шаг 1: Проверяем, может ли весь контент быть валидным JSON
    if _is_valid_json(content):
        if debug:
            logger.info("Весь контент уже является валидным JSON")
        return content
    
    # Шаг 2: Удаляем обрамляющие бэктики (Markdown код)
    cleaned_content = _remove_backticks(content)
    if _is_valid_json(cleaned_content):
        if debug:
            logger.info("Контент после удаления бэктиков является валидным JSON")
        return cleaned_content
    
    # Шаг 3: Ищем JSON в блоках кода
    json_in_code_blocks = _extract_json_from_code_blocks(cleaned_content)
    if json_in_code_blocks:
        if debug:
            logger.info(f"Найден валидный JSON в блоке кода длиной {len(json_in_code_blocks)} символов")
        return json_in_code_blocks
    
    # Шаг 4: Используем более надежный метод извлечения JSON на основе подсчета скобок
    extracted_json = _extract_json_by_brackets(cleaned_content)
    if extracted_json and _is_valid_json_structure(extracted_json):
        if debug:
            logger.info(f"Извлечен потенциально валидный JSON длиной {len(extracted_json)} символов")
        return extracted_json
    
    # Шаг 5: Используем специализированные библиотеки, если они доступны
    if repair_json:
        try:
            repaired = repair_json(cleaned_content)
            if _is_valid_json(repaired):
                if debug:
                    logger.info("JSON успешно восстановлен с помощью json-repair")
                return repaired
        except Exception as e:
            if debug:
                logger.debug(f"Ошибка при восстановлении JSON с помощью json-repair: {str(e)}")
    
    if demjson:
        try:
            # demjson более снисходителен к ошибкам в JSON
            parsed = demjson.decode(cleaned_content)
            # Преобразуем обратно в строку, но с корректным форматированием
            fixed_json = json.dumps(parsed, ensure_ascii=False)
            if debug:
                logger.info("JSON успешно обработан с помощью demjson")
            return fixed_json
        except Exception as e:
            if debug:
                logger.debug(f"Ошибка при обработке JSON с помощью demjson: {str(e)}")
    
    # Возвращаем исходный контент, если не удалось применить специальную обработку
    if debug:
        logger.warning("Не удалось извлечь валидный JSON, возвращаем исходный контент")
    return content

def _is_valid_json(text: str) -> bool:
    """Проверяет, является ли текст валидным JSON."""
    try:
        # Пробуем стандартный парсинг
        json.loads(text.strip())
        return True
    except json.JSONDecodeError:
        return False

def _is_valid_json_structure(text: str) -> bool:
    """
    Проверяет, имеет ли текст структуру, похожую на JSON
    (начинается с { или [ и заканчивается } или ]).
    """
    text = text.strip()
    return ((text.startswith('{') and text.endswith('}')) or 
            (text.startswith('[') and text.endswith(']')))

def _remove_backticks(content: str) -> str:
    """Удаляет Markdown бэктики, обрамляющие код."""
    content = content.strip()
    
    # Удаляем тройные бэктики с возможным указанием языка
    if content.startswith('```') and content.endswith('```'):
        content = re.sub(r'^```.*?\n', '', content)
        content = re.sub(r'\n```$', '', content)
        return content.strip()
    
    # Удаляем одиночные бэктики
    if content.startswith('`') and content.endswith('`'):
        return content[1:-1].strip()
    
    return content

def _extract_json_from_code_blocks(content: str) -> str:
    """Извлекает JSON из блоков кода в формате Markdown."""
    # Ищем блоки кода с JSON
    json_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    json_blocks = re.findall(json_block_pattern, content)
    
    for block in json_blocks:
        if _is_valid_json_structure(block):
            try:
                # Проверяем, валиден ли JSON
                json.loads(block.strip())
                return block.strip()
            except json.JSONDecodeError:
                # Если не валидный JSON, пробуем восстановить с помощью библиотек
                if repair_json:
                    try:
                        repaired = repair_json(block.strip())
                        if _is_valid_json(repaired):
                            return repaired
                    except:
                        pass
                
                if demjson:
                    try:
                        parsed = demjson.decode(block.strip())
                        return json.dumps(parsed, ensure_ascii=False)
                    except:
                        pass
    
    return ""

def _extract_json_by_brackets(content: str) -> str:
    """
    Извлекает JSON из текста, учитывая правильное соответствие скобок,
    строк в кавычках и экранированных символов.
    """
    # Ищем начало JSON объекта или массива
    start_idx = min(
        content.find('{') if content.find('{') != -1 else float('inf'),
        content.find('[') if content.find('[') != -1 else float('inf')
    )
    
    if start_idx == float('inf'):
        return ""  # Не найдено начало JSON
    
    # Определяем тип скобки, с которой начинается JSON
    opening_bracket = content[start_idx]
    closing_bracket = '}' if opening_bracket == '{' else ']'
    
    # Отслеживаем уровень вложенности скобок
    bracket_level = 0
    in_string = False
    escape_next = False
    
    # Проходим по всем символам, начиная с открывающей скобки
    for i in range(start_idx, len(content)):
        char = content[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
        elif char == '"' and not escape_next:
            in_string = not in_string
        elif not in_string:
            if char == opening_bracket:
                bracket_level += 1
            elif char == closing_bracket:
                bracket_level -= 1
                if bracket_level == 0:
                    # Нашли соответствующую закрывающую скобку
                    json_str = content[start_idx:i+1]
                    return json_str
    
    # Если мы дошли до конца текста без нахождения закрывающей скобки,
    # возвращаем пустую строку или частичный JSON (можно изменить поведение)
    return ""

def find_json_objects(text: str) -> List[str]:
    """
    Находит все возможные JSON объекты в тексте.
    
    Args:
        text: Текст для поиска
        
    Returns:
        List[str]: Список найденных JSON-строк
    """
    results = []
    
    # Находим все потенциальные JSON-объекты (начинаются с { и заканчиваются })
    start_pos = 0
    while True:
        # Ищем открывающую скобку
        pos = text.find('{', start_pos)
        if pos == -1:
            break
        
        # Отслеживаем уровень вложенности скобок
        bracket_level = 0
        in_string = False
        escape_next = False
        
        for i in range(pos, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
            elif char == '"' and not escape_next:
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    bracket_level += 1
                elif char == '}':
                    bracket_level -= 1
                    
                    if bracket_level == 0:
                        # Нашли закрывающую скобку для нашей открывающей
                        json_candidate = text[pos:i+1]
                        # Проверяем валидность JSON
                        try:
                            json.loads(json_candidate)
                            results.append(json_candidate)
                        except json.JSONDecodeError:
                            # Если не валидный, пробуем восстановить
                            if repair_json:
                                try:
                                    repaired = repair_json(json_candidate)
                                    results.append(repaired)
                                except:
                                    pass
                            elif demjson:
                                try:
                                    demjson.decode(json_candidate)  # Проверяем, может ли demjson распарсить
                                    results.append(json_candidate)
                                except:
                                    pass
                        
                        start_pos = i + 1
                        break
        else:
            # Если не нашли закрывающую скобку, выходим из цикла
            break
            
        if start_pos >= len(text):
            break
    
    # Находим все потенциальные JSON-массивы (начинаются с [ и заканчиваются ])
    start_pos = 0
    while True:
        # Ищем открывающую скобку массива
        pos = text.find('[', start_pos)
        if pos == -1:
            break
        
        # Аналогичный алгоритм для массивов
        bracket_level = 0
        in_string = False
        escape_next = False
        
        for i in range(pos, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
            elif char == '"' and not escape_next:
                in_string = not in_string
            elif not in_string:
                if char == '[':
                    bracket_level += 1
                elif char == ']':
                    bracket_level -= 1
                    
                    if bracket_level == 0:
                        json_candidate = text[pos:i+1]
                        try:
                            json.loads(json_candidate)
                            results.append(json_candidate)
                        except json.JSONDecodeError:
                            if repair_json:
                                try:
                                    repaired = repair_json(json_candidate)
                                    results.append(repaired)
                                except:
                                    pass
                            elif demjson:
                                try:
                                    demjson.decode(json_candidate)
                                    results.append(json_candidate)
                                except:
                                    pass
                        
                        start_pos = i + 1
                        break
        else:
            break
            
        if start_pos >= len(text):
            break
    
    return results

def process_api_response(response_text: str, debug: bool = False) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Обрабатывает ответ API, извлекая из него структуру курса.
    
    Args:
        response_text: Текст ответа API
        debug: Включить подробное логирование
        
    Returns:
        Tuple[Optional[Dict[str, Any]], bool]: Словарь с данными и флаг успеха
    """
    if debug:
        logger.info(f"=== НАЧАЛО ОБРАБОТКИ ОТВЕТА API ===")
        logger.info(f"Исходный контент перед очисткой длиной {len(response_text)} символов")
        if len(response_text) > 100:
            logger.info(f"ПЕРВЫЕ 100 СИМВОЛОВ ИСХОДНОГО КОНТЕНТА: {response_text[:100]}")
            logger.info(f"ПОСЛЕДНИЕ 100 СИМВОЛОВ ИСХОДНОГО КОНТЕНТА: {response_text[-100:]}")
    
    # 1. Извлекаем JSON из ответа API
    json_content = extract_json_from_api_response(response_text, debug)
    
    if debug:
        logger.info(f"Получен извлеченный JSON длиной {len(json_content)} символов")
    
    # 2. Если извлечь не удалось, ищем все возможные JSON-объекты
    if not json_content or not _is_valid_json_structure(json_content):
        if debug:
            logger.warning("Не удалось извлечь JSON обычным способом, ищем все JSON-объекты")
        
        json_objects = find_json_objects(response_text)
        
        if debug:
            logger.info(f"Найдено {len(json_objects)} JSON-объектов")
        
        # Выбираем самый длинный JSON-объект
        if json_objects:
            json_content = max(json_objects, key=len)
            if debug:
                logger.info(f"Выбран самый длинный JSON-объект длиной {len(json_content)} символов")
    
    # 3. Пытаемся распарсить JSON
    try:
        if _is_valid_json(json_content):
            parsed_json = json.loads(json_content)
            if debug:
                logger.info("JSON успешно распарсен стандартным парсером")
            return parsed_json, True
    except json.JSONDecodeError as e:
        if debug:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
    
    # 4. Если стандартный парсинг не удался, пробуем восстановить с помощью библиотек
    if repair_json:
        try:
            repaired = repair_json(json_content)
            parsed_json = json.loads(repaired)
            if debug:
                logger.info("JSON успешно восстановлен с помощью json-repair")
            return parsed_json, True
        except Exception as e:
            if debug:
                logger.error(f"Ошибка при восстановлении JSON: {str(e)}")
    
    if demjson:
        try:
            parsed_json = demjson.decode(json_content)
            if debug:
                logger.info("JSON успешно распарсен с помощью demjson")
            return parsed_json, True
        except Exception as e:
            if debug:
                logger.error(f"Ошибка при парсинге с помощью demjson: {str(e)}")
    
    if debug:
        logger.error("Не удалось распарсить JSON никаким способом")
    
    return None, False 