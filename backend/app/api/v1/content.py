from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Dict, Any, Optional, List
from ...core.database import get_db
from ...core.cache import CacheService, get_cache_service as get_core_cache_service
from ...core.memory import memory_optimized
from ...models import User, Generation, DailyUsage
from ...services.content.generator import ContentGenerator
from ...services.content.processor import ContentProcessor
from ...services.tracking.usage import UsageTracker
from ...services.achievements.manager import AchievementManager
from ...core.constants import TARIFF_LIMITS
from ...core.security import check_unlimited_access
from ...schemas.content import (
    ContentGeneration,
    ImageGenerationRequest,
    VideoTranscriptRequest,
    TranscriptContentGeneration,
    LessonPlanTranscriptGeneration,
    ExerciseTranscriptGeneration,
    GameTranscriptGeneration,
    ContentResponse,
    ImageResponse,
    VideoTranscriptResponse,
    DetectTextLevelRequest,
    RegenerateTextRequest,
    ChangeTextLevelRequest,
    GenerateQuestionsRequest,
    GenerateSummaryRequest,
    GenerateTitlesRequest,
    GenerateComprehensionTestRequest,
    TextAnalyzerResponse
)
from ...schemas.tracking import UsageLogCreate
import os
import json
import logging
from datetime import datetime, timezone
from ...core.decorators import (
    check_generation_limits,
    check_achievements,
    track_usage,
    track_feature_usage
)
from ...services.content.prompt_translator import prompt_translation_service
from ...decorators.premium_access import check_premium_access
from ...core.constants import ContentType, ActionType
from pydantic import BaseModel
from ...core.security import get_current_user, admin_required, check_admin_rights
from sqlalchemy import text
import re

# Настройка логера для content.py
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(os.path.join('logs', 'generation.log'), mode='a', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

router = APIRouter()

def get_cache_service() -> CacheService:
    """Dependency для получения сервиса кэширования"""
    return get_core_cache_service()

# После модели ContentGeneration, но перед router.post("/generate_lesson_plan")

class LessonPlanFormGeneration(BaseModel):
    """Модель запроса для генерации плана урока из формы"""
    user_id: int
    language: str
    topic: str
    level: Optional[str] = ""
    age: Optional[str] = "teens"
    previous_lesson: Optional[str] = ""
    grammar: Optional[str] = ""
    vocabulary: Optional[str] = ""
    methodology: Optional[List[str]] = []
    individual_group: Optional[str] = "individual"
    online_offline: Optional[str] = "online"
    exam: Optional[str] = ""
    duration: Optional[int] = 60
    with_points: Optional[bool] = False  # Флаг для генерации за баллы
    skip_tariff_check: Optional[bool] = False  # Флаг для пропуска проверки тарифа
    skip_limits: Optional[bool] = False  # Флаг для пропуска лимитов

@router.post("/generate_lesson_plan_form", response_model=ContentResponse)
@check_generation_limits(ContentType.LESSON_PLAN)
@check_achievements(ActionType.GENERATION, ContentType.LESSON_PLAN)
@track_usage(ContentType.LESSON_PLAN)
@track_feature_usage(feature_type="lesson_plan_form", content_type=ContentType.LESSON_PLAN)
@memory_optimized()
async def generate_lesson_plan_form(
        request: LessonPlanFormGeneration,
        session: AsyncSession = Depends(get_db),
        cache: CacheService = Depends(get_cache_service),
        current_user: User = Depends(get_current_user)
):
    """Generate a lesson plan from form data"""
    logger.info("Started lesson plan generation from form")

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    # Создаем кэш-ключ на основе всех параметров запроса
    # Используем ID пользователя из current_user вместо request.user_id
    user_id = current_user.id
    cache_key = f"lesson_plan_form:{user_id}:{hash(str(request.model_dump()))}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Подготавливаем данные для форматирования промпта
        form_data = request.model_dump()
        logger.info(f"Received form data: {form_data}")

        # Форматируем промпт специально для формы (используем улучшенную версию)
        formatted_prompt = format_prompt_lesson_plan_form_improved(form_data)
        logger.info(f"Formatted prompt for form (length: {len(formatted_prompt)})")
        logger.debug(f"Full formatted prompt: {formatted_prompt}")

        # Генерируем контент
        generator = ContentGenerator(session)
        logger.info("Calling content generator...")
        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=user_id,  # Используем user_id из current_user
            content_type=ContentType.LESSON_PLAN,
            use_cache=False,
            force_queue=False
            # Удалили with_points=False - этот параметр не поддерживается
        )

        logger.info(f"Received generated content (length: {len(content)})")
        logger.debug(f"Generated content start: {content[:500]}...")
        logger.debug(f"Generated content end: ...{content[-500:]}")

        # Создаем и сохраняем генерацию в базе данных
        generation = Generation(
            user_id=user_id,  # Используем user_id из current_user
            type=ContentType.LESSON_PLAN,
            content=content,
            prompt=str(request.model_dump()),
            created_at=datetime.now(timezone.utc)
        )
        session.add(generation)
        await session.flush()  # Получаем ID генерации

        # Создаем данные ответа
        response_data = {
            "id": generation.id,
            "user_id": user_id,  # Используем user_id из current_user
            "type": ContentType.LESSON_PLAN.value,
            "content": content,
            "prompt": str(request.model_dump()),
            "with_points": request.with_points,  # Добавляем информацию о генерации за баллы
            "created_at": generation.created_at.isoformat()
        }

        # Логирование использования
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=user_id,  # Используем user_id из current_user
            action_type="generation",
            content_type=ContentType.LESSON_PLAN.value,
            extra_data={"prompt": str(request.model_dump()), "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        # Фиксируем транзакцию
        await session.commit()

        # Кэшируем результат
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": f"Lesson plan generated successfully, length: {len(content)}",
            "with_points": request.with_points  # Добавляем информацию о генерации за баллы
        })

        logger.info("Form-based lesson plan generation completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message=f"Lesson plan generated successfully, length: {len(content)}",
            with_points=request.with_points  # Добавляем информацию о генерации за баллы
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating lesson plan from form: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating lesson plan from form: {str(e)}"
        )

@router.post("/generate_lesson_plan", response_model=ContentResponse)
@check_generation_limits(ContentType.LESSON_PLAN)
@check_achievements(ActionType.GENERATION, ContentType.LESSON_PLAN)
@track_usage(ContentType.LESSON_PLAN)
@track_feature_usage(feature_type="lesson_plan", content_type=ContentType.LESSON_PLAN)
@memory_optimized()
async def generate_lesson_plan(
        request: ContentGeneration,
        session: AsyncSession = Depends(get_db),
        cache: CacheService = Depends(get_cache_service)
):
    """Generate a lesson plan"""
    logger.info("Started lesson plan generation")

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    # Convert string to ContentType if needed
    content_type = request.type
    if isinstance(content_type, str):
        try:
            content_type = ContentType(content_type)
        except (ValueError, TypeError):
            # Default to LESSON_PLAN if conversion fails
            content_type = ContentType.LESSON_PLAN
            logger.warning(f"Invalid content type: {request.type}, defaulting to {content_type}")

    # Set the converted type back to the request
    request.type = content_type

    # Проверяем кэш
    cache_key = f"lesson_plan:{request.user_id}:{hash(request.prompt)}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Parse the prompt
        prompt_data = json.loads(request.prompt)
        logger.info(f"Received prompt data: {prompt_data}")

        # Fixed: call format_prompt function correctly, not as a coroutine
        formatted_prompt = format_prompt(prompt_data, "lesson_plan")
        logger.info(f"Formatted prompt (length: {len(formatted_prompt)})")
        logger.debug(f"Full formatted prompt: {formatted_prompt}")

        # Generate content
        generator = ContentGenerator(session)
        logger.info("Calling content generator...")
        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=request.user_id,
            content_type=content_type,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
        )

        logger.info(f"Received generated content (length: {len(content)})")
        logger.debug(f"Generated content start: {content[:500]}...")
        logger.debug(f"Generated content end: ...{content[-500:]}")

        # Create and store the generation in the database
        generation = Generation(
            user_id=request.user_id,
            type=content_type,
            content=content,
            prompt=request.prompt,
            created_at=datetime.now(timezone.utc)
        )
        session.add(generation)
        await session.flush()  # This assigns an ID to the generation

        # Create response data using the actual generated ID
        response_data = {
            "id": generation.id,
            "user_id": request.user_id,
            "type": content_type.value,  # Use enum value for consistent API response
            "content": content,
            "prompt": request.prompt,
            "with_points": request.with_points,  # Добавляем информацию о генерации за баллы
            "created_at": generation.created_at.isoformat()
        }

        # Log usage
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=content_type.value,  # Pass string value
            extra_data={"prompt": request.prompt, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        # Commit the transaction
        await session.commit()

        # Cache the result
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": f"Lesson plan generated successfully, length: {len(content)}"
        })

        logger.info("Generation completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message=f"Lesson plan generated successfully, length: {len(content)}"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating lesson plan: {str(e)}"
        )

@router.post("/detail_lesson_plan", response_model=ContentResponse)
async def detail_lesson_plan(
        request: ContentGeneration,
        session: AsyncSession = Depends(get_db),
        cache: CacheService = Depends(get_cache_service),
        current_user: User = Depends(get_current_user)
):
    """Detail a lesson plan point or generate related content"""
    logger.info("Started lesson plan content generation")

    # Проверяем, используются ли баллы для генерации
    # Сначала проверяем атрибут with_points в объекте запроса
    with_points = getattr(request, 'with_points', False)

    # Затем проверяем, есть ли with_points в данных запроса
    if hasattr(request, 'model_dump') and callable(request.model_dump):
        try:
            request_data = request.model_dump()
            with_points = with_points or request_data.get('with_points', False)
        except Exception as e:
            logger.warning(f"Ошибка при получении данных запроса: {str(e)}")

    # Также проверяем, есть ли with_points в JSON-данных промпта
    try:
        prompt_data = json.loads(request.prompt) if request.prompt else {}
        with_points = with_points or prompt_data.get('with_points', False)
    except Exception as e:
        logger.warning(f"Ошибка при разборе JSON промпта: {str(e)}")

    # Если используются баллы, устанавливаем соответствующие атрибуты
    if with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    # Получаем параметры skip_tariff_check и skip_limits
    skip_tariff_check = getattr(request, 'skip_tariff_check', False)
    skip_limits = getattr(request, 'skip_limits', False)

    # Если используются баллы, пропускаем проверку лимитов и тарифа
    if with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Пропускаем проверку лимитов и тарифа, если используются баллы
        skip_tariff_check = True
        skip_limits = True
    # Проверяем безлимитный доступ один раз
    is_unlimited = await check_unlimited_access(request.user_id, session)

    # Если не используются баллы и не указано пропустить проверку тарифа
    if not with_points and not skip_tariff_check and not is_unlimited:
        # Проверяем тариф пользователя только если нет безлимитного доступа
        if not current_user:
            logger.error(f"current_user is None. Cannot check tariff.")
            raise HTTPException(status_code=403, detail="User not authenticated")

        if not current_user.tariff:
            logger.warning(f"No active tariff found for user {request.user_id} in current_user object.")
            raise HTTPException(status_code=403, detail="No active tariff")

    if is_unlimited:
        logger.info(f"User {request.user_id} has unlimited access, skipping all limit checks")

    # Если не используются баллы и не указано пропустить проверку лимитов
    if not with_points and not skip_limits and not is_unlimited:
        # Получаем дневное использование
        stmt = select(DailyUsage).where(
            DailyUsage.user_id == request.user_id,
            DailyUsage.date == datetime.now(timezone.utc).date()
        )
        result = await session.execute(stmt)
        daily_usage = result.scalar_one_or_none()

        if not daily_usage:
            daily_usage = DailyUsage(user_id=request.user_id)
            session.add(daily_usage)
            await session.flush()

        # Получаем лимиты для тарифа пользователя
        limit_key = current_user.tariff
        limits = TARIFF_LIMITS.get(limit_key)

        if not limits:
            logger.error(f"Could not find limits for tariff key: {limit_key}")
            raise HTTPException(status_code=500, detail=f"Tariff limits not configured for {current_user.tariff}")

        # Проверяем лимиты генерации
        if daily_usage.generations_count >= limits.daily_generations:
            logger.warning(f"Daily generation limit exceeded for user {request.user_id}")
            raise HTTPException(status_code=429, detail="Daily generation limit exceeded")

    # Convert string to ContentType if needed
    content_type = request.type
    if isinstance(content_type, str):
        try:
            content_type = ContentType(content_type)
        except (ValueError, TypeError):
            # Default to LESSON_PLAN if conversion fails
            content_type = ContentType.LESSON_PLAN
            logger.warning(f"Invalid content type: {request.type}, defaulting to {content_type}")

    # Set the converted type back to the request
    request.type = content_type

    try:
        # Parse the prompt
        prompt_data = json.loads(request.prompt)
        logger.info(f"Received prompt data for content generation: {prompt_data}")

        # Получаем тип запрашиваемого контента
        specific_content_type = prompt_data.get('content_type', 'lesson_plan_point')
        logger.info(f"Specific content type: {specific_content_type}")

        # Настраиваем кэш-ключ в зависимости от типа контента
        cache_key = f"lesson_plan_{specific_content_type}:{request.user_id}:{hash(request.prompt)}"
        cached_result = await cache.get_cached_data(cache_key)
        if cached_result:
            return ContentResponse(**cached_result)

        # Специальная инструкция для генерации контента
        system_instruction = prompt_data.get('system_instruction', """
        Ты опытный преподаватель, который создает дополнительные материалы для существующего плана урока,
        а не создает новые планы. Твоя задача - обогатить план дополнительными деталями или материалами.
        """)

        # Объединяем инструкции и данные
        prompt_data["system_instruction"] = system_instruction

        # Получаем оригинальные опции
        original_options = prompt_data.get('original_options', {})

        # Получаем оригинальный план урока
        original_lesson_plan = prompt_data.get('lesson_plan', '')

        # Ограничиваем размер оригинального плана урока для оптимизации промпта
        # Если план урока слишком большой, берем только первые 3000 символов
        # и добавляем соответствующее примечание
        MAX_LESSON_PLAN_LENGTH = 5000  # Значение подобрано экспериментально
        original_lesson_plan_truncated = original_lesson_plan
        plan_truncated_notice = ""

        if len(original_lesson_plan) > MAX_LESSON_PLAN_LENGTH:
            logger.info(f"Truncating original lesson plan from {len(original_lesson_plan)} to {MAX_LESSON_PLAN_LENGTH} characters")
            # Находим последний полный пункт перед ограничением
            truncation_point = original_lesson_plan[:MAX_LESSON_PLAN_LENGTH].rfind("\n\n")
            if truncation_point == -1:  # Если не нашли двойной перенос строки, ищем одинарный
                truncation_point = original_lesson_plan[:MAX_LESSON_PLAN_LENGTH].rfind("\n")
            if truncation_point == -1:  # Если совсем не нашли перенос строки
                truncation_point = MAX_LESSON_PLAN_LENGTH

            original_lesson_plan_truncated = original_lesson_plan[:truncation_point]
            plan_truncated_notice = "\n[ПРИМЕЧАНИЕ: Оригинальный план урока был сокращен для оптимизации запроса.]"

        # Проверяем, есть ли оригинальный пункт плана в запросе
        original_point = prompt_data.get('original_point', '')

        # Определяем, является ли запрос детализацией конкретного пункта
        is_point_detail = specific_content_type.startswith('point_')
        point_number = None

        if is_point_detail:
            # Извлекаем номер пункта из content_type (например, из 'point_5' получаем '5')
            try:
                point_number = int(specific_content_type.split('_')[1])
                logger.info(f"Запрос на детализацию пункта {point_number}")
            except (IndexError, ValueError):
                logger.warning(f"Не удалось извлечь номер пункта из {specific_content_type}")

        # Форматируем промпт для детализации с учетом оригинальных параметров
        formatted_prompt = f"""
        INSTRUCTION: {prompt_data.get('instruction', 'Детализируй следующий пункт плана урока.')}

        ACTION: {prompt_data.get('action', 'Предоставь подробное описание запрошенной части.')}

        ПАРАМЕТРЫ ИСХОДНОГО УРОКА:
        - Язык: {prompt_data.get('language', 'Не указан')}
        - Возрастная группа: {original_options.get('age', 'Не указана')}
        - Методология: {original_options.get('methodology', 'Не указана')}
        - Продолжительность: {original_options.get('duration', 'Не указана')} минут
        - Тип занятия: {original_options.get('individual_group', 'Не указан')}
        - Формат проведения: {original_options.get('online_offline', 'Не указан')}
        - Фокус урока: {original_options.get('focus', 'Не указан')}
        - Уровень сложности: {original_options.get('level', 'Не указан')}
        """

        # Если это детализация конкретного пункта и у нас есть оригинальный пункт,
        # добавляем его в промпт перед полным планом урока
        if is_point_detail and original_point:
            formatted_prompt += f"""
        ОРИГИНАЛЬНЫЙ ПУНКТ {point_number} ПЛАНА УРОКА:
        {original_point}

        """

        # Добавляем полный план урока
        formatted_prompt += f"""
        ОРИГИНАЛЬНЫЙ ПЛАН УРОКА:
        {original_lesson_plan_truncated}{plan_truncated_notice}

        ВАЖНО:
        1. НЕ СОЗДАВАЙ НОВЫЙ ПЛАН УРОКА.
        2. ГЕНЕРИРУЙ ТОЛЬКО ЗАПРОШЕННЫЙ ТИП КОНТЕНТА: {specific_content_type}
        3. СОХРАНЯЙ СООТВЕТСТВИЕ ОРИГИНАЛЬНОМУ ПЛАНУ И ЕГО ЦЕЛЯМ.
        4. ИСПОЛЬЗУЙ MARKDOWN ДЛЯ ФОРМАТИРОВАНИЯ.
        5. УЧИТЫВАЙ ВСЕ ИСХОДНЫЕ ПАРАМЕТРЫ УРОКА.
        6. НЕ ЗАПРАШИВАЙ ДОПОЛНИТЕЛЬНУЮ ИНФОРМАЦИЮ - ПРЕДОСТАВЬ ПОЛНЫЙ ОТВЕТ НА ОСНОВЕ ИМЕЮЩИХСЯ ДАННЫХ.
        """

        # Generate content
        generator = ContentGenerator(session)
        logger.info("Calling content generator for specialized content generation...")
        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=request.user_id,
            content_type=content_type,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
        )

        logger.info(f"Received content (length: {len(content)})")
        logger.debug(f"Content start: {content[:500]}...")
        logger.debug(f"Content end: ...{content[-500:]}")

        # Create and store the generation in the database
        generation = Generation(
            user_id=request.user_id,
            type=content_type,
            content=content,
            prompt=request.prompt,
            created_at=datetime.now(timezone.utc)
        )
        session.add(generation)
        await session.flush()  # This assigns an ID to the generation

        # Определяем тип контента для сообщения
        content_type_message = {
            'lesson_plan_point': 'Пункт плана урока',
            'homework': 'Домашнее задание',
            'teacher_script': 'Скрипт учителя',
            'exercises': 'Упражнения',
            'game': 'Игра для урока',
            'rewrite_lesson_point': 'Переписанный пункт плана'
        }.get(specific_content_type, 'Дополнительный контент')

        # Create response data using the actual generated ID
        response_data = {
            "id": generation.id,
            "user_id": request.user_id,
            "type": content_type.value,  # Use enum value for consistent API response
            "content": content,
            "prompt": request.prompt,
            "content_type": specific_content_type,  # Добавляем тип контента в ответ
            "original_point": original_point if is_point_detail else "",  # Добавляем оригинальный пункт в ответ
            "with_points": request.with_points,  # Добавляем информацию о генерации за баллы
            "created_at": generation.created_at.isoformat()
        }

        # Log usage
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=content_type.value,  # Pass string value
            extra_data={"prompt": request.prompt, "specific_content": specific_content_type, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        # Проверяем достижения
        try:
            async with AchievementManager(session) as achievement_manager:
                await achievement_manager.check_achievements(
                    user_id=request.user_id,
                    action_type=ActionType.GENERATION,
                    action_data={
                        'content_type': ContentType.LESSON_PLAN.value,
                        'success': True
                    }
                )
        except Exception as e:
            logger.error(f"Error checking achievements: {str(e)}")
            # Don't fail the request if achievements check fails

        # Commit the transaction
        await session.commit()

        # Cache the result
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": f"{content_type_message} сгенерирован успешно, длина: {len(content)}"
        })

        logger.info(f"Content generation completed successfully: {specific_content_type}")
        return ContentResponse(
            status="success",
            data=response_data,
            message=f"{content_type_message} сгенерирован успешно, длина: {len(content)}"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating lesson plan content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error detailing lesson plan point: {str(e)}"
        )

