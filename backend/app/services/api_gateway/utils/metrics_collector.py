"""
Сборщик метрик для API Gateway
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

from ..models import APIResponse, ProviderStats


class MetricsCollector:
    """
    Сборщик и анализатор метрик API Gateway
    
    Функции:
    - Сбор метрик производительности
    - Анализ трендов использования
    - Выявление проблемных паттернов
    - Рекомендации по оптимизации
    """
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.logger = logging.getLogger("metrics_collector")
        
        # История запросов
        self.request_history: deque = deque(maxlen=max_history_size)
        
        # Метрики по провайдерам
        self.provider_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'total_tokens': 0,
            'model_usage': defaultdict(int),
            'error_types': defaultdict(int),
            'hourly_stats': defaultdict(lambda: {
                'requests': 0,
                'successes': 0,
                'avg_response_time': 0.0
            })
        })
        
        # Метрики по эндпоинтам
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'avg_response_time': 0.0,
            'provider_usage': defaultdict(int)
        })
        
        # Общие метрики системы
        self.system_metrics = {
            'total_requests': 0,
            'start_time': datetime.utcnow(),
            'peak_requests_per_minute': 0,
            'current_requests_per_minute': 0
        }
    
    def record_request(
        self,
        endpoint: str,
        response: APIResponse,
        request_data: Optional[Dict[str, Any]] = None
    ):
        """Записать метрики запроса"""
        timestamp = datetime.utcnow()
        
        # Записываем в историю
        request_record = {
            'timestamp': timestamp,
            'endpoint': endpoint,
            'provider': response.provider_name,
            'model': response.model_name,
            'success': response.success,
            'response_time': response.response_time,
            'tokens_used': response.tokens_used,
            'error': response.error if not response.success else None
        }
        
        self.request_history.append(request_record)
        
        # Обновляем метрики провайдера
        self._update_provider_metrics(response, timestamp)
        
        # Обновляем метрики эндпоинта
        self._update_endpoint_metrics(endpoint, response)
        
        # Обновляем системные метрики
        self._update_system_metrics(timestamp)
        
        self.logger.debug(f"Записаны метрики для {endpoint}: {response.provider_name}/{response.model_name}")
    
    def _update_provider_metrics(self, response: APIResponse, timestamp: datetime):
        """Обновить метрики провайдера"""
        provider_name = response.provider_name
        metrics = self.provider_metrics[provider_name]
        
        # Общие метрики
        metrics['total_requests'] += 1
        if response.success:
            metrics['successful_requests'] += 1
        else:
            metrics['failed_requests'] += 1
            if response.error:
                metrics['error_types'][response.error] += 1
        
        metrics['total_response_time'] += response.response_time
        metrics['total_tokens'] += response.tokens_used
        
        # Использование моделей
        if response.model_name:
            metrics['model_usage'][response.model_name] += 1
        
        # Почасовая статистика
        hour_key = timestamp.strftime('%Y-%m-%d-%H')
        hourly = metrics['hourly_stats'][hour_key]
        hourly['requests'] += 1
        if response.success:
            hourly['successes'] += 1
        
        # Обновляем среднее время ответа для часа
        if hourly['requests'] == 1:
            hourly['avg_response_time'] = response.response_time
        else:
            hourly['avg_response_time'] = (
                (hourly['avg_response_time'] * (hourly['requests'] - 1) + response.response_time)
                / hourly['requests']
            )
    
    def _update_endpoint_metrics(self, endpoint: str, response: APIResponse):
        """Обновить метрики эндпоинта"""
        metrics = self.endpoint_metrics[endpoint]
        
        metrics['total_requests'] += 1
        if response.success:
            metrics['successful_requests'] += 1
        
        # Обновляем среднее время ответа
        if metrics['total_requests'] == 1:
            metrics['avg_response_time'] = response.response_time
        else:
            metrics['avg_response_time'] = (
                (metrics['avg_response_time'] * (metrics['total_requests'] - 1) + response.response_time)
                / metrics['total_requests']
            )
        
        # Использование провайдеров
        if response.provider_name:
            metrics['provider_usage'][response.provider_name] += 1
    
    def _update_system_metrics(self, timestamp: datetime):
        """Обновить системные метрики"""
        self.system_metrics['total_requests'] += 1
        
        # Подсчитываем запросы за последнюю минуту
        one_minute_ago = timestamp - timedelta(minutes=1)
        recent_requests = sum(
            1 for record in self.request_history
            if record['timestamp'] > one_minute_ago
        )
        
        self.system_metrics['current_requests_per_minute'] = recent_requests
        
        # Обновляем пиковое значение
        if recent_requests > self.system_metrics['peak_requests_per_minute']:
            self.system_metrics['peak_requests_per_minute'] = recent_requests
    
    def get_provider_stats(self, provider_name: str) -> Dict[str, Any]:
        """Получить статистику провайдера"""
        if provider_name not in self.provider_metrics:
            return {}
        
        metrics = self.provider_metrics[provider_name]
        
        # Вычисляем производные метрики
        total_requests = metrics['total_requests']
        success_rate = (metrics['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = (metrics['total_response_time'] / total_requests) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'successful_requests': metrics['successful_requests'],
            'failed_requests': metrics['failed_requests'],
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'total_tokens_used': metrics['total_tokens'],
            'most_used_model': max(metrics['model_usage'].items(), key=lambda x: x[1])[0] if metrics['model_usage'] else None,
            'model_usage': dict(metrics['model_usage']),
            'common_errors': dict(sorted(metrics['error_types'].items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Получить статистику эндпоинта"""
        if endpoint not in self.endpoint_metrics:
            return {}
        
        metrics = self.endpoint_metrics[endpoint]
        success_rate = (metrics['successful_requests'] / metrics['total_requests'] * 100) if metrics['total_requests'] > 0 else 0
        
        return {
            'total_requests': metrics['total_requests'],
            'successful_requests': metrics['successful_requests'],
            'success_rate': success_rate,
            'avg_response_time': metrics['avg_response_time'],
            'most_used_provider': max(metrics['provider_usage'].items(), key=lambda x: x[1])[0] if metrics['provider_usage'] else None,
            'provider_usage': dict(metrics['provider_usage'])
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Получить общий обзор системы"""
        uptime = datetime.utcnow() - self.system_metrics['start_time']
        
        # Статистика за последний час
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_requests = [
            record for record in self.request_history
            if record['timestamp'] > one_hour_ago
        ]
        
        successful_recent = sum(1 for r in recent_requests if r['success'])
        avg_response_time_recent = (
            sum(r['response_time'] for r in recent_requests) / len(recent_requests)
        ) if recent_requests else 0
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_requests': self.system_metrics['total_requests'],
            'current_requests_per_minute': self.system_metrics['current_requests_per_minute'],
            'peak_requests_per_minute': self.system_metrics['peak_requests_per_minute'],
            'requests_last_hour': len(recent_requests),
            'success_rate_last_hour': (successful_recent / len(recent_requests) * 100) if recent_requests else 0,
            'avg_response_time_last_hour': avg_response_time_recent,
            'active_providers': len(self.provider_metrics),
            'active_endpoints': len(self.endpoint_metrics)
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Получить тренды производительности"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Фильтруем данные за указанный период
        period_requests = [
            record for record in self.request_history
            if record['timestamp'] > cutoff_time
        ]
        
        if not period_requests:
            return {'error': 'No data for the specified period'}
        
        # Группируем по часам
        hourly_data = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'total_response_time': 0.0,
            'providers': defaultdict(int)
        })
        
        for record in period_requests:
            hour_key = record['timestamp'].strftime('%Y-%m-%d-%H')
            hour_data = hourly_data[hour_key]
            
            hour_data['requests'] += 1
            if record['success']:
                hour_data['successes'] += 1
            hour_data['total_response_time'] += record['response_time']
            hour_data['providers'][record['provider']] += 1
        
        # Преобразуем в удобный формат
        trends = []
        for hour_key in sorted(hourly_data.keys()):
            data = hourly_data[hour_key]
            trends.append({
                'hour': hour_key,
                'requests': data['requests'],
                'success_rate': (data['successes'] / data['requests'] * 100) if data['requests'] > 0 else 0,
                'avg_response_time': data['total_response_time'] / data['requests'] if data['requests'] > 0 else 0,
                'top_provider': max(data['providers'].items(), key=lambda x: x[1])[0] if data['providers'] else None
            })
        
        return {
            'period_hours': hours,
            'total_requests': len(period_requests),
            'hourly_trends': trends
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Получить рекомендации по оптимизации"""
        recommendations = []
        
        # Анализируем провайдеров
        for provider_name, metrics in self.provider_metrics.items():
            total_requests = metrics['total_requests']
            if total_requests < 10:  # Недостаточно данных
                continue
            
            success_rate = (metrics['successful_requests'] / total_requests * 100)
            avg_response_time = metrics['total_response_time'] / total_requests
            
            # Низкий success rate
            if success_rate < 80:
                recommendations.append({
                    'type': 'low_success_rate',
                    'provider': provider_name,
                    'current_rate': success_rate,
                    'message': f'Провайдер {provider_name} имеет низкий success rate ({success_rate:.1f}%)',
                    'suggestion': 'Проверьте конфигурацию API ключей и доступность сервисов'
                })
            
            # Высокое время ответа
            if avg_response_time > 30:  # секунд
                recommendations.append({
                    'type': 'high_response_time',
                    'provider': provider_name,
                    'current_time': avg_response_time,
                    'message': f'Провайдер {provider_name} имеет высокое время ответа ({avg_response_time:.1f}s)',
                    'suggestion': 'Рассмотрите увеличение timeout или проверьте сетевое подключение'
                })
        
        # Анализируем общую нагрузку
        current_rpm = self.system_metrics['current_requests_per_minute']
        peak_rpm = self.system_metrics['peak_requests_per_minute']
        
        if current_rpm > peak_rpm * 0.8:  # Близко к пиковой нагрузке
            recommendations.append({
                'type': 'high_load',
                'current_rpm': current_rpm,
                'peak_rpm': peak_rpm,
                'message': f'Текущая нагрузка ({current_rpm} req/min) близка к пиковой ({peak_rpm} req/min)',
                'suggestion': 'Рассмотрите масштабирование или оптимизацию провайдеров'
            })
        
        return recommendations
    
    def clear_old_data(self, hours: int = 168):  # 7 дней по умолчанию
        """Очистить старые данные"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Очищаем историю запросов
        original_size = len(self.request_history)
        self.request_history = deque(
            (record for record in self.request_history if record['timestamp'] > cutoff_time),
            maxlen=self.max_history_size
        )
        
        cleared_count = original_size - len(self.request_history)
        if cleared_count > 0:
            self.logger.info(f"Очищено {cleared_count} старых записей метрик")
        
        # Очищаем почасовую статистику
        cutoff_hour = cutoff_time.strftime('%Y-%m-%d-%H')
        for provider_metrics in self.provider_metrics.values():
            old_hours = [
                hour for hour in provider_metrics['hourly_stats'].keys()
                if hour < cutoff_hour
            ]
            for hour in old_hours:
                del provider_metrics['hourly_stats'][hour]
