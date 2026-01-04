"""
Модуль для работы с OpenRouter AI API
Основан на OpenAI-совместимом API: https://openrouter.ai/docs/quickstart
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import httpx
import json

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Импортируем систему логгирования ключей
try:
    from .api_keys_logger import log_key_usage, log_key_error, log_key_switch
except ImportError:
    # Fallback функции если логгер недоступен
    def log_key_usage(*args, **kwargs):
        pass
    def log_key_error(*args, **kwargs):
        pass
    def log_key_switch(*args, **kwargs):
        pass

# Проверяем доступность OpenRouter API
OPENROUTER_AVAILABLE = os.environ.get("OPENROUTER_API_KEY") is not None

# Исключения для обработки ошибок
class OpenRouterAPIException(Exception):
    """Базовое исключение для API OpenRouter"""
    pass

class OpenRouterConnectionException(OpenRouterAPIException):
    """Исключение при проблемах с подключением к API"""
    pass

class OpenRouterRateLimitException(OpenRouterAPIException):
    """Исключение при превышении лимита запросов"""
    pass

class OpenRouterAuthException(OpenRouterAPIException):
    """Исключение при проблемах с авторизацией"""
    pass

class OpenRouterHandler:
    """Класс для работы с OpenRouter AI API"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Инициализация клиента OpenRouter AI API

        Args:
            api_key: Ключ API OpenRouter
            api_base: Базовый URL API (по умолчанию https://openrouter.ai/api/v1)
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.api_base = api_base or os.environ.get("OPENROUTER_API_BASE") or "https://openrouter.ai/api/v1"

        # Параметры клиента
        self.timeout = 60  # Таймаут запросов по умолчанию, сек
        self.default_model = "google/gemini-2.0-flash-exp:free"  # Модель по умолчанию
        self.available_models = []

        # Дополнительные заголовки для OpenRouter
        self.site_url = os.environ.get("OPENROUTER_SITE_URL", "")
        self.site_name = os.environ.get("OPENROUTER_SITE_NAME", "EVO Teach AI")

        # Подробное логирование
        logger.info(f"Инициализация OpenRouterHandler (api_key доступен: {'Да' if self.api_key else 'Нет'})")
        logger.info(f"api_base: {self.api_base}")
        logger.info(f"default_model: {self.default_model}")

        # Проверяем доступность API
        if self.api_key:
            self._fetch_available_models()

    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов к OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Добавляем опциональные заголовки для рейтингов OpenRouter
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name

        return headers

    def _fetch_available_models(self):
        """Получение списка доступных моделей"""
        if not self.api_key:
            return

        try:
            import requests
            response = requests.get(
                f"{self.api_base}/models",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()

            models_data = response.json()
            self.available_models = models_data.get("data", [])
            logger.info(f"Получено {len(self.available_models)} доступных моделей OpenRouter")

            # Выводим список моделей в лог для отладки (только первые 10)
            model_names = [model.get("id", "unknown") for model in self.available_models[:10]]
            logger.info(f"Первые 10 доступных моделей: {', '.join(model_names)}")
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей OpenRouter: {e}")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return self.api_key is not None

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        models_info = []
        for model in self.available_models:
            models_info.append({
                "id": model.get("id", ""),
                "name": model.get("name", model.get("id", "")),
                "description": model.get("description", ""),
                "max_tokens": model.get("context_length", 0),
                "pricing": {
                    "prompt": model.get("pricing", {}).get("prompt", "0"),
                    "completion": model.get("pricing", {}).get("completion", "0")
                },
                "top_provider": model.get("top_provider", {})
            })
        return models_info

    async def generate_content(self,
                             prompt: str,
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None,
                             stream: bool = False) -> str:
        """
        Асинхронная генерация текста с помощью OpenRouter API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется модель по умолчанию)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе
            stream: Использовать ли потоковую передачу

        Returns:
            Сгенерированный текст
        """
        if not self.api_key:
            raise OpenRouterConnectionException("API ключ OpenRouter не указан")

        # Используем указанную модель или модель по умолчанию
        model_name = model or self.default_model
        logger.info(f"Генерация контента с помощью модели OpenRouter: {model_name}")

        # Засекаем время начала запроса
        start_time = datetime.now()

        try:
            # Подготавливаем данные запроса
            request_data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "stream": stream
            }

            # Добавляем max_tokens, если указан
            if max_tokens:
                request_data["max_tokens"] = max_tokens

            # Выполняем асинхронный запрос
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    result = await self._handle_streaming_response(client, request_data)
                else:
                    result = await self._handle_regular_response(client, request_data)

                # Рассчитываем время ответа
                response_time = (datetime.now() - start_time).total_seconds()

                # Логгируем успешное использование
                log_key_usage(
                    provider="openrouter",
                    key_id=self.api_key,
                    component="openrouter_handler",
                    model=model_name,
                    success=True,
                    response_time=response_time,
                    tokens_used=len(result) if result else 0
                )

                return result

        except httpx.TimeoutException:
            logger.warning(f"Превышен таймаут {self.timeout} сек при генерации контента OpenRouter")
            return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."
        except httpx.HTTPStatusError as e:
            # Рассчитываем время до ошибки
            response_time = (datetime.now() - start_time).total_seconds()

            if e.response.status_code == 429:
                logger.error(f"Превышен лимит запросов к OpenRouter API: {e}")

                # Логгируем rate limit
                log_key_error(
                    provider="openrouter",
                    key_id=self.api_key,
                    error_type="rate_limit",
                    error_message=str(e),
                    component="openrouter_handler",
                    will_retry=False
                )

                raise OpenRouterRateLimitException(f"Превышен лимит запросов: {e}")
            elif e.response.status_code in (401, 403):
                logger.error(f"Ошибка авторизации в OpenRouter API: {e}")

                # Логгируем ошибку авторизации
                log_key_error(
                    provider="openrouter",
                    key_id=self.api_key,
                    error_type="auth_error",
                    error_message=str(e),
                    component="openrouter_handler",
                    will_retry=False
                )

                raise OpenRouterAuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка HTTP OpenRouter API: {e}")

                # Логгируем общую ошибку API
                log_key_error(
                    provider="openrouter",
                    key_id=self.api_key,
                    error_type="api_error",
                    error_message=str(e),
                    component="openrouter_handler",
                    will_retry=False
                )

                raise OpenRouterAPIException(f"Ошибка API: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при использовании OpenRouter API: {e}")

            # Логгируем неожиданную ошибку
            log_key_error(
                provider="openrouter",
                key_id=self.api_key,
                error_type="unexpected_error",
                error_message=str(e),
                component="openrouter_handler",
                will_retry=False
            )

            import traceback
            logger.error(traceback.format_exc())
            raise OpenRouterAPIException(f"Непредвиденная ошибка: {e}")

    async def _handle_regular_response(self, client: httpx.AsyncClient, request_data: Dict) -> str:
        """Обработка обычного (не потокового) ответа"""
        response = await client.post(
            f"{self.api_base}/chat/completions",
            headers=self._get_headers(),
            json=request_data
        )
        response.raise_for_status()

        response_data = response.json()

        # Извлекаем сгенерированный текст
        if "choices" in response_data and len(response_data["choices"]) > 0:
            choice = response_data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]

        logger.warning("Неожиданный формат ответа от OpenRouter API")
        return "Извините, не удалось получить ответ от модели."

    async def _handle_streaming_response(self, client: httpx.AsyncClient, request_data: Dict) -> str:
        """Обработка потокового ответа"""
        full_response = ""

        async with client.stream(
            "POST",
            f"{self.api_base}/chat/completions",
            headers=self._get_headers(),
            json=request_data
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Убираем "data: "

                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            choice = data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                if content:
                                    full_response += content
                    except json.JSONDecodeError:
                        continue

        return full_response

    def generate_content_sync(self,
                            prompt: str,
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None) -> str:
        """
        Синхронная генерация текста с помощью OpenRouter API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется модель по умолчанию)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Сгенерированный текст
        """
        if not self.api_key:
            raise OpenRouterConnectionException("API ключ OpenRouter не указан")

        # Используем указанную модель или модель по умолчанию
        model_name = model or self.default_model
        logger.info(f"Синхронная генерация контента с помощью модели OpenRouter: {model_name}")

        try:
            import requests

            # Подготавливаем данные запроса
            request_data = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "stream": False
            }

            # Добавляем max_tokens, если указан
            if max_tokens:
                request_data["max_tokens"] = max_tokens

            # Выполняем синхронный запрос
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self._get_headers(),
                json=request_data,
                timeout=self.timeout
            )
            response.raise_for_status()

            response_data = response.json()

            # Извлекаем сгенерированный текст
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]

            logger.warning("Неожиданный формат ответа от OpenRouter API")
            return "Извините, не удалось получить ответ от модели."

        except requests.exceptions.Timeout:
            logger.warning(f"Превышен таймаут {self.timeout} сек при генерации контента OpenRouter")
            return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error(f"Превышен лимит запросов к OpenRouter API: {e}")
                raise OpenRouterRateLimitException(f"Превышен лимит запросов: {e}")
            elif e.response.status_code in (401, 403):
                logger.error(f"Ошибка авторизации в OpenRouter API: {e}")
                raise OpenRouterAuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка HTTP OpenRouter API: {e}")
                raise OpenRouterAPIException(f"Ошибка API: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при использовании OpenRouter API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise OpenRouterAPIException(f"Непредвиденная ошибка: {e}")

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о конкретной модели

        Args:
            model_id: Идентификатор модели

        Returns:
            Информация о модели или None, если модель не найдена
        """
        for model in self.available_models:
            if model.get("id") == model_id:
                return model
        return None

    def get_credits(self) -> Optional[Dict[str, Any]]:
        """
        Получение информации о кредитах пользователя

        Returns:
            Информация о кредитах или None при ошибке
        """
        if not self.api_key:
            return None

        try:
            import requests
            response = requests.get(
                f"{self.api_base}/auth/key",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при получении информации о кредитах: {e}")
            return None