@router.post("/generate_exercises", response_model=ContentResponse)
@check_generation_limits(ContentType.EXERCISE)
@check_achievements(ActionType.GENERATION, ContentType.EXERCISE)
@track_usage(ContentType.EXERCISE)
@track_feature_usage("exercise", ContentType.EXERCISE)
@memory_optimized()
async def generate_exercises(
    request: ContentGeneration,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Generate exercises"""
    logger.info("Started exercise generation")

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    cache_key = f"exercises:{request.user_id}:{hash(request.prompt)}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Parse the prompt
        prompt_data = json.loads(request.prompt)
        logger.info(f"Received prompt data: {prompt_data}")

        # Fixed: call format_prompt function correctly, not as a coroutine
        formatted_prompt = format_prompt(prompt_data, "exercise")
        logger.info(f"Formatted prompt (length: {len(formatted_prompt)})")
        logger.debug(f"Full formatted prompt: {formatted_prompt}")

        # Generate content
        generator = ContentGenerator(session)
        logger.info("Calling content generator...")
        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=request.user_id,
            content_type=ContentType.EXERCISE,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
        )

        logger.info(f"Received generated content (length: {len(content)})")
        logger.debug(f"Generated content start: {content[:500]}...")
        logger.debug(f"Generated content end: ...{content[-500:]}")

        # Create and store the generation in the database
        generation = Generation(
            user_id=request.user_id,
            type=ContentType.EXERCISE,
            content=content,
            prompt=request.prompt,
            created_at=datetime.now(timezone.utc)
        )
        session.add(generation)
        await session.flush()  # This assigns an ID to the generation

        # Create response data using the actual generated ID
        response_data = {
            "id": generation.id,
            "user_id": request.user_id,
            "type": ContentType.EXERCISE.value,
            "content": content,
            "prompt": request.prompt,
            "created_at": generation.created_at.isoformat()
        }

        # Log usage
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.EXERCISE.value,
            extra_data={"prompt": request.prompt, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        # Commit the transaction
        await session.commit()

        # Подготовка данных ответа
        # Обрабатываем контент упражнений с помощью ContentProcessor
        # Передаем все данные промпта для правильной обработки
        processed_exercises = await ContentProcessor.process_exercise_content(content, prompt_data, logger)

        # Добавляем обработанные упражнения в ответ
        response_data["processed_content"] = processed_exercises

        # Cache the result
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": f"Exercises generated successfully, items: {len(processed_exercises)}"
        })

        logger.info(f"Generation completed successfully, returning {len(processed_exercises)} exercises")
        return ContentResponse(
            status="success",
            data=response_data,
            message=f"Exercises generated successfully, items: {len(processed_exercises)}"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating exercises: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/generate_game", response_model=ContentResponse)
@check_generation_limits(ContentType.GAME)
@check_achievements(ActionType.GENERATION, ContentType.GAME)
@track_usage(ContentType.GAME)
@track_feature_usage("game", ContentType.GAME)
@memory_optimized()
async def generate_game(
    request: ContentGeneration,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Generate a game"""
    logger.info(f"Начало обработки запроса на генерацию игры для пользователя {request.user_id}")
    logger.info(f"Тип запроса: {request.type}")
    logger.info(f"Промпт (первые 100 символов): {request.prompt[:100]}...")

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    # Проверяем соединение с базой данных
    try:
        await session.execute(text("SELECT 1"))
        logger.info("Соединение с базой данных успешно установлено")
    except Exception as db_error:
        logger.error(f"Ошибка подключения к базе данных: {str(db_error)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(db_error)}"
        )

    cache_key = f"game:{request.user_id}:{hash(request.prompt)}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        logger.info("Найден кэшированный результат, возвращаем его")
        return ContentResponse(**cached_result)

    try:
        logger.info("Пытаемся разобрать JSON промпта")
        try:
            prompt_data = json.loads(request.prompt)
            logger.info(f"JSON успешно разобран: {prompt_data}")
        except json.JSONDecodeError as json_err:
            logger.error(f"Ошибка при разборе JSON: {str(json_err)}")
            logger.error(f"Содержимое промпта: {request.prompt}")
            raise ValueError(f"Невозможно разобрать JSON промпта: {str(json_err)}")

        # Fixed: call format_prompt function correctly, not as a coroutine
        logger.info("Форматируем промпт для генерации игры")
        formatted_prompt = format_prompt(prompt_data, "game")
        logger.info(f"Отформатированный промпт (первые 100 символов): {formatted_prompt[:100]}...")

        logger.info("Создаем экземпляр ContentGenerator")
        generator = ContentGenerator(session)

        logger.info("Вызываем метод generate_content")
        try:
            content = await generator.generate_content(
                prompt=formatted_prompt,
                user_id=request.user_id,
                content_type=ContentType.GAME,
                use_cache=False,
                force_queue=False,
                extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
            )
            logger.info(f"Контент успешно сгенерирован, длина: {len(content)}")
        except Exception as gen_error:
            logger.error(f"Ошибка при генерации контента: {str(gen_error)}", exc_info=True)
            raise ValueError(f"Ошибка при генерации контента: {str(gen_error)}")

        # Create and store the generation in the database
        logger.info("Создаем запись в базе данных")
        generation = Generation(
            user_id=request.user_id,
            type=ContentType.GAME,
            content=content,
            prompt=request.prompt,
            created_at=datetime.now(timezone.utc)
        )

        try:
            session.add(generation)
            logger.info("Выполняем flush для получения ID")
            await session.flush()  # This assigns an ID to the generation
            logger.info(f"Получен ID: {generation.id}")
        except Exception as db_error:
            logger.error(f"Ошибка при сохранении в базу данных: {str(db_error)}", exc_info=True)
            await session.rollback()
            raise ValueError(f"Ошибка при сохранении в базу данных: {str(db_error)}")

        # Create response data using the actual generated ID
        response_data = {
            "id": generation.id,
            "user_id": request.user_id,
            "type": ContentType.GAME.value,
            "content": content,
            "prompt": request.prompt,
            "created_at": generation.created_at.isoformat()
        }
        logger.info("Данные ответа подготовлены")

        logger.info("Логируем использование")
        try:
            tracker = UsageTracker(session)
            await tracker.log_usage(UsageLogCreate(
                user_id=request.user_id,
                action_type="generation",
                content_type=ContentType.GAME.value,
                extra_data={"prompt": request.prompt, "with_points": request.with_points},
                skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
            ))
            logger.info("Использование успешно залогировано")
        except Exception as usage_error:
            logger.error(f"Ошибка при логировании использования: {str(usage_error)}", exc_info=True)
            # Продолжаем выполнение, так как это не критическая ошибка

        logger.info("Выполняем commit транзакции")
        try:
            await session.commit()
            logger.info("Транзакция успешно завершена")
        except Exception as commit_error:
            logger.error(f"Ошибка при выполнении commit: {str(commit_error)}", exc_info=True)
            await session.rollback()
            raise ValueError(f"Ошибка при выполнении commit: {str(commit_error)}")

        # cache the result
        logger.info("Кэшируем результат")
        try:
            await cache.cache_data(cache_key, {
                "status": "success",
                "data": response_data,
                "message": "Game generated successfully"
            })
            logger.info("Результат успешно кэширован")
        except Exception as cache_error:
            logger.error(f"Ошибка при кэшировании результата: {str(cache_error)}", exc_info=True)
            # Продолжаем выполнение, так как это не критическая ошибка

        logger.info("Возвращаем успешный ответ")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Game generated successfully"
        )

    except ValueError as e:
        await session.rollback()
        logger.error(f"Value error in game generation: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating game: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.post("/generate_image", response_model=ImageResponse)
@check_generation_limits(ContentType.IMAGE)
@check_achievements(ActionType.GENERATION, ContentType.IMAGE)
@track_usage(ContentType.IMAGE)
@track_feature_usage("image", ContentType.IMAGE)
@memory_optimized()
async def generate_image(
    request: ImageGenerationRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Generate an image"""

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)
        # Принудительно отключаем кэширование для генерации за баллы
        setattr(request, 'use_cache', False)
        logger.info(f"Cache forcibly disabled for points-based image generation for user {request.user_id}")

    # Проверяем, нужно ли использовать кэш
    # Если генерация за баллы, всегда отключаем кэширование
    use_cache = not hasattr(request, 'use_cache') or request.use_cache is not False
    if hasattr(request, 'with_points') and request.with_points:
        use_cache = False
        logger.info(f"Points-based generation detected, cache forcibly disabled for user {request.user_id}")

    # Для генерации за баллы всегда пропускаем проверку кэша
    if use_cache and not request.with_points:
        # Создаем уникальный ключ кэша на основе пользователя и промпта
        cache_key = f"image:{request.user_id}:{hash(request.prompt)}"
        cached_result = await cache.get_cached_data(cache_key)
        if cached_result:
            logger.info(f"Using cached image for user {request.user_id}")
            return ImageResponse(**cached_result)
    else:
        logger.info(f"Cache disabled for image generation for user {request.user_id}")

    try:
        generator = ContentGenerator(session)
        # Используем параметр use_cache из request или значение по умолчанию
        # Если генерация за баллы, принудительно отключаем кэширование
        use_cache_param = getattr(request, 'use_cache', True)
        if hasattr(request, 'with_points') and request.with_points:
            use_cache_param = False
        logger.info(f"Generating image with use_cache={use_cache_param}, with_points={getattr(request, 'with_points', False)}")

        # Переводим промпт на английский язык перед обработкой
        original_prompt = request.prompt
        logger.info(f"Original prompt: {original_prompt[:100]}...")

        # Переводим пользовательский ввод на английский язык
        try:
            if prompt_translation_service and prompt_translation_service.is_available():
                translated_prompt = await prompt_translation_service.translate_prompt(original_prompt)
                logger.info(f"Translated prompt: {translated_prompt[:100]}...")
            else:
                logger.warning("Translation service not available, using original prompt")
                translated_prompt = original_prompt
        except Exception as e:
            logger.error(f"Error translating prompt: {e}")
            logger.warning("Using original prompt due to translation error")
            translated_prompt = original_prompt

        # Если генерация за баллы, добавляем временную метку к промпту для уникальности
        prompt = translated_prompt
        if hasattr(request, 'with_points') and request.with_points:
            import time
            import random
            # Добавляем временную метку и случайное число к промпту для уникальности
            timestamp = int(time.time())
            random_num = random.randint(1000, 9999)

            # Добавляем более сложный уникальный суффикс для points-based генерации
            # Включаем больше случайных элементов для гарантии уникальности
            unique_suffix = f" [t:{timestamp}:r:{random_num}:u:{random.randint(10000, 99999)}:rand:{random.random()}]"
            prompt = f"{prompt}{unique_suffix}"
            logger.info(f"Added uniqueness suffix to points-based image prompt: {unique_suffix}")

        # Создаем параметры для передачи в генератор с дополнительными параметрами для points-based генерации
        params = {
            'with_points': request.with_points if hasattr(request, 'with_points') else False,
            'use_cache': use_cache_param
        }

        # Для генерации за баллы добавляем дополнительные параметры для уникальности
        if hasattr(request, 'with_points') and request.with_points:
            import time
            import random
            params['timestamp'] = int(time.time())
            params['random'] = random.random()
            params['seed'] = random.randint(1000000, 9999999)
            params['randomize_seed'] = True

        logger.info(f"Passing params to image generator: {params}")

        # Генерируем изображение с обновленными параметрами
        image_url = await generator.generate_image(
            user_id=request.user_id,
            prompt=prompt,
            params=params,
            use_cache=use_cache_param,
            force_queue=False
        )

        # Проверяем, что URL не пустой
        if not image_url:
            logger.error(f"Empty image URL returned for user {request.user_id}")
            raise ValueError("Empty image URL returned from generator")

        # Логируем полученный URL для отладки
        if isinstance(image_url, dict):
            actual_url = image_url.get('url', str(image_url))
            logger.info(f"Generated image URL: {str(actual_url)[:100]}...")
            # Извлекаем URL из словаря если это результат ImageGenerationService
            image_url = actual_url
        else:
            logger.info(f"Generated image URL: {str(image_url)[:100]}...")

        response_data = {
            "id": 1,
            "url": image_url,
            "created_at": datetime.now().isoformat()
        }

        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="image",
            content_type=ContentType.IMAGE.value,
            extra_data={"prompt": request.prompt, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        await session.commit()

        # cache the result only if use_cache is True and not points-based generation
        if use_cache and not request.with_points:
            cache_key = f"image:{request.user_id}:{hash(request.prompt)}"
            await cache.cache_data(cache_key, {
                "status": "success",
                "data": response_data,
                "message": "Image generated successfully"
            })
            logger.info(f"Cached image result for user {request.user_id}")
        else:
            logger.info(f"Skipping cache for image result (use_cache={use_cache}, with_points={request.with_points})")

        return ImageResponse(
            status="success",
            data=response_data,
            message="Image generated successfully"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/process_video_transcript", response_model=VideoTranscriptResponse)
@check_generation_limits(ContentType.TRANSCRIPT)
@check_achievements(ActionType.GENERATION, ContentType.TRANSCRIPT)
@track_usage(ContentType.TRANSCRIPT)
@track_feature_usage("transcript", ContentType.TRANSCRIPT)
@memory_optimized()
async def process_video_transcript(
    request: VideoTranscriptRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Process video transcript"""

    # Проверяем, используются ли баллы для генерации
    if hasattr(request, 'with_points') and request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    cache_key = f"transcript:{request.video_id}:{request.subtitle_language}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return VideoTranscriptResponse(**cached_result)

    try:
        generator = ContentGenerator(session)
        transcript = await generator.process_video_transcript(
            video_id=request.video_id,
            subtitle_language=request.subtitle_language,
            use_cache=False,
            force_queue=False
        )

        response_data = {
            "id": 1,
            "transcript": transcript,
            "created_at": datetime.now().isoformat()
        }

        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TRANSCRIPT.value,
            extra_data={"prompt": request.prompt, "video_id": request.video_id, "with_points": getattr(request, 'with_points', False)},
            skip_limits=getattr(request, 'with_points', False)  # Пропускаем лимиты, если генерация за баллы
        ))

        await session.commit()

        # cache the result with longer TTL for transcripts
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Video transcript processed successfully"
        }, ttl=86400)  # 24 hours cache for transcripts

        return VideoTranscriptResponse(
            status="success",
            data=response_data,
            message="Video transcript processed successfully"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error processing video transcript: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/generate_lesson_plan_from_transcript", response_model=ContentResponse)
@check_generation_limits(ContentType.LESSON_PLAN)
@check_achievements(ActionType.GENERATION, ContentType.LESSON_PLAN)
@track_usage(ContentType.LESSON_PLAN)
@track_feature_usage("lesson_plan_transcript", ContentType.LESSON_PLAN)
@memory_optimized()
async def generate_lesson_plan_from_transcript(
    request: LessonPlanTranscriptGeneration,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Generate lesson plan from video transcript"""

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    cache_key = f"lesson_plan_transcript:{request.video_id}:{request.language}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        generator = ContentGenerator(session)

        # Получаем транскрипт из кэша или YouTube
        transcript_key = f"transcript:{request.video_id}:{request.language}"
        transcript = await cache.get_cached_data(transcript_key)

        if not transcript:
            transcript = await generator.process_video_transcript(
                video_id=request.video_id,
                subtitle_language=request.language,
                use_cache=False,
                force_queue=False
            )
            await cache.cache_data(transcript_key, transcript, ttl=86400)

        # Форматируем промпт с текстом транскрипта
        # Fixed: call format_prompt function correctly, not as a coroutine
        formatted_prompt = format_prompt(
            request.model_dump(),
            "lesson_plan_from_transcript",
            transcript
        )

        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=current_user.id,  # Используем ID из current_user
            content_type=ContentType.LESSON_PLAN,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
        )

        response_data = {
            "id": 1,
            "user_id": current_user.id,  # Используем ID из current_user
            "type": "lesson_plan",
            "content": content,
            "video_id": request.video_id,
            "created_at": datetime.now().isoformat()
        }

        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=current_user.id,  # Используем ID из current_user
            action_type="generation",
            content_type=ContentType.LESSON_PLAN.value,
            extra_data={"transcript_id": request.transcript_id, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        await session.commit()

        # cache the result
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Lesson plan generated successfully"
        })

        return ContentResponse(
            status="success",
            data=response_data,
            message="Lesson plan generated successfully"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/generate_exercises_from_transcript", response_model=ContentResponse)
@check_generation_limits(ContentType.EXERCISE)
@check_achievements(ActionType.GENERATION, ContentType.EXERCISE)
@track_usage(ContentType.EXERCISE)
@track_feature_usage("exercise_transcript", ContentType.EXERCISE)
@memory_optimized()
async def generate_exercises_from_transcript(
    request: ExerciseTranscriptGeneration,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Generate exercises from video transcript"""

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    cache_key = f"exercises_transcript:{request.video_id}:{request.language}:{request.difficulty}:{request.exercise_type}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        generator = ContentGenerator(session)

        # Получаем транскрипт из кэша или YouTube
        transcript_key = f"transcript:{request.video_id}:{request.language}"
        transcript = await cache.get_cached_data(transcript_key)

        if not transcript:
            transcript = await generator.process_video_transcript(
                video_id=request.video_id,
                subtitle_language=request.language,
                use_cache=False,
                force_queue=False
            )
            await cache.cache_data(transcript_key, transcript, ttl=86400)

        # Форматируем промпт с текстом транскрипта
        # Fixed: call format_prompt function correctly, not as a coroutine
        formatted_prompt = format_prompt(
            request.model_dump(),
            "exercises_from_transcript",
            transcript
        )

        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=current_user.id,  # Используем ID из current_user
            content_type=ContentType.EXERCISE,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
        )

        response_data = {
            "id": 1,
            "user_id": current_user.id,  # Используем ID из current_user
            "type": "exercises",
            "content": content,
            "video_id": request.video_id,
            "created_at": datetime.now().isoformat()
        }

        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=current_user.id,  # Используем ID из current_user
            action_type="generation",
            content_type=ContentType.EXERCISE.value,
            extra_data={"transcript_id": request.transcript_id, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        await session.commit()

        # cache the result
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Exercises generated successfully"
        })

        return ContentResponse(
            status="success",
            data=response_data,
            message="Exercises generated successfully"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating exercises: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/generate_games_from_transcript", response_model=ContentResponse)
@check_generation_limits(ContentType.GAME)
@check_achievements(ActionType.GENERATION, ContentType.GAME)
@track_usage(ContentType.GAME)
@track_feature_usage("game_transcript", ContentType.GAME)
@memory_optimized()
async def generate_games_from_transcript(
    request: GameTranscriptGeneration,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Generate games from video transcript"""

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {request.user_id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Устанавливаем атрибуты skip_tariff_check и skip_limits в request для декораторов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)

    cache_key = f"games_transcript:{request.video_id}:{request.language}:{request.game_type}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        generator = ContentGenerator(session)

        # Получаем транскрипт из кэша или YouTube
        transcript_key = f"transcript:{request.video_id}:{request.language}"
        transcript = await cache.get_cached_data(transcript_key)

        if not transcript:
            transcript = await generator.process_video_transcript(
                video_id=request.video_id,
                subtitle_language=request.language,
                use_cache=False,
                force_queue=False
            )
            await cache.cache_data(transcript_key, transcript, ttl=86400)

        # Форматируем промпт с текстом транскрипта
        # Fixed: call format_prompt function correctly, not as a coroutine
        formatted_prompt = format_prompt(
            request.model_dump(),
            "games_from_transcript",
            transcript
        )

        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=current_user.id,  # Используем ID из current_user
            content_type=ContentType.GAME,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': request.with_points}  # Передаем with_points через extra_params
        )

        response_data = {
            "id": 1,
            "user_id": current_user.id,  # Используем ID из current_user
            "type": "games",
            "content": content,
            "video_id": request.video_id,
            "created_at": datetime.now().isoformat()
        }

        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=current_user.id,  # Используем ID из current_user
            action_type="generation",
            content_type=ContentType.GAME.value,
            extra_data={"transcript_id": request.transcript_id, "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        await session.commit()

        # cache the result
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Games generated successfully"
        })

        return ContentResponse(
            status="success",
            data=response_data,
            message="Games generated successfully"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating games: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Modified: Changed from async def to regular def
def format_prompt(data: dict, prompt_type: str, transcript: str = None) -> str:
    """
    Форматирует промпт для генерации контента в зависимости от типа
    """
    # Общие инструкции для форматирования
    lesson_format_instructions = """
    Format your response in Markdown. Use headers, lists, and emphasis where appropriate.
    """

    # Инструкции для ревизии
    revision_instructions = ""
    if data.get('revision', False):
        revision_instructions = """
        This is a revision lesson. Focus on reviewing previously learned material.
        """

    # Инструкции для онлайн/оффлайн формата
    online_offline_instructions = ""
    if data.get('online_offline', '').lower() == 'online':
        online_offline_instructions = """
        This is for an online lesson. Include activities suitable for video conferencing platforms.
        """
    elif data.get('online_offline', '').lower() == 'offline':
        online_offline_instructions = """
        This is for an in-person lesson. Include activities that require physical presence.
        """

    # Инструкции для экзаменационной подготовки
    exam_instructions = ""
    exam_value = data.get('exam', '')
    if isinstance(exam_value, str) and exam_value.strip() and exam_value.strip() != 'N/A':
        exam_specific_requirements = get_exam_specific_requirements(exam_value.strip())
        exam_instructions = f"""
        🎯 EXAM PREPARATION FOCUS: {exam_value.strip()}

        {exam_specific_requirements}

        MANDATORY EXAM INTEGRATION:
        - ALL activities must prepare students for {exam_value.strip()} format
        - Include {exam_value.strip()}-specific vocabulary and structures
        - Practice authentic {exam_value.strip()}-style tasks and question types
        - Focus on skills and competencies tested in {exam_value.strip()}
        - Provide {exam_value.strip()} strategies and time management techniques
        """

    # Инструкции для методологии
    methodology_instructions = ""
    methodology_value = data.get('methodology', '')
    if isinstance(methodology_value, str) and methodology_value.strip() and methodology_value.strip() != 'N/A':
        methodology_instructions = f"""
        Use {methodology_value.strip()} methodology for this lesson.
        """

    # Инструкции для типа упражнений
    exercise_type_instructions = ""
    exercise_type_value = data.get('exercise_type', '')
    if isinstance(exercise_type_value, str) and exercise_type_value.strip() and exercise_type_value.strip() != 'N/A':
        exercise_type_instructions = f"""
        Focus on {exercise_type_value.strip()} exercises.
        """

    # Инструкции для сложности
    difficulty_instructions = ""
    difficulty_value = data.get('difficulty', '')
    if isinstance(difficulty_value, str) and difficulty_value.strip() and difficulty_value.strip() != 'N/A':
        difficulty_instructions = f"""
        The difficulty level is {difficulty_value.strip()}.
        """

    # Инструкции для возрастной группы
    age_group_instructions = ""
    age_value = data.get('age', '')
    if isinstance(age_value, str) and age_value.strip() and age_value.strip() != 'N/A':
        age_group_instructions = f"""
        This is for {age_value.strip()} learners.
        """

    # Инструкции для типа игры
    game_type_instructions = ""
    game_type_value = data.get('game_type', '')
    if isinstance(game_type_value, str) and game_type_value.strip() and game_type_value.strip() != 'N/A':
        game_type_instructions = f"""
        Create a {game_type_value.strip()} game.
        """

    # Форматирование промпта в зависимости от типа
    if prompt_type == "lesson_plan":
        # Получаем стадии урока в зависимости от методологии
        lesson_stages = get_lesson_stages(data.get('methodology', ''))

        # Инструкции для фокуса урока
        focus_instructions = ""
        lesson_focus = data.get('focus', '')
        if isinstance(lesson_focus, str) and lesson_focus.strip() and lesson_focus.strip() != 'mixed':
            focus_map = {
                'grammar': "Focus on grammar teaching and practice. Include clear grammar explanations and structured practice activities.",
                'vocabulary': "Focus on vocabulary acquisition and practice. Include word lists, semantic grouping, and vocabulary practice activities.",
                'speaking': "Focus on speaking skills development. Include conversation practice, role-plays, and discussion activities.",
                'listening': "Focus on listening skills development. Include listening comprehension activities and audio-based exercises.",
                'reading': "Focus on reading skills development. Include reading comprehension activities and text analysis.",
                'writing': "Focus on writing skills development. Include writing practice, text structure analysis, and feedback techniques."
            }
            focus_instructions = focus_map.get(lesson_focus.strip(), "")

        # Инструкции для уровня сложности
        level_instructions = ""
        lesson_level = data.get('level', '')
        if isinstance(lesson_level, str) and lesson_level.strip():
            level_map = {
                'beginner': "This lesson is for beginners (A1 level). Use simple language, basic vocabulary, and focus on fundamental concepts.",
                'elementary': "This lesson is for elementary students (A2 level). Use straightforward language and gradually introduce more complex structures.",
                'intermediate': "This lesson is for intermediate students (B1 level). Use moderately complex language and introduce more advanced concepts.",
                'upper_intermediate': "This lesson is for upper-intermediate students (B2 level). Use more complex language and challenging activities.",
                'advanced': "This lesson is for advanced students (C1 level). Use sophisticated language and complex concepts.",
                'proficient': "This lesson is for proficient students (C2 level). Use native-like language and highly complex concepts."
            }
            level_instructions = level_map.get(lesson_level.strip(), "")

        # Инструкции для продолжительности урока
        duration_instructions = ""
        lesson_duration = data.get('duration', '')
        if lesson_duration:
            # Проверяем тип данных перед вызовом strip()
            if isinstance(lesson_duration, (int, float)):
                # Если это число, преобразуем его в строку
                duration_instructions = f"""
                This lesson should be designed for a {lesson_duration}-minute class.
                Include a detailed timeline for each activity.
                """
            elif isinstance(lesson_duration, str) and lesson_duration.strip():
                # Если это строка и она не пустая после удаления пробелов
                duration_instructions = f"""
                This lesson should be designed for a {lesson_duration.strip()}-minute class.
                Include a detailed timeline for each activity.
                """

        # Извлекаем текст для генерации (тему)
        content_text = ""
        # Сначала проверяем text_content
        if 'text_content' in data and data['text_content'] and isinstance(data['text_content'], str) and data['text_content'].strip():
            content_text = data['text_content'].strip()
            logger.info(f"Используем text_content для плана урока: {content_text[:100]}...")
        # Если text_content не задан, используем topic
        elif 'topic' in data and data['topic'] and isinstance(data['topic'], str) and data['topic'].strip():
            content_text = data['topic'].strip()
            logger.info(f"Используем topic для плана урока: {content_text[:100]}...")
        else:
            logger.warning("Ни text_content, ни topic не заданы для плана урока!")

        formatted_prompt = f"""
        {lesson_format_instructions}
        {revision_instructions}
        {online_offline_instructions}
        {exam_instructions}
        {methodology_instructions}
        {age_group_instructions}
        {focus_instructions}
        {level_instructions}
        {duration_instructions}

        Create a detailed lesson plan for teaching {data.get('language', 'English')} with the topic: {content_text}

        Your lesson plan should include:

        1. Lesson Title
        2. Lesson Objectives (what students will learn)
        3. Target Language (key vocabulary and grammar)
        4. Required Materials
        5. Lesson Structure:
           {lesson_stages}
        6. Homework Assignment (if appropriate)
        7. Assessment Criteria

        Make sure the lesson is appropriate for {data.get('age', 'adult')} learners and follows a logical progression.
        Focus on the topic: {content_text}
        Include specific activities, questions, and examples related to the topic.
        Provide clear instructions for each activity.

        {lesson_format_instructions}
        """

        # Отладочный вывод
        logger.info(f"Сформирован промпт для плана урока длиной {len(formatted_prompt)} символов")

        return formatted_prompt
    elif prompt_type == "exercise":
        # Форматируем промпт для генерации упражнений с улучшенной обработкой уровней
        # Определяем количество упражнений
        count = data.get('count', 5)

        # Определяем тип упражнений
        exercise_type = data.get('exercise_type', 'mixed')

        # Определяем формат упражнений
        exercise_format = data.get('format', 'mixed')

        # Определяем язык
        language = data.get('language', 'English')

        # Получаем уровень владения языком
        proficiency = data.get('proficiency', 'intermediate')

        # Получаем детальные инструкции для уровня
        level_instruction = _get_detailed_level_instruction(proficiency)

        # Получаем текст и ограничиваем его длину, если он слишком длинный
        text_content = data.get('text_content', '')
        max_text_length = 5000  # Максимальная длина текста для упражнений

        if len(text_content) > max_text_length:
            # Если текст слишком длинный, обрезаем его и добавляем примечание
            text_content = text_content[:max_text_length] + "\n\n[Текст был сокращен из-за большой длины. Упражнения будут созданы на основе первой части текста.]"
            logger.info(f"Text for exercise generation was truncated from {len(data.get('text_content', ''))} to {max_text_length} characters")

        # Создаем инструкции для типа упражнений
        exercise_type_instruction = ""
        if exercise_type == "vocabulary":
            exercise_type_instruction = """
            [VOCABULARY EXERCISES] Create exercises that:
            - Focus on key vocabulary from the text
            - Include word meaning, usage, and collocations
            - Provide context for vocabulary items
            - Include a variety of vocabulary practice activities
            - Help students remember and use new words
            """
        elif exercise_type == "grammar":
            exercise_type_instruction = """
            [GRAMMAR EXERCISES] Create exercises that:
            - Focus on specific grammar structures from the text
            - Include form, meaning, and use explanations
            - Provide controlled practice opportunities
            - Progress from guided to free production
            - Include error correction activities
            """
        elif exercise_type == "reading":
            exercise_type_instruction = """
            [READING EXERCISES] Create exercises that:
            - Focus on reading comprehension
            - Include pre-reading, while-reading, and post-reading activities
            - Address different reading skills (skimming, scanning, intensive reading)
            - Include questions about main ideas, details, and inferences
            - Encourage critical thinking about the text
            """
        else:  # mixed
            exercise_type_instruction = """
            [MIXED EXERCISES] Create a variety of exercises that:
            - Address vocabulary, grammar, and comprehension
            - Include different exercise types and formats
            - Provide a balanced approach to language learning
            - Progress from easier to more challenging tasks
            - Cover different aspects of the text
            """

        # Создаем инструкции для формата упражнений
        format_instruction = ""
        if exercise_format == "matching":
            format_instruction = """
            Include matching exercises where students connect:
            - Words with definitions
            - Sentence halves
            - Questions with answers
            - Concepts with examples
            """
        elif exercise_format == "gap-fill":
            format_instruction = """
            Include gap-fill exercises where students:
            - Complete sentences with appropriate words
            - Fill in missing words in a text
            - Use specific vocabulary or grammar structures
            - Apply their understanding of the context

            IMPORTANT: For gap-fill exercises, use short underscores (like "_____") or numbered blanks (like "(1)") to indicate gaps.
            DO NOT use long lines of underscores. Each gap should be 5-10 underscores maximum.
            """
        elif exercise_format == "word-definition":
            format_instruction = """
            Include word-definition exercises where students:
            - Match words with their definitions
            - Create definitions for given words
            - Find words based on definitions
            - Work with key vocabulary from the text
            """
        elif exercise_format == "mixed":
            format_instruction = """
            Include a variety of exercise formats:
            - Matching activities
            - Gap-fill exercises
            - Multiple choice questions
            - Short answer questions
            - Word-definition activities
            - Sentence transformation tasks

            IMPORTANT: For gap-fill exercises, use short underscores (like "_____") or numbered blanks (like "(1)") to indicate gaps.
            DO NOT use long lines of underscores. Each gap should be 5-10 underscores maximum.
            """

        formatted_prompt = f"""
        {lesson_format_instructions}

        {level_instruction}

        {exercise_type_instruction}

        Create EXACTLY {count} COMPLETE and DETAILED exercises for {language} language learners based on the following text:

        ⚠️ IMPORTANT: Generate EXACTLY {count} exercises - no more, no less!

        {text_content}

        {format_instruction}

        CRITICAL REQUIREMENTS FOR EACH EXERCISE:
        1. **Exercise Title** - Clear, descriptive title (e.g., "Exercise 1: Vocabulary Practice")
        2. **Learning Objectives** - What students will achieve
        3. **Step-by-Step Instructions** - Detailed student instructions
        4. **Complete Exercise Content** - Full tasks, not just descriptions
        5. **Worked Examples** - Show students exactly what to do
        6. **Answer Keys** - Complete solutions with explanations
        7. **Teacher Notes** - Implementation tips and common mistakes to watch for

        FORMATTING GUIDELINES:
        - Number each exercise clearly: "Exercise 1:", "Exercise 2:", etc.
        - Use clear and consistent formatting for all exercises
        - For gap-fill exercises, use short underscores (like "_____") or numbered blanks (like "(1)") to indicate gaps
        - Each gap should be 5-10 underscores maximum, NEVER use long lines of underscores
        - For matching exercises, use clear tables or numbered lists
        - For multiple choice questions, use letters (a, b, c, d) for options
        - Ensure all exercises are properly numbered and have clear sections
        - Separate each exercise with clear dividers

        QUANTITY CONTROL:
        - You must create EXACTLY {count} exercises
        - Count your exercises before finishing
        - If you have fewer than {count}, add more
        - If you have more than {count}, remove the extras

        QUALITY STANDARDS:
        - Each exercise must be COMPLETE and READY TO USE
        - Include specific examples, not general descriptions
        - Provide enough content for meaningful practice
        - Ensure exercises build on each other logically
        - Make instructions crystal clear for students

        {lesson_format_instructions}
        """
        return formatted_prompt
    elif prompt_type == "game":
        # Форматируем промпт для генерации игры
        format_instruction = ""
        individual_group = data.get('individual_group', 'individual')
        if individual_group == 'individual':
            format_instruction = "This game should be designed for individual play (one student with a teacher)."
        elif individual_group == 'group':
            format_instruction = "This game should be designed for group play (multiple students)."

        # Инструкции для возрастной группы
        age_instruction = ""
        if data.get('age'):
            age_instruction = f"This game is for {data.get('age')} learners."

        # Инструкции для онлайн/оффлайн формата
        online_offline_instruction = ""
        online_offline = data.get('online_offline', 'online')
        if online_offline == 'online':
            online_offline_instruction = "This game should be designed for online learning environment (video call, web-based tools)."
        elif online_offline == 'offline':
            online_offline_instruction = "This game should be designed for in-person classroom environment."

        # Инструкции для продолжительности
        duration_instruction = ""
        duration = data.get('duration')
        if duration:
            duration_instruction = f"This game should take approximately {duration} minutes to play."

        # Инструкции для уровня сложности
        level_instruction = ""
        level = data.get('level', '')
        if level:
            level_map = {
                'beginner': "beginner (A1) level",
                'elementary': "elementary (A2) level",
                'intermediate': "intermediate (B1) level",
                'upper_intermediate': "upper intermediate (B2) level",
                'advanced': "advanced (C1) level",
                'proficiency': "proficiency (C2) level"
            }
            level_text = level_map.get(level, level)
            level_instruction = f"This game is designed for {level_text} students."

        # Инструкции для типа игры
        game_type = data.get('game_type', 'quiz')

        # Тема для игры
        topic = data.get('topic', '')

        # Язык
        language = data.get('language', 'English')

        formatted_prompt = f"""
        {lesson_format_instructions}

        Create a {game_type} game for {language} language learners with the topic: {topic}

        {format_instruction}
        {online_offline_instruction}
        {age_instruction}
        {level_instruction}
        {duration_instruction}
        {game_type_instructions}

        The game should:
        1. Be engaging and interactive
        2. Focus on language learning related to the topic: {topic}
        3. Be appropriate for the specified level and format
        4. Include clear instructions and rules
        5. Specify required materials
        6. Include a scoring system if applicable

        Include:
        - Game title
        - Required materials
        - Setup instructions
        - Game rules
        - Scoring system (if applicable)
        - Variations (optional)

        {lesson_format_instructions}
        """
        return formatted_prompt
    elif prompt_type == "detect_level":
        # ... existing code ...
        pass
    elif prompt_type == "regenerate_text":
        # ... existing code ...
        pass
    elif prompt_type == "exercises_from_transcript":
        # Форматируем промпт для генерации упражнений из транскрипта
        # Ограничиваем длину транскрипта
        max_transcript_length = 5000  # Максимальная длина транскрипта для упражнений

        if transcript and len(transcript) > max_transcript_length:
            # Если транскрипт слишком длинный, обрезаем его и добавляем примечание
            transcript = transcript[:max_transcript_length] + "\n\n[Транскрипт был сокращен из-за большой длины. Упражнения будут созданы на основе первой части транскрипта.]"
            logger.info(f"Transcript for exercise generation was truncated to {max_transcript_length} characters")

        # Определяем тип упражнений
        exercise_type = data.get('exercise_type', 'mixed')

        # Определяем сложность
        difficulty = data.get('difficulty', 'intermediate')

        # Определяем язык
        language = data.get('language', 'English')

        # Создаем инструкции для типа упражнений
        exercise_type_instruction = ""
        if exercise_type == "vocabulary":
            exercise_type_instruction = """
            [VOCABULARY EXERCISES] Create exercises that:
            - Focus on key vocabulary from the transcript
            - Include word meaning, usage, and collocations
            - Provide context for vocabulary items
            - Include a variety of vocabulary practice activities
            - Help students remember and use new words
            """
        elif exercise_type == "grammar":
            exercise_type_instruction = """
            [GRAMMAR EXERCISES] Create exercises that:
            - Focus on specific grammar structures from the transcript
            - Include form, meaning, and use explanations
            - Provide controlled practice opportunities
            - Progress from guided to free production
            - Include error correction activities
            """
        elif exercise_type == "listening":
            exercise_type_instruction = """
            [LISTENING EXERCISES] Create exercises that:
            - Focus on listening comprehension
            - Include pre-listening, while-listening, and post-listening activities
            - Address different listening skills (gist, detail, inference)
            - Include questions about main ideas, details, and inferences
            - Encourage critical thinking about the content
            """
        else:  # mixed
            exercise_type_instruction = """
            [MIXED EXERCISES] Create a variety of exercises that:
            - Address vocabulary, grammar, and comprehension
            - Include different exercise types and formats
            - Provide a balanced approach to language learning
            - Progress from easier to more challenging tasks
            - Cover different aspects of the transcript
            """

        # Создаем инструкции для сложности
        difficulty_instruction = ""
        if difficulty == "beginner":
            difficulty_instruction = """
            Create exercises for BEGINNER level students (A1-A2):
            - Use simple language and basic vocabulary
            - Focus on fundamental concepts
            - Provide clear examples and guidance
            - Keep tasks straightforward and accessible
            """
        elif difficulty == "intermediate":
            difficulty_instruction = """
            Create exercises for INTERMEDIATE level students (B1-B2):
            - Use moderately complex language
            - Include more advanced concepts
            - Provide some examples but expect more independent work
            - Include a mix of straightforward and challenging tasks
            """
        elif difficulty == "advanced":
            difficulty_instruction = """
            Create exercises for ADVANCED level students (C1-C2):
            - Use sophisticated language and complex concepts
            - Expect high level of language proficiency
            - Focus on nuance and precision in language use
            - Include challenging and complex tasks
            """

        formatted_prompt = f"""
        {lesson_format_instructions}

        {exercise_type_instruction}

        {difficulty_instruction}

        Please create 5 exercises for {language} language learners based on the following transcript:

        {transcript}

        For each exercise, please provide:
        1. Clear instructions
        2. Example question with answer (where appropriate)
        3. Exercise questions
        4. Answer key

        FORMATTING GUIDELINES:
        - Use clear and consistent formatting for all exercises
        - For gap-fill exercises, use short underscores (like "_____") or numbered blanks (like "(1)") to indicate gaps
        - Each gap should be 5-10 underscores maximum, NEVER use long lines of underscores
        - For matching exercises, use clear tables or numbered lists
        - For multiple choice questions, use letters (a, b, c, d) for options
        - Ensure all exercises are properly numbered and have clear sections

        {lesson_format_instructions}
        """
        return formatted_prompt
    elif prompt_type == "games_from_transcript":
        # Форматируем промпт для генерации игр из транскрипта
        # Ограничиваем длину транскрипта
        max_transcript_length = 5000  # Максимальная длина транскрипта для игр

        if transcript and len(transcript) > max_transcript_length:
            # Если транскрипт слишком длинный, обрезаем его и добавляем примечание
            transcript = transcript[:max_transcript_length] + "\n\n[Транскрипт был сокращен из-за большой длины. Игры будут созданы на основе первой части транскрипта.]"
            logger.info(f"Transcript for game generation was truncated to {max_transcript_length} characters")

        # Определяем тип игры
        game_type = data.get('game_type', 'vocabulary')

        # Определяем язык
        language = data.get('language', 'English')

        # Инструкции для типа игры
        game_type_instruction = ""
        if game_type == "vocabulary":
            game_type_instruction = """
            Create a VOCABULARY game that:
            - Focuses on key vocabulary from the transcript
            - Helps students learn and remember new words
            - Is engaging and interactive
            - Can be played in a classroom setting
            """
        elif game_type == "grammar":
            game_type_instruction = """
            Create a GRAMMAR game that:
            - Focuses on grammar structures from the transcript
            - Helps students practice using correct grammar
            - Is engaging and interactive
            - Can be played in a classroom setting
            """
        elif game_type == "conversation":
            game_type_instruction = """
            Create a CONVERSATION game that:
            - Encourages students to speak and interact
            - Uses themes and content from the transcript
            - Develops speaking and listening skills
            - Is engaging and interactive
            - Can be played in a classroom setting
            """
        else:  # mixed
            game_type_instruction = """
            Create a MIXED game that:
            - Incorporates vocabulary, grammar, and conversation elements
            - Uses content from the transcript
            - Develops multiple language skills
            - Is engaging and interactive
            - Can be played in a classroom setting
            """

        formatted_prompt = f"""
        {lesson_format_instructions}

        {game_type_instruction}

        Create a language learning game for {language} students based on the following transcript:

        {transcript}

        Include:
        - Game title
        - Required materials
        - Setup instructions
        - Game rules
        - Scoring system (if applicable)
        - Variations (optional)

        {lesson_format_instructions}
        """
        return formatted_prompt
    elif prompt_type == "change_level":
        # Добавляем инструкции для сохранения стиля
        preserve_style_instructions = ""
        if data.get('preserve_style', True):
            preserve_style_instructions = """
            IMPORTANT: Preserve the original style, tone, and structure of the text as much as possible.
            Keep the same paragraph structure, sentence patterns, and stylistic elements.
            Only change what is necessary to adjust the language level.
            """
        else:
            preserve_style_instructions = """
            You may restructure the text as needed to match the target level.
            Feel free to change sentence structures, vocabulary, and organization to best fit the target level.
            """

        formatted_prompt = f"""
        {lesson_format_instructions}

        Please adapt the following text to {data.get('target_level', 'Intermediate')} level of {data.get('language', 'English')}.

        {preserve_style_instructions}

        When adapting the text:
        1. Adjust vocabulary complexity to match the target level
        2. Modify sentence structures as appropriate for the level
        3. Maintain the original meaning and key information
        4. Ensure the text remains coherent and natural

        Original text:
        {data.get('text_content', '')}

        {lesson_format_instructions}
        """
        return formatted_prompt

def _get_detailed_level_instruction(proficiency: str) -> str:
    """Get detailed CEFR level-specific instructions for exercise generation"""

    # Нормализуем уровень
    proficiency_lower = proficiency.lower()

    # Маппинг различных форматов уровней к стандартным CEFR
    level_mapping = {
        'beginner': 'a1',
        'elementary': 'a2',
        'pre-intermediate': 'a2',
        'intermediate': 'b1',
        'upper-intermediate': 'b2',
        'upper_intermediate': 'b2',
        'advanced': 'c1',
        'proficiency': 'c2',
        'a1': 'a1',
        'a2': 'a2',
        'b1': 'b1',
        'b2': 'b2',
        'c1': 'c1',
        'c2': 'c2'
    }

    cefr_level = level_mapping.get(proficiency_lower, 'b1')

    level_instructions = {
        'a1': """
LEVEL: A1 (BEGINNER) - EXERCISE REQUIREMENTS:

VOCABULARY & LANGUAGE:
- Use only basic, high-frequency words (family, numbers, colors, food)
- Provide clear definitions for any new words
- Use simple present tense and basic structures
- Keep sentences short (max 8 words)

EXERCISE DESIGN:
- Single-step tasks only
- Lots of visual support and examples
- Yes/No and multiple choice questions
- Simple matching exercises
- Basic gap-fill with word banks
        """,

        'a2': """
LEVEL: A2 (ELEMENTARY) - EXERCISE REQUIREMENTS:

VOCABULARY & LANGUAGE:
- 1000-2000 common words
- Basic past and future tenses
- Simple connectors (and, but, because)
- Clear, simple instructions

EXERCISE DESIGN:
- Two-step tasks maximum
- Gap-fill with word banks
- Simple sentence transformation
- Basic reading comprehension
- Short dialogues and role-plays
        """,

        'b1': """
LEVEL: B1 (INTERMEDIATE) - EXERCISE REQUIREMENTS:

VOCABULARY & LANGUAGE:
- 2000-3000 words including abstract concepts
- All major tenses and aspects
- Basic phrasal verbs and idioms
- Complex sentence structures

EXERCISE DESIGN:
- Multi-step tasks requiring planning
- Text analysis and inference
- Opinion-based discussions
- Problem-solving activities
- Creative writing with structure
        """,

        'b2': """
LEVEL: B2 (UPPER-INTERMEDIATE) - EXERCISE REQUIREMENTS:

VOCABULARY & LANGUAGE:
- 3000-4000 words including specialized terms
- Advanced grammar and passive voice
- Sophisticated linking devices
- Academic vocabulary

EXERCISE DESIGN:
- Extended tasks requiring sustained effort
- Critical thinking activities
- Debate and argumentation
- Research-based projects
- Complex listening and reading
        """,

        'c1': """
LEVEL: C1 (ADVANCED) - EXERCISE REQUIREMENTS:

VOCABULARY & LANGUAGE:
- 4000+ words including specialized terminology
- Mastery of all grammatical structures
- Sophisticated idiomatic expressions
- Academic and professional register

EXERCISE DESIGN:
- Extended, autonomous tasks
- Abstract and theoretical concepts
- Independent research and analysis
- Creative and academic writing
- Complex authentic materials
        """,

        'c2': """
LEVEL: C2 (PROFICIENCY) - EXERCISE REQUIREMENTS:

VOCABULARY & LANGUAGE:
- Near-native vocabulary range
- Subtle nuances and connotations
- Literary and archaic expressions
- Native-like control of structures

EXERCISE DESIGN:
- Highly complex, authentic tasks
- Abstract reasoning and analysis
- Sophisticated communication skills
- Cultural and literary analysis
- Professional contexts
        """
    }

    return level_instructions.get(cefr_level, level_instructions['b1'])

def format_questions_to_markdown(questions: List[Dict[str, Any]], language: str) -> str:
    """
    Форматирует вопросы в текстовый формат Markdown с HTML-разметкой для лучшего отображения на фронтенде.

    Args:
        questions: Список вопросов
        language: Язык вопросов

    Returns:
        str: Markdown-форматированный текст с вопросами
    """
    is_russian = language.lower() in ["russian", "русский", "ru"]

    # Заголовок с соответствующей локализацией
    questions_text = f"# {('Вопросы по тексту' if is_russian else 'Questions about the text')}\n\n---\n\n"

    # Функция для очистки текста от всех технических элементов
    def clean_text(text):
        if not text:
            return ""

        # Преобразуем в строку, если это не строка
        text = str(text)

        # Удаляем экранированные символы
        text = text.replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ').replace('\\', '')

        # Удаляем Markdown разметку
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # Удаляем JSON и технические строки
        text = re.sub(r'"meta":[^}]*}', '', text, flags=re.DOTALL)
        text = re.sub(r'"[^"]*":[^,]*,', '', text, flags=re.DOTALL)
        text = re.sub(r',"[^"]*":[^}]*', '', text, flags=re.DOTALL)
        text = re.sub(r'{[^}]*}', '', text, flags=re.DOTALL)
        text = re.sub(r'\[[^\]]*\]', '', text, flags=re.DOTALL)

        # Удаляем любые оставшиеся фрагменты JSON
        text = re.sub(r'":"', ' ', text)
        text = re.sub(r'","', ' ', text)
        text = re.sub(r'":', ' ', text)
        text = re.sub(r'",', ' ', text)
        text = re.sub(r'{"', ' ', text)
        text = re.sub(r'"}', ' ', text)
        text = re.sub(r'[\[\]{}"]', '', text)

        # Удаляем специальные ключевые слова JSON
        keywords = ['meta', 'language', 'count', 'difficulty', 'questions', 'markdown_content',
                   'options', 'answer', 'number', 'question', 'english', 'russian', 'spanish', 'french']
        for keyword in keywords:
            text = re.sub(rf'\b{keyword}\b', '', text)

        # Удаляем лишние пробелы и символы
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    for i, q in enumerate(questions, 1):
        # Получаем номер вопроса
        question_number = q.get('number', i)

        # Очищаем текст вопроса от всех технических элементов
        question_text = clean_text(q.get('question', 'Вопрос отсутствует' if is_russian else 'Question missing'))

        # Проверяем наличие знака вопроса в конце вопроса
        if question_text and not question_text.endswith('?') and not question_text.endswith('.'):
            question_text += '?'

        # Специальное форматирование для номера вопроса (применяем розовый цвет)
        question_label = "Вопрос" if is_russian else "Question"
        questions_text += f"<span style='color: #ff6b9a; font-weight: bold;'>{question_label} {question_number}:</span> {question_text}\n\n"

        # Добавляем варианты ответов, если они есть
        options = q.get('options', [])
        clean_options = []

        # Очищаем варианты ответов от всех технических элементов
        for opt in options:
            clean_opt = clean_text(opt)
            if clean_opt:
                clean_options.append(clean_opt)

        # Получаем и очищаем правильный ответ
        correct_answer = clean_text(q.get('answer', ''))

        # Определяем правильный ответ
        correct_letter = None
        correct_option_text = None

        # Проверяем, содержит ли правильный ответ букву
        if correct_answer:
            letter_match = re.match(r'([A-D])\.?\s*(.*)', correct_answer)
            if letter_match:
                correct_letter = letter_match.group(1)
                correct_option_text = letter_match.group(2).strip()

        # Если буква не найдена, ищем по содержимому
        if not correct_letter and correct_answer and clean_options:
            for j, opt_text in enumerate(clean_options):
                if correct_answer and (correct_answer.lower() in opt_text.lower() or opt_text.lower() in correct_answer.lower()):
                    correct_letter = chr(65 + j)  # A, B, C, D...
                    correct_option_text = opt_text
                    break

        if clean_options:
            options_label = "Варианты ответов:" if is_russian else "Options:"
            questions_text += f"<span style='color: #ff6b9a; font-weight: bold;'>{options_label}</span>\n\n"

            # Выводим варианты ответов
            for j, opt_text in enumerate(clean_options):
                letter = chr(65 + j)  # A, B, C, D...

                # Отмечаем правильный ответ с галочкой и стилями
                circle_color = "#ff6b9a"  # розовый для всех вариантов
                check_mark = ""
                option_style = ""

                if correct_letter and letter == correct_letter:
                    check_mark = "✓ "
                    circle_color = "#4CAF50"  # зеленый для правильного
                    option_style = " <span style='background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8em;'>Правильный</span>"

                questions_text += f"<div style='margin-bottom: 10px;'><span style='background-color: {circle_color}; color: white; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 10px;'>{letter}</span> {check_mark}{opt_text}{option_style}</div>\n\n"

        # Добавляем правильный ответ в отдельной секции с розовым фоном
        if correct_letter and correct_option_text:
            answer_label = "Правильный ответ:" if is_russian else "Correct answer:"
            questions_text += f"<div style='background-color: #f8ecf0; padding: 10px; border-radius: 5px; margin: 10px 0;'><span style='color: #ff6b9a; font-weight: bold;'>{answer_label}</span> {correct_letter}. {check_mark}{correct_option_text}</div>\n\n"
        elif correct_answer:
            answer_label = "Правильный ответ:" if is_russian else "Correct answer:"
            questions_text += f"<div style='background-color: #f8ecf0; padding: 10px; border-radius: 5px; margin: 10px 0;'><span style='color: #ff6b9a; font-weight: bold;'>{answer_label}</span> {correct_answer}</div>\n\n"

        # Добавляем разделитель между вопросами, если это не последний вопрос
        if i < len(questions):
            questions_text += "---\n\n"

    # Финальная очистка всего текста от любых оставшихся специальных символов и экранированных строк
    questions_text = re.sub(r'\\n|\\r|\\t', ' ', questions_text)

    # Удаляем все возможные фрагменты JSON
    json_fragments = [
        r'","|":"|":{"|":\["|"\]"|"{"|"}"|"meta"|"language"|"count"|"difficulty"|"questions"|"markdown_content"',
        r'"options"|"answer"|"number"|"question"|"english"|"russian"|"spanish"|"french"',
        r'":"|","|"{\s*"|"\s*}"|"\s*\["|"\s*\]"',
        r'"\w+":',
        r',"[\w\s]+":',
        r'},"[\w\s]+":',
        r'"[\w\s]+":',
        r':"[\w\s]+"'
    ]

    for pattern in json_fragments:
        questions_text = re.sub(pattern, ' ', questions_text)

    # Удаляем экранированные обратные слеши и повторяющиеся пробелы
    questions_text = re.sub(r'\\{2,}', '', questions_text)
    questions_text = re.sub(r'\s+', ' ', questions_text)

    return questions_text.strip()


@router.post("/generate_questions", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_questions(
    request: GenerateQuestionsRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Генерирует вопросы к тексту"""
    try:
        # Проверяем кэш
        cache_key = f"questions:{request.language}:{hash(request.text_content)}:{request.count}"
        if not request.force:
            cached_content = await cache.get_cached_data(cache_key)
            if cached_content:
                logger.info(f"Using cached questions for user {request.user_id}")
                return ContentResponse(**cached_content)

        # Создаем генератор контента
        async with ContentGenerator(session) as generator:
            # Генерируем вопросы
            questions_analysis = await generator.generate_questions(
                text=request.text_content,
                language=request.language,
                num_questions=request.count,
                vocabulary=request.vocabulary,
                grammar=request.grammar,
                user_id=request.user_id,
                topic=request.topic,
                difficulty=request.difficulty,
                force=request.force
            )

            # Преобразуем результат в словарь
            questions_data = questions_analysis.to_dict()

            # Функция для глубокой очистки текста от JSON и технических фрагментов
            def deep_clean_text(text):
                if not text:
                    return ""

                # Преобразуем в строку
                text = str(text)

                # Удаляем экранированные символы
                text = re.sub(r'\\[nrt]', ' ', text)
                text = re.sub(r'\\{2,}', '', text)

                # Удаляем JSON фрагменты
                json_patterns = [
                    r'"meta":\s*{[^}]*}',
                    r'"language":\s*"[^"]*"',
                    r'"count":\s*\d+',
                    r'"difficulty":\s*"[^"]*"',
                    r'"questions":\s*\[[^\]]*\]',
                    r'"markdown_content":\s*"[^"]*"',
                    r'"options":\s*\[[^\]]*\]',
                    r'"answer":\s*"[^"]*"',
                    r'"number":\s*\d+',
                    r'"question":\s*"[^"]*"',
                    r'"[^"]*":\s*',
                    r'"[^"]*"\s*:'
                ]

                for pattern in json_patterns:
                    text = re.sub(pattern, '', text)

                # Удаляем JSON символы
                text = re.sub(r'[{}\[\]"]', '', text)
                text = re.sub(r',(\s*,)+', ',', text)
                text = re.sub(r'^\s*,|,\s*$', '', text)

                # Удаляем JSON ключевые слова
                keywords = ['meta', 'language', 'count', 'difficulty', 'questions',
                           'markdown_content', 'options', 'answer', 'number', 'question',
                           'english', 'russian', 'spanish', 'french']
                for kw in keywords:
                    text = re.sub(rf'\b{kw}\b', '', text, flags=re.IGNORECASE)

                # Удаляем лишние пробелы
                text = re.sub(r'\s+', ' ', text)

                return text.strip()

            # Очищаем вопросы от JSON фрагментов
            for q in questions_data["questions"]:
                if "question" in q:
                    q["question"] = deep_clean_text(q["question"])

                if "answer" in q:
                    q["answer"] = deep_clean_text(q["answer"])

                if "options" in q:
                    q["options"] = [deep_clean_text(opt) for opt in q["options"]]

            # Форматируем вопросы в текстовый формат
            questions_markdown = format_questions_to_markdown(questions_data["questions"], request.language)

            # Финальная очистка отформатированного текста
            questions_markdown = deep_clean_text(questions_markdown)

            # Дополнительная очистка от JSON разделителей
            questions_markdown = re.sub(r'","', ' ', questions_markdown)
            questions_markdown = re.sub(r'":"', ' ', questions_markdown)
            questions_markdown = re.sub(r'":{"', ' ', questions_markdown)
            questions_markdown = re.sub(r'}}', '', questions_markdown)
            questions_markdown = re.sub(r'{{', '', questions_markdown)

            # Создаем полный ответ
            result = {
                "questions": questions_data["questions"],
                "markdown_content": questions_markdown,
                "meta": {
                    "language": request.language,
                    "count": len(questions_data["questions"]),
                    "difficulty": request.difficulty
                }
            }

            # Кэшируем результат
            await cache.cache_data(cache_key, {
                "status": "success",
                "data": result,
                "with_points": request.with_points
            })

            return ContentResponse(
                status="success",
                data=result,
                with_points=request.with_points
            )

    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )

@router.post("/generate_summary", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_summary(
    request: GenerateSummaryRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Генерация саммари текста"""
    # Логика выбора параметров
    level = request.level
    max_length = request.max_length

    if level:
        logger.info(f"Started generating summary with level: {level}, language: {request.language}")
        # При использовании уровня cache_key должен включать level вместо max_length
        cache_key = f"generate_summary:{request.user_id}:{hash(request.text_content)}:level_{level}:{request.language}"
    else:
        # Для обратной совместимости, если уровень не указан, используем max_length
        max_length = max_length or 200  # Значение по умолчанию, если не указан ни уровень, ни длина
        logger.info(f"Started generating summary with max length: {max_length}, language: {request.language}")
        cache_key = f"generate_summary:{request.user_id}:{hash(request.text_content)}:{max_length}:{request.language}"

    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Генерация саммари
        generator = ContentGenerator(session)
        if level:
            logger.info(f"Calling content generator for level-based summary generation in language: {request.language}, level: {level}...")
            summary = await generator.summarize_text(
                text=request.text_content,
                level=level,
                language=request.language,
                user_id=request.user_id
            )
        else:
            logger.info(f"Calling content generator for length-based summary generation in language: {request.language}, max_length: {max_length}...")
            summary = await generator.summarize_text(
                text=request.text_content,
                max_length=max_length,
                language=request.language,
                user_id=request.user_id
            )

        logger.info(f"Received summary (length: {len(summary)})")

        # Создаем ответ
        response_data = {
            "user_id": request.user_id,
            "language": request.language,
            "original_text": request.text_content,
            "summary": summary
        }

        # Добавляем информацию о параметрах (уровень или длина)
        if level:
            response_data["level"] = level
        if max_length:
            response_data["max_length"] = max_length

        # Логируем использование
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"action": "generate_summary", "level": level, "max_length": max_length}
        ))

        # Сохраняем в кэш
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Summary generated successfully"
        })

        logger.info("Summary generation completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Summary generated successfully"
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )

@router.post("/generate_summaries", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_summaries(
    request: GenerateSummaryRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Генерация резюме текста разной длины"""
    logger.info(f"Started generating multiple summaries for text in language: {request.language}")

    cache_key = f"generate_summaries:{request.user_id}:{hash(request.text_content)}:{request.language}"

    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Генерация резюме разной длины
        generator = ContentGenerator(session)
        logger.info(f"Calling content generator for multiple summaries generation in language: {request.language}...")

        # Проверяем, есть ли метод generate_summaries в генераторе
        if hasattr(generator, 'generate_summaries'):
            summaries = await generator.generate_summaries(
                text=request.text_content,
                language=request.language
            )
        else:
            # Если метода нет, используем summarize_text с разными уровнями
            # Для каждого языка выбираем подходящие уровни для трех резюме
            level_by_language = {
                "english": ["a1", "b1", "c1"],         # CEFR
                "spanish": ["a1", "b1", "c1"],         # CEFR
                "french": ["a1", "b1", "c1"],          # CEFR
                "german": ["a1", "b1", "c1"],          # CEFR
                "italian": ["a1", "b1", "c1"],         # CEFR
                "chinese": ["hsk1", "hsk3", "hsk5"],   # HSK
                "japanese": ["n5", "n3", "n1"],        # JLPT
                "korean": ["topik1", "topik3", "topik5"], # TOPIK
                "turkish": ["a1", "b1", "c1"],         # CEFR
                "russian": ["tea", "t1", "t3"],        # ТРКИ
                "arabic": ["beginner", "intermediate", "advanced"] # Общие уровни
            }

            # Получаем соответствующие уровни для выбранного языка
            levels = level_by_language.get(request.language.lower(), ["a1", "b1", "c1"])

            logger.info(f"Using levels {levels} for generating multiple summaries in {request.language}")

            brief_summary = await generator.summarize_text(
                text=request.text_content,
                level=levels[0],
                language=request.language
            )
            medium_summary = await generator.summarize_text(
                text=request.text_content,
                level=levels[1],
                language=request.language
            )
            detailed_summary = await generator.summarize_text(
                text=request.text_content,
                level=levels[2],
                language=request.language
            )

            # Адаптируем заголовки в зависимости от языка
            if request.language.lower() == 'english':
                summaries = f"""
# Text Summary

## Brief summary (Level {levels[0].upper()}):
{brief_summary}

## Medium summary (Level {levels[1].upper()}):
{medium_summary}

## Detailed summary (Level {levels[2].upper()}):
{detailed_summary}
"""
            else:
                summaries = f"""
# Резюме текста

## Краткое резюме (Уровень {levels[0].upper()}):
{brief_summary}

## Среднее резюме (Уровень {levels[1].upper()}):
{medium_summary}

## Подробное резюме (Уровень {levels[2].upper()}):
{detailed_summary}
"""

        # Создаем ответ
        response_data = {
            "user_id": request.user_id,
            "language": request.language,
            "original_text": request.text_content,
            "summaries": summaries
        }

        # Логируем использование
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"action": "generate_summaries"}
        ))

        # Сохраняем в кэш
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Summaries generated successfully",
            "with_points": request.with_points
        })

        logger.info("Multiple summaries generation completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Summaries generated successfully",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating summaries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summaries: {str(e)}"
        )

