import asyncio
import logging
import re
import time
import uuid
from urllib.parse import urlparse
import random
import os
import json

import g4f
import requests
from g4f import ChatCompletion, Provider
from .log_config import get_g4f_logger
from enum import Enum
import sys
from typing import Optional, Tuple, List, Dict, Any, Union
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger("g4f_handler")
g4f_logger = get_g4f_logger()

# Настройка уровня логирования для g4f
g4f.debug.logging = True  # Включаем расширенное логирование g4f

# Получаем настроенный логгер для g4f
g4f_logger = get_g4f_logger('g4f.handler')

# Основной логгер модуля
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Определяем глобальную переменную для отслеживания доступности Mistral API
MISTRAL_AVAILABLE = False
CHAT_MESSAGE_AVAILABLE = False

# Проверка доступности модуля mistralai
try:
    from mistralai import Mistral
    import mistralai.models as mistral_models
    MISTRAL_AVAILABLE = True
    try:
        # Проверяем, доступен ли класс ChatMessage в новой версии API
        from mistralai.models.chat_completion import ChatMessage
        CHAT_MESSAGE_AVAILABLE = True
        logger.info("Используем новую версию API Mistral с ChatMessage")
    except ImportError:
        logger.info("ChatMessage не найден в mistralai.models, используем формат словаря")
except ImportError:
    logger.warning("Модуль mistralai не найден. Пожалуйста, установите его: pip install mistralai")

# Определяем классы исключений для Mistral API для обратной совместимости
class MistralAPIException(Exception):
    pass

class MistralConnectionException(Exception):
    pass

class MistralRateLimitException(Exception):
    pass

# Импортируем Mistral API клиент (с подробным логированием ошибок)
try:
    logger.info(f"Текущий путь Python: {sys.path}")
    logger.info("Пытаюсь импортировать Mistral...")

    # Попытка установить mistralai если не установлен
    try:
        from mistralai import Mistral, models
        MISTRAL_AVAILABLE = True
        logger.info("Mistral API успешно импортирован и доступен")
    except ImportError as e:
        logger.error(f"Ошибка импорта Mistral: {e}")
        logger.info("Пытаюсь установить mistralai...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai"])
            logger.info("mistralai успешно установлен, пробую импортировать снова")
            from mistralai import Mistral, models
            MISTRAL_AVAILABLE = True
            logger.info("Mistral API успешно импортирован после установки")
        except Exception as install_err:
            logger.error(f"Не удалось установить mistralai: {install_err}")
            MISTRAL_AVAILABLE = False
