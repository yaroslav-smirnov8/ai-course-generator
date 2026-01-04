# services/generations/manager.py
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import pandas as pd
import io
import logging
from typing import Optional, Dict, Any
from ...repositories import GenerationRepository
from ...schemas.generations import GenerationFilter
from ...services.optimization.batch_processor import BatchProcessor
from ...core.memory import memory_optimized

logger = logging.getLogger(__name__)

class GenerationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = GenerationRepository(session)
        self.batch_processor = BatchProcessor(session)

    @memory_optimized()
    async def get_generations(
        self,
        skip: int = 0,
        limit: int = 10,
        type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Получение списка генераций с пагинацией"""
        try:
            items, total = await self.repository.get_paginated(
                skip=skip,
                limit=limit,
                type=type,
                user_id=user_id
            )
            return {
                "items": items,
                "total": total
            }
        except Exception as e:
            logger.error(f"Error getting generations: {str(e)}")
            raise

    async def get_generation(self, generation_id: int):
        """Получение конкретной генерации по ID"""
        try:
            return await self.repository.get_by_id(generation_id)
        except Exception as e:
            logger.error(f"Error getting generation {generation_id}: {str(e)}")
            raise

    @memory_optimized()
    async def export_generations(
        self,
        format: str,
        filter: Optional[GenerationFilter] = None
    ) -> StreamingResponse:
        """Экспорт генераций в CSV или другой формат"""
        try:
            generations = await self.repository.get_filtered(
                type=filter.type if filter else None,
                user_id=filter.user_id if filter else None,
                start_date=filter.start_date if filter else None,
                end_date=filter.end_date if filter else None
            )

            if format == "csv":
                # Обрабатываем данные батчами для оптимизации памяти
                data = []
                async def process_batch(batch):
                    for g in batch:
                        data.append({
                            'id': g.id,
                            'user_id': g.user_id,
                            'type': g.type.value,
                            'content': g.content,
                            'prompt': g.prompt,
                            'created_at': g.created_at
                        })

                await self.batch_processor.process_in_batches(generations, process_batch)

                df = pd.DataFrame(data)
                output = io.StringIO()
                df.to_csv(output, index=False)

                response = StreamingResponse(
                    iter([output.getvalue()]),
                    media_type="text/csv"
                )
                response.headers["Content-Disposition"] = \
                    f"attachment; filename=generations_{datetime.utcnow().date()}.csv"
                return response

            return [g.__dict__ for g in generations]

        except Exception as e:
            logger.error(f"Error exporting generations: {str(e)}")
            raise

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получение статистики по генерациям"""
        try:
            return await self.repository.get_stats(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Error getting generation statistics: {str(e)}")
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()