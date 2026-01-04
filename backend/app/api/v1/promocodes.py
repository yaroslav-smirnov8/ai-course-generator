from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import secrets
import string

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.promocode import PromoCode, PromoCodeUsage, PromoCodeType, PromoCodeUsageType
from app.schemas.promocode import (
    PromoCodeCreate,
    PromoCodeUpdate,
    PromoCodeResponse,
    PromoCodeApplyRequest,
    PromoCodeApplyResponse,
    PromoCodeListResponse,
    PromoCodeStatsResponse,
    PromoCodeUsageResponse
)

router = APIRouter(prefix="/admin/promocodes", tags=["promocodes"])
user_router = APIRouter(prefix="/promocodes", tags=["promocodes"])


def generate_promocode(length: int = 8) -> str:
    """Генерация случайного промокода"""
    characters = string.ascii_uppercase + string.digits
    # Исключаем похожие символы
    characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1')
    return ''.join(secrets.choice(characters) for _ in range(length))


@router.post("/", response_model=PromoCodeResponse)
async def create_promocode(
    promocode_data: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать новый промокод"""

    # Генерируем код, если не указан
    code = promocode_data.code
    if not code:
        # Генерируем уникальный код
        for _ in range(10):  # Максимум 10 попыток
            code = generate_promocode()
            existing = await db.execute(select(PromoCode).where(PromoCode.code == code))
            if not existing.scalar_one_or_none():
                break
        else:
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать уникальный код")
    else:
        # Проверяем уникальность указанного кода
        existing = await db.execute(select(PromoCode).where(PromoCode.code == code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Промокод с таким кодом уже существует")

    # Создаем промокод
    promocode = PromoCode(
        code=code,
        name=promocode_data.name,
        description=promocode_data.description,
        type=promocode_data.type,
        usage_type=promocode_data.usage_type,
        points_amount=promocode_data.points_amount,
        tariff_type=promocode_data.tariff_type,
        tariff_duration_months=promocode_data.tariff_duration_months,
        discount_percent=promocode_data.discount_percent,
        usage_limit=promocode_data.usage_limit,
        user_id=promocode_data.user_id,
        valid_until=promocode_data.valid_until,
        conditions=promocode_data.conditions,
        created_by=current_user.id
    )

    db.add(promocode)
    await db.commit()
    await db.refresh(promocode)

    return promocode


@router.get("/", response_model=PromoCodeListResponse)
async def get_promocodes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    type_filter: Optional[PromoCodeType] = Query(None),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить список промокодов"""

    # Базовый запрос
    query = select(PromoCode)
    count_query = select(func.count(PromoCode.id))

    # Фильтры
    conditions = []

    if search:
        conditions.append(
            or_(
                PromoCode.code.ilike(f"%{search}%"),
                PromoCode.name.ilike(f"%{search}%")
            )
        )

    if type_filter:
        conditions.append(PromoCode.type == type_filter)

    if active_only:
        now = datetime.now(timezone.utc)
        conditions.append(
            and_(
                PromoCode.is_active == True,
                or_(PromoCode.valid_until.is_(None), PromoCode.valid_until > now),
                or_(PromoCode.usage_limit.is_(None), PromoCode.usage_count < PromoCode.usage_limit)
            )
        )

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # Подсчет общего количества
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Пагинация и сортировка
    query = query.order_by(desc(PromoCode.created_at))
    query = query.offset((page - 1) * size).limit(size)

    # Выполнение запроса
    result = await db.execute(query)
    promocodes = result.scalars().all()

    pages = (total + size - 1) // size

    return PromoCodeListResponse(
        items=promocodes,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/history")
async def get_promocodes_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    promocode: Optional[str] = Query(None),
    tariff: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить историю использования промокодов (админ)"""
    
    # Базовый запрос для получения истории использования промокодов
    query = select(PromoCodeUsage).join(PromoCode)
    count_query = select(func.count(PromoCodeUsage.id)).join(PromoCode)
    
    # Фильтры
    conditions = []
    
    if promocode:
        conditions.append(PromoCode.code.ilike(f"%{promocode}%"))
    
    if tariff:
        conditions.append(PromoCodeUsage.tariff_activated == tariff)
    
    if date_from:
        try:
            date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            conditions.append(PromoCodeUsage.used_at >= date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            conditions.append(PromoCodeUsage.used_at <= date_to_parsed)
        except ValueError:
            pass
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Подсчет общего количества
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация и сортировка
    query = query.order_by(desc(PromoCodeUsage.used_at))
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Выполнение запроса
    result = await db.execute(query)
    usages = result.scalars().all()
    
    return {
        "items": usages,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/code/{code}", response_model=PromoCodeResponse)
async def get_promocode(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить промокод по коду"""

    result = await db.execute(select(PromoCode).where(PromoCode.code == code))
    promocode = result.scalar_one_or_none()

    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    return promocode


@router.put("/code/{code}", response_model=PromoCodeResponse)
async def update_promocode(
    code: str,
    promocode_data: PromoCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить промокод"""

    result = await db.execute(select(PromoCode).where(PromoCode.code == code))
    promocode = result.scalar_one_or_none()

    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    # Обновляем только переданные поля
    update_data = promocode_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(promocode, field, value)

    await db.commit()
    await db.refresh(promocode)

    return promocode


@router.delete("/code/{code}")
async def delete_promocode(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить промокод"""

    result = await db.execute(select(PromoCode).where(PromoCode.code == code))
    promocode = result.scalar_one_or_none()

    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    await db.delete(promocode)
    await db.commit()

    return {"message": "Промокод успешно удален"}


@router.post("/code/{code}/deactivate")
async def deactivate_promocode(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Деактивировать промокод"""

    result = await db.execute(select(PromoCode).where(PromoCode.code == code))
    promocode = result.scalar_one_or_none()

    if not promocode:
        raise HTTPException(status_code=404, detail="Промокод не найден")

    promocode.is_active = False
    await db.commit()

    return {"message": "Промокод деактивирован"}


@router.get("/stats", response_model=PromoCodeStatsResponse)
async def get_promocode_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить статистику промокодов"""

    now = datetime.now(timezone.utc)

    # Общая статистика промокодов
    total_result = await db.execute(select(func.count(PromoCode.id)))
    total_promocodes = total_result.scalar()

    active_result = await db.execute(
        select(func.count(PromoCode.id)).where(
            and_(
                PromoCode.is_active == True,
                or_(PromoCode.valid_until.is_(None), PromoCode.valid_until > now)
            )
        )
    )
    active_promocodes = active_result.scalar()

    expired_result = await db.execute(
        select(func.count(PromoCode.id)).where(
            and_(
                PromoCode.valid_until.is_not(None),
                PromoCode.valid_until <= now
            )
        )
    )
    expired_promocodes = expired_result.scalar()

    used_result = await db.execute(
        select(func.count(PromoCode.id)).where(
            and_(
                PromoCode.usage_limit.is_not(None),
                PromoCode.usage_count >= PromoCode.usage_limit
            )
        )
    )
    used_promocodes = used_result.scalar()

    # Статистика использований
    total_usages_result = await db.execute(select(func.count(PromoCodeUsage.id)))
    total_usages = total_usages_result.scalar()

    points_result = await db.execute(select(func.sum(PromoCodeUsage.points_added)))
    total_points_distributed = points_result.scalar() or 0

    tariffs_result = await db.execute(
        select(func.count(PromoCodeUsage.id)).where(
            PromoCodeUsage.tariff_activated.is_not(None)
        )
    )
    total_tariffs_activated = tariffs_result.scalar()

    return PromoCodeStatsResponse(
        total_promocodes=total_promocodes,
        active_promocodes=active_promocodes,
        expired_promocodes=expired_promocodes,
        used_promocodes=used_promocodes,
        total_usages=total_usages,
        total_points_distributed=total_points_distributed,
        total_tariffs_activated=total_tariffs_activated,
        most_popular_promocodes=[],  # TODO: Реализовать
        usage_by_type={},  # TODO: Реализовать
        usage_by_month=[]  # TODO: Реализовать
    )


# Пользовательские эндпоинты для применения промокодов
@user_router.post("/apply", response_model=PromoCodeApplyResponse)
async def apply_promocode(
    request_data: PromoCodeApplyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Применить промокод"""

    # Найти промокод
    result = await db.execute(select(PromoCode).where(PromoCode.code == request_data.code))
    promocode = result.scalar_one_or_none()

    if not promocode:
        return PromoCodeApplyResponse(
            success=False,
            message="Промокод не найден"
        )

    # Проверить валидность
    if not promocode.is_valid:
        return PromoCodeApplyResponse(
            success=False,
            message="Промокод недействителен или истек"
        )

    # Проверить, для конкретного пользователя ли промокод
    if promocode.usage_type == PromoCodeUsageType.SINGLE_USER and promocode.user_id != current_user.id:
        return PromoCodeApplyResponse(
            success=False,
            message="Этот промокод предназначен для другого пользователя"
        )

    # Проверить, не использовал ли уже этот пользователь данный промокод
    existing_usage = await db.execute(
        select(PromoCodeUsage).where(
            and_(
                PromoCodeUsage.promocode_id == promocode.id,
                PromoCodeUsage.user_id == current_user.id
            )
        )
    )
    if existing_usage.scalar_one_or_none():
        return PromoCodeApplyResponse(
            success=False,
            message="Вы уже использовали этот промокод"
        )

    # Применить промокод
    points_added = 0
    tariff_activated = None
    tariff_duration = None
    discount_applied = 0.0

    try:
        if promocode.type == PromoCodeType.POINTS:
            # Добавить баллы
            current_user.points += promocode.points_amount
            points_added = promocode.points_amount

        elif promocode.type == PromoCodeType.TARIFF:
            # Активировать тариф (упрощенная версия)
            # TODO: Интегрировать с TariffManager когда он будет готов

            # Вычисляем дату окончания тарифа
            end_date = datetime.now(timezone.utc) + timedelta(days=30 * promocode.tariff_duration_months)

            # Обновляем тариф пользователя напрямую
            current_user.tariff = promocode.tariff_type
            current_user.tariff_valid_until = end_date

            tariff_activated = promocode.tariff_type
            tariff_duration = promocode.tariff_duration_months

        elif promocode.type == PromoCodeType.DISCOUNT:
            # Скидка будет применена при следующей покупке
            discount_applied = promocode.discount_percent

        # Создать запись об использовании
        usage = PromoCodeUsage(
            promocode_id=promocode.id,
            user_id=current_user.id,
            points_added=points_added,
            tariff_activated=tariff_activated,
            tariff_duration=tariff_duration,
            discount_applied=discount_applied,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        db.add(usage)

        # Увеличить счетчик использований промокода
        promocode.usage_count += 1

        await db.commit()
        await db.refresh(usage)
        await db.refresh(promocode)

        return PromoCodeApplyResponse(
            success=True,
            message="Промокод успешно применен!",
            promocode=promocode,
            usage=usage,
            points_added=points_added,
            tariff_activated=tariff_activated,
            tariff_duration=tariff_duration,
            discount_applied=discount_applied
        )

    except Exception as e:
        await db.rollback()
        return PromoCodeApplyResponse(
            success=False,
            message=f"Ошибка при применении промокода: {str(e)}"
        )


@user_router.get("/history", response_model=List[PromoCodeUsageResponse])
async def get_user_promocode_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить историю использования промокодов пользователем"""

    result = await db.execute(
        select(PromoCodeUsage)
        .where(PromoCodeUsage.user_id == current_user.id)
        .order_by(desc(PromoCodeUsage.used_at))
    )

    usages = result.scalars().all()
    return usages
