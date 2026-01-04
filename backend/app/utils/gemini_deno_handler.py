"""
Модуль для работы с API Google Gemini через прокси Deno Deploy.
Расширяет возможности базового GeminiHandler для стабильного доступа к API.
"""

import os
import json
import httpx
import logging
import time
import hashlib
import urllib3
from typing import Dict, List, Any, Optional
from .gemini_api import (
    GeminiHandler, 
    GeminiAPIException, 
    GeminiConnectionException, 
    GeminiAuthException, 
    GeminiRateLimitException
)

# Отключаем предупреждения о небезопасных подключениях
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем URL Deno Deploy прокси из переменных окружения
DENO_PROXY_URL = os.getenv("DENO_PROXY_URL", "https://important-chicken-26.deno.dev")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "87da1d5b1e9f44f795a94cc6d9abe9e3")

class DenoGeminiHandler(GeminiHandler):
    """
    Расширение класса GeminiHandler для работы через прокси Deno Deploy.
    Использует тот же интерфейс, что и базовый класс, но направляет
    запросы через улучшенный Deno прокси с поддержкой кэширования,
    ротации ключей и расширенной обработки ошибок.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 120, component_id: Optional[str] = None):
        """
        Инициализация обработчика для работы с Google Gemini API через Deno Deploy прокси.
        
        Args:
            api_key: Ключ API Google Gemini
            timeout: Таймаут запросов (в секундах)
            component_id: Идентификатор компонента приложения (для компонентных URL)
        """
        # Вызываем инициализатор родительского класса
        super().__init__(
            api_key=api_key, 
            timeout=timeout, 
            use_cloudflare=True,  # Указываем, что используем прокси
            component_id=component_id
        )
        
        # Устанавливаем URL Deno прокси
        self.deno_proxy_url = DENO_PROXY_URL
        if not self.deno_proxy_url:
            logger.warning("URL Deno прокси не задан в переменных окружения (DENO_PROXY_URL), "
                          "используем Cloudflare URL в качестве запасного варианта")
            self.deno_proxy_url = self.cloudflare_url
        
        # Токен авторизации для прокси
        self.auth_token = API_AUTH_TOKEN
        
        # Флаг для отслеживания использования кэша
        self.cache_hit = False
        
        # Принудительно отключаем проверку SSL для этого обработчика
        self.disable_ssl_verification = True
        self.disable_http2 = True
        
        logger.info(f"Инициализирован DenoGeminiHandler с URL: {self.deno_proxy_url}")
        logger.info(f"Проверка SSL отключена: {self.disable_ssl_verification}")
        logger.info(f"HTTP/2 отключен: {self.disable_http2}")
    
    def _get_proxy_url(self) -> str:
        """
        Формирует URL для Deno прокси с учетом компонента
        """
        if not self.deno_proxy_url:
            return None
            
        base_url = self.deno_proxy_url.rstrip('/')
        
        # Если указан компонент, формируем компонентный URL
        if self.component_id:
            return f"{base_url}/component/{self.component_id}"
        
        return base_url
    
    def _generate_cache_key(self, prompt: str, model: str) -> str:
        """
        Генерирует ключ для кэширования запроса
        
        Args:
            prompt: Текст запроса
            model: Название модели
            
        Returns:
            str: Хеш-ключ для кэширования
        """
        if not self.cache_enabled:
            return None
            
        # Формируем данные для хеширования
        key_data = f"{prompt}:{model}".encode('utf-8')
        return hashlib.md5(key_data).hexdigest()
    
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
        Генерация текста через прокси Deno Deploy.
        
        Args:
            prompt: Текст запроса для генерации
            model: Используемая модель
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            top_p: Top-p параметр (0.0-1.0)
            top_k: Top-k параметр
            safety_settings: Настройки безопасности
            stream: Включить потоковую генерацию (не поддерживается в текущей версии)
            request_api_key: API ключ для использования в конкретном запросе
            
        Returns:
            str: Сгенерированный текст
            
        Raises:
            GeminiConnectionException: При проблемах с подключением
            GeminiAuthException: При проблемах с аутентификацией
            GeminiRateLimitException: При превышении лимита запросов
            GeminiAPIException: При других ошибках API
        """
        # Получаем URL прокси
        proxy_url = self._get_proxy_url()
        if not proxy_url:
            raise GeminiConnectionException("URL прокси не настроен")
        
        # Используем переданный ключ API или базовый ключ из настроек
        api_key = request_api_key or self.api_key
        if not api_key:
            raise GeminiAuthException("API ключ не указан")
        
        # Формируем заголовки
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DenoGeminiHandler/1.0"
        }
        
        # Добавляем токен авторизации, если он настроен
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Генерируем ключ кэширования, если кэширование включено
        cache_key = self._generate_cache_key(prompt, model)
        
        # Формируем данные запроса
        request_data = {
            "model": model,
            "apiKey": api_key,
            "prompt": prompt,
            "temperature": temperature,
            "maxTokens": max_tokens,
            "topP": top_p,
            "topK": top_k
        }
        
        # Добавляем ключ кэширования, если он сгенерирован
        if cache_key:
            request_data["cacheKey"] = cache_key
            logger.debug(f"Используем кэширование с ключом: {cache_key[:8]}...")
        
        # Добавляем настройки безопасности, если они указаны
        if safety_settings:
            request_data["safetySettings"] = safety_settings
        
        # Отправляем запрос
        start_time = time.time()
        self.cache_hit = False  # Сбрасываем флаг кэш-хита
        
        try:
            # Настройки транспорта для избежания проблем с SSL
            transport = httpx.AsyncHTTPTransport(
                verify=False,  # Всегда отключаем проверку SSL для Deno Deploy
                http2=False,  # Отключаем HTTP/2
                retries=3
            )
            
            # Создаем клиент с отключенными проверками SSL
            async with httpx.AsyncClient(
                transport=transport,
                timeout=self.timeout,
                follow_redirects=True,
                verify=False,  # Еще раз подтверждаем отключение SSL проверки
                trust_env=False  # Игнорируем переменные окружения для прокси
            ) as client:
                logger.info(f"Отправка запроса к Deno Deploy на URL: {proxy_url}")
                logger.info(f"Длина промпта: {len(prompt)} символов")
                logger.info(f"Модель: {model}")
                
                # Отправляем запрос с отключенной проверкой SSL
                response = await client.post(
                    proxy_url,
                    json=request_data,
                    headers=headers
                )
                
                # Обработка ответа на основе статуса
                if response.status_code == 200:
                    # Проверяем, был ли это кэшированный ответ
                    if 'X-Cache' in response.headers and response.headers['X-Cache'] == 'HIT':
                        self.cache_hit = True
                        logger.info(f"Получен кэшированный ответ (X-Cache: {response.headers['X-Cache']})")
                    
                    # Проверяем время выполнения из заголовка
                    if 'X-Execution-Time' in response.headers:
                        logger.info(f"Время выполнения запроса: {response.headers['X-Execution-Time']}")
                    
                    # Логируем статистику запроса
                    total_time = time.time() - start_time
                    logger.info(f"Запрос через Deno прокси выполнен за {total_time:.2f} сек")
                    
                    # Парсим JSON ответ
                    try:
                        result = response.json()
                        
                        # Проверяем наличие ошибки в JSON
                        if 'error' in result:
                            error_msg = result.get('error', 'Неизвестная ошибка')
                            logger.error(f"Ошибка в JSON ответе: {error_msg}")
                            
                            if "API key not valid" in error_msg or "unauthorized" in error_msg.lower():
                                raise GeminiAuthException(f"Ошибка аутентификации: {error_msg}")
                            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                                raise GeminiRateLimitException(f"Превышение лимита запросов: {error_msg}")
                            else:
                                raise GeminiAPIException(f"Ошибка API: {error_msg}")
                        
                        # Извлекаем текст из ответа модели
                        if 'candidates' in result and result['candidates']:
                            candidate = result['candidates'][0]
                            if 'content' in candidate and 'parts' in candidate['content']:
                                parts = candidate['content']['parts']
                                if parts and 'text' in parts[0]:
                                    return parts[0]['text']
                        
                        # Если не удалось извлечь текст, возвращаем полный результат как JSON строку
                        logger.warning("Не удалось извлечь текст из ответа. Возвращаем полный JSON.")
                        return json.dumps(result, ensure_ascii=False)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка при разборе JSON ответа: {e}")
                        # Если не удалось распарсить JSON, возвращаем текстовый ответ
                        return response.text
                
                # Если статус не 200, обрабатываем ошибку
                elif response.status_code == 401 or response.status_code == 403:
                    logger.error(f"Ошибка аутентификации (HTTP {response.status_code}): {response.text}")
                    raise GeminiAuthException(f"Ошибка аутентификации: {response.text}")
                    
                elif response.status_code == 429:
                    logger.error(f"Превышение лимита запросов (HTTP 429): {response.text}")
                    raise GeminiRateLimitException(f"Превышение лимита запросов: {response.text}")
                    
                else:
                    logger.error(f"Ошибка запроса (HTTP {response.status_code}): {response.text}")
                    raise GeminiAPIException(f"Ошибка API: {response.text}")
                    
        except httpx.RequestError as e:
            logger.error(f"Ошибка соединения с Deno Deploy прокси: {e}")
            raise GeminiConnectionException(f"Ошибка соединения: {str(e)}")
            
        except httpx.TimeoutException as e:
            logger.error(f"Превышено время ожидания ответа от Deno Deploy прокси: {e}")
            raise GeminiConnectionException(f"Таймаут соединения: {str(e)}")
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при работе с Deno Deploy прокси: {e}")
            raise GeminiAPIException(f"Непредвиденная ошибка: {str(e)}")
    
    def was_cache_hit(self) -> bool:
        """
        Проверяет, был ли последний запрос получен из кэша
        
        Returns:
            bool: True, если ответ был получен из кэша
        """
        return self.cache_hit 