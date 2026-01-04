"""
Модуль для работы с Groq Cloud API через прокси Cloudflare Workers.
Аналог gemini_api.py, но для Groq API через систему прокси.
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Any, Optional
import asyncio

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения для Groq прокси
GROQ_PROXY_ENABLED = os.getenv("USE_GROQ_PROXY", "false").lower() == "true"
GROQ_PROXY_URL = os.getenv("GROQ_PROXY_URL", "https://aiteachers.netlify.app/api")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Настройки таймаутов
DEFAULT_TIMEOUT = 120
MAX_RETRIES = 3

class GroqProxyException(Exception):
    """Базовое исключение для Groq Proxy"""
    pass

class GroqProxyConnectionException(GroqProxyException):
    """Исключение при проблемах с соединением"""
    pass

class GroqProxyAuthException(GroqProxyException):
    """Исключение при проблемах с авторизацией"""
    pass

class GroqProxyRateLimitException(GroqProxyException):
    """Исключение при превышении лимита запросов"""
    pass

class GroqProxyHandler:
    """
    Класс для работы с Groq Cloud API через Cloudflare Workers прокси.
    Аналогичен GeminiHandler, но работает с Groq API.
    """
    
    def __init__(self, 
                 component_id: str,
                 api_key: Optional[str] = None, 
                 timeout: int = DEFAULT_TIMEOUT,
                 proxy_url: Optional[str] = None):
        """
        Инициализация обработчика Groq прокси
        
        Args:
            component_id: Идентификатор компонента (groq-exercises, groq-lesson-planner, etc.)
            api_key: Ключ API Groq Cloud
            timeout: Таймаут запросов (в секундах)
            proxy_url: URL прокси сервера
        """
        self.component_id = component_id
        self.api_key = api_key or GROQ_API_KEY
        self.timeout = timeout
        self.proxy_url = proxy_url or GROQ_PROXY_URL
        
        # Проверяем наличие API ключа
        if not self.api_key:
            logger.warning("API ключ Groq не найден в переменных окружения")
            self._available = False
        else:
            self._available = True
            logger.info(f"GroqProxyHandler инициализирован для компонента: {component_id}")
        
        # Настройки для HTTP клиента
        self.client_config = {
            "timeout": httpx.Timeout(timeout),
            "follow_redirects": True,
            "verify": True
        }
        
        # Статистика использования
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_errors": 0
        }
    
    def is_available(self) -> bool:
        """Проверяет доступность Groq прокси"""
        return self._available and bool(self.api_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования"""
        return {
            "component_id": self.component_id,
            "proxy_url": self.proxy_url,
            "available": self.is_available(),
            **self.stats
        }
    
    async def _make_request(self, 
                           endpoint: str,
                           data: Dict[str, Any],
                           retries: int = MAX_RETRIES) -> Dict[str, Any]:
        """
        Выполняет запрос к Groq API через прокси
        
        Args:
            endpoint: Эндпоинт API (например, 'chat/completions')
            data: Данные запроса
            retries: Количество попыток
            
        Returns:
            Ответ от API
        """
        if not self.is_available():
            raise GroqProxyException("Groq прокси недоступен")
        
        # Формируем URL для запроса через компонентный роутер
        url = f"{self.proxy_url}/{self.component_id}/groq/{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "X-Groq-API-Key": self.api_key,
            "X-Component-ID": self.component_id,
            "User-Agent": "GroqProxyHandler/1.0"
        }
        
        # Добавляем токен авторизации, если он есть
        auth_token = os.getenv("API_AUTH_TOKEN")
        if auth_token:
            headers["X-Auth-Token"] = auth_token
        
        self.stats["total_requests"] += 1
        
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(**self.client_config) as client:
                    logger.info(f"Отправка запроса к Groq прокси (попытка {attempt + 1}/{retries})")
                    logger.info(f"URL: {url}")
                    logger.info(f"Component: {self.component_id}")
                    
                    response = await client.post(
                        url,
                        json=data,
                        headers=headers
                    )
                    
                    # Обрабатываем различные статусы ответа
                    if response.status_code == 200:
                        self.stats["successful_requests"] += 1
                        result = response.json()
                        logger.info(f"Успешный ответ от Groq прокси, длина: {len(str(result))}")
                        return result
                    
                    elif response.status_code == 429:
                        self.stats["rate_limit_errors"] += 1
                        logger.warning(f"Превышен лимит запросов Groq (попытка {attempt + 1})")
                        
                        if attempt < retries - 1:
                            # Экспоненциальная задержка
                            wait_time = (2 ** attempt) * 5  # 5, 10, 20 секунд
                            logger.info(f"Ожидание {wait_time} секунд перед повторной попыткой")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise GroqProxyRateLimitException(
                                f"Превышен лимит запросов Groq после {retries} попыток"
                            )
                    
                    elif response.status_code == 401:
                        raise GroqProxyAuthException("Ошибка авторизации Groq API")
                    
                    elif response.status_code == 404:
                        raise GroqProxyException(f"Компонент {self.component_id} не найден")
                    
                    else:
                        error_text = response.text
                        logger.error(f"Ошибка Groq прокси: {response.status_code} - {error_text}")
                        
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                            continue
                        else:
                            raise GroqProxyException(
                                f"Ошибка Groq прокси: {response.status_code} - {error_text}"
                            )
            
            except httpx.TimeoutException:
                logger.error(f"Таймаут запроса к Groq прокси (попытка {attempt + 1})")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise GroqProxyConnectionException("Таймаут соединения с Groq прокси")
            
            except httpx.RequestError as e:
                logger.error(f"Ошибка соединения с Groq прокси: {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise GroqProxyConnectionException(f"Ошибка соединения: {str(e)}")
        
        self.stats["failed_requests"] += 1
        raise GroqProxyException("Все попытки запроса к Groq прокси исчерпаны")
    
    async def generate_content(self,
                             prompt: str,
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: int = 2048,
                             top_p: float = 1.0,
                             **kwargs) -> str:
        """
        Генерирует контент с использованием Groq API через прокси
        
        Args:
            prompt: Текст запроса для генерации
            model: Модель для использования (если не указана, будет выбрана автоматически)
            temperature: Температура генерации (0.0-2.0)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Top-p параметр (0.0-1.0)
            **kwargs: Дополнительные параметры
            
        Returns:
            Сгенерированный текст
        """
        if not self.is_available():
            raise GroqProxyException("Groq прокси недоступен")
        
        # Подготавливаем данные запроса в формате OpenAI API
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": False
        }
        
        # Добавляем модель, если указана
        if model:
            request_data["model"] = model
        
        logger.info(f"Генерация контента через Groq прокси ({self.component_id})")
        logger.info(f"Параметры: temperature={temperature}, max_tokens={max_tokens}")
        
        try:
            # Выполняем запрос
            response = await self._make_request("chat/completions", request_data)
            
            # Извлекаем сгенерированный текст
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                
                # Логируем информацию об использованной модели
                if "model" in response:
                    logger.info(f"Использована модель: {response['model']}")
                
                # Логируем статистику токенов
                if "usage" in response:
                    usage = response["usage"]
                    logger.info(f"Использовано токенов: {usage.get('total_tokens', 'неизвестно')}")
                
                logger.info(f"Контент успешно сгенерирован, длина: {len(content)}")
                return content
            else:
                logger.error("Пустой ответ от Groq API")
                raise GroqProxyException("Пустой ответ от Groq API")
        
        except Exception as e:
            logger.error(f"Ошибка при генерации контента через Groq прокси: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Тестирует соединение с Groq прокси
        
        Returns:
            True если соединение работает, False иначе
        """
        try:
            # Простой тестовый запрос
            await self.generate_content(
                prompt="Ответь одним словом: 'Работает'",
                max_tokens=10
            )
            logger.info("Тест соединения с Groq прокси успешен")
            return True
        except Exception as e:
            logger.error(f"Тест соединения с Groq прокси не удался: {str(e)}")
            return False

# Проверяем доступность Groq прокси
GROQ_PROXY_AVAILABLE = bool(GROQ_API_KEY and GROQ_PROXY_URL)

if GROQ_PROXY_AVAILABLE:
    logger.info("Groq прокси доступен")
else:
    logger.warning("Groq прокси недоступен - проверьте настройки GROQ_API_KEY и GROQ_PROXY_URL")
