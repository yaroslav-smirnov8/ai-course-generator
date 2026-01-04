"""
Модуль для работы с Groq Cloud API
Поддерживает автоматическое переключение между моделями при достижении лимитов
"""

import os
import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
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

# Проверяем доступность Groq API
try:
    from groq import Groq, AsyncGroq
    GROQ_AVAILABLE = True
    logger.info("Groq библиотека успешно импортирована")
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq библиотека не установлена. Установите: pip install groq")

# Исключения для обработки ошибок
class GroqAPIException(Exception):
    """Базовое исключение для API Groq"""
    pass

class GroqConnectionException(GroqAPIException):
    """Исключение при проблемах с подключением к API"""
    pass

class GroqRateLimitException(GroqAPIException):
    """Исключение при превышении лимита запросов"""
    pass

class GroqAuthException(GroqAPIException):
    """Исключение при проблемах с авторизацией"""
    pass

class GroqModelUnavailableException(GroqAPIException):
    """Исключение когда все модели недоступны"""
    pass


class GroqHandler:
    """Класс для работы с Groq Cloud API с автоматическим переключением моделей"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента Groq Cloud API

        Args:
            api_key: Ключ API Groq
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        
        # Параметры клиента
        self.timeout = 60  # Таймаут запросов по умолчанию, сек
        
        # Модели в порядке приоритета (как запросил пользователь)
        self.models_priority = [
            "meta-llama/llama-4-maverick-17b-128e-instruct",  # Llama 4.0 Maverick
            "meta-llama/llama-4-scout-17b-16e-instruct",      # Llama 4.0 Scout
            "qwen-qwq-32b",                                    # QwQ
            "llama-3.3-70b-versatile",                        # LLaMA 3.3 70B
            "llama-3.1-8b-instant",                           # llama-3.1-8b-instant
            "mistral-saba-24b",                               # Mistral Saba
            "deepseek-r1-distill-llama-70b"                   # deepseek-r1-distill-llama-70b
        ]
        
        # Информация о моделях
        self.models_info = {
            "meta-llama/llama-4-maverick-17b-128e-instruct": {
                "name": "Llama 4.0 Maverick",
                "context_window": 131072,
                "max_completion_tokens": 8192,
                "type": "preview"
            },
            "meta-llama/llama-4-scout-17b-16e-instruct": {
                "name": "Llama 4.0 Scout", 
                "context_window": 131072,
                "max_completion_tokens": 8192,
                "type": "preview"
            },
            "qwen-qwq-32b": {
                "name": "Qwen QwQ 32B",
                "context_window": 128000,
                "max_completion_tokens": 8192,
                "type": "preview"
            },
            "llama-3.3-70b-versatile": {
                "name": "LLaMA 3.3 70B Versatile",
                "context_window": 128000,
                "max_completion_tokens": 32768,
                "type": "production"
            },
            "llama-3.1-8b-instant": {
                "name": "LLaMA 3.1 8B Instant",
                "context_window": 128000,
                "max_completion_tokens": 8192,
                "type": "production"
            },
            "mistral-saba-24b": {
                "name": "Mistral Saba 24B",
                "context_window": 32000,
                "max_completion_tokens": 8192,
                "type": "preview"
            },
            "deepseek-r1-distill-llama-70b": {
                "name": "DeepSeek R1 Distill LLaMA 70B",
                "context_window": 128000,
                "max_completion_tokens": 8192,
                "type": "preview"
            }
        }
        
        # Отслеживание использования моделей
        self.model_usage = {}
        self.model_cooldowns = {}  # Время когда модель снова станет доступной
        
        # Текущая активная модель
        self.current_model = None
        
        # Подробное логирование
        logger.info(f"Инициализация GroqHandler (api_key доступен: {'Да' if self.api_key else 'Нет'})")
        logger.info(f"Доступно моделей: {len(self.models_priority)}")
        logger.info(f"Приоритет моделей: {', '.join(self.models_priority)}")

        # Инициализируем клиенты
        self.sync_client = None
        self.async_client = None
        
        if self.api_key:
            try:
                if GROQ_AVAILABLE:
                    self.sync_client = Groq(api_key=self.api_key)
                    self.async_client = AsyncGroq(api_key=self.api_key)
                    logger.info("Groq клиенты успешно инициализированы")
                else:
                    logger.warning("Groq библиотека не доступна")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Groq клиентов: {e}")
        else:
            logger.warning("API ключ Groq не указан")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return self.api_key is not None and GROQ_AVAILABLE

    def get_available_model(self) -> Optional[str]:
        """
        Получение доступной модели с учетом лимитов и кулдаунов

        Returns:
            str: ID доступной модели или None если все модели недоступны
        """
        current_time = datetime.now()

        for model_id in self.models_priority:
            # Проверяем, не находится ли модель в кулдауне
            if model_id in self.model_cooldowns:
                cooldown_end = self.model_cooldowns[model_id]
                if current_time < cooldown_end:
                    remaining = (cooldown_end - current_time).total_seconds()
                    logger.debug(f"Модель {model_id} в кулдауне еще {remaining:.0f} секунд")
                    continue
                else:
                    # Кулдаун закончился, убираем из списка
                    del self.model_cooldowns[model_id]
                    logger.info(f"Кулдаун для модели {model_id} закончился")

            # Модель доступна
            if self.current_model != model_id:
                old_model = self.current_model
                self.current_model = model_id
                model_name = self.models_info.get(model_id, {}).get("name", model_id)
                logger.info(f"Переключение на модель: {model_name} ({model_id})")

                # Логгируем переключение модели
                if old_model:
                    log_key_switch(
                        provider="groq",
                        from_key=old_model,
                        to_key=model_id,
                        reason="model_switch",
                        component="groq_handler"
                    )

            return model_id

        # Все модели недоступны
        logger.error("Все модели Groq находятся в кулдауне")
        log_key_error(
            provider="groq",
            key_id="all_models",
            error_type="all_models_unavailable",
            error_message="Все модели Groq находятся в кулдауне",
            component="groq_handler"
        )
        return None

    def set_model_cooldown(self, model_id: str, minutes: int = 1):
        """
        Устанавливает кулдаун для модели

        Args:
            model_id: ID модели
            minutes: Время кулдауна в минутах
        """
        cooldown_end = datetime.now() + timedelta(minutes=minutes)
        self.model_cooldowns[model_id] = cooldown_end

        model_name = self.models_info.get(model_id, {}).get("name", model_id)
        logger.warning(f"Модель {model_name} ({model_id}) помещена в кулдаун на {minutes} минут")

        # Логгируем установку кулдауна
        log_key_error(
            provider="groq",
            key_id=model_id,
            error_type="cooldown_set",
            error_message=f"Модель помещена в кулдаун на {minutes} минут",
            component="groq_handler",
            cooldown_minutes=minutes
        )

    def get_models_info(self) -> List[Dict[str, Any]]:
        """Получение информации о всех доступных моделях"""
        models_list = []
        current_time = datetime.now()
        
        for model_id in self.models_priority:
            model_info = self.models_info.get(model_id, {}).copy()
            model_info["id"] = model_id
            
            # Проверяем статус доступности
            if model_id in self.model_cooldowns:
                cooldown_end = self.model_cooldowns[model_id]
                if current_time < cooldown_end:
                    remaining = (cooldown_end - current_time).total_seconds()
                    model_info["status"] = "cooldown"
                    model_info["available_in"] = f"{remaining:.0f} seconds"
                else:
                    model_info["status"] = "available"
            else:
                model_info["status"] = "available"
            
            # Добавляем статистику использования
            usage = self.model_usage.get(model_id, {"requests": 0, "tokens": 0})
            model_info["usage"] = usage
            
            models_list.append(model_info)
        
        return models_list

    async def generate_content(self,
                             prompt: str,
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None,
                             stream: bool = False) -> str:
        """
        Асинхронная генерация текста с помощью Groq API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется автоматический выбор)
            temperature: Температура генерации (0.0 - 2.0)
            max_tokens: Максимальное количество токенов в ответе
            stream: Использовать ли потоковую передачу

        Returns:
            Сгенерированный текст
        """
        if not self.is_available():
            raise GroqConnectionException("Groq API недоступен")

        # Выбираем модель
        if model is None:
            model = self.get_available_model()
            if model is None:
                raise GroqModelUnavailableException("Все модели Groq недоступны")

        model_name = self.models_info.get(model, {}).get("name", model)
        logger.info(f"Генерация контента с помощью модели Groq: {model_name}")

        # Засекаем время начала запроса
        start_time = datetime.now()

        try:
            # Подготавливаем данные запроса
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Определяем максимальное количество токенов для модели
            if max_tokens is None:
                model_info = self.models_info.get(model, {})
                max_tokens = min(model_info.get("max_completion_tokens", 8192), 8192)

            # Выполняем асинхронный запрос
            if stream:
                result = await self._handle_streaming_response(model, messages, temperature, max_tokens)
            else:
                result = await self._handle_regular_response(model, messages, temperature, max_tokens)

            # Рассчитываем время ответа
            response_time = (datetime.now() - start_time).total_seconds()

            # Логгируем успешное использование
            log_key_usage(
                provider="groq",
                key_id=model,
                component="groq_handler",
                model=model,
                success=True,
                response_time=response_time,
                tokens_used=len(result) if result else 0
            )

            return result

        except Exception as e:
            # Рассчитываем время до ошибки
            response_time = (datetime.now() - start_time).total_seconds()

            # Логгируем неудачное использование
            log_key_usage(
                provider="groq",
                key_id=model,
                component="groq_handler",
                model=model,
                success=False,
                response_time=response_time
            )

            # Обрабатываем различные типы ошибок
            if "429" in str(e) or "rate limit" in str(e).lower():
                logger.warning(f"Превышен лимит для модели {model_name}: {e}")
                self.set_model_cooldown(model, minutes=1)

                # Логгируем ошибку rate limit
                log_key_error(
                    provider="groq",
                    key_id=model,
                    error_type="rate_limit",
                    error_message=str(e),
                    component="groq_handler",
                    will_retry=True,
                    cooldown_minutes=1
                )

                raise GroqRateLimitException(f"Превышен лимит запросов для модели {model_name}")
            elif "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error(f"Ошибка авторизации в Groq API: {e}")

                # Логгируем ошибку авторизации
                log_key_error(
                    provider="groq",
                    key_id=model,
                    error_type="auth_error",
                    error_message=str(e),
                    component="groq_handler",
                    will_retry=False
                )

                raise GroqAuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка Groq API для модели {model_name}: {e}")

                # Логгируем общую ошибку API
                log_key_error(
                    provider="groq",
                    key_id=model,
                    error_type="api_error",
                    error_message=str(e),
                    component="groq_handler",
                    will_retry=False
                )

                raise GroqAPIException(f"Ошибка API: {e}")

    async def _handle_regular_response(self, model: str, messages: List[Dict],
                                     temperature: float, max_tokens: int) -> str:
        """Обработка обычного (не потокового) ответа"""
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Обновляем статистику использования
            self._update_usage_stats(model, response)

            # Извлекаем сгенерированный текст
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()

            logger.warning("Неожиданный формат ответа от Groq API")
            return "Извините, не удалось получить ответ от модели."

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа Groq API: {e}")
            raise

    async def _handle_streaming_response(self, model: str, messages: List[Dict],
                                       temperature: float, max_tokens: int) -> str:
        """Обработка потокового ответа"""
        try:
            full_response = ""

            stream = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content

            return full_response.strip()

        except Exception as e:
            logger.error(f"Ошибка при обработке потокового ответа Groq API: {e}")
            raise

    def _update_usage_stats(self, model: str, response):
        """Обновление статистики использования модели"""
        try:
            if model not in self.model_usage:
                self.model_usage[model] = {"requests": 0, "tokens": 0}

            self.model_usage[model]["requests"] += 1

            # Добавляем токены если доступна информация
            if hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, 'total_tokens'):
                    self.model_usage[model]["tokens"] += response.usage.total_tokens

        except Exception as e:
            logger.debug(f"Ошибка при обновлении статистики: {e}")

    def generate_content_sync(self,
                            prompt: str,
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None) -> str:
        """
        Синхронная генерация текста с помощью Groq API

        Args:
            prompt: Текст запроса
            model: Название модели (если не указана, используется автоматический выбор)
            temperature: Температура генерации (0.0 - 2.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Сгенерированный текст
        """
        if not self.is_available():
            raise GroqConnectionException("Groq API недоступен")

        # Выбираем модель
        if model is None:
            model = self.get_available_model()
            if model is None:
                raise GroqModelUnavailableException("Все модели Groq недоступны")

        model_name = self.models_info.get(model, {}).get("name", model)
        logger.info(f"Синхронная генерация контента с помощью модели Groq: {model_name}")

        try:
            # Подготавливаем данные запроса
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Определяем максимальное количество токенов для модели
            if max_tokens is None:
                model_info = self.models_info.get(model, {})
                max_tokens = min(model_info.get("max_completion_tokens", 8192), 8192)

            # Выполняем синхронный запрос
            response = self.sync_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Обновляем статистику использования
            self._update_usage_stats(model, response)

            # Извлекаем сгенерированный текст
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()

            logger.warning("Неожиданный формат ответа от Groq API")
            return "Извините, не удалось получить ответ от модели."

        except Exception as e:
            # Обрабатываем различные типы ошибок
            if "429" in str(e) or "rate limit" in str(e).lower():
                logger.warning(f"Превышен лимит для модели {model_name}: {e}")
                self.set_model_cooldown(model, minutes=1)
                raise GroqRateLimitException(f"Превышен лимит запросов для модели {model_name}")
            elif "401" in str(e) or "unauthorized" in str(e).lower():
                logger.error(f"Ошибка авторизации в Groq API: {e}")
                raise GroqAuthException(f"Ошибка авторизации: {e}")
            else:
                logger.error(f"Ошибка Groq API для модели {model_name}: {e}")
                raise GroqAPIException(f"Ошибка API: {e}")

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о конкретной модели

        Args:
            model_id: Идентификатор модели

        Returns:
            Информация о модели или None, если модель не найдена
        """
        if model_id in self.models_info:
            info = self.models_info[model_id].copy()
            info["id"] = model_id

            # Добавляем статус доступности
            current_time = datetime.now()
            if model_id in self.model_cooldowns:
                cooldown_end = self.model_cooldowns[model_id]
                if current_time < cooldown_end:
                    remaining = (cooldown_end - current_time).total_seconds()
                    info["status"] = "cooldown"
                    info["available_in"] = f"{remaining:.0f} seconds"
                else:
                    info["status"] = "available"
            else:
                info["status"] = "available"

            return info
        return None

    def reset_cooldowns(self):
        """Сброс всех кулдаунов (для тестирования)"""
        self.model_cooldowns.clear()
        logger.info("Все кулдауны моделей сброшены")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Получение статистики использования"""
        return {
            "models_usage": self.model_usage.copy(),
            "current_model": self.current_model,
            "models_in_cooldown": len(self.model_cooldowns),
            "available_models": len([m for m in self.models_priority if m not in self.model_cooldowns])
        }
