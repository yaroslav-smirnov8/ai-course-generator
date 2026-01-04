# app/services/queue/generation_queue.py
from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...schemas.content import GenerationStatus
from ...services.content.generator import ContentGenerator
from .base import QueueItem

logger = logging.getLogger(__name__)


class AsyncGenerationQueue:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[int, QueueItem] = {}
        self.task_counter = 0
        self.max_concurrent_tasks = 3  # Максимум одновременных генераций
        self.active_generations = 0
        self._running = False
        self.session = session
        self.generator = None

        # Статистика для оценки времени
        self.average_generation_time: Dict[str, float] = {
            'lesson_plan': 30,  # секунды
            'exercises': 45,
            'game': 40,
            'image': 20
        }

    async def initialize(self):
        """Инициализация очереди с сессией, если она не была предоставлена в конструкторе"""
        if not self.session:
            self.session = await anext(get_db())

        # Avoid circular import by lazy-loading
        from ...services.content.generator import ContentGenerator
        self.generator = ContentGenerator(self.session)

    async def start(self):
        """Запуск обработчика очереди"""
        if not self._running:
            if not self.session:
                await self.initialize()
            self._running = True
            asyncio.create_task(self._process_queue())

    async def stop(self):
        """Остановка обработчика очереди"""
        self._running = False
        if self.session:
            await self.session.close()

    async def add_to_queue(
            self,
            user_id: int,
            content_type: str,
            prompt: str,
            priority: int = 0
    ) -> int:
        """Добавление задачи в очередь"""
        self.task_counter += 1
        task_id = self.task_counter

        item = QueueItem(
            task_id=task_id,
            user_id=user_id,
            content_type=content_type,
            prompt=prompt,
            priority=priority
        )

        await self.queue.put((-priority, item))
        self.active_tasks[task_id] = item

        logger.info(f"Added task {task_id} to queue for user {user_id}")

        if not self._running:
            await self.start()

        return task_id

    async def get_status(self, task_id: int) -> Dict[str, Any]:
        """Получение статуса задачи"""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")

        item = self.active_tasks[task_id]
        return {
            "status": item.status,
            "created_at": item.created_at,
            "started_at": item.started_at,
            "completed_at": item.completed_at,
            "result": item.result,
            "error": item.error,
            "content_type": item.content_type
        }

    async def get_position(self, task_id: int) -> int:
        """Получение позиции в очереди"""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")

        item = self.active_tasks[task_id]
        if item.status != GenerationStatus.QUEUED:
            return 0

        position = 1
        queue_items = [i for _, i in self.queue._queue]
        for queue_item in queue_items:
            if queue_item.priority > item.priority:
                position += 1
        return position

    async def estimate_wait_time(self, position: int, user_priority: int) -> float:
        """Оценка времени ожидания в секундах"""
        if position == 0:
            return 0

        base_time = self.average_generation_time.get(
            self.active_tasks[position].content_type,
            30
        )

        priority_factor = max(0.5, min(2.0, user_priority / 50))
        concurrent_factor = max(1, self.max_concurrent_tasks / (self.active_generations + 1))

        return base_time * position * priority_factor * concurrent_factor

    async def cancel_task(self, task_id: int) -> bool:
        """Отмена задачи"""
        if task_id not in self.active_tasks:
            return False

        item = self.active_tasks[task_id]
        if item.status != GenerationStatus.QUEUED:
            return False

        self.queue._queue = [
            (p, i) for p, i in self.queue._queue
            if i.task_id != task_id
        ]
        del self.active_tasks[task_id]

        logger.info(f"Cancelled task {task_id}")
        return True

    async def get_queue_info(self) -> Dict[str, Any]:
        """Получение информации о состоянии очереди"""
        queue_size = self.queue.qsize()
        tasks_by_type = {}

        for item in self.active_tasks.values():
            if item.content_type not in tasks_by_type:
                tasks_by_type[item.content_type] = 0
            tasks_by_type[item.content_type] += 1

        return {
            "total_tasks": queue_size,
            "active_generations": self.active_generations,
            "tasks_by_type": tasks_by_type,
            "average_wait_time": await self._calculate_average_wait_time()
        }

    async def get_user_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение задач пользователя"""
        user_tasks = []
        for task_id, item in self.active_tasks.items():
            if item.user_id == user_id:
                user_tasks.append({
                    "task_id": task_id,
                    "status": item.status,
                    "content_type": item.content_type,
                    "created_at": item.created_at
                })
        return user_tasks

    async def check_task_ownership(self, task_id: int, user_id: int) -> bool:
        """Проверка принадлежности задачи пользователю"""
        if task_id not in self.active_tasks:
            return False
        return self.active_tasks[task_id].user_id == user_id

    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Очистка старых задач"""
        current_time = datetime.utcnow()
        tasks_to_remove = []

        for task_id, task in self.active_tasks.items():
            if task.status in [GenerationStatus.COMPLETED, GenerationStatus.ERROR]:
                age = (current_time - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]

    async def _process_queue(self):
        """Обработка очереди"""
        while self._running:
            try:
                if self.active_generations >= self.max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue

                if self.queue.empty():
                    await asyncio.sleep(1)
                    continue

                _, item = await self.queue.get()
                self.active_generations += 1
                item.status = GenerationStatus.GENERATING
                item.started_at = datetime.utcnow()

                try:
                    # Create a new instance to avoid shared state issues
                    generator = None
                    try:
                        from ...services.content.generator import ContentGenerator
                        if not self.session:
                            logger.error("Session is None in _process_queue")
                            item.error = "Database session error"
                            item.status = GenerationStatus.ERROR
                            continue
                            
                        # Создаем новый генератор для каждой задачи
                        generator = ContentGenerator(self.session)
                    except Exception as e:
                        logger.error(f"Error creating generator: {str(e)}")
                        item.error = f"Failed to initialize content generator: {str(e)}"
                        item.status = GenerationStatus.ERROR
                        continue

                    if not generator:
                        logger.error("Failed to create ContentGenerator")
                        item.error = "Failed to initialize content generator"
                        item.status = GenerationStatus.ERROR
                        continue

                    # Проверим, не является ли content_type строкой и преобразуем при необходимости
                    content_type = item.content_type
                    if isinstance(content_type, str):
                        from ...core.constants import ContentType
                        try:
                            content_type = ContentType(content_type)
                        except (ValueError, TypeError):
                            # Если преобразование невозможно, оставляем как есть
                            logger.warning(f"Cannot convert content_type {content_type} to enum")
                            pass

                    # Добавляем таймаут для генерации
                    try:
                        # Создаем задачу с таймаутом
                        timeout_seconds = 280  # немного меньше чем в generator.py (300)
                        generation_task = asyncio.create_task(
                            generator.generate_content(
                                prompt=item.prompt,
                                user_id=item.user_id,
                                content_type=content_type
                            )
                        )
                        
                        # Ждем завершения задачи или таймаута
                        result = await asyncio.wait_for(generation_task, timeout=timeout_seconds)
                        
                        item.result = result
                        item.status = GenerationStatus.COMPLETED
                        
                    except asyncio.TimeoutError:
                        logger.error(f"Generation timeout for task {item.task_id}")
                        item.error = "Generation timeout exceeded"
                        item.status = GenerationStatus.ERROR
                        # Отменяем задачу, если она еще выполняется
                        if not generation_task.done():
                            generation_task.cancel()
                            try:
                                await generation_task
                            except asyncio.CancelledError:
                                pass
                    except Exception as e:
                        item.error = str(e)
                        item.status = GenerationStatus.ERROR
                        logger.error(f"Error processing task {item.task_id}: {str(e)}")

                except Exception as e:
                    item.error = str(e)
                    item.status = GenerationStatus.ERROR
                    logger.error(f"Error processing task {item.task_id}: {str(e)}")

                finally:
                    self.active_generations -= 1
                    item.completed_at = datetime.utcnow()

                    if item.completed_at and item.started_at:
                        generation_time = (
                                item.completed_at - item.started_at
                        ).total_seconds()
                        
                        # Обрабатываем возможное исключение
                        try:
                            await self._update_average_generation_time(
                                item.content_type,
                                generation_time
                            )
                        except Exception as update_err:
                            logger.error(f"Error updating generation time: {str(update_err)}")

                    self.queue.task_done()

            except Exception as e:
                logger.error(f"Error in queue processing: {str(e)}")
                await asyncio.sleep(1)

    async def _update_average_generation_time(self, content_type: str, time: float):
        """Обновление среднего времени генерации"""
        if content_type in self.average_generation_time:
            current_avg = self.average_generation_time[content_type]
            self.average_generation_time[content_type] = (current_avg * 0.9 + time * 0.1)

    async def _calculate_average_wait_time(self) -> float:
        """Расчет среднего времени ожидания"""
        if not self.active_tasks:
            return 0

        completed_tasks = [
            task for task in self.active_tasks.values()
            if task.completed_at and task.created_at
        ]

        if not completed_tasks:
            return 30  # Значение по умолчанию

        total_wait_time = sum(
            (task.completed_at - task.created_at).total_seconds()
            for task in completed_tasks
        )
        return total_wait_time / len(completed_tasks)

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


# For backward compatibility
GenerationQueue = AsyncGenerationQueue