"""
Chutes AI API Handler
Модуль для работы с Chutes AI API
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

# Проверяем доступность Chutes AI API
CHUTES_AVAILABLE = True

class ChutesAPIException(Exception):
    """Исключение для ошибок Chutes API"""
    pass

class ChutesHandler:
    """Обработчик для Chutes AI API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента Chutes AI API

        Args:
            api_key: Ключ API Chutes AI
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("CHUTES_API_KEY")

        self.api_url = "https://llm.chutes.ai/v1/chat/completions"  # Исправленный URL
        self.timeout = 60

        # Приоритетные модели Chutes AI
        self.models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "gemini-2.0-flash-exp",
            "llama-3.3-70b-instruct"
        ]

        # Загружаем API ключи из переменных окружения (только 3 ключа)
        self.api_keys = []
        for i in range(1, 4):  # CHUTES_API_KEY_1 до CHUTES_API_KEY_3
            key = os.environ.get(f"CHUTES_API_KEY_{i}")
            if key and key != 'unused':
                self.api_keys.append(key)

        # Добавляем основной ключ если есть
        if self.api_key and self.api_key not in self.api_keys:
            self.api_keys.insert(0, self.api_key)

        logger.info(f"Инициализация ChutesHandler (доступно ключей: {len(self.api_keys)}/3)")
        
        # Состояние ключей и моделей
        self.key_cooldowns = {}  # Кулдауны для ключей
        self.model_cooldowns = {}  # Кулдауны для моделей
        self.current_key_index = 0
        self.current_model_index = 0
        
        # Специальная логика для Chutes - более длительные кулдауны из-за меньшего количества ключей
        self.default_key_cooldown = 2  # 2 минуты вместо 1
        self.default_model_cooldown = 1  # 1 минута для моделей

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
                        provider="chutes",
                        from_key=self._last_used_key,
                        to_key=api_key,
                        reason="key_rotation",
                        component="chutes_handler"
                    )

                self.current_key_index = key_index
                self._last_used_key = api_key
                return api_key

        # Если все ключи в кулдауне, используем первый (у нас только 3 ключа)
        logger.warning("Все 3 API ключа Chutes в кулдауне, используем первый")
        log_key_error(
            provider="chutes",
            key_id="all_keys",
            error_type="all_keys_in_cooldown",
            error_message="Все 3 API ключа Chutes в кулдауне",
            component="chutes_handler"
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
        logger.warning("Все модели Chutes в кулдауне, используем первую")
        self.current_model_index = 0
        return self.models[0]
    
    def set_key_cooldown(self, api_key: str, minutes: Optional[int] = None):
        """Устанавливает кулдаун для API ключа"""
        if minutes is None:
            minutes = self.default_key_cooldown
            
        cooldown_end = datetime.now() + timedelta(minutes=minutes)
        self.key_cooldowns[api_key] = cooldown_end
        logger.info(f"API ключ Chutes заблокирован на {minutes} минут (осталось {len(self.api_keys)} ключей)")
    
    def set_model_cooldown(self, model: str, minutes: Optional[int] = None):
        """Устанавливает кулдаун для модели"""
        if minutes is None:
            minutes = self.default_model_cooldown
            
        cooldown_end = datetime.now() + timedelta(minutes=minutes)
        self.model_cooldowns[model] = cooldown_end
        logger.info(f"Модель Chutes {model} заблокирована на {minutes} минут")
    
    async def generate_content(
        self,
        prompt: str,
        max_tokens: int = 3500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Асинхронная генерация контента через Chutes AI API
        
        Args:
            prompt: Текст промпта
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            top_p: Top-p параметр
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с результатом генерации
        """
        
        # Ограничиваем количество попыток из-за малого количества ключей
        max_attempts = min(len(self.api_keys) * 2, 6)  # Максимум 6 попыток
        
        for attempt in range(max_attempts):
            api_key = self.get_available_api_key()
            model = self.get_available_model()

            # Засекаем время начала запроса
            start_time = datetime.now()

            try:
                logger.info(f"Chutes попытка {attempt + 1}: ключ {self.current_key_index + 1}/3, модель {model}")

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
                        logger.warning(f"Rate limit для Chutes ключа {self.current_key_index + 1}/3")
                        self.set_key_cooldown(api_key, 2)  # Увеличенный кулдаун
                        continue
                    
                    if response.status_code == 400:
                        logger.warning(f"Ошибка модели Chutes {model}")
                        self.set_model_cooldown(model, 1)
                        continue
                    
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"Chutes API error: {response.status_code} {error_text}")
                        
                        if response.status_code >= 500:
                            self.set_key_cooldown(api_key, 2)  # Увеличенный кулдаун
                            continue
                        else:
                            raise ChutesAPIException(f"Chutes API error: {response.status_code} {error_text}")
                    
                    result = response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]

                        # Рассчитываем время ответа
                        response_time = (datetime.now() - start_time).total_seconds()

                        # Логгируем успешное использование
                        log_key_usage(
                            provider="chutes",
                            key_id=api_key,
                            component="chutes_handler",
                            model=model,
                            success=True,
                            response_time=response_time,
                            tokens_used=result.get("usage", {}).get("total_tokens", len(content))
                        )

                        return {
                            "content": content,
                            "model": model,
                            "usage": result.get("usage", {}),
                            "provider": "chutes"
                        }
                    else:
                        raise ChutesAPIException("Неожиданная структура ответа от Chutes")
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout для Chutes ключа {self.current_key_index + 1}/3")
                self.set_key_cooldown(api_key, 2)  # Увеличенный кулдаун
                continue
                
            except Exception as e:
                logger.error(f"Ошибка Chutes: {str(e)}")
                if attempt < max_attempts - 1:
                    self.set_key_cooldown(api_key, 1)
                    continue
                else:
                    raise ChutesAPIException(f"Все попытки Chutes исчерпаны: {str(e)}")
        
        raise ChutesAPIException("Все 3 API ключа Chutes недоступны")
    
    def generate_content_sync(
        self,
        prompt: str,
        max_tokens: int = 3500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Синхронная генерация контента через Chutes AI API
        
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
chutes_handler = ChutesHandler()

# Функции для совместимости
async def generate_content_async(prompt: str, **kwargs) -> Dict[str, Any]:
    """Асинхронная генерация контента"""
    return await chutes_handler.generate_content(prompt, **kwargs)

def generate_content(prompt: str, **kwargs) -> Dict[str, Any]:
    """Синхронная генерация контента"""
    return chutes_handler.generate_content_sync(prompt, **kwargs)
