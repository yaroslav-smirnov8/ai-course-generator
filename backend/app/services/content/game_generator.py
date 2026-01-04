import logging
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

# Используем TYPE_CHECKING для избежания циклических импортов при проверке типов
if TYPE_CHECKING:
    from ...models.course import Lesson as LessonModel, Course as CourseModel
    from ...schemas.course import GenerateGameRequest # Убираем GeneratedGameResponse

from ...core.constants import ContentType

logger = logging.getLogger(__name__)

async def generate_game_content(
    lesson: "LessonModel",
    course: "CourseModel",
    request_data: "GenerateGameRequest",
    session: AsyncSession
) -> str: # Возвращаем строку Markdown
    """
    Генерирует описание и правила игры для урока в формате Markdown,
    используя контекст урока, курса и запрошенный тип игры.
    """
    logger.info(f"Начало генерации игры (Markdown) для урока ID: {lesson.id} - '{lesson.title}'. Запрошенный тип: {request_data.game_type}")

    # 1. Формирование промпта для AI
    game_type_request = request_data.game_type or "any relevant type"
    prompt_parts = [
        f"Создайте детальную ГОТОВУЮ К ИСПОЛЬЗОВАНИЮ игру для урока английского языка в формате Markdown.",
        f"Игра должна быть полноценной, с конкретными примерами и готовыми материалами.",
        f"Запрошенный тип игры: '{game_type_request}'.",
        f"Если тип 'any relevant type', выберите подходящий тип (matching, quiz, true/false, crossword, role-play, word search, grammar race).",
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
        f"\nТребования к выводу:",
        f"  - ТОЛЬКО готовая игра в формате Markdown, без лишних объяснений",
        f"  - Начните с заголовка '# [Название игры]'",
        f"  - Обязательные секции:",
        f"    * **Тип игры:** [конкретный тип]",
        f"    * **Время:** [продолжительность]",  
        f"    * **Участники:** [количество]",
        f"    * **Цель игры:** [четкая цель]",
        f"    * **Материалы:** [конкретный список]",
        f"    * **Правила игры:** [пошаговые инструкции]",
        f"    * **Примеры заданий:** [минимум 10-15 конкретных примеров]",
        f"    * **Подведение итогов:** [как определить победителя]",
        f"    * **Вариации:** [2-3 способа адаптации игры]",
        f"  - Включите РЕАЛЬНЫЕ примеры слов, предложений, вопросов из темы урока",
        f"  - Игра должна быть готова к немедленному использованию на уроке",
        f"  - Не используйте заполнители типа '[пример]' - только реальный контент"
    ]
    prompt = "\n".join(prompt_parts)
    logger.debug(f"Сформированный промпт для генерации игры (Markdown):\n{prompt}")

    # 2. Вызов генератора контента
    try:
        from .generator import ContentGenerator
        content_generator = ContentGenerator(session=session)

        generated_content = await content_generator.generate_content(
            content_type=ContentType.COURSE_GAME, # Используем новый тип для игр в курсе
            prompt=prompt,
            user_id=course.creator_id
        )

        if not generated_content or not isinstance(generated_content, str):
             logger.warning(f"Генератор контента не вернул строку для игры урока {lesson.id}")
             # Возвращаем сообщение об ошибке в Markdown
             return "### Error\n\nFailed to generate game content."

        logger.info(f"Успешно сгенерирован Markdown игры для урока {lesson.id}, длина: {len(generated_content)}")
        
        # Обрабатываем контент через ContentProcessor для получения структурированной информации об игре
        try:
            from .processor import ContentProcessor
            
            # Создаем данные для обработки
            game_data = {
                'language': course.language,
                'level': course.level.value,
                'game_type': request_data.game_type,
                'target_audience': course.target_audience.value
            }
            
            # Сначала применяем базовую обработку для конвертации JSON в читаемый формат
            formatted_content = ContentProcessor.process_game(generated_content)
            
            # Затем обрабатываем контент и получаем структурированную информацию об игре
            processed_game = await ContentProcessor.process_game_content(
                formatted_content, game_data, logger
            )
            
            logger.info(f"Игра обработана: тип='{processed_game.get('game_type', 'не определен')}', название='{processed_game.get('title', 'Без названия')}'")
            
            # Возвращаем как кортеж: (отформатированный контент, обработанная игра)
            return formatted_content.strip(), processed_game
            
        except Exception as e:
            logger.error(f"Ошибка при обработке игры: {str(e)}")
            # В случае ошибки возвращаем только исходный контент
            return generated_content.strip(), None

    except Exception as e:
        logger.error(f"Ошибка при вызове ContentGenerator для игры урока {lesson.id}: {e}", exc_info=True)
        # Возвращаем сообщение об ошибке в Markdown
        return f"### Error\n\nAn error occurred during game generation: {e}"
