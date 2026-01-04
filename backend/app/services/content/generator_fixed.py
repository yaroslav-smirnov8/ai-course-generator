# app/services/content/generator.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List, Union
import logging
from datetime import datetime, timedelta
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
from ...utils import G4FHandler
from youtube_transcript_api import YouTubeTranscriptApi
from ...utils.g4f_handler import MISTRAL_AVAILABLE
from ...schemas.content import TextLevelAnalysis, TitlesAnalysis, QuestionsAnalysis

logger = logging.getLogger(__name__)


class ContentGenerator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_optimizer = QueryOptimizer(session)
        self.cache_service = CacheService()
        self.batch_processor = BatchProcessor(session)
        # Initialize queue to None - we'll create it when needed
        self._generation_queue = None
        # Initialize G4FHandler
        self.g4f_handler = G4FHandler()
        # Флаг доступности G4FHandler
        self._g4f_available = True
        logger.info("ContentGenerator initialized with G4FHandler")

    async def ensure_g4f_handler(self) -> bool:
        """Проверяем и обеспечиваем доступность G4F Handler"""
        if not self._g4f_available or self.g4f_handler is None:
            logger.info("G4FHandler unavailable, attempting to reinitialize")
            return await self.refresh_g4f_handler()
        return True

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
        # Проверяем кэш, если разрешено
        if use_cache and self.cache_service:
            cache_key = f"content:{content_type.value}:{hashlib.md5(prompt.encode()).hexdigest()}"
            cached_content = await self.cache_service.get_cached_data(cache_key)
            if cached_content:
                logger.info(f"Используем закэшированный контент для пользователя {user_id}, тип {content_type.value}, длина {len(cached_content)}")
                return cached_content

        # Валидируем промпт для данного типа контента
        self._validate_prompt(prompt, content_type)

        # Определяем, как будем генерировать контент
        generation_method = None
        
        # Если принудительно используем очередь или G4FHandler недоступен
        if force_queue or not await self.ensure_g4f_handler():
            generation_method = "queue"
            logger.info(f"Используем очередь для генерации контента (force_queue={force_queue}, g4f_available={self._g4f_available})")
            content = await self._generate_with_queue(user_id, prompt, content_type)
        else:
            # Пробуем сначала через G4FHandler
            try:
                logger.info(f"Пробуем генерировать контент напрямую через G4FHandler для пользователя {user_id}")
                generation_method = "g4f"
                content = await self._generate_with_g4f(prompt, content_type)
                
                # Если не удалось, переключаемся на очередь
                if content is None:
                    logger.warning("Не удалось сгенерировать контент через G4FHandler, переключаемся на очередь")
                    generation_method = "queue_fallback"
                    content = await self._generate_with_queue(user_id, prompt, content_type)
            except Exception as e:
                logger.error(f"Ошибка при прямой генерации через G4FHandler: {str(e)}, переключаемся на очередь")
                generation_method = "queue_fallback"
                content = await self._generate_with_queue(user_id, prompt, content_type)

        # Убеждаемся, что контент не пустой
        if not content:
            raise ValidationError("Не удалось сгенерировать контент")

        # Сохраняем генерацию в базу данных
        try:
            # Проверка на None перед использованием batch_processor
            if self.session is not None:
                if self.batch_processor is None:
                    # Создаем запись о генерации напрямую
                    generation = Generation(
                        user_id=user_id,
                        type=content_type.value,
                        content=content,
                        prompt=prompt
                    )
                    self.session.add(generation)
                    await self.session.commit()
                else:
                    # Используем BatchProcessor если он доступен
                    await self.batch_processor.process_in_batches(
                        [{"user_id": user_id, "type": content_type, "content": content, "prompt": prompt}],
                        self._save_generation
                    )
        except Exception as e:
            logger.error(f"Ошибка при сохранении генерации: {str(e)}")

        # Кэшируем результат, если это разрешено
        if use_cache and self.cache_service:
            await self.cache_service.cache_data(cache_key, content, ttl=3600)  # TTL 1 час

        logger.info(f"Успешно сгенерирован контент для пользователя {user_id}, тип {content_type.value}, метод {generation_method}, длина {len(content)}")
        return content

    async def _save_generation(self, batch: List[Dict[str, Any]]) -> None:
        """Batch save generations"""
        generations = [
            Generation(
                user_id=item["user_id"],
                type=item["type"].value if hasattr(item["type"], "value") else item["type"],
                content=item["content"],
                prompt=item["prompt"],
                created_at=datetime.utcnow()
            )
            for item in batch
        ]
        self.session.add_all(generations)
        await self.session.flush()

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

    def _validate_prompt(self, prompt: str, content_type: Union[str, ContentType]) -> None:
        """Validate prompt length based on content type"""
        # Define max lengths for different content types
        max_lengths = {
            ContentType.LESSON_PLAN: 15000,  # Увеличиваем лимит для планов уроков до 15000 символов
            ContentType.EXERCISE: 15000,  # Увеличиваем лимит для упражнений до 15000 символов
            ContentType.GAME: 15000,  # Увеличиваем лимит для игр до 15000 символов
            ContentType.TRANSCRIPT: 500,
            ContentType.TEXT_ANALYSIS: 15000,  # Увеличиваем лимит для анализа текста до 15000 символов
            'lesson_plan': 15000,  # Увеличиваем лимит для планов уроков (строковый вариант) до 15000 символов
            'exercise': 15000,  # Увеличиваем лимит для упражнений (строковый вариант) до 15000 символов
            'game': 15000,  # Увеличиваем лимит для игр (строковый вариант) до 15000 символов
            'transcript': 500,
            'text_analysis': 15000,  # Увеличиваем лимит для анализа текста (строковый вариант) до 15000 символов
            'image': 200
        }

        # Get max_length based on content_type (can be string or enum)
        max_length = max_lengths.get(content_type, 500)

        if len(prompt) > max_length:
            ct_value = content_type.value if hasattr(content_type, 'value') else content_type
            raise ValidationError(f"Prompt too long for {ct_value}")

    @memory_optimized()
    async def generate_lesson_plan(
            self,
            user_id: int,
            course_id: Optional[int] = None,
            lesson_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate lesson plan with optimization"""
        try:
            # Prepare context for generation
            context = await self._prepare_lesson_context(course_id, lesson_data)

            # Create prompt
            prompt = self._create_lesson_plan_prompt(context)

            # Generate content through queue
            content = await self.generate_content(
                content_type=ContentType.LESSON_PLAN,
                prompt=prompt,
                user_id=user_id,
                extra_params=context
            )

            # Structure result
            lesson_plan = self._structure_lesson_plan(content)

            # If there's a course, link it
            if course_id:
                await self._link_lesson_to_course(
                    course_id,
                    lesson_plan
                )

            return lesson_plan

        except Exception as e:
            logger.error(f"Error generating lesson plan: {str(e)}")
            raise

    async def _prepare_lesson_context(self, course_id: Optional[int], lesson_data: Optional[Dict[
        str, Any]]) -> Dict[
        str, Any]:
        """Prepare context for lesson generation"""
        context = lesson_data or {}

        if course_id:
            # Get course information to provide context
            query = select(Course).where(Course.id == course_id)
            result = await self.session.execute(query)
            course = result.scalar_one_or_none()

            if course:
                context.update({
                    "course_title": course.title,
                    "course_description": course.description,
                    "course_level": course.level,
                    "course_language": course.language
                })

                # Get previous lessons in the course
                lessons_query = select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.id.desc()).limit(1)
                result = await self.session.execute(lessons_query)
                previous_lesson = result.scalar_one_or_none()

                if previous_lesson:
                    context["previous_lesson"] = previous_lesson.title
                    context["previous_content"] = previous_lesson.content

        return context

    def _create_lesson_plan_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for lesson plan generation"""
        prompt_template = """
        Create a detailed lesson plan with the following parameters:

        Language: {language}
        Level: {level}
        Topic: {topic}
        Previous lesson: {previous_lesson}

        Include the following sections:
        1. Lesson objectives
        2. Required materials
        3. Warm-up activity (5-10 minutes)
        4. Main activities with timing
        5. Practice activities
        6. Assessment
        7. Homework assignment
        8. Additional notes

        Make the lesson interactive, engaging, and appropriate for the specified level.
        """

        # Fill in the template with context values or defaults
        return prompt_template.format(
            language=context.get('language', 'English'),
            level=context.get('level', 'Intermediate'),
            topic=context.get('topic', 'General communication'),
            previous_lesson=context.get('previous_lesson', 'None')
        )

    def _structure_lesson_plan(self, content: str) -> Dict[str, Any]:
        """Structure the raw generated content into a lesson plan format"""
        # Simple parser for the content
        sections = {
            "title": "",
            "objectives": [],
            "materials": [],
            "warm_up": "",
            "main_activities": [],
            "practice": [],
            "assessment": "",
            "homework": "",
            "notes": ""
        }

        # Very basic parsing - in a real app, you'd want more robust parsing
        current_section = None
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to identify sections
            lower_line = line.lower()
            if "objectives" in lower_line or "goals" in lower_line:
                current_section = "objectives"
                continue
            elif "materials" in lower_line or "resources" in lower_line:
                current_section = "materials"
                continue
            elif "warm" in lower_line and ("up" in lower_line or "activity" in lower_line):
                current_section = "warm_up"
                continue
            elif "main" in lower_line and "activit" in lower_line:
                current_section = "main_activities"
                continue
            elif "practice" in lower_line:
                current_section = "practice"
                continue
            elif "assessment" in lower_line or "evaluation" in lower_line:
                current_section = "assessment"
                continue
            elif "homework" in lower_line or "assignment" in lower_line:
                current_section = "homework"
                continue
            elif "notes" in lower_line or "additional" in lower_line:
                current_section = "notes"
                continue
            elif current_section is None and not sections["title"]:
                sections["title"] = line
                continue

            # Process content based on current section
            if current_section == "objectives" and line.startswith("- "):
                sections["objectives"].append(line[2:])
            elif current_section == "materials" and line.startswith("- "):
                sections["materials"].append(line[2:])
            elif current_section == "warm_up":
                sections["warm_up"] += line + "\n"
            elif current_section == "main_activities" and line.startswith("- "):
                sections["main_activities"].append(line[2:])
            elif current_section == "practice" and line.startswith("- "):
                sections["practice"].append(line[2:])
            elif current_section == "assessment":
                sections["assessment"] += line + "\n"
            elif current_section == "homework":
                sections["homework"] += line + "\n"
            elif current_section == "notes":
                sections["notes"] += line + "\n"
            elif current_section:  # Catch-all for non-bullet points in list sections
                if current_section in ["warm_up", "assessment", "homework", "notes"]:
                    sections[current_section] += line + "\n"

        return sections

    async def _link_lesson_to_course(self, course_id: int, lesson_plan: Dict[str, Any]) -> None:
        """Link lesson to course"""
        lesson = Lesson(
            course_id=course_id,
            title=lesson_plan.get('title', ''),
            content=lesson_plan,
            created_at=datetime.utcnow()
        )
        self.session.add(lesson)
        await self.session.flush()

    @memory_optimized()
    async def generate_exercises(
            self,
            user_id: int,
            params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate exercises with optimization"""
        try:
            # Check parameters
            self._validate_exercise_params(params)

            # Create prompt
            prompt = self._create_exercises_prompt(params)

            # Generate content through queue
            content = await self.generate_content(
                content_type=ContentType.EXERCISE,
                prompt=prompt,
                user_id=user_id,
                extra_params=params
            )

            # Structure exercises
            raw_exercises = self._structure_exercises(content)
            
            # Подготовка данных для сохранения - добавляем user_id и дополнительные поля
            exercises_to_save = []
            for ex in raw_exercises:
                exercise_data = {
                    "user_id": user_id,
                    "type": ContentType.EXERCISE.value,
                    "content": ex,  # Сохраняем всю структуру упражнения
                    "prompt": prompt,  # Сохраняем промпт, который использовался для генерации
                    "difficulty": params.get("difficulty", "medium")
                }
                exercises_to_save.append(exercise_data)

            # Batch save exercises если список не пустой
            if exercises_to_save:
                await self.batch_processor.process_in_batches(
                    exercises_to_save,
                    self._save_exercises
                )

            return raw_exercises

        except Exception as e:
            logger.error(f"Error generating exercises: {str(e)}")
            raise

    async def _save_exercises(self, batch: List[Dict[str, Any]]) -> None:
        """Batch save exercises"""
        try:
            # Используем существующую модель Generation для сохранения упражнений
            generations = [
                Generation(
                    user_id=item.get("user_id"),
                    type=item.get("type"),
                    content=str(item.get("content")),  # Преобразуем словарь в строку
                    prompt=str(item.get("prompt", "")),  # Устанавливаем пустую строку, если prompt нет
                    created_at=datetime.utcnow()
                )
                for item in batch if item.get("content")
            ]
            
            if generations:
                self.session.add_all(generations)
                await self.session.flush()
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении упражнений: {str(e)}")
            raise

    def _validate_exercise_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters for exercise generation"""
        required_params = ['language', 'topic', 'difficulty', 'quantity']
        for param in required_params:
            if param not in params:
                raise ValidationError(f"Missing required parameter: {param}")

        if not 1 <= params.get('quantity', 0) <= 10:
            raise ValidationError("Quantity must be between 1 and 10")

    def _create_exercises_prompt(self, params: Dict[str, Any]) -> str:
        """Create prompt for exercise generation"""
        
        # Получаем метаданные или инициализируем пустой словарь
        meta = params.get('meta', {})
        
        # Формируем инструкции для индивидуальных/групповых занятий
        format_instruction = ""
        if params.get('individual_group') == 'individual':
            format_instruction = """
!!! IMPORTANT !!!
This is an INDIVIDUAL lesson (one-on-one teaching). The exercises should:
- Be designed for one-on-one interaction between teacher and student
- NOT include any pair or group activities
- Focus on personalized feedback and individual practice
- Avoid phrases like "work with a partner" or "discuss in groups"
            """
        elif params.get('individual_group') == 'group':
            format_instruction = """
The exercises should be designed for GROUP teaching:
- Include activities where students can work together
- Incorporate peer interaction and collaborative tasks
- Utilize group dynamics for language practice
            """
            
        # Формируем инструкции для онлайн/оффлайн занятий
        online_instruction = ""
        if params.get('online_offline') == 'online':
            online_instruction = """
The exercises should be adapted for ONLINE teaching:
- Utilize digital tools and platforms
- Be suitable for screen sharing and virtual interaction
- Consider the limitations of online communication
            """
        elif params.get('online_offline') == 'offline':
            online_instruction = """
The exercises should be adapted for OFFLINE teaching:
- Utilize physical materials and classroom resources
- Take advantage of face-to-face interaction
- Include physical movement and tactile elements when appropriate
            """
            
        # Дополнительные опции
        additional_options = ""
        if meta.get('includeAnswers', True):
            additional_options += "- Include ANSWER KEYS for all exercises\n"
        if meta.get('includeInstructions', True):
            additional_options += "- Include TEACHER INSTRUCTIONS with suggestions for implementation\n"
        if meta.get('adaptiveDifficulty', False):
            additional_options += "- Provide variations for different proficiency levels within the same exercise\n"
            
        # Выбранные типы упражнений из метаданных
        selected_types = meta.get('selectedTypes', [])
        types_instruction = ""
        if selected_types:
            types_str = ", ".join(selected_types)
            types_instruction = f"Focus on these exercise types: {types_str}"
            
        # Выбранные форматы упражнений
        selected_formats = meta.get('selectedFormats', [])
        formats_instruction = ""
        if selected_formats:
            formats_str = ", ".join(selected_formats)
            formats_instruction = f"Use these exercise formats: {formats_str}"
            
        # Основной шаблон промпта
        prompt_template = """
        Create {quantity} {difficulty} level exercises for {language} language learners.
        Topic: {topic}
Proficiency level: {proficiency}
Exercise Type: {exercise_type}

{types_instruction}
{formats_instruction}
{format_instruction}
{online_instruction}

        Each exercise should include:
1. Clear instructions for students
2. The exercise content
3. Any necessary materials or resources
{additional_options}

        Make the exercises interactive, appropriate for the level, and focused on the topic.
        """

        return prompt_template.format(
            quantity=params.get('quantity', 3),
            difficulty=params.get('difficulty', 'intermediate'),
            language=params.get('language', 'English'),
            topic=params.get('topic', 'General'),
            proficiency=meta.get('proficiency', 'intermediate'),
            exercise_type=params.get('exercise_type', 'grammar'),
            types_instruction=types_instruction,
            formats_instruction=formats_instruction,
            format_instruction=format_instruction,
            online_instruction=online_instruction,
            additional_options=additional_options
        )

    def _structure_exercises(self, content: str) -> List[Dict[str, Any]]:
        """Structure the raw generated content into exercises"""
        exercises = []

        # Журналирование для отладки
        logger.info(f"Начало парсинга упражнений. Длина контента: {len(content)} символов")
        
        try:
            # Проверка наличия разделов ответов и инструкций
            has_answers = "answers" in content.lower() or "answer key" in content.lower() or "answer keys" in content.lower()
            has_instructions = "teacher instructions" in content.lower() or "teaching notes" in content.lower()
            
            logger.info(f"Определение секций: answers={has_answers}, instructions={has_instructions}")

            # Пытаемся разделить контент на упражнения по маркерам
            # Проверяем различные формы маркеров упражнений
            if "exercise" in content.lower():
                sections = re.split(r"(?i)exercise\s*\d+[\.:]?", content)
                logger.info(f"Разделение по 'Exercise N': получено {len(sections)} секций")
            elif "упражнение" in content.lower():
                sections = re.split(r"(?i)упражнение\s*\d+[\.:]?", content)
                logger.info(f"Разделение по 'Упражнение N': получено {len(sections)} секций")
            else:
                # Если не нашли стандартных маркеров, рассматриваем весь текст как одно упражнение
                logger.info(f"Не найдены стандартные маркеры упражнений. Возвращаем весь контент как одно упражнение.")
                return [{
                    "type": "general",
                    "content": content,
                    "answers": "",
                    "instructions": ""
                }]
            
            # Убираем первую пустую секцию, если она есть
            if sections and not sections[0].strip():
                sections = sections[1:]
                
            if not sections:
                logger.warning("После разделения не найдено упражнений. Возвращаем весь контент как одно упражнение.")
                return [{
                    "type": "general",
                    "content": content,
                    "answers": "",
                    "instructions": ""
                }]
            
