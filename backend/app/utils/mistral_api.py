"""
Модуль для работы с Mistral AI API
Основан на официальной библиотеке: https://github.com/mistralai/client-python
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
import httpx
from mistralai import Mistral, models
from mistralai.models import UserMessage

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Проверяем доступность Mistral API
MISTRAL_AVAILABLE = os.environ.get("MISTRAL_API_KEY") is not None

# Исключения для обработки ошибок
class MistralAPIException(Exception):
    """Базовое исключение для API Mistral"""
    pass

class MistralConnectionException(MistralAPIException):
    """Исключение при проблемах с подключением к API"""
    pass

class MistralRateLimitException(MistralAPIException):
    """Исключение при превышении лимита запросов"""
    pass

class MistralAuthException(MistralAPIException):
    """Исключение при проблемах с авторизацией"""
    pass

class MistralHandler:
    """Класс для работы с Mistral AI API"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Инициализация клиента Mistral AI API

        Args:
            api_key: Ключ API Mistral AI
            api_base: Базовый URL API (по умолчанию https://api.mistral.ai)
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self.api_base = api_base or os.environ.get("MISTRAL_API_BASE") or "https://api.mistral.ai"

        # Параметры клиента
        self.timeout = 60  # Таймаут запросов по умолчанию, сек
        self.mistral_client = None
        self.default_model = "open-mistral-nemo"  # Модель по умолчанию
        self.available_models = []

        # Подробное логирование
        logger.info(f"Инициализация MistralHandler (api_key доступен: {'Да' if self.api_key else 'Нет'})")
        logger.info(f"api_base: {self.api_base}")

        # Инициализируем клиент
        self._init_client()

    def _init_client(self):
        """Инициализация клиента Mistral AI"""
        if not self.api_key:
            logger.warning("API ключ Mistral не указан, клиент не будет инициализирован")
            return

        try:
            # Создаем клиент с правильными параметрами согласно документации
            self.mistral_client = Mistral(
                api_key=self.api_key,
                server_url=self.api_base
            )
            logger.info("Mistral API клиент успешно инициализирован")

            # Получаем список доступных моделей
            self._fetch_available_models()
        except Exception as e:
            logger.error(f"Ошибка при инициализации Mistral API клиента: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.mistral_client = None
            raise MistralConnectionException(f"Не удалось подключиться к Mistral API: {e}")

    def _fetch_available_models(self):
        """Получение списка доступных моделей"""
        if not self.mistral_client:
            return

        try:
            response = self.mistral_client.models.list()
            self.available_models = response.data
            logger.info(f"Получено {len(self.available_models)} доступных моделей Mistral")

            # Выводим список моделей в лог для отладки
            model_names = [model.id for model in self.available_models]
            logger.info(f"Доступные модели: {', '.join(model_names)}")
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей Mistral: {e}")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return self.mistral_client is not None

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        models_info = []
        for model in self.available_models:
            models_info.append({
                "id": model.id,
                "name": model.name,
                "description": model.description,
                "max_tokens": model.max_context_length,
                "capabilities": {
                    "chat": model.capabilities.completion_chat,
                    "function_calling": model.capabilities.function_calling,
                    "vision": model.capabilities.vision
                }
            })
        return models_info

    async def _iterate_response(self, response):
        """
        Вспомогательный метод для итерации по асинхронному ответу с таймаутом

        Args:
            response: Асинхронный итератор ответа от Mistral API

        Yields:
            Чанки ответа
        """
        async for chunk in response:
            yield chunk

    async def generate_content(self,
                             prompt: str,
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None) -> str:
        """
        Асинхронная генерация текста с помощью Mistral API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется модель по умолчанию)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Сгенерированный текст
        """
        if not self.mistral_client:
            raise MistralConnectionException("Клиент Mistral не инициализирован")

        # Используем указанную модель или модель по умолчанию
        model_name = model or self.default_model
        logger.info(f"Генерация контента с помощью модели Mistral: {model_name}")

        try:
            # Создаем сообщение для API
            messages = [UserMessage(content=prompt)]

            # Настраиваем параметры запроса
            params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature
            }

            # Добавляем max_tokens, если указан
            if max_tokens:
                params["max_tokens"] = max_tokens

            # Используем метод stream_async для асинхронной генерации с таймаутом
            response = await self.mistral_client.chat.stream_async(**params)

            full_response = ""
            # Устанавливаем таймаут для асинхронного итератора
            import asyncio
            try:
                async for chunk in asyncio.wait_for(self._iterate_response(response), timeout=self.timeout):
                    if chunk.data.choices[0].delta.content is not None:
                        full_response += chunk.data.choices[0].delta.content
            except asyncio.TimeoutError:
                logger.warning(f"Превышен таймаут {self.timeout} сек при генерации контента Mistral")
                return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."

            return full_response

        except models.HTTPValidationError as e:
            logger.error(f"Ошибка валидации запроса Mistral API: {e}")
            raise MistralAPIException(f"Ошибка в запросе: {e}")
        except models.SDKError as e:
            if e.status_code == 429:
                logger.error(f"Превышен лимит запросов к Mistral API: {e}")
                raise MistralRateLimitException(f"Превышен лимит запросов: {e}")
            elif e.status_code in (401, 403):
                logger.error(f"Ошибка авторизации в Mistral API: {e}")
                raise MistralAuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка Mistral API: {e}")
                raise MistralAPIException(f"Ошибка API: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при использовании Mistral API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise MistralAPIException(f"Непредвиденная ошибка: {e}")

    def generate_content_sync(self,
                            prompt: str,
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None) -> str:
        """
        Синхронная генерация текста с помощью Mistral API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется модель по умолчанию)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Сгенерированный текст
        """
        if not self.mistral_client:
            raise MistralConnectionException("Клиент Mistral не инициализирован")

        # Используем указанную модель или модель по умолчанию
        model_name = model or self.default_model
        logger.info(f"Генерация контента с помощью модели Mistral: {model_name}")

        try:
            # Создаем сообщение для API
            messages = [UserMessage(content=prompt)]

            # Настраиваем параметры запроса
            params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature
            }

            # Добавляем max_tokens, если указан
            if max_tokens:
                params["max_tokens"] = max_tokens

            # Используем метод stream для синхронной генерации с таймаутом
            response = self.mistral_client.chat.stream(**params)

            full_response = ""
            # Устанавливаем таймаут для синхронного итератора
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Превышен таймаут {self.timeout} сек при генерации контента Mistral")

            # Устанавливаем обработчик сигнала
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)

            try:
                for chunk in response:
                    if chunk.data.choices[0].delta.content is not None:
                        full_response += chunk.data.choices[0].delta.content
                # Отключаем таймаут
                signal.alarm(0)
            except TimeoutError as e:
                logger.warning(str(e))
                return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."

            return full_response

        except models.HTTPValidationError as e:
            logger.error(f"Ошибка валидации запроса Mistral API: {e}")
            raise MistralAPIException(f"Ошибка в запросе: {e}")
        except models.SDKError as e:
            if e.status_code == 429:
                logger.error(f"Превышен лимит запросов к Mistral API: {e}")
                raise MistralRateLimitException(f"Превышен лимит запросов: {e}")
            elif e.status_code in (401, 403):
                logger.error(f"Ошибка авторизации в Mistral API: {e}")
                raise MistralAuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка Mistral API: {e}")
                raise MistralAPIException(f"Ошибка API: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при использовании Mistral API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise MistralAPIException(f"Непредвиденная ошибка: {e}")