#app/api/v1/telegram.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...services.telegram.events import TelegramEventHandler
from ...services.telegram.session import TelegramSessionManager
from ...core.cache import get_cache_service

router = APIRouter()

@router.post("/webhook/close")
async def handle_webapp_close(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    cache = Depends(get_cache_service)
):
    handler = TelegramEventHandler(session, cache)
    await handler.handle_close_event(telegram_id)
    return {"status": "success"}

@router.post("/webhook/revoke")
async def handle_access_revoke(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    cache = Depends(get_cache_service)
):
    handler = TelegramEventHandler(session, cache)
    await handler.handle_access_revoked(telegram_id)
    return {"status": "success"}

@router.get("/session/restore/{telegram_id}")
async def restore_webapp_session(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    cache = Depends(get_cache_service)
):
    session_manager = TelegramSessionManager(session, cache)
    session_data = await session_manager.restore_session(telegram_id)
    return session_data or {"status": "no_session"}