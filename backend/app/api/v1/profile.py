from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.security import get_current_user
from ...core.database import get_db
from ...models import User
from ...schemas.user import UserProfile
from ...services.user import UserManager

router = APIRouter()

# Dependency для получения UserManager
async def get_user_manager(session: AsyncSession = Depends(get_db)) -> UserManager:
    return UserManager(session)

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    profile = await user_manager.get_user_profile(current_user.id)
    return profile

@router.post("/sync/telegram")
async def sync_telegram_data(
    telegram_data: dict,
    current_user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    await user_manager.update_telegram_data(current_user.id, telegram_data)
    return {"status": "success"}