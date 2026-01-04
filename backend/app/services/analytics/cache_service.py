import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta, timezone
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class CacheService:
    """Сервис кэширования для оптимизации аналитики"""

    def __init__(self, default_ttl: int = 3600):
        """
        Инициализация сервиса кэширования

        Args:
            default_ttl: Время жизни кэша по умолчанию в секундах (1 час)
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def _get_lock(self, key: str) -> asyncio.Lock:
        """
        Получает блокировку для указанного ключа

        Args:
            key: Ключ кэша

        Returns:
            asyncio.Lock: Объект блокировки
        """
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        return self.locks[key]

    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Генерирует ключ кэша на основе префикса и параметров

        Args:
            prefix: Префикс ключа
            params: Параметры для включения в ключ

        Returns:
            str: Ключ кэша
        """
        # Сортируем параметры для стабильного хэша
        sorted_params = {k: params[k] for k in sorted(params.keys())}
        params_str = json.dumps(sorted_params, sort_keys=True)

        # Создаем хэш параметров
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        return f"{prefix}:{params_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Получает данные из кэша

        Args:
            key: Ключ кэша

        Returns:
            Optional[Any]: Данные из кэша или None, если кэш отсутствует или устарел
        """
        async with self._get_lock(key):
            if key not in self.cache:
                return None

            cache_entry = self.cache[key]

            # Проверяем, не устарел ли кэш
            if datetime.now(timezone.utc) > cache_entry["expires_at"]:
                del self.cache[key]
                return None

            logger.debug(f"Получены данные из кэша: {key}")
            return cache_entry["data"]

    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        Сохраняет данные в кэш

        Args:
            key: Ключ кэша
            data: Данные для сохранения
            ttl: Время жизни в секундах (если None, используется значение по умолчанию)
        """
        if ttl is None:
            ttl = self.default_ttl

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        async with self._get_lock(key):
            self.cache[key] = {
                "data": data,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            }

            logger.debug(f"Данные сохранены в кэш: {key} (TTL: {ttl} сек)")

    async def invalidate(self, key: str) -> bool:
        """
        Инвалидирует кэш по ключу

        Args:
            key: Ключ кэша

        Returns:
            bool: True, если кэш был инвалидирован, False в противном случае
        """
        async with self._get_lock(key):
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Кэш инвалидирован: {key}")
                return True
            return False

    async def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Инвалидирует все ключи кэша с указанным префиксом

        Args:
            prefix: Префикс ключа

        Returns:
            int: Количество инвалидированных ключей
        """
        keys_to_invalidate = [k for k in self.cache.keys() if k.startswith(prefix)]
        count = 0

        for key in keys_to_invalidate:
            if await self.invalidate(key):
                count += 1

        logger.debug(f"Инвалидировано {count} ключей с префиксом: {prefix}")
        return count

    async def get_or_set(self, key: str, data_func: Callable[[], Any],
                        ttl: Optional[int] = None) -> Any:
        """
        Получает данные из кэша или вызывает функцию для получения данных

        Args:
            key: Ключ кэша
            data_func: Функция для получения данных, если кэш отсутствует
            ttl: Время жизни в секундах

        Returns:
            Any: Данные из кэша или результат вызова функции
        """
        # Пытаемся получить данные из кэша
        cached_data = await self.get(key)
        if cached_data is not None:
            return cached_data

        # Если данных нет в кэше, получаем их с помощью функции
        async with self._get_lock(key):
            # Проверяем еще раз, возможно, данные уже были получены другим потоком
            cached_data = await self.get(key)
            if cached_data is not None:
                return cached_data

            # Получаем данные с помощью функции
            data = await data_func()

            # Сохраняем данные в кэш
            await self.set(key, data, ttl)

            return data

    def cached(self, prefix: str, ttl: Optional[int] = None):
        """
        Декоратор для кэширования результатов функции

        Args:
            prefix: Префикс ключа кэша
            ttl: Время жизни в секундах

        Returns:
            Callable: Декорированная функция
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Создаем словарь параметров для генерации ключа
                params = {}

                # Добавляем позиционные аргументы
                for i, arg in enumerate(args[1:], 1):  # Пропускаем self
                    params[f"arg_{i}"] = arg

                # Добавляем именованные аргументы
                params.update(kwargs)

                # Генерируем ключ кэша
                cache_key = self._generate_key(prefix, params)

                # Используем get_or_set для получения данных
                async def data_func():
                    return await func(*args, **kwargs)

                return await self.get_or_set(cache_key, data_func, ttl)

            return wrapper

        return decorator

    async def start_cleanup_task(self, interval: int = 300) -> None:
        """
        Запускает фоновую задачу для очистки устаревших записей кэша

        Args:
            interval: Интервал очистки в секундах (5 минут по умолчанию)
        """
        if self._cleanup_task and not self._cleanup_task.done():
            return

        async def cleanup_expired():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self.cleanup_expired()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.exception(f"Ошибка при очистке кэша: {str(e)}")

        self._cleanup_task = asyncio.create_task(cleanup_expired())
        logger.info(f"Запущена фоновая задача очистки кэша (интервал: {interval} сек)")

    async def stop_cleanup_task(self) -> None:
        """Останавливает фоновую задачу очистки кэша"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            logger.info("Остановлена фоновая задача очистки кэша")

    async def cleanup_expired(self) -> int:
        """
        Очищает устаревшие записи кэша

        Returns:
            int: Количество очищенных записей
        """
        now = datetime.now(timezone.utc)
        keys_to_remove = []

        # Находим устаревшие записи
        for key, entry in self.cache.items():
            if now > entry["expires_at"]:
                keys_to_remove.append(key)

        # Удаляем устаревшие записи
        for key in keys_to_remove:
            await self.invalidate(key)

        count = len(keys_to_remove)
        if count > 0:
            logger.debug(f"Очищено {count} устаревших записей кэша")

        return count

    async def get_stats(self) -> Dict[str, Any]:
        """
        Получает статистику кэша

        Returns:
            Dict[str, Any]: Статистика кэша
        """
        total_entries = len(self.cache)
        total_size = 0
        expired_entries = 0
        now = datetime.now(timezone.utc)

        # Группировка по префиксам
        prefix_stats: Dict[str, Dict[str, Any]] = {}

        for key, entry in self.cache.items():
            # Определяем префикс (до первого двоеточия)
            prefix = key.split(":")[0] if ":" in key else "other"

            # Инициализируем статистику для префикса, если она еще не существует
            if prefix not in prefix_stats:
                prefix_stats[prefix] = {
                    "count": 0,
                    "expired": 0,
                    "size": 0
                }

            # Увеличиваем счетчики
            prefix_stats[prefix]["count"] += 1

            # Проверяем, устарела ли запись
            if now > entry["expires_at"]:
                expired_entries += 1
                prefix_stats[prefix]["expired"] += 1

            # Оцениваем размер данных (приблизительно)
            try:
                data_size = len(json.dumps(entry["data"]))
                total_size += data_size
                prefix_stats[prefix]["size"] += data_size
            except (TypeError, OverflowError):
                # Если данные не могут быть сериализованы, пропускаем их
                pass

        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "total_size_bytes": total_size,
            "prefix_stats": prefix_stats
        }