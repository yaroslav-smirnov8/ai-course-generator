from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging
from sqlalchemy import and_, func, desc

from ...core.database import get_db
from ...models import User, LinkClick
from ...schemas.link_clicks import LinkClickCreate, LinkClickResponse, LinkClicksAnalyticsResponse
from ...managers.link_click_manager import LinkClickManager
from ...core.security import get_current_user, get_current_admin_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/link_click", response_model=LinkClickResponse)
async def log_link_click(
    link_click_data: LinkClickCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Логирование перехода по ссылке"""
    logger.info(f"=== log_link_click ===")
    logger.info(f"Получен запрос на логирование перехода по ссылке: {link_click_data}")
    logger.info(f"Текущий пользователь: {current_user.id if current_user else 'Не авторизован'}")

    # Подробное логирование для отладки
    logger.info(f"Детали запроса:")
    logger.info(f"- link_id: {link_click_data.link_id}")
    logger.info(f"- link_title: {link_click_data.link_title}")
    logger.info(f"- link_url: {link_click_data.link_url}")
    logger.info(f"- user_id: {link_click_data.user_id}")

    try:
        # Если пользователь авторизован, добавляем его ID
        if current_user and not link_click_data.user_id:
            logger.info(f"Добавляем ID пользователя {current_user.id} к данным о переходе")
            link_click_data.user_id = current_user.id

        logger.info(f"Создаем запись о переходе с данными: {link_click_data}")
        manager = LinkClickManager(session)
        link_click = await manager.create_link_click(link_click_data)

        logger.info(f"Запись о переходе создана: {link_click.id}")
        await session.commit()
        logger.info(f"Транзакция успешно завершена")

        # Проверяем, что запись действительно создана
        from sqlalchemy import select
        from ...models import LinkClick

        check_query = select(LinkClick).where(LinkClick.id == link_click.id)
        result = await session.execute(check_query)
        saved_link_click = result.scalar_one_or_none()

        if saved_link_click:
            logger.info(f"Проверка: запись найдена в базе данных с ID {saved_link_click.id}")
            logger.info(f"Данные записи: {saved_link_click.__dict__}")
        else:
            logger.warning(f"Проверка: запись с ID {link_click.id} не найдена в базе данных!")

        return link_click
    except Exception as e:
        logger.error(f"Error logging link click: {str(e)}", exc_info=True)
        await session.rollback()
        logger.error(f"Транзакция отменена")
        raise HTTPException(
            status_code=500,
            detail=f"Error logging link click: {str(e)}"
        )


@router.get("/links", response_model=LinkClicksAnalyticsResponse)
async def get_links_analytics(
    period: str = Query("week", description="Период анализа: week, month, year, all"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Получить аналитику по переходам по ссылкам (только для админов)"""
    logger.info(f"=== get_links_analytics ===")
    logger.info(f"Запрос аналитики переходов по ссылкам за период: {period}")
    logger.info(f"Запрос от пользователя: {current_user.id} (роль: {current_user.role})")

    try:
        # Проверим количество записей в таблице link_clicks
        from sqlalchemy import select, func
        from ...models import LinkClick

        count_query = select(func.count(LinkClick.id))
        total_count = await session.scalar(count_query)
        logger.info(f"Всего записей в таблице link_clicks: {total_count}")

        # Получаем аналитику
        manager = LinkClickManager(session)
        analytics = await manager.get_link_clicks_analytics(period)

        logger.info(f"Получена аналитика: {analytics}")
        return analytics
    except Exception as e:
        logger.error(f"Error getting links analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting links analytics: {str(e)}"
        )
