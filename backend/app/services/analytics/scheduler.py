import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.cache import CacheService
from .analytics_service import AnalyticsService
from .feature_usage import FeatureUsageService

logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """Планировщик задач для аналитики с низким приоритетом"""
    
    # Константы для настройки планировщика
    DEFAULT_INTERVALS = {
        'refresh_materialized_views': 3600,  # 1 час
        'cleanup_old_data': 86400,           # 1 день
        'save_analytics_snapshot': 43200,    # 12 часов
        'refresh_cache': 1800                # 30 минут
    }
    
    def __init__(self, session_factory, config: Optional[Dict] = None):
        """
        Инициализация планировщика задач для аналитики
        
        :param session_factory: Фабрика сессий для создания новых сессий
        :param config: Конфигурация планировщика (интервалы выполнения задач)
        """
        self.session_factory = session_factory
        self.config = config or {}
        self.tasks = []
        self.running = False
        
        # Устанавливаем интервалы выполнения задач
        self.intervals = {
            'refresh_materialized_views': self.config.get('refresh_materialized_views', 
                                                         self.DEFAULT_INTERVALS['refresh_materialized_views']),
            'cleanup_old_data': self.config.get('cleanup_old_data', 
                                               self.DEFAULT_INTERVALS['cleanup_old_data']),
            'save_analytics_snapshot': self.config.get('save_analytics_snapshot', 
                                                      self.DEFAULT_INTERVALS['save_analytics_snapshot']),
            'refresh_cache': self.config.get('refresh_cache', 
                                            self.DEFAULT_INTERVALS['refresh_cache'])
        }
        
    async def start(self):
        """Запуск планировщика задач"""
        if self.running:
            logger.warning("Analytics scheduler is already running")
            return
            
        self.running = True
        logger.info("Starting analytics scheduler")
        
        # Запускаем задачи с низким приоритетом
        self.tasks.append(asyncio.create_task(
            self._run_periodic(
                self._refresh_materialized_views,
                self.intervals['refresh_materialized_views']
            )
        ))
        
        self.tasks.append(asyncio.create_task(
            self._run_periodic(
                self._cleanup_old_data,
                self.intervals['cleanup_old_data']
            )
        ))
        
        self.tasks.append(asyncio.create_task(
            self._run_periodic(
                self._save_analytics_snapshot,
                self.intervals['save_analytics_snapshot']
            )
        ))
        
        self.tasks.append(asyncio.create_task(
            self._run_periodic(
                self._refresh_cache,
                self.intervals['refresh_cache']
            )
        ))
        
        logger.info(f"Analytics scheduler started with {len(self.tasks)} tasks")
        
    async def stop(self):
        """Остановка планировщика задач"""
        if not self.running:
            logger.warning("Analytics scheduler is not running")
            return
            
        self.running = False
        logger.info("Stopping analytics scheduler")
        
        # Отменяем все задачи
        for task in self.tasks:
            task.cancel()
            
        # Ждем завершения всех задач
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        self.tasks = []
        logger.info("Analytics scheduler stopped")
        
    async def _run_periodic(self, func: Callable, interval: int):
        """
        Запуск периодической задачи с указанным интервалом
        
        :param func: Функция для выполнения
        :param interval: Интервал выполнения в секундах
        """
        # Добавляем случайную задержку для распределения нагрузки
        initial_delay = random.uniform(0, min(interval, 60))
        logger.info(f"Scheduling task {func.__name__} with interval {interval}s (initial delay: {initial_delay:.2f}s)")
        await asyncio.sleep(initial_delay)
        
        while self.running:
            try:
                start_time = datetime.utcnow()
                logger.info(f"Running scheduled task: {func.__name__}")
                
                # Выполняем задачу
                await func()
                
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()
                logger.info(f"Task {func.__name__} completed in {execution_time:.2f}s")
                
                # Вычисляем время до следующего запуска
                next_run = max(0, interval - execution_time)
                logger.info(f"Next run of {func.__name__} in {next_run:.2f}s")
                
                # Ждем до следующего запуска
                await asyncio.sleep(next_run)
                
            except asyncio.CancelledError:
                logger.info(f"Task {func.__name__} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduled task {func.__name__}: {str(e)}")
                # Ждем до следующего запуска
                await asyncio.sleep(interval)
    
    async def _refresh_materialized_views(self):
        """Обновление материализованных представлений"""
        async with self.session_factory() as session:
            try:
                feature_usage_service = FeatureUsageService(session)
                await feature_usage_service.refresh_materialized_views()
                logger.info("Materialized views refreshed successfully")
            except Exception as e:
                logger.error(f"Error refreshing materialized views: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Очистка устаревших данных аналитики"""
        async with self.session_factory() as session:
            try:
                # Очищаем устаревшие данные использования функций
                feature_usage_service = FeatureUsageService(session)
                await feature_usage_service.cleanup_old_data()
                
                # Очищаем устаревшие данные аналитики
                analytics_service = AnalyticsService(session)
                await analytics_service.cleanup_old_analytics()
                
                logger.info("Old analytics data cleaned up successfully")
            except Exception as e:
                logger.error(f"Error cleaning up old analytics data: {str(e)}")
    
    async def _save_analytics_snapshot(self):
        """Сохранение снимка аналитических данных"""
        async with self.session_factory() as session:
            try:
                analytics_service = AnalyticsService(session)
                result = await analytics_service.save_analytics_snapshot()
                if result:
                    logger.info("Analytics snapshot saved successfully")
                else:
                    logger.warning("Failed to save analytics snapshot")
            except Exception as e:
                logger.error(f"Error saving analytics snapshot: {str(e)}")
    
    async def _refresh_cache(self):
        """Обновление кэша аналитики"""
        async with self.session_factory() as session:
            try:
                # Получаем сервис кэширования
                cache = CacheService(session)
                
                # Инвалидируем устаревшие ключи кэша
                patterns = [
                    "dashboard_stats:*",
                    "feature_usage:*",
                    "analytics:*",
                    "points_metrics:*"
                ]
                
                for pattern in patterns:
                    await cache.invalidate_pattern(pattern)
                
                logger.info("Analytics cache refreshed successfully")
            except Exception as e:
                logger.error(f"Error refreshing analytics cache: {str(e)}") 