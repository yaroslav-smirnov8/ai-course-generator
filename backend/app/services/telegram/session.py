# app/services/telegram/session.py
from typing import Optional, Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from ...repositories.user import UserRepository
from ...core.cache import CacheService
import logging

logger = logging.getLogger(__name__)


class TelegramSessionManager:
    def __init__(self, session: AsyncSession, cache: CacheService):
        self.session = session
        self.cache = cache
        self.user_repository = UserRepository(session)

    async def restore_session(self, telegram_id: int) -> Optional[Dict]:
        """Восстановление состояния сессии"""
        try:
            # Пробуем получить сохраненное состояние
            session_data = await self.cache.get_cached_data(f"session:{telegram_id}")
            if session_data:
                user = await self.user_repository.get_by_telegram_id(telegram_id)
                if user and user.has_access:
                    # Проверяем актуальность сессии
                    last_state = datetime.fromisoformat(session_data['last_state'])
                    if (datetime.now(timezone.utc) - last_state).seconds < 3600:
                        await self._update_session_state(telegram_id, user.id)
                        return session_data

            return None

        except Exception as e:
            logger.error(f"Error restoring session: {e}")
            return None

    async def _update_session_state(self, telegram_id: int, user_id: int):
        """Обновление состояния сессии"""
        try:
            # Обновляем время последней активности
            await self.user_repository.update_last_active(user_id)

            # Обновляем данные сессии
            session_data = {
                'last_state': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id,
                'telegram_id': telegram_id
            }
            await self.cache.cache_data(
                f"session:{telegram_id}",
                session_data,
                ttl=3600
            )

        except Exception as e:
            logger.error(f"Error updating session state: {e}")