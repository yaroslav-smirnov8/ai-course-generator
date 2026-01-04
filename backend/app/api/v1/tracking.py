# app/api/v1/tracking.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...services.tracking.usage import UsageTracker
from ...schemas.tracking import UsageLogCreate, UsageLogResponse
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/usage", response_model=UsageLogResponse)
async def log_usage(
   log_data: UsageLogCreate,
   session: AsyncSession = Depends(get_db)
):
   async with UsageTracker(session) as tracker:
       try:
           log = await tracker.log_usage(log_data)
           if log is None:
               # Если log_usage вернул None, значит произошла ошибка,
               # но мы хотим вернуть успешный ответ, чтобы не блокировать пользователя
               logger.warning(f"Failed to log usage, but continuing: {log_data}")
               return Response(status_code=200, content='{"status":"ok"}')
           return log
       except Exception as e:
           logger.error(f"Error in log_usage endpoint: {str(e)}")
           # Также возвращаем успешный ответ, чтобы не блокировать пользователя
           return Response(status_code=200, content='{"status":"handled"}')

@router.get("/usage/{user_id}", response_model=List[UsageLogResponse])
async def get_user_usage(
   user_id: int,
   session: AsyncSession = Depends(get_db)
):
   async with UsageTracker(session) as tracker:
       logs = await tracker.get_user_logs(user_id)
       return logs