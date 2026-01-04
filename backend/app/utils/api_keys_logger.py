"""
Централизованная система логгирования использования API ключей
Отслеживает использование, отказы, переключения и статистику ключей
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
from collections import defaultdict, deque

class APIKeysLogger:
    """Централизованный логгер для API ключей"""
    
    def __init__(self):
        # Настройка директории для логов
        self.logs_dir = Path("logs/api_keys")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Настройки (должны быть ДО setup_loggers!)
        self.max_log_file_size = 10 * 1024 * 1024  # 10MB
        self.max_log_files = 5

        # Настройка логгеров
        self.setup_loggers()
        
        # Статистика в памяти
        self.stats = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limits': 0,
            'auth_errors': 0,
            'last_used': None,
            'last_error': None,
            'consecutive_failures': 0,
            'cooldown_until': None
        })
        
        # Очередь недавних событий (для быстрого анализа)
        self.recent_events = deque(maxlen=1000)
        
        # Блокировка для thread-safety
        self.lock = threading.Lock()
        
    def setup_loggers(self):
        """Настройка логгеров для разных типов событий"""
        
        # Основной логгер использования ключей
        self.usage_logger = logging.getLogger('api_keys.usage')
        self.usage_logger.setLevel(logging.INFO)
        
        # Логгер ошибок и отказов
        self.errors_logger = logging.getLogger('api_keys.errors')
        self.errors_logger.setLevel(logging.WARNING)
        
        # Логгер статистики
        self.stats_logger = logging.getLogger('api_keys.stats')
        self.stats_logger.setLevel(logging.INFO)
        
        # Настройка обработчиков файлов
        self.setup_file_handlers()
        
    def setup_file_handlers(self):
        """Настройка обработчиков файлов с ротацией"""
        
        from logging.handlers import RotatingFileHandler
        
        # Обработчик для использования ключей
        usage_handler = RotatingFileHandler(
            self.logs_dir / 'usage.log',
            maxBytes=self.max_log_file_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        usage_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        usage_handler.setFormatter(usage_formatter)
        self.usage_logger.addHandler(usage_handler)
        
        # Обработчик для ошибок
        errors_handler = RotatingFileHandler(
            self.logs_dir / 'errors.log',
            maxBytes=self.max_log_file_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        errors_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        errors_handler.setFormatter(errors_formatter)
        self.errors_logger.addHandler(errors_handler)
        
        # Обработчик для статистики (ежечасно)
        stats_handler = RotatingFileHandler(
            self.logs_dir / 'stats.log',
            maxBytes=self.max_log_file_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        stats_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        stats_handler.setFormatter(stats_formatter)
        self.stats_logger.addHandler(stats_handler)
        
    def log_key_usage(self, provider: str, key_id: str, component: str = None, 
                     model: str = None, success: bool = True, 
                     response_time: float = None, tokens_used: int = None):
        """Логгирует использование API ключа"""
        
        with self.lock:
            timestamp = datetime.now()
            
            # Маскируем ключ для безопасности
            masked_key = self.mask_key(key_id)
            
            # Обновляем статистику
            key_stats = self.stats[f"{provider}:{masked_key}"]
            key_stats['total_requests'] += 1
            key_stats['last_used'] = timestamp.isoformat()
            
            if success:
                key_stats['successful_requests'] += 1
                key_stats['consecutive_failures'] = 0
            else:
                key_stats['failed_requests'] += 1
                key_stats['consecutive_failures'] += 1
            
            # Создаем событие
            event = {
                'timestamp': timestamp.isoformat(),
                'provider': provider,
                'key_id': masked_key,
                'component': component,
                'model': model,
                'success': success,
                'response_time': response_time,
                'tokens_used': tokens_used
            }
            
            # Добавляем в очередь недавних событий
            self.recent_events.append(event)
            
            # Логгируем
            log_message = f"USAGE | {provider} | {masked_key} | {component or 'unknown'} | {model or 'unknown'} | {'SUCCESS' if success else 'FAILED'}"
            if response_time:
                log_message += f" | {response_time:.2f}s"
            if tokens_used:
                log_message += f" | {tokens_used} tokens"
                
            self.usage_logger.info(log_message)
            
    def log_key_error(self, provider: str, key_id: str, error_type: str, 
                     error_message: str, component: str = None, 
                     will_retry: bool = False, cooldown_minutes: int = None):
        """Логгирует ошибку использования ключа"""
        
        with self.lock:
            timestamp = datetime.now()
            
            # Маскируем ключ
            masked_key = self.mask_key(key_id)
            
            # Обновляем статистику ошибок
            key_stats = self.stats[f"{provider}:{masked_key}"]
            key_stats['last_error'] = timestamp.isoformat()
            
            if error_type == 'rate_limit':
                key_stats['rate_limits'] += 1
            elif error_type == 'auth_error':
                key_stats['auth_errors'] += 1
            
            # Устанавливаем кулдаун если указан
            if cooldown_minutes:
                cooldown_until = timestamp + timedelta(minutes=cooldown_minutes)
                key_stats['cooldown_until'] = cooldown_until.isoformat()
            
            # Создаем событие ошибки
            error_event = {
                'timestamp': timestamp.isoformat(),
                'provider': provider,
                'key_id': masked_key,
                'component': component,
                'error_type': error_type,
                'error_message': error_message,
                'will_retry': will_retry,
                'cooldown_minutes': cooldown_minutes
            }
            
            self.recent_events.append(error_event)
            
            # Логгируем ошибку
            log_message = f"ERROR | {provider} | {masked_key} | {component or 'unknown'} | {error_type} | {error_message}"
            if will_retry:
                log_message += " | WILL_RETRY"
            if cooldown_minutes:
                log_message += f" | COOLDOWN_{cooldown_minutes}min"
                
            self.errors_logger.error(log_message)
            
    def log_key_switch(self, provider: str, from_key: str, to_key: str, 
                      reason: str, component: str = None):
        """Логгирует переключение между ключами"""
        
        with self.lock:
            timestamp = datetime.now()
            
            # Маскируем ключи
            masked_from = self.mask_key(from_key)
            masked_to = self.mask_key(to_key)
            
            # Создаем событие переключения
            switch_event = {
                'timestamp': timestamp.isoformat(),
                'provider': provider,
                'from_key': masked_from,
                'to_key': masked_to,
                'reason': reason,
                'component': component
            }
            
            self.recent_events.append(switch_event)
            
            # Логгируем переключение
            log_message = f"SWITCH | {provider} | {masked_from} -> {masked_to} | {reason} | {component or 'unknown'}"
            self.usage_logger.warning(log_message)
            
    def log_provider_fallback(self, from_provider: str, to_provider: str, 
                            reason: str, component: str = None):
        """Логгирует переключение между провайдерами"""
        
        with self.lock:
            timestamp = datetime.now()
            
            # Создаем событие fallback
            fallback_event = {
                'timestamp': timestamp.isoformat(),
                'from_provider': from_provider,
                'to_provider': to_provider,
                'reason': reason,
                'component': component
            }
            
            self.recent_events.append(fallback_event)
            
            # Логгируем fallback
            log_message = f"FALLBACK | {from_provider} -> {to_provider} | {reason} | {component or 'unknown'}"
            self.usage_logger.warning(log_message)
            
    def get_key_stats(self, provider: str = None, key_id: str = None) -> Dict[str, Any]:
        """Получает статистику по ключам"""
        
        with self.lock:
            if provider and key_id:
                masked_key = self.mask_key(key_id)
                key_name = f"{provider}:{masked_key}"
                return self.stats.get(key_name, {})
            elif provider:
                return {k: v for k, v in self.stats.items() if k.startswith(f"{provider}:")}
            else:
                return dict(self.stats)
                
    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[Dict[str, Any]]:
        """Получает недавние события"""
        
        with self.lock:
            events = list(self.recent_events)
            
            if event_type:
                events = [e for e in events if e.get('error_type') == event_type or 
                         ('from_key' in e and event_type == 'switch') or
                         ('from_provider' in e and event_type == 'fallback')]
            
            return events[-limit:] if limit else events
            
    def generate_hourly_stats(self):
        """Генерирует почасовую статистику"""
        
        with self.lock:
            timestamp = datetime.now()
            
            # Собираем статистику по провайдерам
            provider_stats = defaultdict(lambda: {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'active_keys': 0,
                'keys_in_cooldown': 0
            })
            
            for key_name, stats in self.stats.items():
                if ':' in key_name:
                    provider = key_name.split(':')[0]
                    provider_stats[provider]['total_requests'] += stats['total_requests']
                    provider_stats[provider]['successful_requests'] += stats['successful_requests']
                    provider_stats[provider]['failed_requests'] += stats['failed_requests']
                    provider_stats[provider]['active_keys'] += 1
                    
                    # Проверяем кулдаун
                    if stats.get('cooldown_until'):
                        cooldown_time = datetime.fromisoformat(stats['cooldown_until'])
                        if cooldown_time > timestamp:
                            provider_stats[provider]['keys_in_cooldown'] += 1
            
            # Логгируем статистику
            stats_data = {
                'timestamp': timestamp.isoformat(),
                'providers': dict(provider_stats),
                'total_events': len(self.recent_events)
            }
            
            self.stats_logger.info(f"HOURLY_STATS | {json.dumps(stats_data, ensure_ascii=False)}")
            
    def mask_key(self, key: str) -> str:
        """Маскирует API ключ для безопасности"""
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}***{key[-4:]}"
        
    def export_stats_to_json(self, filepath: str = None) -> str:
        """Экспортирует статистику в JSON файл"""
        
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.logs_dir / f"stats_export_{timestamp}.json"
        
        with self.lock:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'stats': dict(self.stats),
                'recent_events': list(self.recent_events)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            return str(filepath)
            
    def cleanup_old_stats(self, days_to_keep: int = 7):
        """Очищает старую статистику"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.lock:
            # Очищаем старые события
            self.recent_events = deque([
                event for event in self.recent_events 
                if datetime.fromisoformat(event['timestamp']) > cutoff_date
            ], maxlen=1000)
            
            # Сбрасываем статистику для неиспользуемых ключей
            inactive_keys = []
            for key_name, stats in self.stats.items():
                if stats.get('last_used'):
                    last_used = datetime.fromisoformat(stats['last_used'])
                    if last_used < cutoff_date:
                        inactive_keys.append(key_name)
            
            for key_name in inactive_keys:
                del self.stats[key_name]

# Глобальный экземпляр логгера
api_keys_logger = APIKeysLogger()

# Удобные функции для использования
def log_key_usage(provider: str, key_id: str, **kwargs):
    """Удобная функция для логгирования использования ключа"""
    api_keys_logger.log_key_usage(provider, key_id, **kwargs)

def log_key_error(provider: str, key_id: str, error_type: str, error_message: str, **kwargs):
    """Удобная функция для логгирования ошибки ключа"""
    api_keys_logger.log_key_error(provider, key_id, error_type, error_message, **kwargs)

def log_key_switch(provider: str, from_key: str, to_key: str, reason: str, **kwargs):
    """Удобная функция для логгирования переключения ключей"""
    api_keys_logger.log_key_switch(provider, from_key, to_key, reason, **kwargs)

def log_provider_fallback(from_provider: str, to_provider: str, reason: str, **kwargs):
    """Удобная функция для логгирования fallback провайдеров"""
    api_keys_logger.log_provider_fallback(from_provider, to_provider, reason, **kwargs)
