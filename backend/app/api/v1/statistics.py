from fastapi import APIRouter, Depends, HTTPException, Query
import asyncio # Добавлен импорт
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging
from fastapi.responses import StreamingResponse
from ...utils.excel_export import export_to_excel
from ...core.database import get_db
from ...core.cache import CacheService, get_cache_service
from ...services.statistics.collector import StatisticsCollector
from ...services.optimization.query_optimizer import QueryOptimizer
from ...core.constants import StatisticsPeriod, StatisticsMetric
from ...core.security import get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Константы для кеширования
STATISTICS_CACHE_TTL = {
   'dashboard': 300,  # 5 минут
   'users': 600,  # 10 минут
   'generations': 600,
   'tariffs': 1800,  # 30 минут
   'server': 60  # 1 минута
}


@router.get("/statistics/users")
async def get_user_statistics(
       period: StatisticsPeriod,
       start_date: Optional[datetime] = None,
       end_date: Optional[datetime] = None,
       session: AsyncSession = Depends(get_db),
       cache: CacheService = Depends(get_cache_service),
       _: dict = Depends(get_current_admin_user)
):
   """Получить статистику по пользователям"""
   try:
       cache_key = (
           f"user_stats:{period}:"
           f"{start_date.date() if start_date else 'default'}:"
           f"{end_date.date() if end_date else 'default'}"
       )

       cached_data = await cache.get_cached_data(cache_key)
       if cached_data:
           return cached_data

       async with StatisticsCollector(session) as collector:
           stats = await collector.get_user_statistics(period, start_date, end_date)

           await cache.cache_data(
               cache_key,
               stats,
               ttl=STATISTICS_CACHE_TTL['users']
           )

           return stats

   except Exception as e:
       logger.error(f"Error getting user statistics: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/generations")
async def get_generation_statistics(
       period: StatisticsPeriod,
       start_date: Optional[datetime] = None,
       end_date: Optional[datetime] = None,
       session: AsyncSession = Depends(get_db),
       cache: CacheService = Depends(get_cache_service),
       _: dict = Depends(get_current_admin_user)
):
   """Получить статистику по генерациям"""
   try:
       cache_key = (
           f"gen_stats:{period}:"
           f"{start_date.date() if start_date else 'default'}:"
           f"{end_date.date() if end_date else 'default'}"
       )

       cached_data = await cache.get_cached_data(cache_key)
       if cached_data:
           return cached_data

       async with StatisticsCollector(session) as collector:
           stats = await collector.get_generation_statistics(period, start_date, end_date)

           await cache.cache_data(
               cache_key,
               stats,
               ttl=STATISTICS_CACHE_TTL['generations']
           )

           return stats

   except Exception as e:
       logger.error(f"Error getting generation statistics: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/tariffs")
async def get_tariff_statistics(
       period: StatisticsPeriod,
       session: AsyncSession = Depends(get_db),
       cache: CacheService = Depends(get_cache_service),
       _: dict = Depends(get_current_admin_user)
):
   """Получить статистику по тарифам"""
   try:
       cache_key = f"tariff_stats:{period}"

       cached_data = await cache.get_cached_data(cache_key)
       if cached_data:
           return cached_data

       async with StatisticsCollector(session) as collector:
           stats = await collector.get_tariff_statistics(period)

           await cache.cache_data(
               cache_key,
               stats,
               ttl=STATISTICS_CACHE_TTL['tariffs']
           )

           return stats

   except Exception as e:
       logger.error(f"Error getting tariff statistics: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/server")
async def get_server_statistics(
       period: StatisticsPeriod,
       metric: StatisticsMetric,
       session: AsyncSession = Depends(get_db),
       cache: CacheService = Depends(get_cache_service),
       _: dict = Depends(get_current_admin_user)
):
   """Получить статистику по серверу"""
   try:
       cache_key = f"server_stats:{period}:{metric}"

       cached_data = await cache.get_cached_data(cache_key)
       if cached_data:
           return cached_data

       async with StatisticsCollector(session) as collector:
           stats = await collector.get_server_statistics(period, metric)

           await cache.cache_data(
               cache_key,
               stats,
               ttl=STATISTICS_CACHE_TTL['server']
           )

           return stats

   except Exception as e:
       logger.error(f"Error getting server statistics: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/dashboard")
