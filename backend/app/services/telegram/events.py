# app/services/telegram/events.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from ...repositories.user import UserRepository
from ...core.cache import CacheService
import logging

logger = logging.getLogger(__name__)

class TelegramEventHandler:
    def __init__(self, session: AsyncSession, cache: CacheService):
        self.session = session
        self.cache = cache
        self.user_repository = UserRepository(session)

    async def handle_close_event(self, telegram_id: int):
        """Обработка закрытия WebApp"""
        try:
            user = await self.user_repository.get_by_telegram_id(telegram_id)
            if user:
                # Сохраняем состояние сессии
                session_data = {
                    'last_state': datetime.utcnow().isoformat(),
                    'user_id': user.id,
                    'telegram_id': telegram_id
                }
                await self.cache.cache_data(
                    f"session:{telegram_id}",
                    session_data,
                    ttl=3600  # 1 час на восстановление
                )
                logger.info(f"Saved session state for user {telegram_id}")

        except Exception as e:
            logger.error(f"Error handling close event: {e}")

    async def handle_access_revoked(self, telegram_id: int):
        """Обработка отзыва доступа к WebApp"""
        try:
            user = await self.user_repository.get_by_telegram_id(telegram_id)
            if user:
                await self.user_repository.update(
                    user.id,
                    {
                        "has_access": False,
                        "unsubscribed_at": datetime.utcnow()
                    }
                )
                # Инвалидируем кэш
                await self.cache.invalidate_pattern(f"session:{telegram_id}")
                await self.cache.invalidate_pattern(f"user:{user.id}")
                logger.info(f"Access revoked for user {telegram_id}")

        except Exception as e:
            logger.error(f"Error handling access revocation: {e}")