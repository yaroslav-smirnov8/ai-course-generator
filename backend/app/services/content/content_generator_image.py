# app/services/content/content_generator_image.py
"""
Модуль для генерации изображений
"""
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

from ...models import Image
from ...core.memory import memory_optimized
from ...core.constants import ContentType

logger = logging.getLogger(__name__)


class ContentGeneratorImage:
    """
    Миксин для генерации изображений
    """
    
    @memory_optimized()
    async def generate_image(
            self,
            user_id: int,
            prompt: str,
            params: Optional[Dict[str, Any]] = None,
            use_cache: bool = True,
            force_queue: bool = False
    ) -> str:
        """Generate image with optimization"""
        try:
            logger.info("🔄 Attempting to use new ImageGenerationService...")
            
            # Попытка использовать новый ImageGenerationService
            try:
                from .image_generator import ImageGenerationService
                
                # Создаем экземпляр сервиса
                image_service = ImageGenerationService()
                
                # Извлекаем параметры
                with_points = params.get('with_points', False) if params else False
                
                logger.info(f"Generating image with use_cache={use_cache}, with_points={with_points}")
                logger.info(f"Passing params to image generator: {params}")
                
                # Генерируем изображение
                image_url = await image_service.generate_image(
                    prompt=prompt,
                    user_id=user_id,
                    with_points=with_points,
                    use_cache=use_cache
                )
                
                if image_url:
                    logger.info(f"✅ Successfully generated image via ImageGenerationService: {image_url}")
                    return image_url
                else:
                    logger.warning("⚠️ ImageGenerationService returned empty result, falling back to old method")
                    
            except ImportError as e:
                logger.warning(f"⚠️ ImageGenerationService not available: {e}, falling back to old method")
            except Exception as e:
                logger.error(f"❌ Error with ImageGenerationService: {e}, falling back to old method")
            
            # Fallback к старому методу
            logger.info("🔄 Using fallback image generation method...")
            
            # Определяем cache_key независимо от use_cache, используя более стабильный md5 хэш
            cache_key = f"image:{hashlib.md5(prompt.encode()).hexdigest()}"

            # Check cache
            if use_cache:
                cached_image = await self.cache_service.get_cached_data(cache_key)
                if cached_image:
                    return cached_image

            # Generate image through queue
            image_url = await self.generate_content(
                content_type=ContentType.IMAGE,
                prompt=prompt,
                user_id=user_id,
                extra_params=params,
                use_cache=use_cache,
                force_queue=force_queue
            )

            # Save image information
            image = Image(
                user_id=user_id,
                url=image_url,
                prompt=prompt,
                created_at=datetime.utcnow()
            )
            self.session.add(image)
            await self.session.flush()

            # Cache result only if use_cache is True
            if use_cache:
                await self.cache_service.cache_data(cache_key, image_url, ttl=3600)

            return image_url

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise

    async def _generate_with_g4f(self, prompt: str, content_type: ContentType) -> Optional[str]:
        """
        Генерация контента через G4F провайдеры
        """
        try:
            if not self.g4f_handler:
                logger.warning("G4F handler не инициализирован")
                return None

            logger.info(f"Генерация через G4F для типа контента: {content_type}")
            
            # Для изображений используем специальную логику
            if content_type == ContentType.IMAGE:
                logger.info("🖼️ Generating image via G4F...")
                result = await self.g4f_handler.generate_image(prompt)
                if result:
                    logger.info("✅ Successfully generated image via G4F")
                    return result
                else:
                    logger.warning("⚠️ G4F image generation returned empty result")
                    return None
            
            # Для текстового контента
            result = await self.g4f_handler.generate_text(prompt)
            
            if result:
                logger.info(f"Успешно сгенерирован контент через G4F, длина: {len(result)}")
                return result
            else:
                logger.warning("G4F вернул пустой результат")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка генерации через G4F: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _generate_with_queue(
            self,
            user_id: int,
            prompt: str,
            content_type: ContentType
    ) -> Optional[str]:
        """
        Генерация контента через очередь (резервный метод)
        """
        try:
            logger.info("Генерация через очередь...")
            
            # Получаем очередь генерации
            queue = await self.get_generation_queue()
            
            # Получаем приоритет пользователя (с защитой от конфликтов БД)
            try:
                priority = await self._get_user_priority(user_id)
            except Exception as e:
                logger.warning(f"Не удалось получить приоритет пользователя: {e}, используем приоритет по умолчанию")
                priority = 0
            
            # Добавляем задачу в очередь
            task_id = await queue.add_to_queue(
                user_id=user_id,
                content_type=content_type.value if hasattr(content_type, 'value') else str(content_type),
                prompt=prompt,
                priority=priority
            )
            
            logger.info(f"Задача добавлена в очередь с ID: {task_id}")
            
            # Ждем выполнения задачи
            result = await queue.wait_for_result(task_id, timeout=300)  # 5 минут таймаут
            
            if result:
                logger.info(f"Получен результат из очереди, длина: {len(result) if isinstance(result, str) else 'не строка'}")
                return result
            else:
                logger.error("Очередь вернула пустой результат")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка генерации через очередь: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
