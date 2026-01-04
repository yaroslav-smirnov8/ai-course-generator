from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ...models import (
    User,
    Generation,
    Image,
    UsageLog,
    TariffPlan,
    UserTariff,
    DailyUsage,
    ServerStatistics
)
from ...core.constants import StatisticsPeriod, StatisticsMetric
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
import logging
import psutil
import asyncio

logger = logging.getLogger(__name__)


class StatisticsCollector:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = BatchProcessor(session)

    async def get_user_statistics(
            self,
            period: StatisticsPeriod,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получает статистику по пользователям"""
        try:
            if not start_date:
                start_date = self._get_start_date(period)
            if not end_date:
                end_date = datetime.utcnow()

            total_users, new_users, active_users, users_with_tariffs = await asyncio.gather(
                self.query_optimizer.get_total_users(),
                self.query_optimizer.get_new_users(start_date, end_date),
                self.query_optimizer.get_active_users(start_date, end_date),
                self.query_optimizer.get_users_with_tariffs()
            )

            tariff_distribution = await self._get_tariff_distribution()

            return {
                "total_users": total_users,
                "new_users": new_users,
                "active_users": active_users,
                "users_with_tariffs": users_with_tariffs,
                "tariff_distribution": tariff_distribution,
                "period": period.value,
                "start_date": start_date,
                "end_date": end_date
            }

        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            raise

    async def get_generation_statistics(
            self,
            period: StatisticsPeriod,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получает статистику по генерациям"""
        try:
            if not start_date:
                start_date = self._get_start_date(period)
            if not end_date:
                end_date = datetime.utcnow()

            total_generations, generations_by_type, images_count, popular_prompts = await asyncio.gather(
                self.query_optimizer.get_total_generations(start_date, end_date),
                self._get_generations_by_type(start_date, end_date),
                self.query_optimizer.get_images_count(start_date, end_date),
                self._get_popular_prompts(start_date, end_date)
            )

            return {
                "total_generations": total_generations,
                "images_count": images_count,
                "generations_by_type": generations_by_type,
                "popular_prompts": popular_prompts,
                "period": period.value,
                "start_date": start_date,
                "end_date": end_date
            }

        except Exception as e:
            logger.error(f"Error getting generation statistics: {str(e)}")
            raise

    async def get_tariff_statistics(
            self,
            period: StatisticsPeriod
    ) -> Dict[str, Any]:
        """Получает статистику по тарифам"""
        try:
            start_date = self._get_start_date(period)

            purchases = await self.query_optimizer.get_tariff_purchases(start_date)
            purchases_by_tariff = await self._get_purchases_by_tariff(start_date)

            total_purchases = len(purchases)
            total_points = sum(p.points_spent for p in purchases if p.points_spent)
            avg_discount = await self._calculate_average_discount(purchases)

            return {
                "total_purchases": total_purchases,
                "total_points_spent": total_points,
                "average_discount": avg_discount,
                "purchases_by_tariff": purchases_by_tariff,
                "period": period.value
            }

        except Exception as e:
            logger.error(f"Error getting tariff statistics: {str(e)}")
            raise

    async def get_server_statistics(
            self,
            period: StatisticsPeriod,
            metric: StatisticsMetric
    ) -> Dict[str, Any]:
        """Получает статистику по серверу"""
        try:
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent

            server_stats = ServerStatistics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                timestamp=datetime.utcnow()
            )

            self.session.add(server_stats)
            await self.session.flush()
            await self.session.commit()

            start_date = self._get_start_date(period)
            metrics_history = await self._get_metrics_history(start_date, metric)

            return {
                "current": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "disk_usage": disk_usage
                },
                "history": metrics_history,
                "period": period.value
            }

        except Exception as e:
            logger.error(f"Error getting server statistics: {str(e)}")
            await self.session.rollback()
            raise

    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Получает общую статистику для дашборда"""
        try:
            yesterday = datetime.utcnow() - timedelta(days=1)

            new_users_24h, generations_24h, active_users_24h = await asyncio.gather(
                self.query_optimizer.get_new_users(yesterday, datetime.utcnow()),
                self.query_optimizer.get_total_generations(yesterday, datetime.utcnow()),
                self.query_optimizer.get_active_users(yesterday, datetime.utcnow())
            )

            return {
                "last_24h": {
                    "new_users": new_users_24h,
                    "generations": generations_24h,
                    "active_users": active_users_24h
                },
                "system_health": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                },
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {str(e)}")
            raise

    def _get_start_date(self, period: StatisticsPeriod) -> datetime:
        """Получает начальную дату для периода"""
        now = datetime.utcnow()
        if period == StatisticsPeriod.DAY:
            return now - timedelta(days=1)
        elif period == StatisticsPeriod.WEEK:
            return now - timedelta(weeks=1)
        else:  # MONTH
            return now - timedelta(days=30)

    async def _get_generations_by_type(
            self,
            start_date: datetime,
            end_date: datetime
    ) -> Dict[str, int]:
        """Получает количество генераций по типам"""
        try:
            query = select(Generation.type, func.count(Generation.id)).where(
                Generation.created_at.between(start_date, end_date)
            ).group_by(Generation.type)

            result = await self.session.execute(query)
            return {gen_type: count for gen_type, count in result.all()}

        except Exception as e:
            logger.error(f"Error getting generations by type: {str(e)}")
            return {}

    async def _get_popular_prompts(
            self,
            start_date: datetime,
            end_date: datetime,
            limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получает популярные запросы"""
        try:
            return await self.query_optimizer.get_popular_prompts(
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting popular prompts: {str(e)}")
            return []

    async def _get_tariff_distribution(self) -> Dict[str, int]:
        """Получает распределение пользователей по тарифам"""
        try:
            query = select(UserTariff.type, func.count(UserTariff.id)).where(
                UserTariff.expires_at > datetime.utcnow()
            ).group_by(UserTariff.type)

            result = await self.session.execute(query)
            return {tariff_type: count for tariff_type, count in result.all()}

        except Exception as e:
            logger.error(f"Error getting tariff distribution: {str(e)}")
            return {}

    async def _calculate_average_discount(
            self,
            purchases: List[UserTariff]
    ) -> float:
        """Рассчитывает средний размер скидки"""
        if not purchases:
            return 0.0

        total_discount = sum(p.discount_percent for p in purchases if p.discount_percent)
        return total_discount / len(purchases)

    async def _get_purchases_by_tariff(
            self,
            start_date: datetime
    ) -> Dict[str, Dict[str, int]]:
        """Получает статистику покупок по тарифам"""
        try:
            query = select(
                UserTariff.type,
                func.count(UserTariff.id).label('count'),
                func.sum(UserTariff.points_spent).label('points')
            ).where(
                UserTariff.created_at >= start_date
            ).group_by(UserTariff.type)

            result = await self.session.execute(query)
            return {
                tariff_type: {
                    "count": count,
                    "points": points or 0
                }
                for tariff_type, count, points in result.all()
            }

        except Exception as e:
            logger.error(f"Error getting purchases by tariff: {str(e)}")
            return {}

    async def _get_metrics_history(
            self,
            start_date: datetime,
            metric: StatisticsMetric
    ) -> List[Dict[str, Any]]:
        """Получает историю метрик сервера"""
        try:
            return await self.query_optimizer.get_server_metrics_history(
                start_date=start_date,
                metric=metric
            )
        except Exception as e:
            logger.error(f"Error getting metrics history: {str(e)}")
            return []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()