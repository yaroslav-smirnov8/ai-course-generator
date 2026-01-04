# app/services/content/content_generator_core.py
"""
Основной класс ContentGenerator с базовой функциональностью
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List, Union
import logging
from datetime import datetime, timedelta, timezone
import asyncio
import time
import re
import hashlib
import json
import os

from ...models import Generation, User, Course, Lesson, Image, VideoTranscript
from ...core.exceptions import ValidationError
from ...core.constants import ContentType
from ...services.optimization.query_optimizer import QueryOptimizer
from ...services.optimization.batch_processor import BatchProcessor
from ...core.cache import CacheService
from ...core.memory import memory_optimized

# Импорты для компонентов
from .content_generator_providers import ContentGeneratorProviders
from .content_generator_image import ContentGeneratorImage
from .content_generator_lesson import ContentGeneratorLesson
from .content_generator_text import ContentGeneratorText
from .content_generator_course import ContentGeneratorCourse
from .content_generator_game import ContentGeneratorGame

# Импорты для API Gateway
from ..api_gateway import APIGateway
from ..api_gateway.models import ContentType as GatewayContentType, APIRequest

logger = logging.getLogger(__name__)


class ContentGenerator(
    ContentGeneratorProviders,
    ContentGeneratorImage,
    ContentGeneratorLesson,
    ContentGeneratorText,
    ContentGeneratorCourse,
    ContentGeneratorGame
):
    """
    Основной класс для генерации контента с поддержкой множественных AI провайдеров
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.cache_service = CacheService()
        self.batch_processor = BatchProcessor(session)
        # Initialize queue to None - we'll create it when needed
        self._generation_queue = None

        # Инициализируем API Gateway
        self.api_gateway = APIGateway()

        # Инициализируем провайдеры (для обратной совместимости)
        super().__init__()

    def _get_api_keys(self) -> Dict[str, str]:
        """Получить API ключи для всех провайдеров из .env"""
        api_keys = {}

        # Получаем ключи из переменных окружения (приоритет)
        api_keys.update({
            'gemini': os.getenv('GEMINI_API_KEY', ''),
            'groq': os.getenv('GROQ_API_KEY', ''),
            'openrouter': os.getenv('OPENROUTER_API_KEY', ''),
            'llm7': os.getenv('LLM7_API_KEY', ''),
            'together': os.getenv('TOGETHER_API_KEY', ''),
            'cerebras': os.getenv('CEREBRAS_API_KEY', ''),
            'chutes': os.getenv('CHUTES_API_KEY', ''),
            'mistral': os.getenv('MISTRAL_API_KEY', '')
        })

        # Fallback на handlers если они есть
        if hasattr(self, 'gemini_handler') and self.gemini_handler and not api_keys.get('gemini'):
            api_keys['gemini'] = getattr(self.gemini_handler, 'api_key', '')

        if hasattr(self, 'groq_handler') and self.groq_handler and not api_keys.get('groq'):
            api_keys['groq'] = getattr(self.groq_handler, 'api_key', '')

        if hasattr(self, 'openrouter_handler') and self.openrouter_handler and not api_keys.get('openrouter'):
            api_keys['openrouter'] = getattr(self.openrouter_handler, 'api_key', '')

        if hasattr(self, 'llm7_handler') and self.llm7_handler and not api_keys.get('llm7'):
            api_keys['llm7'] = getattr(self.llm7_handler, 'api_key', '')

        if hasattr(self, 'together_handler') and self.together_handler and not api_keys.get('together'):
            api_keys['together'] = getattr(self.together_handler, 'api_key', '')

        if hasattr(self, 'cerebras_handler') and self.cerebras_handler and not api_keys.get('cerebras'):
            api_keys['cerebras'] = getattr(self.cerebras_handler, 'api_key', '')

        # Фильтруем пустые ключи
        return {k: v for k, v in api_keys.items() if v}

    def _map_content_type(self, content_type) -> GatewayContentType:
        """Маппинг типов контента для API Gateway"""
        # Проверяем по строковому значению для совместимости
        if hasattr(content_type, 'value'):
            content_str = content_type.value
        else:
            content_str = str(content_type).lower()

        if 'image' in content_str:
            return GatewayContentType.IMAGE
        else:
            return GatewayContentType.TEXT

    def _get_endpoint_for_content_type(self, content_type) -> str:
        """Получить эндпоинт для типа контента"""
        # Проверяем по строковому значению для совместимости
        if hasattr(content_type, 'value'):
            content_str = content_type.value
        else:
            content_str = str(content_type).lower()

        # Маппинг по строковым значениям
        if 'lesson' in content_str or 'plan' in content_str:
            return 'lesson-plan'
        elif 'exercise' in content_str:
            return 'exercises'
        elif 'game' in content_str:
            return 'games'
        elif 'course' in content_str:
            return 'course-generator'
        elif 'analysis' in content_str or 'analyzer' in content_str:
            return 'text-analyzer'
        elif 'concept' in content_str or 'explanation' in content_str:
            return 'concept-explainer'
        elif 'image' in content_str:
            return 'flux-images'
        else:
            return 'assistant'

    async def generate_content_via_gateway(
        self,
        prompt: str,
        content_type: ContentType,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Генерация контента через API Gateway (новый метод)

        Args:
            prompt: Промпт для генерации
            content_type: Тип контента
            preferred_provider: Предпочтительный провайдер
            preferred_model: Предпочтительная модель
            extra_params: Дополнительные параметры

        Returns:
            str: Сгенерированный контент
        """
        try:
            # Получаем API ключи
            api_keys = self._get_api_keys()

            if not api_keys:
                logger.warning("Нет доступных API ключей для генерации")
                return "Ошибка: API ключи недоступны"

            # Маппим тип контента
            gateway_content_type = self._map_content_type(content_type)
            endpoint = self._get_endpoint_for_content_type(content_type)

            # Подготавливаем данные для запроса
            request_data = {
                'prompt': prompt,
                'temperature': 0.7,
                'maxTokens': 4000
            }

            # Добавляем дополнительные параметры
            if extra_params:
                request_data.update(extra_params)

            logger.info(f"Генерация через API Gateway: {endpoint} ({gateway_content_type.value})")

            # Вызываем API Gateway
            response = await self.api_gateway.generate_content(
                endpoint=endpoint,
                data=request_data,
                api_keys=api_keys,
                content_type=gateway_content_type,
                preferred_provider=preferred_provider,
                preferred_model=preferred_model
            )

            if response.success:
                logger.info(f"Успешная генерация через {response.provider_name}/{response.model_name}")

                # Для изображений возвращаем URL
                if gateway_content_type == GatewayContentType.IMAGE:
                    return response.image_url or response.content
                else:
                    return response.content
            else:
                logger.error(f"Ошибка генерации через API Gateway: {response.error}")
                return f"Ошибка генерации: {response.error}"

        except Exception as e:
            logger.error(f"Критическая ошибка в generate_content_via_gateway: {e}")
            return f"Критическая ошибка генерации: {str(e)}"

    async def _generate_with_g4f(self, prompt: str, content_type: ContentType, with_points: bool = False) -> Optional[str]:
        """
        Генерирует контент с использованием доступных провайдеров
        в порядке приоритета: LLM7 -> Gemini -> OpenRouter -> Groq -> Together -> Cerebras -> Chutes -> Mistral -> G4F

        Args:
            prompt: Текст промпта для генерации
            content_type: Тип контента
            with_points: Флаг использования баллов (влияет на определение токенов)

        Returns:
            Optional[str]: Сгенерированный текст или None в случае ошибки
        """
        try:
            # Определяем параметры генерации в зависимости от типа контента и специфики запроса
            temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7

            # Умное определение токенов в зависимости от типа запроса
            max_tokens = self._get_smart_token_count(content_type, prompt, with_points)

            logger.info(f"Параметры генерации: temperature={temperature}, max_tokens={max_tokens}, content_type={content_type}, with_points={with_points}")

            # Для изображений используем специальный метод
            if content_type == ContentType.IMAGE:
                logger.info("Генерация изображения через G4F handler")
                if self.g4f_handler:
                    image_url = await self.g4f_handler.generate_image(prompt)
                    return image_url
                else:
                    logger.error("G4FHandler не инициализирован для генерации изображений")
                    return None

            # Для текстового контента используем приоритет провайдеров

            # 1. Пробуем LLM7 API (основной провайдер)
            if hasattr(self, 'llm7_handler') and self.llm7_handler:
                try:
                    logger.info("Генерация контента через LLM7 API (primary)")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    model_override = os.getenv('LLM7_DEFAULT_MODEL', 'default')
                    generated_content = await self.llm7_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        model=model_override
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через LLM7 API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("LLM7 API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка LLM7 API: {str(e)}")

            # 2. Пробуем Gemini API
            if hasattr(self, 'gemini_handler') and self.gemini_handler:
                try:
                    # Устанавливаем правильный component_id на основе content_type
                    from ...utils.component_mapping import get_gemini_component_id
                    correct_component_id = get_gemini_component_id(content_type)
                    self.gemini_handler.component_id = correct_component_id
                    
                    logger.info(f"Генерация контента через Gemini API")
                    logger.info(f"Content type: {content_type}, Component ID: {correct_component_id}")
                    # Используем параметры как в боте
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.gemini_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через Gemini API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("Gemini API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка Gemini API: {str(e)}")

            # 2. Пробуем OpenRouter API
            if hasattr(self, 'openrouter_handler') and self.openrouter_handler:
                try:
                    logger.info(f"Генерация контента через OpenRouter API")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.openrouter_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через OpenRouter API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("OpenRouter API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка OpenRouter API: {str(e)}")

            # 2. Пробуем Groq API
            if hasattr(self, 'groq_handler') and self.groq_handler:
                try:
                    # Устанавливаем правильный component_id для Groq
                    from ...utils.component_mapping import get_groq_component_id
                    correct_component_id = get_groq_component_id(content_type)
                    self.groq_handler.component_id = correct_component_id
                    
                    logger.info(f"Генерация контента через Groq API")
                    logger.info(f"Content type: {content_type}, Component ID: {correct_component_id}")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.groq_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через Groq API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("Groq API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка Groq API: {str(e)}")


            # 5. Пробуем Together API
            if hasattr(self, 'together_handler') and self.together_handler:
                try:
                    logger.info(f"Генерация контента через Together API")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.together_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через Together API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("Together API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка Together API: {str(e)}")

            # 6. Пробуем Cerebras API
            if hasattr(self, 'cerebras_handler') and self.cerebras_handler:
                try:
                    logger.info(f"Генерация контента через Cerebras API")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.cerebras_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через Cerebras API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("Cerebras API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка Cerebras API: {str(e)}")

            # 7. Пробуем Chutes API
            if hasattr(self, 'chutes_handler') and self.chutes_handler:
                try:
                    logger.info(f"Генерация контента через Chutes API")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.chutes_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через Chutes API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("Chutes API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка Chutes API: {str(e)}")

            # 8. Пробуем Mistral API
            if hasattr(self, 'mistral_handler') and self.mistral_handler:
                try:
                    logger.info(f"Генерация контента через Mistral API")
                    temperature = 0.8 if content_type in [ContentType.LESSON_PLAN, ContentType.EXERCISE, ContentType.GAME] else 0.7
                    generated_content = await self.mistral_handler.generate_content(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens  # Динамически как в боте
                    )
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через Mistral API, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("Mistral API вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка Mistral API: {str(e)}")

            # 9. Последний fallback - G4F
            if self.g4f_handler:
                try:
                    logger.info(f"Генерация контента через G4F (последний fallback)")
                    generated_content = await self.g4f_handler.generate_content(prompt)
                    if generated_content:
                        logger.info(f"✅ Контент сгенерирован через G4F, длина: {len(generated_content)}")
                        return generated_content
                    else:
                        logger.warning("G4F вернул пустой ответ")
                except Exception as e:
                    logger.error(f"Ошибка G4F: {str(e)}")

            logger.error("Все провайдеры генерации контента недоступны или вернули ошибки")
            return None

        except Exception as e:
            logger.error(f"Критическая ошибка в _generate_with_g4f: {str(e)}")
            return None

    def _get_smart_token_count(self, content_type: ContentType, prompt: str, with_points: bool = False) -> int:
        """
        Умное определение количества токенов в зависимости от типа контента и специфики запроса

        Args:
            content_type: Тип контента
            prompt: Текст промпта для анализа

        Returns:
            int: Количество токенов для генерации
        """
        # Анализируем промпт для определения специфики запроса
        prompt_lower = prompt.lower()

        # Анализируем JSON данные из промпта для более точного определения
        is_regeneration = False
        is_single_exercise = False

        try:
            # Используем переданный флаг with_points
            is_with_points = with_points

            # Проверяем данные формы для определения типа запроса
            if any(keyword in prompt_lower for keyword in ['regenerate', 'обновить', 'перегенерируй']):
                is_regeneration = True

            # Проверяем, это перегенерация одного упражнения
            if any(keyword in prompt_lower for keyword in ['упражнение №', 'exercise_index', 'single_exercise']):
                is_single_exercise = True

        except Exception as e:
            logger.debug(f"Ошибка при анализе JSON в промпте: {e}")

        # Ключевые слова для детализации планов уроков
        lesson_detail_keywords = [
            'детализируй', 'детализация', 'подробнее', 'расширь', 'дополни',
            'перепиши', 'перегенерируй', 'переделай', 'улучши',
            'скрипт учителя', 'инструкции для учителя', 'методические указания',
            'домашнее задание', 'дз для студентов', 'homework',
            'пункт плана', 'раздел плана', 'часть урока'
        ]

        # Проверяем, является ли это детализацией плана урока
        is_lesson_detail = any(keyword in prompt_lower for keyword in lesson_detail_keywords)

        if content_type == ContentType.LESSON_PLAN:
            if is_lesson_detail:
                # Детализация планов - меньше токенов
                max_tokens = 6000  # Вместо 17000 для основных планов
                request_type = "детализация плана"
            else:
                # Основные планы уроков - увеличено до 17000 токенов
                max_tokens = 17000
                request_type = "основной план"

        elif content_type == ContentType.EXERCISE:
            if is_single_exercise:
                # Перегенерация одного упражнения (кнопка 🔄 на карточке)
                max_tokens = 4000
                request_type = "одно упражнение"
            elif is_regeneration or is_with_points:
                # Перегенерация всех упражнений (кнопки 🔄 Обновить все / 💎 За баллы)
                max_tokens = 8000
                request_type = "перегенерация упражнений"
            else:
                # Основные упражнения - как в боте (кнопка Сгенерировать упражнения)
                max_tokens = 12000
                request_type = "основные упражнения"

        elif content_type == ContentType.GAME:
            if is_regeneration or is_with_points:
                # Перегенерация игры (кнопки 💎 За баллы / GameTypeSelector)
                max_tokens = 7000
                request_type = "перегенерация игры"
            else:
                # Основные игры - как в боте (кнопка Сгенерировать игру)
                max_tokens = 10000
                request_type = "основная игра"

        elif content_type == ContentType.TEXT_ANALYSIS:
            # Анализ текста - разные токены в зависимости от функции
            # За баллы (with_points) используются те же токены, что и для основной генерации
            if any(keyword in prompt_lower for keyword in ['detect_text_level', 'определить уровень']):
                max_tokens = 6000
                request_type = "определение уровня текста"
            elif any(keyword in prompt_lower for keyword in ['regenerate_text', 'перегенерировать']):
                max_tokens = 5000
                request_type = "перегенерация текста"
            elif any(keyword in prompt_lower for keyword in ['change_text_level', 'изменить уровень']):
                max_tokens = 5000
                request_type = "изменение уровня текста"
            elif any(keyword in prompt_lower for keyword in ['generate_questions', 'создать вопросы']):
                max_tokens = 4000
                request_type = "генерация вопросов"
            elif any(keyword in prompt_lower for keyword in ['generate_summary', 'создать саммари']):
                max_tokens = 3000
                request_type = "генерация саммари"
            elif any(keyword in prompt_lower for keyword in ['generate_titles', 'создать заголовки']):
                max_tokens = 2000
                request_type = "генерация заголовков"
            elif any(keyword in prompt_lower for keyword in ['comprehension_test', 'тест на понимание']):
                max_tokens = 4000
                request_type = "тест на понимание"
            else:
                # Общий анализ текста
                max_tokens = 5000
                request_type = "анализ текста"

        elif content_type == ContentType.CONCEPT_EXPLANATION:
            # Объяснение концепций - одинаковые токены для обычной генерации и за баллы
            max_tokens = 6000
            request_type = "объяснение концепций"

        elif content_type == ContentType.COURSE:
            # Генерация курсов - оптимальное количество токенов для полной структуры с activities
            max_tokens = 19000
            request_type = "генерация курса"

        elif content_type == ContentType.IMAGE:
            # Генерация изображений - не используют токены, но для логирования
            max_tokens = 0
            request_type = "генерация изображений"

        else:
            # Остальные типы контента (свободные запросы, AI ассистент)
            # Одинаковые токены для обычной генерации и за баллы
            max_tokens = 6000
            request_type = "свободный запрос"

        logger.info(f"Определены токены: {max_tokens} для content_type={content_type}, тип запроса: {request_type}")
        return max_tokens

    async def get_generation_queue(self):
        """Lazy initialization of generation queue"""
        if self._generation_queue is None:
            # Import here to avoid circular import
            from ...services.queue.generation_queue import AsyncGenerationQueue
            self._generation_queue = AsyncGenerationQueue(self.session)
            await self._generation_queue.initialize()
        return self._generation_queue

    async def generate_content(
        self,
        user_id: int,
        prompt: str,
        content_type: ContentType,
        use_cache: bool = True,
        force_queue: bool = False,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Генерирует контент на основе промпта

        Args:
            user_id: ID пользователя
            prompt: Текст промпта
            content_type: Тип контента
            use_cache: Использовать ли кэширование
            force_queue: Принудительно использовать очередь вместо прямой генерации
            extra_params: Дополнительные параметры для генерации

        Returns:
            str: Сгенерированный текст
        """
        try:
            # Логируем детали запроса
            logger.info(f"Генерация контента типа: {content_type.value if hasattr(content_type, 'value') else content_type}")
            logger.info(f"Параметры: user_id={user_id}, use_cache={use_cache}, force_queue={force_queue}")

            # Сохраняем параметры для использования в других методах
            self._current_extra_params = extra_params or {}
            # Добавляем параметр use_cache в extra_params для передачи в другие методы
            self._current_extra_params['use_cache'] = use_cache

            if extra_params:
                logger.info(f"Дополнительные параметры: {json.dumps(extra_params, ensure_ascii=False, default=str)[:200]}...")

            # Создаем кэш-ключ
            cache_key = self._create_cache_key(prompt, content_type, extra_params)

            # Проверяем кэш, если use_cache=True
            if use_cache:
                cached_content = await self.cache_service.get_cached_data(cache_key)
                if cached_content:
                    logger.info(f"Найден кэшированный контент, длина: {len(cached_content) if isinstance(cached_content, str) else 'не строка'}")
                    return cached_content

            # Валидируем длину промпта
            self._validate_prompt(prompt, content_type)

            # ВРЕМЕННО ОТКЛЮЧЕНО: API Gateway (пока исправляем ошибки)
            # if not force_queue:
            #     try:
            #         logger.info("Генерация контента через API Gateway")
            #         content = await self.generate_content_via_gateway(
            #             prompt=prompt,
            #             content_type=content_type,
            #             extra_params=extra_params
            #         )
            #         if content and not content.startswith("Ошибка"):
            #             return content
            #     except Exception as gateway_error:
            #         logger.error(f"Ошибка генерации через API Gateway: {str(gateway_error)}")

            # ПРИОРИТЕТ 1: Проверяем и инициализируем G4FHandler
            if not force_queue and await self.ensure_g4f_handler():
                # Пытаемся сгенерировать с использованием G4FHandler
                try:
                    logger.info("Генерация контента через G4FHandler")
                    # Извлекаем with_points из extra_params
                    with_points = extra_params.get('with_points', False) if extra_params else False
                    content = await self._generate_with_g4f(prompt, content_type, with_points)
                    if content:
                        # Кэшируем результат, если use_cache=True
                        if use_cache:
                            await self.cache_service.cache_data(cache_key, content, ttl=3600)

                        # Для структурированных данных, проверяем формат
                        if content_type == ContentType.STRUCTURED_DATA:
                            logger.info(f"Проверка формата структурированных данных, длина контента: {len(content)}")
                            try:
                                if isinstance(content, str):
                                    # Для строковых данных, попытка найти валидный JSON
                                    content = content.strip()
                                    start_idx = content.find('{')
                                    end_idx = content.rfind('}') + 1

                                    if start_idx >= 0 and end_idx > start_idx:
                                        json_str = content[start_idx:end_idx]
                                        logger.info(f"Извлечен JSON из контента, длина: {len(json_str)}")
                                        # Проверка валидности JSON
                                        try:
                                            json.loads(json_str)
                                            return content
                                        except json.JSONDecodeError as je:
                                            logger.error(f"Ошибка декодирования JSON: {str(je)}")
                                            logger.error(f"Фрагмент JSON: {json_str[:200]}...")
                                            # Продолжаем выполнение, попробуем резервный метод
                                    else:
                                        logger.error("Не удалось найти валидный JSON в сгенерированном контенте")
                                else:
                                    # Если контент уже не строка, возвращаем как есть
                                    return content
                            except Exception as e:
                                logger.error(f"Ошибка при проверке формата структурированных данных: {str(e)}")
                                # Продолжаем выполнение, попробуем резервный метод
                        else:
                            # Для не структурированных данных возвращаем как есть
                            return content
                except Exception as g4f_error:
                    # Логируем ошибку G4FHandler
                    logger.error(f"Ошибка генерации через G4FHandler: {str(g4f_error)}")
                    logger.info("Переключение на резервный метод генерации через очередь")

            # FALLBACK: Резервный метод - генерация через очередь
            logger.info("Генерация контента через очередь (резервный метод)")
            content = await self._generate_with_queue(user_id, prompt, content_type)

            if content:
                # Кэшируем результат, если use_cache=True
                if use_cache:
                    await self.cache_service.cache_data(cache_key, content, ttl=3600)
                return content
            else:
                logger.error("Оба метода генерации (G4FHandler и очередь) не смогли сгенерировать контент")
                return "Не удалось сгенерировать контент. Пожалуйста, попробуйте позже или обратитесь в поддержку."

        except Exception as e:
            logger.error(f"Критическая ошибка при генерации контента: {str(e)}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            return "Произошла ошибка при генерации контента. Пожалуйста, попробуйте позже."

    def _validate_prompt(self, prompt: str, content_type: Union[str, ContentType]) -> None:
        """Validate prompt length based on content type"""
        # Define max lengths for different content types
        max_lengths = {
            ContentType.LESSON_PLAN: 15000,
            ContentType.EXERCISE: 15000,
            ContentType.GAME: 15000,
            ContentType.TRANSCRIPT: 500,
            ContentType.TEXT_ANALYSIS: 15000,
            ContentType.STRUCTURED_DATA: 30000,
            ContentType.COURSE: 30000,
            'lesson_plan': 15000,
            'exercise': 15000,
            'game': 15000,
            'transcript': 500,
            'text_analysis': 15000,
            'structured_data': 30000,
            'course': 30000,
            'image': 200
        }

        # Get max_length based on content_type (can be string or enum)
        max_length = max_lengths.get(content_type, 500)

        if len(prompt) > max_length:
            ct_value = content_type.value if hasattr(content_type, 'value') else content_type
            raise ValidationError(f"Prompt too long for {ct_value}")

    def _create_cache_key(self, prompt: str, content_type: Union[str, ContentType], extra_params: Optional[Dict[str, Any]] = None) -> str:
        """Create cache key for content"""
        # Создаем базовый ключ из промпта и типа контента
        base_key = f"{content_type}:{hashlib.md5(prompt.encode()).hexdigest()}"
        
        # Добавляем параметры если есть
        if extra_params:
            params_str = json.dumps(extra_params, sort_keys=True, ensure_ascii=False)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()
            base_key += f":{params_hash}"
            
        return base_key

    async def _save_generation(self, batch: List[Dict[str, Any]]) -> None:
        """Batch save generations (улучшенная версия с детальным логированием)"""
        try:
            logger.info(f"=== SAVING GENERATIONS ===")
            logger.info(f"Batch size: {len(batch)}")

            if len(batch) > 0:
                logger.info(f"First item user_id: {batch[0].get('user_id')}")
                logger.info(f"First item type: {batch[0].get('type')}")
                logger.info(f"First item prompt: {batch[0].get('prompt')[:100]}...")

            generations = [
                Generation(
                    user_id=item["user_id"],
                    type=item["type"].value if hasattr(item["type"], "value") else item["type"],
                    content=item["content"],
                    prompt=item["prompt"],
                    created_at=datetime.now(timezone.utc)  # Используем timezone-aware datetime
                )
                for item in batch
            ]

            logger.info(f"Created {len(generations)} Generation objects")

            self.session.add_all(generations)
            await self.session.flush()

            logger.info(f"Successfully saved {len(generations)} generations to database")

            # Проверяем, что генерации действительно сохранились
            try:
                from sqlalchemy import select, func
                from ...models import Generation

                # Получаем общее количество генераций в базе
                count_query = select(func.count()).select_from(Generation.__table__)
                total_count = await self.session.scalar(count_query)

                logger.info(f"Total generations in database: {total_count}")
            except Exception as count_error:
                logger.error(f"Error checking total generations count: {str(count_error)}")

        except Exception as e:
            logger.error(f"Error saving generations: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def _get_user_priority(self, user_id: int) -> int:
        """Get user priority for queue"""
        query = await self.query_optimizer.optimize_query(
            select(User).where(User.id == user_id)
        )
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return 0

        # Priority based on tariff and points
        priority = 0
        if user.tariff:
            priority += {
                'tariff_2': 1,
                'tariff_4': 2,
                'tariff_6': 3
            }.get(user.tariff, 0)

        priority += min(user.points // 1000, 5)  # Up to 5 additional points for points
        return priority

    async def get_g4f_status(self):
        """Получить статус G4F провайдеров"""
        try:
            status = {
                "available": self._g4f_available,
                "providers": {
                    "gemini": self._gemini_available,
                    "openrouter": self._openrouter_available,
                    "groq": self._groq_available,
                    "llm7": self._llm7_available,
                    "together": self._together_available,
                    "cerebras": self._cerebras_available,
                    "chutes": self._chutes_available,
                    "mistral": self._mistral_available,
                    "g4f": self._g4f_available
                }
            }
            return status
        except Exception as e:
            logger.error(f"Error getting G4F status: {str(e)}")
            return {"available": False, "error": str(e)}

    def set_generation_timeout(self, timeout: int):
        """Установить таймаут для генерации"""
        self._generation_timeout = timeout
        logger.info(f"Generation timeout set to {timeout} seconds")

    async def clear_content_cache(self, content_type: Optional[ContentType] = None):
        """Очистить кэш контента"""
        try:
            if content_type:
                # Очищаем кэш для конкретного типа контента
                await self.cache_service.clear_cache_by_pattern(f"{content_type.value}:*")
                logger.info(f"Cleared cache for content type: {content_type.value}")
            else:
                # Очищаем весь кэш
                await self.cache_service.clear_all_cache()
                logger.info("Cleared all content cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    # API Gateway methods
    async def get_api_gateway_health(self) -> Dict[str, Any]:
        """Получить статус здоровья API Gateway"""
        try:
            return await self.api_gateway.get_provider_health_status()
        except Exception as e:
            logger.error(f"Error getting API Gateway health: {str(e)}")
            return {"error": str(e)}

    def get_api_gateway_stats(self) -> Dict[str, Any]:
        """Получить статистику API Gateway"""
        try:
            return self.api_gateway.get_stats()
        except Exception as e:
            logger.error(f"Error getting API Gateway stats: {str(e)}")
            return {"error": str(e)}

    async def cleanup_api_gateway(self):
        """Очистить ресурсы API Gateway"""
        try:
            await self.api_gateway.cleanup()
            logger.info("API Gateway resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up API Gateway: {str(e)}")

    # Context manager methods
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Очищаем ресурсы API Gateway
        await self.cleanup_api_gateway()
        await self.session.close()
