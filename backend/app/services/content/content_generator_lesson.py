# app/services/content/content_generator_lesson.py
"""
Модуль для генерации планов уроков
"""
import logging
import re
from typing import Optional, Dict, Any, List
from sqlalchemy import select

from ...models import Course, Lesson
from ...core.memory import memory_optimized
from ...core.constants import ContentType
from ...core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ContentGeneratorLesson:
    """
    Миксин для генерации планов уроков
    """
    
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
        """Create prompt for lesson plan generation with methodology-specific criteria"""

        # Используем улучшенную функцию из content.py
        from ...api.v1.content import format_prompt_lesson_plan_form

        # Преобразуем context в формат, ожидаемый format_prompt_lesson_plan_form
        form_data = {
            'topic': context.get('topic', ''),
            'language': context.get('language', 'English'),
            'level': context.get('level', 'Beginner'),
            'duration': context.get('duration', 60),
            'methodology': context.get('methodology', 'Communicative'),
            'focus_skills': context.get('focus_skills', []),
            'materials': context.get('materials', []),
            'homework': context.get('homework', False),
            'assessment': context.get('assessment', False),
            'notes': context.get('notes', ''),
            'exam_name': context.get('exam_name', ''),
            'course_title': context.get('course_title', ''),
            'course_description': context.get('course_description', ''),
            'course_level': context.get('course_level', ''),
            'course_language': context.get('course_language', ''),
            'previous_lesson': context.get('previous_lesson', ''),
            'previous_content': context.get('previous_content', '')
        }

        return format_prompt_lesson_plan_form(form_data)

    def _structure_lesson_plan(self, content: str) -> Dict[str, Any]:
        """Structure lesson plan content into organized format"""
        try:
            # Базовая структура плана урока
            lesson_plan = {
                "title": "",
                "objective": "",
                "duration": 60,
                "materials": [],
                "stages": [],
                "homework": "",
                "assessment": "",
                "notes": "",
                "content": content
            }

            # Попытка извлечь структурированную информацию из контента
            lines = content.split('\n')
            current_section = None
            current_content = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Определяем секции по заголовкам
                if line.startswith('#'):
                    # Сохраняем предыдущую секцию
                    if current_section and current_content:
                        self._add_section_to_lesson_plan(lesson_plan, current_section, '\n'.join(current_content))

                    # Начинаем новую секцию
                    current_section = line.lower()
                    current_content = []
                else:
                    current_content.append(line)

            # Добавляем последнюю секцию
            if current_section and current_content:
                self._add_section_to_lesson_plan(lesson_plan, current_section, '\n'.join(current_content))

            return lesson_plan

        except Exception as e:
            logger.error(f"Error structuring lesson plan: {str(e)}")
            # Возвращаем базовую структуру с исходным контентом
            return {
                "title": "Generated Lesson Plan",
                "content": content,
                "objective": "",
                "duration": 60,
                "materials": [],
                "stages": [],
                "homework": "",
                "assessment": "",
                "notes": ""
            }

    def _add_section_to_lesson_plan(self, lesson_plan: Dict[str, Any], section: str, content: str):
        """Add section content to lesson plan structure"""
        if 'title' in section or 'название' in section:
            lesson_plan['title'] = content
        elif 'objective' in section or 'цель' in section:
            lesson_plan['objective'] = content
        elif 'material' in section or 'материал' in section:
            lesson_plan['materials'] = [item.strip() for item in content.split('\n') if item.strip()]
        elif 'homework' in section or 'домашн' in section:
            lesson_plan['homework'] = content
        elif 'assessment' in section or 'оценк' in section:
            lesson_plan['assessment'] = content
        elif 'note' in section or 'заметк' in section:
            lesson_plan['notes'] = content
        elif 'stage' in section or 'этап' in section or 'activity' in section:
            if 'stages' not in lesson_plan:
                lesson_plan['stages'] = []
            lesson_plan['stages'].append({
                'name': section,
                'content': content
            })

    async def _link_lesson_to_course(self, course_id: int, lesson_plan: Dict[str, Any]) -> None:
        """Link lesson to course"""
        try:
            lesson = Lesson(
                course_id=course_id,
                title=lesson_plan.get('title', 'Generated Lesson'),
                content=lesson_plan.get('content', ''),
                objective=lesson_plan.get('objective', ''),
                duration=lesson_plan.get('duration', 60)
            )
            self.session.add(lesson)
            await self.session.flush()
            logger.info(f"Lesson linked to course {course_id}")
        except Exception as e:
            logger.error(f"Error linking lesson to course: {str(e)}")

    @memory_optimized()
    async def generate_exercises(
            self,
            user_id: int,
            lesson_id: Optional[int] = None,
            exercise_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate exercises for lesson"""
        try:
            # Prepare context for generation
            context = exercise_data or {}
            
            if lesson_id:
                # Get lesson information
                query = select(Lesson).where(Lesson.id == lesson_id)
                result = await self.session.execute(query)
                lesson = result.scalar_one_or_none()
                
                if lesson:
                    context.update({
                        "lesson_title": lesson.title,
                        "lesson_content": lesson.content,
                        "lesson_objective": lesson.objective
                    })

            # Create prompt for exercises
            prompt = self._create_exercises_prompt(context)

            # Generate content
            content = await self.generate_content(
                content_type=ContentType.EXERCISE,
                prompt=prompt,
                user_id=user_id,
                extra_params=context
            )

            # Structure exercises
            exercises = self._structure_exercises(content)

            # Save exercises if needed
            if exercises:
                await self._save_exercises([{
                    "user_id": user_id,
                    "type": ContentType.EXERCISE,
                    "content": content,
                    "prompt": prompt
                }])

            return exercises

        except Exception as e:
            logger.error(f"Error generating exercises: {str(e)}")
            raise

    def _create_exercises_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for exercise generation with detailed CEFR level instructions"""

        # Получаем метаданные или инициализируем пустой словарь
        meta = context.get('meta', {})

        # Получаем уровень владения языком и создаем детальные инструкции
        proficiency = meta.get('proficiency', context.get('level', 'intermediate'))
        level_instruction = self._get_cefr_level_instruction(proficiency)

        # Формируем инструкции для индивидуальных/групповых занятий
        format_instruction = ""
        if context.get('individual_group') == 'individual':
            format_instruction = """
!!! IMPORTANT !!!
This is an INDIVIDUAL lesson (one-on-one teaching). The exercises should:
- Be designed for one-on-one interaction between teacher and student
- NOT include any pair or group activities
- Focus on personalized feedback and individual practice
- Avoid phrases like "work with a partner" or "discuss in groups"
            """
        elif context.get('individual_group') == 'group':
            format_instruction = """
The exercises should be designed for GROUP teaching:
- Include activities where students can work together
- Incorporate peer interaction and collaborative tasks
- Utilize group dynamics for language practice
            """

        # Дополнительные опции
        additional_options = ""
        if meta.get('includeAnswers', True):
            additional_options += "- Include COMPLETE ANSWER KEYS for all exercises with explanations\n"
        if meta.get('includeInstructions', True):
            additional_options += "- Include DETAILED TEACHER INSTRUCTIONS with step-by-step implementation guide\n"

        # Выбранные типы упражнений из метаданных
        selected_types = meta.get('selectedTypes', [])
        types_instruction = self._get_exercise_types_instruction(selected_types)

        # Выбранные форматы упражнений
        selected_formats = meta.get('selectedFormats', [])
        formats_instruction = self._get_exercise_formats_instruction(selected_formats)

        # Игровые элементы
        gamification = meta.get('gamification', [])
        gamification_instruction = self._get_gamification_instruction(gamification)

        # Тематические элементы
        theme = meta.get('theme', '')
        theme_instruction = ""
        if theme:
            theme_instruction = f"""
THEME INTEGRATION:
- Incorporate the theme "{theme}" throughout all exercises
- Use vocabulary, examples, and contexts related to this theme
- Make the theme central to the learning experience
            """

        # Основной шаблон промпта
        prompt_template = """
Create EXACTLY {quantity} COMPLETE and DETAILED exercises for {language} language learners.

⚠️ IMPORTANT: Generate EXACTLY {quantity} exercises - no more, no less!

TOPIC: {topic}
PROFICIENCY LEVEL: {proficiency}
EXERCISE TYPE: {exercise_type}

{level_instruction}

{types_instruction}
{formats_instruction}
{theme_instruction}
{gamification_instruction}
{format_instruction}

CRITICAL REQUIREMENTS FOR EACH EXERCISE:
1. **Exercise Title** - Clear, descriptive title (e.g., "Exercise 1: Present Simple Practice")
2. **Learning Objectives** - What students will achieve
3. **Step-by-Step Instructions** - Detailed student instructions
4. **Complete Exercise Content** - Full tasks, not just descriptions
5. **Worked Examples** - Show students exactly what to do
6. **Answer Keys** - Complete solutions with explanations
7. **Teacher Notes** - Implementation tips and common mistakes to watch for

{additional_options}

FORMATTING REQUIREMENTS:
- Number each exercise clearly: "Exercise 1:", "Exercise 2:", etc.
- Separate each exercise with clear dividers
- Include all required sections for each exercise
- Make each exercise self-contained and complete

QUANTITY CONTROL:
- You must create EXACTLY {quantity} exercises
- Count your exercises before finishing
- If you have fewer than {quantity}, add more
- If you have more than {quantity}, remove the extras

QUALITY STANDARDS:
- Each exercise must be COMPLETE and READY TO USE
- Include specific examples, not general descriptions
- Provide enough content for meaningful practice
- Ensure exercises build on each other logically
- Make instructions crystal clear for students
        """

        return prompt_template.format(
            quantity=context.get('quantity', 3),
            language=context.get('language', 'English'),
            topic=context.get('topic', 'General'),
            proficiency=proficiency,
            exercise_type=context.get('exercise_type', 'grammar'),
            level_instruction=level_instruction,
            types_instruction=types_instruction,
            formats_instruction=formats_instruction,
            theme_instruction=theme_instruction,
            gamification_instruction=gamification_instruction,
            format_instruction=format_instruction,
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
                sections = re.split(r"(?i)## Exercise \d+:", content)
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

            # Обрабатываем каждую секцию
            for i, section in enumerate(sections, 1):
                if not section.strip():
                    continue

                logger.info(f"Обработка упражнения {i}, длина секции: {len(section)} символов")

                exercise = {
                    "type": "general",
                    "content": "",
                    "answers": "",
                    "instructions": ""
                }

                # Ищем секцию ответов (может быть в разных форматах)
                answer_patterns = [
                    r"(?i)###\s*answer\s*keys?.*?$",
                    r"(?i)answer\s*keys?:?.*?$",
                    r"(?i)answers:?.*?$",
                    r"(?i)ответы:?.*?$",
                    r"(?i)solutions?:?.*?$"
                ]

                # Ищем секцию инструкций
                instruction_patterns = [
                    r"(?i)###\s*teacher\s*instructions.*?$",
                    r"(?i)teacher\s*instructions:?.*?$",
                    r"(?i)teaching\s*notes:?.*?$",
                    r"(?i)инструкции\s*для\s*учителя:?.*?$",
                    r"(?i)notes\s*for\s*teacher:?.*?$"
                ]

                content_parts = {}
                current_section = section

                # Извлекаем ответы
                answers_match = None
                for pattern in answer_patterns:
                    matches = re.search(pattern, current_section, re.MULTILINE)
                    if matches:
                        answers_match = matches
                        break

                if answers_match:
                    split_pos = answers_match.start()
                    content_parts['content'] = current_section[:split_pos].strip()
                    content_parts['answers'] = current_section[split_pos:].strip()
                    current_section = content_parts['content']  # Обновляем текущую секцию для дальнейшего поиска
                else:
                    content_parts['content'] = current_section
                    content_parts['answers'] = ""

                # Извлекаем инструкции
                instructions_match = None
                for pattern in instruction_patterns:
                    matches = re.search(pattern, current_section, re.MULTILINE)
                    if matches:
                        instructions_match = matches
                        break

                if instructions_match:
                    split_pos = instructions_match.start()
                    # Обновляем содержимое, отделяя инструкции
                    content_parts['instructions'] = current_section[split_pos:].strip()
                    content_parts['content'] = current_section[:split_pos].strip()
                else:
                    content_parts['instructions'] = ""

                # Если в ответах есть инструкции, обрабатываем их
                for pattern in instruction_patterns:
                    if content_parts['answers']:
                        matches = re.search(pattern, content_parts['answers'], re.MULTILINE)
                        if matches:
                            split_pos = matches.start()
                            content_parts['instructions'] = content_parts['answers'][split_pos:].strip()
                            content_parts['answers'] = content_parts['answers'][:split_pos].strip()
                            break

                # Заполняем данные упражнения
                exercise['content'] = content_parts['content'].strip()
                exercise['answers'] = content_parts['answers'].strip()
                exercise['instructions'] = content_parts['instructions'].strip()

                # Определяем тип упражнения (если возможно)
                exercise_type_patterns = {
                    "grammar": r"(?i)(grammar|грамматик|tense|время|артикл|предлог|союз|синтакс)",
                    "vocabulary": r"(?i)(vocabulary|словар|лексик|слов|term|термин)",
                    "reading": r"(?i)(reading|чтени|текст|passage|отрыв)",
                    "writing": r"(?i)(writing|письм|composition|сочинени|эссе|essay)",
                    "speaking": r"(?i)(speaking|говорени|диалог|монолог|conversation|разговор)",
                    "listening": r"(?i)(listening|аудировани|слушани)"
                }

                for type_key, pattern in exercise_type_patterns.items():
                    if re.search(pattern, exercise['content']):
                        exercise['type'] = type_key
                        break

                # Логируем результат
                logger.info(f"Упражнение {i} обработано: {len(exercise['content'])} символов контента, " +
                           f"{len(exercise['answers'])} символов ответов, {len(exercise['instructions'])} символов инструкций")

                exercises.append(exercise)

            logger.info(f"Успешно обработано {len(exercises)} упражнений")
            return exercises

        except Exception as e:
            logger.error(f"Ошибка при обработке структуры упражнений: {str(e)}")
            # В случае ошибки возвращаем весь контент как одно упражнение
            return [{
                "type": "general",
                "content": content,
                "answers": "",
                "instructions": ""
            }]

    async def _save_exercises(self, batch: List[Dict[str, Any]]) -> None:
        """Save exercises to database"""
        try:
            await self._save_generation(batch)
        except Exception as e:
            logger.error(f"Error saving exercises: {str(e)}")
            raise

    def _validate_exercise_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters for exercise generation"""
        required_params = ['language', 'topic', 'difficulty', 'quantity']
        for param in required_params:
            if param not in params:
                raise ValidationError(f"Missing required parameter: {param}")

        if not 1 <= params.get('quantity', 0) <= 10:
            raise ValidationError("Quantity must be between 1 and 10")

    def _get_cefr_level_instruction(self, proficiency: str) -> str:
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
LEVEL: A1 (BEGINNER) - DETAILED REQUIREMENTS:

VOCABULARY:
- Use only the most basic, high-frequency words (family, numbers, colors, days, food)
- Limit vocabulary to 500-1000 most common words
- Provide clear definitions or visual aids for any new words
- Use cognates and international words when possible

GRAMMAR:
- Present simple tense only (I am, I have, I like)
- Basic question forms (What is...? Where is...?)
- Simple negatives (I don't like, It's not...)
- Basic prepositions (in, on, at)
- Singular/plural nouns (book/books)

EXERCISE COMPLEXITY:
- Single-step tasks only
- Clear, simple instructions (max 10 words)
- Lots of examples and visual support
- Repetitive practice with slight variations
- Yes/No and multiple choice questions
- Matching exercises with pictures/words

LANGUAGE OF INSTRUCTIONS:
- Use very simple English
- Short sentences (max 8 words)
- Present tense only
- Avoid complex grammar in instructions
            """,

            'a2': """
LEVEL: A2 (ELEMENTARY) - DETAILED REQUIREMENTS:

VOCABULARY:
- Expand to 1000-2000 common words
- Include basic adjectives, adverbs, and connectors
- Introduce topic-specific vocabulary gradually
- Use simple definitions in English

GRAMMAR:
- Past simple regular and irregular verbs
- Future with 'going to' and 'will'
- Present continuous for current actions
- Comparative and superlative adjectives
- Basic modal verbs (can, must, should)
- Simple conditionals (If I have time...)

EXERCISE COMPLEXITY:
- Two-step tasks maximum
- Clear sequencing (First... Then... Finally...)
- Gap-fill exercises with word banks
- Simple sentence transformation
- Basic reading comprehension with factual questions
- Short dialogues and role-plays

LANGUAGE OF INSTRUCTIONS:
- Simple but complete sentences
- Use familiar vocabulary in instructions
- Provide examples for each task type
            """,

            'b1': """
LEVEL: B1 (INTERMEDIATE) - DETAILED REQUIREMENTS:

VOCABULARY:
- 2000-3000 words including abstract concepts
- Topic-specific vocabulary for common themes
- Phrasal verbs and basic idioms
- Formal and informal register awareness

GRAMMAR:
- All major tenses including perfect aspects
- Passive voice in common situations
- Reported speech for statements and questions
- Complex conditionals (2nd and 3rd conditional)
- Relative clauses (who, which, that, where)
- Advanced modal verbs and their meanings

EXERCISE COMPLEXITY:
- Multi-step tasks requiring planning
- Text analysis and inference questions
- Opinion-based discussions with justification
- Problem-solving activities
- Creative writing with guided structure
- Listening for specific information and gist

LANGUAGE OF INSTRUCTIONS:
- Natural, fluent English
- Complex sentence structures acceptable
- Assume understanding of common academic vocabulary
            """,

            'b2': """
LEVEL: B2 (UPPER-INTERMEDIATE) - DETAILED REQUIREMENTS:

VOCABULARY:
- 3000-4000 words including specialized terminology
- Advanced phrasal verbs and idiomatic expressions
- Nuanced vocabulary for expressing opinions and emotions
- Academic and professional vocabulary

GRAMMAR:
- Advanced tenses and aspects in context
- Complex passive constructions
- Advanced conditionals and hypothetical situations
- Sophisticated linking devices and discourse markers
- Advanced modal verbs for speculation and deduction
- Inversion and emphasis structures

EXERCISE COMPLEXITY:
- Extended tasks requiring sustained effort
- Critical thinking and analysis activities
- Debate and argumentation exercises
- Research-based projects
- Creative and analytical writing
- Complex listening with multiple speakers and accents

LANGUAGE OF INSTRUCTIONS:
- Sophisticated language acceptable
- Academic style instructions
- Minimal scaffolding required
            """,

            'c1': """
LEVEL: C1 (ADVANCED) - DETAILED REQUIREMENTS:

VOCABULARY:
- 4000+ words including low-frequency and specialized terms
- Sophisticated idiomatic expressions and metaphors
- Academic and professional register mastery
- Cultural references and allusions

GRAMMAR:
- Mastery of all grammatical structures
- Subtle distinctions in meaning and usage
- Advanced stylistic devices
- Complex sentence structures with multiple clauses
- Sophisticated discourse organization

EXERCISE COMPLEXITY:
- Extended, autonomous tasks
- Abstract and theoretical concepts
- Independent research and presentation
- Critical evaluation and synthesis
- Creative and academic writing at advanced level
- Complex authentic materials (lectures, academic texts)

LANGUAGE OF INSTRUCTIONS:
- Native-like complexity acceptable
- Minimal explicit instruction needed
- Focus on refinement and sophistication
            """,

            'c2': """
LEVEL: C2 (PROFICIENCY) - DETAILED REQUIREMENTS:

VOCABULARY:
- Near-native vocabulary range (5000+ words)
- Subtle nuances and connotations
- Specialized terminology across multiple fields
- Literary and archaic expressions
- Regional and stylistic variations

GRAMMAR:
- Native-like control of all structures
- Subtle grammatical distinctions
- Stylistic and rhetorical effects
- Complex discourse patterns
- Implicit and explicit meaning

EXERCISE COMPLEXITY:
- Highly complex, authentic tasks
- Abstract reasoning and analysis
- Independent critical thinking
- Sophisticated communication skills
- Professional and academic contexts
- Cultural and literary analysis

LANGUAGE OF INSTRUCTIONS:
- Native-speaker level complexity
- Sophisticated academic language
- Implicit understanding assumed
            """
        }

        return level_instructions.get(cefr_level, level_instructions['b1'])

    def _get_exercise_types_instruction(self, selected_types: List[str]) -> str:
        """Get detailed instructions for selected exercise types"""
        if not selected_types:
            return ""

        type_instructions = {
            'story': """
STORY-BASED EXERCISES:
- Create engaging narratives relevant to the topic
- Include character development and plot progression
- Use stories to introduce and practice new vocabulary/grammar
- Add comprehension questions about plot, characters, and themes
- Include creative writing extensions (alternative endings, character perspectives)
            """,

            'roleplay': """
ROLE-PLAYING EXERCISES:
- Design realistic scenarios for language practice
- Provide clear character descriptions and motivations
- Include specific language functions (asking for help, making complaints, etc.)
- Add preparation time and follow-up discussion questions
- Ensure roles are appropriate for the proficiency level
            """,

            'quiz': """
INTERACTIVE QUIZ EXERCISES:
- Create varied question types (multiple choice, true/false, short answer)
- Include immediate feedback and explanations
- Progress from easier to more challenging questions
- Add bonus questions for advanced learners
- Include visual elements where appropriate
            """,

            'game': """
LANGUAGE GAME EXERCISES:
- Design competitive or collaborative game elements
- Include clear rules and scoring systems
- Add time limits for excitement and challenge
- Ensure games reinforce learning objectives
- Provide variations for different group sizes
            """,

            'project': """
CREATIVE PROJECT EXERCISES:
- Design multi-step creative tasks
- Include research and presentation components
- Allow for personal expression and creativity
- Provide clear assessment criteria
- Include peer feedback opportunities
            """,

            'media': """
MEDIA CREATION EXERCISES:
- Include video, audio, or digital content creation
- Provide technical guidance and templates
- Focus on communication skills through media
- Include planning and scripting phases
- Add sharing and feedback components
            """
        }

        instructions = []
        for exercise_type in selected_types:
            if exercise_type in type_instructions:
                instructions.append(type_instructions[exercise_type])

        if instructions:
            return "SELECTED EXERCISE TYPES:\n" + "\n".join(instructions)
        return ""

    def _get_exercise_formats_instruction(self, selected_formats: List[str]) -> str:
        """Get detailed instructions for selected exercise formats"""
        if not selected_formats:
            return ""

        format_instructions = {
            'gap_fill': """
GAP-FILL FORMAT:
- Use short underscores (____) or numbered blanks (1), (2), (3)
- Maximum 5-10 underscores per gap
- Provide word banks when appropriate
- Include both grammar and vocabulary gaps
- Add context clues to help students
- Provide complete answer keys with explanations
            """,

            'sentence_building': """
SENTENCE BUILDING FORMAT:
- Provide scrambled words or phrases
- Include punctuation guidance
- Start with shorter sentences, progress to longer ones
- Add visual cues or prompts when helpful
- Include multiple correct possibilities when appropriate
- Show word order rules explicitly
            """,

            'open_brackets': """
OPEN BRACKETS FORMAT:
- Provide words in brackets to be transformed
- Include clear instructions for each transformation
- Cover verb tenses, word forms, and grammatical changes
- Provide examples of the transformation type
- Include answer keys with explanations of rules
- Progress from simple to complex transformations
            """,

            'sentence_matching': """
SENTENCE MATCHING FORMAT:
- Create logical connections between sentence parts
- Include distractors to increase difficulty
- Use clear formatting (numbers and letters)
- Ensure only one correct match per item
- Add context or theme to make matching meaningful
- Include answer keys with explanations
            """,

            'word_definition': """
WORD-DEFINITION MATCHING FORMAT:
- Use vocabulary appropriate for the level
- Include both simple and complex definitions
- Add example sentences for context
- Include synonyms and antonyms when relevant
- Use clear, unambiguous definitions
- Provide pronunciation guides when needed
            """
        }

        instructions = []
        for format_type in selected_formats:
            if format_type in format_instructions:
                instructions.append(format_instructions[format_type])

        if instructions:
            return "SELECTED EXERCISE FORMATS:\n" + "\n".join(instructions)
        return ""

    def _get_gamification_instruction(self, gamification_elements: List[str]) -> str:
        """Get gamification instructions"""
        if not gamification_elements:
            return ""

        gamification_instructions = {
            'points': """
POINTS SYSTEM:
- Award points for correct answers and completion
- Create different point values for different difficulty levels
- Include bonus points for creativity or extra effort
- Display running totals and achievements
            """,

            'levels': """
LEVEL PROGRESSION:
- Design exercises that unlock progressively
- Create clear level indicators and requirements
- Include "boss battles" or major challenges
- Provide level-appropriate rewards and recognition
            """,

            'badges': """
ACHIEVEMENT BADGES:
- Create specific badges for different accomplishments
- Include both skill-based and effort-based badges
- Design visually appealing badge descriptions
- Allow students to display and share their badges
            """,

            'leaderboards': """
COMPETITIVE LEADERBOARDS:
- Track individual and team performance
- Include multiple categories (speed, accuracy, creativity)
- Update rankings regularly and fairly
- Encourage healthy competition and collaboration
            """,

            'storytelling': """
NARRATIVE ELEMENTS:
- Embed exercises within engaging storylines
- Create character progression and plot development
- Use story outcomes based on student performance
- Include branching narratives for different choices
            """
        }

        instructions = []
        for element in gamification_elements:
            if element in gamification_instructions:
                instructions.append(gamification_instructions[element])

        if instructions:
            return "GAMIFICATION ELEMENTS:\n" + "\n".join(instructions)
        return ""
