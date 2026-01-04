# app/services/optimization/batch_processor.py
from typing import List, Any, Callable, AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import traceback

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, session: AsyncSession, batch_size: int = 1000):
        self.session = session
        self.batch_size = batch_size

    async def process_in_batches(
            self,
            items,
            processor_func: Callable
    ) -> None:
        """Обработка данных батчами"""
        try:
            logger.info(f"Starting batch processing with batch size: {self.batch_size}, items type: {type(items)}, items length: {len(items) if hasattr(items, '__len__') else 'unknown'}")
            
            if self.session and hasattr(items, 'limit'):
                # It's a SQLAlchemy query object
                offset = 0
                while True:
                    result = await self.session.execute(
                        items.limit(self.batch_size).offset(offset)
                    )
                    batch = result.scalars().all()

                    if not batch:
                        logger.info("Empty batch received from SQLAlchemy query, stopping batch processing")
                        break

                    logger.info(f"Processing SQLAlchemy query batch, size: {len(batch)}")
                    try:
                        result = processor_func(batch)
                        logger.info(f"Processor result type: {type(result)}, has __await__: {hasattr(result, '__await__')}, is None: {result is None}")
                        
                        # Проверяем, что результат - awaitable объект и не None, перед await
                        if result is not None and hasattr(result, '__await__'):
                            try:
                                await result
                                logger.info("Successfully awaited processor_func result")
                            except Exception as await_error:
                                logger.error(f"Error while awaiting processor_func result: {str(await_error)}")
                                logger.error(traceback.format_exc())
                                # Продолжаем выполнение, не поднимая исключение выше
                    except Exception as proc_error:
                        logger.error(f"Error in processor_func execution: {str(proc_error)}")
                        logger.error(traceback.format_exc())
                        # Продолжаем выполнение, не поднимая исключение выше
                        
                    offset += self.batch_size
            else:
                # It's a list or other iterable
                if not items or len(items) == 0:
                    logger.info("Empty items list, nothing to process")
                    return
                    
                for i in range(0, len(items), self.batch_size):
                    batch = items[i:i + self.batch_size]
                    if not batch:
                        logger.info(f"Empty batch at index {i}, skipping")
                        continue
                        
                    logger.info(f"Processing list batch {i // self.batch_size + 1}, size: {len(batch)}")
                    try:
                        result = processor_func(batch)
                        logger.info(f"Processor result type: {type(result)}, has __await__: {hasattr(result, '__await__')}, is None: {result is None}")
                        
                        # Проверяем, что результат - awaitable объект и не None, перед await
                        if result is not None and hasattr(result, '__await__'):
                            try:
                                await result
                                logger.info("Successfully awaited processor_func result")
                            except Exception as await_error:
                                logger.error(f"Error while awaiting processor_func result: {str(await_error)}")
                                logger.error(traceback.format_exc())
                                # Продолжаем выполнение, не поднимая исключение выше
                    except Exception as proc_error:
                        logger.error(f"Error in processor_func execution: {str(proc_error)}")
                        logger.error(traceback.format_exc())
                        # Продолжаем выполнение, не поднимая исключение выше

            # Only expire session if it exists
            if self.session is not None:
                try:
                    # Дополнительная проверка, что сессия все еще валидна
                    if hasattr(self.session, 'expire_all'):
                        # expire_all - синхронный метод, просто вызываем его без await
                        self.session.expire_all()
                        logger.info("Successfully expired session")
                    else:
                        logger.warning("Сессия существует, но не имеет метода expire_all()")
                except Exception as expire_error:
                    logger.error(f"Error while expiring session: {str(expire_error)}")
                    logger.error(traceback.format_exc())
            
            logger.info("Batch processing completed successfully")

        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            logger.error(traceback.format_exc())
            # Не поднимаем исключение выше, чтобы не прерывать основной процесс
            # raise

    async def process_query_in_chunks(
            self,
            query: select,
            chunk_size: int = 1000
    ) -> AsyncGenerator[List[Any], None]:
        """Асинхронный генератор для обработки запроса чанками"""
        try:
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

        except Exception as e:
            logger.error(f"Error processing query in chunks: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
        """Разбивает список на чанки для массовой вставки"""
        return [
            items[i:i + chunk_size]
            for i in range(0, len(items), chunk_size)
        ]

    async def bulk_insert(
            self,
            items: List[Any],
            chunk_size: int = 1000
    ) -> None:
        """Массовая вставка данных с обработкой по чанкам"""
        try:
            for chunk in self.chunk_list(items, chunk_size):
                self.session.add_all(chunk)
                await self.session.flush()
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error during bulk insert: {str(e)}")
            logger.error(traceback.format_exc())
            await self.session.rollback()
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()