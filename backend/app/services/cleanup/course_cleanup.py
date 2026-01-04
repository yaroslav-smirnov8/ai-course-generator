from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from datetime import datetime, timedelta
from typing import Optional
from ...models.course import Course
import logging

logger = logging.getLogger(__name__)


class CourseCleanupService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.retention_days = 7  # Срок хранения неиспользуемых курсов

    async def cleanup_unused_courses(self) -> int:
        """Очистка неиспользуемых курсов"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

            # Создаем query для удаления
            delete_query = delete(Course).where(
                Course.is_used == False,
                Course.created_at < cutoff_date
            ).returning(Course.id)

            # Выполняем удаление и получаем количество удаленных записей
            result = await self.session.execute(delete_query)
            deleted_count = len(result.all())

            await self.session.commit()
            logger.info(f"Cleaned up {deleted_count} unused courses")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during course cleanup: {str(e)}")
            await self.session.rollback()
            raise

    async def mark_course_as_used(self, course_id: int) -> bool:
        """Отмечает курс как использованный"""
        try:
            # Создаем query для проверки существования курса
            course_query = select(Course).where(Course.id == course_id)
            result = await self.session.execute(course_query)
            course = result.scalar_one_or_none()

            if course:
                # Создаем query для обновления
                update_query = update(Course).where(
                    Course.id == course_id
                ).values(
                    is_used=True,
                    last_used=datetime.utcnow()
                )
                await self.session.execute(update_query)
                await self.session.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Error marking course as used: {str(e)}")
            await self.session.rollback()
            return False

    async def cleanup_old_courses(self, days: Optional[int] = None) -> int:
        """Принудительная очистка старых курсов"""
        try:
            retention = days or self.retention_days
            cutoff_date = datetime.utcnow() - timedelta(days=retention)

            # Создаем query для удаления
            delete_query = delete(Course).where(
                Course.created_at < cutoff_date
            ).returning(Course.id)

            # Выполняем удаление и получаем количество удаленных записей
            result = await self.session.execute(delete_query)
            deleted_count = len(result.all())

            await self.session.commit()
            logger.info(f"Cleaned up {deleted_count} old courses")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during old course cleanup: {str(e)}")
            await self.session.rollback()
            raise