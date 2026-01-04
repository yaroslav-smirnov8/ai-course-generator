# app/services/session/session.py
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
from ...repositories.user import UserRepository
from ...models.user import User

class SessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)

    async def create_user_session(self, telegram_data: dict) -> User:
        """
        Создает или обновляет сессию пользователя
        """
        # Находим или создаем пользователя
        user = await self.user_repository.get_by_telegram_id(telegram_data["id"])
        if not user:
            user = await self.user_repository.create_telegram_user(telegram_data)

        # Обновляем время последней активности
        await self.user_repository.update_last_active(user.id)

        return user

    async def validate_telegram_auth(self, telegram_data: dict) -> bool:
        """
        Проверяет данные аутентификации Telegram
        Реальная проверка выполняется в middleware
        """
        return True

    async def check_session_valid(self, user_id: int) -> bool:
        """
        Проверяет активность пользователя
        """
        user = await self.user_repository.get(user_id)
        if not user:
            return False

        # Проверяем, был ли пользователь активен в последние 24 часа
        if user.last_active:
            return datetime.utcnow() - user.last_active < timedelta(days=1)
        return False