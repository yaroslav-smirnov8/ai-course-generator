from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, text, delete, and_, desc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
import logging
import asyncio
from sqlalchemy.exc import SQLAlchemyError
from ...models import (
    FeatureUsage,
    FeatureUsageMetrics,
    User,
    DetailedGenerationMetrics
)
from ...core.constants import ContentType, UserRole
from ...services.optimization import QueryOptimizer, BatchProcessor
from ...core.cache import CacheService
from ...core.database import async_session

logger = logging.getLogger(__name__)


class FeatureUsageService:
    """Service for tracking and analyzing feature usage with optimization"""

    # Оптимизированные константы
    DEFAULT_BATCH_SIZE = 200  # Увеличенный размер пакета для снижения количества операций
    DEFAULT_CACHE_TTL = 3600  # 1 час
    DEFAULT_CLEANUP_DAYS = 90
    DASHBOARD_CACHE_TTL = 600  # 10 минут для дашборда
    ANALYTICS_CACHE_TTL = 1800  # 30 минут для аналитики

    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session, batch_size=self.DEFAULT_BATCH_SIZE)
        self.cache = CacheService(session)
        self.cache_ttl = self.DEFAULT_CACHE_TTL
        # Список для отслеживания фоновых задач
        self.background_tasks = []


    async def track_feature_usage(
            self,
            user_id: int,
            feature_type: str,
            content_type: Optional[str] = None,  # Changed from ContentType to str
            success: bool = True,
            usage_data: Dict = None,
            error_type: Optional[str] = None,
            generation_time: Optional[float] = None,
            tokens_used: Optional[int] = None
    ) -> None:
        """Track feature usage with optimized batch processing"""
        try:
            # Convert string content_type to ContentType enum if needed
            content_type_enum = None
            if content_type:
                try:
                    content_type_enum = ContentType(content_type)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid content_type: {content_type}. Error: {str(e)}")
                    # We'll keep the conversion error but continue with None

            # Create usage record
            usage_record = {
                'user_id': user_id,
                'feature_type': feature_type,
                'content_type': content_type_enum,  # Use converted enum or None
                'success': success,
                'usage_data': usage_data or {},
                'error_type': error_type,
                'created_at': datetime.utcnow()
            }

            # Создаем асинхронную задачу для обработки записи с новой сессией
            # Это позволит не блокировать основной поток выполнения и избежать проблем с транзакциями
            task = asyncio.create_task(
                self._process_usage_record_with_new_session(usage_record)
            )
            
            # Добавляем задачу в список для отслеживания
            self.background_tasks.append(task)
            
            # Очищаем завершенные задачи
            self.background_tasks = [t for t in self.background_tasks if not t.done()]
                
            # If generation metrics provided, track them separately
            if content_type and generation_time and tokens_used is not None:
                # Создаем асинхронную задачу для сохранения метрик с новой сессией
                metrics_task = asyncio.create_task(
                    self._save_generation_metrics_with_new_session(
                        user_id,
                        content_type_enum,
                        generation_time,
                        tokens_used,
                        success
                    )
                )
                
                # Добавляем задачу в список для отслеживания
                self.background_tasks.append(metrics_task)
                
                # Очищаем завершенные задачи
                self.background_tasks = [t for t in self.background_tasks if not t.done()]
                
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
            # Не поднимаем исключение, чтобы не прерывать основной поток

    async def _process_usage_record(self, usage_record: Dict) -> None:
        """Обработка одной записи использования функции"""
        try:
            # Создаем объект FeatureUsage
            feature_usage = FeatureUsage(**usage_record)
            
            # Добавляем запись в сессию
            self.session.add(feature_usage)
            
            # Коммитим изменения
            await self.session.commit()
            
            # Инвалидируем кэш аналитики
            await self.cache.invalidate_pattern("feature_usage:*")
            
        except Exception as e:
            # Безопасный откат транзакции
            try:
                # Проверяем наличие активной транзакции через _transaction
                if hasattr(self.session, '_transaction') and self.session._transaction:
                    await self.session.rollback()
            except Exception as rollback_error:
                # Если откат не удался, просто логируем ошибку и продолжаем
                logger.error(f"Error during rollback: {str(rollback_error)}")
            
            logger.error(f"Error processing usage record: {str(e)}")

    async def _save_generation_metrics(
            self, 
            user_id: int, 
            content_type: ContentType, 
            generation_time: float, 
            tokens_used: int, 
            success: bool
    ) -> None:
        """Сохранение метрик генерации"""
        try:
            # Создаем объект метрик
            metrics = DetailedGenerationMetrics(
                user_id=user_id,
                content_type=content_type,
                generation_time=generation_time,
                tokens_used=tokens_used,
                success=success,
                created_at=datetime.utcnow()
            )
            
            # Добавляем запись в сессию
            self.session.add(metrics)
            
            # Коммитим изменения
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
        """Получение аналитики использования функций с оптимизированными запросами"""
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
            
            # Проверяем наличие материализованного представления
            # Если оно есть, используем его для ускорения запросов
            has_materialized_view = await self._check_materialized_view_exists('feature_usage_daily_summary')
            
            if has_materialized_view and period in ['week', 'month', 'year']:
                # Используем материализованное представление для более быстрого запроса
                query = text("""
                    SELECT 
                        feature_type,
                        content_type,
                        SUM(total_count) as count,
                        SUM(unique_users) as unique_users,
                        AVG(success_rate) as success_rate
                    FROM 
                        feature_usage_daily_summary
                    WHERE 
                        day >= :start_date
                """)
                
                params = {"start_date": start_date}
                
                if feature_type:
                    query = text(f"{query.text} AND feature_type = :feature_type")
                    params["feature_type"] = feature_type
                    
                if content_type:
                    query = text(f"{query.text} AND content_type = :content_type")
                    params["content_type"] = content_type
                    
                query = text(f"{query.text} GROUP BY feature_type, content_type ORDER BY count DESC")
                
                result = await self.session.execute(query, params)
                rows = result.fetchall()
            else:
                # Используем обычный запрос для детальных данных
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
                
                if feature_type:
                    query = query.where(FeatureUsage.feature_type == feature_type)
                if content_type:
                    query = query.where(FeatureUsage.content_type == content_type)
                    
                query = query.group_by(
                    FeatureUsage.feature_type,
                    FeatureUsage.content_type
                ).order_by(
                    func.count().desc()
                )
                
                result = await self.session.execute(query)
                rows = result.fetchall()
            
            # Формируем результат
            analytics_data = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'features': []
            }
            
            total_count = 0
            unique_users_set = set()
            
            for row in rows:
                feature_data = {
                    'feature_type': row.feature_type,
                    'content_type': row.content_type,
                    'count': row.count,
                    'unique_users': row.unique_users,
                    'success_rate': float(row.success_rate) if row.success_rate is not None else 0.0
                }
                analytics_data['features'].append(feature_data)
                total_count += row.count
                
                # Для точного подсчета уникальных пользователей нам нужны их ID
                # Но в материализованном представлении у нас только агрегированные данные
                # Поэтому мы просто суммируем уникальных пользователей по каждой функции
                # Это даст приблизительное значение, но достаточное для аналитики
                unique_users_set.add(row.unique_users)
            
            analytics_data['total_count'] = total_count
            analytics_data['unique_users'] = sum(unique_users_set)
            
            # Кэшируем результат
            await self.cache.cache_data(
                cache_key,
                analytics_data,
                ttl=self.ANALYTICS_CACHE_TTL
            )
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error getting feature usage analytics: {str(e)}")
            return {
                'period': period,
                'error': str(e),
                'features': []
            }

    async def _check_materialized_view_exists(self, view_name: str) -> bool:
        """Проверка существования материализованного представления"""
        try:
            query = text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_matviews 
                    WHERE matviewname = :view_name
                )
            """)
            
            result = await self.session.execute(query, {"view_name": view_name})
            return result.scalar() or False
        except Exception as e:
            logger.error(f"Error checking materialized view: {str(e)}")
            return False

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
            """)
            
            await self.session.execute(daily_stats_view)
            
            # Создаем индекс для материализованного представления отдельным запросом
            daily_stats_index = text("""
                CREATE INDEX IF NOT EXISTS idx_feature_usage_daily_summary_day 
                ON feature_usage_daily_summary(day);
            """)
            
            await self.session.execute(daily_stats_index)
            
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
            """)
            
            await self.session.execute(user_stats_view)
            
            # Создаем индекс для материализованного представления отдельным запросом
            user_stats_index = text("""
                CREATE INDEX IF NOT EXISTS idx_user_activity_summary_user_id 
                ON user_activity_summary(user_id);
            """)
            
            await self.session.execute(user_stats_index)
            
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

    async def cleanup_old_data(self) -> None:
        """Очистка устаревших данных аналитики"""
        try:
            # Определяем дату для очистки
            cutoff_date = datetime.utcnow() - timedelta(days=self.DEFAULT_CLEANUP_DAYS)
            
            # Удаляем устаревшие данные
            delete_query = text("""
                DELETE FROM feature_usage
                WHERE created_at < :cutoff_date
            """)
            
            await self.session.execute(delete_query, {"cutoff_date": cutoff_date})
            
            # Удаляем устаревшие метрики
            delete_metrics_query = text("""
                DELETE FROM detailed_generation_metrics
                WHERE date < :cutoff_date
            """)
            
            await self.session.execute(delete_metrics_query, {"cutoff_date": cutoff_date})
            
            # Коммитим изменения
            await self.session.commit()
            
            # Обновляем материализованные представления
            await self.refresh_materialized_views()
            
            logger.info(f"Cleaned up analytics data older than {cutoff_date}")
            
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

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ждем завершения всех фоновых задач
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

    async def _process_usage_record_with_new_session(self, usage_record: Dict) -> None:
        """Обработка одной записи использования функции с новой сессией"""
        # Создаем новую сессию для изоляции от основной транзакции
        async with async_session() as session:
            try:
                # Создаем объект FeatureUsage
                feature_usage = FeatureUsage(**usage_record)
                
                # Добавляем запись в сессию
                session.add(feature_usage)
                
                # Коммитим изменения
                await session.commit()
                
                # Инвалидируем кэш аналитики
                cache = CacheService(session)
                await cache.invalidate_pattern("feature_usage:*")
                
            except Exception as e:
                # Безопасный откат транзакции
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback in new session: {str(rollback_error)}")
                
                logger.error(f"Error processing usage record with new session: {str(e)}")

    async def _save_generation_metrics_with_new_session(
            self, 
            user_id: int, 
            content_type: ContentType, 
            generation_time: float, 
            tokens_used: int, 
            success: bool
    ) -> None:
        """Сохранение метрик генерации с новой сессией"""
        # Создаем новую сессию для изоляции от основной транзакции
        async with async_session() as session:
            try:
                # Создаем запись метрик
                metrics = DetailedGenerationMetrics(
                    user_id=user_id,
                    content_type=content_type,
                    generation_time=generation_time,
                    tokens_used=tokens_used,
                    success=success,
                    date=datetime.utcnow().date()
                )
                
                # Добавляем запись в сессию
                session.add(metrics)
                
                # Коммитим изменения
                await session.commit()
                
                # Инвалидируем кэш аналитики
                cache = CacheService(session)
                await cache.invalidate_pattern("generation_metrics:*")
                
            except Exception as e:
                # Безопасный откат транзакции
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback in new session: {str(rollback_error)}")
                
                logger.error(f"Error saving generation metrics with new session: {str(e)}")

class AchievementManager:
    # ... existing code ...
    
    async def get_available_achievements(self, user_id=None):
        """
        Получить список доступных достижений
        
        Args:
            user_id: ID пользователя (опционально)
            
        Returns:
            List[Dict]: Список достижений
        """
        try:
            # Базовый список достижений
            achievements = [
                {
                    "id": "first_generation",
                    "code": "first_generation",
                    "name": "First Generation",
                    "description": "Create your first content",
                    "icon": "🎯",
                    "conditions": {"generations_count": 1},
                    "points_reward": 10
                },
                {
                    "id": "power_user",
                    "code": "power_user",
                    "name": "Power User",
                    "description": "Create 10 generations",
                    "icon": "⚡",
                    "conditions": {"generations_count": 10},
                    "points_reward": 50
                },
                {
                    "id": "content_master",
                    "code": "content_master",
                    "name": "Content Master",
                    "description": "Create 50 generations",
                    "icon": "🏆",
                    "conditions": {"generations_count": 50},
                    "points_reward": 200
                }
            ]
            
            # Если указан пользователь, можно добавить информацию о прогрессе
            if user_id:
                # Здесь можно добавить логику получения прогресса пользователя
                pass
                
            return achievements
        except Exception as e:
            logger.error(f"Error getting available achievements: {str(e)}")
            return []