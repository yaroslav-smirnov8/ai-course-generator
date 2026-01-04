"""
Модуль для работы с Google Gemini API
Использует официальную библиотеку: https://github.com/google/generative-ai-python
С опциональной поддержкой проксирования через Cloudflare для стабильности
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
import httpx
import json
from urllib.parse import urlparse
import ssl
import random
import asyncio
import time
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Настройки переключения и управления ключами
USE_RATE_LIMITER = os.getenv("USE_RATE_LIMITER", "true").lower() == "true"
ENABLE_BASE_KEY_FALLBACK = os.getenv("ENABLE_BASE_KEY_FALLBACK", "true").lower() == "true"
MAX_BASE_KEY_FALLBACK_ATTEMPTS = int(os.getenv("MAX_BASE_KEY_FALLBACK_ATTEMPTS", "3"))

# Константы для кеширования
GEMINI_CACHE_ENABLED = os.getenv("GEMINI_CACHE_ENABLED", "true").lower() == "true"

# Настройки для автоматического переключения на SOCKS5 для больших запросов
AUTO_SWITCH_TO_SOCKS5 = os.environ.get("AUTO_SWITCH_TO_SOCKS5", "true").lower() == "true"
MAX_CLOUDFLARE_PROMPT_LENGTH = int(os.environ.get("MAX_CLOUDFLARE_PROMPT_LENGTH", "5000"))
BYPASS_CLOUDFLARE_SIZE_CHECK = os.environ.get("BYPASS_CLOUDFLARE_SIZE_CHECK", "false").lower() == "true"

# Настройки для прямого подключения
ALLOW_DIRECT_CONNECTION = os.environ.get("ALLOW_DIRECT_CONNECTION", "false").lower() == "true"

# Настройки авторизации для Cloudflare Worker
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")

# Импортируем менеджер лимитов API, если он доступен
RATE_LIMITER_AVAILABLE = False
try:
    from .gemini_rate_limiter import gemini_limiter
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    logger.warning("Не удалось импортировать gemini_rate_limiter. Управление лимитами API недоступно.")

# Настройки прокси
CLOUDFLARE_PROXY_ENABLED = os.getenv("USE_CLOUDFLARE_PROXY", "false").lower() == "true"
CLOUDFLARE_PROXY_URL = os.getenv("CLOUDFLARE_PROXY_URL", "https://api.yourservice.com/gemini")

# Прямое подключение к Cloudflare Workers (без промежуточного прокси)
USE_DIRECT_WORKERS = os.getenv("USE_DIRECT_WORKERS", "true").lower() == "true"

# Прямые URL Cloudflare Workers
CLOUDFLARE_WORKERS_DIRECT = {
    'lesson-plan': 'https://lesson-plan.syysyy33.workers.dev',
    'course-lesson-plan': 'https://course-lesson-plan.syysyy33.workers.dev',
    'course-exercises': 'https://course-exercises.syysyy33.workers.dev',
    'course-games': 'https://course-games.syysyy33.workers.dev',
    'exercises': 'https://exercises.syysyy33.workers.dev',
    'games': 'https://games.syysyy33.workers.dev',
    'course-generator': 'https://course-generator.syysyy33.workers.dev',
    'assistant': 'https://assistant.syysyy33.workers.dev',
    'concept-explainer': 'https://concept-explainer.syysyy33.workers.dev',
    'text-analyzer': 'https://text-analyzer.syysyy33.workers.dev',
    'flux-images': 'https://flux-images.syysyy33.workers.dev',
    'bot-lesson-plan': 'https://bot-lesson-plan.syysyy33.workers.dev',
    'bot-images': 'https://bot-images.syysyy33.workers.dev',
    'bot-moderation': 'https://bot-moderation.syysyy33.workers.dev'
}

SOCKS5_PROXY_ENABLED = os.getenv("USE_SOCKS5_PROXY", "false").lower() == "true"
SOCKS5_PROXY_HOST = os.getenv("SOCKS5_PROXY_HOST", "127.0.0.1")
SOCKS5_PROXY_PORT = int(os.getenv("SOCKS5_PROXY_PORT", "1080"))
SOCKS5_PROXY_USER = os.getenv("SOCKS5_PROXY_USER", "")
SOCKS5_PROXY_PASS = os.getenv("SOCKS5_PROXY_PASS", "")

# Настройки SSL/TLS
DISABLE_SSL_VERIFICATION = os.getenv("DISABLE_SSL_VERIFICATION", "false").lower() == "true"
DISABLE_HTTP2 = os.getenv("DISABLE_HTTP2", "false").lower() == "true"

# Проверяем доступность SOCKS5
SOCKS5_AVAILABLE = False
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    # Проверяем доступность SOCKS5 прокси
    s.connect((os.environ.get("SOCKS5_PROXY_HOST", "127.0.0.1"),
               int(os.environ.get("SOCKS5_PROXY_PORT", "1080"))))
    s.close()
    SOCKS5_AVAILABLE = True
    logger.info("SOCKS5 прокси доступен и будет использоваться для больших запросов")
except Exception as e:
    logger.warning(f"SOCKS5 прокси недоступен: {str(e)}")
    SOCKS5_AVAILABLE = False

# Исключения для обработки ошибок
class GeminiAPIException(Exception):
    """Базовое исключение для API Gemini"""
    pass

class GeminiConnectionException(GeminiAPIException):
    """Исключение при проблемах с подключением к API"""
    pass

class GeminiAuthException(GeminiAPIException):
    """Исключение при проблемах с авторизацией"""
    pass

class GeminiRateLimitException(GeminiAPIException):
    """Исключение при превышении лимита запросов"""
    pass

class GeminiHandler:
    """Класс для работы с Google Gemini API"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60,
                 use_cloudflare: Optional[bool] = None, use_socks5: Optional[bool] = None,
                 use_rate_limiter: bool = True, component_id: Optional[str] = None,
                 use_proxy: Optional[bool] = None):
        """
        Инициализация обработчика Gemini API.

        Args:
            api_key: Ключ API для доступа к Google Gemini.
            timeout: Таймаут запросов (в секундах).
            use_cloudflare: Использовать ли Cloudflare Worker для запросов.
            use_socks5: Использовать ли SOCKS5 прокси для запросов.
            use_rate_limiter: Использовать ли ограничитель скорости для API ключей.
            component_id: Идентификатор компонента (для использования компонентных URL).
            use_proxy: Использовать ли прямое подключение к Cloudflare Workers.
        """
        # Инициализация базовых переменных
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.timeout = timeout
        self.gemini_client = None
        self.available_models = []
        self.default_model = "gemini-2.0-flash"  # Модель по умолчанию
        self.component_id = component_id
        self.use_rate_limiter = use_rate_limiter and RATE_LIMITER_AVAILABLE

        # Определяем, использовать ли прямое подключение к Workers
        if use_proxy is None:
            self.use_direct_workers = USE_DIRECT_WORKERS
        else:
            self.use_direct_workers = use_proxy

        # Определяем, использовать ли Cloudflare прокси
        if use_cloudflare is None:
            self.use_cloudflare = CLOUDFLARE_PROXY_ENABLED
        else:
            self.use_cloudflare = use_cloudflare

        # Определяем, использовать ли SOCKS5 прокси
        if use_socks5 is None:
            self.use_socks5 = SOCKS5_AVAILABLE
        else:
            self.use_socks5 = use_socks5 and SOCKS5_AVAILABLE

        # Запрещаем автоматическое переключение на SOCKS5, если установлен флаг BYPASS_CLOUDFLARE_SIZE_CHECK
        if BYPASS_CLOUDFLARE_SIZE_CHECK:
            logger.info("BYPASS_CLOUDFLARE_SIZE_CHECK=true, отключаем автоматическое переключение на SOCKS5")
            self.bypass_size_check = True
        else:
            self.bypass_size_check = False

        # URL для Cloudflare Worker
        self.cloudflare_url = os.environ.get("CLOUDFLARE_PROXY_URL", "https://aiteachers.netlify.app/api")

        # Флаги для безопасного соединения
        self.disable_ssl_verification = DISABLE_SSL_VERIFICATION
        self.disable_http2 = DISABLE_HTTP2

        # Настройка фолбэка на базовый ключ
        self.enable_base_key_fallback = True
        self.max_base_key_fallback_attempts = 1
        self.is_using_component_key = bool(component_id)

        # Настройка кеширования
        self.cache_enabled = GEMINI_CACHE_ENABLED

        # Подробное логирование
        logger.info(f"Инициализация GeminiHandler (api_key доступен: {'Да' if self.api_key else 'Нет'}, "
                   f"Direct Workers: {'Включен' if self.use_direct_workers else 'Выключен'}, "
                   f"Cloudflare: {'Включен' if self.use_cloudflare else 'Выключен'}, "
                   f"SOCKS5: {'Включен' if self.use_socks5 else 'Выключен'}, "
                   f"Rate Limiter: {'Включен' if self.use_rate_limiter else 'Выключен'}, "
                   f"Компонент: {self.component_id or 'не указан'}, "
                   f"Использует {'компонентный' if self.is_using_component_key else 'базовый'} ключ")

        # Инициализируем клиент
        self._init_client()

    def _get_base_api_key(self) -> str:
        """
        Возвращает базовый API ключ из переменной окружения

        Returns:
            Базовый API ключ
        """
        return os.getenv("GEMINI_API_KEY", "")

    def _get_component_api_key(self, component_id: str) -> Optional[str]:
        """
        Получает специальный API ключ для указанного компонента

        Args:
            component_id: Идентификатор компонента

        Returns:
            Ключ API для компонента или None, если ключ не найден
        """
        # Пробуем найти ключ в формате GEMINI_API_KEY_{COMPONENT_ID}
        env_var_name = f"GEMINI_API_KEY_{component_id.upper().replace('-', '_')}"
        component_key = os.getenv(env_var_name)

        if component_key:
            logger.info(f"Найден специальный API ключ для компонента {component_id}")
            return component_key
        else:
            # Если ключ не найден, используем общий ключ
            logger.info(f"Специальный API ключ для компонента {component_id} не найден, "
                      f"используем общий ключ GEMINI_API_KEY")
            return self._get_base_api_key()

    def _get_proxy_url(self) -> Optional[str]:
        """Формирует URL для SOCKS5 прокси"""
        if not self.use_socks5:
            return None

        # Формируем URL с учетом аутентификации, если она указана
        if self.socks5_user and self.socks5_pass:
            return f"socks5://{self.socks5_user}:{self.socks5_pass}@{self.socks5_host}:{self.socks5_port}"
        else:
            return f"socks5://{self.socks5_host}:{self.socks5_port}"

    def _get_cloudflare_url(self) -> str:
        """
        Формирует URL для Cloudflare Worker с учетом компонента
        """
        if not self.cloudflare_url:
            return None

        base_url = self.cloudflare_url.rstrip('/')

        # Если указан компонент, формируем компонентный URL
        if self.component_id:
            return f"{base_url}/component/{self.component_id}"

        return base_url

    def _init_client(self):
        """Инициализация клиента Google Gemini API"""
        if not GEMINI_AVAILABLE and not (self.use_cloudflare or self.use_socks5):
            logger.error("Библиотека google.generativeai не установлена и ни один из прокси не используется")
            return

        if not self.api_key:
            logger.warning("API ключ Google Gemini не указан, клиент не будет инициализирован")
            return

        # Проверка настроек Cloudflare
        if self.use_cloudflare and (not self.cloudflare_url or self.cloudflare_url == 'https://api.yourservice.com/gemini'):
            # Устанавливаем URL по умолчанию для Netlify
            self.cloudflare_url = 'https://aiteachers.netlify.app/api'
            logger.info(f"URL Cloudflare не указан, используем URL по умолчанию: {self.cloudflare_url}")

        try:
            # При использовании Cloudflare или SOCKS5 нам не нужен официальный клиент для прямого доступа
            if not (self.use_cloudflare or self.use_socks5):
                # Конфигурация API
                genai.configure(api_key=self.api_key)
                self.gemini_client = genai
                logger.info("Google Gemini API клиент успешно инициализирован")

                # Получаем список доступных моделей
                self._fetch_available_models()
            else:
                logger.info(f"Используется {'Cloudflare' if self.use_cloudflare else 'SOCKS5'} для проксирования запросов к Google Gemini API")
                # Для прокси нам не нужно инициализировать клиент Google API

                # Если используем Cloudflare, проверяем его доступность
                if self.use_cloudflare:
                    import asyncio
                    try:
                        # Создаем новый event loop для асинхронной проверки
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._check_cloudflare_availability())
                    except Exception as e:
                        logger.warning(f"Не удалось проверить доступность Cloudflare прокси: {e}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации Google Gemini API клиента: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.gemini_client = None
            raise GeminiConnectionException(f"Не удалось подключиться к Google Gemini API: {e}")

    async def _check_cloudflare_availability(self):
        """Проверка доступности Cloudflare прокси"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Отправляем простой запрос для проверки доступности
                response = await client.get(
                    f"{self.cloudflare_url}/models",
                    headers={
                        "X-Gemini-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code == 200:
                    logger.info("Cloudflare прокси доступен")
                    # Сохраняем список моделей, если он есть в ответе
                    try:
                        models_data = response.json().get("models", [])
                        if models_data:
                            logger.info(f"Получено {len(models_data)} моделей через Cloudflare прокси")
                    except Exception as e:
                        logger.warning(f"Не удалось разобрать ответ с моделями: {e}")
                else:
                    logger.warning(f"Cloudflare прокси вернул код {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при проверке доступности Cloudflare прокси: {e}")

    def _fetch_available_models(self):
        """Получение списка доступных моделей"""
        if not self.gemini_client:
            return

        try:
            self.available_models = self.gemini_client.list_models()
            logger.info(f"Получено {len(self.available_models)} доступных моделей Google Gemini")

            # Выводим список моделей в лог для отладки
            model_names = [model.name for model in self.available_models]
            logger.info(f"Доступные модели: {', '.join(model_names[:5])}...")
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей Google Gemini: {e}")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        if self.use_cloudflare or self.use_socks5:
            # Если используем прокси, считаем API доступным если есть API ключ
            return bool(self.api_key)
        elif ALLOW_DIRECT_CONNECTION:
            # Если используем прямое подключение без библиотеки, тоже считаем доступным при наличии ключа
            return bool(self.api_key)
        else:
            # Иначе проверяем наличие клиента
            return self.gemini_client is not None and GEMINI_AVAILABLE

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        models_info = []

        # Если используем прокси, вернем базовый набор моделей
        if self.use_cloudflare or self.use_socks5:
            models_info = [
                {
                    "id": "gemini-2.0-flash",
                    "name": "gemini-2.0-flash",
                    "description": f"Gemini 2.0 Flash (через {'Cloudflare' if self.use_cloudflare else 'SOCKS5'})",
                    "max_tokens": 32768,
                    "capabilities": {
                        "chat": True,
                        "function_calling": True,
                        "vision": True
                    }
                },
                {
                    "id": "gemini-1.5-pro",
                    "name": "gemini-1.5-pro",
                    "description": f"Gemini 1.5 Pro (через {'Cloudflare' if self.use_cloudflare else 'SOCKS5'})",
                    "max_tokens": 32768,  # Примерное значение
                    "capabilities": {
                        "chat": True,
                        "function_calling": True,
                        "vision": True
                    }
                },
                {
                    "id": "gemini-1.5-flash",
                    "name": "gemini-1.5-flash",
                    "description": f"Gemini 1.5 Flash (через {'Cloudflare' if self.use_cloudflare else 'SOCKS5'})",
                    "max_tokens": 32768,
                    "capabilities": {
                        "chat": True,
                        "function_calling": True,
                        "vision": True
                    }
                }
            ]
            return models_info

        # Иначе используем стандартный метод получения моделей
        if not self.is_available():
            return models_info

        for model in self.available_models:
            models_info.append({
                "id": model.name,
                "name": model.name.split('/')[-1] if '/' in model.name else model.name,
                "description": getattr(model, "description", ""),
                "max_tokens": getattr(model, "input_token_limit", 0),
                "capabilities": {
                    "chat": True,
                    "function_calling": True,
                    "vision": "generateContent" in getattr(model, "supported_generation_methods", [])
                }
            })
        return models_info

    async def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        safety_settings: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Генерирует контент с использованием Google Gemini API.

        Args:
            prompt: Текст запроса для генерации.
            model: Используемая модель. По умолчанию используется модель по умолчанию.
            temperature: Температура генерации (0.0-1.0).
            max_tokens: Максимальное количество токенов в ответе.
            top_p: Top-p параметр (0.0-1.0).
            top_k: Top-k параметр.
            safety_settings: Настройки безопасности.
            stream: Включить потоковую генерацию.

        Returns:
            Сгенерированный текст.

        Raises:
            GeminiConnectionException: При проблемах с подключением.
            GeminiAuthException: При проблемах с аутентификацией.
            GeminiRateLimitException: При превышении лимита запросов.
            GeminiAPIException: При других ошибках API.
        """
        # Устанавливаем значения по умолчанию, если они не заданы
        if not model:
            model = self.default_model or "gemini-2.0-flash"

        temperature = temperature if temperature is not None else 0.7
        max_tokens = max_tokens if max_tokens is not None else 2048
        top_p = top_p if top_p is not None else 0.95
        top_k = top_k if top_k is not None else 40

        api_key_to_use = None
        model_to_use = model

        # Если включен rate limiter, получаем доступный ключ и модель
        if self.use_rate_limiter and RATE_LIMITER_AVAILABLE:
            try:
                api_key_to_use, model_to_use = gemini_limiter.get_available_key_and_model()
                logger.info(f"Модель выбрана rate limiter: {model_to_use}")
                logger.info(f"Используем API ключ из rate limiter: {api_key_to_use[:5]}...")
            except Exception as e:
                logger.error(f"Ошибка при получении ключа из rate limiter: {e}")
                # Если не удалось получить ключ из rate limiter, используем текущий ключ
                api_key_to_use = self.api_key
                model_to_use = model

        # Если не используем rate limiter или возникла ошибка, используем текущий ключ
        if not api_key_to_use:
            api_key_to_use = self.api_key
            model_to_use = model

        # Логирование информации о запросе
        logger.info(f"Генерация контента с использованием Google Gemini API через "
                  f"{'Cloudflare' if self.use_cloudflare else 'прямое соединение'}")
        logger.info(f"Модель: {model_to_use}")
        logger.info(f"Длина запроса: {len(prompt)} символов")
        logger.info(f"Параметры: temperature={temperature}, max_tokens={max_tokens}, top_p={top_p}, top_k={top_k}")

        try:
            # Генерируем контент с выбранным ключом
            result = await self._generate_content_with_key(
                prompt=prompt,
                model=model_to_use,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                safety_settings=safety_settings,
                stream=stream,
                request_api_key=api_key_to_use
            )

            # Записываем использование в rate limiter (если используется)
            if self.use_rate_limiter and RATE_LIMITER_AVAILABLE:
                gemini_limiter.record_usage(api_key_to_use, model_to_use)

            return result
        except GeminiAPIException as e:
            # Записываем ошибку в rate limiter (если используется)
            if self.use_rate_limiter and RATE_LIMITER_AVAILABLE:
                gemini_limiter.record_error(api_key_to_use, model_to_use, str(e))

            # Пробрасываем ошибку выше
            raise

    async def _generate_with_socks5(
        self,
        prompt: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int
    ) -> str:
        """Генерация контента с использованием SOCKS5 прокси"""

        logger.info("Генерация контента с использованием Google Gemini API через SOCKS5 прокси")
        logger.info(f"Модель: {self.default_model}")
        logger.info(f"Длина запроса: {len(prompt)} символов")
        logger.info(f"Параметры: temperature={temperature}, max_tokens={max_tokens}, top_p={top_p}, top_k={top_k}")

        # Формируем данные запроса
        request_data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": top_p,
                "topK": top_k
            }
        }

        # Настраиваем транспорт с SOCKS5 прокси
        socks5_host = os.environ.get("SOCKS5_PROXY_HOST", "127.0.0.1")
        socks5_port = int(os.environ.get("SOCKS5_PROXY_PORT", "1080"))
        proxy = f"socks5://{socks5_host}:{socks5_port}"

        transport = httpx.AsyncHTTPTransport(
            proxy=proxy,
            verify=False,  # Отключаем проверку SSL для стабильности
            http2=False    # Отключаем HTTP/2
        )

        # URL для запроса
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.default_model}:generateContent"

        try:
            # Отправляем запрос через SOCKS5 прокси с уменьшенным таймаутом
            async with httpx.AsyncClient(
                transport=transport,
                timeout=60.0,  # Устанавливаем таймаут в 60 секунд
                follow_redirects=True
            ) as client:
                # Добавляем API ключ как параметр запроса
                params = {"key": api_key}

                start_time = time.time()
                # Выполняем запрос
                response = await client.post(
                    url,
                    json=request_data,
                    params=params,
                    headers={"Content-Type": "application/json"}
                )
                request_time = time.time() - start_time

                logger.info(f"SOCKS5: Получен ответ, статус: {response.status_code}, время запроса: {request_time:.2f} сек")

                if response.status_code == 200:
                    result = response.json()

                    # Извлекаем текст из ответа
                    if "candidates" in result and result["candidates"]:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and "text" in parts[0]:
                                text = parts[0]["text"]
                                logger.info(f"SOCKS5: Успешно получен ответ ({len(text)} символов)")
                                return text

                    logger.error(f"SOCKS5: Неожиданная структура ответа: {json.dumps(result)[:200]}")
                    raise GeminiAPIException(f"Неожиданная структура ответа API")
                else:
                    error_text = response.text
                    logger.error(f"SOCKS5: Ошибка API {response.status_code}: {error_text[:200]}")
                    raise GeminiConnectionException(f"Ошибка API: {response.status_code}, {error_text[:200]}")

        except httpx.RequestError as e:
            logger.error(f"SOCKS5: Ошибка запроса: {str(e)}")
            raise GeminiConnectionException(f"Ошибка соединения: {str(e)}")
        except Exception as e:
            logger.error(f"SOCKS5: Неожиданная ошибка: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise GeminiConnectionException(f"Неожиданная ошибка: {str(e)}")

    async def _generate_with_cloudflare(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        safety_settings: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        request_api_key: Optional[str] = None
    ) -> str:
        """
        Генерация текста через Cloudflare Worker

        Args:
            prompt: Текст запроса для генерации
            model: Модель для генерации
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Top-p параметр (0.0-1.0)
            top_k: Top-k параметр
            safety_settings: Настройки безопасности
            stream: Включить потоковую генерацию
            request_api_key: API ключ для этого запроса

        Returns:
            str: Сгенерированный текст
        """
        # Получаем URL Cloudflare Worker
        request_url = self._get_cloudflare_url()

        # Используем переданный ключ API или ключ из настроек
        api_key = request_api_key or self.api_key

        # Формируем аргументы
        params = {}

        # Формируем заголовки
        headers = {
            "Content-Type": "application/json",
            "X-Gemini-API-Key": api_key
        }

        # Если настроен токен авторизации для Cloudflare Worker, добавляем его
        if API_AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {API_AUTH_TOKEN}"

        # Формируем данные запроса
        request_data = {
            "model": model,
            "apiKey": api_key,
            "prompt": prompt,
            "temperature": temperature,
            "maxTokens": max_tokens, # Используем переданное значение или дефолтное
            "topP": top_p,
            "topK": top_k
        }

        try:
            # Отправляем запрос с уменьшенным таймаутом
            timeout = httpx.Timeout(timeout=60.0, connect=30.0)
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True
            ) as client:
                response = await client.post(
                    request_url,
                    params=params,
                    headers=headers,
                    json=request_data
                )

                # Проверяем статус ответа
                if response.status_code == 200:
                    # Попытка обработать JSON
                    try:
                        result = response.json()
                    except json.JSONDecodeError:
                        # Если ответ не является JSON, анализируем текст на признаки ошибки
                        text_resp = response.text
                        if 'RESOURCE_EXHAUSTED' in text_resp or 'quota' in text_resp.lower():
                            raise GeminiRateLimitException(text_resp[:500])
                        return text_resp

                    # Если воркер вернул объект ошибки — пробрасываем её как исключение
                    if isinstance(result, dict) and 'error' in result:
                        err = result['error']
                        msg = err.get('message', str(err))
                        status = err.get('status', '')
                        if 'RESOURCE_EXHAUSTED' in status or 'quota' in msg.lower():
                            raise GeminiRateLimitException(msg)
                        raise GeminiAPIException(msg)

                    # Извлекаем текст из ответа стандартного формата Gemini API
                    if "candidates" in result and result["candidates"]:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and "text" in parts[0]:
                                return parts[0]["text"]

                    # Простой формат ответа от Worker
                    if "text" in result:
                        return result["text"]

                    # Прямой ответ без вложенности
                    if isinstance(result, str):
                        # Если это строка, проверим на признаки ошибки квоты
                        if 'RESOURCE_EXHAUSTED' in result or 'quota' in result.lower():
                            raise GeminiRateLimitException(result[:500])
                        return result

                    # В крайнем случае, пытаемся сериализовать, но предварительно проверяем на признаки ошибки
                    serial = json.dumps(result, ensure_ascii=False)
                    if 'RESOURCE_EXHAUSTED' in serial or 'quota' in serial.lower():
                        raise GeminiRateLimitException(serial[:500])
                    return serial

                elif response.status_code == 401:
                    logger.error(f"Ошибка аутентификации: {response.status_code}")
                    logger.error(f"Детали ошибки: {response.text[:500]}")
                    raise GeminiAuthException(f"Ошибка аутентификации: {response.text[:200]}")

                elif response.status_code == 429:
                    logger.error(f"Превышение лимита запросов: {response.status_code}")
                    raise GeminiRateLimitException(f"Превышение лимита запросов: {response.text}")

                else:
                    logger.error(f"Ошибка API: {response.status_code}")
                    logger.error(f"Детали ошибки: {response.text[:500]}")
                    raise GeminiConnectionException(f"Ошибка API: {response.status_code}, {response.text[:200]}")

        except httpx.ConnectError as e:
            logger.error(f"Ошибка соединения с API: {e}")
            raise GeminiConnectionException(f"Ошибка соединения: {e}")

        except httpx.TimeoutException as e:
            logger.error(f"Таймаут соединения: {e}")
            raise GeminiConnectionException(f"Таймаут соединения: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}")
            if response and response.status_code == 200:
                return response.text
            raise GeminiConnectionException(f"Ошибка декодирования JSON: {e}")

    async def _generate_with_direct_worker(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        safety_settings: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        request_api_key: Optional[str] = None
    ) -> str:
        """
        Генерация текста через прямое подключение к Cloudflare Worker

        Args:
            prompt: Текст запроса для генерации
            model: Модель для генерации
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Top-p параметр (0.0-1.0)
            top_k: Top-k параметр
            safety_settings: Настройки безопасности
            stream: Включить потоковую генерацию
            request_api_key: API ключ для этого запроса

        Returns:
            str: Сгенерированный текст
        """
        # Определяем воркер для компонента
        component_name = self.component_id or 'lesson-plan'
        
        # Получаем прямой URL воркера
        worker_url = CLOUDFLARE_WORKERS_DIRECT.get(component_name)
        if not worker_url:
            raise GeminiConnectionException(f"Воркер для компонента {component_name} не найден")
        
        # Формируем полный URL с эндпоинтом
        url = f"{worker_url}/generateContent"
        
        # Используем переданный ключ API или ключ из настроек
        api_key = request_api_key or self.api_key
        
        logger.info(f"Генерация контента через прямое подключение к Cloudflare Worker")
        logger.info(f"Компонент: {component_name}")
        logger.info(f"URL: {url}")
        logger.info(f"Модель: {model}")
        logger.info(f"Длина запроса: {len(prompt)} символов")

        # Формируем заголовки
        headers = {
            "Content-Type": "application/json"
        }

        # Добавляем API ключи в заголовки (аналогично боту)
        if api_key:
            headers["X-Gemini-API-Key"] = api_key

        # Формируем данные запроса в правильном формате Gemini API
        request_data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": top_p,
                "topK": top_k
            }
        }

        try:
            # Отправляем запрос с таймаутом
            timeout = httpx.Timeout(timeout=300.0, connect=30.0)  # Увеличенный таймаут для генерации курсов
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True
            ) as client:
                start_time = time.time()
                response = await client.post(
                    url,
                    headers=headers,
                    json=request_data
                )
                request_time = time.time() - start_time

                logger.info(f"Worker: Получен ответ, статус: {response.status_code}, время запроса: {request_time:.2f} сек")

                # Проверяем статус ответа
                if response.status_code == 200:
                    try:
                        result = response.json()
                        
                        # Если воркер вернул объект ошибки — пробрасываем её как исключение
                        if isinstance(result, dict) and 'error' in result:
                            err = result['error']
                            msg = err.get('message', str(err))
                            status = err.get('status', '')
                            if 'RESOURCE_EXHAUSTED' in status or 'quota' in msg.lower():
                                raise GeminiRateLimitException(msg)
                            raise GeminiAPIException(msg)
                        
                        # Парсим ответ в формате Gemini API
                        if "candidates" in result and result["candidates"]:
                            candidate = result["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                parts = candidate["content"]["parts"]
                                if parts and "text" in parts[0]:
                                    generated_text = parts[0]["text"]
                                    logger.info(f"Worker: Успешно получен ответ от Gemini API ({len(generated_text)} символов)")
                                    return generated_text
                        
                        # Извлекаем текст из ответа (альтернативные форматы)
                        elif result.get('success') and result.get('text'):
                            generated_text = result['text']
                            logger.info(f"Worker: Успешно получен ответ ({len(generated_text)} символов)")
                            return generated_text
                        elif 'text' in result:
                            generated_text = result['text']
                            logger.info(f"Worker: Успешно получен ответ ({len(generated_text)} символов)")
                            return generated_text
                        else:
                            logger.warning(f"Worker: Неожиданная структура ответа, анализируем на признаки ошибки")
                            serial = json.dumps(result, ensure_ascii=False)
                            if 'RESOURCE_EXHAUSTED' in serial or 'quota' in serial.lower():
                                raise GeminiRateLimitException(serial[:500])
                            logger.debug(f"Worker: Полный ответ: {serial[:1000]}")
                            return serial

                    except json.JSONDecodeError:
                        generated_text = response.text
                        # Проверяем текст на признаки ошибки квоты
                        if 'RESOURCE_EXHAUSTED' in generated_text or 'quota' in generated_text.lower():
                            raise GeminiRateLimitException(generated_text[:500])
                        logger.info(f"Worker: Получен текстовый ответ ({len(generated_text)} символов)")
                        return generated_text

                elif response.status_code == 401:
                    logger.error(f"Worker: Ошибка аутентификации: {response.status_code}")
                    raise GeminiAuthException(f"Ошибка аутентификации: {response.text[:200]}")

                elif response.status_code == 429:
                    logger.error(f"Worker: Превышение лимита запросов: {response.status_code}")
                    raise GeminiRateLimitException(f"Превышение лимита запросов: {response.text}")

                else:
                    logger.error(f"Worker: Ошибка API: {response.status_code}")
                    logger.error(f"Worker: Детали ошибки: {response.text[:500]}")
                    raise GeminiConnectionException(f"Ошибка API: {response.status_code}, {response.text[:200]}")

        except httpx.ConnectError as e:
            logger.error(f"Worker: Ошибка соединения: {e}")
            raise GeminiConnectionException(f"Ошибка соединения с Worker: {e}")

        except httpx.TimeoutException as e:
            logger.error(f"Worker: Таймаут соединения: {e}")
            raise GeminiConnectionException(f"Таймаут соединения с Worker: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Worker: Ошибка декодирования JSON: {e}")
            if response and response.status_code == 200:
                return response.text
            raise GeminiConnectionException(f"Ошибка декодирования JSON от Worker: {e}")

    async def _generate_async(self, model, prompt, stream=False):
        """
        Асинхронная генерация контента.

        Args:
            model: Модель Gemini.
            prompt: Текст запроса.
            stream: Включить потоковую генерацию.

        Returns:
            Ответ модели.
        """
        if stream:
            # Для потоковой генерации
            response = await model.generate_content_async(
                prompt,
                stream=True
            )

            # Собираем весь сгенерированный текст
            chunks = []
            async for chunk in response:
                if chunk.text:
                    chunks.append(chunk.text)

            # TODO: Реализовать корректный возврат для потоковой генерации
            # Сейчас просто возвращаем объединенный текст
            return type('GenerativeResponse', (), {'text': ''.join(chunks)})
        else:
            # Для обычной генерации
            response = await model.generate_content_async(prompt)
            return response

    def generate_content_sync(self,
                           prompt: str,
                           model: Optional[str] = None,
                           temperature: float = 0.7,
                           max_tokens: Optional[int] = None) -> str:
        """
        Синхронная генерация текста с помощью Google Gemini API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется модель по умолчанию)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Сгенерированный текст
        """
        if not self.is_available():
            raise GeminiConnectionException("Клиент Google Gemini не инициализирован")

        # Если используем прокси, то вызываем асинхронный метод в синхронном контексте
        # Это не оптимально, но работает для совместимости
        if self.use_cloudflare or self.use_socks5:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Если нет активного event loop, создаем новый
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self.generate_content(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            ))

        # Используем указанную модель или модель по умолчанию
        model_name = model or self.default_model
        logger.info(f"Генерация контента с помощью модели Google Gemini: {model_name}")

        try:
            # Настраиваем параметры генерации (синхронизировано с ботом)
            # Используем max_tokens если передан, иначе дефолтное значение
            max_output_tokens = max_tokens if max_tokens else 15000  # По умолчанию как для планов уроков в боте

            generation_config = {
                "temperature": temperature,
                # Устанавливаем максимальное количество токенов как в боте
                "max_output_tokens": max_output_tokens, # Динамически как в боте
                "top_p": 0.95,
                "top_k": 64  # Увеличено с 40 до 64 как в боте
            }

            # Настройка безопасных фильтров (менее строгие)
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            # Получаем модель
            model = self.gemini_client.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            # Создаем запрос и генерируем ответ
            response = model.generate_content(prompt)

            # Проверяем, есть ли ответ
            if not response or not response.text:
                logger.warning("Google Gemini вернул пустой ответ")
                return "Извините, не удалось сгенерировать ответ. Пожалуйста, попробуйте позже."

            # Извлекаем и возвращаем текст
            logger.info(f"Успешно получен ответ от Google Gemini, длина: {len(response.text)}")
            return response.text

        except Exception as e:
            error_message = str(e)

            # Обрабатываем возможные типы ошибок
            if "API key not valid" in error_message or "authentication" in error_message.lower():
                logger.error(f"Ошибка аутентификации в Google Gemini API: {e}")
                raise GeminiAuthException(f"Недействительный API ключ: {e}")

            elif "quota" in error_message.lower() or "rate limit" in error_message.lower():
                logger.error(f"Превышен лимит запросов к Google Gemini API: {e}")
                raise GeminiRateLimitException(f"Превышен лимит запросов: {e}")

            else:
                logger.error(f"Непредвиденная ошибка при использовании Google Gemini API: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise GeminiAPIException(f"Непредвиденная ошибка: {e}")

    async def _generate_content_with_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        safety_settings: Optional[Dict[str, Any]],
        stream: bool,
        request_api_key: str
    ) -> str:
        """
        Внутренний метод для генерации контента с использованием определенного API ключа

        Args:
            prompt: Текст запроса для генерации.
            model: Используемая модель.
            temperature: Температура генерации (0.0-1.0).
            max_tokens: Максимальное количество токенов в ответе.
            top_p: Top-p параметр (0.0-1.0).
            top_k: Top-k параметр.
            safety_settings: Настройки безопасности.
            stream: Включить потоковую генерацию.
            request_api_key: Ключ API для запроса.

        Returns:
            Сгенерированный текст.
        """
        # Логирование информации об используемом ключе
        logger.info(f"Используем API ключ {request_api_key[:5]}...")

        try:
            # Приоритет 1: Прямое подключение к Cloudflare Workers (если включено)
            if self.use_direct_workers:
                result = await self._generate_with_direct_worker(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    safety_settings=safety_settings,
                    stream=stream,
                    request_api_key=request_api_key
                )
            # Приоритет 2: Проверяем, нужно ли переключиться на SOCKS5 из-за размера запроса
            elif (self.use_cloudflare and AUTO_SWITCH_TO_SOCKS5 and
                not self.bypass_size_check and
                len(prompt) > MAX_CLOUDFLARE_PROMPT_LENGTH and
                SOCKS5_AVAILABLE):
                logger.info(f"Запрос слишком большой для Cloudflare ({len(prompt)} символов > {MAX_CLOUDFLARE_PROMPT_LENGTH}). "
                          f"Переключаемся на прямое подключение через SOCKS5.")
                result = await self._generate_with_socks5(
                    prompt=prompt,
                    api_key=request_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    top_k=top_k
                )
            # Приоритет 3: Cloudflare прокси
            elif self.use_cloudflare:
                result = await self._generate_with_cloudflare(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    top_k=top_k,
                    safety_settings=safety_settings,
                    stream=stream,
                    request_api_key=request_api_key
                )
            # Приоритет 4: Прямой запрос к Google Gemini API
            else:
                result = await self._generate_direct(
                    prompt=prompt,
                    api_key=request_api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    top_k=top_k
                )

            return result

        except Exception as e:
            logger.warning(f"Запрос к модели {model} с API ключом {request_api_key[:5]}... не удался")
            logger.error(f"Ошибка при использовании модели {model} с ключом {request_api_key[:5]}...: {str(e)}")

            # Пробрасываем исключение выше
            raise

    async def _generate_direct(
        self,
        prompt: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int
    ) -> str:
        """
        Прямая генерация через официальный клиент Google Gemini API

        Args:
            prompt: Текст запроса для генерации
            api_key: API ключ
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Top-p параметр (0.0-1.0)
            top_k: Top-k параметр

        Returns:
            str: Сгенерированный текст
        """
        # Проверяем наличие библиотеки и клиента
        if not GEMINI_AVAILABLE:
            raise GeminiConnectionException("Библиотека для работы с Gemini API не установлена")

        if not self.gemini_client:
            # Пробуем инициализировать клиент
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.gemini_client = genai
                logger.info("Клиент Google Generative AI успешно инициализирован для прямого подключения")
            except ImportError:
                raise GeminiConnectionException("Не удалось импортировать библиотеку google.generativeai")
            except Exception as e:
                raise GeminiConnectionException(f"Ошибка при инициализации клиента Gemini: {e}")

        try:
            # Настраиваем параметры генерации (синхронизировано с ботом)
            # Используем max_tokens если передан, иначе дефолтное значение
            max_output_tokens = max_tokens if max_tokens else 15000  # По умолчанию как для планов уроков в боте

            generation_config = {
                "temperature": temperature,
                # Устанавливаем максимальное количество токенов как в боте
                "max_output_tokens": max_output_tokens, # Динамически как в боте
                "top_p": 0.95,
                "top_k": 64  # Увеличено с 40 до 64 как в боте
            }

            # Получаем модель
            model = self.gemini_client.GenerativeModel(
                model_name=self.default_model,
                generation_config=generation_config
            )

            # Генерируем ответ с таймаутом
            import asyncio
            try:
                response = await asyncio.wait_for(self._generate_async(model, prompt, stream=False), timeout=60.0)
            except asyncio.TimeoutError:
                logger.warning("Превышен таймаут при генерации контента через Google Gemini API")
                return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."

            # Проверяем, есть ли ответ
            if not response or not response.text:
                logger.warning("Google Gemini вернул пустой ответ")
                return "Извините, не удалось сгенерировать ответ. Пожалуйста, попробуйте позже."

            # Возвращаем сгенерированный текст
            logger.info(f"Успешно получен ответ от Google Gemini API через прямое подключение, длина: {len(response.text)}")
            return response.text

        except Exception as e:
            error_message = str(e)

            # Классифицируем ошибку
            if "API key not valid" in error_message or "authentication" in error_message.lower():
                raise GeminiAuthException(f"Ошибка аутентификации: {e}")
            elif "quota" in error_message.lower() or "rate limit" in error_message.lower():
                raise GeminiRateLimitException(f"Превышение лимита запросов: {e}")
            else:
                raise GeminiConnectionException(f"Ошибка при генерации контента: {e}")