async def get_dashboard_statistics(
       session: AsyncSession = Depends(get_db),
       cache: CacheService = Depends(get_cache_service),
       _: dict = Depends(get_current_admin_user)
):
   """Получить общую статистику для дашборда"""
   try:
       cache_key = f"dashboard_stats:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"

       cached_data = await cache.get_cached_data(cache_key)
       if cached_data:
           return cached_data

       async with StatisticsCollector(session) as collector:
           stats = await collector.get_dashboard_statistics()

           await cache.cache_data(
               cache_key,
               stats,
               ttl=STATISTICS_CACHE_TTL['dashboard']
           )

           return stats

   except Exception as e:
       logger.error(f"Error getting dashboard statistics: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


@router.post("/statistics/refresh")
async def refresh_statistics(
       stat_type: str = Query(..., regex="^(dashboard|users|generations|tariffs|server)$"),
       session: AsyncSession = Depends(get_db),
       cache: CacheService = Depends(get_cache_service),
       _: dict = Depends(get_current_admin_user)
):
   """Принудительное обновление статистики определенного типа"""
   try:
       # Инвалидируем кеш для указанного типа статистики
       await cache.invalidate_pattern(f"{stat_type}_stats:*")

       async with StatisticsCollector(session) as collector:
           # Пересчитываем статистику
           if stat_type == 'dashboard':
               return await collector.get_dashboard_statistics()
           elif stat_type == 'users':
               return await collector.get_user_statistics(StatisticsPeriod.DAY)
           elif stat_type == 'generations':
               return await collector.get_generation_statistics(StatisticsPeriod.DAY)
           elif stat_type == 'tariffs':
               return await collector.get_tariff_statistics(StatisticsPeriod.DAY)
           elif stat_type == 'server':
               return await collector.get_server_statistics(
                   StatisticsPeriod.DAY,
                   StatisticsMetric.SERVER
               )

   except Exception as e:
       logger.error(f"Error refreshing {stat_type} statistics: {str(e)}")
       raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/dashboard")
async def get_admin_dashboard(
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    _: dict = Depends(get_current_admin_user)
):
    """Получить данные для дашборда админки"""
    cache_key = f"admin_dashboard:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
    cached_data = await cache.get_cached_data(cache_key)
    if cached_data:
        return cached_data

    try:
        async with StatisticsCollector(session) as collector, \
                   QueryOptimizer(session) as optimizer:

            # Получаем основные метрики за последние 24 часа
            dashboard_stats_24h = await collector.get_dashboard_statistics()

            # Получаем общее количество пользователей и активных тарифов
            total_users, users_with_tariffs = await asyncio.gather(
                optimizer.get_total_users(),
                optimizer.get_users_with_tariffs()
            )

            # Получаем данные активности за последнюю неделю
            end_date = datetime.utcnow()
            start_date_week = end_date - timedelta(days=7)
            activity_data_week = await optimizer.get_daily_activity(start_date_week, end_date)

            # Получаем распределение использования фич за последние 30 дней
            start_date_month = end_date - timedelta(days=30)
            feature_stats_month = await optimizer.get_feature_usage_stats(start_date_month, end_date)

            # Получаем последние 5 действий (пример, можно заменить на реальный запрос)
            recent_actions = await optimizer.get_recent_actions(limit=5) # Предполагаем, что такой метод есть

            dashboard_data = {
                "stats": {
                    "totalUsers": total_users,
                    "usersTrend": dashboard_stats_24h.get("last_24h", {}).get("new_users", 0), # Пример тренда - новые за 24ч
                    "activeTariffs": users_with_tariffs,
                    "tariffsTrend": 0, # Заглушка для тренда тарифов
                    "dailyGenerations": dashboard_stats_24h.get("last_24h", {}).get("generations", 0),
                    "generationsTrend": 0, # Заглушка для тренда генераций
                    "featureUsage": feature_stats_month.get('total', 0),
                    "usageTrend": 0 # Заглушка для тренда использования
                },
                "activity": activity_data_week,
                "features": [
                    {"name": feature, "value": count}
                    for feature, count in feature_stats_month.get('distribution', {}).items()
                ],
                "recent": recent_actions,
                 "system_health": dashboard_stats_24h.get("system_health", {})
            }

            await cache.cache_data(cache_key, dashboard_data, ttl=STATISTICS_CACHE_TTL['dashboard'])
            return dashboard_data

    except Exception as e:
        logger.error(f"Error getting admin dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting admin dashboard: {str(e)}")


@router.get("/admin/analytics/activity")
async def get_activity_data(
    period: str = Query("week", regex="^(day|week|month)$"),
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    _: dict = Depends(get_current_admin_user)
):
    """Получить данные активности пользователей"""
    cache_key = f"admin_activity:{period}:{datetime.utcnow().strftime('%Y-%m-%d')}"
    cached_data = await cache.get_cached_data(cache_key)
    if cached_data:
        return cached_data

    try:
        end_date = datetime.utcnow()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else: # week
            start_date = end_date - timedelta(days=7)

        async with QueryOptimizer(session) as optimizer:
            activity_data = await optimizer.get_daily_activity(start_date, end_date)

        await cache.cache_data(cache_key, activity_data, ttl=STATISTICS_CACHE_TTL['dashboard']) # Используем TTL дашборда
        return activity_data

    except Exception as e:
        logger.error(f"Error getting activity data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting activity data: {str(e)}")


@router.get("/admin/generations")
async def get_detailed_generations(
    period: str = Query("week", regex="^(day|week|month|all|custom)$"),
    type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("created_at", regex="^(id|user_id|type|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    _: dict = Depends(get_current_admin_user)
):
    """Получить детальную информацию о генерациях с пагинацией, фильтрацией и сортировкой"""
    logger.info(f"=== ADMIN GENERATIONS API CALLED ===")
    logger.info(f"Parameters: period={period}, type={type}, user_id={user_id}, start_date={start_date}, end_date={end_date}, skip={skip}, limit={limit}, sort_by={sort_by}, sort_order={sort_order}")

    try:
        # Определяем временной период
        date_end = datetime.now(timezone.utc)

        if period == 'custom' and start_date and end_date:
            # Если указан кастомный период, используем переданные даты
            try:
                date_start = datetime.fromisoformat(start_date)
                if not date_start.tzinfo:
                    date_start = date_start.replace(tzinfo=timezone.utc)

                date_end = datetime.fromisoformat(end_date)
                if not date_end.tzinfo:
                    date_end = date_end.replace(tzinfo=timezone.utc)

                logger.info(f"Using custom date range: {date_start} to {date_end}")
            except ValueError as e:
                logger.error(f"Error parsing custom dates: {e}")
                # Используем период по умолчанию при ошибке парсинга дат
                date_start = date_end - timedelta(days=7)
        elif period == 'day':
            date_start = date_end - timedelta(days=1)
        elif period == 'week':
            date_start = date_end - timedelta(days=7)
        elif period == 'month':
            date_start = date_end - timedelta(days=30)
        else:  # all
            date_start = None

        logger.info(f"Date range: start_date={date_start}, end_date={date_end}")

        # Переименовываем переменные для совместимости с остальным кодом
        start_date = date_start
        end_date = date_end

        # Формируем ключ кеша с учетом всех параметров
        user_id_part = f"user_{user_id}" if user_id else "all_users"
        date_part = ""
        if period == 'custom' and start_date and end_date:
            # Форматируем даты для использования в ключе кеша
            start_str = start_date.isoformat().replace(':', '-') if isinstance(start_date, datetime) else str(start_date).replace(':', '-')
            end_str = end_date.isoformat().replace(':', '-') if isinstance(end_date, datetime) else str(end_date).replace(':', '-')
            date_part = f"{start_str}_{end_str}"

        cache_key = f"admin_generations:{period}:{type or 'all'}:{user_id_part}:{date_part}:{skip}:{limit}:{sort_by}:{sort_order}:{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')}"
        cached_data = await cache.get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for key: {cache_key}")
            return cached_data

        # Получаем статистику генераций
        logger.info("Fetching generation statistics...")
        async with StatisticsCollector(session) as collector:
            # Получаем общую статистику
            stats_period = StatisticsPeriod.DAY if period == 'day' else StatisticsPeriod.WEEK if period == 'week' else StatisticsPeriod.MONTH
            generation_stats = await collector.get_generation_statistics(stats_period, start_date, end_date)
            logger.info(f"Generation stats: {generation_stats}")

        # Получаем детальный список генераций
        from sqlalchemy import select, func
        from ...models import Generation
        from ...core.constants import ContentType

        # Проверяем наличие таблицы generations с помощью прямого SQL-запроса
        try:
            # Используем прямой SQL-запрос вместо инспектора
            from sqlalchemy import text

            # Запрос для проверки существования таблицы
            check_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'generations'
                );
            """)

            result = await session.execute(check_query)
            exists = result.scalar()

            logger.info(f"Table 'generations' exists: {exists}")
            if not exists:
                logger.error("Table 'generations' does not exist in the database!")
        except Exception as table_error:
            logger.error(f"Error checking tables: {str(table_error)}")

        # Формируем запрос с фильтрами
        query = select(Generation)
        logger.info(f"Base query: {query}")

        # Применяем фильтр по периоду, если указан
        if start_date:
            query = query.where(Generation.created_at >= start_date)
        query = query.where(Generation.created_at <= end_date)
        logger.info(f"Query with date filters: {query}")

        # Применяем фильтр по типу, если указан
        if type:
            try:
                content_type = ContentType(type)
                query = query.where(Generation.type == content_type)
                logger.info(f"Applied type filter: {type}")
            except ValueError:
                # Если тип не соответствует enum, игнорируем фильтр
                logger.warning(f"Invalid content type filter: {type}")

        # Применяем фильтр по пользователю, если указан
        if user_id:
            query = query.where(Generation.user_id == user_id)
            logger.info(f"Applied user_id filter: {user_id}")

        # Получаем общее количество записей для пагинации
        try:
            count_query = select(func.count()).select_from(query.subquery())
            logger.info(f"Count query: {count_query}")
            total_count = await session.scalar(count_query)
            logger.info(f"Total count: {total_count}")
        except Exception as count_error:
            logger.error(f"Error getting total count: {str(count_error)}")
            total_count = 0

        # Применяем сортировку
        sort_column = getattr(Generation, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Применяем пагинацию
        query = query.offset(skip).limit(limit)
        logger.info(f"Final query with pagination: {query}")

        # Выполняем запрос
        try:
            result = await session.execute(query)
            generations = result.scalars().all()
            logger.info(f"Query executed successfully, got {len(generations)} generations")
        except Exception as query_error:
            logger.error(f"Error executing query: {str(query_error)}")
            generations = []

        # Преобразуем результаты в словари
        generations_list = []
        for gen in generations:
            try:
                gen_dict = {
                    "id": gen.id,
                    "user_id": gen.user_id,
                    "type": gen.type.value,  # Преобразуем enum в строку
                    "content": gen.content[:100] + "..." if len(gen.content) > 100 else gen.content,  # Сокращаем для логов
                    "prompt": gen.prompt[:100] + "..." if len(gen.prompt) > 100 else gen.prompt,  # Сокращаем для логов
                    "created_at": gen.created_at.isoformat()
                }
                generations_list.append(gen_dict)
                logger.info(f"Processed generation: id={gen.id}, type={gen.type.value}, created_at={gen.created_at}")
            except Exception as gen_error:
                logger.error(f"Error processing generation: {str(gen_error)}")

        # Формируем итоговый ответ
        response = {
            "generations": generations_list,
            "total": total_count,
            "total_generations": generation_stats.get("total_generations", 0),
            "by_type": generation_stats.get("generations_by_type", {}),
            "popular_prompts": generation_stats.get("popular_prompts", []),
            "period": period,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat()
        }
        logger.info(f"Response prepared with {len(generations_list)} generations")

        # Кешируем результат
        await cache.cache_data(cache_key, response, ttl=STATISTICS_CACHE_TTL['generations'])
        logger.info(f"Response cached with key: {cache_key}")

        return response

    except Exception as e:
        logger.error(f"Error getting detailed generations: {str(e)}")
        # Добавляем трассировку стека для более подробной информации об ошибке
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting detailed generations: {str(e)}")


@router.get("/admin/generations/export")
async def export_generations_to_excel(
    period: str = Query("week", regex="^(day|week|month|all|custom)$"),
    type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(id|user_id|type|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin_user)
):
    """Экспорт генераций в Excel файл"""
    logger.info(f"=== ADMIN GENERATIONS EXPORT API CALLED ===")
    logger.info(f"Parameters: period={period}, type={type}, user_id={user_id}, start_date={start_date}, end_date={end_date}, sort_by={sort_by}, sort_order={sort_order}")

    try:
        # Определяем временной период
        date_end = datetime.now(timezone.utc)

        if period == 'custom' and start_date and end_date:
            # Если указан кастомный период, используем переданные даты
            try:
                date_start = datetime.fromisoformat(start_date)
                if not date_start.tzinfo:
                    date_start = date_start.replace(tzinfo=timezone.utc)

                date_end = datetime.fromisoformat(end_date)
                if not date_end.tzinfo:
                    date_end = date_end.replace(tzinfo=timezone.utc)

                logger.info(f"Using custom date range: {date_start} to {date_end}")
            except ValueError as e:
                logger.error(f"Error parsing custom dates: {e}")
                # Используем период по умолчанию при ошибке парсинга дат
                date_start = date_end - timedelta(days=7)
        elif period == 'day':
            date_start = date_end - timedelta(days=1)
        elif period == 'week':
            date_start = date_end - timedelta(days=7)
        elif period == 'month':
            date_start = date_end - timedelta(days=30)
        else:  # all
            date_start = None

        logger.info(f"Date range: start_date={date_start}, end_date={date_end}")

        # Переименовываем переменные для совместимости с остальным кодом
        start_date = date_start
        end_date = date_end

        # Получаем детальный список генераций
        from sqlalchemy import select, func
        from ...models import Generation, User
        from ...core.constants import ContentType

        # Формируем запрос с фильтрами
        query = select(Generation)

        # Применяем фильтр по периоду, если указан
        if start_date:
            query = query.where(Generation.created_at >= start_date)
        query = query.where(Generation.created_at <= end_date)

        # Применяем фильтр по типу, если указан
        if type:
            try:
                content_type = ContentType(type)
                query = query.where(Generation.type == content_type)
                logger.info(f"Applied type filter: {type}")
            except ValueError:
                # Если тип не соответствует enum, игнорируем фильтр
                logger.warning(f"Invalid content type filter: {type}")

        # Применяем фильтр по пользователю, если указан
        if user_id:
            query = query.where(Generation.user_id == user_id)
            logger.info(f"Applied user_id filter: {user_id}")

        # Применяем сортировку
        sort_column = getattr(Generation, sort_by)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Выполняем запрос (без пагинации для экспорта)
        result = await session.execute(query)
        generations = result.scalars().all()
        logger.info(f"Query executed successfully, got {len(generations)} generations for export")

        # Получаем информацию о пользователях для экспорта
        user_ids = list(set(gen.user_id for gen in generations))
        users_query = select(User).where(User.id.in_(user_ids))
        users_result = await session.execute(users_query)
        users = {user.id: user for user in users_result.scalars().all()}

        # Преобразуем результаты в словари для экспорта
        generations_list = []
        for gen in generations:
            try:
                # Получаем информацию о пользователе
                user = users.get(gen.user_id)
                user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() if user else ""
                user_name = user_name or (user.username if user else "")
                user_name = user_name or f"ID: {gen.user_id}"

                gen_dict = {
                    "id": gen.id,
                    "user_id": gen.user_id,
                    "user_name": user_name,
                    "type": gen.type.value,  # Преобразуем enum в строку
                    "type_formatted": gen.type.value.replace("_", " ").title(),
                    "content": gen.content,
                    "prompt": gen.prompt,
                    "created_at": gen.created_at.isoformat()
                }
                generations_list.append(gen_dict)
            except Exception as gen_error:
                logger.error(f"Error processing generation for export: {str(gen_error)}")

        # Определяем маппинг полей для экспорта
        column_mapping = {
            "id": "ID",
            "user_id": "ID пользователя",
            "user_name": "Имя пользователя",
            "type": "Тип генерации",
            "type_formatted": "Тип (форматированный)",
            "content": "Содержимое",
            "prompt": "Запрос",
            "created_at": "Дата создания"
        }

        # Формируем имя файла с датой и периодом
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"generations_export_{period}_{now}"

        # Экспортируем данные в Excel
        return export_to_excel(
            data=generations_list,
            filename=filename,
            sheet_name="Генерации",
            column_mapping=column_mapping
        )

    except Exception as e:
        logger.error(f"Error exporting generations to Excel: {str(e)}")
        # Добавляем трассировку стека для более подробной информации об ошибке
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error exporting generations to Excel: {str(e)}")


@router.get("/statistics/generations")
async def get_generations_statistics(
    period: str = Query("week", regex="^(day|week|month|all)$"),
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Получить статистику генераций для графиков"""
    logger.info(f"=== GENERATIONS STATISTICS API CALLED ===")
    logger.info(f"Parameters: period={period}")

    try:
        # Формируем ключ кеша
        cache_key = f"generations_statistics:{period}:{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')}"

        # Пытаемся получить данные из кеша
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached generations statistics for period {period}")
            return cached_data

        # Определяем временной период
        end_date = datetime.now(timezone.utc)
        if period == 'day':
            start_date = end_date - timedelta(days=1)
            # Для дневной статистики берем почасовые данные
            time_format = '%Y-%m-%d %H:00'
            interval = 'hour'
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
            # Для недельной статистики берем данные по дням
            time_format = '%Y-%m-%d'
            interval = 'day'
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
            # Для месячной статистики берем данные по дням
            time_format = '%Y-%m-%d'
            interval = 'day'
        else:  # all
            start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
            # Для всего времени берем данные по месяцам
            time_format = '%Y-%m'
            interval = 'month'

        logger.info(f"Date range: start_date={start_date}, end_date={end_date}")

        # Получаем статистику по типам генераций
        from sqlalchemy import select, func, extract
        from ...models import Generation
        from ...core.constants import ContentType

        # Статистика по типам
        type_query = select(
            Generation.type,
            func.count(Generation.id).label('count')
        ).where(
            Generation.created_at >= start_date,
            Generation.created_at <= end_date
        ).group_by(
            Generation.type
        )

        type_result = await session.execute(type_query)
        generations_by_type = {
            row[0].value: row[1] for row in type_result.all()
        }

        # Статистика по времени
        if interval == 'hour':
            # Для часовой статистики
            time_query = select(
                func.date_trunc('hour', Generation.created_at).label('date'),
                func.count(Generation.id).label('count')
            ).where(
                Generation.created_at >= start_date,
                Generation.created_at <= end_date
            ).group_by(
                func.date_trunc('hour', Generation.created_at)
            ).order_by(
                func.date_trunc('hour', Generation.created_at)
            )
        elif interval == 'day':
            # Для дневной статистики
            time_query = select(
                func.date_trunc('day', Generation.created_at).label('date'),
                func.count(Generation.id).label('count')
            ).where(
                Generation.created_at >= start_date,
                Generation.created_at <= end_date
            ).group_by(
                func.date_trunc('day', Generation.created_at)
            ).order_by(
                func.date_trunc('day', Generation.created_at)
            )
        else:  # month
            # Для месячной статистики
            time_query = select(
                func.date_trunc('month', Generation.created_at).label('date'),
                func.count(Generation.id).label('count')
            ).where(
                Generation.created_at >= start_date,
                Generation.created_at <= end_date
            ).group_by(
                func.date_trunc('month', Generation.created_at)
            ).order_by(
                func.date_trunc('month', Generation.created_at)
            )

        time_result = await session.execute(time_query)
        time_series = [
            {
                'date': row[0].isoformat(),
                'count': row[1]
            } for row in time_result.all()
        ]

        # Общее количество генераций
        count_query = select(func.count(Generation.id)).where(
            Generation.created_at >= start_date,
            Generation.created_at <= end_date
        )
        total_count = await session.scalar(count_query)

        # Формируем ответ
        response = {
            'total_generations': total_count,
            'generations_by_type': generations_by_type,
            'time_series': time_series,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

        # Добавляем дополнительную информацию для отладки
        logger.info(f"Returning statistics response: {response}")

        # Кешируем результат
        await cache.set(cache_key, response, ttl=3600)  # Кешируем на 1 час

        return response

    except Exception as e:
        logger.error(f"Error getting generations statistics: {str(e)}")
        # Добавляем трассировку стека для более подробной информации об ошибке
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting generations statistics: {str(e)}")
