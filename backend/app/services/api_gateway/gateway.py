"""
Основной API Gateway класс с fallback логикой между провайдерами
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
import logging

from .models import (
    APIRequest, APIResponse, ContentType, ProviderConfig, 
    ProviderStats, ProviderType
)
from .config import get_provider_config
from .providers import (
    BaseProvider, DirectProvider, NetlifyProvider
)


class APIGateway:
    """
    Основной API Gateway с поддержкой fallback логики.
    
    Логика работы:
    1. Для каждого типа контента (текст/изображения) есть список провайдеров по приоритету
    2. Внутри каждого провайдера есть fallback на модели
    3. При неудаче провайдера переходим к следующему в списке
    4. Ведется статистика и мониторинг здоровья провайдеров
    """
    
    def __init__(self):
        self.logger = logging.getLogger("api_gateway")
        self.text_providers: List[BaseProvider] = []
        self.image_providers: List[BaseProvider] = []
        self.provider_stats: Dict[str, ProviderStats] = {}
        
        # Инициализируем провайдеры
        self._initialize_providers()
        
        self.logger.info("API Gateway инициализирован")
    
    def _initialize_providers(self):
        """Инициализация провайдеров"""
        provider_classes = {
            ProviderType.DIRECT: DirectProvider,
            ProviderType.NETLIFY: NetlifyProvider
        }
        
        # Инициализация провайдеров для текста
        text_configs = get_provider_config(ContentType.TEXT)
        for config in text_configs:
            try:
                provider_class = provider_classes[config.type]
                provider = provider_class(config)
                self.text_providers.append(provider)
                self.provider_stats[provider.name] = ProviderStats(provider_name=provider.name)
                self.logger.info(f"Инициализирован текстовый провайдер: {provider.name}")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации провайдера {config.name}: {e}")
        
        # Инициализация провайдеров для изображений
        image_configs = get_provider_config(ContentType.IMAGE)
        for config in image_configs:
            try:
                provider_class = provider_classes[config.type]
                provider = provider_class(config)
                self.image_providers.append(provider)
                self.provider_stats[provider.name] = ProviderStats(provider_name=provider.name)
                self.logger.info(f"Инициализирован провайдер изображений: {provider.name}")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации провайдера {config.name}: {e}")
        
        # Сортируем провайдеры по приоритету
        self.text_providers.sort(key=lambda p: p.config.priority)
        self.image_providers.sort(key=lambda p: p.config.priority)
    
    async def generate_content(
        self,
        endpoint: str,
        data: Dict[str, Any],
        api_keys: Dict[str, str],
        content_type: ContentType = ContentType.TEXT,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> APIResponse:
        """
        Основной метод генерации контента с fallback логикой
        """
        # Создаем объект запроса
        request = APIRequest(
            endpoint=endpoint,
            content_type=content_type,
            data=data,
            api_keys=api_keys,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model,
            timeout=timeout,
            max_retries=max_retries
        )
        
        self.logger.info(f"Генерация контента: {endpoint} ({content_type.value})")
        
        # Выбираем провайдеры в зависимости от типа контента
        providers = self._get_providers_for_content_type(content_type, preferred_provider)
        
        if not providers:
            return APIResponse(
                success=False,
                error=f"Нет доступных провайдеров для типа контента {content_type.value}",
                response_time=0
            )
        
        start_time = time.time()
        last_error = None
        
        # Пробуем провайдеры в порядке приоритета
        for provider in providers:
            try:
                self.logger.info(f"Пробуем провайдер: {provider.name}")
                
                # Быстрая проверка здоровья провайдера
                if not await self._quick_health_check(provider):
                    self.logger.warning(f"Провайдер {provider.name} не прошел health check")
                    continue
                
                # Вызываем провайдер
                response = await provider.call_api(request)
                
                if response.success:
                    # Успешный ответ
                    response.response_time = time.time() - start_time
                    
                    # Обновляем статистику
                    self._update_provider_stats(provider.name, response)
                    
                    self.logger.info(f"Успешная генерация через {provider.name} (модель: {response.model_name})")
                    return response
                else:
                    # Провайдер вернул неуспешный ответ
                    last_error = Exception(response.error or "Unknown provider error")
                    self.logger.warning(f"Провайдер {provider.name} вернул ошибку: {response.error}")
                    
                    # Обновляем статистику
                    self._update_provider_stats(provider.name, response)
                    
                    continue
                    
            except Exception as e:
                last_error = e
                self.logger.error(f"Ошибка с провайдером {provider.name}: {e}")
                
                # Создаем ответ с ошибкой для статистики
                error_response = APIResponse(
                    success=False,
                    error=str(e),
                    provider_name=provider.name,
                    response_time=time.time() - start_time
                )
                self._update_provider_stats(provider.name, error_response)
                
                continue
        
        # Все провайдеры не удались
        final_response = APIResponse(
            success=False,
            error=f"Все провайдеры для {content_type.value} недоступны",
            error_details={'last_error': str(last_error) if last_error else 'Unknown'},
            response_time=time.time() - start_time
        )
        
        self.logger.error(f"Генерация контента не удалась: {final_response.error}")
        return final_response
    
    def _get_providers_for_content_type(
        self, 
        content_type: ContentType, 
        preferred_provider: Optional[str] = None
    ) -> List[BaseProvider]:
        """Получить провайдеры для типа контента с учетом предпочтений"""
        if content_type == ContentType.TEXT:
            providers = self.text_providers.copy()
        elif content_type == ContentType.IMAGE:
            providers = self.image_providers.copy()
        else:
            return []
        
        # Если указан предпочтительный провайдер, ставим его первым
        if preferred_provider:
            preferred = [p for p in providers if p.name == preferred_provider]
            others = [p for p in providers if p.name != preferred_provider]
            providers = preferred + others
        
        return providers
    
    async def _quick_health_check(self, provider: BaseProvider) -> bool:
        """Быстрая проверка здоровья провайдера"""
        try:
            # Используем таймаут для health check
            return await asyncio.wait_for(provider.health_check(), timeout=5)
        except asyncio.TimeoutError:
            self.logger.warning(f"Health check провайдера {provider.name} превысил таймаут")
            return False
        except Exception as e:
            self.logger.warning(f"Health check провайдера {provider.name} не удался: {e}")
            return False
    
    def _update_provider_stats(self, provider_name: str, response: APIResponse):
        """Обновить статистику провайдера"""
        if provider_name in self.provider_stats:
            self.provider_stats[provider_name].update_stats(response)
    
    async def get_provider_health_status(self) -> Dict[str, Any]:
        """Получить статус здоровья всех провайдеров"""
        health_status = {
            'text_providers': {},
            'image_providers': {},
            'overall_health': True
        }
        
        # Проверяем текстовые провайдеры
        for provider in self.text_providers:
            try:
                is_healthy = await asyncio.wait_for(provider.health_check(), timeout=10)
                health_status['text_providers'][provider.name] = {
                    'healthy': is_healthy,
                    'available_models': len(provider.config.get_available_models()),
                    'total_models': len(provider.config.models)
                }
                if not is_healthy:
                    health_status['overall_health'] = False
            except Exception as e:
                health_status['text_providers'][provider.name] = {
                    'healthy': False,
                    'error': str(e)
                }
                health_status['overall_health'] = False
        
        # Проверяем провайдеры изображений
        for provider in self.image_providers:
            try:
                is_healthy = await asyncio.wait_for(provider.health_check(), timeout=10)
                health_status['image_providers'][provider.name] = {
                    'healthy': is_healthy,
                    'available_models': len(provider.config.get_available_models()),
                    'total_models': len(provider.config.models)
                }
            except Exception as e:
                health_status['image_providers'][provider.name] = {
                    'healthy': False,
                    'error': str(e)
                }
        
        return health_status
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить общую статистику API Gateway"""
        return {
            'text_providers_count': len(self.text_providers),
            'image_providers_count': len(self.image_providers),
            'provider_stats': {
                name: {
                    'total_requests': stats.total_requests,
                    'successful_requests': stats.successful_requests,
                    'failed_requests': stats.failed_requests,
                    'success_rate': stats.get_success_rate(),
                    'average_response_time': stats.average_response_time,
                    'total_tokens_used': stats.total_tokens_used
                }
                for name, stats in self.provider_stats.items()
            }
        }
    
    async def cleanup(self):
        """Очистка ресурсов API Gateway"""
        self.logger.info("Очистка API Gateway...")
        
        # Очищаем провайдеры
        for provider in self.text_providers + self.image_providers:
            if hasattr(provider, 'cleanup'):
                try:
                    await provider.cleanup()
                except Exception as e:
                    self.logger.warning(f"Ошибка очистки провайдера {provider.name}: {e}")
        
        self.logger.info("API Gateway очищен")
