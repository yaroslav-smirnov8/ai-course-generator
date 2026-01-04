from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from datetime import datetime, timedelta, timezone
import logging

from ..models import LinkClick
from ..schemas.link_clicks import LinkClickCreate

logger = logging.getLogger(__name__)


class LinkClickManager:
    """Менеджер для работы с переходами по ссылкам"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_link_click(self, link_click_data: LinkClickCreate) -> LinkClick:
        """Создать запись о переходе по ссылке"""
        logger.info(f"LinkClickManager.create_link_click: Создание записи о переходе по ссылке")
        logger.info(f"Данные: {link_click_data}")

        # Подробное логирование для отладки
        logger.info(f"Детали данных:")
        logger.info(f"- link_id: {link_click_data.link_id}")
        logger.info(f"- link_title: {link_click_data.link_title}")
        logger.info(f"- link_url: {link_click_data.link_url}")
        logger.info(f"- user_id: {link_click_data.user_id}")

        # Проверяем состояние сессии
        logger.info(f"Состояние сессии перед созданием записи: {self.session}")

        try:
            # Создаем объект LinkClick
            link_click = LinkClick(
                link_id=link_click_data.link_id,
                link_title=link_click_data.link_title,
                link_url=link_click_data.link_url,
                user_id=link_click_data.user_id
            )
            logger.info(f"Создан объект LinkClick: {link_click.__dict__}")

            # Добавляем объект в сессию
            self.session.add(link_click)
            logger.info(f"Объект добавлен в сессию")

            # Сбрасываем сессию
            await self.session.flush()
            logger.info(f"Сессия сброшена, ID объекта: {link_click.id}")

            # Проверяем, что объект действительно добавлен в сессию

            check_query = select(LinkClick).where(LinkClick.id == link_click.id)
            result = await self.session.execute(check_query)
            saved_link_click = result.scalar_one_or_none()

            if saved_link_click:
                logger.info(f"Проверка в менеджере: запись найдена в сессии с ID {saved_link_click.id}")
            else:
                logger.warning(f"Проверка в менеджере: запись с ID {link_click.id} не найдена в сессии!")

            return link_click
        except Exception as e:
            logger.error(f"Ошибка при создании записи о переходе: {str(e)}", exc_info=True)
            raise

    async def get_link_clicks_analytics(self, period: str = "week"):
        """Получить аналитику по переходам по ссылкам"""
        logger.info(f"LinkClickManager.get_link_clicks_analytics: Получение аналитики за период {period}")

        try:
            # Определяем временной интервал на основе выбранного периода
            now = datetime.now(timezone.utc)

            # Удаляем информацию о часовом поясе для совместимости с базой данных
            now_naive = now.replace(tzinfo=None)

            if period == "week":
                start_date = now_naive - timedelta(days=7)
            elif period == "month":
                start_date = now_naive - timedelta(days=30)
            elif period == "year":
                start_date = now_naive - timedelta(days=365)
            else:  # all
                start_date = datetime(2000, 1, 1)  # Достаточно давно для "всех времен", без timezone

            logger.info(f"Период анализа: с {start_date} по {now_naive}")

            # 1. Получаем общее количество переходов
            total_clicks_query = select(func.count(LinkClick.id)).where(
                LinkClick.clicked_at >= start_date
            )
            logger.info(f"SQL запрос для общего количества переходов: {total_clicks_query}")
            total_clicks = await self.session.scalar(total_clicks_query)
            logger.info(f"Общее количество переходов: {total_clicks}")

            # 2. Получаем количество уникальных пользователей
            unique_users_query = select(func.count(func.distinct(LinkClick.user_id))).where(
                and_(
                    LinkClick.clicked_at >= start_date,
                    LinkClick.user_id.is_not(None)
                )
            )
            logger.info(f"SQL запрос для уникальных пользователей: {unique_users_query}")
            unique_users = await self.session.scalar(unique_users_query)
            logger.info(f"Количество уникальных пользователей: {unique_users}")

            # 3. Получаем популярные ссылки
            popular_links_query = select(
                LinkClick.link_id,
                LinkClick.link_title,
                LinkClick.link_url,
                func.count(LinkClick.id).label("click_count")
            ).where(
                LinkClick.clicked_at >= start_date
            ).group_by(
                LinkClick.link_id, LinkClick.link_title, LinkClick.link_url
            ).order_by(
                desc("click_count")
            ).limit(10)

            logger.info(f"SQL запрос для популярных ссылок: {popular_links_query}")
            popular_links_result = await self.session.execute(popular_links_query)

            popular_links = []
            for row in popular_links_result:
                link_data = {
                    "link_id": row.link_id,
                    "link_title": row.link_title,
                    "link_url": row.link_url,
                    "click_count": row.click_count
                }
                popular_links.append(link_data)
                logger.info(f"Популярная ссылка: {link_data}")

            # 4. Получаем данные о переходах по времени
            # Определяем количество дней для группировки
            days_count = 7 if period == "week" else 30 if period == "month" else 365 if period == "year" else 30
            logger.info(f"Количество дней для анализа: {days_count}")

            # Создаем список дат для графика
            clicks_by_time = []
            for i in range(days_count):
                date = now - timedelta(days=days_count - i - 1)
                date_str = date.strftime("%Y-%m-%d")

                # Получаем количество переходов за этот день
                # Используем timezone-naive datetime для совместимости с базой данных
                day_start = datetime(date.year, date.month, date.day, 0, 0, 0)
                day_end = datetime(date.year, date.month, date.day, 23, 59, 59)

                clicks_count_query = select(
                    func.count(LinkClick.id)
                ).where(
                    and_(
                        LinkClick.clicked_at >= day_start,
                        LinkClick.clicked_at <= day_end
                    )
                )

                logger.info(f"SQL запрос для переходов за {date_str}: {clicks_count_query}")
                clicks_count = await self.session.scalar(clicks_count_query) or 0
                logger.info(f"Количество переходов за {date_str}: {clicks_count}")

                clicks_by_time.append({
                    "date": date_str,
                    "count": clicks_count
                })

            result = {
                "total_clicks": total_clicks or 0,
                "unique_users": unique_users or 0,
                "popular_links": popular_links,
                "clicks_by_time": clicks_by_time,
                "period": period
            }

            logger.info(f"Результат аналитики: total_clicks={result['total_clicks']}, unique_users={result['unique_users']}")
            return result

        except Exception as e:
            logger.error(f"Ошибка при получении аналитики переходов: {str(e)}", exc_info=True)
            raise
