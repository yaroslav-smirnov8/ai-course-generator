"""
Together AI API Handler
Модуль для работы с Together AI API
"""

import os
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta

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

# Проверяем доступность Together AI API
TOGETHER_AVAILABLE = True

class TogetherAPIException(Exception):
    """Исключение для ошибок Together AI API"""
    pass

class TogetherHandler:
    """Обработчик для Together AI API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента Together AI API

        Args:
            api_key: Ключ API Together AI
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")

        self.api_url = "https://api.together.xyz/v1/chat/completions"
        self.timeout = 60

        # Приоритетные модели Together AI
        self.models = [
            "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
            "teknium/OpenHermes-2.5-Mistral-7B"
        ]

        # Загружаем API ключи из переменных окружения
        self.api_keys = []
        for i in range(1, 7):  # TOGETHER_API_KEY_1 до TOGETHER_API_KEY_6
            key = os.environ.get(f"TOGETHER_API_KEY_{i}")
            if key and key != 'unused':
                self.api_keys.append(key)

        # Добавляем основной ключ если есть
        if self.api_key and self.api_key not in self.api_keys:
            self.api_keys.insert(0, self.api_key)

        logger.info(f"Инициализация TogetherHandler (доступно ключей: {len(self.api_keys)})")
        
        # Состояние ключей и моделей
        self.key_cooldowns = {}  # Кулдауны для ключей
        self.model_cooldowns = {}  # Кулдауны для моделей
        self.current_key_index = 0
        self.current_model_index = 0

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return len(self.api_keys) > 0
        
    def get_available_api_key(self) -> Optional[str]:
        """Получает доступный API ключ с учетом кулдаунов"""
        current_time = datetime.now()

        # Проверяем все ключи начиная с текущего
        for i in range(len(self.api_keys)):
            key_index = (self.current_key_index + i) % len(self.api_keys)
            api_key = self.api_keys[key_index]

            cooldown_end = self.key_cooldowns.get(api_key)
            if not cooldown_end or current_time >= cooldown_end:
                # Логгируем переключение ключа если изменился
                if self.current_key_index != key_index and hasattr(self, '_last_used_key'):
                    log_key_switch(
                        provider="together",
                        from_key=self._last_used_key,
                        to_key=api_key,
                        reason="key_rotation",
                        component="together_handler"
                    )

                self.current_key_index = key_index
                self._last_used_key = api_key
                return api_key

        # Если все ключи в кулдауне, используем первый
        logger.warning("Все API ключи Together AI в кулдауне, используем первый")
        log_key_error(
            provider="together",
            key_id="all_keys",
            error_type="all_keys_in_cooldown",
            error_message="Все API ключи Together AI в кулдауне",
            component="together_handler"
        )
        self.current_key_index = 0
        return self.api_keys[0]
    
    def get_available_model(self) -> str:
        """Получает доступную модель с учетом кулдаунов"""
        current_time = datetime.now()
        
        # Проверяем все модели начиная с текущей
        for i in range(len(self.models)):
            model_index = (self.current_model_index + i) % len(self.models)
            model = self.models[model_index]
            
            cooldown_end = self.model_cooldowns.get(model)
            if not cooldown_end or current_time >= cooldown_end:
                self.current_model_index = model_index
                return model
        
        # Если все модели в кулдауне, используем первую
        logger.warning("Все модели Together AI в кулдауне, используем первую")
        self.current_model_index = 0
        return self.models[0]
    
    def set_key_cooldown(self, api_key: str, minutes: int = 1):
        """Устанавливает кулдаун для API ключа"""
        cooldown_end = datetime.now() + timedelta(minutes=minutes)
        self.key_cooldowns[api_key] = cooldown_end
        logger.info(f"API ключ Together AI заблокирован на {minutes} минут")
    
    def set_model_cooldown(self, model: str, minutes: int = 1):
        """Устанавливает кулдаун для модели"""
        cooldown_end = datetime.now() + timedelta(minutes=minutes)
        self.model_cooldowns[model] = cooldown_end
        logger.info(f"Модель Together AI {model} заблокирована на {minutes} минут")
    
    async def generate_content(
        self,
        prompt: str,
        max_tokens: int = 3500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Асинхронная генерация контента через Together AI API
        
        Args:
            prompt: Текст промпта
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            top_p: Top-p параметр
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатом генерации
        """
        
        # Пробуем разные комбинации ключей и моделей
        max_attempts = min(len(self.api_keys) * len(self.models), 10)

        for attempt in range(max_attempts):
            api_key = self.get_available_api_key()
            model = self.get_available_model()

            # Засекаем время начала запроса
            start_time = datetime.now()

            try:
                logger.info(f"Together AI попытка {attempt + 1}: ключ {self.current_key_index + 1}, модель {model}")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": False
                }
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=data
                    )
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limit для Together AI ключа {self.current_key_index + 1}")

                        # Логгируем rate limit
                        log_key_error(
                            provider="together",
                            key_id=api_key,
                            error_type="rate_limit",
                            error_message=f"Rate limit для ключа {self.current_key_index + 1}",
                            component="together_handler",
                            will_retry=True,
                            cooldown_minutes=1
                        )

                        self.set_key_cooldown(api_key, 1)
                        continue

                    if response.status_code == 400:
                        logger.warning(f"Ошибка модели Together AI {model}")

                        # Логгируем ошибку модели
                        log_key_error(
                            provider="together",
                            key_id=model,
                            error_type="model_error",
                            error_message=f"Ошибка модели {model}",
                            component="together_handler",
                            will_retry=True,
                            cooldown_minutes=1
                        )

                        self.set_model_cooldown(model, 1)
                        continue

                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"Together AI API error: {response.status_code} {error_text}")

                        # Логгируем API ошибку
                        log_key_error(
                            provider="together",
                            key_id=api_key,
                            error_type="api_error",
                            error_message=f"HTTP {response.status_code}: {error_text}",
                            component="together_handler",
                            will_retry=response.status_code >= 500
                        )

                        if response.status_code >= 500:
                            self.set_key_cooldown(api_key, 1)
                            continue
                        else:
                            raise TogetherAPIException(f"Together AI API error: {response.status_code} {error_text}")
                    
                    result = response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]

                        # Рассчитываем время ответа
                        response_time = (datetime.now() - start_time).total_seconds()

                        # Логгируем успешное использование
                        log_key_usage(
                            provider="together",
                            key_id=api_key,
                            component="together_handler",
                            model=model,
                            success=True,
                            response_time=response_time,
                            tokens_used=result.get("usage", {}).get("total_tokens", len(content))
                        )

                        return {
                            "content": content,
                            "model": model,
                            "usage": result.get("usage", {}),
                            "provider": "together"
                        }
                    else:
                        raise TogetherAPIException("Неожиданная структура ответа от Together AI")
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout для Together AI ключа {self.current_key_index + 1}")
                self.set_key_cooldown(api_key, 1)
                continue
                
            except Exception as e:
                logger.error(f"Ошибка Together AI: {str(e)}")
                if attempt < max_attempts - 1:
                    self.set_key_cooldown(api_key, 1)
                    continue
                else:
                    raise TogetherAPIException(f"Все попытки Together AI исчерпаны: {str(e)}")
        
        raise TogetherAPIException("Все API ключи и модели Together AI недоступны")
    
    def generate_content_sync(
        self,
        prompt: str,
        max_tokens: int = 3500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Синхронная генерация контента через Together AI API
        
        Args:
            prompt: Текст промпта
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            top_p: Top-p параметр
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатом генерации
        """
        return asyncio.run(self.generate_content(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs
        ))

# Глобальный экземпляр обработчика
together_handler = TogetherHandler()

# Функции для совместимости
async def generate_content_async(prompt: str, **kwargs) -> Dict[str, Any]:
    """Асинхронная генерация контента"""
    return await together_handler.generate_content(prompt, **kwargs)

def generate_content(prompt: str, **kwargs) -> Dict[str, Any]:
    """Синхронная генерация контента"""
    return together_handler.generate_content_sync(prompt, **kwargs)
