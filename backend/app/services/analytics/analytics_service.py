import asyncio
from sqlalchemy import func, text, select, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import json
import csv
import io
from app.models import (
    Generation,
    AnalyticsData,
    User,
    DetailedGenerationMetrics,
    PointTransaction
)
from app.core.types import ContentType, TariffType
from ..optimization import QueryOptimizer
from ...core.cache import CacheService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Асинхронный сервис для сбора и анализа статистики"""

    # Константы для настройки кэширования и производительности
    CACHE_TTL = {
        'dashboard': 600,  # 10 минут
        'users': 1800,     # 30 минут
        'generations': 1800,
        'tariffs': 3600,   # 1 час
        'server': 300      # 5 минут
    }
    
    # Константы для настройки хранения данных
    RETENTION_DAYS = {
        'detailed': 30,    # 30 дней для детальных данных
        'aggregated': 365  # 1 год для агрегированных данных
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.cache = CacheService(session)
        # Список для отслеживания фоновых задач
        self.background_tasks = []

    async def get_analytics(self, period: str = 'week') -> Dict[str, Any]:
        """Получение аналитических данных за указанный период"""
        try:
            # Формируем ключ кэша
            cache_key = f"analytics:{period}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
            
            # Проверяем кэш
            cached_data = await self.cache.get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            end_date = datetime.utcnow()
            start_date = self._get_start_date(end_date, period)

            # Получаем все метрики через оптимизатор
            user_stats = self.query_optimizer.get_user_statistics(start_date, end_date)
            gen_metrics = self.query_optimizer.get_generation_metrics()
            tariff_stats = self.query_optimizer.get_tariff_usage()
            daily_active = self.query_optimizer.get_daily_active_users()
            feature_stats = self.query_optimizer.get_feature_usage_stats(days=30)
            retention_data = self.query_optimizer.get_user_retention()
            points_metrics = self._get_point_metrics(start_date, end_date)

            # Ждем выполнения всех запросов
            results = await asyncio.gather(
                user_stats,
                gen_metrics,
                tariff_stats,
                daily_active,
                feature_stats,
                retention_data,
                points_metrics,
                return_exceptions=True  # Не прерываем выполнение при ошибке в одном из запросов
            )
            
            # Обрабатываем результаты, заменяя исключения на None
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in analytics query: {str(result)}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)

            analytics_data = {
                "users": processed_results[0] or {},
                "generations": processed_results[1] or {},
                "tariffs": processed_results[2] or {},
                "daily_activity": processed_results[3] or {},
                "feature_usage": processed_results[4] or {},
                "retention": processed_results[5] or {},
                "points": processed_results[6] or {},
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                analytics_data,
                ttl=self.CACHE_TTL['dashboard']
            )

            return analytics_data

        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            # Возвращаем базовую структуру с ошибкой
            return {
                "error": str(e),
                "period": {
                    "start": start_date.isoformat() if 'start_date' in locals() else None,
                    "end": end_date.isoformat() if 'end_date' in locals() else None
                }
            }

    async def _get_point_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Получение метрик по баллам с оптимизированными запросами"""
        try:
            # Формируем ключ кэша
            cache_key = f"points_metrics:{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"
            
            # Проверяем кэш
            cached_data = await self.cache.get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Используем оптимизированный запрос с агрегацией
            points_query = text("""
                SELECT 
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_earned,
                    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as total_spent,
                    COUNT(*) as total_transactions
                FROM 
                    point_transactions
                WHERE 
                    created_at BETWEEN :start_date AND :end_date
            """)

            result = await self.session.execute(
                points_query, 
                {"start_date": start_date, "end_date": end_date}
            )
            points_stats = result.fetchone()

            # Ежедневная статистика с оптимизированным запросом
            daily_points_query = text("""
                SELECT 
                    DATE_TRUNC('day', created_at) as date,
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as earned,
                    SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as spent,
                    COUNT(*) as transactions
                FROM 
                    point_transactions
                WHERE 
                    created_at BETWEEN :start_date AND :end_date
                GROUP BY 
                    DATE_TRUNC('day', created_at)
                ORDER BY 
                    date
            """)
            
            daily_result = await self.session.execute(
                daily_points_query, 
                {"start_date": start_date, "end_date": end_date}
            )
            daily_stats = daily_result.fetchall()
            
            # Формируем результат
            points_data = {
                "total_earned": points_stats.total_earned or 0,
                "total_spent": points_stats.total_spent or 0,
                "total_transactions": points_stats.total_transactions or 0,
                "daily_stats": [
                    {
                        "date": row.date.strftime("%Y-%m-%d"),
                        "earned": row.earned or 0,
                        "spent": row.spent or 0,
                        "transactions": row.transactions or 0
                    }
                    for row in daily_stats
                ]
            }
            
            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                points_data,
                ttl=self.CACHE_TTL['dashboard']
            )
            
            return points_data

        except Exception as e:
            logger.error(f"Error getting point metrics: {str(e)}")
            return {
                "total_earned": 0,
                "total_spent": 0,
                "total_transactions": 0,
                "daily_stats": [],
                "error": str(e)
            }

    async def export_analytics(self, format: str = 'json', period: str = 'month') -> Optional[bytes]:
        """Экспорт аналитических данных в JSON или CSV формате"""
        try:
            # Получаем аналитические данные
            analytics_data = await self.get_analytics(period)
            
            if format == 'json':
                # Экспорт в JSON
                return json.dumps(analytics_data, ensure_ascii=False, indent=2).encode('utf-8')
            elif format == 'csv':
                # Экспорт в CSV
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Записываем заголовки
                writer.writerow(['Category', 'Metric', 'Value'])
                
                # Записываем данные пользователей
                if 'users' in analytics_data:
                    for key, value in analytics_data['users'].items():
                        writer.writerow(['Users', key, value])
                
                # Записываем данные генераций
                if 'generations' in analytics_data:
                    for key, value in analytics_data['generations'].items():
                        writer.writerow(['Generations', key, value])
                
                # Записываем данные тарифов
                if 'tariffs' in analytics_data:
                    for key, value in analytics_data['tariffs'].items():
                        writer.writerow(['Tariffs', key, value])
                
                # Записываем данные баллов
                if 'points' in analytics_data:
                    for key, value in analytics_data['points'].items():
                        if key != 'daily_stats':  # Пропускаем ежедневную статистику
                            writer.writerow(['Points', key, value])
                
                return output.getvalue().encode('utf-8')
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
                
        except Exception as e:
            logger.error(f"Error exporting analytics: {str(e)}")
            return None

    async def save_analytics_snapshot(self) -> bool:
        """Сохранение снимка аналитических данных для исторического анализа"""
        try:
            # Получаем аналитические данные за день
            analytics_data = await self.get_analytics('day')
            
            # Создаем запись в таблице аналитики
            snapshot = AnalyticsData(
                date=datetime.utcnow(),
                total_users=analytics_data.get('users', {}).get('total', 0),
                active_users=analytics_data.get('users', {}).get('active', 0),
                new_users=analytics_data.get('users', {}).get('new', 0),
                users_with_tariffs=analytics_data.get('tariffs', {}).get('total', 0),
                tariff_distribution=analytics_data.get('tariffs', {}).get('distribution', {}),
                total_generations=analytics_data.get('generations', {}).get('total', 0),
                generations_by_type=analytics_data.get('generations', {}).get('by_type', {}),
                average_generations_per_user=analytics_data.get('generations', {}).get('avg_per_user', 0.0),
                total_points_spent=analytics_data.get('points', {}).get('spent', 0),
                total_points_earned=analytics_data.get('points', {}).get('earned', 0),
                average_user_balance=analytics_data.get('points', {}).get('avg_balance', 0.0)
            )
            
            # Добавляем запись в сессию
            self.session.add(snapshot)
            
            # Коммитим изменения
            await self.session.commit()
            
            logger.info(f"Saved analytics snapshot at {snapshot.date}")
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving analytics snapshot: {str(e)}")
            return False

    async def cleanup_old_analytics(self) -> None:
        """Очистка устаревших данных аналитики"""
        try:
            # Определяем даты для очистки
            detailed_cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['detailed'])
            aggregated_cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['aggregated'])
            
            # Удаляем устаревшие детальные данные
            detailed_query = text("""
                DELETE FROM detailed_generation_metrics
                WHERE date < :cutoff_date
            """)
            
            await self.session.execute(detailed_query, {"cutoff_date": detailed_cutoff})
            
            # Удаляем устаревшие агрегированные данные
            aggregated_query = text("""
                DELETE FROM analytics_data
                WHERE date < :cutoff_date
            """)
            
            await self.session.execute(aggregated_query, {"cutoff_date": aggregated_cutoff})
            
            # Коммитим изменения
            await self.session.commit()
            
            logger.info(f"Cleaned up analytics data older than {detailed_cutoff} (detailed) and {aggregated_cutoff} (aggregated)")
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up old analytics data: {str(e)}")
            return False

    def _get_start_date(self, end_date: datetime, period: str) -> datetime:
        """Получение начальной даты для периода"""
        if period == 'day':
            return end_date - timedelta(days=1)
        elif period == 'week':
            return end_date - timedelta(days=7)
        elif period == 'month':
            return end_date - timedelta(days=30)
        elif period == 'year':
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=7)  # По умолчанию неделя

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ждем завершения всех фоновых задач
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)