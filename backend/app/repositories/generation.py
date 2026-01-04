# repositories/generation.py
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime
from ..models import Generation
from ..core.constants import ContentType

# repositories/generation.py
class GenerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 10,
        type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> tuple[List[Generation], int]:
        # Convert to async query
        query = select(Generation)

        if type:
            query = query.where(Generation.type == type)
        if user_id:
            query = query.where(Generation.user_id == user_id)

        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(query)
        )
        total = count_result.scalar()

        # Get paginated results
        result = await self.session.execute(
            query.order_by(desc(Generation.created_at))
            .offset(skip)
            .limit(limit)
        )
        items = result.scalars().all()

        return items, total

    async def get_by_id(self, generation_id: int) -> Optional[Generation]:
        query = select(Generation).where(Generation.id == generation_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        type: Optional[str] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Generation]:
        query = select(Generation)

        if type:
            query = query.where(Generation.type == type)
        if user_id:
            query = query.where(Generation.user_id == user_id)
        if start_date:
            query = query.where(Generation.created_at >= start_date)
        if end_date:
            query = query.where(Generation.created_at <= end_date)

        result = await self.session.execute(query)
        return result.scalars().all()