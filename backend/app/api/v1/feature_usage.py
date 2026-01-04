import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.security import get_current_admin_user
from ...services.analytics.feature_usage import FeatureUsageService
from ...services.optimization.query_optimizer import QueryOptimizer
from ...core.cache import CacheService, get_cache_service
from ...models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Время кеширования для аналитики
ANALYTICS_CACHE_TTL = 300  # 5 минут



@router.get("/admin/analytics/features")
async def get_feature_analytics(
    period: str = Query("week", regex="^(day|week|month)$"),
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить аналитику использования функций"""
    try:
        # Проверяем кеш
        cache_key = f"feature_analytics:{period}"
        cached_data = await cache.get_cached_data(cache_key)
        if cached_data:
            return cached_data

        end_date = datetime.utcnow()
        start_date = _calculate_start_date(end_date, period)

        # Используем асинхронные запросы через QueryOptimizer
        async with QueryOptimizer(session) as query_optimizer:
            feature_stats, user_dist, success_rates = await asyncio.gather(
                query_optimizer.get_feature_usage_stats(
                    start_date=start_date,
                    end_date=end_date
                ),
                query_optimizer.get_user_distribution(
                    start_date=start_date,
                    end_date=end_date
                ),
                query_optimizer.get_feature_success_rates(
                    start_date=start_date,
                    end_date=end_date
                )
            )

            analytics_data = {
                "totalUsage": feature_stats.get('total', 0),
                "uniqueUsers": feature_stats.get('users', 0),
                "featureDistribution": feature_stats.get('distribution', {}),
                "userDistribution": user_dist,
                "successRates": success_rates,
                "mostPopular": feature_stats.get('most_popular', []),
                "leastUsed": feature_stats.get('least_used', []),
                "period": period,
                "generatedAt": datetime.utcnow().isoformat()
            }

            # Кешируем результат
            await cache.cache_data(cache_key, analytics_data, ttl=ANALYTICS_CACHE_TTL)
            return analytics_data

    except Exception as e:
        logger.error(f"Error getting feature analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching feature analytics: {str(e)}"
        )

@router.get("/admin/analytics/features/detailed")
async def get_detailed_feature_analytics(
    feature_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить детальную аналитику использования функций"""
    try:
        # Проверяем кеш
        cache_key = (
            f"feature_analytics_detailed:"
            f"{feature_type or 'all'}:"
            f"{start_date.date() if start_date else 'default'}:"
            f"{end_date.date() if end_date else 'default'}"
        )

        cached_data = await cache.get_cached_data(cache_key)
        if cached_data:
            return cached_data

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="End date must be greater than start date"
            )

        # Используем асинхронные запросы через QueryOptimizer
        async with QueryOptimizer(session) as query_optimizer:
            feature_usage_service = FeatureUsageService(session)

            # Получаем агрегированные данные
            analytics = await feature_usage_service.get_feature_analytics_detailed(
                start_date=start_date,
                end_date=end_date,
                feature_type=feature_type
            )

            # Если указан конкретный тип функции
            if feature_type:
                detailed_data = {
                    "feature": feature_type,
                    "usage": analytics["feature_distribution"].get(feature_type, {}),
                    "user_distribution": {
                        "by_role": analytics["user_distribution"]["by_role"].get(feature_type, {}),
                        "by_tariff": analytics["user_distribution"]["by_tariff"].get(feature_type, {})
                    },
                    "performance": analytics["performance"].get(feature_type, {}),
                    "errors": analytics["errors"].get(feature_type, {}),
                    "generated_at": datetime.utcnow().isoformat()
                }
            else:
                detailed_data = {
                    "features": analytics["feature_distribution"],
                    "user_distribution": analytics["user_distribution"],
                    "performance": analytics["performance"],
                    "errors": analytics["errors"],
                    "generated_at": datetime.utcnow().isoformat()
                }

            # Кешируем результат
            await cache.cache_data(cache_key, detailed_data, ANALYTICS_CACHE_TTL)

            return detailed_data

    except Exception as e:
        logger.error(f"Error fetching detailed feature analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch detailed feature analytics: {str(e)}"
        )

def _calculate_start_date(end_date: datetime, period: str) -> datetime:
    """Вспомогательная функция для расчета начальной даты"""
    if period == 'day':
        return end_date - timedelta(days=1)
    elif period == 'week':
        return end_date - timedelta(days=7)
    return end_date - timedelta(days=30)