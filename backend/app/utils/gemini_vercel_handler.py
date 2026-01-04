"""
Модуль для работы с API Google Gemini через прокси Vercel.
Позволяет использовать Vercel вместо Cloudflare/Deno Deploy для стабильного доступа к API.
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Any, Optional
from .gemini_api import (
    GeminiHandler, 
    GeminiAPIException, 
    GeminiConnectionException, 
    GeminiAuthException, 
    GeminiRateLimitException
)

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VercelGeminiHandler(GeminiHandler):
    """
    Расширение класса GeminiHandler для работы через прокси Vercel.
    Использует тот же интерфейс, что и базовый класс, но перенаправляет 
    запросы через Vercel вместо Cloudflare/Deno Deploy.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 120, 
                 component_id: Optional[str] = None):
        """
        Инициализация обработчика Vercel для Gemini API
        
        Args:
            api_key: Ключ API Google Gemini
            timeout: Таймаут запросов (в секундах)
            component_id: Идентификатор компонента приложения для компонентных URL
        """
        # Инициализируем родительский класс с включенным проксированием
        super().__init__(
            api_key=api_key, 
            timeout=timeout, 
            use_cloudflare=True,  # Всегда включаем прокси
            use_socks5=False,     # Отключаем SOCKS5
            component_id=component_id
        )
        
        # Получаем URL для Vercel из переменной окружения
        self.vercel_url = os.getenv("VERCEL_PROXY_URL", "")
        if not self.vercel_url:
            logger.warning("URL Vercel прокси не задан в переменной окружения VERCEL_PROXY_URL. "
                          "Используем стандартный URL Cloudflare.")
        else:
            # Переопределяем URL Cloudflare для использования Vercel
            self.cloudflare_url = self.vercel_url
            logger.info(f"Инициализирован VercelGeminiHandler с URL: {self.vercel_url}")
            
        # Получаем токен авторизации для Vercel
        self.auth_token = os.getenv("API_AUTH_TOKEN", "")
            
    def _get_proxy_url(self) -> Optional[str]:
        """
        Возвращает URL для прокси (переопределяет метод родительского класса)
        
        Returns:
            URL прокси или None, если прокси не настроен
        """
        return self.vercel_url or self.cloudflare_url
    
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
        Генерация текста через Vercel прокси.
        Переопределяет метод _generate_with_cloudflare родительского класса.
        
        Args:
            prompt: Текст запроса
            model: Модель Gemini
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            top_p: Параметр top_p
            top_k: Параметр top_k
            safety_settings: Настройки безопасности
            stream: Потоковая генерация (не поддерживается)
            request_api_key: API ключ для запроса (если отличается от ключа в конфигурации)
            
        Returns:
            Сгенерированный текст
            
        Raises:
            GeminiConnectionException: При ошибке соединения
            GeminiAuthException: При ошибке аутентификации
            GeminiRateLimitException: При превышении лимита запросов
            GeminiAPIException: При других ошибках API
        """
        import json
        import httpx
            
        # Для потоковой генерации заглушка
        if stream:
            raise NotImplementedError("Потоковая генерация через Vercel прокси не поддерживается")
            
        # Получаем URL для Vercel с учетом компонента
        proxy_url = self._get_proxy_url()
        
        if not proxy_url:
            raise GeminiConnectionException("URL для Vercel прокси не настроен")
            
        # Используем переданный ключ или ключ по умолчанию
        api_key = request_api_key or self.api_key
            
        # Данные запроса
        request_data = {
            "model": model,
            "apiKey": api_key,
            "prompt": prompt,
            "temperature": temperature,
            "maxTokens": max_tokens,
            "topP": top_p,
            "topK": top_k
        }
            
        # Добавляем настройки безопасности, если они указаны
        if safety_settings:
            request_data["safetySettings"] = safety_settings
            
        # Заголовки запроса
        headers = {
            "Content-Type": "application/json",
        }
            
        # Токен авторизации для Vercel функции, если он настроен
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        # Если указан компонент, добавляем его в заголовки
        if self.component_id:
            headers["X-Component-ID"] = self.component_id
            
        try:
            # Настройки транспорта для обхода проблем с SSL
            transport = httpx.AsyncHTTPTransport(
                verify=not self.disable_ssl_verification,
                http2=not self.disable_http2
            )
                
            # Выполняем запрос с таймаутом
            async with httpx.AsyncClient(
                transport=transport,
                timeout=float(self.timeout),
                follow_redirects=True
            ) as client:
                # Отправляем запрос
                response = await client.post(
                    proxy_url,
                    headers=headers,
                    json=request_data,
                    timeout=self.timeout
                )
                    
                # Проверяем статус ответа
                if response.status_code == 200:
                    try:
                        # Разбираем JSON
                        data = response.json()
                        
                        # Извлекаем текст из структуры ответа
                        if "candidates" in data and data["candidates"] and data["candidates"][0]["content"]:
                            parts = data["candidates"][0]["content"]["parts"]
                            if parts and len(parts) > 0:
                                result_text = parts[0]["text"]
                                return result_text.strip()
                            
                        # Если текст не найден в ожидаемой структуре
                        logger.warning("Текст не найден в структуре ответа от API")
                        return json.dumps(data)
                        
                    except json.JSONDecodeError:
                        # Если ответ не в формате JSON, возвращаем его как есть
                        logger.warning("Ответ от API не в формате JSON")
                        return response.text
                
                elif response.status_code == 401 or response.status_code == 403:
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
        
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {e}")
            raise GeminiAPIException(f"Непредвиденная ошибка: {e}") 