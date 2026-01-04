"""
API эндпоинты для расширенной аналитики админ-панели
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import asyncio

from ...core.database import get_db
from ...core.security import get_current_admin_user
from ...models.user import User
from ...models.tracking import GenerationMetrics
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["advanced_analytics"])

# Константы для кеширования
CACHE_TTL = {
    'financial': 1800,  # 30 минут
    'time_activity': 600,  # 10 минут
    'content_popularity': 900  # 15 минут
}


def _calculate_start_date(end_date: datetime, period: str) -> datetime:
    """Вычисляет начальную дату на основе периода"""
    if period == "week":
        return end_date - timedelta(days=7)
    elif period == "month":
        return end_date - timedelta(days=30)
    elif period == "quarter":
        return end_date - timedelta(days=90)
    elif period == "year":
        return end_date - timedelta(days=365)
    else:
        return end_date - timedelta(days=30)


# Финансовая аналитика перенесена в analytics.py


@router.get("/admin/analytics/time-activity")
async def get_time_activity_analytics(
    period: str = Query("month", regex="^(week|month|quarter)$"),
    activity_type: str = Query("all", regex="^(all|generations|logins|purchases)$"),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """Получить аналитику активности по времени"""
    try:

        end_date = datetime.now(timezone.utc)
        start_date = _calculate_start_date(end_date, period)

        # Запрос активности по часам
        hourly_query = text("""
            SELECT
                EXTRACT(hour FROM created_at) as hour,
                COUNT(*) as activity_count
            FROM generation_metrics
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY EXTRACT(hour FROM created_at)
            ORDER BY hour
        """)

        # Запрос активности по дням недели
        weekly_query = text("""
            SELECT
                EXTRACT(dow FROM created_at) as day_of_week,
                COUNT(*) as activity_count
            FROM generation_metrics
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY EXTRACT(dow FROM created_at)
            ORDER BY day_of_week
        """)

        # Выполняем запросы
        hourly_result = await session.execute(hourly_query, {"start_date": start_date, "end_date": end_date})
        weekly_result = await session.execute(weekly_query, {"start_date": start_date, "end_date": end_date})

        hourly_data = hourly_result.fetchall()
        weekly_data = weekly_result.fetchall()

        # Обрабатываем данные по часам
        hourly_activity = []
        for hour in range(24):
            activity = next((row.activity_count for row in hourly_data if row.hour == hour), 0)
            hourly_activity.append({"hour": hour, "activity": activity})

        # Обрабатываем данные по дням недели
        day_names = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        weekly_activity = []
        for day in range(7):
            activity = next((row.activity_count for row in weekly_data if row.day_of_week == day), 0)
            weekly_activity.append({"day": day_names[day][:2], "activity": activity})

        # Находим пиковые значения
        peak_hour = max(hourly_activity, key=lambda x: x['activity'])['hour'] if hourly_activity else 14
        peak_day = max(weekly_activity, key=lambda x: x['activity'])['day'] if weekly_activity else 'Ср'

        # Генерируем тепловую карту
        heatmap_data = []
        for day_idx, day_name in enumerate(['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']):
            hours = []
            for hour in range(24):
                # Генерируем случайные данные на основе реальных паттернов
                base_activity = hourly_activity[hour]['activity'] if hour < len(hourly_activity) else 0
                variation = base_activity * (0.5 + (day_idx % 3) * 0.3)
                hours.append(int(variation))
            heatmap_data.append({"name": day_name, "hours": hours})

        # Реальная статистика по дням недели
        daily_query = text("""
            SELECT
                EXTRACT(dow FROM created_at) as day_of_week,
                COUNT(*) as total_activity,
                COUNT(DISTINCT user_id) as unique_users,
                MODE() WITHIN GROUP (ORDER BY EXTRACT(hour FROM created_at)) as peak_hour
            FROM generation_metrics
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY EXTRACT(dow FROM created_at)
            ORDER BY day_of_week
        """)

        daily_result = await session.execute(daily_query, {"start_date": start_date, "end_date": end_date})
        daily_data = daily_result.fetchall()

        # Названия дней недели (0 = воскресенье в PostgreSQL)
        day_names = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

        # Создаем статистику по дням
        daily_stats = []
        daily_activity_map = {int(row.day_of_week): row for row in daily_data}

        for day_index, day_name in enumerate(day_names):
            row = daily_activity_map.get(day_index)
            if row:
                daily_stats.append({
                    "name": day_name,
                    "totalActivity": row.total_activity,
                    "uniqueUsers": row.unique_users,
                    "peakHour": f"{int(row.peak_hour or 14)}:00",
                    "avgSession": 25  # TODO: Вычислить реальную среднюю сессию
                })
            else:
                daily_stats.append({
                    "name": day_name,
                    "totalActivity": 0,
                    "uniqueUsers": 0,
                    "peakHour": "14:00",
                    "avgSession": 0
                })

        # Вычисляем реальные данные по временным зонам
        total_activity = sum(item['activity'] for item in hourly_activity)

        # Подсчитываем активность по временным зонам
        morning_activity = sum(item['activity'] for item in hourly_activity if 6 <= item['hour'] < 12)
        afternoon_activity = sum(item['activity'] for item in hourly_activity if 12 <= item['hour'] < 18)
        evening_activity = sum(item['activity'] for item in hourly_activity if 18 <= item['hour'] < 24)
        night_activity = sum(item['activity'] for item in hourly_activity if 0 <= item['hour'] < 6)

        # Вычисляем проценты
        time_zones = {
            "morning": round((morning_activity / total_activity * 100) if total_activity > 0 else 0, 1),
            "afternoon": round((afternoon_activity / total_activity * 100) if total_activity > 0 else 0, 1),
            "evening": round((evening_activity / total_activity * 100) if total_activity > 0 else 0, 1),
            "night": round((night_activity / total_activity * 100) if total_activity > 0 else 0, 1)
        }

        # Получаем количество активных пользователей
        active_users_query = text("""
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM generation_metrics
            WHERE created_at >= :start_date AND created_at <= :end_date
        """)

        active_users_result = await session.execute(active_users_query, {"start_date": start_date, "end_date": end_date})
        active_users = active_users_result.scalar() or 0

        analytics_data = {
            "peakHour": peak_hour,
            "peakDay": peak_day,
            "avgSessionDuration": 25,  # TODO: Вычислить реальную среднюю продолжительность сессии
            "activeUsers": active_users,
            "timeZones": time_zones,
            "heatmapData": heatmap_data,
            "dailyStats": daily_stats,
            "hourlyActivity": hourly_activity,
            "weeklyActivity": weekly_activity,
            "period": period,
            "activityType": activity_type,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        return analytics_data

    except Exception as e:
        logger.error(f"Error getting time activity analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting time activity analytics: {str(e)}")


@router.get("/admin/analytics/content-popularity")
async def get_content_popularity_analytics(
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    tariff_filter: str = Query("all", regex="^(all|basic|standard|premium|vip)$"),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user)
):
    """Получить аналитику популярности контента"""
    try:

        end_date = datetime.now(timezone.utc)
        start_date = _calculate_start_date(end_date, period)

        # Запрос популярности контента
        content_query = text("""
            SELECT
                gm.content_type,
                COUNT(*) as generation_count,
                COUNT(DISTINCT gm.user_id) as unique_users,
                AVG(CASE WHEN gm.success THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(gm.generation_time) as avg_time
            FROM generation_metrics gm
            WHERE gm.created_at >= :start_date AND gm.created_at <= :end_date
            GROUP BY gm.content_type
            ORDER BY generation_count DESC
        """)

        result = await session.execute(content_query, {"start_date": start_date, "end_date": end_date})
        content_data = result.fetchall()

        total_generations = sum(row.generation_count for row in content_data)

        # Формируем топ контента
        top_content = []
        detailed_stats = []

        for row in content_data:
            percentage = (row.generation_count / total_generations * 100) if total_generations > 0 else 0

            top_content.append({
                "type": row.content_type,
                "count": row.generation_count,
                "percentage": percentage
            })

            detailed_stats.append({
                "type": row.content_type,
                "count": row.generation_count,
                "uniqueUsers": row.unique_users,
                "successRate": round(row.success_rate or 0, 1),
                "avgTime": round(row.avg_time or 0, 1),
                "growth": 0.0  # TODO: Вычислить реальный рост по типам контента
            })

        # Находим самый популярный тип
        most_popular = top_content[0] if top_content else {"name": "Нет данных", "count": 0}
        if most_popular and most_popular.get("type"):
            type_map = {
                'lesson_plan': 'План урока',
                'exercise': 'Упражнение',
                'game': 'Игра',
                'image': 'Изображение',
                'text_analysis': 'Анализ текста',
                'concept_explanation': 'Объяснение концепции',
                'course': 'Курс',
                'ai_assistant': 'AI-ассистент'
            }
            most_popular["name"] = type_map.get(most_popular["type"], most_popular["type"])

        # Получаем реальные тренды по месяцам
        trend_query = text("""
            SELECT
                DATE_TRUNC('month', created_at) as month,
                content_type,
                COUNT(*) as count
            FROM generation_metrics
            WHERE created_at >= :trend_start_date AND created_at <= :end_date
            GROUP BY DATE_TRUNC('month', created_at), content_type
            ORDER BY month DESC
        """)

        trend_start_date = end_date - timedelta(days=150)  # 5 месяцев назад
        trend_result = await session.execute(trend_query, {
            "trend_start_date": trend_start_date,
            "end_date": end_date
        })
        trend_raw_data = trend_result.fetchall()

        # Группируем данные по месяцам
        trend_by_month = {}
        for row in trend_raw_data:
            month_key = row.month.strftime('%Y-%m')
            if month_key not in trend_by_month:
                trend_by_month[month_key] = {
                    "date": month_key,
                    "lesson_plan": 0,
                    "exercise": 0,
                    "game": 0,
                    "image": 0,
                    "text_analysis": 0,
                    "concept_explanation": 0,
                    "course": 0,
                    "ai_assistant": 0
                }
            trend_by_month[month_key][row.content_type] = row.count

        # Сортируем по дате и берем последние 5 месяцев
        trend_data = list(trend_by_month.values())
        trend_data.sort(key=lambda x: x["date"])
        trend_data = trend_data[-5:]  # Последние 5 месяцев

        # Получаем реальные сезонные данные за последний год
        seasonal_query = text("""
            SELECT
                EXTRACT(month FROM created_at) as month,
                COUNT(*) as activity
            FROM generation_metrics
            WHERE created_at >= :year_start AND created_at <= :end_date
            GROUP BY EXTRACT(month FROM created_at)
            ORDER BY month
        """)

        year_start = end_date - timedelta(days=365)
        seasonal_result = await session.execute(seasonal_query, {
            "year_start": year_start,
            "end_date": end_date
        })
        seasonal_raw_data = seasonal_result.fetchall()

        # Создаем данные для всех 12 месяцев
        seasonal_data = []
        seasonal_map = {int(row.month): row.activity for row in seasonal_raw_data}

        for month in range(1, 13):
            seasonal_data.append({
                "month": month,
                "activity": seasonal_map.get(month, 0)
            })

        # Вычисляем рост генераций (сравнение с предыдущим периодом)
        prev_start_date = start_date - (end_date - start_date)
        prev_end_date = start_date

        prev_generations_query = text("""
            SELECT COUNT(*) as count
            FROM generation_metrics
            WHERE created_at >= :prev_start_date AND created_at < :prev_end_date
        """)

        prev_result = await session.execute(prev_generations_query, {
            "prev_start_date": prev_start_date,
            "prev_end_date": prev_end_date
        })
        prev_generations = prev_result.scalar() or 0

        # Вычисляем процент роста
        if prev_generations > 0:
            growth_rate = ((total_generations - prev_generations) / prev_generations) * 100
        else:
            growth_rate = 100.0 if total_generations > 0 else 0.0

        # Вычисляем реальную статистику успешности и времени
        success_stats_query = text("""
            SELECT
                AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(generation_time) as avg_time
            FROM generation_metrics
            WHERE created_at >= :start_date AND created_at <= :end_date
        """)

        success_result = await session.execute(success_stats_query, {
            "start_date": start_date,
            "end_date": end_date
        })
        success_data = success_result.fetchone()

        success_rate = round(success_data.success_rate or 0, 1)
        avg_generation_time = round(success_data.avg_time or 0, 1)

        analytics_data = {
            "totalGenerations": total_generations,
            "generationsGrowth": round(growth_rate, 1),
            "mostPopular": most_popular,
            "successRate": success_rate,
            "avgGenerationTime": avg_generation_time,
            "topContent": top_content[:6],  # Топ 6
            "detailedStats": detailed_stats,
            "qualityStats": {"high": 85, "medium": 12, "low": 3},  # TODO: Вычислить реальную статистику качества
            "trendData": trend_data,
            "seasonalData": seasonal_data,
            "period": period,
            "tariffFilter": tariff_filter,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        return analytics_data

    except Exception as e:
        logger.error(f"Error getting content popularity analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting content popularity analytics: {str(e)}")
