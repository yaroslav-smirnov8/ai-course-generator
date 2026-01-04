# app/api/v1/export.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Optional

from ...core.database import get_db
from ...core.security import get_current_admin_user
from ...services.generations.manager import GenerationService
from ...schemas.generations import GenerationFilter
from ...models.user import User

router = APIRouter()

@router.get("/generations")
async def export_generations(
    format: str = Query("csv", regex="^(csv|json)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    type: Optional[str] = None,
    user_id: Optional[int] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Export generations data in CSV or JSON format"""
    async with GenerationService(session) as manager:
        try:
            # Проверяем валидность дат
            if start_date and end_date and end_date < start_date:
                raise HTTPException(
                    status_code=400,
                    detail="End date cannot be earlier than start date"
                )

            # Если даты не указаны, берем последний месяц
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            filter = GenerationFilter(
                start_date=start_date,
                end_date=end_date,
                type=type,
                user_id=user_id
            )

            content_stream = await manager.export_generations(format, filter)

            media_type = "text/csv" if format == "csv" else "application/json"
            filename = f"generations_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"

            return StreamingResponse(
                content_stream,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "cache-Control": "no-cache"
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error exporting generations: {str(e)}"
            )