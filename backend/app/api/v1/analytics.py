from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.content import Generation
from app.models.payment import Payment
from app.models.point_transaction import PointTransaction
from app.core.constants import ContentType, TariffType
from sqlalchemy import text
from datetime import timezone

router = APIRouter()

@router.get("/financial")
async def get_financial_analytics(
    period: str = Query("month", description="Период: week, month, quarter, year, all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить финансовую аналитику"""

    # Проверяем права администратора
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Определяем период
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # Получаем реальные данные о платежах
    try:
        # Получаем платежи за тарифы в указанном периоде
        tariff_payments_result = await db.execute(
            select(Payment).where(
                Payment.created_at >= start_date,
                Payment.status == "completed",
                Payment.payment_type == "tariff"
            )
        )
        tariff_payments = tariff_payments_result.scalars().all()

        # Получаем платежи за баллы в указанном периоде
        points_payments_result = await db.execute(
            select(Payment).where(
                Payment.created_at >= start_date,
                Payment.status == "completed",
                Payment.payment_type == "points"
            )
        )
        points_payments = points_payments_result.scalars().all()

        # Подсчитываем общий доход
        total_revenue = sum(p.amount for p in tariff_payments + points_payments)

        # Подсчитываем доходы по тарифам
        tariff_revenue = {}
        tariff_names = {
            "tariff_2": "Стандарт",
            "tariff_4": "Премиум",
            "tariff_6": "VIP"
        }

        for payment in tariff_payments:
            tariff_type = payment.meta_data.get("tariff_type") if payment.meta_data else None
            if tariff_type:
                if tariff_type not in tariff_revenue:
                    tariff_revenue[tariff_type] = {"count": 0, "revenue": 0}
                tariff_revenue[tariff_type]["count"] += 1
                tariff_revenue[tariff_type]["revenue"] += payment.amount

        # Подсчитываем доходы от баллов
        points_revenue = sum(p.amount for p in points_payments)

        # Получаем количество активных пользователей
        total_users_result = await db.execute(
            select(func.count(User.id)).where(User.role == "user")
        )
        total_users = total_users_result.scalar() or 0
        paying_users = len(set(p.user_id for p in tariff_payments + points_payments))

    except Exception as e:
        # Если таблица payments не существует, используем данные из активных тарифов
        print(f"Payment table not found, using active tariffs: {e}")

        # Получаем пользователей с активными тарифами
        result = await db.execute(
            select(User).where(
                User.tariff.isnot(None),
                User.tariff_valid_until >= now
            )
        )
        active_tariff_users = result.scalars().all()

        # Подсчитываем доходы по тарифам (симуляция на основе активных пользователей)
        tariff_revenue = {}
        tariff_prices = {
            "tariff_2": 299,  # Стандарт
            "tariff_4": 599,  # Премиум
            "tariff_6": 999   # VIP
        }

        total_revenue = 0
        for user in active_tariff_users:
            tariff_type = user.tariff.value if user.tariff else None
            if tariff_type and tariff_type in tariff_prices:
                if tariff_type not in tariff_revenue:
                    tariff_revenue[tariff_type] = {"count": 0, "revenue": 0}
                tariff_revenue[tariff_type]["count"] += 1
                tariff_revenue[tariff_type]["revenue"] += tariff_prices[tariff_type]
                total_revenue += tariff_prices[tariff_type]

        # Получаем общее количество пользователей
        total_users_result = await db.execute(
            select(func.count(User.id)).where(User.role == "user")
        )
        total_users = total_users_result.scalar() or 0
        paying_users = len(active_tariff_users)
        points_revenue = 0

    # Подсчитываем метрики
    arpu = total_revenue / total_users if total_users > 0 else 0
    conversion_rate = (paying_users / total_users * 100) if total_users > 0 else 0

    # Формируем топ тарифы
    top_tariffs = []
    tariff_names = {
        "tariff_2": "Стандарт",
        "tariff_4": "Премиум",
        "tariff_6": "VIP"
    }

    for tariff_type, data in tariff_revenue.items():
        top_tariffs.append({
            "name": tariff_names.get(tariff_type, tariff_type),
            "subscribers": data["count"],
            "revenue": data["revenue"],
            "share": (data["revenue"] / total_revenue * 100) if total_revenue > 0 else 0,
            "averageCheck": data["revenue"] / data["count"] if data["count"] > 0 else 0
        })

    # Добавляем баллы как отдельную категорию, если есть доходы от баллов
    if points_revenue > 0:
        top_tariffs.append({
            "name": "Баллы",
            "subscribers": len([p for p in points_payments]) if 'points_payments' in locals() else 0,
            "revenue": points_revenue,
            "share": (points_revenue / total_revenue * 100) if total_revenue > 0 else 0,
            "averageCheck": points_revenue / len(points_payments) if 'points_payments' in locals() and points_payments else 0
        })

    # Сортируем по доходу
    top_tariffs.sort(key=lambda x: x["revenue"], reverse=True)

    # Формируем реальную историю доходов по дням
    revenue_history = []
    days_count = (now - start_date).days

    try:
        # Получаем реальные доходы по дням
        for i in range(min(days_count, 30)):  # Максимум 30 точек для графика
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)

            # Получаем платежи за этот день
            day_payments_result = await db.execute(
                select(Payment).where(
                    Payment.created_at >= day_start,
                    Payment.created_at < day_end,
                    Payment.status == "completed"
                )
            )
            day_payments = day_payments_result.scalars().all()
            day_revenue = sum(p.amount for p in day_payments)

            revenue_history.append({
                "date": day_start.strftime("%d.%m"),
                "revenue": day_revenue
            })
    except:
        # Если не удается получить реальные данные, используем равномерное распределение
        avg_daily_revenue = total_revenue / max(days_count, 1) if total_revenue > 0 else 0
        for i in range(min(days_count, 30)):
            day_start = start_date + timedelta(days=i)
            revenue_history.append({
                "date": day_start.strftime("%d.%m"),
                "revenue": avg_daily_revenue
            })

    # Простые прогнозы (на основе среднего дохода)
    avg_daily_revenue = total_revenue / max(days_count, 1) if total_revenue > 0 else 0

    # Рассчитываем рост доходов (сравнение с предыдущим периодом)
    revenue_growth = 0
    try:
        # Получаем доходы за предыдущий период для сравнения
        prev_start_date = start_date - (now - start_date)
        prev_payments_result = await db.execute(
            select(Payment).where(
                Payment.created_at >= prev_start_date,
                Payment.created_at < start_date,
                Payment.status == "completed"
            )
        )
        prev_payments = prev_payments_result.scalars().all()
        prev_revenue = sum(p.amount for p in prev_payments)

        if prev_revenue > 0:
            revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
    except:
        revenue_growth = 0  # Если не удается рассчитать, оставляем 0

    return {
        "totalRevenue": total_revenue,
        "revenueGrowth": round(revenue_growth, 1),
        "arpu": round(arpu, 2),
        "conversionRate": round(conversion_rate, 1),
        "ltv": round(arpu * 12, 2),  # Простая оценка LTV
        "churnRate": 5.0,  # Заглушка - требует более сложного расчета
        "topTariffs": top_tariffs,
        "revenueHistory": revenue_history,
        "forecast": {
            "nextMonth": round(avg_daily_revenue * 30, 2),
            "nextQuarter": round(avg_daily_revenue * 90, 2)
        }
    }

@router.get("/feature-usage")
async def get_feature_usage_analytics(
    period: str = Query("month", description="Период: week, month, quarter, year, all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить аналитику использования функций"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Определяем период
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # Получаем статистику генераций по типам
    result = await db.execute(
        select(
            Generation.type,
            func.count(Generation.id).label('count')
        ).where(
            Generation.created_at >= start_date
        ).group_by(Generation.type)
    )
    generation_stats = result.all()

    # Получаем общее количество генераций
    total_generations = sum(stat.count for stat in generation_stats)

    # Формируем данные для графика
    feature_data = []
    content_type_names = {
        "lesson_plan": "Планы уроков",
        "exercise": "Упражнения",
        "game": "Игры",
        "image": "Изображения",
        "text_analysis": "Анализ текста",
        "concept_explanation": "Объяснение концепций",
        "course": "Курсы",
        "free_query": "AI-ассистент"
    }

    for stat in generation_stats:
        feature_data.append({
            "name": content_type_names.get(stat.type, stat.type),
            "usage": stat.count,
            "percentage": (stat.count / total_generations * 100) if total_generations > 0 else 0
        })

    # Сортируем по использованию
    feature_data.sort(key=lambda x: x["usage"], reverse=True)

    return {
        "totalGenerations": total_generations,
        "features": feature_data,
        "period": period
    }

@router.get("/time-activity")
async def get_time_activity_analytics(
    period: str = Query("month", description="Период: week, month, quarter, year, all"),
    activity_type: str = Query("all", description="Тип активности: all, generations, logins, purchases"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить аналитику активности по времени"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Определяем период
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # Инициализируем данные
    hours_data = [0] * 24
    days_data = [0] * 7
    day_names = ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

    # В зависимости от типа активности получаем разные данные
    if activity_type == "purchases":
        # Получаем покупки тарифов и баллов
        try:
            # Покупки через Payment
            payment_hourly = await db.execute(
                select(
                    func.extract('hour', Payment.created_at).label('hour'),
                    func.count(Payment.id).label('count')
                ).where(
                    Payment.created_at >= start_date,
                    Payment.status == "completed"
                ).group_by(func.extract('hour', Payment.created_at))
            )
            
            payment_daily = await db.execute(
                select(
                    func.extract('dow', Payment.created_at).label('day'),
                    func.count(Payment.id).label('count')
                ).where(
                    Payment.created_at >= start_date,
                    Payment.status == "completed"
                ).group_by(func.extract('dow', Payment.created_at))
            )
            
            # Обрабатываем данные платежей
            for activity in payment_hourly.all():
                hours_data[int(activity.hour)] += activity.count
            
            for activity in payment_daily.all():
                days_data[int(activity.day)] += activity.count
                
        except Exception as e:
            print(f"Payment table not available: {e}")
        
        try:
            # Покупки баллов через PointTransaction
            points_hourly = await db.execute(
                select(
                    func.extract('hour', PointTransaction.created_at).label('hour'),
                    func.count(PointTransaction.id).label('count')
                ).where(
                    PointTransaction.created_at >= start_date,
                    PointTransaction.transaction_type.in_(["purchase", "admin_add"])
                ).group_by(func.extract('hour', PointTransaction.created_at))
            )
            
            points_daily = await db.execute(
                select(
                    func.extract('dow', PointTransaction.created_at).label('day'),
                    func.count(PointTransaction.id).label('count')
                ).where(
                    PointTransaction.created_at >= start_date,
                    PointTransaction.transaction_type.in_(["purchase", "admin_add"])
                ).group_by(func.extract('dow', PointTransaction.created_at))
            )
            
            # Обрабатываем данные транзакций баллов
            for activity in points_hourly.all():
                hours_data[int(activity.hour)] += activity.count
            
            for activity in points_daily.all():
                days_data[int(activity.day)] += activity.count
                
        except Exception as e:
            print(f"PointTransaction table not available: {e}")
            
    elif activity_type == "logins":
        # Получаем входы в систему (по last_active пользователей)
        try:
            login_hourly = await db.execute(
                select(
                    func.extract('hour', User.last_active).label('hour'),
                    func.count(User.id).label('count')
                ).where(
                    User.last_active >= start_date,
                    User.last_active.isnot(None)
                ).group_by(func.extract('hour', User.last_active))
            )
            
            login_daily = await db.execute(
                select(
                    func.extract('dow', User.last_active).label('day'),
                    func.count(User.id).label('count')
                ).where(
                    User.last_active >= start_date,
                    User.last_active.isnot(None)
                ).group_by(func.extract('dow', User.last_active))
            )
            
            # Обрабатываем данные входов
            for activity in login_hourly.all():
                hours_data[int(activity.hour)] = activity.count
            
            for activity in login_daily.all():
                days_data[int(activity.day)] = activity.count
                
        except Exception as e:
            print(f"Login analytics error: {e}")
            
    else:  # "generations" или "all"
        # Получаем активность генераций (оригинальная логика)
        hourly_result = await db.execute(
            select(
                func.extract('hour', Generation.created_at).label('hour'),
                func.count(Generation.id).label('count')
            ).where(
                Generation.created_at >= start_date
            ).group_by(func.extract('hour', Generation.created_at))
        )
        
        daily_result = await db.execute(
            select(
                func.extract('dow', Generation.created_at).label('day'),
                func.count(Generation.id).label('count')
            ).where(
                Generation.created_at >= start_date
            ).group_by(func.extract('dow', Generation.created_at))
        )
        
        # Обрабатываем данные генераций
        for activity in hourly_result.all():
            hours_data[int(activity.hour)] = activity.count
        
        for activity in daily_result.all():
            days_data[int(activity.day)] = activity.count

    # Рассчитываем среднюю продолжительность сессии
    try:
        # Получаем данные о последней активности пользователей
        session_query = await db.execute(
            select(
                User.last_active,
                User.created_at
            ).where(
                User.last_active >= start_date,
                User.last_active.isnot(None)
            )
        )
        sessions = session_query.all()
        
        # Простой расчет средней продолжительности сессии
        # Предполагаем, что сессия длится от создания до последней активности
        total_duration = 0
        session_count = 0
        
        for session in sessions:
            if session.last_active and session.created_at:
                duration = (session.last_active - session.created_at).total_seconds() / 60  # в минутах
                if 0 < duration < 480:  # фильтруем сессии от 0 до 8 часов
                    total_duration += duration
                    session_count += 1
        
        avg_session_duration = total_duration / session_count if session_count > 0 else 0
        
    except Exception as e:
        avg_session_duration = 0

    return {
        "hourlyActivity": [{"hour": i, "count": count} for i, count in enumerate(hours_data)],
        "dailyActivity": [{"day": day_names[i], "count": count} for i, count in enumerate(days_data)],
        "avgSessionDuration": round(avg_session_duration, 1),
        "period": period,
        "activity_type": activity_type
    }

@router.get("/content-popularity")
async def get_content_popularity_analytics(
    period: str = Query("month", description="Период: week, month, quarter, year, all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить аналитику популярности контента"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Определяем период
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # Получаем популярные промпты
    prompts_result = await db.execute(
        select(
            Generation.prompt,
            Generation.type,
            func.count(Generation.id).label('count')
        ).where(
            Generation.created_at >= start_date,
            Generation.prompt.isnot(None),
            Generation.prompt != ""
        ).group_by(Generation.prompt, Generation.type).order_by(desc('count')).limit(10)
    )
    popular_prompts = prompts_result.all()

    # Получаем статистику по типам контента
    content_result = await db.execute(
        select(
            Generation.type,
            func.count(Generation.id).label('count'),
            func.count(func.distinct(Generation.user_id)).label('unique_users')
        ).where(
            Generation.created_at >= start_date
        ).group_by(Generation.type)
    )
    content_stats = content_result.all()

    # Формируем данные
    content_type_names = {
        "lesson_plan": "Планы уроков",
        "exercise": "Упражнения",
        "game": "Игры",
        "image": "Изображения",
        "text_analysis": "Анализ текста",
        "concept_explanation": "Объяснение концепций",
        "course": "Курсы",
        "free_query": "AI-ассистент"
    }

    popular_content = []
    for stat in content_stats:
        popular_content.append({
            "type": stat.type,
            "name": content_type_names.get(stat.type, stat.type),
            "count": stat.count,
            "uniqueUsers": stat.unique_users,
            "avgPerUser": stat.count / stat.unique_users if stat.unique_users > 0 else 0
        })

    # Сортируем по популярности
    popular_content.sort(key=lambda x: x["count"], reverse=True)

    prompts_data = []
    for prompt in popular_prompts:
        prompts_data.append({
            "prompt": prompt.prompt[:100] + "..." if len(prompt.prompt) > 100 else prompt.prompt,
            "type": prompt.type,
            "typeName": content_type_names.get(prompt.type, prompt.type),
            "count": prompt.count
        })

    return {
        "popularContent": popular_content,
        "popularPrompts": prompts_data,
        "period": period
    }


@router.get("/points")
async def get_points_analytics(
    period: str = Query("week", regex="^(week|month|quarter|year|all)$"),
    operation_type: str = Query("all", regex="^(all|usage|purchase)$"),
    tariff: str = Query("all", regex="^(all|basic|tariff_2|tariff_4|tariff_6|none)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить аналитику операций с баллами"""

    # Определяем диапазон дат
    now = datetime.now(timezone.utc)

    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = now - timedelta(days=365 * 3)  # 3 года назад

    try:
        # Получаем транзакции с баллами
        transactions_query = text("""
            SELECT
                pt.id,
                pt.user_id,
                pt.amount,
                pt.transaction_type,
                pt.description,
                pt.created_at,
                u.first_name,
                u.last_name,
                u.username,
                u.tariff
            FROM point_transactions pt
            JOIN users u ON pt.user_id = u.id
            WHERE pt.created_at >= :start_date AND pt.created_at <= :end_date
        """)

        # Добавляем фильтры
        filters = []
        params = {"start_date": start_date, "end_date": now}

        if operation_type != "all":
            if operation_type == "purchase":
                filters.append("pt.transaction_type IN ('purchase', 'admin_add')")
            elif operation_type == "usage":
                filters.append("pt.transaction_type IN ('generation', 'admin_subtract')")

        if tariff != "all":
            if tariff == "none":
                filters.append("(u.tariff IS NULL OR u.tariff = 'basic')")
            else:
                filters.append("u.tariff = :tariff")
                params["tariff"] = tariff

        if filters:
            transactions_query = text(str(transactions_query) + " AND " + " AND ".join(filters))

        # Добавляем сортировку и пагинацию
        transactions_query = text(str(transactions_query) + " ORDER BY pt.created_at DESC LIMIT :limit OFFSET :offset")
        params["limit"] = limit
        params["offset"] = (page - 1) * limit

        result = await db.execute(transactions_query, params)
        transactions = result.fetchall()

        # Получаем общее количество записей
        count_query = text("""
            SELECT COUNT(*)
            FROM point_transactions pt
            JOIN users u ON pt.user_id = u.id
            WHERE pt.created_at >= :start_date AND pt.created_at <= :end_date
        """)

        if filters:
            count_query = text(str(count_query) + " AND " + " AND ".join([f for f in filters if "LIMIT" not in f and "OFFSET" not in f]))

        count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
        total_result = await db.execute(count_query, count_params)
        total_count = total_result.scalar() or 0

        # Преобразуем данные
        items = []
        for row in transactions:
            user_name = f"{row.first_name or ''} {row.last_name or ''}".strip()
            if not user_name:
                user_name = f"User {row.user_id}"

            # Определяем тип операции
            operation_type_mapped = "purchase" if row.transaction_type in ["purchase", "admin_add"] else "usage"

            # Определяем тип контента из описания (если есть)
            content_type = None
            if "generation" in row.transaction_type.lower():
                # Пытаемся извлечь тип контента из описания
                description = row.description or ""
                if "lesson_plan" in description.lower():
                    content_type = "lesson_plan"
                elif "exercise" in description.lower():
                    content_type = "exercise"
                elif "game" in description.lower():
                    content_type = "game"
                elif "image" in description.lower():
                    content_type = "image"
                elif "text_analysis" in description.lower():
                    content_type = "text_analysis"
                elif "concept_explanation" in description.lower():
                    content_type = "concept_explanation"
                elif "course" in description.lower():
                    content_type = "course"
                elif "ai_assistant" in description.lower():
                    content_type = "ai_assistant"

            items.append({
                "id": row.id,
                "user_id": row.user_id,
                "user_name": user_name,
                "username": row.username or "",
                "tariff": row.tariff,
                "type": operation_type_mapped,
                "points": abs(row.amount),  # Всегда положительное число
                "content_type": content_type,
                "created_at": row.created_at.isoformat()
            })

        # Вычисляем статистику
        stats_query = text("""
            SELECT
                SUM(CASE WHEN pt.transaction_type IN ('purchase', 'admin_add') THEN pt.amount ELSE 0 END) as total_purchased,
                SUM(CASE WHEN pt.transaction_type IN ('generation', 'admin_subtract') THEN ABS(pt.amount) ELSE 0 END) as total_used,
                COUNT(DISTINCT pt.user_id) as unique_users
            FROM point_transactions pt
            JOIN users u ON pt.user_id = u.id
            WHERE pt.created_at >= :start_date AND pt.created_at <= :end_date
        """)

        if filters:
            stats_query = text(str(stats_query) + " AND " + " AND ".join([f for f in filters if "LIMIT" not in f and "OFFSET" not in f]))

        stats_result = await db.execute(stats_query, count_params)
        stats_row = stats_result.fetchone()

        # Статистика по тарифам (покупки)
        tariff_stats_query = text("""
            SELECT
                COALESCE(u.tariff, 'none') as tariff,
                SUM(pt.amount) as total_points
            FROM point_transactions pt
            JOIN users u ON pt.user_id = u.id
            WHERE pt.created_at >= :start_date AND pt.created_at <= :end_date
                AND pt.transaction_type IN ('purchase', 'admin_add')
            GROUP BY COALESCE(u.tariff, 'none')
        """)

        tariff_result = await db.execute(tariff_stats_query, count_params)
        tariff_data = {row.tariff: row.total_points for row in tariff_result.fetchall()}

        # Статистика по типам контента (использование) - получаем из generation_metrics
        content_stats_query = text("""
            SELECT
                gm.content_type,
                COUNT(*) * 8 as total_points  -- Предполагаем 8 баллов за генерацию
            FROM generation_metrics gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.created_at >= :start_date AND gm.created_at <= :end_date
                AND gm.with_points = true
            GROUP BY gm.content_type
        """)

        content_result = await db.execute(content_stats_query, count_params)
        content_data = {row.content_type: row.total_points for row in content_result.fetchall()}

        # Добавляем изображения (15 баллов за изображение)
        image_stats_query = text("""
            SELECT
                COUNT(*) * 15 as total_points
            FROM generation_metrics gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.created_at >= :start_date AND gm.created_at <= :end_date
                AND gm.content_type = 'image'
                AND gm.with_points = true
        """)

        image_result = await db.execute(image_stats_query, count_params)
        image_points = image_result.scalar() or 0
        if image_points > 0:
            content_data["image"] = image_points

        stats = {
            "total_purchased": stats_row.total_purchased or 0,
            "total_used": stats_row.total_used or 0,
            "unique_users": stats_row.unique_users or 0,
            "by_tariff": tariff_data,
            "by_content_type": content_data
        }

        return {
            "items": items,
            "total": total_count,
            "stats": stats,
            "period": period,
            "operation_type": operation_type,
            "tariff": tariff,
            "page": page,
            "limit": limit
        }

    except Exception as e:
        # Если таблица point_transactions не существует, возвращаем пустые данные
        print(f"Points analytics error: {e}")
        return {
            "items": [],
            "total": 0,
            "stats": {
                "total_purchased": 0,
                "total_used": 0,
                "unique_users": 0,
                "by_tariff": {},
                "by_content_type": {}
            },
            "period": period,
            "operation_type": operation_type,
            "tariff": tariff,
            "page": page,
            "limit": limit
        }


@router.get("/tariffs")
async def get_tariffs_analytics(
    period: str = Query("week", regex="^(week|month|quarter|year|all)$"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить аналитику использования тарифов"""

    # Определяем диапазон дат
    now = datetime.now(timezone.utc)

    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = now - timedelta(days=365 * 3)  # 3 года назад

    try:
        # Получаем статистику генераций по тарифам
        tariff_usage_query = text("""
            SELECT
                COALESCE(u.tariff, 'basic') as tariff,
                gm.content_type,
                COUNT(*) as generation_count
            FROM generation_metrics gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.created_at >= :start_date AND gm.created_at <= :end_date
            GROUP BY COALESCE(u.tariff, 'basic'), gm.content_type
            ORDER BY tariff, generation_count DESC
        """)

        result = await db.execute(tariff_usage_query, {
            "start_date": start_date,
            "end_date": now
        })
        usage_data = result.fetchall()

        # Получаем общую статистику по тарифам
        tariff_stats_query = text("""
            SELECT
                COALESCE(u.tariff, 'basic') as tariff,
                COUNT(DISTINCT u.id) as user_count,
                COUNT(gm.id) as total_generations
            FROM users u
            LEFT JOIN generation_metrics gm ON u.id = gm.user_id
                AND gm.created_at >= :start_date AND gm.created_at <= :end_date
            GROUP BY COALESCE(u.tariff, 'basic')
            ORDER BY total_generations DESC
        """)

        stats_result = await db.execute(tariff_stats_query, {
            "start_date": start_date,
            "end_date": now
        })
        stats_data = stats_result.fetchall()

        # Получаем историю покупок тарифов
        purchases_query = text("""
            SELECT
                tp.type as tariff_type,
                ut.started_at,
                u.first_name,
                u.last_name,
                u.username,
                tp.name as tariff_name,
                tp.price_points
            FROM user_tariffs ut
            JOIN users u ON ut.user_id = u.id
            JOIN tariff_plans tp ON ut.tariff_id = tp.id
            WHERE ut.started_at >= :start_date AND ut.started_at <= :end_date
            ORDER BY ut.started_at DESC
            LIMIT 100
        """)

        purchases_result = await db.execute(purchases_query, {
            "start_date": start_date,
            "end_date": now
        })
        purchases_data = purchases_result.fetchall()

        # Обрабатываем данные по тарифам
        by_tariff = {}
        content_types = ['lesson_plan', 'exercise', 'game', 'image', 'text_analysis', 'concept_explanation', 'course', 'ai_assistant']

        # Инициализируем структуру для каждого тарифа
        for stat in stats_data:
            tariff = stat.tariff
            by_tariff[tariff] = {
                "total": stat.total_generations or 0,
                "user_count": stat.user_count or 0,
                "by_type": {content_type: 0 for content_type in content_types},
                "by_type_percent": {content_type: 0 for content_type in content_types},
                "popular_types": []
            }

        # Заполняем данные по типам контента
        for usage in usage_data:
            tariff = usage.tariff
            content_type = usage.content_type
            count = usage.generation_count

            if tariff in by_tariff and content_type in by_tariff[tariff]["by_type"]:
                by_tariff[tariff]["by_type"][content_type] = count

                # Вычисляем процент
                total = by_tariff[tariff]["total"]
                if total > 0:
                    by_tariff[tariff]["by_type_percent"][content_type] = round((count / total) * 100, 1)

        # Формируем популярные типы для каждого тарифа
        for tariff in by_tariff:
            popular_types = []
            for content_type, count in by_tariff[tariff]["by_type"].items():
                if count > 0:
                    popular_types.append({
                        "type": content_type,
                        "count": count,
                        "percent": by_tariff[tariff]["by_type_percent"][content_type]
                    })

            # Сортируем по количеству и берем топ-5
            popular_types.sort(key=lambda x: x["count"], reverse=True)
            by_tariff[tariff]["popular_types"] = popular_types[:5]

        # Формируем историю покупок
        purchase_history = []
        for purchase in purchases_data:
            user_name = f"{purchase.first_name or ''} {purchase.last_name or ''}".strip()
            if not user_name:
                user_name = purchase.username or "Unknown User"

            purchase_history.append({
                "tariff_type": purchase.tariff_type,
                "tariff_name": purchase.tariff_name,
                "price_points": purchase.price_points,
                "user_name": user_name,
                "username": purchase.username or "",
                "purchased_at": purchase.started_at.isoformat(),
                "date": purchase.started_at.strftime("%d.%m.%Y %H:%M")
            })

        # Вычисляем общую статистику
        total_generations = sum(tariff["total"] for tariff in by_tariff.values())
        total_users = sum(tariff["user_count"] for tariff in by_tariff.values())

        return {
            "by_tariff": by_tariff,
            "period": period,
            "total_generations": total_generations,
            "total_users": total_users,
            "purchase_history": purchase_history,
            "generated_at": now.isoformat()
        }

    except Exception as e:
        # Если таблицы не существуют, возвращаем пустые данные
        print(f"Tariffs analytics error: {e}")
        return {
            "by_tariff": {
                "basic": {
                    "total": 0,
                    "user_count": 0,
                    "by_type": {content_type: 0 for content_type in ['lesson_plan', 'exercise', 'game', 'image', 'text_analysis', 'concept_explanation', 'course', 'ai_assistant']},
                    "by_type_percent": {content_type: 0 for content_type in ['lesson_plan', 'exercise', 'game', 'image', 'text_analysis', 'concept_explanation', 'course', 'ai_assistant']},
                    "popular_types": []
                }
            },
            "period": period,
            "total_generations": 0,
            "total_users": 0,
            "purchase_history": [],
            "generated_at": now.isoformat()
        }