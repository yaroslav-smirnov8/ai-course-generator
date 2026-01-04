"""
Утилиты для работы с контекстом курса в промптах
"""
from typing import Dict, Any, Optional
from ..core.constants import ContentType


def format_course_context_prompt(
    base_prompt: str,
    course_data: Optional[Dict[str, Any]] = None,
    content_type: Optional[ContentType] = None,
    lesson_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Формирует промпт с контекстом курса для специализированных воркеров
    
    Args:
        base_prompt: Базовый промпт пользователя
        course_data: Данные курса (название, описание, цели, уровень, и т.д.)
        content_type: Тип генерируемого контента
        lesson_info: Информация об уроке (номер, тема, предыдущие уроки)
        
    Returns:
        str: Расширенный промпт с контекстом курса
    """
    
    # Определяем тип контента для специфичных инструкций
    content_descriptions = {
        ContentType.COURSE_LESSON_PLAN: "план урока в рамках курса",
        ContentType.COURSE_EXERCISE: "упражнения для урока курса", 
        ContentType.COURSE_GAME: "игры для урока курса"
    }
    
    content_description = content_descriptions.get(content_type, "контент курса")
    
    # Начинаем формировать контекст
    context_parts = []
    
    # Добавляем информацию о курсе, если есть
    if course_data:
        context_parts.append("=== КОНТЕКСТ КУРСА ===")
        
        if course_data.get('title'):
            context_parts.append(f"**Название курса:** {course_data['title']}")
            
        if course_data.get('description'):
            context_parts.append(f"**Описание курса:** {course_data['description']}")
            
        if course_data.get('level'):
            context_parts.append(f"**Уровень курса:** {course_data['level']}")
            
        if course_data.get('target_audience'):
            context_parts.append(f"**Целевая аудитория:** {course_data['target_audience']}")
            
        if course_data.get('goals'):
            goals_text = "\n".join([f"- {goal}" for goal in course_data['goals']])
            context_parts.append(f"**Цели курса:**\n{goals_text}")
            
        if course_data.get('methodology'):
            context_parts.append(f"**Методология:** {course_data['methodology']}")
            
        if course_data.get('duration'):
            context_parts.append(f"**Продолжительность:** {course_data['duration']}")
            
        # Добавляем информацию о пройденном материале
        if course_data.get('completed_lessons'):
            completed = course_data['completed_lessons']
            if completed:
                completed_text = "\n".join([f"- Урок {i+1}: {lesson}" for i, lesson in enumerate(completed)])
                context_parts.append(f"**Пройденные уроки:**\n{completed_text}")
                
        # Добавляем грамматику и лексику курса
        if course_data.get('grammar_covered'):
            grammar_text = ", ".join(course_data['grammar_covered'])
            context_parts.append(f"**Изученная грамматика:** {grammar_text}")
            
        if course_data.get('vocabulary_areas'):
            vocab_text = ", ".join(course_data['vocabulary_areas'])
            context_parts.append(f"**Лексические области:** {vocab_text}")
    
    # Добавляем информацию об уроке, если есть
    if lesson_info:
        context_parts.append("\n=== КОНТЕКСТ УРОКА ===")
        
        if lesson_info.get('lesson_number'):
            context_parts.append(f"**Номер урока:** {lesson_info['lesson_number']}")
            
        if lesson_info.get('lesson_topic'):
            context_parts.append(f"**Тема урока:** {lesson_info['lesson_topic']}")
            
        if lesson_info.get('lesson_goals'):
            goals_text = "\n".join([f"- {goal}" for goal in lesson_info['lesson_goals']])
            context_parts.append(f"**Цели урока:**\n{goals_text}")
            
        if lesson_info.get('grammar_focus'):
            context_parts.append(f"**Грамматический фокус:** {lesson_info['grammar_focus']}")
            
        if lesson_info.get('vocabulary_focus'):
            context_parts.append(f"**Лексический фокус:** {lesson_info['vocabulary_focus']}")
            
        if lesson_info.get('skills_focus'):
            skills_text = ", ".join(lesson_info['skills_focus'])
            context_parts.append(f"**Развиваемые навыки:** {skills_text}")
            
        if lesson_info.get('previous_lesson_summary'):
            context_parts.append(f"**Предыдущий урок:** {lesson_info['previous_lesson_summary']}")
            
        if lesson_info.get('next_lesson_preview'):
            context_parts.append(f"**Следующий урок:** {lesson_info['next_lesson_preview']}")
    
    # Формируем итоговый промпт
    if context_parts:
        context_text = "\n".join(context_parts)
        enhanced_prompt = f"""{context_text}

=== ЗАДАЧА ===
Создай {content_description} с учетом всей вышеуказанной информации о курсе и уроке.

**Пользовательский запрос:**
{base_prompt}

**ВАЖНО:** 
- Используй всю информацию о курсе для создания релевантного и связного контента
- Учитывай уровень студентов и уже изученный материал  
- Обеспечь логическую связь с предыдущими и следующими уроками
- Следуй методологии курса
- Создавай контент, готовый к использованию в классе"""
        
        return enhanced_prompt
    else:
        # Если контекста нет, возвращаем оригинальный промпт
        return base_prompt


def extract_course_context_from_request(request_data: Dict[str, Any]) -> tuple[
    Optional[Dict[str, Any]], 
    Optional[Dict[str, Any]]
]:
    """
    Извлекает контекст курса и урока из данных запроса
    
    Args:
        request_data: Данные запроса
        
    Returns:
        tuple: (course_data, lesson_info)
    """
    course_data = None
    lesson_info = None
    
    # Ищем данные курса в разных местах запроса
    if 'course_context' in request_data:
        course_data = request_data['course_context']
    elif 'course' in request_data:
        course_data = request_data['course']
    elif 'courseData' in request_data:
        course_data = request_data['courseData']
        
    # Ищем информацию об уроке
    if 'lesson_context' in request_data:
        lesson_info = request_data['lesson_context']
    elif 'lesson' in request_data:
        lesson_info = request_data['lesson']
    elif 'lessonInfo' in request_data:
        lesson_info = request_data['lessonInfo']
        
    return course_data, lesson_info


def is_course_content_type(content_type: ContentType) -> bool:
    """
    Проверяет, является ли тип контента частью курса
    
    Args:
        content_type: Тип контента
        
    Returns:
        bool: True если это контент курса
    """
    course_content_types = {
        ContentType.COURSE_LESSON_PLAN,
        ContentType.COURSE_EXERCISE, 
        ContentType.COURSE_GAME
    }
    
    return content_type in course_content_types


def get_course_content_requirements() -> Dict[str, str]:
    """
    Возвращает требования к разным типам контента курса
    
    Returns:
        Dict: Словарь с требованиями для каждого типа
    """
    return {
        ContentType.COURSE_LESSON_PLAN: """
        - Интеграция с общими целями курса
        - Связь с предыдущими и следующими уроками
        - Использование накопленного словаря и грамматики
        - Прогрессивное увеличение сложности
        - Рециклинг материала из предыдущих уроков
        """,
        
        ContentType.COURSE_EXERCISE: """
        - Закрепление материала текущего урока
        - Повторение материала предыдущих уроков
        - Подготовка к материалу следующих уроков
        - Соответствие уровню курса
        - Разнообразие типов упражнений
        """,
        
        ContentType.COURSE_GAME: """
        - Мотивация и вовлечение студентов
        - Закрепление материала в игровой форме
        - Развитие коммуникативных навыков
        - Командная работа и интеракция
        - Соответствие возрасту и уровню
        """
    }