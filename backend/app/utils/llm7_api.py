"""
Модуль для работы с LLM7 AI API
Основан на OpenAI-совместимом API: https://api.llm7.io/v1/models
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
import httpx
import json

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Проверяем доступность LLM7 API
LLM7_AVAILABLE = os.environ.get("LLM7_API_KEY") is not None

# Исключения для обработки ошибок
class LLM7APIException(Exception):
    """Базовое исключение для API LLM7"""
    pass

class LLM7ConnectionException(LLM7APIException):
    """Исключение при проблемах с подключением к API"""
    pass

class LLM7RateLimitException(LLM7APIException):
    """Исключение при превышении лимита запросов"""
    pass

class LLM7AuthException(LLM7APIException):
    """Исключение при проблемах с авторизацией"""
    pass

class LLM7Handler:
    """Класс для работы с LLM7 AI API"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        Инициализация клиента LLM7 AI API

        Args:
            api_key: Ключ API LLM7
            api_base: Базовый URL API (по умолчанию https://api.llm7.io/v1)
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("LLM7_API_KEY")
        self.api_base = api_base or os.environ.get("LLM7_API_BASE") or "https://api.llm7.io/v1"

        # Параметры клиента
        self.timeout = 120  # Таймаут запросов по умолчанию, сек (увеличен для сложных генераций)
        self.available_models = []
        
        # Приоритетные модели (вначале бесплатные селекторы LLM7)
        self.priority_models = [
            os.environ.get("LLM7_DEFAULT_MODEL", "default"),  # бесплатный селектор
            "fast",                                           # низкая задержка (бесплатный селектор)
            # ниже — возможные конкретные ID, если селекторы недоступны
            "mistral-small-3.1-24b-instruct",
            "llama-3.1-8b-instant"
        ]
        
        # Модель по умолчанию — из env или первая в приоритете
        self.default_model = os.environ.get("LLM7_DEFAULT_MODEL", self.priority_models[0])

        # Дополнительные заголовки для LLM7
        self.site_url = os.environ.get("LLM7_SITE_URL", "https://evo-teach.com")
        self.site_name = os.environ.get("LLM7_SITE_NAME", "EVO Teach AI")

        # Подробное логирование
        logger.info(f"Инициализация LLM7Handler (api_key доступен: {'Да' if self.api_key else 'Нет'})")
        logger.info(f"api_base: {self.api_base}")
        logger.info(f"default_model: {self.default_model}")
        logger.info(f"priority_models: {', '.join(self.priority_models)}")

        # Проверяем доступность API
        if self.api_key:
            self._fetch_available_models()

    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов к LLM7 API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Добавляем опциональные заголовки
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
            # LLM7 возвращает массив моделей напрямую
            if isinstance(models_data, list):
                self.available_models = models_data
            else:
                self.available_models = models_data.get("data", [])
                
            logger.info(f"Получено {len(self.available_models)} доступных моделей LLM7")

            # Проверяем доступность приоритетных моделей
            available_model_ids = [model.get("id", "") for model in self.available_models]
            available_priority = [model for model in self.priority_models if model in available_model_ids]
            logger.info(f"Доступные приоритетные модели: {', '.join(available_priority)}")
            
            # Обновляем модель по умолчанию на первую доступную приоритетную (если не переопределена в env)
            if available_priority:
                env_model = os.environ.get("LLM7_DEFAULT_MODEL")
                if not env_model:
                    self.default_model = available_priority[0]
                    logger.info(f"Модель по умолчанию обновлена на: {self.default_model}")
                else:
                    logger.info(f"Сохраняем модель по умолчанию из ENV: {env_model}")
            else:
                logger.info("Приоритетные модели не найдены в списке /models — остаёмся на селекторе 'default'")
                
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей LLM7: {e}")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return self.api_key is not None

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        models_info = []
        for model in self.available_models:
            models_info.append({
                "id": model.get("id", ""),
                "name": model.get("id", ""),  # LLM7 не предоставляет отдельное поле name
                "object": model.get("object", "model"),
                "created": model.get("created", 0),
                "owned_by": model.get("owned_by", ""),
                "modalities": model.get("modalities", {}),
                "is_priority": model.get("id", "") in self.priority_models
            })
        return models_info

    def get_priority_models(self) -> List[str]:
        """Получение списка приоритетных моделей"""
        return self.priority_models.copy()

    def get_best_available_model(self) -> str:
        """Получение лучшей доступной модели из приоритетного списка"""
        available_model_ids = [model.get("id", "") for model in self.available_models]
        
        # Ищем первую доступную модель из приоритетного списка
        for priority_model in self.priority_models:
            if priority_model in available_model_ids:
                return priority_model
                
        # Если ни одна приоритетная модель недоступна, возвращаем первую доступную
        if available_model_ids:
            return available_model_ids[0]
            
        # Если вообще нет доступных моделей, возвращаем модель по умолчанию
        return self.default_model

    async def generate_content(self,
                             prompt: str,
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None,
                             stream: bool = False) -> str:
        """
        Асинхронная генерация текста с помощью LLM7 API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется лучшая доступная)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе
            stream: Использовать ли потоковую передачу

        Returns:
            Сгенерированный текст
        """
        if not self.api_key:
            raise LLM7ConnectionException("API ключ LLM7 не указан")

        # Используем указанную модель или лучшую доступную
        model_name = model or self.get_best_available_model()
        logger.info(f"Генерация контента с помощью модели LLM7: {model_name}")

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
                    return await self._handle_streaming_response(client, request_data)
                else:
                    return await self._handle_regular_response(client, request_data)

        except httpx.TimeoutException:
            logger.warning(f"Превышен таймаут {self.timeout} сек при генерации контента LLM7")
            return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error(f"Превышен лимит запросов к LLM7 API: {e}")
                raise LLM7RateLimitException(f"Превышен лимит запросов: {e}")
            elif e.response.status_code in (401, 403):
                logger.error(f"Ошибка авторизации в LLM7 API: {e}")
                raise LLM7AuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка HTTP LLM7 API: {e}")
                raise LLM7APIException(f"Ошибка API: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при использовании LLM7 API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise LLM7APIException(f"Непредвиденная ошибка: {e}")

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

        logger.warning("Неожиданный формат ответа от LLM7 API")
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
        Синхронная генерация текста с помощью LLM7 API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется лучшая доступная)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Сгенерированный текст
        """
        if not self.api_key:
            raise LLM7ConnectionException("API ключ LLM7 не указан")

        # Используем указанную модель или лучшую доступную
        model_name = model or self.get_best_available_model()
        logger.info(f"Синхронная генерация контента с помощью модели LLM7: {model_name}")

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

            logger.warning("Неожиданный формат ответа от LLM7 API")
            return "Извините, не удалось получить ответ от модели."

        except requests.exceptions.Timeout:
            logger.warning(f"Превышен таймаут {self.timeout} сек при генерации контента LLM7")
            return "Извините, генерация заняла слишком много времени. Пожалуйста, попробуйте еще раз."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.error(f"Превышен лимит запросов к LLM7 API: {e}")
                raise LLM7RateLimitException(f"Превышен лимит запросов: {e}")
            elif e.response.status_code in (401, 403):
                logger.error(f"Ошибка авторизации в LLM7 API: {e}")
                raise LLM7AuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка HTTP LLM7 API: {e}")
                raise LLM7APIException(f"Ошибка API: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при использовании LLM7 API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise LLM7APIException(f"Непредвиденная ошибка: {e}")

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

    def test_connection(self) -> bool:
        """
        Тестирование подключения к LLM7 API

        Returns:
            True, если подключение успешно, False в противном случае
        """
        if not self.api_key:
            logger.error("API ключ LLM7 не указан")
            return False

        try:
            # Простой тест - получение списка моделей
            import requests
            response = requests.get(
                f"{self.api_base}/models",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            logger.info("Подключение к LLM7 API успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к LLM7 API: {e}")
            return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Получение статистики использования

        Returns:
            Словарь со статистикой
        """
        return {
            "api_available": self.is_available(),
            "total_models": len(self.available_models),
            "priority_models": len(self.priority_models),
            "default_model": self.default_model,
            "best_available_model": self.get_best_available_model() if self.available_models else None
        }
