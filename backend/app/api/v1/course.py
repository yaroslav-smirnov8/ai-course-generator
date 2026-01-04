# app/api/v1/courses.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query # Добавляем Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from ...core.database import get_db
from ...services.course.manager import CourseManager

# Настраиваем логгер
logger = logging.getLogger(__name__)
from ...schemas.course import (
    CourseCreate,
    Course,
    CourseUpdate,
    LessonCreate,
    Lesson, # Убедимся, что Lesson импортирован здесь
    Template,
    TemplateCreate,
    LessonMaterialsResponse, # Добавляем импорт схемы ответа для материалов
    # Импорты для генерации упражнений
    GenerateExercisesRequest,
    GeneratedExercisesResponse,
    LessonContextForGeneration,
    CourseContextForGeneration,
    # Импорты для генерации игр
    GenerateGameRequest,
    GeneratedGameResponse
)
from ...core.security import get_current_user
from ...core.exceptions import NotFoundException
# Импортируем переименованные декораторы для генератора курсов
from ...core.decorators import (
    check_course_generation_limits,
    track_course_usage,
    check_course_achievements
)
from ...decorators.premium_access import check_premium_access
# TODO: Импортировать оригинальные декораторы (check_generation_limits и т.д.) после их восстановления из Git
from ...core.constants import ContentType, ActionType
from ...core.memory import memory_optimized

router = APIRouter()

@router.post("/courses/generate", response_model=Course)
@check_premium_access("Course Generator")
@check_course_generation_limits(ContentType.COURSE) # Изменено
@track_course_usage(ContentType.COURSE)             # Изменено
@check_course_achievements(ActionType.GENERATION, ContentType.COURSE) # Изменено
@memory_optimized()
async def generate_course(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    course_data: CourseCreate = None
):
    """Генерирует структуру курса"""
    # Получаем данные из тела запроса, если course_data не передан
    if course_data is None:
        course_data_dict = await request.json()
        course_data = CourseCreate(**course_data_dict)

    async with CourseManager(session) as course_manager:
        try:
            return await course_manager.generate_course_structure(
                course_data,
                current_user.id
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

# --- НОВЫЙ РОУТ ДЛЯ МАТЕРИАЛОВ УРОКА ---
@router.get("/lessons/{lesson_id}/materials", response_model="LessonMaterialsResponse") # Используем строку для response_model
@track_course_usage(ContentType.LESSON_MATERIAL) # Изменено
@memory_optimized()
async def get_lesson_materials(
    lesson_id: int,
    types: Optional[List[str]] = Query(None, description="Типы материалов для генерации (e.g., exercises, presentation, handouts)"),
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user) # Добавляем аутентификацию
):
    """Получает или генерирует материалы для указанного урока."""
    # Импорты внутри функции
    import logging
    import traceback
    from fastapi import HTTPException, status, Query # Добавляем Query
    from typing import List, Optional # Убедимся, что List и Optional импортированы
    from ...schemas.course import LessonMaterialsResponse # Импортируем схему ответа
    from ...services.course.manager import CourseManager
    from ...core.exceptions import NotFoundException, ValidationError
    from ...core.constants import ContentType # Импортируем ContentType

    logger = logging.getLogger(__name__)
    logger.info(f"Запрос материалов для урока {lesson_id}, типы: {types}")

    async with CourseManager(session) as course_manager:
        try:
            # TODO: Доработать метод generate_lesson_materials в CourseManager,
            # чтобы он принимал 'types' и возвращал структуру LessonMaterialsResponse
            # Пока вызываем существующий метод, предполагая, что он вернет нужную структуру
            # или его нужно будет адаптировать.
            # Передаем все возможные типы, если types не указан
            requested_types = types if types else ["exercises", "presentation", "handouts", "assessments"]

            materials_data = await course_manager.generate_lesson_materials(
                lesson_id=lesson_id,
                types=requested_types # Передаем запрошенные типы
            )

            # Преобразуем результат в Pydantic модель (если manager возвращает dict)
            # Если manager уже возвращает Pydantic модель, эта строка не нужна
            response_data = LessonMaterialsResponse(lesson_id=lesson_id, **materials_data)

            return response_data

        except NotFoundException as e:
            logger.warning(f"Урок {lesson_id} не найден при запросе материалов: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValidationError as e:
             logger.error(f"Ошибка валидации при генерации материалов для урока {lesson_id}: {e}")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Ошибка генерации материалов для урока {lesson_id}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла внутренняя ошибка при генерации материалов урока."
            )
