import asyncio
import logging
from typing import List, Dict, Any, Callable, Awaitable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Класс для пакетной обработки данных аналитики"""
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 10):
        """
        Инициализация процессора пакетной обработки
        
        Args:
            batch_size: Максимальный размер пакета для обработки
            flush_interval: Интервал принудительной обработки в секундах
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batches: Dict[str, List[Dict[str, Any]]] = {}
        self.last_flush: Dict[str, datetime] = {}
        self.processing_locks: Dict[str, asyncio.Lock] = {}
        self.flush_tasks: Dict[str, asyncio.Task] = {}
    
    def _get_lock(self, batch_key: str) -> asyncio.Lock:
        """
        Получает блокировку для указанного ключа пакета
        
        Args:
            batch_key: Ключ пакета
            
        Returns:
            asyncio.Lock: Объект блокировки
        """
        if batch_key not in self.processing_locks:
            self.processing_locks[batch_key] = asyncio.Lock()
        return self.processing_locks[batch_key]
    
    async def add_item(self, batch_key: str, item: Dict[str, Any], 
                      processor: Callable[[List[Dict[str, Any]]], Awaitable[bool]]) -> None:
        """
        Добавляет элемент в пакет и обрабатывает пакет при необходимости
        
        Args:
            batch_key: Ключ пакета (например, 'feature_usage', 'user_activity')
            item: Элемент для добавления в пакет
            processor: Асинхронная функция для обработки пакета
        """
        async with self._get_lock(batch_key):
            # Инициализируем пакет, если он не существует
            if batch_key not in self.batches:
                self.batches[batch_key] = []
                self.last_flush[batch_key] = datetime.now()
            
            # Добавляем элемент в пакет
            self.batches[batch_key].append(item)
            
            # Проверяем, нужно ли обработать пакет
            current_time = datetime.now()
            time_since_last_flush = (current_time - self.last_flush[batch_key]).total_seconds()
            
            if (len(self.batches[batch_key]) >= self.batch_size or 
                time_since_last_flush >= self.flush_interval):
                await self._process_batch(batch_key, processor)
    
    async def _process_batch(self, batch_key: str, 
                           processor: Callable[[List[Dict[str, Any]]], Awaitable[bool]]) -> None:
        """
        Обрабатывает пакет данных
        
        Args:
            batch_key: Ключ пакета
            processor: Асинхронная функция для обработки пакета
        """
        if not self.batches.get(batch_key):
            return
        
        # Получаем текущий пакет и очищаем очередь
        current_batch = self.batches[batch_key]
        self.batches[batch_key] = []
        self.last_flush[batch_key] = datetime.now()
        
        try:
            batch_size = len(current_batch)
            start_time = datetime.now()
            
            # Обрабатываем пакет
            success = await processor(current_batch)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            if success:
                logger.info(f"Пакет '{batch_key}' успешно обработан: {batch_size} элементов за {processing_time:.2f} сек")
            else:
                logger.error(f"Ошибка при обработке пакета '{batch_key}': {batch_size} элементов")
                # Возвращаем элементы в очередь для повторной обработки
                async with self._get_lock(batch_key):
                    self.batches[batch_key] = current_batch + self.batches[batch_key]
        except Exception as e:
            logger.exception(f"Исключение при обработке пакета '{batch_key}': {str(e)}")
            # Возвращаем элементы в очередь для повторной обработки
            async with self._get_lock(batch_key):
                self.batches[batch_key] = current_batch + self.batches[batch_key]
    
    async def flush_all(self, processors: Dict[str, Callable[[List[Dict[str, Any]]], Awaitable[bool]]]) -> None:
        """
        Принудительно обрабатывает все пакеты
        
        Args:
            processors: Словарь с функциями обработки для каждого ключа пакета
        """
        for batch_key, processor in processors.items():
            if batch_key in self.batches and self.batches[batch_key]:
                async with self._get_lock(batch_key):
                    await self._process_batch(batch_key, processor)
    
    def start_background_flush(self, batch_key: str, 
                              processor: Callable[[List[Dict[str, Any]]], Awaitable[bool]]) -> None:
        """
        Запускает фоновую задачу для периодической обработки пакета
        
        Args:
            batch_key: Ключ пакета
            processor: Асинхронная функция для обработки пакета
        """
        if batch_key in self.flush_tasks and not self.flush_tasks[batch_key].done():
            # Задача уже запущена
            return
        
        async def periodic_flush():
            while True:
                try:
                    await asyncio.sleep(self.flush_interval)
                    async with self._get_lock(batch_key):
                        if batch_key in self.batches and self.batches[batch_key]:
                            await self._process_batch(batch_key, processor)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.exception(f"Ошибка в фоновой задаче обработки пакета '{batch_key}': {str(e)}")
        
        self.flush_tasks[batch_key] = asyncio.create_task(periodic_flush())
        logger.info(f"Запущена фоновая задача обработки пакета '{batch_key}'")
    
    def stop_background_flush(self, batch_key: Optional[str] = None) -> None:
        """
        Останавливает фоновую задачу обработки пакета
        
        Args:
            batch_key: Ключ пакета (если None, останавливаются все задачи)
        """
        if batch_key is not None:
            if batch_key in self.flush_tasks and not self.flush_tasks[batch_key].done():
                self.flush_tasks[batch_key].cancel()
                logger.info(f"Остановлена фоновая задача обработки пакета '{batch_key}'")
        else:
            for key, task in self.flush_tasks.items():
                if not task.done():
                    task.cancel()
            logger.info("Остановлены все фоновые задачи обработки пакетов") 