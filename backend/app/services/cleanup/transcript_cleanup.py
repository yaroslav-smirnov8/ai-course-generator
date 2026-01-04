from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.sql import exists
from ...models import VideoTranscript
import logging

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def cleanup_expired_transcripts(self) -> int:
        """Clean up expired video transcripts"""
        try:
            # Создаем query для удаления с использованием delete()
            delete_query = delete(VideoTranscript).where(
                VideoTranscript.expires_at < datetime.utcnow()
            ).returning(VideoTranscript.id)

            # Выполняем запрос и получаем результат
            result = await self.session.execute(delete_query)
            deleted_items = result.scalars().all()
            deleted_count = len(deleted_items)

            # Коммитим транзакцию
            await self.session.commit()

            logger.info(f"Cleaned up {deleted_count} expired transcripts")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during transcript cleanup: {str(e)}")
            await self.session.rollback()
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()