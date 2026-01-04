# app/core/optimization.py
from functools import wraps
from typing import Optional, Callable
import asyncio
from contextlib import contextmanager
import time


class RequestOptimizer:
    def __init__(self):
        self._locks = {}
        self._request_counts = {}
        self._last_reset = time.time()

    @contextmanager
    async def throttle(self, key: str, max_concurrent: int = 3):
        """Ограничивает количество одновременных запросов"""
        if key not in self._locks:
            self._locks[key] = asyncio.Semaphore(max_concurrent)

        async with self._locks[key]:
            yield

    def count_requests(self, key: str):
        """Подсчет количества запросов"""
        current_time = time.time()
        if current_time - self._last_reset > 3600:  # Сброс каждый час
            self._request_counts.clear()
            self._last_reset = current_time

        self._request_counts[key] = self._request_counts.get(key, 0) + 1

    @staticmethod
    def optimize_response(response: dict) -> dict:
        """Оптимизирует размер ответа"""
        # Удаляем ненужные поля
        if 'debug_info' in response:
            del response['debug_info']

        # Округляем числовые значения
        for key, value in response.items():
            if isinstance(value, float):
                response[key] = round(value, 2)

        return response


def optimize_request(max_concurrent: Optional[int] = None):
    """Декоратор для оптимизации обработки запросов"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_key = f"{func.__name__}:{args[0] if args else ''}"

            optimizer = RequestOptimizer()
            optimizer.count_requests(request_key)

            if max_concurrent:
                async with optimizer.throttle(request_key, max_concurrent):
                    response = await func(*args, **kwargs)
            else:
                response = await func(*args, **kwargs)

            return optimizer.optimize_response(response)

        return wrapper

    return decorator