# --- КОНЕЦ НОВОГО РОУТА ДЛЯ МАТЕРИАЛОВ ---

# --- НОВЫЙ РОУТ ДЛЯ ЭКСПОРТА КУРСА ---
@router.get("/courses/{course_id}/export")
# @check_course_generation_limits(...) # Изменено (если раскомментировать)
@track_course_usage(ContentType.COURSE_EXPORT) # Изменено
@memory_optimized()
async def export_course_data(
    request: Request, # Добавляем параметр request для декоратора track_course_usage
    course_id: int,
    format: str = Query(..., description="Формат экспорта ('pdf' или 'docx')", pattern="^(pdf|docx)$"),
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user) # Добавляем аутентификацию
):
    """Экспортирует данные курса в указанном формате."""
    # Импорты внутри функции
    import logging
    import traceback
    from fastapi import HTTPException, status, Query
    from fastapi.responses import StreamingResponse # Для возврата файла
    import io # Для работы с байтами в памяти
    from ...services.course.manager import CourseManager
    from ...core.exceptions import NotFoundException, ValidationError
    from ...core.constants import ContentType # Импортируем ContentType

    logger = logging.getLogger(__name__)
    logger.info(f"Запрос на экспорт курса {course_id} в формате {format} от пользователя {current_user.id}")

    async with CourseManager(session) as course_manager:
        try:
            # Вызываем метод export_course из CourseManager
            logger.info(f"Вызов course_manager.export_course для курса {course_id} в формате {format}")
            file_content_bytes, filename = await course_manager.export_course(course_id, format)

            # Определяем MIME-тип на основе формата
            if format == 'pdf':
                media_type = "application/pdf"
            else: # docx
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

            if not file_content_bytes:
                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось сгенерировать файл для экспорта.")

            # Возвращаем файл как StreamingResponse
            # Используем ASCII-совместимое имя файла для заголовка Content-Disposition
            # Это решает проблему с кодировкой кириллицы в HTTP-заголовках
            return StreamingResponse(
                io.BytesIO(file_content_bytes),
                media_type=media_type,
                headers={'Content-Disposition': f'attachment; filename="{filename}"'}
            )

        except NotFoundException as e:
            logger.warning(f"Курс {course_id} не найден при запросе экспорта: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValidationError as e:
             logger.error(f"Ошибка валидации при экспорте курса {course_id}: {e}")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Ошибка экспорта курса {course_id}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла внутренняя ошибка при экспорте курса."
            )
# --- КОНЕЦ НОВОГО РОУТА ДЛЯ ЭКСПОРТА ---