except Exception as e:
    MISTRAL_AVAILABLE = False
    logger.error(f"Непредвиденная ошибка при импорте mistralai: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Импортируем наш новый модуль для работы с Mistral API
from .mistral_api import MistralHandler

# Импортируем наш новый модуль для работы с OpenRouter API
from .openrouter_api import OpenRouterHandler, OPENROUTER_AVAILABLE

# Импортируем наш новый модуль для работы с LLM7 API
try:
    from .llm7_api import LLM7Handler, LLM7_AVAILABLE
except ImportError:
    LLM7_AVAILABLE = False

try:
    import g4f
    G4F_AVAILABLE = True
except ImportError:
    logging.warning("G4F не установлен, некоторые функции будут недоступны")
    G4F_AVAILABLE = False

# Функция для определения языка ответа
def detect_language(text):
    """
    Простое определение языка ответа на основе первых слов.
    Возвращает 'en' для английского (по умолчанию) или код другого языка.
    """
    if not text or not isinstance(text, str):
        return 'en'  # Возвращаем английский по умолчанию

    # Берем первые несколько слов
    first_words = text.strip().split()[:5]
    first_text = ' '.join(first_words).lower()

    # Простые паттерны для определения наиболее распространенных языков
    language_patterns = {
        'ru': ['привет', 'здравствуйте', 'добрый', 'как', 'что', 'почему', 'где', 'когда', 'я'],
        'zh': ['你好', '早上好', '晚上好', '谢谢', '请问', '什么', '为什么'],
        'es': ['hola', 'buenos', 'como', 'gracias', 'por qué', 'dónde', 'cuándo'],
        'fr': ['bonjour', 'salut', 'merci', 'pourquoi', 'comment', 'où', 'quand'],
        'de': ['hallo', 'guten', 'danke', 'warum', 'wie', 'wo', 'wann'],
    }

    # Проверяем наличие характерных слов
    for lang, patterns in language_patterns.items():
        for pattern in patterns:
            if pattern in first_text:
                return lang

    # По умолчанию возвращаем английский
    return 'en'


class G4FHandler:
    def __init__(self, api_key=None, api_base=None, openrouter_api_key=None, llm7_api_key=None, gemini_handler=None, groq_handler=None, together_handler=None, cerebras_handler=None, chutes_handler=None):
        """Инициализация обработчика G4F"""
        # Получаем API ключ из аргументов или переменной окружения
        # Жёстко задаем ключ если не передан через аргументы и не найден в env
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY") or "15GYbGxbGBYxFcGigUVCJTv7bfUGkK5d"
        self.api_base = api_base or os.environ.get("MISTRAL_API_BASE") or "https://api.mistral.ai"

        # OpenRouter API ключ
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")

        # LLM7 API ключ
        self.llm7_api_key = llm7_api_key or os.environ.get("LLM7_API_KEY")

        # Обработчики провайдеров
        self.gemini_handler = gemini_handler
        self.groq_handler = groq_handler
        self.together_handler = together_handler
        self.cerebras_handler = cerebras_handler
        self.chutes_handler = chutes_handler

        # Инициализация основных параметров
        self._current_model = None  # Текущая модель
        self._model_provider = None  # Текущий провайдер
        self._timeout = 120  # Таймаут запросов по умолчанию, сек

        # Подробное логирование для отладки
        logger.info(f"Инициализация G4FHandler (api_key доступен: {'Да' if self.api_key else 'Нет'})")
        logger.info(f"api_key: {self.api_key[:5]}... (скрыт)")
        logger.info(f"api_base: {self.api_base}")
        logger.info(f"MISTRAL_AVAILABLE: {MISTRAL_AVAILABLE}")
        logger.info(f"Gemini handler: {'Да' if self.gemini_handler else 'Нет'}")
        logger.info(f"Groq handler: {'Да' if self.groq_handler else 'Нет'}")
        logger.info(f"Together handler: {'Да' if self.together_handler else 'Нет'}")
        logger.info(f"Cerebras handler: {'Да' if self.cerebras_handler else 'Нет'}")
        logger.info(f"Chutes handler: {'Да' if self.chutes_handler else 'Нет'}")

        # Инициализируем клиент Mistral с использованием нового модуля
        self.mistral_client = None
        self.mistral_handler = None
        self.mistral_model = "open-mistral-nemo"  # Используем предпочтительную модель

        if MISTRAL_AVAILABLE and self.api_key:
            try:
                # Используем наш новый обработчик Mistral API
                self.mistral_handler = MistralHandler(
                    api_key=self.api_key,
                    api_base=self.api_base
                )
                logger.info("Mistral API обработчик успешно инициализирован")

                # Для совместимости со старым кодом
                self.mistral_client = self.mistral_handler.mistral_client

            except Exception as e:
                logger.error(f"Ошибка при инициализации Mistral API обработчика: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.mistral_handler = None
                self.mistral_client = None
        elif not self.api_key:
            logger.warning("API ключ Mistral не указан, клиент не будет инициализирован")
        elif not MISTRAL_AVAILABLE:
            logger.warning("Библиотека Mistral API не установлена")

        # Инициализируем OpenRouter API
        self.openrouter_handler = None
        if OPENROUTER_AVAILABLE and self.openrouter_api_key:
            try:
                self.openrouter_handler = OpenRouterHandler(api_key=self.openrouter_api_key)
                logger.info("OpenRouter API обработчик успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации OpenRouter API обработчика: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.openrouter_handler = None
        elif not self.openrouter_api_key:
            logger.warning("API ключ OpenRouter не указан")
        elif not OPENROUTER_AVAILABLE:
            logger.warning("Модуль OpenRouter API не доступен")

        # Инициализируем LLM7 API
        self.llm7_handler = None
        if LLM7_AVAILABLE and self.llm7_api_key:
            try:
                self.llm7_handler = LLM7Handler(api_key=self.llm7_api_key)
                logger.info("LLM7 API обработчик успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка при инициализации LLM7 API обработчика: {e}")
                import traceback
                logger.error(traceback.format_exc())
                self.llm7_handler = None
        elif not self.llm7_api_key:
            logger.warning("API ключ LLM7 не указан")
        elif not LLM7_AVAILABLE:
            logger.warning("Модуль LLM7 API не доступен")

        # Инициализируем G4F как запасной вариант
        logger.info("Инициализация G4F как запасного варианта")
        try:
            if G4F_AVAILABLE:
                # Настраиваем модель и провайдер для G4F
                self._current_model, self._model_provider = self._setup_fixed_model()
            else:
                logger.warning("G4F не установлен, будет использоваться только Mistral API")
        except Exception as e:
            logger.error(f"Ошибка при настройке модели G4F: {e}")
            logger.warning("G4F инициализирован, но не удалось установить модель и провайдер")

        # Для генерации изображений
        self.image_providers = {
            "Blackbox": ["flux"],
            "ImageLabs": ["sdxl-turbo"],
            "PollinationsAI": ["lux", "flux-pro", "flux-dev", "flux-schnell", "dall-e-3", "sdxl-turbo"]
        }

    def _setup_fixed_model(self) -> Tuple[Optional[str], Optional[Any]]:
        """
        Настраивает фиксированную модель и провайдер для G4F
        В случае сбоя возвращает None, None
        """
        try:
            # Попробуем найти рабочую комбинацию модели и провайдера
            working_providers = []

            # Список провайдеров для проверки (от наиболее предпочтительных к менее)
            # Оставляем только рабочие провайдеры
            provider_priority = [
                g4f.Provider.You,
                g4f.Provider.Liaobots
            ]

            # Проверим какие провайдеры доступны
            for provider in provider_priority:
                try:
                    provider_info = provider.__name__
                    if hasattr(provider, 'working') and provider.working:
                        working_providers.append(provider)
                except Exception as e:
                    logger.warning(f"Не удалось проверить провайдера {provider.__name__}: {e}")

            # Если есть рабочие провайдеры, используем первый из них
            if working_providers:
                selected_provider = working_providers[0]
                # Выбираем модель GPT-3.5 для большинства провайдеров
                selected_model = "gpt-3.5-turbo"
                logger.info(f"Выбрана модель {selected_model} с провайдером {selected_provider.__name__}")
                return selected_model, selected_provider
            else:
                logger.warning("Не найдено рабочих провайдеров G4F")
                return None, None
        except Exception as e:
            logger.error(f"Ошибка при настройке модели G4F: {e}")
            return None, None

    async def get_available_model(self):
        """
        УСТАРЕВШИЙ МЕТОД - используется только для обратной совместимости
        Находит доступную для использования модель и провайдера. Автоматически
        обновляет self._current_model и self._model_provider.

        Returns:
            tuple: (model, provider) - кортеж с моделью и провайдером
        """
        # Просто устанавливаем фиксированные значения без тестирования
        logger.info("Установка фиксированной модели и провайдера без тестирования")
        try:
            # Используем Blackbox вместо You по запросу пользователя
            provider_name = "Blackbox"
            model_name = "BLACKBOXAI"

            try:
                provider = getattr(__import__("g4f.Provider", fromlist=[provider_name]), provider_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"Ошибка импорта провайдера {provider_name}: {e}")
                # Запасной провайдер
                provider_name = "OpenaiChat"
                provider = getattr(__import__("g4f.Provider", fromlist=[provider_name]), provider_name)

            try:
                # Исправлено: корректно создаем модель
                if hasattr(g4f.models, "ModelUtils") and hasattr(g4f.models.ModelUtils, "convert"):
                    model = g4f.models.ModelUtils.convert(model_name)
                else:
                    # Для старых версий g4f
                    model = g4f.Model(name=model_name, base_provider=provider)

                self._current_model = model
                self._model_provider = provider
                logger.info(f"Установлена модель {model_name} с провайдером {provider_name} (без тестирования)")
                return model, provider
            except Exception as e:
                logger.error(f"Ошибка при создании модели: {e}")
                # Пробуем более простой способ
                try:
                    self._current_model = g4f.models.default
                    self._model_provider = provider
                    logger.info(f"Установлена модель по умолчанию с провайдером {provider_name}")
                    return self._current_model, self._model_provider
                except Exception as e:
                    logger.error(f"Ошибка при установке модели по умолчанию: {e}")
                    return None, None
        except Exception as e:
            logger.error(f"Ошибка при установке фиксированной модели: {e}")
            return None, None

    async def generate_content(self, prompt: str, model=None, provider=None) -> str:
        """
        Асинхронный метод для генерации контента по запросу
        """
        request_id = str(random.getrandbits(32)).encode('utf-8').hex()[:8]
        logger.info(f"[{request_id}] Начало генерации для промпта длиной {len(prompt)} символов")

        # Определяем язык запроса
        detected_language = detect_language(prompt)
        logger.info(f"[{request_id}] Определен язык запроса: {detected_language}")

        # Добавляем отладочную информацию о доступности API
        logger.info(f"[{request_id}] OPENROUTER_AVAILABLE: {OPENROUTER_AVAILABLE}")
        logger.info(f"[{request_id}] openrouter_handler: {bool(self.openrouter_handler)}")
        logger.info(f"[{request_id}] LLM7_AVAILABLE: {LLM7_AVAILABLE}")
        logger.info(f"[{request_id}] llm7_handler: {bool(self.llm7_handler)}")
        logger.info(f"[{request_id}] gemini_handler: {bool(self.gemini_handler)}")
        logger.info(f"[{request_id}] groq_handler: {bool(self.groq_handler)}")
        logger.info(f"[{request_id}] together_handler: {bool(self.together_handler)}")
        logger.info(f"[{request_id}] cerebras_handler: {bool(self.cerebras_handler)}")
        logger.info(f"[{request_id}] chutes_handler: {bool(self.chutes_handler)}")
        logger.info(f"[{request_id}] MISTRAL_AVAILABLE: {MISTRAL_AVAILABLE}")
        logger.info(f"[{request_id}] mistral_client: {bool(self.mistral_client)}")
        logger.info(f"[{request_id}] api_key доступен: {'Да' if self.api_key else 'Нет'}")
        logger.info(f"[{request_id}] openrouter_api_key доступен: {'Да' if self.openrouter_api_key else 'Нет'}")
        logger.info(f"[{request_id}] llm7_api_key доступен: {'Да' if self.llm7_api_key else 'Нет'}")

        # Приоритет 1: Gemini API (самый высокий приоритет)
        if self.gemini_handler and self.gemini_handler.is_available():
            try:
                logger.info(f"[{request_id}] Пробуем использовать Gemini API")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через Gemini
                result = await self.gemini_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result:
                    logger.info(f"[{request_id}] Успешно получен ответ от Gemini API, длина: {len(result)}")
                    return result
                else:
                    logger.warning(f"[{request_id}] Gemini API вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании Gemini API: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] Gemini API недоступен или вернул ошибку, переключаемся на OpenRouter")

        # Приоритет 2: OpenRouter API (высокий приоритет)
        if self.openrouter_handler and self.openrouter_handler.is_available():
            try:
                logger.info(f"[{request_id}] Пробуем использовать OpenRouter API")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через OpenRouter
                result = await self.openrouter_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result:
                    logger.info(f"[{request_id}] Успешно получен ответ от OpenRouter API, длина: {len(result)}")
                    return result
                else:
                    logger.warning(f"[{request_id}] OpenRouter API вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании OpenRouter API: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] OpenRouter API недоступен или вернул ошибку, переключаемся на Groq")

        # Приоритет 3: Groq API (высокий приоритет)
        if self.groq_handler and self.groq_handler.is_available():
            try:
                logger.info(f"[{request_id}] Пробуем использовать Groq API")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через Groq
                result = await self.groq_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result:
                    logger.info(f"[{request_id}] Успешно получен ответ от Groq API, длина: {len(result)}")
                    return result
                else:
                    logger.warning(f"[{request_id}] Groq API вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании Groq API: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] Groq API недоступен или вернул ошибку, переключаемся на OpenRouter")

        # Приоритет 4: LLM7 API (высокий приоритет)
        if self.llm7_handler and self.llm7_handler.is_available():
            try:
                logger.info(f"[{request_id}] Пробуем использовать LLM7 API")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через LLM7
                result = await self.llm7_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result:
                    logger.info(f"[{request_id}] Успешно получен ответ от LLM7 API, длина: {len(result)}")
                    return result
                else:
                    logger.warning(f"[{request_id}] LLM7 API вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании LLM7 API: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] LLM7 API недоступен или вернул ошибку, переключаемся на Together AI")

        # Приоритет 5: Together AI (высокий приоритет)
        if self.together_handler:
            try:
                logger.info(f"[{request_id}] Пробуем использовать Together AI")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через Together AI
                result = await self.together_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result and result.get('content'):
                    content = result['content']
                    logger.info(f"[{request_id}] Успешно получен ответ от Together AI, длина: {len(content)}")
                    return content
                else:
                    logger.warning(f"[{request_id}] Together AI вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании Together AI: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] Together AI недоступен или вернул ошибку, переключаемся на Cerebras")

        # Приоритет 6: Cerebras (высокий приоритет)
        if self.cerebras_handler:
            try:
                logger.info(f"[{request_id}] Пробуем использовать Cerebras")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через Cerebras
                result = await self.cerebras_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result and result.get('content'):
                    content = result['content']
                    logger.info(f"[{request_id}] Успешно получен ответ от Cerebras, длина: {len(content)}")
                    return content
                else:
                    logger.warning(f"[{request_id}] Cerebras вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании Cerebras: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] Cerebras недоступен или вернул ошибку, переключаемся на Chutes")

        # Приоритет 7: Chutes AI (средний приоритет)
        if self.chutes_handler:
            try:
                logger.info(f"[{request_id}] Пробуем использовать Chutes AI")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через Chutes AI
                result = await self.chutes_handler.generate_content(
                    prompt=enhanced_prompt,
                    temperature=0.7,
                    max_tokens=2048
                )

                if result and result.get('content'):
                    content = result['content']
                    logger.info(f"[{request_id}] Успешно получен ответ от Chutes AI, длина: {len(content)}")
                    return content
                else:
                    logger.warning(f"[{request_id}] Chutes AI вернул пустой ответ")

            except Exception as e:
                logger.error(f"[{request_id}] Ошибка при использовании Chutes AI: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] Chutes AI недоступен или вернул ошибку, переключаемся на Mistral")

        # Приоритет 8: Mistral API (средний приоритет)
        # Если есть доступ к Mistral API через наш новый обработчик, используем его
        if self.mistral_handler and self.mistral_handler.is_available():
            try:
                logger.info(f"[{request_id}] Пробуем использовать Mistral API через новый обработчик")
                logger.info(f"[{request_id}] Выбрана модель Mistral: {self.mistral_model}")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                    logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = prompt

                # Генерируем контент через наш новый обработчик
                result = await self.mistral_handler.generate_content(
                    prompt=enhanced_prompt,
                    model=self.mistral_model,
                    temperature=0.7,
                    max_tokens=2048
                )

                logger.info(f"[{request_id}] Успешно получен ответ от Mistral API, длина: {len(result)}")
                return result

            except MistralConnectionException as e:
                logger.error(f"[{request_id}] Ошибка подключения к Mistral API: {e}")

            except MistralRateLimitException as e:
                logger.error(f"[{request_id}] Превышен лимит запросов к Mistral API: {e}")

            except MistralAPIException as e:
                logger.error(f"[{request_id}] Ошибка Mistral API: {e}")

            except Exception as e:
                logger.error(f"[{request_id}] Непредвиденная ошибка при использовании Mistral API: {e}")
                import traceback
                logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

            logger.warning(f"[{request_id}] Mistral API недоступен или вернул ошибку")

        # Приоритет 9: G4F (самый низкий приоритет)
        # Если все остальные провайдеры недоступны или вернули ошибку, используем G4F
        logger.warning(f"[{request_id}] Переключаемся на использование G4F")

        try:
            # Получаем модель и провайдер для G4F
            g4f_model, g4f_provider = self._get_model_and_provider(model)

            if not g4f_model or not g4f_provider:
                logger.error(f"[{request_id}] Не удалось получить модель и провайдер G4F")
                return "Извините, сервис генерации временно недоступен. Пожалуйста, попробуйте позже."

            logger.info(f"[{request_id}] Используем G4F с моделью {g4f_model} и провайдером {g4f_provider.__name__}")

            # Добавляем инструкцию о языке ответа в промпт
            language_instructions = {
                'ru': "Пожалуйста, ответь на русском языке.",
                'zh': "请用中文回答。",
                'es': "Por favor, responde en español.",
                'fr': "Veuillez répondre en français.",
                'de': "Bitte antworte auf Deutsch.",
            }

            # Если язык определен и не английский, добавляем инструкцию
            if detected_language != 'en' and detected_language in language_instructions:
                enhanced_prompt = f"{prompt}\n\n{language_instructions[detected_language]}"
                logger.info(f"[{request_id}] Добавлена инструкция о языке ответа: {detected_language}")
            else:
                enhanced_prompt = prompt

            # Создаем сообщения для G4F
            messages = [{"role": "user", "content": enhanced_prompt}]

            # Генерируем ответ с помощью G4F с уменьшенным таймаутом
            response = await g4f.ChatCompletion.create_async(
                model=g4f_model,
                messages=messages,
                provider=g4f_provider,
                timeout=60  # Уменьшаем таймаут до 60 секунд
            )

            if response:
                logger.info(f"[{request_id}] Успешно получен ответ от G4F, длина: {len(response)}")
                return response
            else:
                logger.warning(f"[{request_id}] G4F вернул пустой ответ")
                return "Извините, не удалось сгенерировать ответ. Пожалуйста, попробуйте позже."

        except Exception as e:
            logger.error(f"[{request_id}] Ошибка при использовании G4F: {e}")
            import traceback
            logger.error(f"[{request_id}] Трассировка ошибки: {traceback.format_exc()}")

        return "Извините, сервис генерации временно недоступен. Пожалуйста, попробуйте позже."

    async def generate_image(self, prompt: str, width: int = 768, height: int = 768, steps: int = 28, seed: int = 0, randomize_seed: bool = True, use_cache: bool = True):
        """
        Генерирует изображение с использованием G4F

        Args:
            prompt: Запрос для генерации изображения
            width: Ширина изображения
            height: Высота изображения
            steps: Количество шагов генерации
            seed: Сид для генерации (0 для случайного)
            randomize_seed: Использовать случайный сид
            use_cache: Использовать кэширование (если False, всегда генерирует новое изображение)

        Returns:
            str: URL сгенерированного изображения
        """
        # Проверяем, есть ли уже уникальный суффикс в промпте
        has_unique_suffix = "[seed:" in prompt or "[t:" in prompt or "[time:" in prompt

        # Всегда используем случайный сид, если кэширование отключено или явно запрошена рандомизация
        if not use_cache or randomize_seed or seed == 0:
            seed = random.randint(1, 9999999)
            logger.info(f"Using random seed: {seed}")

        # Добавляем случайный параметр к промпту, если кэширование отключено или явно запрошена рандомизация
        # Это гарантирует, что даже при одинаковых промптах будут генерироваться разные изображения
        if (not use_cache or randomize_seed) and not has_unique_suffix:
            # Добавляем текущее время и случайное число для гарантии уникальности
            import time
            timestamp = int(time.time())
            random_num = random.randint(1000, 9999)

            # Для более надежной рандомизации, добавляем случайные слова и модификаторы к промпту
            # Это поможет обойти кэширование на стороне провайдера
            style_modifiers = [
                "vibrant", "muted", "bright", "dark", "colorful", "monochrome",
                "pastel", "neon", "vintage", "modern", "abstract", "realistic"
            ]

            angle_modifiers = [
                "front view", "side view", "top view", "perspective view",
                "close-up", "wide angle", "detailed", "simple"
            ]

            color_modifiers = [
                "red", "blue", "green", "yellow", "purple", "orange",
                "teal", "pink", "gold", "silver", "bronze", "copper"
            ]

            lighting_modifiers = [
                "soft lighting", "dramatic lighting", "natural light", "studio light",
                "backlit", "rim light", "ambient light", "high contrast"
            ]

            # Выбираем случайные модификаторы - используем больше модификаторов для большей вариативности
            style = style_modifiers[random.randint(0, len(style_modifiers)-1)]
            angle = angle_modifiers[random.randint(0, len(angle_modifiers)-1)]
            color = color_modifiers[random.randint(0, len(color_modifiers)-1)]
            lighting = lighting_modifiers[random.randint(0, len(lighting_modifiers)-1)]

            # Добавляем модификаторы и технические параметры для уникальности
            # Используем больше параметров и более сложную структуру для гарантии уникальности
            random_suffix = f", hint of {color}, {style}, {angle}, {lighting} [seed:{seed}:time:{timestamp}:rand:{random_num}:unique:{random.randint(10000, 99999)}]"
            prompt = f"{prompt}{random_suffix}"
            logger.info(f"Cache disabled or randomization requested, using randomized prompt with modifiers: {random_suffix}")

        logger.info(f"Генерация изображения с использованием G4F: {prompt[:100]}...")

        # Прямой способ (самый надежный)
        try:
            logger.info(f"Пробуем прямой способ генерации изображения через Blackbox")
            from g4f.Provider import Blackbox

            # Формируем сообщения для API
            messages = [{"role": "user", "content": prompt}]

            try:
                # Явно указываем модель flux
                url = await Blackbox.create_async(
                    messages=messages,
                    model="flux",  # Принудительно используем flux для изображений
                    width=width,
                    height=height,
                    timeout=self._timeout
                )

                if url:
                    logger.info(f"Успешно сгенерировано изображение через Blackbox/flux: {url[:100]}")
                    return self._validate_and_return_url(url)
            except Exception as e:
                logger.warning(f"Ошибка прямой генерации через Blackbox: {e}")
        except ImportError as e:
            logger.warning(f"Не удалось импортировать Blackbox: {e}")

        # Запасной метод - прямой вызов других провайдеров
        try:
            logger.info(f"Пробуем ImageLabs")
            from g4f.Provider import ImageLabs

            # Формируем сообщения для API
            messages = [{"role": "user", "content": prompt}]

            try:
                url = await ImageLabs.create_async(
                    messages=messages,
                    model="sdxl-turbo",
                    width=width,
                    height=height,
                    timeout=self._timeout
                )

                if url:
                    logger.info(f"Успешно сгенерировано изображение через ImageLabs: {url[:100]}")
                    return self._validate_and_return_url(url)
            except Exception as e:
                logger.warning(f"Ошибка прямой генерации через ImageLabs: {e}")
        except ImportError as e:
            logger.warning(f"Не удалось импортировать ImageLabs: {e}")

        # Запасной метод - PollinationsAI
        try:
            logger.info(f"Пробуем PollinationsAI")
            from g4f.Provider import PollinationsAI

            # Формируем сообщения для API
            messages = [{"role": "user", "content": prompt}]

            try:
                url = await PollinationsAI.create_async(
                    messages=messages,
                    model="sdxl-turbo",  # Пробуем более надежную модель
                    width=width,
                    height=height,
                    timeout=self._timeout
                )

                if url:
                    logger.info(f"Успешно сгенерировано изображение через PollinationsAI: {url[:100]}")
                    return self._validate_and_return_url(url)
            except Exception as e:
                logger.warning(f"Ошибка прямой генерации через PollinationsAI: {e}")
        except ImportError as e:
            logger.warning(f"Не удалось импортировать PollinationsAI: {e}")

        # Если не удалось сгенерировать изображение, возвращаем запасной URL
        logger.warning("Не удалось сгенерировать изображение через G4F")
        return self._get_fallback_image_url(prompt)

    def _validate_and_return_url(self, url):
        """Проверяет и возвращает валидный URL изображения"""
        if not url or not isinstance(url, str):
            logger.warning(f"Получен невалидный URL: {url}")
            return None

        # Проверяем сначала на Markdown разметку
        if '![' in url or '](https://' in url:
            # Пробуем извлечь URL из Markdown разметки ![alt](url)
            try:
                # Регулярное выражение для извлечения URL из Markdown разметки ![alt](url)
                md_pattern = r'\]\((https?://[^\s)]+)\)'
                md_matches = re.findall(md_pattern, url)
                if md_matches:
                    url = md_matches[0]
                    logger.info(f"Извлечен URL из Markdown разметки: {url[:100]}")
            except Exception as e:
                logger.warning(f"Ошибка извлечения URL из Markdown: {e}")

        # Проверяем на HTML-разметку
        if '<img' in url or 'src=' in url:
            # Пробуем извлечь URL из HTML <img src="url">
            try:
                # Регулярное выражение для извлечения URL из HTML src="url"
                html_pattern = r'src=[\'"]([^\'"]+)[\'"]'
                html_matches = re.findall(html_pattern, url)
                if html_matches:
                    url = html_matches[0]
                    logger.info(f"Извлечен URL из HTML разметки: {url[:100]}")
            except Exception as e:
                logger.warning(f"Ошибка извлечения URL из HTML: {e}")

        # Если в строке несколько URL, берем первый
        if url.count('http') > 1:
            try:
                # Регулярное выражение для извлечения всех URL из строки
                url_pattern = r'(https?://[^\s)"\'>]+)'
                url_matches = re.findall(url_pattern, url)
                if url_matches:
                    url = url_matches[0]
                    logger.info(f"Извлечен первый URL из строки: {url[:100]}")
            except Exception as e:
                logger.warning(f"Ошибка извлечения URL из строки: {e}")

        # Отслеживаем проблемные домены для аналитики, но не заменяем их
        if "pornlabs" in url:
            logger.warning(f"Обнаружен проблемный домен в URL: {url[:100]}")
            # Мы больше не заменяем домен, а просто возвращаем оригинальный URL
            # Это позволит использовать оригинальный URL, который точно работает

        return url

    def _get_fallback_image_url(self, prompt):
        """Получение запасного URL для изображения"""
        # Пробуем получить изображение из запасного источника
        try:
            # Запасной URL для изображений
            fallback_url = "https://picsum.photos/640/480"

            # Проверяем доступность запасного URL
            response = requests.head(fallback_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Используем запасной источник изображений: {fallback_url}")
                return fallback_url
            else:
                logger.warning(f"Запасной URL недоступен, статус: {response.status_code}")
        except Exception as e:
            logger.warning(f"Ошибка при проверке запасного URL: {e}")

        # Если даже запасной URL не работает, используем гарантированно работающий URL
        backup_url = "https://placehold.co/640x480/gray/white?text=Image+Not+Available"
        logger.info(f"Используем гарантированный запасной URL: {backup_url}")
        return backup_url

    # Для обратной совместимости оставляем старый метод
    async def generate(self, prompt: str) -> str:
        """Генерация текста (оставлен для обратной совместимости)"""
        return await self.generate_content(prompt)

    def set_timeout(self, timeout: int):
        """Установка таймаута для запросов"""
        self._timeout = max(30, timeout)  # Минимум 30 секунд
        logger.info(f"G4FHandler timeout set to {self._timeout} seconds")

        # Также устанавливаем таймаут для Mistral handler, если он инициализирован
        if self.mistral_handler:
            self.mistral_handler.set_timeout(self._timeout)

    def generate_chat_completion(self, messages, model=None, temperature=0.7, max_tokens=None, timeout=None):
        """
        Основной метод генерации ответа на основе диалога
        """
        start_time = time.time()
        logger.info(f"Начинаем генерацию с помощью Mistral API")
        logger.debug(f"Сообщения: {messages}")

        # Проверяем параметры
        if not max_tokens:
            max_tokens = 2048  # Значение по умолчанию

        if not timeout:
            timeout = self._timeout  # Используем значение таймаута по умолчанию

        # Используем Mistral API через наш новый обработчик
        if self.mistral_handler and self.mistral_handler.is_available():
            try:
                logger.info(f"Используем Mistral API с моделью {self.mistral_model}")

                # Получаем текст последнего сообщения пользователя
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get("role") == "user" and msg.get("content"):
                        last_user_message = msg["content"]
                        break

                if not last_user_message:
                    logger.warning("Не найдено сообщение пользователя в диалоге")
                    return {"content": "Извините, не могу обработать запрос без сообщения пользователя."}

                # Определяем язык запроса
                detected_language = detect_language(last_user_message)
                logger.info(f"Определен язык запроса: {detected_language}")

                # Добавляем инструкцию о языке ответа в промпт
                language_instructions = {
                    'ru': "Пожалуйста, ответь на русском языке.",
                    'zh': "请用中文回答。",
                    'es': "Por favor, responde en español.",
                    'fr': "Veuillez répondre en français.",
                    'de': "Bitte antworte auf Deutsch.",
                }

                # Если язык определен и не английский, добавляем инструкцию
                if detected_language != 'en' and detected_language in language_instructions:
                    enhanced_prompt = f"{last_user_message}\n\n{language_instructions[detected_language]}"
                    logger.info(f"Добавлена инструкция о языке ответа: {detected_language}")
                else:
                    enhanced_prompt = last_user_message

                # Отправляем запрос в Mistral API через наш обработчик
                response_text = self.mistral_handler.generate_content_sync(
                    prompt=enhanced_prompt,
                    model=self.mistral_model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                logger.info(f"Получен ответ от Mistral API, длина: {len(response_text)}")

                # Время выполнения
                execution_time = time.time() - start_time
                logger.info(f"Время выполнения запроса: {execution_time:.2f} сек")

                # Формируем ответ в формате, совместимом с интерфейсом
                return {
                    "content": response_text,
                    "model": self.mistral_model,
                    "provider": "MistralAPI"
                }

            except Exception as e:
                logger.error(f"Ошибка при использовании Mistral API: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.error("Mistral API клиент не инициализирован")
            return {"content": "Mistral API недоступен. Пожалуйста, проверьте настройки API ключа."}

    def _get_model_and_provider(self, model=None) -> Tuple[Optional[str], Optional[Any]]:
        """
        Возвращает модель и провайдер для использования в G4F.
        Если указана модель, пытается найти подходящего провайдера для неё.
        В противном случае возвращает текущую модель и провайдер или настраивает их заново.

        Args:
            model: Опциональное название модели

        Returns:
            Tuple[str, Any]: Модель и провайдер для G4F
        """
        if model:
            # Если модель указана, пытаемся найти подходящего провайдера
            try:
                # Список провайдеров для проверки
                # Оставляем только рабочие провайдеры
                providers_to_check = [
                    g4f.Provider.You,
                    g4f.Provider.Liaobots
                ]

                # Фильтруем только работающие провайдеры
                working_providers = [p for p in providers_to_check if hasattr(p, 'working') and p.working]

                if working_providers:
                    # Используем первый работающий провайдер
                    selected_provider = working_providers[0]
                    logger.info(f"Для модели {model} выбран провайдер {selected_provider.__name__}")
                    return model, selected_provider
                else:
                    logger.warning(f"Не найдено работающих провайдеров для модели {model}")
                    return None, None
            except Exception as e:
                logger.error(f"Ошибка при поиске провайдера для модели {model}: {e}")
                return None, None

        # Если модель не указана или не удалось найти провайдера, используем текущую конфигурацию
        if self._current_model and self._model_provider:
            return self._current_model, self._model_provider

        # Если текущая конфигурация не определена, пытаемся настроить
        return self._setup_fixed_model()