@router.post("/generate_titles", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_titles(
    request: GenerateTitlesRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Генерация заголовков для текста"""
    logger.info(f"Started generating {request.count} titles for text")

    # Проверяем кэш, если force не установлен
    if not request.force:
        cache_key = f"titles:{request.user_id}:{hash(request.text_content)}:{request.count}"
        cached_result = await cache.get_cached_data(cache_key)
        if cached_result:
            logger.info(f"Using cached titles from key: {cache_key}")
            return ContentResponse(**cached_result)
    else:
        logger.info(f"Force flag set or not available, skipping cache lookup")

    try:
        # Генерация заголовков
        generator = ContentGenerator(session)
        logger.info("Calling content generator for title generation...")
        titles_result = await generator.generate_titles(
            text=request.text_content,
            language=request.language,
            count=request.count,
            user_id=request.user_id
        )

        # Получаем данные из объекта TitlesAnalysis
        titles = titles_result.titles
        recommended_index = titles_result.recommended_index

        logger.info(f"Generated {len(titles)} titles with recommended index {recommended_index}")

        # Объединяем заголовки в текст для фронтенда, отмечая рекомендуемый заголовок
        formatted_titles = []
        for i, title in enumerate(titles):
            # Добавляем метку для рекомендуемого заголовка
            if i == recommended_index:
                formatted_titles.append(f"## <span style=\"color: #1e7e34; font-weight: bold; background-color: #f0fff0; padding: 4px 8px; border-radius: 4px; border-left: 4px solid #1e7e34;\">{i+1}. **{title}** ✓ (рекомендуемый)</span>")
            else:
                formatted_titles.append(f"## {i+1}. **{title}**")

        titles_markdown = "\n\n".join(formatted_titles)

        # Создаем ответ
        response_data = {
            "user_id": request.user_id,
            "language": request.language,
            "count": request.count,
            "titles": titles,
            "recommended_index": recommended_index,
            "titles_markdown": titles_markdown
        }

        # Логируем использование
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"action": "generate_titles", "count": request.count}
        ))

        # Сохраняем в кэш, если force не установлен
        if not request.force:
            logger.info(f"Caching titles with key: {cache_key}")
            await cache.cache_data(cache_key, {
                "status": "success",
                "data": response_data,
                "message": "Titles generated successfully",
                "with_points": request.with_points
            })

        return ContentResponse(
            status="success",
            data=response_data,
            message="Titles generated successfully",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error generating titles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating titles: {str(e)}"
        )

@router.post("/generate_comprehension_test", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_comprehension_test(
    request: GenerateComprehensionTestRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Генерирует тест на понимание текста с вопросами множественного выбора

    Args:
        request: Запрос на генерацию теста
        session: Сессия базы данных
        cache: Сервис кэширования

    Returns:
        ContentResponse: Ответ с тестом
    """
    logger.info(f"Запрос на генерацию теста на понимание текста для пользователя ID: {request.user_id}")

    # Создаем ключ кэша, зависящий от текста и параметров
    cache_key = f"comprehension_test:{request.user_id}:{hash(request.text_content)}:{request.question_count}:{request.difficulty}"

    # Проверяем, есть ли результат в кэше
    if not request.force:
        cached_result = await cache.get_cached_data(cache_key)
        if cached_result:
            logger.info(f"Возвращаем кэшированный тест для пользователя ID: {request.user_id}")
            return ContentResponse(**cached_result)

    async with ContentGenerator(session) as generator:
        try:
            test_content = await generator.generate_comprehension_test(
                text=request.text_content,
                language=request.language,
                question_count=request.question_count,
                difficulty=request.difficulty
            )

            # Создаем ответ
            result = {
                "content": test_content,
                "markdown_content": test_content,
                "user_id": request.user_id,
                "language": request.language
            }

            # Кэшируем результат
            await cache.cache_data(cache_key, {
                "status": "success",
                "message": "Тест на понимание текста успешно сгенерирован",
                "data": result,
                "with_points": request.with_points
            })

            logger.info(f"Тест на понимание текста успешно сгенерирован для пользователя ID: {request.user_id}")

            return ContentResponse(
                status="success",
                message="Тест на понимание текста успешно сгенерирован",
                data=result,
                with_points=request.with_points
            )

        except Exception as e:
            logger.error(f"Ошибка при генерации теста на понимание: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при генерации теста на понимание: {str(e)}"
            )

# Новая схема для ответа с информацией о статусе G4FHandler
class G4FStatusResponse(BaseModel):
    available: bool
    model: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None

# Новая схема для параметров обновления G4FHandler
class G4FUpdateParams(BaseModel):
    timeout: Optional[int] = None
    force_refresh: bool = False
    clear_cache: bool = False
    content_type: Optional[str] = None

# Endpoint для получения статуса G4FHandler
@router.get("/g4f/status", response_model=G4FStatusResponse)
async def get_g4f_status(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение статуса G4FHandler"""
    try:
        generator = ContentGenerator(session)
        model_info = await generator.g4f_handler.get_available_model()

        if model_info:
            model, provider = model_info
            return G4FStatusResponse(
                available=True,
                model=model,
                provider=provider.__name__ if provider else None
            )
        else:
            return G4FStatusResponse(
                available=False,
                error="No available models found"
            )
    except Exception as e:
        logger.error(f"Error getting G4F status: {str(e)}")
        return G4FStatusResponse(
            available=False,
            error=str(e)
        )

# Endpoint для управления G4FHandler
@router.post("/g4f/update", response_model=G4FStatusResponse)
async def update_g4f_handler(
    params: G4FUpdateParams,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    user: User = Depends(get_current_user)
):
    """
    Обновить параметры G4FHandler или переинициализировать его.
    Требуется права администратора.
    """
    try:
        # Проверяем права администратора
        if not await check_admin_rights(user.id, session):
            raise HTTPException(
                status_code=403,
                detail="Требуются права администратора"
            )

        generator = ContentGenerator(session=session)

        # Обновляем таймаут, если задан
        if params.timeout is not None:
            generator.set_generation_timeout(params.timeout)

        # Принудительно обновляем G4FHandler, если требуется
        if params.force_refresh:
            await generator.refresh_g4f_handler()

        # Очищаем кэш, если требуется
        if params.clear_cache:
            content_type = None
            if params.content_type:
                try:
                    content_type = ContentType(params.content_type)
                except ValueError:
                    logger.warning(f"Неизвестный тип контента: {params.content_type}")

            await generator.clear_content_cache(content_type)

        # Возвращаем текущий статус
        status = await generator.get_g4f_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка при обновлении G4FHandler: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении G4FHandler: {str(e)}")

# Эндпоинты для анализатора текста

@router.post("/detect_text_level", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def detect_text_level(
    request: DetectTextLevelRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Определение уровня текста"""
    logger.info("Started text level detection")

    cache_key = f"text_level:{request.user_id}:{hash(request.text_content)}:{request.language}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Генерация анализа
        generator = ContentGenerator(session)
        logger.info("Calling content generator for text level detection...")
        analysis_result = await generator.detect_text_level(
            text=request.text_content,
            language=request.language,
            user_id=request.user_id
        )

        # analysis_result теперь содержит объект TextLevelAnalysis
        # с атрибутами: markdown_content, level, raw_analysis

        logger.info(f"Received text level analysis with detected level: {analysis_result.level}")

        # Создаем ответ
        response_data = {
            "user_id": request.user_id,
            "language": request.language,
            "original_text": request.text_content,
            "content": analysis_result.markdown_content,
            "detected_level": analysis_result.level,
            "analysis_data": analysis_result.raw_analysis or {}
        }

        # Логируем использование
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"action": "detect_text_level", "language": request.language, "detected_level": analysis_result.level}
        ))

        # Сохраняем в кэш
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Text level detected successfully",
            "with_points": request.with_points
        })

        logger.info("Text level detection completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Text level detected successfully",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error detecting text level: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting text level: {str(e)}"
        )