# --- НОВЫЙ ЭНДПОИНТ ДЛЯ ГЕНЕРАЦИИ ПЛАНА УРОКА КУРСА ---
@router.post("/lessons/{lesson_id_in_path}/generate_plan", response_model=Lesson) # Возвращаем обновленный урок
@check_course_generation_limits(ContentType.COURSE_LESSON_PLAN) # Используем новый тип для планов в курсе
@track_course_usage(ContentType.COURSE_LESSON_PLAN)             # Используем новый тип для планов в курсе
@check_course_achievements(ActionType.GENERATION, ContentType.COURSE_LESSON_PLAN) # Используем новый тип для планов в курсе
@memory_optimized()
async def generate_plan_for_course_lesson(
    lesson_id_in_path: int, # Изменено здесь
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Генерирует детальный план для конкретного урока в рамках курса."""
    lesson_id = lesson_id_in_path # Добавлено для совместимости
    # Импорты внутри функции
    import logging
    import traceback
    from fastapi import HTTPException, status
    from ...services.course.manager import CourseManager
    from ...services.content.lesson_plan_generator import generate_lesson_plan_content # Импортируем новую функцию
    from ...core.exceptions import NotFoundException
    from ...models.course import Lesson # Импортируем модель Lesson
    from sqlalchemy.orm import selectinload # Добавлено
    from sqlalchemy import select # Добавлено

    logger = logging.getLogger(__name__)
    logger.info(f"Запрос на генерацию плана для урока {lesson_id} от пользователя {current_user.id}")

    # async with CourseManager(session) as course_manager: # CourseManager больше не нужен здесь для получения урока
    try:
        # 1. Получаем урок и связанный курс напрямую через сессию
        query = select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.course))
        result = await session.execute(query)
        lesson = result.scalar_one_or_none()

        if not lesson or not lesson.course:
            raise NotFoundException(f"Урок с ID {lesson_id} или связанный курс не найдены.")

        # Проверяем, принадлежит ли курс текущему пользователю (или админ)
        # if lesson.course.creator_id != current_user.id and not current_user.is_admin:
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")

        # 2. Генерируем контент плана урока
        logger.info(f"Вызов generate_lesson_plan_content для урока {lesson_id}")
        generated_plan_content = await generate_lesson_plan_content(
            lesson=lesson,
            course=lesson.course,
            session=session # Передаем сессию
        )
        # ЛОГ: Результат генератора (первые 100 символов, если строка)
        log_content_preview = generated_plan_content[:100] + '...' if isinstance(generated_plan_content, str) else generated_plan_content
        logger.info(f"generate_lesson_plan_content вернул (тип: {type(generated_plan_content)}): {log_content_preview}")

        # 3. Обновляем поле 'plan_content' в модели Lesson
        lesson.plan_content = generated_plan_content # <-- ИСПОЛЬЗУЕМ НОВОЕ ПОЛЕ
        logger.info(f"Поле plan_content для урока {lesson_id} обновлено. Тип: {type(lesson.plan_content)}") # Добавил лог типа

        # 4. Сохраняем изменения урока
        session.add(lesson)
        await session.commit()
        logger.info(f"Изменения для урока {lesson_id} сохранены.")

        # 5. Expire объекта lesson, чтобы гарантировать перезагрузку из БД при следующем доступе
        session.expire(lesson)
        logger.info(f"Урок {lesson_id} помечен как expired.")

        # 6. Повторно получаем урок из БД после expire, чтобы гарантировать прикрепление к сессии
        # и загрузку всех необходимых полей для Pydantic модели
        refetch_query = select(Lesson).where(Lesson.id == lesson_id).options(
            selectinload(Lesson.course),
            selectinload(Lesson.activities)
        )
        refetch_result = await session.execute(refetch_query)
        refetched_lesson = refetch_result.scalar_one_or_none()

        if not refetched_lesson:
             # Этого не должно произойти, если commit прошел успешно, но добавим проверку
             logger.error(f"Не удалось повторно получить урок {lesson_id} после expire.")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении обновленного урока.")
        else:
              logger.info(f"Урок {lesson_id} успешно повторно получен после expire.")

        # 7. Вручную создаем словарь ответа из данных refetched_lesson
        # Это обходит потенциальные проблемы с автоматической сериализацией Pydantic/FastAPI
        logger.info(f"Создание словаря ответа для урока {lesson_id}...")
        response_data = {
            "id": refetched_lesson.id,
            "title": refetched_lesson.title,
            "duration": refetched_lesson.duration,
            "order": refetched_lesson.order,
            "objectives": refetched_lesson.objectives,
            "grammar": refetched_lesson.grammar,
            "vocabulary": refetched_lesson.vocabulary,
            "materials": refetched_lesson.materials,
            "homework": refetched_lesson.homework,
            "course_id": refetched_lesson.course_id,
            "is_completed": refetched_lesson.is_completed,
            "created_at": refetched_lesson.created_at,
            "updated_at": refetched_lesson.updated_at,
            "plan_content": refetched_lesson.plan_content, # Убедимся, что plan_content включен
            "activities": []
        }

        # Вручную создаем словари для активностей
        if refetched_lesson.activities:
             logger.info(f"Обработка {len(refetched_lesson.activities)} активностей для урока {lesson_id}...")
             for activity_orm in refetched_lesson.activities:
                 # Важно: Убедимся, что все поля активности доступны и не вызовут DetachedInstanceError
                 # Если есть сомнения, можно добавить .options(selectinload(Lesson.activities)) в запрос refetch_query
                 activity_dict = {
                     "id": activity_orm.id,
                     "name": activity_orm.name,
                     "type": activity_orm.type,
                     "duration": activity_orm.duration,
                     "description": activity_orm.description,
                     "materials": activity_orm.materials,
                     "objectives": activity_orm.objectives,
                     "lesson_id": activity_orm.lesson_id,
                     "created_at": activity_orm.created_at,
                     "updated_at": activity_orm.updated_at
                 }
                 response_data["activities"].append(activity_dict)
        else:
             logger.info(f"Активности для урока {lesson_id} отсутствуют.")

        logger.info(f"Словарь ответа для урока {lesson_id} успешно создан.")
        # ЛОГ: Содержимое словаря перед возвратом
        logger.debug(f"Возвращаемый response_data для урока {lesson_id}: {response_data}")

        # 8. Возвращаем словарь
        # FastAPI автоматически проверит его соответствие response_model=Lesson
        return response_data

    except NotFoundException as e:
        logger.warning(f"Урок с ID {lesson_id} не найден при запросе генерации плана: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка генерации плана для урока {lesson_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла внутренняя ошибка при генерации плана урока."
        )
# --- КОНЕЦ НОВОГО ЭНДПОИНТА ДЛЯ ГЕНЕРАЦИИ ПЛАНА УРОКА ---


# --- НОВЫЙ ЭНДПОИНТ ДЛЯ ГЕНЕРАЦИИ УПРАЖНЕНИЙ УРОКА ---
@router.post("/lessons/{lesson_id}/generate_exercises", response_model=GeneratedExercisesResponse)
@check_course_generation_limits(ContentType.EXERCISE) # Изменено
@track_course_usage(ContentType.EXERCISE)             # Изменено
# @check_course_achievements(ActionType.GENERATION, ContentType.EXERCISE) # Изменено (если раскомментировать)
@memory_optimized()
async def generate_exercises_for_course_lesson(
    lesson_id: int,
    request_data: GenerateExercisesRequest, # Используем новую схему запроса
    request: Request, # Добавляем зависимость Request
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Генерирует упражнения для конкретного урока в рамках курса, используя контекст."""
    # Импорты внутри функции
    import logging
    import traceback
    from fastapi import HTTPException, status
    from ...services.content.exercise_generator import generate_exercises_content # Импортируем генератор упражнений
    from ...core.exceptions import NotFoundException
    from ...models.course import Lesson as LessonModel # Используем псевдоним, чтобы избежать конфликта с Pydantic схемой
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select

    logger = logging.getLogger(__name__)
    logger.info(f"Запрос на генерацию упражнений для урока {lesson_id} от пользователя {current_user.id}")

    try:
        # 1. Получаем урок и связанный курс напрямую через сессию
        # Используем request_data для получения деталей, если они нужны генератору,
        # но для получения ORM модели используем lesson_id
        query = select(LessonModel).where(LessonModel.id == lesson_id).options(selectinload(LessonModel.course))
        result = await session.execute(query)
        lesson_orm = result.scalar_one_or_none()

        if not lesson_orm or not lesson_orm.course:
            raise NotFoundException(f"Урок с ID {lesson_id} или связанный курс не найдены.")

        # Проверка доступа (опционально)
        # if lesson_orm.course.creator_id != current_user.id and not current_user.is_admin:
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")

        # 2. Вызываем функцию-генератор упражнений
        logger.info(f"Вызов generate_exercises_content для урока {lesson_id}")
        result = await generate_exercises_content(
            lesson=lesson_orm, # Передаем ORM модель урока
            course=lesson_orm.course, # Передаем ORM модель курса
            request_data=request_data, # Передаем детали из запроса, если нужны
            session=session
        )
        
        # Обрабатываем результат - может быть строка или кортеж (контент, обработанные_упражнения)
        if isinstance(result, tuple):
            generated_exercises_md, processed_exercises = result
            logger.info(f"generate_exercises_content вернул контент длиной {len(generated_exercises_md)} и {len(processed_exercises) if processed_exercises else 0} обработанных упражнений")
        else:
            generated_exercises_md = result
            processed_exercises = None
            logger.info(f"generate_exercises_content вернул контент длиной {len(generated_exercises_md)}")

        # 3. Формируем и возвращаем ответ
        response_data = GeneratedExercisesResponse(
            exercises_content=generated_exercises_md,
            processed_exercises=processed_exercises
        )
        logger.debug(f"Возвращаемый response_data для упражнений урока {lesson_id}: {response_data}")
        return response_data

    except NotFoundException as e:
        logger.warning(f"Урок с ID {lesson_id} не найден при запросе генерации упражнений: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка генерации упражнений для урока {lesson_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка при генерации упражнений для урока."
        )
# --- КОНЕЦ НОВОГО ЭНДПОИНТА ДЛЯ ГЕНЕРАЦИИ УПРАЖНЕНИЙ ---


# --- НОВЫЙ ЭНДПОИНТ ДЛЯ ГЕНЕРАЦИИ ИГРЫ УРОКА ---
@router.post("/lessons/{lesson_id}/generate_game", response_model=GeneratedGameResponse)
@check_course_generation_limits(ContentType.GAME) # Изменено
@track_course_usage(ContentType.GAME)             # Изменено
# @check_course_achievements(ActionType.GENERATION, ContentType.GAME) # Изменено (если раскомментировать)
@memory_optimized()
async def generate_game_for_course_lesson(
    lesson_id: int,
    request_data: GenerateGameRequest, # Используем новую схему запроса
    request: Request, # Добавляем зависимость Request
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Генерирует игру для конкретного урока в рамках курса, используя контекст."""
    # Импорты внутри функции
    import logging
    import traceback
    from fastapi import HTTPException, status
    from ...services.content.game_generator import generate_game_content # Импортируем генератор игр
    from ...core.exceptions import NotFoundException
    from ...models.course import Lesson as LessonModel
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select

    logger = logging.getLogger(__name__)
    logger.info(f"Запрос на генерацию игры для урока {lesson_id} от пользователя {current_user.id}. Тип игры: {request_data.game_type}")

    try:
        # 1. Получаем урок и связанный курс
        query = select(LessonModel).where(LessonModel.id == lesson_id).options(selectinload(LessonModel.course))
        result = await session.execute(query)
        lesson_orm = result.scalar_one_or_none()

        if not lesson_orm or not lesson_orm.course:
            raise NotFoundException(f"Урок с ID {lesson_id} или связанный курс не найдены.")

        # 2. Вызываем функцию-генератор игр
        logger.info(f"Вызов generate_game_content для урока {lesson_id}")
        result = await generate_game_content(
            lesson=lesson_orm,
            course=lesson_orm.course,
            request_data=request_data, # Передаем тип игры и др. параметры
            session=session
        )
        
        # Обрабатываем результат - может быть строка или кортеж (контент, обработанная_игра)
        if isinstance(result, tuple):
            game_response, processed_game = result
            logger.info(f"generate_game_content вернул контент длиной {len(game_response)} и обработанную игру типа '{processed_game.get('game_type', 'не определен') if processed_game else 'None'}'")
            extracted_game_type = processed_game.get('game_type') if processed_game else None
        else:
            game_response = result
            processed_game = None
            extracted_game_type = None
            logger.info(f"generate_game_content вернул контент игры длиной {len(game_response)}")

        # 3. Формируем и возвращаем ответ в соответствии с обновленной схемой
        response_data = GeneratedGameResponse(
            game_content=game_response, 
            game_type=extracted_game_type,
            processed_game=processed_game
        )
        logger.debug(f"Возвращаемый response_data для игры урока {lesson_id}: {response_data.game_content[:100]}...") # Логируем начало контента
        return response_data

    except NotFoundException as e:
        logger.warning(f"Урок с ID {lesson_id} не найден при запросе генерации игры: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка генерации игры для урока {lesson_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка при генерации игры для урока."
        )
# --- КОНЕЦ НОВОГО ЭНДПОИНТА ДЛЯ ГЕНЕРАЦИИ ИГРЫ ---


# --- НОВЫЙ РОУТ ---
@router.post("/courses/{course_id}/lessons/next_batch", response_model=List[Lesson])
@check_course_generation_limits(ContentType.COURSE) # Изменено
@track_course_usage(ContentType.COURSE)             # Изменено
# @check_course_achievements(...) # Оставляем оригинальный или переименованный, если он тут нужен
@memory_optimized()
async def generate_next_lessons_batch(
    course_id: int,
    request_data: "NextBatchRequest", # Используем строку для отложенной аннотации, если схема в том же файле или импортируется ниже
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Генерирует следующую порцию уроков для указанного курса."""
    # Импортируем здесь, если нужно
    import logging
    import traceback
    from fastapi import HTTPException, status
    from ...schemas.course import NextBatchRequest, Lesson # Убедимся, что схема импортирована
    from ...services.course.manager import CourseManager # Убедимся, что менеджер импортирован
    from ...core.exceptions import NotFoundException, ValidationError # Убедимся, что исключения импортированы

    logger = logging.getLogger(__name__) # Получаем логгер

    logger.info(f"Получен запрос на генерацию следующей части уроков для курса {course_id} от пользователя {current_user.id}")
    async with CourseManager(session) as course_manager:
        try:
            # Вызываем новый метод в CourseManager
            new_lessons = await course_manager.generate_next_batch(
                course_id=course_id,
                current_lesson_count=request_data.current_lesson_count,
                user_id=current_user.id
                # batch_size можно передать из request_data или использовать дефолтный в manager
            )
            if not new_lessons:
                 logger.info(f"Для курса {course_id} больше нет уроков для генерации или AI не вернул уроки.")
                 return []

            logger.info(f"Успешно сгенерировано {len(new_lessons)} уроков для курса {course_id}")
            return new_lessons

        except NotFoundException as e:
            logger.warning(f"Курс {course_id} не найден при запросе генерации следующей части: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValidationError as e:
             logger.error(f"Ошибка валидации при генерации следующей части для курса {course_id}: {e}")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Ошибка генерации следующей части уроков для курса {course_id}: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Произошла внутренняя ошибка при генерации следующей части уроков."
            )
# --- КОНЕЦ НОВОГО РОУТА ---

@router.post("/courses", response_model=Course)
async def create_course(
    course_data: CourseCreate,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Создает новый курс"""
    async with CourseManager(session) as course_manager:
        try:
            return await course_manager.create_course(course_data, current_user.id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

@router.get("/courses/{course_id}", response_model=Course)
async def get_course(
    course_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Получает курс по ID"""
    async with CourseManager(session) as course_manager:
        course = await course_manager.get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        return course

@router.put("/courses/{course_id}", response_model=Course)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обновляет существующий курс"""
    async with CourseManager(session) as course_manager:
        try:
            # Обновляем курс
            updated_course = await course_manager.update_course(course_id, course_data)
            if not updated_course:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )

            # Логируем успешное обновление
            logger.info(f"Course {course_id} successfully updated by user {current_user.id}")

            # Возвращаем обновленный курс
            return updated_course
        except Exception as e:
            logger.error(f"Error updating course {course_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Удаляет курс"""
    async with CourseManager(session) as course_manager:
        try:
            success = await course_manager.delete_course(course_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found"
                )
            return {"message": "Course deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

@router.get("/courses/{course_id}/progress")
async def get_course_progress(
    course_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Получает прогресс по курсу"""
    async with CourseManager(session) as course_manager:
        try:
            return await course_manager.get_course_progress(course_id)
        except NotFoundException as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
