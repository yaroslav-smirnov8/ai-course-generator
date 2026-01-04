# app/models/optimization.py
from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from typing import List, Any, AsyncGenerator, Callable
from ..models import User, Generation
from ..services.optimization import BatchProcessor

# Добавляем индексы для часто используемых полей
Index('idx_user_telegram_id', User.telegram_id)
Index('idx_user_created_at', User.created_at)
Index('idx_user_last_active', User.last_active)
Index('idx_generation_created_at_type', Generation.created_at, Generation.type)


class AsyncBatchProcessor:
    def __init__(self, session: AsyncSession, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size

    async def process_in_batches(
            self,
            query: select,
            processor_func: Callable
    ) -> None:
        """Асинхронная обработка больших наборов данных батчами"""
        offset = 0
        while True:
            # Выполняем запрос с текущим смещением
            result = await self.session.execute(
                query.limit(self.batch_size).offset(offset)
            )
            batch = result.scalars().all()

            if not batch:
                break

            # Обрабатываем батч
            await processor_func(batch)
            offset += self.batch_size

            # Очищаем сессию
            await self.session.expire_all()

    async def process_query_in_chunks(
            self,
            query: select,
            chunk_size: int = 1000
    ) -> AsyncGenerator[List[Any], None]:
        """Асинхронный генератор для обработки запроса чанками"""
        offset = 0
        while True:
            result = await self.session.execute(
                query.limit(chunk_size).offset(offset)
            )
            chunk = result.scalars().all()

            if not chunk:
                break

            yield chunk
            offset += chunk_size

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
        """Разбивает список на чанки для массовой вставки"""
        return [
            items[i:i + chunk_size]
            for i in range(0, len(items), chunk_size)
        ]


# Оптимизированные асинхронные запросы
class OptimizedQueries:
    @staticmethod
    async def get_active_users(session: AsyncSession) -> int:
        """Получает количество активных пользователей за последние 24 часа"""
        query = text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM generations 
            WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
        """)
        result = await session.execute(query)
        return result.scalar()

    @staticmethod
    async def get_generation_stats(
            session: AsyncSession,
            start_date: str
    ) -> List[dict]:
        """Получает статистику генераций"""
        query = text("""
            SELECT 
                type,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_time
            FROM generations 
            WHERE created_at >= :start_date
            GROUP BY type
        """)
        result = await session.execute(query, {"start_date": start_date})
        return [dict(row) for row in result]

    @staticmethod
    async def get_user_activity(session: AsyncSession) -> List[dict]:
        """Получает активность пользователей за текущий день"""
        query = text("""
            WITH daily_stats AS (
                SELECT 
                    user_id,
                    COUNT(*) as generation_count,
                    SUM(CASE WHEN type = 'image' THEN 1 ELSE 0 END) as image_count
                FROM generations
                WHERE created_at >= CURRENT_DATE
                GROUP BY user_id
            )
            SELECT 
                u.id,
                u.telegram_id,
                COALESCE(ds.generation_count, 0) as today_generations,
                COALESCE(ds.image_count, 0) as today_images
            FROM users u
            LEFT JOIN daily_stats ds ON u.id = ds.user_id
            WHERE u.has_access = true
        """)
        result = await session.execute(query)
        return [dict(row) for row in result]

    @staticmethod
    async def get_detailed_user_stats(
            session: AsyncSession,
            user_id: int
    ) -> dict:
        """Получает детальную статистику по пользователю"""
        query = text("""
            WITH user_stats AS (
                SELECT 
                    COUNT(*) as total_generations,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    SUM(CASE WHEN type = 'image' THEN 1 ELSE 0 END) as total_images,
                    MAX(created_at) as last_generation
                FROM generations 
                WHERE user_id = :user_id
            ),
            daily_stats AS (
                SELECT 
                    COUNT(*) as today_generations,
                    SUM(CASE WHEN type = 'image' THEN 1 ELSE 0 END) as today_images
                FROM generations 
                WHERE user_id = :user_id 
                AND DATE(created_at) = CURRENT_DATE
            )
            SELECT 
                us.*, ds.today_generations, ds.today_images,
                u.points, u.tariff, u.has_access
            FROM user_stats us
            CROSS JOIN daily_stats ds
            JOIN users u ON u.id = :user_id
        """)
        result = await session.execute(query, {"user_id": user_id})
        return dict(result.first() or {})


class QueryOptimizer:
    """Класс для оптимизации сложных запросов"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_optimized_query(
            self,
            query: select,
            params: dict = None
    ) -> Any:
        """Выполняет оптимизированный запрос"""
        try:
            result = await self.session.execute(query, params or {})
            return result.scalars().all()
        except Exception as e:
            await self.session.rollback()
            raise e

    async def bulk_insert(
            self,
            items: List[Any],
            chunk_size: int = 1000
    ) -> None:
        """Массовая вставка данных"""
        try:
            for chunk in BatchProcessor.chunk_list(items, chunk_size):
                self.session.add_all(chunk)
                await self.session.flush()
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e

    @staticmethod
    def optimize_query(query: select) -> select:
        """Оптимизирует запрос, добавляя нужные опции"""
        return query.execution_options(
            compiled_cache=True
        ).with_hint(
            selectable=query.froms[0],
            text="ANALYZE",
            dialect_name="postgresql"
        )