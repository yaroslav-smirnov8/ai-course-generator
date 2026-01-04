"""
Утилита для проверки здоровья провайдеров
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

from ..models import ProviderStats, ContentType
from ..providers import BaseProvider


class HealthChecker:
    """
    Утилита для мониторинга здоровья провайдеров
    
    Функции:
    - Периодическая проверка всех провайдеров
    - Сбор метрик производительности
    - Уведомления о проблемах
    - Автоматическое восстановление
    """
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval  # секунд
        self.logger = logging.getLogger("health_checker")
        self.is_running = False
        self.health_history: Dict[str, List[Dict[str, Any]]] = {}
        
    async def start_monitoring(self, providers: List[BaseProvider]):
        """Запуск мониторинга провайдеров"""
        if self.is_running:
            self.logger.warning("Мониторинг уже запущен")
            return
        
        self.is_running = True
        self.logger.info(f"Запуск мониторинга {len(providers)} провайдеров")
        
        try:
            while self.is_running:
                await self._check_all_providers(providers)
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            self.logger.info("Мониторинг остановлен")
        except Exception as e:
            self.logger.error(f"Ошибка в мониторинге: {e}")
        finally:
            self.is_running = False
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.is_running = False
        self.logger.info("Остановка мониторинга")
    
    async def _check_all_providers(self, providers: List[BaseProvider]):
        """Проверка всех провайдеров"""
        check_time = datetime.utcnow()
        
        # Создаем задачи для параллельной проверки
        tasks = []
        for provider in providers:
            task = asyncio.create_task(
                self._check_provider_health(provider, check_time)
            )
            tasks.append(task)
        
        # Ждем завершения всех проверок
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                self.logger.error(f"Ошибка проверки провайдера {provider.name}: {result}")
            else:
                self._update_health_history(provider.name, result)
    
    async def _check_provider_health(
        self, 
        provider: BaseProvider, 
        check_time: datetime
    ) -> Dict[str, Any]:
        """Проверка здоровья конкретного провайдера"""
        try:
            # Проверяем основное здоровье
            start_time = datetime.utcnow()
            is_healthy = await asyncio.wait_for(
                provider.health_check(), 
                timeout=30
            )
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Получаем дополнительную информацию
            available_models = provider.config.get_available_models()
            total_models = len(provider.config.models)
            
            # Получаем статистику провайдера
            provider_stats = provider.get_stats()
            
            result = {
                'provider_name': provider.name,
                'check_time': check_time,
                'is_healthy': is_healthy,
                'response_time': response_time,
                'available_models': len(available_models),
                'total_models': total_models,
                'success_rate': provider_stats.get('success_rate', 0),
                'total_requests': provider_stats.get('total_requests', 0),
                'average_response_time': provider_stats.get('average_response_time', 0),
                'models_in_cooldown': total_models - len(available_models)
            }
            
            # Additional checks for specific providers
            if hasattr(provider, 'get_proxy_stats'):
                # ProxyProvider
                proxy_stats = await provider.get_proxy_stats()
                result['proxy_stats'] = proxy_stats
            
            return result
            
        except asyncio.TimeoutError:
            return {
                'provider_name': provider.name,
                'check_time': check_time,
                'is_healthy': False,
                'error': 'Health check timeout',
                'response_time': 30.0
            }
        except Exception as e:
            return {
                'provider_name': provider.name,
                'check_time': check_time,
                'is_healthy': False,
                'error': str(e),
                'response_time': 0
            }
    
    def _update_health_history(self, provider_name: str, health_data: Dict[str, Any]):
        """Обновление истории здоровья провайдера"""
        if provider_name not in self.health_history:
            self.health_history[provider_name] = []
        
        # Добавляем новую запись
        self.health_history[provider_name].append(health_data)
        
        # Ограничиваем историю (храним последние 100 записей)
        if len(self.health_history[provider_name]) > 100:
            self.health_history[provider_name] = self.health_history[provider_name][-100:]
        
        # Логируем изменения статуса
        if health_data.get('is_healthy'):
            if self._was_unhealthy_recently(provider_name):
                self.logger.info(f"Провайдер {provider_name} восстановлен")
        else:
            if self._was_healthy_recently(provider_name):
                self.logger.warning(f"Провайдер {provider_name} стал недоступен: {health_data.get('error', 'Unknown')}")
    
    def _was_unhealthy_recently(self, provider_name: str) -> bool:
        """Проверить, был ли провайдер недоступен в последних проверках"""
        history = self.health_history.get(provider_name, [])
        if len(history) < 2:
            return False
        
        # Проверяем последние 3 записи
        recent_checks = history[-3:-1]
        return any(not check.get('is_healthy', True) for check in recent_checks)
    
    def _was_healthy_recently(self, provider_name: str) -> bool:
        """Проверить, был ли провайдер доступен в последних проверках"""
        history = self.health_history.get(provider_name, [])
        if len(history) < 2:
            return True
        
        # Проверяем последние 3 записи
        recent_checks = history[-3:-1]
        return any(check.get('is_healthy', False) for check in recent_checks)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Получить сводку здоровья всех провайдеров"""
        summary = {
            'total_providers': len(self.health_history),
            'healthy_providers': 0,
            'unhealthy_providers': 0,
            'providers': {}
        }
        
        for provider_name, history in self.health_history.items():
            if not history:
                continue
            
            latest = history[-1]
            is_healthy = latest.get('is_healthy', False)
            
            if is_healthy:
                summary['healthy_providers'] += 1
            else:
                summary['unhealthy_providers'] += 1
            
            # Статистика за последний час
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_checks = [
                check for check in history 
                if check.get('check_time', datetime.min) > one_hour_ago
            ]
            
            if recent_checks:
                uptime = sum(1 for check in recent_checks if check.get('is_healthy', False))
                uptime_percentage = (uptime / len(recent_checks)) * 100
                avg_response_time = sum(
                    check.get('response_time', 0) for check in recent_checks
                ) / len(recent_checks)
            else:
                uptime_percentage = 0
                avg_response_time = 0
            
            summary['providers'][provider_name] = {
                'is_healthy': is_healthy,
                'last_check': latest.get('check_time'),
                'uptime_1h': uptime_percentage,
                'avg_response_time_1h': avg_response_time,
                'available_models': latest.get('available_models', 0),
                'total_models': latest.get('total_models', 0),
                'error': latest.get('error') if not is_healthy else None
            }
        
        return summary
    
    def get_provider_history(
        self, 
        provider_name: str, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Получить историю здоровья провайдера"""
        if provider_name not in self.health_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            check for check in self.health_history[provider_name]
            if check.get('check_time', datetime.min) > cutoff_time
        ]
    
    async def force_check_provider(self, provider: BaseProvider) -> Dict[str, Any]:
        """Принудительная проверка конкретного провайдера"""
        check_time = datetime.utcnow()
        result = await self._check_provider_health(provider, check_time)
        self._update_health_history(provider.name, result)
        return result
