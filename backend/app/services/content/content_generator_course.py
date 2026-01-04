# app/services/content/content_generator_course.py
"""
Модуль для генерации курсов и структур курсов
"""
import logging
from typing import Optional, Dict, Any, List
import json
import re

from ...core.memory import memory_optimized
from ...core.constants import ContentType

logger = logging.getLogger(__name__)


class ContentGeneratorCourse:
    """
    Миксин для генерации курсов
    """
    
    async def generate_course_structure(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует структуру курса на основе промпта

        Args:
            prompt (Dict[str, Any]): Параметры для генерации курса

        Returns:
            Dict[str, Any]: Структура курса
        """
        try:
            logger.info("Generating course structure")

            # Извлекаем параметры из основного промпта или из 'context'
            user_id = prompt.get('user_id', 1)
            context = prompt.get('context', {})

            course_title = context.get('course_name') or prompt.get('title', 'New Course')
            course_description = context.get('description') or prompt.get('description', '')
            target_level = context.get('level') or prompt.get('level', 'intermediate')
            language = context.get('language') or prompt.get('language', 'English')
            
            # Определяем количество уроков
            lessons_count = context.get('lessons_count')
            if lessons_count is None:
                duration_weeks = prompt.get('duration_weeks', 8)
                lessons_per_week = prompt.get('lessons_per_week', 2)
                lessons_count = duration_weeks * lessons_per_week
            else:
                duration_weeks = (lessons_count + 6) // 7
                lessons_per_week = 7

            # Используем 'requirements' из промпта, если он есть
            generation_prompt = prompt.get('requirements')
            if not generation_prompt:
                # Fallback, если 'requirements' нет, создаем свой промпт
                generation_prompt = self._create_course_structure_prompt(
                    course_title, course_description, target_level,
                    language, duration_weeks, lessons_per_week
                )

            # Генерируем структуру через основной метод
            content = await self.generate_content(
                content_type=ContentType.COURSE,
                prompt=generation_prompt,
                user_id=user_id,
                extra_params={
                    'title': course_title,
                    'level': target_level,
                    'language': language,
                    'total_lessons': lessons_count,
                    **prompt.get('extra_params', {})
                }
            )

            # --- ДОБАВЛЕНО ЛОГИРОВАНИЕ СЫРОГО КОНТЕНТА ---
            logger.info(f"=== ОТЛАДКА: Сырой контент от AI ===")
            logger.info(f"Длина контента: {len(content) if content else 0}")
            logger.info(f"Тип контента: {type(content)}")
            if content:
                logger.info(f"Первые 300 символов: {content[:300]}")
                logger.info(f"Последние 300 символов: {content[-300:]}")
            # --- КОНЕЦ ЛОГИРОВАНИЯ СЫРОГО КОНТЕНТА ---

            # Структурируем результат
            course_structure = self._structure_course_content(content, prompt)

            # --- ДОБАВЛЕНО ЛОГИРОВАНИЕ СТРУКТУРИРОВАННОГО КОНТЕНТА ---
            logger.info(f"=== ОТЛАДКА: Структурированный контент ===")
            logger.info(f"Ключи структуры: {list(course_structure.keys()) if isinstance(course_structure, dict) else 'Не словарь'}")
            if isinstance(course_structure, dict):
                logger.info(f"Содержит 'lessons': {'lessons' in course_structure}")
                if 'lessons' in course_structure:
                    logger.info(f"Количество уроков в структуре: {len(course_structure['lessons']) if isinstance(course_structure['lessons'], list) else 'Не список'}")
            # --- КОНЕЦ ЛОГИРОВАНИЯ СТРУКТУРИРОВАННОГО КОНТЕНТА ---

            logger.info(f"Successfully generated course structure for: {course_title}")
            return course_structure

        except Exception as e:
            logger.error(f"Error generating course structure: {str(e)}")
            raise

    def _create_course_structure_prompt(
        self,
        title: str,
        description: str,
        level: str,
        language: str,
        duration_weeks: int,
        lessons_per_week: int
    ) -> str:
        """Создает промпт для генерации структуры курса в формате JSON"""

        total_lessons = duration_weeks * lessons_per_week

        prompt = f"""
Create a comprehensive course structure for a {language} language course.

Course Details:
- Title: {title}
- Description: {description}
- Target Level: {level}
- Total lessons: {total_lessons}

Please create a detailed course structure with exactly {total_lessons} lessons.

IMPORTANT: You must return the response in the following JSON format:
{{
    "title": "{title}",
    "description": "{description}",
    "level": "{level}",
    "language": "{language}",
    "total_lessons": {total_lessons},
    "lessons": [
        {{
            "title": "Lesson Title 1",
            "lesson_number": 1,
            "objectives": ["Objective 1", "Objective 2"],
            "vocabulary": ["word1", "phrase1"],
            "grammar": ["Grammar topic 1"],
            "activities": [
                {{
                    "name": "Activity Name",
                    "duration": 15,
                    "description": "Activity description"
                }}
            ],
            "materials": ["Material 1", "Material 2"],
            "homework": {{
                "description": "Homework description",
                "tasks": ["Task 1", "Task 2"]
            }},
            "duration": 60
        }}
    ]
}}

IMPORTANT:
- The response must be ONLY a valid JSON.
- You must include the "lessons" field with an array of lessons.
- Each lesson must contain all the specified fields.
- Create exactly {total_lessons} lessons.
"""

        return prompt

    def _structure_course_content(self, content: str, original_prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Структурирует сгенерированный контент курса"""
        try:
            # Сначала пытаемся извлечь JSON из контента
            lessons = self._extract_lessons_from_content(content, original_prompt)

            # Базовая структура курса
            course_structure = {
                "title": original_prompt.get('title', 'New Course'),
                "description": original_prompt.get('description', ''),
                "level": original_prompt.get('level', 'intermediate'),
                "language": original_prompt.get('language', 'English'),
                "duration_weeks": original_prompt.get('duration_weeks', 8),
                "lessons_per_week": original_prompt.get('lessons_per_week', 2),
                "total_lessons": original_prompt.get('duration_weeks', 8) * original_prompt.get('lessons_per_week', 2),
                "content": content,
                "structure": self._parse_course_sections(content),
                "lessons": lessons,  # ДОБАВЛЕНО: поле lessons
                "created_by": "AI Generator",
                "status": "draft"
            }

            # Логируем результат
            logger.info(f"Структурирован курс с {len(lessons)} уроками")

            return course_structure

        except Exception as e:
            logger.error(f"Error structuring course content: {str(e)}")
            # Возвращаем базовую структуру при ошибке с пустыми уроками
            return {
                "title": original_prompt.get('title', 'New Course'),
                "content": content,
                "lessons": [],  # ДОБАВЛЕНО: пустой массив уроков при ошибке
                "error": str(e)
            }

    def _extract_lessons_from_content(self, content: str, original_prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлекает уроки из сгенерированного контента"""
        lessons = []

        try:
            # Сначала пытаемся найти JSON в контенте
            json_lessons = self._try_extract_json_lessons(content)
            if json_lessons:
                logger.info(f"Извлечено {len(json_lessons)} уроков из JSON")
                # Нормализуем структуру уроков
                normalized_lessons = self._normalize_lessons(json_lessons)
                return normalized_lessons

            # Если JSON не найден, парсим текстовый контент
            text_lessons = self._parse_text_lessons(content, original_prompt)
            if text_lessons:
                logger.info(f"Извлечено {len(text_lessons)} уроков из текста")
                return text_lessons

            # Если ничего не найдено, создаем базовые уроки
            fallback_lessons = self._create_fallback_lessons(original_prompt)
            logger.warning(f"Создано {len(fallback_lessons)} базовых уроков как fallback")
            return fallback_lessons

        except Exception as e:
            logger.error(f"Error extracting lessons: {str(e)}")
            return self._create_fallback_lessons(original_prompt)

    def _try_extract_json_lessons(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """Пытается извлечь уроки из JSON в контенте"""
        try:
            import json
            import re

            # Ищем JSON блоки в контенте
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```',
                r'(\{[^{}]*"lessons"[^{}]*\[.*?\][^{}]*\})',
                r'(\{.*?"lessons".*?\})'
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, dict) and 'lessons' in data:
                            lessons = data['lessons']
                            if isinstance(lessons, list) and lessons:
                                return lessons
                    except json.JSONDecodeError:
                        continue

            # Пытаемся парсить весь контент как JSON
            try:
                data = json.loads(content.strip())
                if isinstance(data, dict) and 'lessons' in data:
                    lessons = data['lessons']
                    if isinstance(lessons, list):
                        return lessons
            except json.JSONDecodeError:
                pass

        except Exception as e:
            logger.debug(f"JSON extraction failed: {str(e)}")

        return None

    def _normalize_lessons(self, lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Нормализует структуру уроков, добавляя недостающие обязательные поля
        """
        normalized_lessons = []
        
        try:
            for i, lesson in enumerate(lessons):
                if not isinstance(lesson, dict):
                    continue
                
                normalized_lesson = {
                    'title': lesson.get('title', f'Lesson {i + 1}'),
                    'lesson_number': lesson.get('lesson_number', i + 1),
                    'objectives': lesson.get('objectives', []),
                    'vocabulary': lesson.get('vocabulary', lesson.get('lexica', [])),  # AI использует 'lexica' вместо 'vocabulary'
                    'grammar': lesson.get('grammar', []),
                    'activities': lesson.get('activities', []),
                    'materials': lesson.get('materials', []),
                    'homework': lesson.get('homework', {}),
                    'duration': lesson.get('duration', 60)
                }
                
                # Нормализуем objectives - должен быть список
                if isinstance(normalized_lesson['objectives'], str):
                    normalized_lesson['objectives'] = [normalized_lesson['objectives']]
                elif not isinstance(normalized_lesson['objectives'], list):
                    normalized_lesson['objectives'] = []
                
                # Нормализуем vocabulary - должен быть список
                if isinstance(normalized_lesson['vocabulary'], str):
                    normalized_lesson['vocabulary'] = [normalized_lesson['vocabulary']]
                elif not isinstance(normalized_lesson['vocabulary'], list):
                    normalized_lesson['vocabulary'] = []
                
                # Нормализуем grammar - должен быть список
                if isinstance(normalized_lesson['grammar'], str):
                    normalized_lesson['grammar'] = [normalized_lesson['grammar']]
                elif not isinstance(normalized_lesson['grammar'], list):
                    normalized_lesson['grammar'] = []
                
                # Нормализуем activities - должен быть список словарей
                if not isinstance(normalized_lesson['activities'], list):
                    normalized_lesson['activities'] = []
                
                # Добавляем базовые активности если их нет
                if not normalized_lesson['activities']:
                    normalized_lesson['activities'] = [
                        {
                            'name': f'Main Activity {i + 1}',
                            'duration': 45,
                            'description': f'Core learning activity for lesson {i + 1}'
                        },
                        {
                            'name': f'Practice Activity {i + 1}',
                            'duration': 15,
                            'description': f'Practice exercises for lesson {i + 1}'
                        }
                    ]
                
                # Нормализуем materials - должен быть список
                if isinstance(normalized_lesson['materials'], str):
                    normalized_lesson['materials'] = [normalized_lesson['materials']]
                elif not isinstance(normalized_lesson['materials'], list):
                    normalized_lesson['materials'] = ['Textbook', 'Audio materials', 'Worksheets']
                
                # Добавляем базовые материалы если их нет
                if not normalized_lesson['materials']:
                    normalized_lesson['materials'] = ['Textbook', 'Audio materials', 'Worksheets']
                
                # Нормализуем homework - должен быть словарь с description и tasks
                if not isinstance(normalized_lesson['homework'], dict):
                    normalized_lesson['homework'] = {}
                
                if 'description' not in normalized_lesson['homework']:
                    normalized_lesson['homework']['description'] = f'Complete exercises related to lesson {i + 1}'
                
                if 'tasks' not in normalized_lesson['homework']:
                    normalized_lesson['homework']['tasks'] = [f'Exercise {i + 1}.1', f'Exercise {i + 1}.2']
                elif not isinstance(normalized_lesson['homework']['tasks'], list):
                    normalized_lesson['homework']['tasks'] = [f'Exercise {i + 1}.1', f'Exercise {i + 1}.2']
                
                normalized_lessons.append(normalized_lesson)
            
            logger.info(f"Нормализовано {len(normalized_lessons)} уроков")
            return normalized_lessons
            
        except Exception as e:
            logger.error(f"Ошибка при нормализации уроков: {str(e)}")
            return lessons  # Возвращаем исходные уроки при ошибке

    def _parse_text_lessons(self, content: str, original_prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Парсит уроки из текстового контента"""
        lessons = []

        try:
            # Ищем паттерны уроков в тексте
            lesson_patterns = [
                r'(?:\u0423\u0440\u043e\u043a|Lesson)\s*(\d+)[:\.]?\s*([^\n]+)',
                r'(?:\u0417\u0430\u043d\u044f\u0442\u0438\u0435|Class)\s*(\d+)[:\.]?\s*([^\n]+)',
                r'(\d+)\.\s*([^\n]+)'
            ]

            # Убираем проблемные символы из content
            cleaned_lines = []
            for line in content.split('\n'):
                # Удаляем невидимые символы, мусорные control chars, кроме обычного текста и знаков препинания
                clean_line = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u0400-\u04FF]+', '', line)
                cleaned_lines.append(clean_line)

            lines = cleaned_lines
            current_lesson = None
            lesson_content = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Проверяем, начинается ли новый урок
                lesson_found = False
                for pattern in lesson_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        # Сохраняем предыдущий урок
                        if current_lesson:
                            current_lesson['content'] = '\n'.join(lesson_content)
                            lessons.append(current_lesson)

                        # Начинаем новый урок
                        current_lesson = {
                            'title': match.group(2).strip(),
                            'lesson_number': int(match.group(1)),
                            'objectives': [],
                            'vocabulary': [],
                            'grammar': [],
                            'activities': [],
                            'materials': [],
                            'homework': '',
                            'duration': original_prompt.get('lesson_duration', 60)
                        }
                        lesson_content = []
                        lesson_found = True
                        break

                if not lesson_found and current_lesson:
                    lesson_content.append(line)

            # Добавляем последний урок
            if current_lesson:
                current_lesson['content'] = '\n'.join(lesson_content)
                lessons.append(current_lesson)

            # Если не найдено ни одного урока, создаем базовые по количеству уроков
            if not lessons:
                total_lessons = original_prompt.get('duration_weeks', 8) * original_prompt.get('lessons_per_week', 2)
                for i in range(1, min(total_lessons + 1, 13)):
                    lessons.append({
                        'title': f'Lesson {i}',
                        'lesson_number': i,
                        'objectives': [f'Learn key concepts for lesson {i}'],
                        'vocabulary': [f'Vocabulary for lesson {i}'],
                        'grammar': [f'Grammar focus for lesson {i}'],
                        'activities': [{
                            'name': f'Activity {i}',
                            'duration': 60,
                            'description': f'Learning activities for lesson {i}'
                        }],
                        'materials': ['Basic materials'],
                        'homework': {
                            'description': f'Practice exercises for lesson {i}',
                            'tasks': [f'Exercise {i}.1', f'Exercise {i}.2']
                        },
                        'duration': original_prompt.get('lesson_duration', 60)
                    })

        except Exception as e:
            logger.error(f"Error parsing text lessons: {str(e)}")
            # Возвращаем пустой список при ошибке
            lessons = []

        return lessons

    def _create_fallback_lessons(self, original_prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создает базовые уроки как fallback"""
        lessons = []

        try:
            total_lessons = original_prompt.get('duration_weeks', 8) * original_prompt.get('lessons_per_week', 2)
            course_title = original_prompt.get('title', 'New Course')
            level = original_prompt.get('level', 'intermediate')
            language = original_prompt.get('language', 'English')

            for i in range(1, min(total_lessons + 1, 13)):  # Максимум 12 уроков
                lesson = {
                    'title': f'{course_title} - Lesson {i}',
                    'lesson_number': i,
                    'objectives': [
                        f'Learn basic {language} concepts for {level} level',
                        f'Practice communication skills',
                        f'Build vocabulary and grammar foundation'
                    ],
                    'vocabulary': [
                        f'Key vocabulary for lesson {i}',
                        f'Common phrases and expressions',
                        f'Topic-specific terminology'
                    ],
                    'grammar': [
                        f'Grammar focus for lesson {i}',
                        f'Sentence structures',
                        f'Language patterns'
                    ],
                    'activities': [
                        {
                            'name': f'Warm-up Activity {i}',
                            'duration': 10,
                            'description': f'Introduction and review for lesson {i}'
                        },
                        {
                            'name': f'Main Activity {i}',
                            'duration': 35,
                            'description': f'Core learning activity for lesson {i}'
                        },
                        {
                            'name': f'Practice Activity {i}',
                            'duration': 15,
                            'description': f'Practice and consolidation for lesson {i}'
                        }
                    ],
                    'materials': [
                        'Textbook',
                        'Audio materials',
                        'Visual aids',
                        'Worksheets'
                    ],
                    'homework': {
                        'description': f'Complete exercises related to lesson {i} topics',
                        'tasks': [f'Exercise {i}.1', f'Exercise {i}.2']
                    },
                    'duration': original_prompt.get('lesson_duration', 60)
                }
                lessons.append(lesson)

            logger.info(f"Created {len(lessons)} fallback lessons")

        except Exception as e:
            logger.error(f"Error creating fallback lessons: {str(e)}")
            # Создаем хотя бы один урок
            lessons = [{
                'title': 'Basic Lesson',
                'lesson_number': 1,
                'objectives': ['Learn basic concepts'],
                'vocabulary': ['Basic vocabulary'],
                'grammar': ['Basic grammar'],
                'activities': [{'name': 'Basic Activity', 'duration': 60, 'description': 'Basic learning activity'}],
                'materials': ['Basic materials'],
                'homework': {'description': 'Basic homework', 'tasks': ['Task 1', 'Task 2']},
                'duration': 60
            }]

        return lessons

    def _parse_course_sections(self, content: str) -> Dict[str, Any]:
        """Парсит секции курса из сгенерированного контента"""
        try:
            sections = {
                "overview": "",
                "weekly_breakdown": [],
                "lesson_structure": "",
                "resources": [],
                "assessment": ""
            }
            
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Определяем секции по заголовкам
                line_lower = line.lower()
                if 'overview' in line_lower and line.startswith('#'):
                    if current_section and current_content:
                        self._add_section_content(sections, current_section, '\n'.join(current_content))
                    current_section = 'overview'
                    current_content = []
                elif 'weekly' in line_lower and line.startswith('#'):
                    if current_section and current_content:
                        self._add_section_content(sections, current_section, '\n'.join(current_content))
                    current_section = 'weekly_breakdown'
                    current_content = []
                elif 'lesson structure' in line_lower and line.startswith('#'):
                    if current_section and current_content:
                        self._add_section_content(sections, current_section, '\n'.join(current_content))
                    current_section = 'lesson_structure'
                    current_content = []
                elif 'resource' in line_lower and line.startswith('#'):
                    if current_section and current_content:
                        self._add_section_content(sections, current_section, '\n'.join(current_content))
                    current_section = 'resources'
                    current_content = []
                elif 'assessment' in line_lower and line.startswith('#'):
                    if current_section and current_content:
                        self._add_section_content(sections, current_section, '\n'.join(current_content))
                    current_section = 'assessment'
                    current_content = []
                else:
                    current_content.append(line)
            
            # Добавляем последнюю секцию
            if current_section and current_content:
                self._add_section_content(sections, current_section, '\n'.join(current_content))
            
            return sections
            
        except Exception as e:
            logger.error(f"Error parsing course sections: {str(e)}")
            return {"content": content}

    def _add_section_content(self, sections: Dict[str, Any], section: str, content: str):
        """Добавляет контент в соответствующую секцию"""
        if section == 'weekly_breakdown':
            # Парсим недельную разбивку
            weeks = []
            week_lines = content.split('\n')
            current_week = None
            
            for line in week_lines:
                if line.strip().lower().startswith('week'):
                    if current_week:
                        weeks.append(current_week)
                    current_week = {
                        "title": line.strip(),
                        "content": []
                    }
                elif current_week and line.strip():
                    current_week["content"].append(line.strip())
            
            if current_week:
                weeks.append(current_week)
            
            sections[section] = weeks
        elif section == 'resources':
            # Парсим ресурсы как список
            resources = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            sections[section] = resources
        else:
            sections[section] = content

    @memory_optimized()
    async def generate_summaries(
        self,
        texts: list,
        summary_type: str = "brief",
        language: str = "en",
        **kwargs
    ) -> list:
        """
        Генерирует краткие изложения для списка текстов

        Args:
            texts (list): Список текстов для суммаризации
            summary_type (str): Тип суммаризации
            language (str): Язык суммаризации
            **kwargs: Дополнительные параметры

        Returns:
            list: Список кратких изложений
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Generating {len(texts)} summaries of type: {summary_type}")

            summaries = []
            
            for i, text in enumerate(texts):
                try:
                    # Создаем промпт для каждого текста
                    prompt = self._create_batch_summary_prompt(text, summary_type, language, i + 1)
                    
                    # Генерируем суммаризацию
                    summary = await self.generate_content(
                        content_type=ContentType.TEXT_ANALYSIS,
                        prompt=prompt,
                        user_id=user_id,
                        extra_params={
                            "summary_type": summary_type,
                            "language": language,
                            "batch_index": i
                        }
                    )
                    
                    summaries.append({
                        "original_text": text[:100] + "..." if len(text) > 100 else text,
                        "summary": summary,
                        "index": i
                    })
                    
                except Exception as e:
                    logger.error(f"Error summarizing text {i}: {str(e)}")
                    summaries.append({
                        "original_text": text[:100] + "..." if len(text) > 100 else text,
                        "summary": f"Error generating summary: {str(e)}",
                        "index": i,
                        "error": True
                    })

            return summaries

        except Exception as e:
            logger.error(f"Error generating summaries: {str(e)}")
            raise

    def _create_batch_summary_prompt(self, text: str, summary_type: str, language: str, index: int) -> str:
        """Создает промпт для суммаризации в батче"""
        
        type_instructions = {
            "brief": "Create a brief summary in 1-2 sentences",
            "detailed": "Create a detailed summary covering main points",
            "bullet_points": "Create a summary using bullet points"
        }
        
        instruction = type_instructions.get(summary_type, type_instructions["brief"])
        
        prompt = f"""
Text #{index} Summary Task:

{instruction} of the following text in {language} language.

Text to summarize:
{text}

Summary:
"""
        
        return prompt
