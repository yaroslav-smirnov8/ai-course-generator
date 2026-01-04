# backend/app/services/content/lesson_plan_generator.py
import logging
from typing import Dict, Any, Optional, List
from ...models.course import Lesson, Course
from ...core.constants import ContentType
from .generator import ContentGenerator # Предполагаем, что основной генератор здесь
from ...core.database import get_db # Для возможного доступа к сессии, если нужно
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

def get_lesson_stages(methodology: Optional[str]) -> str:
    """Возвращает структуру стадий урока в зависимости от методологии."""
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

        'communicative': default_stages, # Пример
        # ... другие методологии ...
    }
    # Приводим к нижнему регистру и проверяем наличие
    methodology_key = methodology.lower() if methodology else ""
    return methodology_stages.get(methodology_key, default_stages)

async def format_lesson_plan_prompt(lesson: Lesson, course: Course, session: AsyncSession) -> str:
    """
    Форматирует промпт для генерации детального плана конкретного урока курса с использованием новой системы контекста.
    Включает контекст предыдущих уроков и полную информацию о курсе.
    """
    from sqlalchemy import select
    from ...api.v1.content import format_prompt_lesson_plan_form_improved
    from ...utils.course_context import format_course_context_prompt
    from ...core.constants import ContentType

    # Получаем предыдущие уроки для контекста
    previous_lessons_query = select(Lesson).where(
        Lesson.course_id == course.id,
        Lesson.order < lesson.order
    ).order_by(Lesson.order.desc()).limit(3)
    
    previous_lessons_result = await session.execute(previous_lessons_query)
    previous_lessons = previous_lessons_result.scalars().all()

    # Получаем следующий урок для лучшего планирования переходов
    next_lesson_query = select(Lesson).where(
        Lesson.course_id == course.id,
        Lesson.order > lesson.order
    ).order_by(Lesson.order).limit(1)
    
    next_lesson_result = await session.execute(next_lesson_query)
    next_lesson = next_lesson_result.scalar_one_or_none()

    # Извлекаем данные урока и курса с более полной информацией
    language = course.language or 'English'
    level = course.level.value if course.level else 'intermediate'
    topic = lesson.title or 'General Topic'
    duration = lesson.duration or course.lesson_duration or 60
    objectives = lesson.objectives or []
    grammar = lesson.grammar or []
    vocabulary = lesson.vocabulary or []
    methodology = course.methodology or 'communicative'
    target_audience = course.target_audience.value if course.target_audience else 'adults'
    lesson_format = course.format.value if course.format else 'online'

    # Формируем контекст предыдущих уроков
    previous_lessons_context = ""
    if previous_lessons:
        previous_lessons_context = "Previous lessons covered:\n"
        for prev_lesson in reversed(previous_lessons):  # Показываем в хронологическом порядке
            prev_grammar = ', '.join(prev_lesson.grammar) if prev_lesson.grammar else 'None'
            prev_vocab = ', '.join(prev_lesson.vocabulary) if prev_lesson.vocabulary else 'None'
            previous_lessons_context += f"- Lesson {prev_lesson.order}: {prev_lesson.title} (Grammar: {prev_grammar}, Vocabulary: {prev_vocab})\n"

    # Формируем контекст следующего урока
    next_lesson_context = ""
    if next_lesson:
        next_grammar = ', '.join(next_lesson.grammar) if next_lesson.grammar else 'None'
        next_vocab = ', '.join(next_lesson.vocabulary) if next_lesson.vocabulary else 'None'
        next_lesson_context = f"Next lesson will cover: {next_lesson.title} (Grammar: {next_grammar}, Vocabulary: {next_vocab})"

    # Преобразуем данные в формат для улучшенной функции
    form_data = {
        'language': language,
        'level': level,
        'topic': topic,
        'previous_lesson': previous_lessons_context,
        'age': target_audience,
        'methodology': [methodology] if methodology else [],
        'individual_group': 'group',  # По умолчанию, можно добавить в модель курса
        'online_offline': lesson_format,
        'duration': duration,
        'grammar': ', '.join(grammar) if grammar else '',
        'vocabulary': ', '.join(vocabulary) if vocabulary else '',
        'exam': course.exam_prep or course.custom_exam or ''
    }

    # Получаем улучшенный промпт
    enhanced_prompt = format_prompt_lesson_plan_form_improved(form_data)

    # Добавляем расширенную специфическую информацию о курсе и уроке
    course_context = f"""

    DETAILED COURSE CONTEXT:
    Course: {course.name}
    Course Description: {course.description or 'Not specified'}
    Course Level: {level}
    Course Language: {language}
    Total Course Duration: {course.total_duration} minutes
    Lesson {lesson.order} of {course.total_lessons if hasattr(course, 'total_lessons') else 'unknown'}

    LESSON CONTEXT:
    Lesson Title: {lesson.title}
    Lesson Duration: {duration} minutes
    Lesson Order: {lesson.order}
    Lesson Objectives: {', '.join(objectives) if objectives else 'Not specified'}
    Grammar Focus: {', '.join(grammar) if grammar else 'Not specified'}
    Vocabulary Focus: {', '.join(vocabulary) if vocabulary else 'Not specified'}
    Materials Available: {', '.join(lesson.materials) if lesson.materials else 'Standard classroom materials'}

    COURSE LEARNING PROGRESSION:
    {previous_lessons_context}
    {next_lesson_context}

    DETAILED COURSE INFORMATION:
    Student Age Group: {course.student_age or 'Not specified'}
    Student Interests: {course.student_interests or 'Not specified'}
    Student Goals: {course.student_goals or 'Not specified'}
    Common Student Mistakes: {course.common_mistakes or 'Not specified'}
    Exam Preparation: {course.exam_prep or course.custom_exam or 'Not specified'}
    
    Course Learning Outcomes: {', '.join(course.learning_outcomes) if course.learning_outcomes else 'Not specified'}
    Course Prerequisites: {', '.join(course.prerequisites) if course.prerequisites else 'None'}
    Main Course Topics: {course.main_topics or 'Not specified'}
    Course Grammar Focus: {course.grammar_focus or 'Not specified'}
    Course Vocabulary Focus: {course.vocabulary_focus or 'Not specified'}
    
    Skills Included:
    - Speaking: {'Yes' if course.include_speaking else 'No'}
    - Listening: {'Yes' if course.include_listening else 'No'}
    - Reading: {'Yes' if course.include_reading else 'No'}
    - Writing: {'Yes' if course.include_writing else 'No'}
    - Games: {'Yes' if course.include_games else 'No'}

    DETAILED LESSON PLAN REQUIREMENTS:
    This lesson is part of a structured course. The lesson plan must:
    1. Build upon knowledge from previous lessons and prepare for upcoming content
    2. Be highly detailed with specific timings, instructions, and activities
    3. Include comprehensive teacher notes and student instructions
    4. Provide detailed assessment criteria and homework assignments
    5. Include backup activities and differentiation strategies
    6. Specify exact materials and resources needed
    7. Contain step-by-step instructions for each activity
    8. Include interaction patterns (individual/pair/group work)
    9. Provide language analysis and anticipated problems
    10. Include detailed feedback and error correction strategies
    """

    # Объединяем улучшенный промпт с расширенным контекстом курса
    final_prompt = enhanced_prompt + course_context

    logger.debug(f"Generated enhanced lesson plan prompt for lesson {lesson.id}: {final_prompt[:500]}...")
    return final_prompt.strip()

