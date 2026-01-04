from typing import List, Any, Callable, Awaitable, Optional
from log import logger

class BatchProcessor:
    def __init__(self, batch_size: int):
        self.batch_size = batch_size

    async def process_in_batches(
            self,
            data: List[Any],
            process_func: Callable[[List[Any]], Awaitable[None]],
            batch_size: Optional[int] = None
    ) -> None:
        """Process items in batches using the given function."""
        try:
            # Проверка на None и пустые значения
            if data is None:
                logger.error("Data is None in process_in_batches")
                return
                
            if not data:
                logger.debug("Empty data list provided to process_in_batches")
                return

            if process_func is None:
                logger.error("Process function is None in process_in_batches")
                return

            # Используем размер батча из параметров или из конфига
            effective_batch_size = batch_size or self.batch_size
            
            # Разбиваем данные на батчи
            for i in range(0, len(data), effective_batch_size):
                batch = data[i:i + effective_batch_size]
                try:
                    # Выполняем функцию обработки для текущего батча
                    await process_func(batch)
                except Exception as e:
                    logger.error(f"Error processing batch {i//effective_batch_size + 1}: {str(e)}")
                    # Продолжаем с следующим батчем вместо остановки всего процесса
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}") 