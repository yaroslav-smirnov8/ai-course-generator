# app/core/cache.py

from typing import Optional, Any
import pickle
import json
from datetime import datetime
import aioredis
from .config import settings
import logging

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, session=None):  # Accept optional session parameter and ignore it
        self.redis = None
        self.default_ttl = 3600  # 1 час

    async def init_redis(self):
        """Инициализация Redis соединения"""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
                db=settings.REDIS_DB,
                encoding='utf-8',  # Устанавливаем кодировку
                decode_responses=False  # Отключаем автоматическое декодирование
            )

    async def get_cached_data(self, key: str) -> Optional[Any]:
        """Получение данных из кэша с автоматической десериализацией"""
        try:
            await self.init_redis()
            data = await self.redis.get(key)
            if data:
                try:
                    if isinstance(data, bytes):
                        return pickle.loads(data)
                    return data
                except (pickle.UnpicklingError, json.JSONDecodeError) as e:
                    logger.error(f"Cache deserialization error: {str(e)}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
            return None

    async def cache_data(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Кэширование данных с автоматической сериализацией"""
        try:
            await self.init_redis()

            try:
                # Всегда используем pickle для сериализации
                serialized = pickle.dumps(data)

                await self.redis.set(
                    key,
                    serialized,
                    ex=ttl or self.default_ttl
                )
                return True
            except pickle.PicklingError as e:
                logger.error(f"Cache serialization error: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Инвалидация кэша по паттерну"""
        try:
            await self.init_redis()
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
            return 0

    async def invalidate(self, key: str) -> bool:
        """Инвалидация конкретного ключа в кэше"""
        try:
            await self.init_redis()
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
            return False

    async def close(self):
        """Закрытие соединения с Redis"""
        if self.redis is not None:
            await self.redis.close()
            self.redis = None

    async def __aenter__(self):
        await self.init_redis()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Создаем глобальный экземпляр сервиса
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """Dependency для получения сервиса кэширования"""
    return cache_service