async def generate_lesson_plan_content(
    lesson: Lesson,
    course: Course,
    session: AsyncSession # Передаем сессию для ContentGenerator
) -> str:
    """
    Генерирует контент плана урока, используя ContentGenerator.
    """
    prompt = await format_lesson_plan_prompt(lesson, course, session)
    # Важно: ContentGenerator должен быть инициализирован с сессией
    generator = ContentGenerator(session=session) 

    try:
        # Используем user_id из курса или урока, если доступно, иначе можно использовать ID админа или системный ID
        user_id = course.creator_id or 1 # Пример: используем ID создателя курса или 1 по умолчанию

        content = await generator.generate_content(
            prompt=prompt,
            user_id=user_id, # Необходимо передать user_id
            content_type=ContentType.COURSE_LESSON_PLAN, # Используем новый тип для планов в курсе
            use_cache=False, # Возможно, стоит добавить кэширование позже
            force_queue=False # Или True, в зависимости от нагрузки
        )
        # TODO: Добавить обработку ошибок и парсинг/валидацию ответа AI, если нужно
        # Убедимся, что возвращается строка
        if content is None:
             logger.warning(f"AI returned None for lesson plan {lesson.id}")
             return "Error: AI failed to generate lesson plan content."
        elif not isinstance(content, str):
             logger.warning(f"AI returned non-string content for lesson plan {lesson.id}: {type(content)}")
             return str(content) # Преобразуем в строку на всякий случай
        
        # Возвращаем контент без дополнительной обработки format_markdown для API
        # (format_markdown предназначен для Telegram бота, а не для мини-приложения)
        logger.info(f"Lesson plan content generated successfully for lesson {lesson.id}")
        return content
    except Exception as e:
        logger.error(f"Error generating lesson plan content for lesson {lesson.id}: {e}", exc_info=True)
        raise # Пробрасываем ошибку дальше для обработки в API
