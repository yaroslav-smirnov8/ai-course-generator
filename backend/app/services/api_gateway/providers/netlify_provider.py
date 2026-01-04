"""
Провайдер для генерации изображений через Netlify (ТОЛЬКО для изображений)
"""

import httpx
from typing import Dict, Any
from .base_provider import BaseProvider
from ..models import ModelConfig


class NetlifyProvider(BaseProvider):
    """
    Провайдер для генерации изображений через Netlify Functions
    
    Особенности:
    - ТОЛЬКО для генерации изображений
    - Автоматический перевод промптов на английский
    - Использует Together AI через Netlify Functions
    - Единственный провайдер для изображений
    """
    
    async def _call_model_api(
        self, 
        model: ModelConfig,
        endpoint: str,
        data: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Вызов генерации изображений через Netlify"""
        
        # Получаем URL Netlify функции из конфигурации
        netlify_endpoint = self.config.endpoints.get(endpoint)
        if not netlify_endpoint:
            raise Exception(f"Netlify эндпоинт {endpoint} не найден")
        
        url = f"{self.config.base_url}/{netlify_endpoint}"
        
        # Подготавливаем данные для Netlify функции
        netlify_data = {
            'prompt': data.get('prompt', ''),
            'width': data.get('width', 1024),
            'height': data.get('height', 1024),
            'model': model.name,
            'steps': data.get('steps', 4),
            'n': data.get('n', 1)
        }
        
        # Добавляем специфичные заголовки для Netlify
        netlify_headers = headers.copy()
        netlify_headers['X-Component-ID'] = endpoint
        
        self.logger.info(f"Генерация изображения через Netlify: {url}")
        self.logger.debug(f"Промпт: {netlify_data['prompt'][:100]}...")
        
        async with httpx.AsyncClient(timeout=model.timeout) as client:
            response = await client.post(url, json=netlify_data, headers=netlify_headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Нормализуем ответ от Netlify
                return {
                    'success': True,
                    'image_url': result.get('image_url', result.get('url', '')),
                    'model': result.get('model', model.name),
                    'provider': 'netlify',
                    'metadata': {
                        'original_prompt': data.get('prompt', ''),
                        'translated_prompt': result.get('translated_prompt'),
                        'generation_time': result.get('generation_time', 0),
                        'image_size': f"{netlify_data['width']}x{netlify_data['height']}",
                        'steps': netlify_data['steps']
                    }
                }
            else:
                # Получаем детали ошибки
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', f'HTTP {response.status_code}')
                    error_details = error_data.get('message', response.text)
                except:
                    error_message = f'HTTP {response.status_code}'
                    error_details = response.text
                
                self.logger.error(f"Netlify ошибка {response.status_code}: {error_message}")
                
                raise Exception(f"Netlify HTTP {response.status_code}: {error_message} - {error_details}")
    
    async def _health_check_implementation(self) -> bool:
        """Проверка доступности Netlify Functions"""
        try:
            # Тестируем основные эндпоинты для изображений
            test_endpoints = ['flux-images']
            
            for endpoint in test_endpoints:
                netlify_endpoint = self.config.endpoints.get(endpoint)
                if netlify_endpoint:
                    try:
                        url = f"{self.config.base_url}/{netlify_endpoint}"
                        
                        async with httpx.AsyncClient(timeout=10) as client:
                            # Пробуем OPTIONS запрос
                            response = await client.options(url)
                            
                            # Netlify Functions обычно возвращают 200 или 204 на OPTIONS
                            if response.status_code in [200, 204, 405]:
                                self.logger.debug(f"Health check Netlify {endpoint} успешен")
                                return True
                            else:
                                self.logger.debug(f"Health check Netlify {endpoint}: HTTP {response.status_code}")
                                
                    except Exception as e:
                        self.logger.debug(f"Health check Netlify {endpoint} не удался: {e}")
                        continue
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Health check Netlify не удался: {e}")
            return False
    
    def _should_cooldown_model(self, error: Exception) -> bool:
        """
        Переопределяем логику cooldown для Netlify.
        Учитываем специфичные ошибки генерации изображений.
        """
        error_str = str(error).lower()
        
        # Стандартные ошибки
        if super()._should_cooldown_model(error):
            return True
        
        # Специфичные ошибки Netlify
        if 'netlify' in error_str and 'timeout' in error_str:
            return True
        
        if 'function timeout' in error_str:
            return True
        
        # Ошибки генерации изображений
        if 'image generation failed' in error_str:
            return True
        
        if 'together ai' in error_str and 'error' in error_str:
            return True
        
        # Ошибки перевода промптов
        if 'translation failed' in error_str:
            return False  # Не ставим в cooldown, можем попробовать без перевода
        
        return False
    
    def _get_cooldown_minutes(self, error: Exception) -> int:
        """Получить время cooldown для Netlify ошибок"""
        error_str = str(error).lower()
        
        # Netlify специфичные cooldown времена
        if 'function timeout' in error_str:
            return 5  # Средний cooldown для timeout функций
        
        if 'image generation failed' in error_str:
            return 3  # Короткий cooldown для ошибок генерации
        
        if 'together ai' in error_str and 'error' in error_str:
            return 10  # Долгий cooldown для проблем с Together AI
        
        if 'netlify' in error_str and 'timeout' in error_str:
            return 7  # Средний cooldown для Netlify timeout
        
        # Используем стандартную логику для остальных ошибок
        return super()._get_cooldown_minutes(error)
    
    async def test_image_generation(self, test_prompt: str = "A simple test image") -> Dict[str, Any]:
        """Тестирование генерации изображений"""
        try:
            # Используем первую доступную модель
            available_models = self.config.get_available_models()
            if not available_models:
                return {
                    'success': False,
                    'error': 'No available models for testing'
                }
            
            model = available_models[0]
            
            # Подготавливаем тестовые данные
            test_data = {
                'prompt': test_prompt,
                'width': 512,  # Меньший размер для быстрого теста
                'height': 512,
                'steps': 1  # Минимум шагов для быстрого теста
            }
            
            # Подготавливаем заголовки
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AITeachers-WebApp-Test/1.0'
            }
            
            # Добавляем API ключи
            if hasattr(self, '_test_api_keys'):
                headers.update(self._prepare_headers(self._test_api_keys, model))
            
            result = await self._call_model_api(model, 'flux-images', test_data, headers)
            
            return {
                'success': True,
                'model': model.name,
                'image_url': result.get('image_url'),
                'metadata': result.get('metadata', {})
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_test_api_keys(self, api_keys: Dict[str, str]):
        """Установить API ключи для тестирования"""
        self._test_api_keys = api_keys
    
    def get_stats(self) -> Dict[str, Any]:
        """Расширенная статистика для Netlify провайдера"""
        base_stats = super().get_stats()
        
        # Добавляем специфичную информацию о Netlify
        base_stats.update({
            'provider_type': 'netlify',
            'base_url': self.config.base_url,
            'supported_endpoints': list(self.config.endpoints.keys()),
            'netlify_timeout': self.config.timeout,
            'translation_enabled': self.config.extra_config.get('translation_required', False),
            'translation_provider': self.config.extra_config.get('translation_provider', 'unknown')
        })
        
        return base_stats
