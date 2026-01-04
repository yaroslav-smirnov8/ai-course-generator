"""
Базовый провайдер с fallback логикой на модели
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import asyncio
import time
from datetime import datetime, timedelta

from ..models import (
    ProviderConfig, ModelConfig, APIRequest, APIResponse, 
    ModelStatus, ProviderStats, ContentType
)
from ..config import update_model_cooldown, mark_model_success


class BaseProvider(ABC):
    """
    Базовый класс провайдера с поддержкой fallback на модели.
    
    Логика fallback:
    1. Пробуем модели в порядке приоритета внутри провайдера
    2. При ошибке модели - ставим её в cooldown и пробуем следующую
    3. Если все модели недоступны - провайдер считается недоступным
    """
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        self.logger = logging.getLogger(f"api_gateway.{self.name}")
        self.stats = ProviderStats(provider_name=self.name)
        
        # Кэш для проверки здоровья
        self._last_health_check = None
        self._health_check_result = True
        self._health_check_ttl = 60  # секунд
    
    @abstractmethod
    async def _call_model_api(
        self, 
        model: ModelConfig,
        endpoint: str,
        data: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Вызов API конкретной модели.
        Должен быть реализован в наследниках.
        """
        pass
    
    @abstractmethod
    async def _health_check_implementation(self) -> bool:
        """
        Реализация проверки здоровья провайдера.
        Должна быть реализована в наследниках.
        """
        pass
    
    async def call_api(
        self, 
        request: APIRequest
    ) -> APIResponse:
        """
        Основной метод вызова API с fallback на модели
        """
        start_time = time.time()
        available_models = self.config.get_available_models()
        
        if not available_models:
            return APIResponse(
                success=False,
                error="Нет доступных моделей",
                provider_name=self.name,
                response_time=time.time() - start_time
            )
        
        last_error = None
        
        # Пробуем модели в порядке приоритета
        for model in available_models:
            try:
                self.logger.info(f"Пробуем модель {model.name} в провайдере {self.name}")
                
                # Подготавливаем заголовки с API ключами
                headers = self._prepare_headers(request.api_keys, model)
                
                # Вызываем API модели с повторными попытками
                result = await self._call_model_with_retry(
                    model, request.endpoint, request.data, headers
                )
                
                if result.get('success') or result.get('text') or result.get('content'):
                    # Успешный вызов
                    response = APIResponse(
                        success=True,
                        content=result.get('text', result.get('content', '')),
                        provider_name=self.name,
                        model_name=model.name,
                        response_time=time.time() - start_time,
                        tokens_used=result.get('usage', {}).get('total_tokens', 0),
                        metadata=result.get('metadata', {}),
                        image_url=result.get('image_url')
                    )
                    
                    # Отмечаем успех модели
                    mark_model_success(self.name, model.name, request.content_type)
                    
                    # Обновляем статистику
                    self.stats.update_stats(response)
                    self.config.successful_requests += 1
                    
                    return response
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"Ошибка с моделью {model.name}: {e}")
                
                # Ставим модель в cooldown при определенных ошибках
                if self._should_cooldown_model(e):
                    cooldown_minutes = self._get_cooldown_minutes(e)
                    update_model_cooldown(
                        self.name, model.name, request.content_type, cooldown_minutes
                    )
                    self.logger.info(f"Модель {model.name} поставлена в cooldown на {cooldown_minutes} минут")
                
                continue
        
        # Все модели не удались
        response = APIResponse(
            success=False,
            error=f"Все модели провайдера {self.name} недоступны",
            error_details={'last_error': str(last_error) if last_error else 'Unknown'},
            provider_name=self.name,
            response_time=time.time() - start_time
        )
        
        self.stats.update_stats(response)
        self.config.failed_requests += 1
        
        return response
    
    async def _call_model_with_retry(
        self,
        model: ModelConfig,
        endpoint: str,
        data: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Вызов модели с повторными попытками"""
        last_error = None
        
        for attempt in range(model.retry_count):
            try:
                self.logger.debug(f"Попытка {attempt + 1}/{model.retry_count} для модели {model.name}")
                
                result = await asyncio.wait_for(
                    self._call_model_api(model, endpoint, data, headers),
                    timeout=model.timeout
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = Exception(f"Timeout {model.timeout}s для модели {model.name}")
                self.logger.warning(f"Timeout для модели {model.name} на попытке {attempt + 1}")
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Ошибка модели {model.name} на попытке {attempt + 1}: {e}")
                
                # Небольшая задержка между попытками
                if attempt < model.retry_count - 1:
                    await asyncio.sleep(min(2 ** attempt, 10))  # Exponential backoff
        
        raise last_error or Exception(f"Все попытки для модели {model.name} не удались")
    
    def _prepare_headers(self, api_keys: Dict[str, str], model: ModelConfig) -> Dict[str, str]:
        """Подготовка заголовков с API ключами"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AITeachers-WebApp/1.0'
        }
        
        # Добавляем API ключи в заголовки (как в воркерах)
        provider_type = model.provider_type.lower()
        
        if provider_type == 'gemini' and api_keys.get('gemini'):
            headers['X-Gemini-API-Key'] = api_keys['gemini']
        elif provider_type == 'groq' and api_keys.get('groq'):
            headers['X-Groq-API-Key'] = api_keys['groq']
        elif provider_type == 'openrouter' and api_keys.get('openrouter'):
            headers['X-OpenRouter-API-Key'] = api_keys['openrouter']
        elif provider_type == 'llm7' and api_keys.get('llm7'):
            headers['X-LLM7-API-Key'] = api_keys['llm7']
        elif provider_type == 'together' and api_keys.get('together'):
            headers['X-Together-API-Key'] = api_keys['together']
        elif provider_type == 'cerebras' and api_keys.get('cerebras'):
            headers['X-Cerebras-API-Key'] = api_keys['cerebras']
        
        # Добавляем специфичные заголовки модели
        headers.update(model.headers)
        
        return headers
    
    def _should_cooldown_model(self, error: Exception) -> bool:
        """Определить, нужно ли ставить модель в cooldown"""
        error_str = str(error).lower()
        
        # Rate limiting
        if 'rate limit' in error_str or '429' in error_str:
            return True
            
        # Server errors (5xx)
        if any(code in error_str for code in ['500', '502', '503', '504']):
            return True
            
        # Timeout errors
        if 'timeout' in error_str:
            return True
            
        return False
    
    def _get_cooldown_minutes(self, error: Exception) -> int:
        """Получить время cooldown в зависимости от ошибки"""
        error_str = str(error).lower()
        
        if 'rate limit' in error_str or '429' in error_str:
            return 10  # 10 минут для rate limit
        elif 'timeout' in error_str:
            return 5   # 5 минут для timeout
        else:
            return 3   # 3 минуты для других ошибок
    
    async def health_check(self) -> bool:
        """Проверка здоровья провайдера с кэшированием"""
        now = datetime.utcnow()
        
        # Используем кэшированный результат если он свежий
        if (self._last_health_check and 
            (now - self._last_health_check).total_seconds() < self._health_check_ttl):
            return self._health_check_result
        
        try:
            self._health_check_result = await self._health_check_implementation()
            self._last_health_check = now
            return self._health_check_result
            
        except Exception as e:
            self.logger.warning(f"Health check провайдера {self.name} не удался: {e}")
            self._health_check_result = False
            self._last_health_check = now
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику провайдера"""
        return {
            'provider_name': self.name,
            'total_requests': self.stats.total_requests,
            'successful_requests': self.stats.successful_requests,
            'failed_requests': self.stats.failed_requests,
            'success_rate': self.stats.get_success_rate(),
            'average_response_time': self.stats.average_response_time,
            'total_tokens_used': self.stats.total_tokens_used,
            'available_models': len(self.config.get_available_models()),
            'total_models': len(self.config.models),
            'model_stats': self.stats.model_stats
        }
