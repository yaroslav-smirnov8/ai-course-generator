from sqlalchemy import text, func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class QueryOptimizer:
    def __init__(self, session: AsyncSession):
        if not isinstance(session, AsyncSession):
            raise ValueError("Session must be AsyncSession instance")
        self.session = session

    async def optimize_query(self, query):
        """
        Оптимизирует запрос, добавляя нужные опции
        """
        optimized = query

        # Добавляем опции загрузки для ORM запросов
        if hasattr(query, 'statement'):
            optimized = optimized.options(
                selectinload('*')
            )

        return optimized

    async def execute_optimized(self, query, single=True):
        """Выполняет оптимизированный запрос"""
        try:
            optimized = await self.optimize_query(query)
            result = await self.session.execute(optimized)

            if single:
                return result.scalar_one_or_none()
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error executing optimized query: {str(e)}")
            raise

    async def get_user_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Получение статистики по пользователям"""
        try:
            total_users = await self.session.scalar(
                select(func.count()).select_from(text('users'))
            )

            active_users = await self.session.scalar(
                select(func.count())
                .select_from(text('users'))
                .where(
                    and_(
                        text('users.last_active >= :start_date'),
                        text('users.last_active <= :end_date')
                    )
                ),
                {'start_date': start_date, 'end_date': end_date}
            )

            new_users = await self.session.scalar(
                select(func.count())
                .select_from(text('users'))
                .where(
                    and_(
                        text('users.created_at >= :start_date'),
                        text('users.created_at <= :end_date')
                    )
                ),
                {'start_date': start_date, 'end_date': end_date}
            )

            return {
                'total': total_users or 0,
                'active': active_users or 0,
                'new': new_users or 0
            }
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {'total': 0, 'active': 0, 'new': 0}

    async def get_generation_metrics(self) -> Dict[str, Any]:
        """Получение метрик генераций"""
        try:
            query = text("""
                WITH generation_stats AS (
                    SELECT
                        type,
                        COUNT(*) as count,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM generations
                    WHERE DATE(created_at) = CURRENT_DATE
                    GROUP BY type
                )
                SELECT
                    type,
                    count,
                    unique_users
                FROM generation_stats
            """)

            result = await self.session.execute(query)
            metrics = {}
            for row in result:
                metrics[row.type] = {
                    'count': row.count,
                    'unique_users': row.unique_users
                }

            return metrics
        except Exception as e:
            logger.error(f"Error getting generation metrics: {str(e)}")
            return {}

    async def get_feature_usage_stats(self, start_date: datetime = None, end_date: datetime = None, days: int = 30) -> Dict[str, Any]:
        """Получение статистики использования функций"""
        try:
            # Если даты не указаны, используем days для вычисления периода
            if start_date is None or end_date is None:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)

            query = text("""
                WITH feature_stats AS (
                    SELECT
                        feature_type,
                        COUNT(*) as total_uses,
                        COUNT(DISTINCT user_id) as unique_users,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100 as success_rate
                    FROM feature_usage
                    WHERE created_at BETWEEN :start_date AND :end_date
                    GROUP BY feature_type
                ),
                total_stats AS (
                    SELECT SUM(total_uses) as grand_total
                    FROM feature_stats
                )
                SELECT
                    fs.feature_type,
                    fs.total_uses,
                    fs.unique_users,
                    ROUND(fs.success_rate::numeric, 2) as success_rate,
                    ROUND((fs.total_uses::float / ts.grand_total::float * 100)::numeric, 2) as percentage
                FROM feature_stats fs
                CROSS JOIN total_stats ts
                ORDER BY fs.total_uses DESC
            """)

            result = await self.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            })

            stats = {}
            total_uses = 0
            unique_users_count = 0
            features_list = []

            for row in result:
                feature_data = {
                    'total_usage': row.total_uses,
                    'unique_users': row.unique_users,
                    'success_rate': row.success_rate,
                    'percentage': row.percentage
                }
                stats[row.feature_type] = feature_data
                total_uses += row.total_uses
                unique_users_count = max(unique_users_count, row.unique_users)

                features_list.append({
                    'feature': row.feature_type,
                    'count': row.total_uses,
                    'percentage': row.percentage
                })

            # Формируем most_popular и least_used
            most_popular = features_list[:5] if features_list else []
            least_used = features_list[-3:] if len(features_list) > 3 else []

            # Добавляем общую статистику
            return {
                'total': total_uses,
                'users': unique_users_count,
                'distribution': stats,
                'most_popular': most_popular,
                'least_used': least_used
            }
        except Exception as e:
            logger.error(f"Error getting feature usage stats: {str(e)}")
            return {
                'total': 0,
                'users': 0,
                'distribution': {},
                'most_popular': [],
                'least_used': []
            }

    async def get_user_retention(self) -> Dict[str, Any]:
        """Получение данных по удержанию пользователей"""
        try:
            query = text("""
                WITH user_cohorts AS (
                    SELECT
                        DATE_TRUNC('month', created_at) as cohort_month,
                        COUNT(DISTINCT id) as cohort_size,
                        COUNT(DISTINCT CASE
                            WHEN last_active >= NOW() - INTERVAL '30 days'
                            THEN id
                        END) as retained_users
                    FROM users
                    GROUP BY DATE_TRUNC('month', created_at)
                )
                SELECT
                    TO_CHAR(cohort_month, 'YYYY-MM') as cohort,
                    cohort_size,
                    retained_users,
                    ROUND((retained_users::float / NULLIF(cohort_size, 0)::float * 100)::numeric, 2) as retention_rate
                FROM user_cohorts
                ORDER BY cohort_month DESC
                LIMIT 12
            """)

            result = await self.session.execute(query)
            return {row.cohort: {
                'size': row.cohort_size,
                'retained': row.retained_users,
                'rate': row.retention_rate
            } for row in result}
        except Exception as e:
            logger.error(f"Error getting user retention: {str(e)}")
            return {}

    async def get_daily_active_users(self) -> Dict[str, Any]:
        """Получение статистики активных пользователей за день"""
        try:
            query = text("""
                SELECT
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(*) as total_actions,
                    CASE
                        WHEN COUNT(DISTINCT user_id) > 0
                        THEN COUNT(*) / COUNT(DISTINCT user_id)::float
                        ELSE 0
                    END as actions_per_user
                FROM feature_usage
                WHERE DATE(created_at) = CURRENT_DATE
            """)

            result = await self.session.execute(query)
            row = result.first()
            return {
                'active_users': row.active_users,
                'total_actions': row.total_actions,
                'actions_per_user': round(row.actions_per_user, 2)
            } if row else {'active_users': 0, 'total_actions': 0, 'actions_per_user': 0}
        except Exception as e:
            logger.error(f"Error getting daily active users: {str(e)}")
            return {'active_users': 0, 'total_actions': 0, 'actions_per_user': 0}

    async def get_tariff_usage(self) -> Dict[str, Any]:
        """Получение статистики использования тарифов"""
        try:
            query = text("""
                SELECT
                    tariff,
                    COUNT(*) as users_count,
                    SUM(points) as total_points,
                    AVG(points)::integer as avg_points
                FROM users
                WHERE tariff IS NOT NULL
                GROUP BY tariff
            """)

            result = await self.session.execute(query)
            tariffs = {}
            for row in result:
                tariffs[row.tariff] = {
                    'users_count': row.users_count,
                    'total_points': row.total_points,
                    'avg_points': row.avg_points
                }

            return tariffs
        except Exception as e:
            logger.error(f"Error getting tariff usage: {str(e)}")
            return {}

    async def get_user_distribution(self, start_date: datetime = None, end_date: datetime = None, days: int = 30) -> Dict[str, Any]:
        """Получение распределения пользователей по тарифам (роли не используются)"""
        try:
            # Если даты не указаны, используем days для вычисления периода
            if start_date is None or end_date is None:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)

            # Сначала проверяем, существует ли таблица feature_usage
            check_table_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'feature_usage'
                )
            """)

            table_exists_result = await self.session.execute(check_table_query)
            table_exists = table_exists_result.scalar()

            if not table_exists:
                # Если таблица не существует, возвращаем данные из таблицы users
                fallback_query = text("""
                    SELECT
                        COALESCE(tariff, 'free') as tariff,
                        COUNT(*) as user_count,
                        COUNT(*) as usage_count
                    FROM users
                    WHERE created_at BETWEEN :start_date AND :end_date
                    GROUP BY tariff
                """)

                result = await self.session.execute(fallback_query, {
                    'start_date': start_date,
                    'end_date': end_date
                })

                distribution = {}
                for row in result:
                    distribution[row.tariff] = {
                        'user_count': row.user_count,
                        'usage_count': row.usage_count
                    }

                return distribution

            # Запрос для распределения по тарифам
            tariff_query = text("""
                SELECT
                    COALESCE(u.tariff, 'free') as tariff,
                    COUNT(DISTINCT f.user_id) as user_count,
                    COUNT(*) as usage_count
                FROM feature_usage f
                JOIN users u ON f.user_id = u.id
                WHERE f.created_at BETWEEN :start_date AND :end_date
                GROUP BY u.tariff
            """)

            tariff_result = await self.session.execute(tariff_query, {
                'start_date': start_date,
                'end_date': end_date
            })

            tariff_dist = {}
            total_users = 0
            total_usage = 0

            for row in tariff_result:
                tariff_dist[row.tariff] = {
                    'count': row.user_count,
                    'usage_count': row.usage_count
                }
                total_users += row.user_count
                total_usage += row.usage_count

            # Добавляем проценты
            for tariff in tariff_dist:
                tariff_dist[tariff]['percentage'] = (
                    (tariff_dist[tariff]['count'] / total_users * 100) if total_users > 0 else 0
                )

            return {
                'by_role': {},  # Пустой, так как роли не используются
                'by_tariff': tariff_dist
            }
        except Exception as e:
            logger.error(f"Error getting user distribution: {str(e)}")
            return {
                'by_role': {},
                'by_tariff': {}
            }

    async def get_feature_success_rates(self, start_date: datetime = None, end_date: datetime = None, days: int = 30) -> Dict[str, Any]:
        """Получение статистики успешности использования функций"""
        try:
            # Если даты не указаны, используем days для вычисления периода
            if start_date is None or end_date is None:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)

            query = text("""
                SELECT
                    feature_type,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_attempts,
                    ROUND((SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100)::numeric, 2) as success_rate,
                    COUNT(DISTINCT error_type) as error_types_count
                FROM feature_usage
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY feature_type
            """)

            result = await self.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            })

            success_rates = {}
            for row in result:
                success_rates[row.feature_type] = {
                    'total_attempts': row.total_attempts,
                    'successful_attempts': row.successful_attempts,
                    'success_rate': row.success_rate,
                    'error_types_count': row.error_types_count
                }

            return success_rates
        except Exception as e:
            logger.error(f"Error getting feature success rates: {str(e)}")
            return {}

    async def get_total_generations(self, start_date: datetime, end_date: datetime) -> int:
        """Получение общего количества генераций за период"""
        try:
            query = text("""
                SELECT COUNT(*) as total
                FROM generations
                WHERE created_at BETWEEN :start_date AND :end_date
            """)

            result = await self.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            })

            row = result.first()
            return row.total if row else 0
        except Exception as e:
            logger.error(f"Error getting total generations: {str(e)}")
            return 0

    async def get_images_count(self, start_date: datetime, end_date: datetime) -> int:
        """Получение количества сгенерированных изображений за период"""
        try:
            query = text("""
                SELECT COUNT(*) as total
                FROM generations
                WHERE type = 'IMAGE' AND created_at BETWEEN :start_date AND :end_date
            """)

            result = await self.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            })

            row = result.first()
            return row.total if row else 0
        except Exception as e:
            logger.error(f"Error getting images count: {str(e)}")
            return 0

    async def get_popular_prompts(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получение популярных запросов за период"""
        try:
            query = text("""
                SELECT
                    prompt,
                    COUNT(*) as count
                FROM generations
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY prompt
                ORDER BY count DESC
                LIMIT :limit
            """)

            result = await self.session.execute(query, {
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            })

            return [
                {
                    "prompt": row.prompt,
                    "count": row.count
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting popular prompts: {str(e)}")
            return []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()