"""
Провайдер для прямых вызовов Cloudflare Workers (fallback)
"""

import httpx
import time
from typing import Dict, Any
from .base_provider import BaseProvider
from ..models import ModelConfig


class DirectProvider(BaseProvider):
    """
    Провайдер для прямых вызовов Cloudflare Workers
    
    Особенности:
    - Fallback провайдер (последний в цепочке для текста)
    - Прямые HTTP вызовы без прокси или VPN
    - Может не работать в некоторых регионах из-за блокировок
    - Самый быстрый при доступности
    """
    
    async def _call_model_api(
        self, 
        model: ModelConfig,
        endpoint: str,
        data: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Прямой вызов Cloudflare Worker"""
        
        # Получаем URL воркера из конфигурации
        worker_url = self.config.endpoints.get(endpoint)
        if not worker_url:
            raise Exception(f"Воркер для эндпоинта {endpoint} не найден")
        
        # Добавляем информацию о предпочтительном провайдере
        headers['X-Preferred-Provider'] = model.provider_type
        headers['X-Preferred-Model'] = model.name
        
        self.logger.info(f"Прямой вызов воркера: {worker_url} с моделью {model.name}")
        self.logger.debug(f"Данные запроса: {data}")
        
        async with httpx.AsyncClient(timeout=model.timeout) as client:
            response = await client.post(worker_url, json=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Нормализуем ответ от воркера
                return {
                    'success': True,
                    'text': result.get('text', result.get('content', '')),
                    'content': result.get('text', result.get('content', '')),
                    'model': result.get('model', model.name),
                    'provider': 'direct',
                    'usage': result.get('usage', {}),
                    'metadata': {
                        'worker_response_time': result.get('response_time', 0),
                        'actual_provider': result.get('actual_provider', model.provider_type),
                        'actual_model': result.get('actual_model', model.name),
                        'worker_url': worker_url
                    }
                }
            else:
                # Получаем детали ошибки
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', f'HTTP {response.status_code}')
                    error_details = error_data.get('details', response.text)
                except:
                    error_message = f'HTTP {response.status_code}'
                    error_details = response.text
                
                self.logger.error(f"Прямой вызов воркера ошибка {response.status_code}: {error_message}")
                
                raise Exception(f"Worker HTTP {response.status_code}: {error_message} - {error_details}")
    
    async def _health_check_implementation(self) -> bool:
        """Проверка доступности прямых вызовов воркеров"""
        try:
            # Тестируем несколько воркеров для надежности
            test_endpoints = ['lesson-plan', 'exercises', 'games']
            successful_tests = 0
            
            for endpoint in test_endpoints:
                worker_url = self.config.endpoints.get(endpoint)
                if worker_url:
                    try:
                        async with httpx.AsyncClient(timeout=10) as client:
                            # Пробуем OPTIONS запрос (обычно быстрее и безопаснее)
                            response = await client.options(worker_url)
                            
                            # Cloudflare Workers обычно возвращают 200 или 204 на OPTIONS
                            # 405 (Method Not Allowed) тоже означает что сервер доступен
                            if response.status_code in [200, 204, 405]:
                                successful_tests += 1
                                self.logger.debug(f"Health check воркера {endpoint} успешен")
                            else:
                                self.logger.debug(f"Health check воркера {endpoint}: HTTP {response.status_code}")
                                
                    except Exception as e:
                        self.logger.debug(f"Health check воркера {endpoint} не удался: {e}")
                        continue
            
            # Считаем провайдер здоровым если хотя бы половина воркеров доступна
            is_healthy = successful_tests >= len(test_endpoints) // 2
            
            if is_healthy:
                self.logger.debug(f"Direct provider здоров: {successful_tests}/{len(test_endpoints)} воркеров доступны")
            else:
                self.logger.warning(f"Direct provider нездоров: только {successful_tests}/{len(test_endpoints)} воркеров доступны")
            
            return is_healthy
            
        except Exception as e:
            self.logger.warning(f"Health check Direct provider не удался: {e}")
            return False
    
    def _should_cooldown_model(self, error: Exception) -> bool:
        """
        Переопределяем логику cooldown для прямых вызовов.
        Учитываем специфичные ошибки Cloudflare Workers.
        """
        error_str = str(error).lower()
        
        # Стандартные ошибки
        if super()._should_cooldown_model(error):
            return True
        
        # Специфичные ошибки прямых вызовов
        if 'cloudflare' in error_str:
            return True
        
        # Ошибки блокировки/доступности
        if 'connection refused' in error_str:
            return True
        
        if 'dns resolution failed' in error_str:
            return True
        
        if 'ssl' in error_str and 'error' in error_str:
            return True
        
        # Географические блокировки
        if 'forbidden' in error_str or '403' in error_str:
            return True
        
        return False
    
    def _get_cooldown_minutes(self, error: Exception) -> int:
        """Получить время cooldown для прямых вызовов"""
        error_str = str(error).lower()
        
        # Специфичные cooldown времена для прямых вызовов
        if 'connection refused' in error_str or 'dns resolution failed' in error_str:
            return 15  # Долгий cooldown для сетевых проблем
        
        if 'forbidden' in error_str or '403' in error_str:
            return 30  # Очень долгий cooldown для блокировок
        
        if 'ssl' in error_str and 'error' in error_str:
            return 5  # Средний cooldown для SSL проблем
        
        if 'cloudflare' in error_str:
            return 10  # Средний cooldown для Cloudflare ошибок
        
        # Используем стандартную логику для остальных ошибок
        return super()._get_cooldown_minutes(error)
    
    async def test_worker_connectivity(self, endpoint: str) -> Dict[str, Any]:
        """Тестирование подключения к конкретному воркеру"""
        worker_url = self.config.endpoints.get(endpoint)
        if not worker_url:
            return {
                'endpoint': endpoint,
                'success': False,
                'error': 'Endpoint not found in configuration'
            }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                start_time = time.time()
                response = await client.options(worker_url)
                response_time = time.time() - start_time
                
                return {
                    'endpoint': endpoint,
                    'worker_url': worker_url,
                    'success': response.status_code in [200, 204, 405],
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'headers': dict(response.headers)
                }
                
        except Exception as e:
            return {
                'endpoint': endpoint,
                'worker_url': worker_url,
                'success': False,
                'error': str(e)
            }
    
    async def test_all_workers(self) -> Dict[str, Any]:
        """Тестирование всех воркеров"""
        results = {}
        
        for endpoint in self.config.endpoints.keys():
            results[endpoint] = await self.test_worker_connectivity(endpoint)
        
        # Общая статистика
        total_workers = len(results)
        successful_workers = sum(1 for r in results.values() if r['success'])
        
        return {
            'total_workers': total_workers,
            'successful_workers': successful_workers,
            'success_rate': (successful_workers / total_workers * 100) if total_workers > 0 else 0,
            'worker_results': results
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Расширенная статистика для Direct провайдера"""
        base_stats = super().get_stats()
        
        # Добавляем специфичную информацию о прямых вызовах
        base_stats.update({
            'provider_type': 'direct',
            'supported_endpoints': list(self.config.endpoints.keys()),
            'worker_urls': self.config.endpoints,
            'direct_timeout': self.config.timeout
        })
        
        return base_stats
