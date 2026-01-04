# api/v1/generations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from ...core.database import get_db
from ...core.security import get_current_user, get_current_admin_user
from ...services.generations import GenerationService
from ...models.user import User
from ...schemas.generations import (
    GenerationResponse,
    GenerationListResponse,
    GenerationFilter
)

router = APIRouter()


@router.get("/generations", response_model=GenerationListResponse)
async def list_generations(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        type: Optional[str] = None,
        user_id: Optional[int] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список генераций с фильтрацией"""
    # Проверяем права доступа
    if user_id and user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view other user's generations"
        )

    async with GenerationService(session) as service:
        try:
            return await service.get_generations(
                skip=skip,
                limit=limit,
                type=type,
                user_id=user_id or current_user.id
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching generations: {str(e)}"
            )


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation(
        generation_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить детальную информацию о генерации"""
    async with GenerationService(session) as service:
        try:
            generation = await service.get_generation(generation_id)
            if not generation:
                raise HTTPException(
                    status_code=404,
                    detail="Generation not found"
                )

            # Проверяем права доступа
            if generation.user_id != current_user.id and current_user.role != "admin":
                raise HTTPException(
                    status_code=403,
                    detail="Not enough permissions to view this generation"
                )

            return generation

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching generation: {str(e)}"
            )


@router.get("/generations/export")
async def export_generations(
        format: str = Query(..., regex="^(csv|json)$"),
        filter: Optional[GenerationFilter] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)  # Только для админов
):
    """Экспорт генераций в CSV или JSON формате"""
    async with GenerationService(session) as service:
        try:
            content = await service.export_generations(format, filter)

            media_type = "text/csv" if format == "csv" else "application/json"
            filename = f"generations_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"

            return StreamingResponse(
                content,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error exporting generations: {str(e)}"
            )


@router.get("/generations/stats")
async def get_generation_stats(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)  # Только для админов
):
    """Получить статистику по генерациям"""
    async with GenerationService(session) as service:
        try:
            if end_date and start_date and end_date < start_date:
                raise HTTPException(
                    status_code=400,
                    detail="End date cannot be earlier than start date"
                )

            return await service.get_statistics(
                start_date=start_date,
                end_date=end_date
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching generation statistics: {str(e)}"
            )