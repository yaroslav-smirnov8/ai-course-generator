import logging
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

# Используем TYPE_CHECKING для избежания циклических импортов при проверке типов
if TYPE_CHECKING:
    from ...models.course import Lesson as LessonModel, Course as CourseModel # Исправлено: ...models
    from ...schemas.course import GenerateExercisesRequest # Исправлено: ...schemas
    from .generator import ContentGenerator # Предполагаем, что ContentGenerator находится здесь

from ...core.constants import ContentType # Исправлено: ...core

logger = logging.getLogger(__name__)

async def generate_exercises_content(
    lesson: "LessonModel",
    course: "CourseModel",
    request_data: "GenerateExercisesRequest",
    session: AsyncSession
) -> str:
    """
    Генерирует упражнения для урока в формате Markdown, используя контекст урока и курса.
    """
    logger.info(f"Начало генерации упражнений для урока ID: {lesson.id} - '{lesson.title}'")

    # 1. Формирование промпта для AI
    # TODO: Создать детальный промпт, включающий:
    # - Контекст: язык, уровень, аудитория, цели курса/студента
    # - Детали урока: тема, цели, грамматика, лексика
    # - Требование: сгенерировать релевантные упражнения в формате Markdown
    # - (Опционально) Учесть типы упражнений, если они будут передаваться

    prompt_parts = [
        f"Создайте ГОТОВЫЕ К ИСПОЛЬЗОВАНИЮ упражнения для урока английского языка в формате Markdown.",
        f"Упражнения должны быть детальными, с конкретными примерами и полными ответами.",
        f"Минимум 5-7 разнообразных упражнений на урок.",
        f"\nКонтекст курса:",
        f"  - Язык: {course.language}",
        f"  - Уровень: {course.level.value}",
        f"  - Аудитория: {course.target_audience.value}",
        f"  - Методология: {course.methodology or 'не указана'}",
        f"  - Возраст студентов: {course.student_age or 'не указан'}",
        f"  - Цели студентов: {course.student_goals or 'не указаны'}",
        f"  - Интересы студентов: {course.student_interests or 'не указаны'}",
        f"\nДетали урока {lesson.order}: {lesson.title}:",
        f"  - Цели урока: {', '.join(lesson.objectives) if lesson.objectives else 'не указаны'}",
        f"  - Грамматический фокус: {', '.join(lesson.grammar) if lesson.grammar else 'не указан'}",
        f"  - Лексический фокус: {', '.join(lesson.vocabulary) if lesson.vocabulary else 'не указан'}",
        f"  - Продолжительность: {lesson.duration} минут",
        f"\nТребования к упражнениям:",
        f"  - ТОЛЬКО готовые упражнения в формате Markdown, без лишних объяснений",
        f"  - Каждое упражнение должно иметь структуру:",
        f"    * ## Упражнение [номер]: [Название]",
        f"    * **Цель:** [четкая цель упражнения]",
        f"    * **Время:** [примерное время выполнения]",
        f"    * **Уровень сложности:** [легкий/средний/сложный]",
        f"    * **Инструкции:** [пошаговые инструкции для студентов]",
        f"    * **Примеры/Задания:** [конкретные задания с реальным контентом]",
        f"    * **Ответы:** [полные правильные ответы]",
        f"  - Типы упражнений должны включать:",
        f"    * Vocabulary Practice (словарные упражнения)",
        f"    * Grammar Practice (грамматические упражнения)",
        f"    * Reading Comprehension (понимание прочитанного)",
        f"    * Listening Activity (аудирование)",
        f"    * Speaking Practice (разговорная практика)",
        f"    * Writing Exercise (письменные упражнения)",
        f"    * Communication Activity (коммуникативные задания)",
        f"  - Включайте РЕАЛЬНЫЕ примеры из темы урока",
        f"  - Каждое упражнение должно содержать минимум 10-15 конкретных заданий",
        f"  - Упражнения готовы к немедленному использованию",
        f"  - Не используйте заполнители - только реальный контент"
    ]
    prompt = "\n".join(prompt_parts)
    logger.debug(f"Сформированный промпт для генерации упражнений:\n{prompt}")

    # 2. Вызов генератора контента
    # TODO: Убедиться, что ContentGenerator правильно инициализируется и вызывается
    try:
        # Предполагаем наличие инициализированного ContentGenerator
        # Возможно, его нужно будет получить через Depends или создать экземпляр
        from .generator import ContentGenerator # Импорт здесь для примера
        content_generator = ContentGenerator(session=session) # Пример инициализации

        generated_content = await content_generator.generate_content(
            content_type=ContentType.COURSE_EXERCISE, # Используем новый тип для упражнений в курсе
            prompt=prompt,
            user_id=course.creator_id # Передаем ID пользователя для отслеживания/лимитов
            # Другие параметры, если нужны (temperature, max_tokens и т.д.)
        )

        if not generated_content or not isinstance(generated_content, str):
             logger.warning(f"Генератор контента не вернул строку для упражнений урока {lesson.id}")
             raise ValueError("Failed to generate exercise content string.")

        logger.info(f"Успешно сгенерирован контент упражнений для урока {lesson.id}, длина: {len(generated_content)}")
        
        # Обрабатываем контент через ContentProcessor для получения структурированных упражнений
        try:
            from .processor import ContentProcessor
            
            # Создаем данные для обработки (похоже на формат из content.py)
            exercise_data = {
                'language': course.language,
                'level': course.level.value,
                'type': 'mixed',  # По умолчанию смешанный тип
                'quantity': 3,  # По умолчанию 3 упражнения
                'meta': {
                    'includeAnswers': True,
                    'includeInstructions': True
                }
            }
            
            # Сначала применяем базовую обработку для конвертации JSON в читаемый формат
            formatted_content = ContentProcessor.process_exercise(generated_content)
            
            # Затем обрабатываем контент и получаем структурированные упражнения
            processed_exercises = await ContentProcessor.process_exercise_content(
                formatted_content, exercise_data, logger
            )
            
            logger.info(f"Контент обработан, получено {len(processed_exercises)} структурированных упражнений")
            
            # Возвращаем как кортеж: (отформатированный контент, обработанные упражнения)
            return formatted_content, processed_exercises
            
        except Exception as e:
            logger.error(f"Ошибка при обработке упражнений: {str(e)}")
            # В случае ошибки возвращаем только исходный контент
            return generated_content, None

    except Exception as e:
        logger.error(f"Ошибка при вызове ContentGenerator для упражнений урока {lesson.id}: {e}", exc_info=True)
        # Можно пробросить ошибку дальше или вернуть стандартное сообщение
        raise ValueError(f"Error during exercise generation: {e}")
