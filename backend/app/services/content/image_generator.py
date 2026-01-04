"""
Unified Image Generation Service
Объединенный сервис генерации изображений с приоритетом Flux Schnell
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Импортируем систему логгирования ключей
try:
    from ...utils.api_keys_logger import log_provider_fallback
except ImportError:
    def log_provider_fallback(*args, **kwargs):
        pass

class ImageGenerationService:
    """Сервис генерации изображений с приоритетной системой провайдеров"""
    
    def __init__(self):
        self.providers = []
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Инициализирует провайдеры в порядке приоритета"""
        
        # 1. Together AI Flux Schnell (приоритет #1 - бесплатный и быстрый)
        try:
            from ...utils.together_images_api import TogetherImagesHandler, TOGETHER_IMAGES_AVAILABLE
            
            if TOGETHER_IMAGES_AVAILABLE:
                flux_handler = TogetherImagesHandler()
                if flux_handler.is_available():
                    self.providers.append({
                        'name': 'flux_schnell',
                        'handler': flux_handler,
                        'priority': 1,
                        'description': 'Together AI Flux Schnell (Free)',
                        'supports_local_save': True
                    })
                    logger.info("✅ Flux Schnell provider initialized")
                else:
                    logger.warning("⚠️ Flux Schnell provider unavailable (no API keys)")
            else:
                logger.warning("⚠️ Flux Schnell provider unavailable (library missing)")
                
        except ImportError as e:
            logger.warning(f"⚠️ Flux Schnell provider unavailable (import error): {e}")
        
        # 2. G4F SDXL (приоритет #2 - fallback)
        try:
            from g4f import AsyncClient
            from g4f.Provider import RetryProvider, Pizzagpt, Pi, FreeChatgpt, You, GeminiPro, HuggingChat, DeepInfra, DeepInfraChat, ChatGpt, AiChatOnline, NexraFluxPro, AmigoChat, Airforce
            
            g4f_client = AsyncClient(
                provider=RetryProvider([
                    Pizzagpt, Pi, FreeChatgpt, You,
                    GeminiPro, HuggingChat, DeepInfra, 
                    DeepInfraChat, ChatGpt, AiChatOnline,
                    NexraFluxPro, AmigoChat, Airforce
                ], shuffle=True)
            )
            
            self.providers.append({
                'name': 'g4f_sdxl',
                'handler': g4f_client,
                'priority': 2,
                'description': 'G4F Stable Diffusion XL',
                'supports_local_save': False
            })
            logger.info("✅ G4F SDXL provider initialized")
            
        except ImportError as e:
            logger.warning(f"⚠️ G4F SDXL provider unavailable (import error): {e}")
        
        # Сортируем провайдеры по приоритету
        self.providers.sort(key=lambda x: x['priority'])
        
        logger.info(f"🎯 Initialized {len(self.providers)} image providers")
        for provider in self.providers:
            logger.info(f"   {provider['priority']}. {provider['description']}")

    async def generate_image(
        self,
        prompt: str,
        user_id: Optional[int] = None,
        width: int = 1024,
        height: int = 1024,
        save_locally: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Генерирует изображение используя приоритетную систему провайдеров

        Args:
            prompt: Текстовое описание изображения
            user_id: ID пользователя
            width: Ширина изображения
            height: Высота изображения
            save_locally: Сохранять ли изображение локально
            **kwargs: Дополнительные параметры

        Returns:
            Dict с URL изображения и метаданными
        """
        
        if not self.providers:
            raise Exception("Нет доступных провайдеров для генерации изображений")
        
        logger.info(f"🎨 Generating image with prompt: {prompt[:100]}...")
        
        last_error = None
        
        # Пробуем провайдеры в порядке приоритета
        for provider_info in self.providers:
            provider_name = provider_info['name']
            handler = provider_info['handler']
            
            try:
                logger.info(f"🔄 Trying provider: {provider_info['description']}")
                
                if provider_name == 'flux_schnell':
                    # Together AI Flux Schnell через Worker
                    result = await handler.generate_image(
                        prompt=prompt,
                        width=width,
                        height=height,
                        save_locally=save_locally and provider_info['supports_local_save'],
                        use_worker=True  # Используем Worker по умолчанию
                    )
                    
                    logger.info(f"✅ Successfully generated image with {provider_info['description']}")
                    
                    # Добавляем метаданные
                    result.update({
                        'provider_used': provider_name,
                        'provider_description': provider_info['description'],
                        'generation_time': datetime.now().isoformat(),
                        'user_id': user_id
                    })
                    
                    return result
                    
                elif provider_name == 'g4f_sdxl':
                    # G4F SDXL
                    response = await handler.images.generate(
                        model="sdxl",
                        prompt=prompt,
                        response_format="url"
                    )
                    
                    if not response or not response.data:
                        raise Exception("Empty response from G4F SDXL")
                    
                    image_url = response.data[0].url
                    
                    logger.info(f"✅ Successfully generated image with {provider_info['description']}")
                    
                    result = {
                        'url': image_url,
                        'model': 'sdxl',
                        'provider': provider_name,
                        'provider_used': provider_name,
                        'provider_description': provider_info['description'],
                        'width': width,
                        'height': height,
                        'saved_locally': False,
                        'generation_time': datetime.now().isoformat(),
                        'user_id': user_id
                    }
                    
                    return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Provider {provider_info['description']} failed: {e}")
                
                # Логгируем fallback если это не последний провайдер
                current_index = self.providers.index(provider_info)
                if current_index < len(self.providers) - 1:
                    next_provider = self.providers[current_index + 1]
                    log_provider_fallback(
                        from_provider=provider_name,
                        to_provider=next_provider['name'],
                        reason=str(e),
                        component="image_generator"
                    )
                
                continue
        
        # Если все провайдеры не сработали
        error_msg = f"Все провайдеры генерации изображений недоступны. Последняя ошибка: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def get_available_providers(self) -> list:
        """Возвращает список доступных провайдеров"""
        return [
            {
                'name': provider['name'],
                'description': provider['description'],
                'priority': provider['priority'],
                'supports_local_save': provider['supports_local_save']
            }
            for provider in self.providers
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Проверяет состояние всех провайдеров"""
        
        health_status = {
            'total_providers': len(self.providers),
            'available_providers': 0,
            'providers': []
        }
        
        for provider_info in self.providers:
            provider_name = provider_info['name']
            
            try:
                if provider_name == 'flux_schnell':
                    # Проверяем доступность Flux
                    is_available = provider_info['handler'].is_available()
                    status = 'healthy' if is_available else 'no_api_keys'
                    
                elif provider_name == 'g4f_sdxl':
                    # G4F всегда считается доступным
                    is_available = True
                    status = 'healthy'
                    
                else:
                    is_available = False
                    status = 'unknown'
                
                if is_available:
                    health_status['available_providers'] += 1
                
                health_status['providers'].append({
                    'name': provider_name,
                    'description': provider_info['description'],
                    'priority': provider_info['priority'],
                    'status': status,
                    'available': is_available
                })
                
            except Exception as e:
                health_status['providers'].append({
                    'name': provider_name,
                    'description': provider_info['description'],
                    'priority': provider_info['priority'],
                    'status': f'error: {e}',
                    'available': False
                })
        
        health_status['overall_status'] = 'healthy' if health_status['available_providers'] > 0 else 'unhealthy'
        
        return health_status

# Глобальный экземпляр сервиса
try:
    image_service = ImageGenerationService()
    logger.info("✅ ImageGenerationService successfully initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize ImageGenerationService: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    # Создаем заглушку
    image_service = None
