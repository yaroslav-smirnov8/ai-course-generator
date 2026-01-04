from typing import Generator, Any, List
import gc
import weakref
from functools import wraps

class MemoryOptimizer:
    _large_objects = weakref.WeakSet()

    @classmethod
    def register_large_object(cls, obj: Any):
        """Регистрация большого объекта для отслеживания"""
        cls._large_objects.add(obj)

    @classmethod
    def cleanup(cls):
        """Очистка неиспользуемых объектов"""
        gc.collect()

    @staticmethod
    def chunk_generator(data: List[Any], chunk_size: int = 1000) -> Generator:
        """Генератор для обработки больших списков частями"""
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    @staticmethod
    def optimize_dict(data: dict) -> dict:
        """Оптимизация словаря для уменьшения использования памяти"""
        optimized = {}
        for key, value in data.items():
            # Конвертируем строки в bytes для экономии памяти
            if isinstance(value, str) and len(value) > 100:
                optimized[key] = value.encode('utf-8')
            else:
                optimized[key] = value
        return optimized

def memory_optimized(cleanup: bool = True):
    """Декоратор для оптимизации использования памяти"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                # Не регистрируем списки, так как они не поддерживают слабые ссылки
                # Это предотвращает ошибку TypeError: cannot create weak reference to 'list' object
                # Просто вызываем сборщик мусора в конце
                return result
            finally:
                if cleanup:
                    MemoryOptimizer.cleanup()
        return wrapper
    return decorator
