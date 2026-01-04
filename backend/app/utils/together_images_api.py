"""
Together AI Images API Handler
Модуль для работы с Together AI Images API (Flux Schnell)
"""

import os
import asyncio
import json
import logging
import base64
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Импортируем систему логгирования ключей
try:
    from .api_keys_logger import log_key_usage, log_key_error, log_key_switch
except ImportError:
    # Fallback функции если логгер недоступен
    def log_key_usage(*args, **kwargs):
        pass
    def log_key_error(*args, **kwargs):
        pass
    def log_key_switch(*args, **kwargs):
        pass

# Проверяем доступность Together AI Images API
TOGETHER_IMAGES_AVAILABLE = True

class TogetherImagesAPIException(Exception):
    """Исключение для ошибок Together AI Images API"""
    pass

class TogetherImagesHandler:
    """Обработчик для Together AI Images API (Flux Schnell)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента Together AI Images API

        Args:
            api_key: Ключ API Together AI
        """
        # Получаем API ключ из аргументов или переменной окружения
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY_1")
        
        self.api_url = "https://api.together.xyz/v1/images/generations"
        self.timeout = 120  # Увеличенный таймаут для генерации изображений
        
        # Доступные модели Flux
        self.models = [
            "black-forest-labs/FLUX.1-schnell",  # Бесплатная и быстрая модель
            "black-forest-labs/FLUX.1-dev",     # Более качественная модель
            "black-forest-labs/FLUX.1-pro"      # Профессиональная модель
        ]
        
        # Загружаем API ключи из переменных окружения
        self.api_keys = []
        for i in range(1, 7):  # TOGETHER_API_KEY_1 до TOGETHER_API_KEY_6
            key = os.environ.get(f"TOGETHER_API_KEY_{i}")
            if key and key != 'unused':
                self.api_keys.append(key)
        
        # Добавляем основной ключ если есть
        if self.api_key and self.api_key not in self.api_keys:
            self.api_keys.insert(0, self.api_key)
        
        # Состояние ключей
        self.key_cooldowns = {}  # Кулдауны для ключей
        self.current_key_index = 0
        
        # Директория для сохранения изображений
        self.images_dir = Path("static/generated_images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Инициализация TogetherImagesHandler (доступно ключей: {len(self.api_keys)})")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return len(self.api_keys) > 0

    def get_available_api_key(self) -> Optional[str]:
        """Получает доступный API ключ с учетом кулдаунов"""
        current_time = datetime.now()
        
        # Проверяем все ключи начиная с текущего
        for i in range(len(self.api_keys)):
            key_index = (self.current_key_index + i) % len(self.api_keys)
            api_key = self.api_keys[key_index]
            
            cooldown_end = self.key_cooldowns.get(api_key)
            if not cooldown_end or current_time >= cooldown_end:
                # Логгируем переключение ключа если изменился
                if self.current_key_index != key_index and hasattr(self, '_last_used_key'):
                    log_key_switch(
                        provider="together_images",
                        from_key=self._last_used_key,
                        to_key=api_key,
                        reason="key_rotation",
                        component="together_images_handler"
                    )
                
                self.current_key_index = key_index
                self._last_used_key = api_key
                return api_key
        
        # Если все ключи в кулдауне, используем первый
        logger.warning("Все API ключи Together AI Images в кулдауне, используем первый")
        log_key_error(
            provider="together_images",
            key_id="all_keys",
            error_type="all_keys_in_cooldown",
            error_message="Все API ключи Together AI Images в кулдауне",
            component="together_images_handler"
        )
        self.current_key_index = 0
        return self.api_keys[0]

    def set_key_cooldown(self, api_key: str, minutes: int = 1):
        """Устанавливает кулдаун для ключа"""
        cooldown_end = datetime.now() + timedelta(minutes=minutes)
        self.key_cooldowns[api_key] = cooldown_end
        logger.warning(f"Together AI Images ключ помещен в кулдаун на {minutes} минут")

    async def generate_image(
        self,
        prompt: str,
        model: str = "black-forest-labs/FLUX.1-schnell",
        width: int = 1024,
        height: int = 1024,
        steps: int = 4,
        seed: Optional[int] = None,
        save_locally: bool = True,
        use_worker: bool = True
    ) -> Dict[str, Any]:
        """
        Генерирует изображение с помощью Together AI Flux

        Args:
            prompt: Текстовое описание изображения
            model: Модель для генерации (по умолчанию Flux Schnell)
            width: Ширина изображения
            height: Высота изображения
            steps: Количество шагов генерации
            seed: Сид для воспроизводимости
            save_locally: Сохранять ли изображение локально

        Returns:
            Dict с URL изображения и метаданными
        """
        
        # Засекаем время начала запроса
        start_time = datetime.now()

        # Если используем Worker, вызываем метод для Worker
        if use_worker:
            return await self._generate_image_via_worker(
                prompt=prompt,
                model=model,
                width=width,
                height=height,
                steps=steps,
                seed=seed,
                save_locally=save_locally,
                start_time=start_time
            )

        # Пробуем разные ключи (прямой API)
        max_attempts = min(len(self.api_keys), 3)
        
        for attempt in range(max_attempts):
            api_key = self.get_available_api_key()
            
            try:
                logger.info(f"Together AI Images попытка {attempt + 1}: ключ {self.current_key_index + 1}, модель {model}")
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model,
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "n": 1,  # Количество изображений
                    "response_format": "url"  # Получаем прямые URL вместо base64
                }
                
                if seed is not None:
                    data["seed"] = seed
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.api_url, headers=headers, json=data)
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limit для Together AI Images ключа {self.current_key_index + 1}")
                        
                        # Логгируем rate limit
                        log_key_error(
                            provider="together_images",
                            key_id=api_key,
                            error_type="rate_limit",
                            error_message=f"Rate limit для ключа {self.current_key_index + 1}",
                            component="together_images_handler",
                            will_retry=True,
                            cooldown_minutes=5
                        )
                        
                        self.set_key_cooldown(api_key, 5)
                        continue
                    
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"Together AI Images API error: {response.status_code} {error_text}")
                        
                        # Логгируем API ошибку
                        log_key_error(
                            provider="together_images",
                            key_id=api_key,
                            error_type="api_error",
                            error_message=f"HTTP {response.status_code}: {error_text}",
                            component="together_images_handler",
                            will_retry=response.status_code >= 500
                        )
                        
                        if response.status_code >= 500:
                            self.set_key_cooldown(api_key, 1)
                            continue
                        else:
                            raise TogetherImagesAPIException(f"Together AI Images API error: {response.status_code} {error_text}")
                    
                    result = response.json()
                    
                    if "data" in result and len(result["data"]) > 0:
                        image_data = result["data"][0]
                        
                        # Рассчитываем время ответа
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        # Обрабатываем изображение
                        if "url" in image_data:
                            # Используем прямую ссылку от Together AI (приоритет)
                            image_url = image_data["url"]
                            logger.info(f"Получен прямой URL от Together AI: {image_url[:100]}...")
                        elif save_locally and "b64_json" in image_data:
                            # Fallback: сохраняем изображение локально
                            image_url = await self._save_image_locally(image_data["b64_json"], prompt)
                            logger.info("Сохранено изображение локально (fallback)")
                        else:
                            raise TogetherImagesAPIException("Неожиданная структура ответа от Together AI Images")
                        
                        # Логгируем успешное использование
                        log_key_usage(
                            provider="together_images",
                            key_id=api_key,
                            component="together_images_handler",
                            model=model,
                            success=True,
                            response_time=response_time
                        )
                        
                        return {
                            "url": image_url,
                            "model": model,
                            "provider": "together_images",
                            "width": width,
                            "height": height,
                            "steps": steps,
                            "seed": image_data.get("seed"),
                            "saved_locally": save_locally
                        }
                    else:
                        raise TogetherImagesAPIException("Неожиданная структура ответа от Together AI Images")
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout для Together AI Images ключа {self.current_key_index + 1}")
                
                # Логгируем timeout
                log_key_error(
                    provider="together_images",
                    key_id=api_key,
                    error_type="timeout",
                    error_message="Request timeout",
                    component="together_images_handler",
                    will_retry=True
                )
                
                self.set_key_cooldown(api_key, 2)
                continue
                
            except Exception as e:
                logger.error(f"Неожиданная ошибка Together AI Images: {e}")
                
                # Логгируем неожиданную ошибку
                log_key_error(
                    provider="together_images",
                    key_id=api_key,
                    error_type="unexpected_error",
                    error_message=str(e),
                    component="together_images_handler",
                    will_retry=False
                )
                
                raise TogetherImagesAPIException(f"Неожиданная ошибка: {e}")
        
        # Если все попытки неудачны
        raise TogetherImagesAPIException("Все API ключи Together AI Images недоступны")

    async def _save_image_locally(self, base64_data: str, prompt: str) -> str:
        """Сохраняет изображение локально и возвращает URL"""
        try:
            # Декодируем base64
            image_bytes = base64.b64decode(base64_data)
            
            # Генерируем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_prompt = safe_prompt.replace(' ', '_')
            filename = f"flux_{timestamp}_{safe_prompt}.png"
            
            # Сохраняем файл
            file_path = self.images_dir / filename
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            # Возвращаем полный URL для совместимости с фронтендом
            # Получаем базовый URL из переменных окружения или используем дефолтный
            import os
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            return f"{base_url}/static/generated_images/{filename}"
            
        except Exception as e:
            logger.error(f"Ошибка сохранения изображения: {e}")
            raise TogetherImagesAPIException(f"Ошибка сохранения изображения: {e}")

    async def _generate_image_via_worker(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        steps: int,
        seed: Optional[int],
        save_locally: bool,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Генерирует изображение через Cloudflare Worker"""

        try:
            # URL Netlify функции для Flux Images
            netlify_url = os.environ.get("NETLIFY_FLUX_IMAGES_URL", "https://aiteachers.netlify.app/.netlify/functions/flux-images")
            auth_token = os.environ.get("API_AUTH_TOKEN")

            if not auth_token:
                raise TogetherImagesAPIException("API_AUTH_TOKEN не настроен для Worker")

            # Подготавливаем данные запроса
            request_data = {
                "prompt": prompt,
                "model": model,
                "width": width,
                "height": height,
                "steps": steps
            }

            if seed is not None:
                request_data["seed"] = seed

            # Получаем доступный API ключ Together AI
            api_key = self.get_available_api_key()

            headers = {
                "Content-Type": "application/json",
                "X-Auth-Token": auth_token,
                "X-Component-ID": "flux-images",
                "X-Together-API-Key": api_key  # Добавляем API ключ Together AI
            }

            logger.info(f"Отправляем запрос к Flux Worker: {netlify_url}")
            logger.info(f"Используем Together AI ключ: {api_key[:10]}... (ключ {self.current_key_index + 1}/{len(self.api_keys)})")

            async with httpx.AsyncClient(timeout=180) as client:
                response = await client.post(netlify_url, headers=headers, json=request_data)

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Worker error: {response.status_code} {error_text}")
                    raise TogetherImagesAPIException(f"Worker error: {response.status_code} {error_text}")

                result = response.json()

                if not result.get("success"):
                    raise TogetherImagesAPIException(f"Worker returned error: {result}")

                image_data = result.get("image", {})
                image_url = image_data.get("url")

                if not image_url:
                    raise TogetherImagesAPIException("No image URL in Worker response")

                # Рассчитываем время ответа
                response_time = (datetime.now() - start_time).total_seconds()

                logger.info(f"Получен прямой URL от Together AI через Worker: {image_url[:100]}...")

                # Логгируем успешное использование
                log_key_usage(
                    provider="together_images_worker",
                    key_id="netlify_worker",
                    component="together_images_handler",
                    model=model,
                    success=True,
                    response_time=response_time
                )

                return {
                    "url": image_url,
                    "model": model,
                    "provider": "together_images_worker",
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "seed": image_data.get("seed"),
                    "saved_locally": False,  # Не сохраняем локально, используем прямой URL
                    "worker_version": result.get("worker_version", "1.0.0")
                }

        except Exception as e:
            # Рассчитываем время до ошибки
            response_time = (datetime.now() - start_time).total_seconds()

            # Логгируем ошибку Worker
            log_key_error(
                provider="together_images_worker",
                key_id="netlify_worker",
                error_type="worker_error",
                error_message=str(e),
                component="together_images_handler",
                will_retry=False
            )

            logger.error(f"Worker generation failed: {e}")
            raise TogetherImagesAPIException(f"Worker generation failed: {e}")
