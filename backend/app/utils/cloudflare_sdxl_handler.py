"""
Cloudflare AI SDXL Handler
Модуль для работы с Cloudflare Workers AI (Stable Diffusion XL)
"""

import os
import asyncio
import json
import logging
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import httpx

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

# Проверяем доступность Cloudflare AI
CLOUDFLARE_AI_AVAILABLE = True


class CloudflareSDXLException(Exception):
    """Исключение для ошибок Cloudflare AI SDXL API"""
    pass


class CloudflareSDXLHandler:
    """Обработчик для Cloudflare AI Workers (Stable Diffusion XL)"""

    def __init__(self):
        """
        Инициализация клиента Cloudflare AI SDXL
        """
        # Получаем учетные данные из переменных окружения
        self.account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
        
        # API endpoint для Stable Diffusion XL
        if self.account_id and self.api_token:
            self.api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
        else:
            self.api_url = None
        
        self.timeout = 120  # Таймаут для генерации изображений
        
        # Модель по умолчанию
        self.model = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        
        # Состояние ключей (для совместимости с api_keys_logger)
        self.current_key_index = 0
        self.current_key_id = f"{self.account_id[:8]}..." if self.account_id else "none"
        self._last_used_key = self.current_key_id
        
        # Директория для сохранения изображений
        self.images_dir = Path("static/generated_images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Инициализация CloudflareSDXLHandler (Account ID: {'SET' if self.account_id else 'NOT SET'}, API Token: {'SET' if self.api_token else 'NOT SET'})")

    def is_available(self) -> bool:
        """Проверка доступности API"""
        available = bool(self.account_id and self.api_token)
        logger.debug(f"Cloudflare SDXL is_available: {available}")
        return available

    def translate_prompt_to_english(self, prompt: str) -> str:
        """
        Переводит промпт на английский используя доступный LLM обработчик
        
        Args:
            prompt: Текстовый промпт для генерации
            
        Returns:
            Английский промпт или оригинал если он уже на английском
        """
        # Простая проверка на английский язык
        if self._is_english(prompt):
            return prompt

        try:
            # Используем LLM7 для перевода
            from .gemini_api import GeminiHandler
            gemini_handler = GeminiHandler()
            
            if gemini_handler.is_available():
                translate_prompt = f"""You are a professional translator specializing in image generation prompts.
Translate the following text to English, preserving the artistic and descriptive intent for image generation.
Keep technical terms, artistic styles, and descriptive elements intact.
Return ONLY the translated text without any additional comments or explanations.

Text to translate: {prompt}"""

                translated = gemini_handler.generate_content_sync(
                    translate_prompt,
                    model="gemini-2.0-flash-exp",
                    temperature=0.3
                )

                if translated and translated.strip():
                    logger.info(f"Translated prompt: {prompt[:50]}... -> {translated[:50]}...")
                    return translated.strip()

            logger.warning("LLM unavailable for translation, using original prompt")
            return prompt

        except Exception as e:
            logger.error(f"Error translating prompt: {e}")
            return prompt

    def _is_english(self, text: str) -> bool:
        """Простая проверка на английский язык"""
        if not text:
            return True

        # Проверяем наличие кириллицы или других не-латинских символов
        non_latin_chars = sum(1 for char in text if ord(char) > 127)
        return non_latin_chars / len(text) < 0.1  # Менее 10% не-латинских символов

    def enhance_prompt_for_quality(self, prompt: str) -> str:
        """
        Улучшает промпт для лучшего качества SDXL изображений.
        Добавляет дескрипторы качества для лучших результатов.
        
        Args:
            prompt: Исходный промпт
            
        Returns:
            Улучшенный промпт
        """
        # Дескрипторы качества для SDXL
        quality_enhancers = [
            "high quality",
            "detailed",
            "sharp focus",
            "professional",
            "well composed",
            "clear",
            "realistic proportions",
            "good lighting"
        ]

        # Проверяем, есть ли уже дескрипторы качества
        prompt_lower = prompt.lower()
        has_quality_terms = any(
            term in prompt_lower 
            for term in ["high quality", "detailed", "sharp", "professional", "realistic", "clear"]
        )

        if not has_quality_terms:
            # Добавляем дескрипторы качества в конец промпта
            enhanced_prompt = f"{prompt}, {', '.join(quality_enhancers[:4])}"
            logger.info(f"Prompt enhanced for quality: {enhanced_prompt[:100]}...")
            return enhanced_prompt

        return prompt

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = 20,
        seed: Optional[int] = None,
        save_locally: bool = True,
        use_worker: bool = False
    ) -> Dict[str, Any]:
        """
        Генерирует изображение с помощью Cloudflare AI SDXL

        Args:
            prompt: Текстовое описание изображения
            width: Ширина изображения
            height: Высота изображения
            steps: Количество шагов генерации
            seed: Сид для воспроизводимости
            save_locally: Сохранять ли изображение локально
            use_worker: Использовать ли Worker (Cloudflare не требует Worker)

        Returns:
            Dict с URL изображения и метаданными
        """
        
        # Засекаем время начала запроса
        start_time = datetime.now()

        if not self.is_available():
            raise CloudflareSDXLException("Cloudflare AI SDXL unavailable - missing API credentials")

        # Переводим промпт на английский
        english_prompt = self.translate_prompt_to_english(prompt)

        # Улучшаем промпт для лучшего качества
        enhanced_prompt = self.enhance_prompt_for_quality(english_prompt)
        logger.info(f"Generating image with Cloudflare SDXL: {enhanced_prompt[:100]}...")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            # Формат запроса Cloudflare SDXL
            # SDXL лучше всего работает с квадратными изображениями и определенными размерами
            request_data = {
                "prompt": enhanced_prompt,
                "num_steps": steps or 20,
                "width": width,
                "height": height,
                "guidance_scale": 7.5
            }

            if seed is not None:
                request_data["seed"] = seed

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_data
                )

                logger.info(f"Cloudflare API Response Status: {response.status_code}")
                logger.debug(f"Cloudflare API Response Headers: {dict(response.headers)}")

                if response.status_code == 200:
                    import io
                    from PIL import Image as PILImage
                    
                    # Cloudflare может вернуть:
                    # 1. Двоичные данные изображения (PNG)
                    # 2. JSON с base64-кодированным изображением
                    try:
                        result = response.json()
                        # Формат ответа JSON
                        if result.get("success") and result.get("result"):
                            image_data = result["result"]["image"]
                            image_bytes = base64.b64decode(image_data)
                            logger.info("Received JSON response with base64 image from Cloudflare AI")
                        else:
                            error_msg = result.get("errors", [{"message": "Unknown error"}])[0].get("message", "Unknown error")
                            raise CloudflareSDXLException(f"Cloudflare AI error: {error_msg}")
                    except Exception:
                        # Пытаемся распарсить как двичные данные изображения
                        content_type = response.headers.get('Content-Type', '')
                        if 'image' in content_type or response.content.startswith(b'\x89PNG'):
                            logger.info("Received direct binary image from Cloudflare AI")
                            image_bytes = response.content
                        else:
                            raise CloudflareSDXLException(f"Unexpected response format. Content-Type: {content_type}")

                    # Открываем и сохраняем изображение
                    image = PILImage.open(io.BytesIO(image_bytes))

                    if save_locally:
                        # Сохраняем в папку images
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_prompt = safe_prompt.replace(' ', '_')
                        filename = f"sdxl_{timestamp}_{safe_prompt}.png"
                        filepath = self.images_dir / filename
                        image.save(filepath)
                        
                        # Возвращаем полный URL для совместимости с фронтендом
                        base_url = os.getenv('BASE_URL', 'http://localhost:8000')
                        image_url = f"{base_url}/static/generated_images/{filename}"
                        saved_locally = True
                        logger.info(f"Saved image locally: {filepath}")
                    else:
                        # Возвращаем base64-encoded изображение
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        image_url = f"data:image/png;base64,{image_base64}"
                        saved_locally = False

                    # Рассчитываем время ответа
                    response_time = (datetime.now() - start_time).total_seconds()

                    # Логгируем успешное использование
                    log_key_usage(
                        provider="cloudflare_sdxl",
                        key_id=self.current_key_id,
                        component="cloudflare_sdxl_handler",
                        model=self.model,
                        success=True,
                        response_time=response_time
                    )

                    logger.info(f"Successfully generated image via Cloudflare SDXL: {image_url}")

                    return {
                        "url": image_url,
                        "model": self.model,
                        "provider": "cloudflare_sdxl",
                        "width": width,
                        "height": height,
                        "steps": steps or 20,
                        "seed": seed,
                        "saved_locally": saved_locally,
                        "response_time": response_time,
                        "prompt": enhanced_prompt
                    }

                else:
                    error_text = response.text
                    logger.error(f"Cloudflare AI error: {response.status_code} {error_text}")
                    
                    # Логгируем ошибку
                    error_type = self._classify_error(response.status_code)
                    log_key_error(
                        provider="cloudflare_sdxl",
                        key_id=self.current_key_id,
                        error_type=error_type,
                        error_message=f"HTTP {response.status_code}: {error_text}",
                        component="cloudflare_sdxl_handler",
                        will_retry=response.status_code >= 500 or response.status_code == 429
                    )
                    
                    raise CloudflareSDXLException(f"Cloudflare AI error: {response.status_code} {error_text}")

        except httpx.TimeoutException:
            # Таймаут запроса
            log_key_error(
                provider="cloudflare_sdxl",
                key_id=self.current_key_id,
                error_type="timeout",
                error_message="Request timeout",
                component="cloudflare_sdxl_handler",
                will_retry=True
            )
            
            logger.error(f"Timeout generating image with Cloudflare SDXL")
            raise CloudflareSDXLException("Timeout generating image with Cloudflare SDXL")
            
        except CloudflareSDXLException:
            # Перебрасываем наши исключения
            raise
            
        except Exception as e:
            # Логгируем неожиданную ошибку
            log_key_error(
                provider="cloudflare_sdxl",
                key_id=self.current_key_id,
                error_type="unexpected_error",
                error_message=str(e),
                component="cloudflare_sdxl_handler",
                will_retry=False
            )
            
            logger.error(f"Error generating image with Cloudflare SDXL: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise CloudflareSDXLException(f"Error generating image with Cloudflare SDXL: {e}")

    def _classify_error(self, status_code: int) -> str:
        """Классифицирует ошибку по статус коду"""
        if status_code == 401:
            return "unauthorized"
        elif status_code == 404:
            return "not_found"
        elif status_code == 429:
            return "rate_limit"
        elif status_code >= 500:
            return "server_error"
        else:
            return "api_error"


# Глобальный экземпляр обработчика
try:
    cloudflare_sdxl_handler = CloudflareSDXLHandler()
    logger.info("✅ CloudflareSDXLHandler successfully initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize CloudflareSDXLHandler: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    cloudflare_sdxl_handler = None
    CLOUDFLARE_AI_AVAILABLE = False


# Helper функции для совместимости с другими модулями
async def generate_image(prompt: str, **kwargs) -> Dict[str, Any]:
    """Асинхронная генерация изображения"""
    if cloudflare_sdxl_handler and cloudflare_sdxl_handler.is_available():
        return await cloudflare_sdxl_handler.generate_image(prompt, **kwargs)
    raise CloudflareSDXLException("Cloudflare SDXL handler not available")


def generate_image_sync(prompt: str, **kwargs) -> Dict[str, Any]:
    """Синхронная генерация изображения"""
    import asyncio
    if cloudflare_sdxl_handler and cloudflare_sdxl_handler.is_available():
        return asyncio.run(cloudflare_sdxl_handler.generate_image(prompt, **kwargs))
    raise CloudflareSDXLException("Cloudflare SDXL handler not available")