@router.post("/regenerate_text", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def regenerate_text(
    request: RegenerateTextRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Перегенерация текста с заданным типом лексики"""
    logger.info(f"Started text regeneration with vocabulary type: {request.vocabulary}")

    cache_key = f"regenerate_text:{request.user_id}:{hash(request.text_content)}:{request.vocabulary}:{request.preserve_style}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Функция для глубокой очистки текста от JSON и технических фрагментов
        def deep_clean_text(text):
            if not text:
                return ""

            # Преобразуем в строку
            text = str(text)

            # Удаляем экранированные символы
            text = re.sub(r'\\[nrt]', ' ', text)
            text = re.sub(r'\\{2,}', '', text)

            # Удаляем JSON фрагменты
            json_patterns = [
                r'"meta":\s*{[^}]*}',
                r'"language":\s*"[^"]*"',
                r'"count":\s*\d+',
                r'"difficulty":\s*"[^"]*"',
                r'"vocabulary_type":\s*"[^"]*"',
                r'"preserve_style":\s*(?:true|false)',
                r'"original_text":\s*"[^"]*"',
                r'"regenerated_text":\s*"[^"]*"',
                r'"[^"]*":\s*',
                r'"[^"]*"\s*:'
            ]

            for pattern in json_patterns:
                text = re.sub(pattern, '', text)

            # Удаляем JSON символы
            text = re.sub(r'[{}\[\]"]', '', text)
            text = re.sub(r',(\s*,)+', ',', text)
            text = re.sub(r'^\s*,|,\s*$', '', text)

            # Удаляем JSON ключевые слова
            keywords = ['meta', 'language', 'vocabulary_type', 'preserve_style',
                        'original_text', 'regenerated_text', 'formal', 'informal',
                        'academic', 'slang', 'neutral']
            for kw in keywords:
                text = re.sub(rf'\b{kw}\b', '', text, flags=re.IGNORECASE)

            # Удаляем лишние пробелы
            text = re.sub(r'\s+', ' ', text)

            return text.strip()

        # Генерация текста
        generator = ContentGenerator(session)
        logger.info("Calling content generator for text regeneration...")
        regenerated_text = await generator.regenerate_text(
            text=request.text_content,
            language=request.language,
            vocabulary_type=request.vocabulary,
            preserve_style=request.preserve_style,
            user_id=request.user_id
        )

        # Очищаем сгенерированный текст от возможных JSON-фрагментов
        regenerated_text = deep_clean_text(regenerated_text)

        logger.info(f"Received regenerated text (length: {len(regenerated_text)})")

        # Создаем ответ
        response_data = {
            "user_id": request.user_id,
            "language": request.language,
            "vocabulary_type": request.vocabulary,
            "preserve_style": request.preserve_style,
            "original_text": request.text_content,
            "regenerated_text": regenerated_text,
            "content": regenerated_text  # Добавляем поле content для совместимости с фронтендом
        }

        # Логируем использование
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"action": "regenerate_text", "vocabulary": request.vocabulary, "preserve_style": request.preserve_style}
        ))

        # Сохраняем в кэш
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Text regenerated successfully",
            "with_points": request.with_points
        })

        logger.info("Text regeneration completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Text regenerated successfully",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error regenerating text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error regenerating text: {str(e)}"
        )

@router.post("/change_text_level", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("text_analysis", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def change_text_level(
    request: ChangeTextLevelRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """Изменение уровня сложности текста"""
    logger.info(f"Started changing text level to: {request.target_level}")

    cache_key = f"change_text_level:{request.user_id}:{hash(request.text_content)}:{request.target_level}:{request.preserve_style}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        return ContentResponse(**cached_result)

    try:
        # Функция для глубокой очистки текста от JSON и технических фрагментов
        def deep_clean_text(text):
            if not text:
                return ""

            # Преобразуем в строку
            text = str(text)

            # Удаляем экранированные символы
            text = re.sub(r'\\[nrt]', ' ', text)
            text = re.sub(r'\\{2,}', '', text)

            # Удаляем JSON фрагменты
            json_patterns = [
                r'"meta":\s*{[^}]*}',
                r'"language":\s*"[^"]*"',
                r'"count":\s*\d+',
                r'"difficulty":\s*"[^"]*"',
                r'"questions":\s*\[[^\]]*\]',
                r'"markdown_content":\s*"[^"]*"',
                r'"options":\s*\[[^\]]*\]',
                r'"answer":\s*"[^"]*"',
                r'"number":\s*\d+',
                r'"question":\s*"[^"]*"',
                r'"[^"]*":\s*',
                r'"[^"]*"\s*:',
                r'"original_text":\s*"[^"]*"',
                r'"adapted_text":\s*"[^"]*"',
                r'"target_level":\s*"[^"]*"'
            ]

            for pattern in json_patterns:
                text = re.sub(pattern, '', text)

            # Удаляем JSON символы
            text = re.sub(r'[{}\[\]"]', '', text)
            text = re.sub(r',(\s*,)+', ',', text)
            text = re.sub(r'^\s*,|,\s*$', '', text)

            # Удаляем JSON ключевые слова
            keywords = ['meta', 'language', 'count', 'difficulty', 'questions',
                       'markdown_content', 'options', 'answer', 'number', 'question',
                       'english', 'russian', 'spanish', 'french', 'original_text', 'adapted_text',
                       'target_level', 'preserve_style']
            for kw in keywords:
                text = re.sub(rf'\b{kw}\b', '', text, flags=re.IGNORECASE)

            # Удаляем лишние пробелы
            text = re.sub(r'\s+', ' ', text)

            return text.strip()

        # Изменение уровня текста
        generator = ContentGenerator(session)
        logger.info("Calling content generator for changing text level...")
        adapted_text = await generator.change_text_level(
            text=request.text_content,
            language=request.language,
            target_level=request.target_level,
            preserve_style=request.preserve_style,
            user_id=request.user_id
        )

        # Очищаем адаптированный текст от возможных JSON-фрагментов
        adapted_text = deep_clean_text(adapted_text)

        logger.info(f"Received adapted text (length: {len(adapted_text)})")

        # Создаем ответ
        response_data = {
            "user_id": request.user_id,
            "language": request.language,
            "target_level": request.target_level,
            "preserve_style": request.preserve_style,
            "original_text": request.text_content,
            "adapted_text": adapted_text,
            "content": adapted_text  # Добавляем поле content для совместимости с фронтендом
        }

        # Логируем использование
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=request.user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"action": "change_text_level", "target_level": request.target_level, "preserve_style": request.preserve_style}
        ))

        # Сохраняем в кэш
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Text level changed successfully",
            "with_points": request.with_points
        })

        logger.info("Text level change completed successfully")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Text level changed successfully",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Error changing text level: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error changing text level: {str(e)}"
        )

def get_exam_specific_requirements(exam_name: str) -> str:
    """
    Возвращает специфические требования для различных экзаменов
    """
    exam_name_lower = exam_name.lower().strip()

    exam_requirements = {
        'ielts': """
        IELTS SPECIFIC REQUIREMENTS:
        - Reading: Academic texts, multiple choice, matching, True/False/Not Given
        - Writing: Task 1 (graphs/charts/diagrams), Task 2 (argumentative essays)
        - Listening: 4 sections, multiple accents, note completion, matching
        - Speaking: Part 1 (personal questions), Part 2 (long turn), Part 3 (discussion)
        - Band descriptors: Fluency, Lexical Resource, Grammatical Range, Pronunciation
        - Academic vocabulary and formal register required
        """,

        'toefl': """
        TOEFL SPECIFIC REQUIREMENTS:
        - Reading: Academic passages, multiple choice, inference questions
        - Writing: Integrated tasks (read-listen-write), Independent essay
        - Listening: Academic lectures and conversations, note-taking skills
        - Speaking: Independent and integrated tasks, 15-30 second responses
        - Focus on American English and academic contexts
        - Computer-based format simulation
        """,

        'cambridge': """
        CAMBRIDGE EXAMS (FCE/CAE/CPE) REQUIREMENTS:
        - Use of English: Grammar, vocabulary, word formation, key word transformations
        - Reading: Multiple texts, gapped text, multiple choice, multiple matching
        - Writing: Essays, reports, reviews, proposals (formal/informal register)
        - Listening: Multiple choice, sentence completion, multiple matching
        - Speaking: Interview, long turn, collaborative task, discussion
        - Focus on British English and varied contexts
        """,

        'fce': """
        FCE (B2 First) SPECIFIC REQUIREMENTS:
        - Use of English: Multiple choice cloze, open cloze, word formation, key word transformations
        - Reading: Multiple choice, gapped text, multiple matching
        - Writing: Essay (140-190 words), article/email/letter/report/review (140-190 words)
        - Listening: Multiple choice, sentence completion, multiple matching
        - Speaking: Interview, long turn, collaborative task, discussion
        - B2 level vocabulary and structures
        """,

        'cae': """
        CAE (C1 Advanced) SPECIFIC REQUIREMENTS:
        - Use of English: Multiple choice cloze, open cloze, word formation, key word transformations
        - Reading: Multiple choice, gapped text, multiple matching, cross-text multiple matching
        - Writing: Essay (220-260 words), report/proposal/review/letter (220-260 words)
        - Listening: Multiple choice, sentence completion, multiple matching
        - Speaking: Interview, long turn, collaborative task, discussion
        - C1 level advanced vocabulary and complex structures
        """,

        'cpe': """
        CPE (C2 Proficiency) SPECIFIC REQUIREMENTS:
        - Use of English: Multiple choice cloze, open cloze, word formation, key word transformations
        - Reading: Multiple choice, gapped text, multiple matching, cross-text multiple matching
        - Writing: Essay (240-280 words), article/letter/proposal/report/review (280-320 words)
        - Listening: Multiple choice, sentence completion, multiple matching
        - Speaking: Interview, long turn, collaborative task, discussion
        - C2 level sophisticated vocabulary and native-like accuracy
        """
    }

    # Поиск по ключевым словам для гибкости
    for key, requirements in exam_requirements.items():
        if key in exam_name_lower:
            return requirements

    # Общие требования для неизвестных экзаменов
    return f"""
    GENERAL EXAM PREPARATION REQUIREMENTS FOR {exam_name.upper()}:
    - Include exam-style tasks and question formats
    - Practice time management and exam strategies
    - Focus on accuracy and fluency appropriate for the exam level
    - Include vocabulary and structures commonly tested
    - Provide tips for avoiding common mistakes
    - Simulate exam conditions where possible
    """

def get_lesson_stages(methodology):
    # Стадии по умолчанию
    default_stages = """
    a. Warm-up/Introduction (5-10 minutes)
    b. Presentation of New Material (10-15 minutes)
    c. Controlled Practice (10-15 minutes)
    d. Free Practice/Production (10-15 minutes)
    e. Review and Feedback (5-10 minutes)
    """

    # Стадии в зависимости от методологии
    methodology_stages = {
        'celta': """
        a. Lead-in (5 minutes) - Engage students with the topic through guided discovery questions and context setting
        b. Exposure (10 minutes) - Present new language in authentic context, using elicitation techniques to draw out student knowledge
        c. Highlighting (5 minutes) - Guide students to notice target language through guided discovery questions rather than direct explanation
        d. Clarification (10 minutes) - Use concept checking questions (CCQs) and guided discovery to help students understand meaning, form, and pronunciation
        e. Controlled Practice (10 minutes) - Structured practice with pair/group work, focusing on accuracy
        f. Freer Practice (15 minutes) - Communicative activities emphasizing fluency, with extensive pair/group interaction
        g. Feedback and Error Correction (5 minutes) - Student-centered feedback with peer correction and self-reflection

        CELTA Teaching Principles to incorporate:
        - Use guided discovery throughout (avoid direct explanation where possible)
        - Maximize student talking time through pair/group work
        - Employ elicitation techniques constantly to engage students
        - Focus on student-centered learning with teacher as facilitator
        - Include concept checking questions (CCQs) for meaning clarification
        - Provide opportunities for both accuracy and fluency practice
        - Encourage peer feedback and self-correction
        """,

        'clil': """
        a. Activation of Prior Knowledge (5 minutes) - Connect to students' existing content and cultural knowledge
        b. Content and Language Integrated Input (15 minutes) - Present new content with embedded language focus
        c. Cognitive Processing (10 minutes) - Higher-order thinking activities combining content and language
        d. Communicative Output (15 minutes) - Meaningful communication tasks about content
        e. Assessment and Reflection (5 minutes) - Evaluate both content learning and language development

        CLIL Integration Principles:
        - Balance content and language objectives equally
        - Use authentic materials from the subject area
        - Promote critical thinking through content
        - Develop academic language naturally through content
        - Include cultural and intercultural elements
        """,

        'tbl': """
        a. Pre-task (5 minutes) - Introduce topic, activate schema, prepare for task with language support
        b. Task Performance (15 minutes) - Students complete meaningful, outcome-focused task
        c. Planning (5 minutes) - Prepare to report on task outcomes and process
        d. Report (10 minutes) - Share task outcomes with class, compare approaches
        e. Language Focus (10 minutes) - Analyze language that emerged, practice specific features

        TBL Core Principles:
        - Focus on meaning and communication during task performance
        - Use authentic, real-world tasks with clear outcomes
        - Allow natural language emergence through task completion
        - Provide language focus after meaningful use
        - Encourage fluency over accuracy during task phase
        """,

        'tblt': """
        a. Pre-task Phase (10 minutes) - Introduce topic and prepare for task
        b. Task Phase (15 minutes) - Complete the main task
        c. Planning Phase (5 minutes) - Prepare to report on the task
        d. Report Phase (10 minutes) - Present task outcomes
        e. Analysis Phase (5 minutes) - Examine language used
        f. Practice Phase (5 minutes) - Focus on specific language features
        """,

        'cbi': """
        a. Schema Activation (5 minutes) - Activate prior content knowledge and academic language
        b. Content Input (15 minutes) - Present new content using authentic academic materials
        c. Content Processing (15 minutes) - Analyze, synthesize, and evaluate content information
        d. Academic Language Development (10 minutes) - Focus on content-specific language features
        e. Content and Language Assessment (5 minutes) - Evaluate mastery of both content and language

        CBI Integration Principles:
        - Use authentic academic content as the vehicle for language learning
        - Develop academic language skills through content study
        - Integrate higher-order thinking skills with language development
        - Connect to students' academic and professional goals
        - Balance content mastery with language proficiency development
        """,

        'tpr': """
        a. Command Introduction (5 minutes)
        b. Teacher Demonstration (10 minutes)
        c. Group Practice (10 minutes)
        d. Student Command Phase (10 minutes)
        e. Written Follow-up (10 minutes)
        f. Extension Activities (5 minutes)
        """,

        'dm': """
        a. Dialogue or Text Introduction (10 minutes)
        b. Question-Answer Exchange (15 minutes)
        c. Target Language Practice (15 minutes)
        d. Inductive Grammar Discovery (5 minutes)
        e. Application Activities (5 minutes)
        """,

        'suggestopedia': """
        a. Preparation Phase (5 minutes) - Create positive atmosphere
        b. First Concert (10 minutes) - Active presentation with music
        c. Second Concert (10 minutes) - Passive review with music
        d. Activation Phase (15 minutes) - Games and activities
        e. Performance Phase (10 minutes) - Use new material creatively
        """,

        'silentWay': """
        a. Teacher Modeling (5 minutes) - Silent demonstration
        b. Student Approximation (10 minutes) - Attempts at production
        c. Peer Correction (10 minutes) - Students help each other
        d. Self-Correction (10 minutes) - Independent work
        e. Practice with Rods/Charts (10 minutes)
        f. Free Application (5 minutes)
        """,

        'ali': """
        a. Dialogue Presentation (10 minutes)
        b. Repetition and Memorization (10 minutes)
        c. Pattern Drills (15 minutes)
        d. Controlled Conversation (10 minutes)
        e. Application Activities (5 minutes)
        """,

        'esl': """
        a. Warm-up Discussion (5 minutes)
        b. Communicative Activity (15 minutes)
        c. Language Focus (10 minutes)
        d. Practical Application (15 minutes)
        e. Real-world Connection (5 minutes)
        """,

        'efl': """
        a. Introduction and Activation (5 minutes)
        b. Presentation of Target Language (10 minutes)
        c. Controlled Practice (10 minutes)
        d. Semi-controlled Practice (10 minutes)
        e. Free Practice (10 minutes)
        f. Assessment and Feedback (5 minutes)
        """,

        'esp': """
        a. Professional Context Activation (5 minutes) - Connect to students' specific professional needs
        b. Specialized Language Input (10 minutes) - Present field-specific vocabulary and discourse patterns
        c. Authentic Material Analysis (15 minutes) - Work with real workplace documents and situations
        d. Professional Task Simulation (15 minutes) - Practice authentic workplace communication tasks
        e. Performance Evaluation (5 minutes) - Assess professional communication competence

        ESP Core Principles:
        - Base all activities on learners' specific professional needs
        - Use authentic materials from the target professional field
        - Focus on immediate practical application
        - Develop specialized vocabulary and discourse patterns
        - Simulate real workplace communication situations
        """,

        'eap': """
        a. Academic Context Setting (5 minutes) - Establish academic purpose and activate academic schema
        b. Academic Language Focus (10 minutes) - Develop discipline-specific academic language
        c. Critical Thinking Development (10 minutes) - Practice academic reasoning and analysis skills
        d. Academic Task Performance (15 minutes) - Complete authentic academic tasks (writing, research, presentation)
        e. Academic Reflection and Assessment (10 minutes) - Evaluate academic performance and learning strategies

        EAP Core Principles:
        - Develop critical thinking alongside language skills
        - Focus on academic genres and discourse conventions
        - Integrate study skills and learning strategies
        - Prepare students for academic assessment formats
        - Promote academic autonomy and self-directed learning
        """
    }

    return methodology_stages.get(methodology, default_stages)

def get_multilingual_instructions(target_language: str) -> str:
    """
    Returns instructions for lesson plans with English instructions for the teacher
    and tasks in the target language for students
    """
    # Define language name in Russian
    language_names_russian = {
        'english': 'английского языка',
        'spanish': 'испанского языка',
        'french': 'французского языка',
        'german': 'немецкого языка',
        'italian': 'итальянского языка',
        'chinese': 'китайского языка',
        'japanese': 'японского языка',
        'korean': 'корейского языка',
        'turkish': 'турецкого языка',
        'arabic': 'арабского языка',
        'portuguese': 'португальского языка',
        'dutch': 'голландского языка',
        'polish': 'польского языка',
        'czech': 'чешского языка',
        'hungarian': 'венгерского языка',
        'finnish': 'финского языка',
        'swedish': 'шведского языка',
        'norwegian': 'норвежского языка',
        'danish': 'датского языка'
    }

    # Определяем название языка на изучаемом языке
    language_names_native = {
        'english': 'English',
        'spanish': 'Español',
        'french': 'Français',
        'german': 'Deutsch',
        'italian': 'Italiano',
        'chinese': '中文',
        'japanese': '日本語',
        'korean': '한국어',
        'turkish': 'Türkçe',
        'arabic': 'العربية',
        'portuguese': 'Português',
        'dutch': 'Nederlands',
        'polish': 'Polski',
        'czech': 'Čeština',
        'hungarian': 'Magyar',
        'finnish': 'Suomi',
        'swedish': 'Svenska',
        'norwegian': 'Norsk',
        'danish': 'Dansk'
    }

    target_lang_lower = target_language.lower()
    russian_name = language_names_russian.get(target_lang_lower, f'{target_language} языка')
    native_name = language_names_native.get(target_lang_lower, target_language)

    return f"""
    📚 {russian_name.upper()} LESSON PLAN FOR TEACHERS

    CRITICALLY IMPORTANT - LANGUAGE SEPARATION:

    📚 FOR TEACHER (in English):
    - All instructions and methodological guidelines
    - Grammar and vocabulary explanations
    - Activity descriptions and their objectives
    - Lesson delivery tips
    - Potential problems and solutions
    - Assessment criteria
    - Homework assignments (description for teacher)

    🎯 FOR STUDENTS (in {native_name}):
    - All exercises and tasks
    - Reading texts
    - Dialogues and role-plays
    - Questions and task instructions
    - Example sentences
    - Vocabulary lists
    - Homework assignments (the tasks themselves)

    MANDATORY FORMAT:
    - Section headings: IN ENGLISH
    - Methodological instructions: IN ENGLISH
    - Упражнения и задания: НА {native_name.upper()}
    - CCQs (teacher questions): IN ENGLISH
    - Student answers in examples: IN {native_name.upper()}
    """

def format_prompt_lesson_plan_form(data: dict) -> str:
    """
    Форматирует промпт для генерации плана урока из данных формы.
    Учитывает все возможные поля из формы и создает соответствующие инструкции.
    Creates lesson plans for teachers: instructions in English, tasks in the target language.
    """
    target_language = data.get('language', 'English')

    # Получаем многоязычные инструкции
    multilingual_instructions = get_multilingual_instructions(target_language)

    # Общие инструкции форматирования
    lesson_format_instructions = """
    Respond in English for all teacher instructions, but use the target language for all student tasks and exercises.
    Use Markdown formatting with headers, lists, and emphasis.
    """

    # Инструкции для языка
    language_instructions = f"Создай план урока для изучения {target_language}."

    # Инструкции для темы
    topic_instructions = ""
    if data.get('topic') and isinstance(data.get('topic'), str) and data.get('topic').strip():
        topic_instructions = f"""
        The lesson topic is: {data.get('topic').strip()}
        Focus all activities and materials on this topic.
        """

    # Инструкции для возрастной группы
    age_instructions = ""
    age_value = data.get('age', '')
    if isinstance(age_value, str) and age_value.strip():
        age_map = {
            'children': "This lesson is for children (7-12 years old). Use appropriate activities and language for this age group.",
            'teens': "This lesson is for teenagers (13-17 years old). Use engaging, age-appropriate activities and examples relevant to their interests.",
            'adults': "This lesson is for adult learners (18+ years old). Use mature examples and consider professional/practical applications."
        }
        age_instructions = age_map.get(age_value.strip().lower(), f"This lesson is for {age_value.strip()} learners.")

    # Инструкции для уровня сложности
    level_instructions = ""
    level_value = data.get('level', '')
    if isinstance(level_value, str) and level_value.strip():
        level_map = {
            'beginner': "This lesson is for beginners (A1 level). Use simple language, basic vocabulary, and focus on fundamental concepts.",
            'elementary': "This lesson is for elementary students (A2 level). Use straightforward language and gradually introduce more complex structures.",
            'intermediate': "This lesson is for intermediate students (B1 level). Use moderately complex language and introduce more advanced concepts.",
            'upper_intermediate': "This lesson is for upper-intermediate students (B2 level). Use more complex language and challenging activities.",
            'advanced': "This lesson is for advanced students (C1 level). Use sophisticated language and complex concepts.",
            'proficient': "This lesson is for proficient students (C2 level). Use native-like language and highly complex concepts."
        }
        level_instructions = level_map.get(level_value.strip().lower(), f"The students' level is {level_value.strip()}.")

    # Инструкции для предыдущего урока
    previous_lesson_instructions = ""
    if data.get('previous_lesson') and isinstance(data.get('previous_lesson'), str) and data.get('previous_lesson').strip():
        previous_lesson_instructions = f"""
        The previous lesson covered:
        {data.get('previous_lesson').strip()}

        Make sure to review and build upon this material where appropriate.
        """

    # Инструкции для грамматики
    grammar_instructions = ""
    if data.get('grammar') and isinstance(data.get('grammar'), str) and data.get('grammar').strip():
        grammar_instructions = f"""
        Focus on the following grammar points:
        {data.get('grammar').strip()}

        Include explanations and practice activities for these grammar structures.
        """

    # Инструкции для лексики
    vocabulary_instructions = ""
    if data.get('vocabulary') and isinstance(data.get('vocabulary'), str) and data.get('vocabulary').strip():
        vocabulary_instructions = f"""
        Include the following vocabulary focus:
        {data.get('vocabulary').strip()}

        Incorporate vocabulary teaching and practice activities around these words/themes.
        """

    # Инструкции для методологии
    methodology_instructions = ""
    methodology_specific_instructions = ""
    lesson_stages = get_lesson_stages("")  # Инициализируем стандартными стадиями по умолчанию
    methodology_value = data.get('methodology', [])
    if methodology_value and isinstance(methodology_value, list) and len(methodology_value) > 0:
        # Получаем стадии урока на основе первой методологии в списке
        main_methodology = methodology_value[0] if methodology_value else ""
        lesson_stages = get_lesson_stages(main_methodology)

        # Формируем инструкции для всех методологий
        methodology_names = ", ".join([str(m) for m in methodology_value])
        methodology_instructions = f"""
        Use the following teaching methodology/methodologies: {methodology_names}
        Structure your lesson plan according to these principles.
        """

        # Добавляем специфические инструкции для методологий

        # Проверяем каждую методологию и добавляем соответствующие критерии
        for method in methodology_value:
            method_lower = str(method).lower()

            if method_lower == 'celta':
                methodology_specific_instructions += """

                CELTA ASSESSMENT CRITERIA - Ensure your lesson plan demonstrates:

                PLANNING:
                - Thorough analysis of target language (meaning, form, pronunciation, appropriacy)
                - Clear, specific, and measurable lesson objectives
                - Appropriate selection of resources and materials for successful language development
                - Logical lesson structure with smooth transitions between stages
                - Consideration of potential problems and solutions

                TEACHING TECHNIQUES:
                - Variety of classroom teaching techniques used successfully
                - Guided discovery approach (students discover rules through examples and questions)
                - Extensive use of elicitation techniques throughout the lesson
                - Concept Checking Questions (CCQs) to verify understanding
                - Instructions checking questions to ensure task clarity
                - Appropriate use of teacher talking time vs student talking time

                AWARENESS OF LEARNERS:
                - Student-centered approach with teacher as facilitator
                - Extensive pair work and group activities to maximize student interaction
                - Activities appropriate for the specified level and age group
                - Consideration of different learning styles and preferences
                - Opportunities for both accuracy and fluency practice
                - Differentiation strategies for mixed-ability classes

                REFLECTION AND DEVELOPMENT:
                - Built-in opportunities for student self-assessment and reflection
                - Peer feedback and correction activities
                - Clear criteria for assessing lesson objectives achievement
                - Identification of areas for future development

                OVERALL LANGUAGE LEARNING UNDERSTANDING:
                - Demonstrates excellent understanding of English language learning processes
                - Balances focus on meaning, form, and pronunciation appropriately
                - Provides authentic contexts for language use
                - Encourages natural language acquisition through meaningful communication
                """

            elif method_lower == 'clil':
                methodology_specific_instructions += """

                CLIL QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                CONTENT INTEGRATION:
                - Clear integration of subject content and language learning objectives
                - Authentic content that is age and level appropriate
                - Content that provides meaningful context for language use
                - Balance between content learning and language development

                COGNITIVE ENGAGEMENT:
                - Activities that promote higher-order thinking skills (analysis, synthesis, evaluation)
                - Problem-solving tasks that require both content knowledge and language use
                - Critical thinking opportunities through content exploration
                - Scaffolding to support cognitive and linguistic demands

                COMMUNICATION FOCUS:
                - Multiple opportunities for meaningful communication about content
                - Academic language development appropriate to the subject area
                - Integration of all four skills (reading, writing, listening, speaking)
                - Authentic communication tasks related to content

                CULTURAL AWARENESS:
                - Content that promotes intercultural understanding
                - Multiple perspectives on subject matter
                - Cultural contexts that enhance content comprehension
                - Global citizenship development through content

                ASSESSMENT INTEGRATION:
                - Assessment of both content knowledge and language proficiency
                - Formative assessment throughout the lesson
                - Clear criteria for content and language achievement
                - Multiple assessment formats to accommodate different learning styles
                """

            elif method_lower in ['tbl', 'tblt']:
                methodology_specific_instructions += """

                TASK-BASED LEARNING QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                TASK AUTHENTICITY:
                - Tasks that reflect real-world language use and communication needs
                - Meaningful outcomes that students can relate to their lives
                - Authentic materials and contexts for task completion
                - Clear connection between tasks and real-world applications

                TASK DESIGN PRINCIPLES:
                - Tasks with clear, achievable goals and outcomes
                - Information gap, opinion gap, or reasoning gap activities
                - Focus on meaning rather than form during task performance
                - Appropriate cognitive and linguistic challenge for the level

                THREE-PHASE STRUCTURE:
                - Pre-task: Clear task preparation and language activation
                - Task cycle: Focus on fluency and task completion
                - Language focus: Analysis and practice of emerging language
                - Smooth transitions between phases with clear objectives

                LEARNER ENGAGEMENT:
                - Student-centered approach with teacher as facilitator
                - Collaborative and interactive task completion
                - Opportunities for negotiation of meaning
                - Multiple ways for students to approach and complete tasks

                LANGUAGE DEVELOPMENT:
                - Natural language emergence through task completion
                - Focus on communication strategies and fluency
                - Post-task language analysis and consciousness-raising
                - Integration of accuracy work based on task performance
                """

            elif method_lower == 'cbi':
                methodology_specific_instructions += """

                CONTENT-BASED INSTRUCTION QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                CONTENT-LANGUAGE INTEGRATION:
                - Meaningful academic or professional content as the vehicle for language learning
                - Clear content objectives alongside language objectives
                - Authentic materials from the target content area
                - Balance between content mastery and language development

                ACADEMIC LANGUAGE DEVELOPMENT:
                - Focus on academic vocabulary and discourse patterns
                - Development of content-specific language functions
                - Scaffolding for academic reading and writing skills
                - Integration of study skills and learning strategies

                COGNITIVE ENGAGEMENT:
                - Higher-order thinking skills through content exploration
                - Critical analysis and evaluation of content materials
                - Problem-solving activities related to content area
                - Research and inquiry-based learning opportunities

                ASSESSMENT ALIGNMENT:
                - Assessment of both content knowledge and language proficiency
                - Authentic assessment tasks reflecting real academic demands
                - Multiple assessment formats (oral, written, project-based)
                - Clear rubrics for content and language achievement
                """

            elif method_lower == 'tpr':
                methodology_specific_instructions += """

                TOTAL PHYSICAL RESPONSE QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                PHYSICAL ENGAGEMENT:
                - Extensive use of physical movement and gestures
                - Commands and instructions that require physical responses
                - Kinesthetic learning opportunities throughout the lesson
                - Movement activities that reinforce language comprehension

                COMPREHENSION-FIRST APPROACH:
                - Focus on listening comprehension before speaking production
                - Silent period respect for learners not ready to speak
                - Comprehension checking through physical responses
                - Gradual progression from receptive to productive skills

                STRESS-FREE ENVIRONMENT:
                - Low-anxiety learning atmosphere
                - No forced speech production
                - Error tolerance and natural correction
                - Playful and enjoyable learning activities

                NATURAL ACQUISITION PRINCIPLES:
                - Language learning that mirrors first language acquisition
                - Meaningful and contextual language input
                - Right-brain learning through physical coordination
                - Holistic language experience rather than analytical study
                """

            elif method_lower == 'dm':
                methodology_specific_instructions += """

                DIRECT METHOD QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                TARGET LANGUAGE IMMERSION:
                - Exclusive use of target language throughout the lesson
                - No translation or native language use
                - Direct association between objects/concepts and target language
                - Immersive language environment creation

                NATURAL LEARNING APPROACH:
                - Teaching that mimics natural language acquisition
                - Inductive grammar learning through examples and patterns
                - Emphasis on oral communication and pronunciation
                - Everyday vocabulary and practical language use

                DEMONSTRATION AND ASSOCIATION:
                - Visual aids, realia, and demonstrations for meaning conveyance
                - Direct association between words and their meanings
                - Contextual learning without translation
                - Concrete before abstract concept introduction

                ORAL PROFICIENCY FOCUS:
                - Speaking and listening skills prioritization
                - Pronunciation and intonation emphasis
                - Conversational practice and dialogue work
                - Gradual progression to reading and writing skills
                """

            elif method_lower == 'suggestopedia':
                methodology_specific_instructions += """

                SUGGESTOPEDIA QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                RELAXED LEARNING ENVIRONMENT:
                - Comfortable, stress-free classroom atmosphere
                - Positive suggestion and encouragement throughout
                - Elimination of psychological barriers to learning
                - Supportive and non-threatening learning context

                MUSIC AND RHYTHM INTEGRATION:
                - Baroque music for passive learning phases
                - Rhythmic presentation of new material
                - Musical background for memory enhancement
                - Synchronized learning with musical patterns

                DUAL-PLANE COMMUNICATION:
                - Conscious and unconscious learning activation
                - Peripheral learning through environmental stimuli
                - Subliminal suggestion techniques
                - Multi-sensory learning experience

                ACCELERATED LEARNING PRINCIPLES:
                - Large amounts of material presented efficiently
                - Rapid vocabulary acquisition techniques
                - Memory enhancement through suggestion
                - Confidence building and positive expectation
                """

            elif method_lower == 'sw':
                methodology_specific_instructions += """

                SILENT WAY QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                LEARNER AUTONOMY:
                - Students as active discoverers of language patterns
                - Minimal teacher intervention and maximum student exploration
                - Self-correction and peer correction encouragement
                - Independent problem-solving and hypothesis testing

                DISCOVERY LEARNING:
                - Inductive approach to grammar and vocabulary learning
                - Pattern recognition and rule formation by students
                - Experimentation with language structures
                - Learning through trial and error with guidance

                VISUAL AND TACTILE AIDS:
                - Cuisenaire rods for meaning and structure demonstration
                - Color-coded pronunciation charts
                - Visual representations of abstract concepts
                - Hands-on manipulation of learning materials

                TEACHER SILENCE AND STUDENT PRODUCTION:
                - Strategic teacher silence to promote student thinking
                - Student-generated language and self-expression
                - Peer teaching and collaborative learning
                - Focus on student discovery rather than teacher explanation
                """

            elif method_lower == 'alm':
                methodology_specific_instructions += """

                AUDIO-LINGUAL METHOD QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                PATTERN PRACTICE AND DRILLS:
                - Systematic pattern drills and repetition exercises
                - Substitution, transformation, and expansion drills
                - Mechanical practice leading to automatic responses
                - Gradual progression from simple to complex structures

                HABIT FORMATION:
                - Consistent practice to develop language habits
                - Immediate error correction to prevent bad habits
                - Positive reinforcement for correct responses
                - Overlearning through extensive repetition

                ORAL-AURAL EMPHASIS:
                - Listening and speaking skills prioritization
                - Pronunciation and intonation accuracy focus
                - Minimal reading and writing in early stages
                - Audio materials and language laboratory use

                STRUCTURAL PROGRESSION:
                - Systematic presentation of grammatical structures
                - Controlled progression from known to unknown
                - Contrastive analysis to predict learning difficulties
                - Scientific approach to language structure presentation
                """

            elif method_lower == 'esp':
                methodology_specific_instructions += """

                ENGLISH FOR SPECIFIC PURPOSES QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                NEEDS ANALYSIS INTEGRATION:
                - Clear connection to learners' professional or academic needs
                - Specific language skills required in target situations
                - Authentic workplace or field-specific contexts
                - Relevant vocabulary and discourse patterns for the specialty

                AUTHENTIC MATERIALS AND TASKS:
                - Real-world documents and materials from the target field
                - Workplace-relevant communication tasks
                - Professional scenarios and case studies
                - Industry-specific language functions and genres

                SPECIALIZED LANGUAGE FOCUS:
                - Technical vocabulary and terminology development
                - Field-specific grammar and discourse patterns
                - Professional communication skills (presentations, reports, meetings)
                - Register and style appropriate to professional contexts

                PRACTICAL APPLICATION:
                - Immediate applicability to learners' professional contexts
                - Simulation of real workplace communication situations
                - Problem-solving tasks relevant to the field
                - Assessment based on professional communication competence
                """

            elif method_lower == 'eap':
                methodology_specific_instructions += """

                ENGLISH FOR ACADEMIC PURPOSES QUALITY CRITERIA - Ensure your lesson plan demonstrates:

                ACADEMIC SKILLS DEVELOPMENT:
                - Critical thinking and analytical skills integration
                - Academic writing conventions and genres
                - Research and citation skills development
                - Academic presentation and discussion skills

                DISCOURSE COMPETENCE:
                - Academic register and formal language use
                - Discipline-specific discourse patterns
                - Argumentation and evidence-based reasoning
                - Academic vocabulary and collocations

                STUDY SKILLS INTEGRATION:
                - Note-taking and summarizing strategies
                - Academic reading strategies (skimming, scanning, critical reading)
                - Time management and study organization
                - Information literacy and source evaluation

                ASSESSMENT PREPARATION:
                - Academic assessment format familiarity
                - Test-taking strategies for academic contexts
                - Portfolio development and self-assessment
                - Peer review and collaborative academic work
                """
    # Если методология не указана, lesson_stages уже инициализирована стандартными стадиями выше

    # Инструкции для формата урока (индивидуальный/групповой)
    individual_group_instructions = ""
    individual_group_value = data.get('individual_group', '')
    if isinstance(individual_group_value, str):
        if individual_group_value.lower() == 'individual':
            individual_group_instructions = """
            This is an individual lesson (one-to-one teaching) following student-centered principles.
            MAXIMIZE STUDENT TALKING TIME through:
            - Extensive use of elicitation questions to draw out student knowledge
            - Guided discovery activities where student discovers rules through examples
            - Role-play activities where student practices both roles
            - Student-led discussions and presentations
            - Self-correction opportunities before teacher correction

            PERSONALIZED APPROACH:
            - Tailor activities to student's specific interests and needs
            - Provide immediate, personalized feedback
            - Adjust pace according to student's learning speed
            - Include student's real-life contexts in examples and practice
            - Encourage student reflection on their own learning process
            """
        elif individual_group_value.lower() == 'group':
            individual_group_instructions = """
            This is a group lesson following student-centered approach.
            MAXIMIZE STUDENT INTERACTION through:
            - Extensive pair work activities (students work in pairs frequently)
            - Small group discussions and collaborative tasks
            - Peer teaching and peer correction opportunities
            - Student-to-student communication rather than teacher-to-student
            - Group problem-solving and discovery activities
            - Mingling activities where students interact with multiple partners

            CLASSROOM MANAGEMENT for group work:
            - Clear instructions with instruction checking questions (ICQs)
            - Defined roles for group members when appropriate
            - Time limits and clear signals for transitions
            - Monitoring techniques to support without interrupting
            - Feedback collection from multiple groups
            """

    # Инструкции для формата (онлайн/оффлайн)
    online_offline_instructions = ""
    online_offline_value = data.get('online_offline', '')
    if isinstance(online_offline_value, str):
        if online_offline_value.lower() == 'online':
            online_offline_instructions = """
            This is an online lesson.
            Include activities suitable for video conferencing platforms.
            Consider use of digital tools, screen sharing, and online resources.
            Adapt activities to work in a virtual environment.
            """
        elif online_offline_value.lower() == 'offline':
            online_offline_instructions = """
            This is an in-person, classroom-based lesson.
            Include activities that use physical materials and classroom space.
            Consider movement activities, board work, and printed materials.
            """

    # Инструкции для экзаменационной подготовки
    exam_instructions = ""
    exam_value = data.get('exam', '')
    if isinstance(exam_value, str) and exam_value.strip():
        exam_specific_requirements = get_exam_specific_requirements(exam_value.strip())
        exam_instructions = f"""
        🎯 EXAM PREPARATION FOCUS: {exam_value.strip()}

        {exam_specific_requirements}

        MANDATORY EXAM INTEGRATION:
        - ALL activities must prepare students for {exam_value.strip()} format
        - Include {exam_value.strip()}-specific vocabulary, collocations, and structures
        - Practice authentic {exam_value.strip()}-style tasks and question types
        - Focus on skills and competencies tested in {exam_value.strip()}
        - Provide {exam_value.strip()} strategies, tips, and time management techniques
        - Include sample {exam_value.strip()} questions and practice materials
        - Address common {exam_value.strip()} mistakes and how to avoid them
        - Integrate {exam_value.strip()} assessment criteria into lesson objectives
        """

    # Инструкции для продолжительности урока
    duration_instructions = ""
    duration_value = data.get('duration', 60)
    if duration_value:
        duration_instructions = f"""
        This lesson should be designed for a {duration_value}-minute class.
        Include a detailed timeline for each activity.
        Ensure activities fit within the time constraints.
        """

    # Формируем итоговый промпт
    # Упрощенный промпт для получения качественного результата
    formatted_prompt = f"""
    Создайте ДЕТАЛЬНЫЙ ПЛАН УРОКА для изучения {target_language}.
    
    You MUST use English instructions for the teacher and {target_language} для заданий студентов.
    
    Параметры урока:
    - Тема: {data.get('topic', 'Общая тема')}
    - Уровень: {level_instructions}
    - Возраст: {age_instructions}  
    - Продолжительность: {duration_instructions}
    - Грамматика: {grammar_instructions}
    - Лексика: {vocabulary_instructions}
    
    {previous_lesson_instructions}

    СТРУКТУРА ПЛАНА УРОКА:

    # [Название урока]

    ## 📋 Обзор урока  
    **Цели урока:** (3-5 конкретных целей)
    **Продолжительность:** {data.get('duration', 60)} минут
    **Уровень:** {data.get('level', 'intermediate')}
    **Тема:** {data.get('topic', 'General Topic')}

    ## ⏰ Подробное расписание урока
    
    ### 1. Разминка (5-10 мин)
    **Цель:** [Цель этапа]
    **Действия учителя:** [Конкретные инструкции]
    **Задания для студентов:** [Конкретные задания на {target_language}]
    
    ### 2. Презентация материала (15-20 мин)
    **Цель:** [Цель этапа]
    **Действия учителя:** [Конкретные инструкции]
    **Задания для студентов:** [Конкретные задания на {target_language}]
    
    ### 3. Практика (20-25 мин)
    **Цель:** [Цель этапа]
    **Действия учителя:** [Конкретные инструкции]
    **Задания для студентов:** [Конкретные задания на {target_language}]
    
    ### 4. Закрепление (10-15 мин)
    **Цель:** [Цель этапа]
    **Действия учителя:** [Конкретные инструкции]
    **Задания для студентов:** [Конкретные задания на {target_language}]

    ## 🎯 Материалы и ресурсы
    [Список всех необходимых материалов]

    ## ✅ Домашнее задание
    [Конкретное задание с инструкциями]

    ВАЖНЫЕ ТРЕБОВАНИЯ:
    
    ✅ ОБЯЗАТЕЛЬНО ВКЛЮЧАТЬ:
    - Конкретные диалоги и упражнения на {target_language}
    - Step-by-step instructions for the teacher in English
    - Ready-made materials (texts, questions, tasks)
    - Точное время для каждого этапа
    
    ❌ НЕ ИСПОЛЬЗОВАТЬ общие описания:
    - "Студенты практикуют"
    - "Учитель объясняет"
    - "Работа в парах"
    
    Создайте ПОЛНЫЙ, ДЕТАЛЬНЫЙ план урока минимум 800-1000 слов с конкретными заданиями!
    
    ИСПОЛЬЗУЙТЕ ТОЧНО ТАКУЮ СТРУКТУРУ как показано выше и заполните все секции КОНКРЕТНЫМ СОДЕРЖИМЫМ.

    ## 1. LESSON OVERVIEW (Minimum 100 words)
    - Comprehensive lesson summary including key learning objectives
    - Clear connections to previous and upcoming lessons
    - Overview of skills and language areas covered
    - Assessment overview and success criteria

    ## 2. DETAILED TIMING AND ACTIVITIES (Minimum 500 words)
    Each activity section must include:
    - Exact timing (e.g., "5 minutes", "10-12 minutes")
    - Step-by-step teacher instructions
    - Complete student instructions and examples
    - Interaction patterns (T-S, S-S, individual work, etc.)
    - Materials needed for each activity
    - Alternative activities for early finishers
    - Differentiation strategies for different ability levels

    ## 3. LANGUAGE ANALYSIS (Minimum 200 words)
    - Detailed breakdown of target grammar structures
    - Comprehensive vocabulary list with definitions and pronunciation
    - Potential pronunciation difficulties and solutions
    - Common student errors and correction strategies
    - Language functions and their appropriate contexts

    ## 4. MATERIALS AND RESOURCES (Minimum 100 words)
    - Complete list of all materials needed
    - Detailed description of handouts, worksheets, or visual aids
    - Technology requirements and backup options
    - Preparation instructions for teachers
    - Student materials checklist

    ## 5. ASSESSMENT AND FEEDBACK (Minimum 150 words)
    - Detailed assessment criteria for each objective
    - Formative assessment activities throughout the lesson
    - Summative assessment methods
    - Specific feedback strategies for different activity types
    - Self-assessment and peer assessment opportunities
    - Error correction techniques and timing

    ## 6. HOMEWORK AND FOLLOW-UP (Minimum 100 words)
    - Detailed homework assignments with clear instructions
    - Connection to lesson objectives and next lesson
    - Differentiated homework options
    - Assessment criteria for homework
    - Follow-up activities for next lesson preparation

    ## 7. CONTINGENCY PLANNING (Minimum 100 words)
    - Alternative activities if technology fails
    - Shorter activities if running out of time
    - Extension activities for fast finishers
    - Classroom management strategies for difficult situations
    - Adaptation strategies for different class sizes

    ## 8. REFLECTION AND DEVELOPMENT (Minimum 100 words)
    - Areas for teacher reflection post-lesson
    - Potential improvements for future iterations
    - Professional development connections
    - Student feedback collection methods

    QUALITY STANDARDS:
    - Total lesson plan length: MINIMUM 1500 words
    - Each activity must have specific, actionable instructions
    - Include exact questions, prompts, and student examples
    - Provide complete worksheets or activity materials in the plan
    - Use authentic, engaging contexts relevant to students' lives
    - Balance individual, pair, and group work throughout
    - Include at least 3 different activity types per lesson stage
    - Provide multiple assessment checkpoints throughout

    Make your plan extremely detailed and practical with specific activities, questions, and examples.
    Include clear instructions for each activity and estimate the time for each section.
    Focus on student-centered learning with the teacher as facilitator rather than information provider.
    Provide actual exercises, worksheets, and activities that can be used immediately in class.
    This should be a comprehensive, professional-quality lesson plan ready for immediate classroom use.

    {lesson_format_instructions}
    """

    # Отладочный вывод
    logger.info(f"Created form-based lesson plan prompt with length {len(formatted_prompt)} characters")

    return formatted_prompt

def format_prompt_lesson_plan_form_improved(data: dict) -> str:
    """
    Улучшенная функция для генерации промпта плана урока без перегрузки деталями.
    Создает качественный персонализированный контент вместо шаблонов.
    """
    target_language = data.get('language', 'English')
    
    formatted_prompt = f"""
    Создайте ДЕТАЛЬНЫЙ ПЛАН УРОКА для изучения {target_language}.
    
    You MUST use English instructions for the teacher and {target_language} для заданий студентов.
    
    Параметры урока:
    - Тема: {data.get('topic', 'Общая тема')}
    - Уровень: {data.get('level', 'intermediate')}
    - Возраст: {data.get('age', 'adults')}  
    - Продолжительность: {data.get('duration', 60)} минут
    - Грамматика: {data.get('grammar', 'не указана')}
    - Лексика: {data.get('vocabulary', 'не указана')}
    
    СТРУКТУРА ПЛАНА УРОКА:

    # [Название урока]

    ## 📋 Обзор урока  
    **Цели урока:** (3-5 конкретных целей)
    **Продолжительность:** {data.get('duration', 60)} минут
    **Уровень:** {data.get('level', 'intermediate')}
    **Тема:** {data.get('topic', 'General Topic')}

    ## ⏰ Подробное расписание урока
    
    ### 1. Разминка (5-10 мин)
    **Цель:** [Цель этапа]
    **Teacher Actions:** [Specific instructions in English]
    **Задания для студентов:** [Конкретные задания на {target_language}]
    
    ### 2. Презентация материала (15-20 мин)
    **Цель:** [Цель этапа]
    **Teacher Actions:** [Specific instructions in English]
    **Задания для студентов:** [Конкретные задания на {target_language}]
    
    ### 3. Практика (20-25 мин)
    **Цель:** [Цель этапа]
    **Teacher Actions:** [Specific instructions in English]
    **Задания для студентов:** [Конкретные задания на {target_language}]
    
    ### 4. Закрепление (10-15 мин)
    **Цель:** [Цель этапа]
    **Teacher Actions:** [Specific instructions in English]
    **Задания для студентов:** [Конкретные задания на {target_language}]

    ## 🎯 Материалы и ресурсы
    [Конкретный список всех необходимых материалов]

    ## ✅ Домашнее задание
    [Конкретное задание с инструкциями на {target_language}]
    
    ВАЖНЫЕ ТРЕБОВАНИЯ:
    
    ✅ ОБЯЗАТЕЛЬНО ВКЛЮЧАТЬ:
    - Конкретные диалоги и упражнения на {target_language}
    - Step-by-step instructions for the teacher in English
    - Ready-made materials (texts, questions, tasks)
    - Точное время для каждого этапа
    
    ❌ НЕ ИСПОЛЬЗОВАТЬ общие описания:
    - "Студенты практикуют"
    - "Учитель объясняет"
    - "Работа в парах"
    
    Создайте ПОЛНЫЙ, ДЕТАЛЬНЫЙ план урока минимум 800-1000 слов с конкретными заданиями!
    
    ИСПОЛЬЗУЙТЕ ТОЧНО ТАКУЮ СТРУКТУРУ как показано выше и заполните все секции КОНКРЕТНЫМ СОДЕРЖИМЫМ.
    
    Создайте профессиональный план урока готовый к немедленному использованию в классе.
    """
    
    return formatted_prompt

# Модель запроса для свободного запроса
class FreeQueryRequest(BaseModel):
    """Модель запроса для свободного запроса к AI"""
    language: str
    query: str
    user_id: Optional[int] = None
    with_points: Optional[bool] = False
    skip_tariff_check: Optional[bool] = False

@router.post("/generate_free_query", response_model=ContentResponse)
@check_premium_access("AI Assistant")
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("free_query", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_free_query(
    request: FreeQueryRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Обработка свободного запроса к AI-ассистенту"""
    logger.info(f"Получен свободный запрос к AI: {request.query[:50]}...")

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {current_user.id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)

    # Проверяем, нужно ли пропустить проверку тарифа
    if request.skip_tariff_check:
        logger.info(f"Skip tariff check requested for user {current_user.id}")
        # Устанавливаем атрибут skip_tariff_check в request для декораторов
        setattr(request, 'skip_tariff_check', True)

    # Всегда используем ID текущего пользователя из токена аутентификации
    user_id = current_user.id
    logger.info(f"Используем ID пользователя: {user_id} из current_user")

    # Создаем кэш-ключ на основе запроса и ID пользователя
    cache_key = f"free_query:{user_id}:{hash(request.query)}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        logger.info("Возвращаем кэшированный результат свободного запроса")
        # Проверяем, что cached_result.data.content является строкой
        if cached_result.get("data", {}).get("content") is not None and not isinstance(cached_result.get("data", {}).get("content"), str):
            cached_result["data"]["content"] = str(cached_result["data"]["content"])
        return ContentResponse(**cached_result)

    try:
        # Формируем промпт для AI
        system_instruction = """
        Ты опытный методист и консультант по языковому образованию, специализирующийся на помощи преподавателям иностранных языков.

        ТВОЯ РОЛЬ:
        - Помогать преподавателям решать методические вопросы
        - Предлагать эффективные техники обучения
        - Адаптировать материалы под разные уровни и потребности
        - Давать практические советы по организации учебного процесса

        ПРИНЦИПЫ ОТВЕТОВ:
        - Отвечай конкретно и практично, с готовыми к использованию решениями
        - Consider the specifics of working with students
        - Предлагай современные методики и подходы
        - Включай примеры и пошаговые инструкции

        ФОРМАТИРОВАНИЕ:
        - Используй Markdown для структурирования ответа
        - Применяй заголовки (##, ###) для разделения разделов
        - Используй списки для перечислений и пошаговых инструкций
        - Для сравнительных данных создавай таблицы в формате:
          | Заголовок 1 | Заголовок 2 | Заголовок 3 |
          |-------------|-------------|-------------|
          | Данные 1    | Данные 2    | Данные 3    |
        - Выделяй ключевые термины **жирным шрифтом**
        - Используй `код` для примеров упражнений или фраз

        ВАЖНО: Если создаешь таблицы, делай их компактными (максимум 4-5 колонок) и с короткими ячейками для удобства чтения на мобильных устройствах.
        """

        formatted_prompt = f"""
        {system_instruction}

        Язык: {request.language}

        Запрос пользователя: {request.query}

        Предоставь полезный и информативный ответ на этот запрос.
        Используй Markdown для форматирования ответа - заголовки, списки, жирный текст, где это уместно.
        Убедись, что твой ответ является текстовой строкой, а не JSON или другим структурированным форматом.
        """

        # Генерируем ответ
        generator = ContentGenerator(session)
        logger.info("Вызываем генератор контента для свободного запроса...")
        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=user_id,
            content_type=ContentType.TEXT_ANALYSIS,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': False}  # Свободные запросы не используют баллы
        )

        logger.info(f"Получен сгенерированный ответ для свободного запроса (длина: {len(content) if content else 'None'})")

        # Убедимся, что content является строкой
        if content is None:
            content = "Извините, не удалось сгенерировать ответ. Пожалуйста, попробуйте еще раз."
        elif not isinstance(content, str):
            logger.warning(f"Сгенерированный контент не является строкой. Тип: {type(content)}")
            content = str(content)

        # Создаем и сохраняем генерацию в базе данных
        generation = Generation(
            user_id=user_id,
            type=ContentType.TEXT_ANALYSIS,
            content=content,
            prompt=request.query,
            created_at=datetime.now(timezone.utc)
        )
        session.add(generation)
        await session.flush()  # Получаем ID генерации

        # Создаем данные ответа
        response_data = {
            "id": generation.id,
            "user_id": user_id,
            "type": ContentType.TEXT_ANALYSIS.value,
            "content": content,
            "prompt": request.query,
            "created_at": generation.created_at.isoformat()
        }

        # Логирование использования
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={
                "prompt": request.query,
                "action": "free_query",
                "with_points": request.with_points,
                "skip_tariff_check": request.skip_tariff_check
            },
            skip_limits=request.with_points or request.skip_tariff_check  # Пропускаем лимиты, если генерация за баллы или пропуск проверки тарифа
        ))

        # Фиксируем транзакцию
        await session.commit()

        # Убедимся, что данные ответа имеют правильный формат перед кэшированием
        if not isinstance(response_data["content"], str):
            response_data["content"] = str(response_data["content"])

        # Кэшируем результат
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Ответ на свободный запрос получен успешно",
            "with_points": request.with_points
        })

        logger.info("Свободный запрос обработан успешно")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Ответ на свободный запрос получен успешно",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при обработке свободного запроса: {str(e)}", exc_info=True)

        # Возвращаем понятное сообщение об ошибке в текстовом формате
        error_response = {
            "id": 0,
            "user_id": user_id,
            "type": ContentType.TEXT_ANALYSIS.value,
            "content": f"Произошла ошибка при обработке запроса: {str(e)}",
            "prompt": request.query,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return ContentResponse(
            status="error",
            data=error_response,
            message=f"Ошибка при обработке свободного запроса: {str(e)}"
        )

# Модель запроса для объяснения концепции
class ConceptExplanationRequest(BaseModel):
    """Модель запроса для объяснения концепции в удобном для понимания формате"""
    language: str
    concept: Optional[str] = None
    age: Optional[str] = None
    level: Optional[str] = None
    interests: Optional[str] = ""
    style: Optional[str] = "simple"
    user_id: Optional[int] = None
    prompt: Optional[str] = None  # JSON строка с параметрами
    type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    with_points: Optional[bool] = False
    skip_tariff_check: Optional[bool] = False
    skip_limits: Optional[bool] = False

@router.post("/generate_concept_explanation", response_model=ContentResponse)
@check_generation_limits(ContentType.TEXT_ANALYSIS)
@check_achievements(ActionType.GENERATION, ContentType.TEXT_ANALYSIS)
@track_usage(ContentType.TEXT_ANALYSIS)
@track_feature_usage("concept_explanation", ContentType.TEXT_ANALYSIS)
@memory_optimized()
async def generate_concept_explanation(
    request: ConceptExplanationRequest,
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """Обработка запроса на объяснение сложной концепции в удобном для понимания формате"""
    logger.info(f"Получен запрос на объяснение концепции")

    # Проверяем, используются ли баллы для генерации
    if request.with_points:
        logger.info(f"Generation with points requested for user {current_user.id}")
        # Устанавливаем атрибут with_points в request для декораторов
        setattr(request, 'with_points', True)
        # Если используются баллы, автоматически пропускаем проверку тарифа и лимитов
        setattr(request, 'skip_tariff_check', True)
        setattr(request, 'skip_limits', True)
        logger.info(f"Automatically skipping tariff check and limits for points-based generation")

    # Проверяем, нужно ли пропустить проверку тарифа
    elif request.skip_tariff_check:
        logger.info(f"Skip tariff check requested for user {current_user.id}")
        # Устанавливаем атрибут skip_tariff_check в request для декораторов
        setattr(request, 'skip_tariff_check', True)

    # Проверяем, нужно ли пропустить лимиты
    if request.skip_limits:
        logger.info(f"Skip limits requested for user {current_user.id}")
        # Устанавливаем атрибут skip_limits в request для декораторов
        setattr(request, 'skip_limits', True)

    # Всегда используем ID текущего пользователя из токена аутентификации
    user_id = current_user.id
    logger.info(f"Используем ID пользователя: {user_id} из current_user")

    # Извлекаем данные из prompt, если они есть и некоторых полей нет
    prompt_data = {}

    if request.prompt:
        try:
            prompt_data = json.loads(request.prompt)
            logger.info(f"Успешно извлечены данные из prompt: {prompt_data}")
        except Exception as e:
            logger.error(f"Ошибка при попытке распарсить prompt как JSON: {str(e)}")

    # Получаем все необходимые параметры, либо из основных полей, либо из prompt
    concept = request.concept or prompt_data.get("concept", "")
    age = request.age or prompt_data.get("age", "adults")
    level = request.level or prompt_data.get("level", "intermediate")
    interests = request.interests or prompt_data.get("interests", "")
    style = request.style or prompt_data.get("style", "simple")

    # Проверяем наличие обязательных параметров
    if not concept:
        logger.error("Отсутствует обязательный параметр 'concept'")
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать концепцию для объяснения"
        )

    logger.info(f"Параметры запроса: concept={concept}, age={age}, level={level}, style={style}")

    # Создаем кэш-ключ на основе запроса и ID пользователя
    cache_key = f"concept_explanation:{user_id}:{concept}:{age}:{level}:{request.language}"
    cached_result = await cache.get_cached_data(cache_key)
    if cached_result:
        logger.info("Возвращаем кэшированный результат объяснения концепции")
        # Проверяем, что cached_result.data.content является строкой
        if cached_result.get("data", {}).get("content") is not None and not isinstance(cached_result.get("data", {}).get("content"), str):
            cached_result["data"]["content"] = str(cached_result["data"]["content"])
        return ContentResponse(**cached_result)

    try:
        # Формируем промпт для AI
        system_instruction = """
        Ты опытный преподаватель иностранных языков и методист, специализирующийся на объяснении языковых концепций.
        Твоя задача - объяснить языковую концепцию (грамматику, лексику, произношение) просто, понятно и с учетом уровня владения языком ученика.

        ПРИНЦИПЫ ОБЪЯСНЕНИЯ:
        - Используй примеры из реальной жизни и практические ситуации
        - Сравнивай с родным языком ученика, где это уместно
        - Объясняй не только "как", но и "когда" и "зачем" использовать концепцию
        - Предлагай мнемонические приемы для запоминания
        - Структурируй объяснение от простого к сложному

        ФОРМАТИРОВАНИЕ:
        - Используй Markdown для структурирования (заголовки ##, ###)
        - Создавай таблицы для сравнений и систематизации:
          | Форма | Использование | Пример |
          |-------|---------------|--------|
          | ... | ... | ... |
        - Выделяй ключевые термины **жирным шрифтом**
        - Используй `код` для примеров предложений

        ВАЖНО: Делай таблицы компактными (максимум 4 колонки) для удобства чтения на мобильных устройствах.
        """

        # Определяем стиль объяснения для языковых концепций
        style_instructions = ""
        if style.lower() == "simple":
            style_instructions = "Используй максимально простой язык, базовые примеры и избегай сложной терминологии."
        elif style.lower() == "visual":
            style_instructions = "Создавай таблицы, схемы и используй визуальные метафоры для объяснения грамматических правил."
        elif style.lower() == "creative":
            style_instructions = "Используй истории, метафоры и творческие приемы для запоминания языковых правил."
        elif style.lower() == "analogy":
            style_instructions = "Объясняй через сравнения с родным языком и знакомыми понятиями."
        elif style.lower() == "practical":
            style_instructions = "Фокусируйся на практическом применении с множеством реальных примеров и упражнений."
        elif style.lower() == "humorous":
            style_instructions = "Используй юмор и забавные примеры для лучшего запоминания языковых правил."
        else:
            style_instructions = "Используй сбалансированный подход с простыми объяснениями и практическими примерами."

        # Инструкции по интересам ученика
        interests_instructions = ""
        if interests and interests.strip():
            interests_instructions = f"""
            У ученика следующие интересы: {interests}
            Используй примеры и аналогии, связанные с этими интересами, для лучшего понимания.
            """

        formatted_prompt = f"""
        {system_instruction}

        Язык объяснения: {request.language}

        Концепция для объяснения: {concept}

        Возраст ученика: {age}

        Уровень знаний: {level}

        {interests_instructions}

        {style_instructions}

        Составь объяснение языковой концепции, которое будет:
        1. Понятным для указанного уровня владения языком
        2. Структурированным (с подзаголовками ##, ###)
        3. Содержать практические примеры с переводом
        4. Включать таблицы для систематизации информации (если уместно)
        5. Содержать мнемонические приемы для запоминания
        6. Включать мини-упражнения для закрепления

        Используй Markdown для форматирования ответа - заголовки, списки, таблицы, жирный текст.
        Убедись, что твой ответ является текстовой строкой, а не JSON или другим структурированным форматом.
        """

        # Генерируем ответ
        generator = ContentGenerator(session)
        logger.info("Вызываем генератор контента для объяснения концепции...")
        content = await generator.generate_content(
            prompt=formatted_prompt,
            user_id=user_id,
            content_type=ContentType.TEXT_ANALYSIS,
            use_cache=False,
            force_queue=False,
            extra_params={'with_points': False}  # Объяснение концепций не использует баллы
        )

        logger.info(f"Получен сгенерированный ответ для объяснения концепции (длина: {len(content) if content else 'None'})")

        # Убедимся, что content является строкой
        if content is None:
            content = "Извините, не удалось сгенерировать объяснение. Пожалуйста, попробуйте еще раз."
        elif not isinstance(content, str):
            logger.warning(f"Сгенерированный контент не является строкой. Тип: {type(content)}")
            content = str(content)

        # Создаем и сохраняем генерацию в базе данных
        generation = Generation(
            user_id=user_id,
            type=ContentType.TEXT_ANALYSIS,
            content=content,
            prompt=concept,
            created_at=datetime.now(timezone.utc)
        )
        session.add(generation)
        await session.flush()  # Получаем ID генерации

        # Создаем данные ответа
        response_data = {
            "id": generation.id,
            "user_id": user_id,
            "type": ContentType.TEXT_ANALYSIS.value,
            "content": content,
            "prompt": concept,
            "created_at": generation.created_at.isoformat()
        }

        # Логирование использования
        tracker = UsageTracker(session)
        await tracker.log_usage(UsageLogCreate(
            user_id=user_id,
            action_type="generation",
            content_type=ContentType.TEXT_ANALYSIS.value,
            extra_data={"concept": concept, "action": "concept_explanation", "with_points": request.with_points},
            skip_limits=request.with_points  # Пропускаем лимиты, если генерация за баллы
        ))

        # Фиксируем транзакцию
        await session.commit()

        # Убедимся, что данные ответа имеют правильный формат перед кэшированием
        if not isinstance(response_data["content"], str):
            response_data["content"] = str(response_data["content"])

        # Кэшируем результат
        await cache.cache_data(cache_key, {
            "status": "success",
            "data": response_data,
            "message": "Объяснение концепции получено успешно",
            "with_points": request.with_points
        })

        logger.info("Объяснение концепции обработано успешно")
        return ContentResponse(
            status="success",
            data=response_data,
            message="Объяснение концепции получено успешно",
            with_points=request.with_points
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при обработке объяснения концепции: {str(e)}", exc_info=True)

        # Возвращаем понятное сообщение об ошибке в текстовом формате
        error_response = {
            "id": 0,
            "user_id": user_id,
            "type": ContentType.TEXT_ANALYSIS.value,
            "content": f"Произошла ошибка при обработке запроса: {str(e)}",
            "prompt": concept,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return ContentResponse(
            status="error",
            data=error_response,
            message=f"Ошибка при обработке объяснения концепции: {str(e)}"
        )











