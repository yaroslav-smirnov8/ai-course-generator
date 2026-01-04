import asyncio
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from sqlalchemy import text, func, select, insert # Добавлен импорт insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.cache import CacheService
# Добавлен импорт модели PurchaseAnalytics
from ...models import (
    FeatureUsage,
    FeatureUsageMetrics,
    AnalyticsData,
    User,
    Generation,
    DetailedGenerationMetrics,
    PurchaseAnalytics
)
from ..optimization.batch_processor import BatchProcessor
from ..optimization.query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)


class OptimizedAnalyticsService:
    """Оптимизированный сервис аналитики с низким потреблением ресурсов"""

    # Константы для настройки производительности
    BATCH_SIZE = 200  # Увеличенный размер пакета для снижения количества операций
    CACHE_TTL = {
        'dashboard': 600,  # 10 минут для дашборда
        'analytics': 1800,  # 30 минут для аналитики
        'feature_usage': 3600,  # 1 час для использования функций
    }
    RETENTION_DAYS = {
        'detailed': 30,  # 30 дней для детальных данных
        'aggregated': 365  # 1 год для агрегированных данных
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session, batch_size=self.BATCH_SIZE)
        self.cache = CacheService(session)
        self.background_tasks = []

    async def track_feature_usage(
            self,
            user_id: int,
            feature_type: str,
            content_type: Optional[str] = None,
            success: bool = True,
            usage_data: Dict = None,
            error_type: Optional[str] = None,
            generation_time: Optional[float] = None,
            tokens_used: Optional[int] = None
    ) -> None:
        """Отслеживание использования функций с оптимизированной обработкой"""
        try:
            # Создаем запись использования
            usage_record = {
                'user_id': user_id,
                'feature_type': feature_type,
                'content_type': content_type,
                'success': success,
                'usage_data': usage_data or {},
                'error_type': error_type,
                'created_at': datetime.utcnow()
            }

            # Добавляем запись в очередь для пакетной обработки
            # Используем фоновую задачу для асинхронной обработки
            task = asyncio.create_task(
                self._process_usage_batch([usage_record])
            )
            
            # Не ждем завершения задачи, чтобы не блокировать основной поток
            self.background_tasks.append(task)
            
            # Очищаем завершенные задачи
            self.background_tasks = [t for t in self.background_tasks if not t.done()]
            
            # Если есть метрики генерации, сохраняем их отдельно
            if generation_time is not None and tokens_used is not None:
                metrics_record = {
                    'user_id': user_id,
                    'content_type': content_type,
                    'generation_time': generation_time,
                    'tokens_used': tokens_used,
                    'success': success,
                    'created_at': datetime.utcnow()
                }
                
                metrics_task = asyncio.create_task(
                    self._save_generation_metrics(metrics_record)
                )
                self.background_tasks.append(metrics_task)
                
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
            # Не поднимаем исключение, чтобы не прерывать основной поток

    async def _process_usage_batch(self, batch_data: List[Dict]) -> None:
        """Обработка пакета данных использования функций"""
        try:
            # Создаем объекты FeatureUsage из данных пакета
            feature_usages = []
            for item in batch_data:
                feature_usage = FeatureUsage(**item)
                feature_usages.append(feature_usage)
                
            # Добавляем все записи в сессию
            self.session.add_all(feature_usages)
            
            # Коммитим изменения
            await self.session.commit()
            
            # Инвалидируем кэш аналитики
            await self.cache.invalidate_pattern("feature_usage:*")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error processing usage batch: {str(e)}")

    async def _save_generation_metrics(self, metrics_data: Dict) -> None:
        """Сохранение метрик генерации"""
        try:
            metrics = DetailedGenerationMetrics(**metrics_data)
            self.session.add(metrics)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error saving generation metrics: {str(e)}")

    async def get_feature_usage_analytics(
            self,
            period: str = 'week',
            feature_type: Optional[str] = None,
            content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Получение аналитики использования функций"""
        try:
            # Формируем ключ кэша
            cache_key = f"feature_usage:{period}:{feature_type or 'all'}:{content_type or 'all'}"
            
            # Проверяем кэш
            cached_data = await self.cache.get_cached_data(cache_key)
            if cached_data:
                return cached_data
                
            # Определяем период
            end_date = datetime.utcnow()
            start_date = self._get_start_date(end_date, period)
            
            # Базовый запрос
            query = select([
                FeatureUsage.feature_type,
                FeatureUsage.content_type,
                func.count().label('count'),
                func.count(func.distinct(FeatureUsage.user_id)).label('unique_users'),
                func.avg(func.case(
                    [(FeatureUsage.success == True, 1)],
                    else_=0
                )).label('success_rate')
            ]).where(
                FeatureUsage.created_at.between(start_date, end_date)
            )
            
            # Добавляем фильтры
            if feature_type:
                query = query.where(FeatureUsage.feature_type == feature_type)
            if content_type:
                query = query.where(FeatureUsage.content_type == content_type)
                
            # Группировка и сортировка
            query = query.group_by(
                FeatureUsage.feature_type,
                FeatureUsage.content_type
            ).order_by(
                func.count().desc()
            )
            
            # Выполняем запрос
            result = await self.session.execute(query)
            rows = result.fetchall()
            
            # Формируем результат
            analytics_data = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_count': sum(row.count for row in rows),
                'unique_users': len(set().union(*[set([row.unique_users]) for row in rows])),
                'features': [
                    {
                        'feature_type': row.feature_type,
                        'content_type': row.content_type,
                        'count': row.count,
                        'unique_users': row.unique_users,
                        'success_rate': float(row.success_rate)
                    }
                    for row in rows
                ]
            }
            
            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                analytics_data,
                ttl=self.CACHE_TTL['feature_usage']
            )
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error getting feature usage analytics: {str(e)}")
            return {
                'period': period,
                'error': str(e),
                'features': []
            }

    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Получение статистики для дашборда"""
        try:
            # Формируем ключ кэша
            cache_key = f"dashboard_stats:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
            
            # Проверяем кэш
            cached_data = await self.cache.get_cached_data(cache_key)
            if cached_data:
                return cached_data
                
            # Получаем базовую статистику
            total_users = await self.session.scalar(
                select(func.count()).select_from(User)
            )
            
            # Получаем активных пользователей за сегодня
            today = datetime.utcnow().date()
            active_users_query = select(
                func.count(func.distinct(FeatureUsage.user_id))
            ).where(
                func.date(FeatureUsage.created_at) == today
            )
            active_users = await self.session.scalar(active_users_query)
            
            # Получаем количество генераций за сегодня
            generations_query = select(
                func.count()
            ).select_from(Generation).where(
                func.date(Generation.created_at) == today
            )
            generations_today = await self.session.scalar(generations_query)
            
            # Формируем результат
            stats = {
                'users': {
                    'total': total_users or 0,
                    'active_today': active_users or 0
                },
                'generations': {
                    'today': generations_today or 0
                },
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                stats,
                ttl=self.CACHE_TTL['dashboard']
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {str(e)}")
            return {
                'users': {'total': 0, 'active_today': 0},
                'generations': {'today': 0},
                'updated_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    async def cleanup_old_data(self) -> None:
        """Очистка устаревших данных аналитики"""
        try:
            # Определяем даты для очистки
            detailed_cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['detailed'])
            aggregated_cutoff = datetime.utcnow() - timedelta(days=self.RETENTION_DAYS['aggregated'])
            
            # Удаляем устаревшие детальные данные
            detailed_query = text("""
                DELETE FROM feature_usage
                WHERE created_at < :cutoff_date
            """)
            
            await self.session.execute(
                detailed_query,
                {'cutoff_date': detailed_cutoff}
            )
            
            # Удаляем устаревшие агрегированные данные
            aggregated_query = text("""
                DELETE FROM analytics_data
                WHERE created_at < :cutoff_date
            """)
            
            await self.session.execute(
                aggregated_query,
                {'cutoff_date': aggregated_cutoff}
            )
            
            # Коммитим изменения
            await self.session.commit()
            
            logger.info(f"Cleaned up analytics data older than {detailed_cutoff}")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up old analytics data: {str(e)}")

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

    async def create_materialized_views(self) -> None:
        """Создание материализованных представлений для оптимизации запросов"""
        try:
            # Создаем материализованное представление для ежедневной статистики
            daily_stats_view = text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS feature_usage_daily_summary AS
                SELECT 
                    DATE_TRUNC('day', created_at) AS day,
                    feature_type,
                    content_type,
                    COUNT(*) AS total_count,
                    COUNT(DISTINCT user_id) AS unique_users,
                    AVG(CASE WHEN success THEN 1 ELSE 0 END) AS success_rate
                FROM 
                    feature_usage
                GROUP BY 
                    DATE_TRUNC('day', created_at),
                    feature_type,
                    content_type;
                
                CREATE INDEX IF NOT EXISTS idx_feature_usage_daily_summary_day 
                ON feature_usage_daily_summary(day);
            """)
            
            await self.session.execute(daily_stats_view)
            
            # Создаем материализованное представление для статистики пользователей
            user_stats_view = text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS user_activity_summary AS
                SELECT 
                    user_id,
                    COUNT(*) AS total_actions,
                    MIN(created_at) AS first_action,
                    MAX(created_at) AS last_action,
                    COUNT(DISTINCT DATE_TRUNC('day', created_at)) AS active_days
                FROM 
                    feature_usage
                GROUP BY 
                    user_id;
                
                CREATE INDEX IF NOT EXISTS idx_user_activity_summary_user_id 
                ON user_activity_summary(user_id);
            """)
            
            await self.session.execute(user_stats_view)
            
            # Коммитим изменения
            await self.session.commit()
            
            logger.info("Created materialized views for analytics")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating materialized views: {str(e)}")

    async def refresh_materialized_views(self) -> None:
        """Обновление материализованных представлений"""
        try:
            # Обновляем материализованное представление для ежедневной статистики
            refresh_daily_stats = text("""
                REFRESH MATERIALIZED VIEW feature_usage_daily_summary;
            """)
            
            await self.session.execute(refresh_daily_stats)
            
            # Обновляем материализованное представление для статистики пользователей
            refresh_user_stats = text("""
                REFRESH MATERIALIZED VIEW user_activity_summary;
            """)
            
            await self.session.execute(refresh_user_stats)
            
            # Коммитим изменения
            await self.session.commit()
            
            logger.info("Refreshed materialized views for analytics")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error refreshing materialized views: {str(e)}")

    async def track_purchase(
            self,
            user_id: int,
            purchase_type: str,  # 'tariff' или 'points'
            amount: float,
            item_id: Optional[str] = None,
            item_name: Optional[str] = None,
            discount: Optional[float] = None,
            payment_method: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Отслеживание покупок тарифов и баллов с оптимизированной обработкой"""
        try:
            # Создаем запись покупки
            purchase_record = {
                "user_id": user_id,
                "purchase_type": purchase_type,
                "amount": amount,
                "item_id": item_id,
                "item_name": item_name,
                "discount": discount,
                "payment_method": payment_method,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            # Добавляем запись в очередь для пакетной обработки через фоновую задачу
            task = asyncio.create_task(
                self._process_purchase_record([purchase_record]) # Передаем список с одним элементом
            )
            self.background_tasks.append(task)
            # Очищаем завершенные задачи (опционально, можно делать реже)
            self.background_tasks = [t for t in self.background_tasks if not t.done()]

            # Инвалидируем кэш аналитики
            await self.cache.invalidate_pattern("analytics:purchases:*") # Исправлено: invalidate_by_prefix -> invalidate_pattern
            await self.cache.invalidate_pattern("dashboard:stats:*") # Исправлено: invalidate_by_prefix -> invalidate_pattern
            
            logger.info(f"Purchase tracked: {purchase_type} for user {user_id}, amount: {amount}")
        except Exception as e:
            logger.error(f"Error tracking purchase: {str(e)}")
    
    async def _process_purchase_record(self, purchase_records: List[Dict[str, Any]]) -> bool:
        """Обработка записей покупок"""
        try:
            if not purchase_records:
                return True

            # Готовим данные для bulk insert через SQLAlchemy Core
            values_to_insert = [
                {
                    "user_id": record["user_id"],
                    "purchase_type": record["purchase_type"],
                    "amount": record["amount"],
                    "item_id": record["item_id"],
                    "item_name": record["item_name"],
                    "discount": record["discount"],
                    "payment_method": record["payment_method"],
                    "purchase_metadata": record.get("metadata"), # Используем правильное имя колонки и ключ из record
                    "created_at": record["timestamp"]
                }
                for record in purchase_records
            ]

            # Создаем и выполняем insert statement
            stmt = insert(PurchaseAnalytics).values(values_to_insert)
            await self.session.execute(stmt)

            await self.session.commit()
            logger.info(f"Successfully processed {len(purchase_records)} purchase records using SQLAlchemy insert.")
            return True
        except Exception as e:
            logger.error(f"Error processing purchase records with SQLAlchemy insert: {str(e)}")
            await self.session.rollback()
            return False

    async def track_course_interaction(
            self,
            user_id: int,
            course_id: int,
            interaction_type: str,  # 'click', 'view', 'enroll', 'complete', etc.
            course_name: Optional[str] = None,
            section: Optional[str] = None,  # 'courses_list', 'dashboard', 'search', etc.
            metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Отслеживание взаимодействий с курсами, включая клики по кнопкам"""
        try:
            # Создаем запись взаимодействия
            interaction_record = {
                "user_id": user_id,
                "course_id": course_id,
                "interaction_type": interaction_type,
                "course_name": course_name,
                "section": section,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            # Добавляем запись в очередь для пакетной обработки через фоновую задачу
            task = asyncio.create_task(
                self._process_course_interaction([interaction_record]) # Передаем список с одним элементом
            )
            self.background_tasks.append(task)
            # Очищаем завершенные задачи (опционально, можно делать реже)
            self.background_tasks = [t for t in self.background_tasks if not t.done()]
            
            # Инвалидируем кэш аналитики
            await self.cache.invalidate_pattern("analytics:courses:*") # Исправлено: invalidate_by_prefix -> invalidate_pattern
            
            logger.info(f"Course interaction tracked: {interaction_type} for course {course_id} by user {user_id}")
        except Exception as e:
            logger.error(f"Error tracking course interaction: {str(e)}")
    
    async def _process_course_interaction(self, interaction_records: List[Dict[str, Any]]) -> bool:
        """Обработка записей взаимодействий с курсами"""
        try:
            if not interaction_records:
                return True
                
            # Создаем запрос для пакетной вставки
            query = text("""
                INSERT INTO course_interaction_analytics 
                (user_id, course_id, interaction_type, course_name, section, metadata, created_at)
                VALUES (:user_id, :course_id, :interaction_type, :course_name, :section, :metadata, :timestamp)
            """)
            
            # Выполняем пакетную вставку
            await self.session.execute(
                query,
                [
                    {
                        "user_id": record["user_id"],
                        "course_id": record["course_id"],
                        "interaction_type": record["interaction_type"],
                        "course_name": record["course_name"],
                        "section": record["section"],
                        "metadata": record["metadata"],
                        "timestamp": record["timestamp"]
                    }
                    for record in interaction_records
                ]
            )
            
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error processing course interaction records: {str(e)}")
            await self.session.rollback()
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ждем завершения всех фоновых задач
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
