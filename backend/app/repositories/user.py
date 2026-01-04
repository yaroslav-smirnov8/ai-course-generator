# app/repositories/user.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import datetime, timezone
from .base import BaseRepository
from ..models.user import User
from ..core.constants import UserRole

class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        return await self.get_by_field("telegram_id", telegram_id)

    async def get_active_users(self) -> List[User]:
        """Получить активных пользователей"""
        query = select(self.model).where(self.model.has_access == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Получить пользователей по роли"""
        query = select(self.model).where(self.model.role == role)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_last_active(self, user_id: int) -> None:
        """Обновить время последней активности"""
        await self.update(user_id, {"last_active": datetime.now(timezone.utc)})

    async def get_users_with_valid_tariff(self) -> List[User]:
        """Получить пользователей с активным тарифом"""
        query = select(self.model).where(
            and_(
                self.model.tariff.isnot(None),
                self.model.tariff_valid_until > datetime.now(timezone.utc)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_telegram_user(self, telegram_data: dict) -> User:
        """Создать пользователя из данных Telegram"""
        user_data = {
            "telegram_id": telegram_data["id"],
            "username": telegram_data.get("username"),
            "first_name": telegram_data.get("first_name"),
            "last_name": telegram_data.get("last_name"),
            "role": UserRole.USER,
            "has_access": True,
            "invite_code": telegram_data.get("invite_code")
        }
        return await self.create(user_data)