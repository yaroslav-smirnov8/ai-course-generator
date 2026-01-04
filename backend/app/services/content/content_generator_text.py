# app/services/content/content_generator_text.py
"""
Модуль для анализа текста и генерации текстового контента
"""
import logging
from typing import Optional, Dict, Any, List
from youtube_transcript_api import YouTubeTranscriptApi
from sqlalchemy import select
import re

from ...models import VideoTranscript
from ...core.memory import memory_optimized
from ...core.constants import ContentType
from ...core.exceptions import ValidationError
from ...schemas.content import TextLevelAnalysis, TitlesAnalysis, QuestionsAnalysis

logger = logging.getLogger(__name__)


class ContentGeneratorText:
    """
    Миксин для анализа текста и генерации текстового контента
    """
    
    @memory_optimized()
    async def generate_comprehension_test(
        self,
        text: str,
        language: str,
        question_count: int = 5,
        difficulty: str = "medium",
        **kwargs
    ) -> str:
        """
        Генерирует вопросы к тексту

        Args:
            text (str): Текст, на основе которого генерируются вопросы
            language (str): Язык текста
            question_count (int): Количество вопросов
            difficulty (str): Уровень сложности (easy, medium, hard)
            **kwargs: Дополнительные параметры

        Returns:
            str: Сгенерированные вопросы к тексту в формате Markdown
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Generating comprehension questions with {question_count} questions for text in {language}, difficulty: {difficulty}")

            # Проверяем параметры
            if not 1 <= question_count <= 15:
                raise ValidationError("Question count must be between 1 and 15")

            if difficulty not in ["easy", "medium", "hard"]:
                logger.warning(f"Unknown difficulty level: {difficulty}, using 'medium' as default")
                difficulty = "medium"

            # Создаем промпт для теста на понимание
            prompt = self._create_comprehension_test_prompt(text, language, question_count, difficulty)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={"difficulty": difficulty, "question_count": question_count}
            )

            # Заменяем заголовок "Тест на понимание текста" на "Вопросы по тексту"
            is_russian = language.lower() in ["russian", "русский", "ru"]

            if is_russian:
                content = content.replace("# Reading Comprehension Test", "# Text Questions")
                content = content.replace("## Reading Comprehension Test", "# Text Questions")
            else:
                content = content.replace("# Reading Comprehension Test", "# Text Questions")
                content = content.replace("## Reading Comprehension Test", "# Text Questions")

            # Обрабатываем экранированные символы
            content = content.replace("\\n", "\n").replace("\\\\", "\\")

            # Возвращаем сгенерированный тест
            return content

        except Exception as e:
            logger.error(f"Error generating comprehension test: {str(e)}")
            raise

    def _create_comprehension_test_prompt(self, text: str, language: str, question_count: int, difficulty: str) -> str:
        """Создает промпт для теста на понимание текста"""

        difficulty_descriptions = {
            "easy": "basic comprehension questions suitable for beginners",
            "medium": "moderate difficulty questions requiring good understanding",
            "hard": "challenging questions requiring deep analysis and inference"
        }

        diff_description = difficulty_descriptions.get(difficulty, "moderate difficulty questions")

        # Определяем языковые параметры на основе указанного языка
        language_codes = {
            "english": {"code": "en", "native": "English"},
            "spanish": {"code": "es", "native": "Español"},
            "french": {"code": "fr", "native": "Français"},
            "german": {"code": "de", "native": "Deutsch"},
            "italian": {"code": "it", "native": "Italiano"},
            "chinese": {"code": "zh", "native": "中文"},
            "japanese": {"code": "ja", "native": "日本語"},
            "korean": {"code": "ko", "native": "한국어"},
            "turkish": {"code": "tr", "native": "Türkçe"},
            "russian": {"code": "ru", "native": "Русский"},
            "arabic": {"code": "ar", "native": "العربية"}
        }

        language_info = language_codes.get(language.lower(), {"code": "en", "native": "English"})
        language_code = language_info["code"]
        language_native = language_info["native"]

        # Определяем, является ли язык русским для особого форматирования
        is_russian = language.lower() in ["russian", "русский", "ru"]
        title = "Text Questions" if is_russian else "Text Questions"

        # Создаем промпт по структуре CARE (Context, Ask, Rules, Examples)
        prompt = f"""
# RESPOND ONLY IN {language_native.upper()} ({language_code})

# CONTEXT:
I am working with a text in {language_native} that contains approximately {len(text.split())} words.
The text begins with: {text[:100]}...
The difficulty level requested is: {difficulty} ({diff_description})

# ASK:
Create {question_count} multiple-choice questions based on the provided text. The questions should help assess comprehension of the text.

# IMPORTANT LANGUAGE INSTRUCTION:
- The content MUST be created in {language_native} language ({language_code})
- All questions, options, and answers MUST be written in {language_native}
- The title should be "{title}"
- All content must be formatted in Markdown
- DO NOT translate any part of the text or questions into any other language
- Use ONLY {language_native} for ALL content including titles, questions, options, and explanations

# RULES:
- Start with a main heading: "# {title}"
- Each question must be clearly numbered and formatted with a colored number using this exact format:
  "Question 1:" for all languages
- Use exactly 4 options (A, B, C, D) for each question
- For each question's options, format them like this:
  A. First option
  B. Second option
  C. Third option
  D. Fourth option
- Mark the correct answer with a ✓ symbol at the beginning of the line
- After the options, include a section titled "Correct Answer:" for all languages that shows the correct option
- Add a separator "---" between questions
- All questions and answers must be based solely on the text content
- Questions should be challenging but fair at the {difficulty} level
- Ensure all formatting is consistent throughout

# EXAMPLE FORMAT:
# Text Questions

Question 1: [Text of the question]

Options:

A. Option one
B. Option two
C. ✓ Correct option
D. Option four

Correct Answer: C. ✓ Correct option

---

Question 2: [Text of the second question]
...

# THE TEXT:
{text}

Now create well-structured multiple-choice questions based on this text in {language_native} language following the exact format specified.
"""

        return prompt

    @memory_optimized()
    async def generate_titles(
        self,
        text: str,
        count: int = 5,
        style: str = "engaging",
        **kwargs
    ) -> TitlesAnalysis:
        """
        Генерирует заголовки для текста

        Args:
            text (str): Исходный текст
            count (int): Количество заголовков для генерации
            style (str): Стиль заголовков (engaging, formal, creative, etc.)
            **kwargs: Дополнительные параметры

        Returns:
            TitlesAnalysis: Объект с сгенерированными заголовками
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Generating {count} titles in {style} style for text")

            # Создаем промпт для генерации заголовков
            language = kwargs.get('language', 'english')
            prompt = self._create_titles_prompt(text, language, count)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={"count": count, "style": style}
            )

            # Парсим результат с использованием улучшенного парсера
            parsed_result = self._parse_titles_from_content(content)
            titles = parsed_result.get("titles", [])
            recommended_index = parsed_result.get("recommended_index", 0)

            return TitlesAnalysis(
                original_text=text[:200] + "..." if len(text) > 200 else text,
                titles=titles,
                style=style,
                count=len(titles),
                recommended_index=recommended_index
            )

        except Exception as e:
            logger.error(f"Error generating titles: {str(e)}")
            raise

    def _create_titles_prompt(self, text: str, language: str, count: int) -> str:
        """Создает промпт для генерации заголовков"""

        # Определяем языковые параметры на основе указанного языка
        language_codes = {
            "english": {"code": "en", "native": "English"},
            "spanish": {"code": "es", "native": "Español"},
            "french": {"code": "fr", "native": "Français"},
            "german": {"code": "de", "native": "Deutsch"},
            "italian": {"code": "it", "native": "Italiano"},
            "chinese": {"code": "zh", "native": "中文"},
            "japanese": {"code": "ja", "native": "日本語"},
            "korean": {"code": "ko", "native": "한국어"},
            "turkish": {"code": "tr", "native": "Türkçe"},
            "russian": {"code": "ru", "native": "Русский"},
            "arabic": {"code": "ar", "native": "العربية"}
        }

        language_info = language_codes.get(language.lower(), {"code": "en", "native": "English"})
        language_code = language_info["code"]
        language_native = language_info["native"]

        # Формируем промпт для генерации заголовков
        prompt = f"""
# RESPOND ONLY IN {language_native.upper()} ({language_code})

# CONTEXT:
I have a text in {language_native} that contains approximately {len(text.split())} words.
The text begins with: {text[:100]}...

# ASK:
Generate {count} distinct and creative titles for this text.

# IMPORTANT LANGUAGE INSTRUCTION:
- The titles MUST be created in {language_native} language ({language_code})
- DO NOT translate titles into any other language
- Use ONLY {language_native} for ALL titles

# RULES:
- Create exactly {count} titles
- One of the titles MUST be accurate and directly relevant to the text content
- Titles should be catchy, engaging, and appropriate for the text
- Titles should be concise (typically 3-10 words)
- Titles should vary in style (e.g., question, statement, metaphorical)
- Each title should be unique and different from the others
- Number each title in the format: "1. [Title text]"
- Mark the most accurate and relevant title with a ✓ symbol at the end
- Do not include quotes or extra formatting around the titles

# EXAMPLE OUTPUT:
1. The Surprising Benefits of Daily Exercise ✓
2. From Couch to Marathon: A Journey of Transformation
3. Your Body's Hidden Potential: Unlock It Through Movement
4. Exercise: The Free Medicine That Changes Lives

# FINAL REMINDER:
You MUST create ALL titles in {language_native} language ONLY.
Don't forget to mark the most accurate and relevant title with a ✓ symbol.

# THE TEXT:
{text}

Now generate {count} unique and engaging titles for this text.
"""

        return prompt

    def _parse_titles_response(self, content: str) -> List[str]:
        """Парсит ответ с заголовками"""
        try:
            titles = []
            lines = content.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Ищем пронумерованные заголовки
                if re.match(r'^\d+\.', line):
                    title = re.sub(r'^\d+\.\s*', '', line)
                    if title:
                        titles.append(title)
                elif line.startswith('-') or line.startswith('*'):
                    title = line[1:].strip()
                    if title:
                        titles.append(title)

            return titles[:10]  # Максимум 10 заголовков

        except Exception as e:
            logger.error(f"Error parsing titles response: {str(e)}")
            return ["Generated Title"]

    def _parse_titles_from_content(self, content: str) -> dict:
        """Извлекает заголовки из сгенерированного контента"""
        titles = []
        recommended_index = -1  # Индекс рекомендуемого заголовка

        # Ищем строки, начинающиеся с числа и точки, за которым следует текст
        pattern = r'^\s*(\d+)\.?\s*(.+?)(\s*✓)?\s*$'

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            match = re.match(pattern, line)
            if match:
                title_number = int(match.group(1)) - 1  # Индекс с нуля
                title_text = match.group(2).strip()
                is_recommended = bool(match.group(3))

                # Добавляем заголовок в список
                titles.append(title_text)

                # Если это рекомендуемый заголовок, запоминаем его индекс
                if is_recommended:
                    recommended_index = title_number

        # Если не удалось найти заголовки в нужном формате, пробуем другой подход
        if not titles:
            # Разделяем по пустым строкам и берем первые строки каждого раздела
            sections = [s.strip() for s in content.split('\n\n')]
            for section in sections:
                if section and not section.startswith('#'):
                    lines = section.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Ищем символ рекомендованного заголовка
                        is_recommended = '✓' in line
                        if is_recommended:
                            recommended_index = len(titles)  # Этот заголовок будет рекомендуемым

                        # Удаляем метку из заголовка
                        clean_line = line.replace('✓', '').strip()

                        if clean_line and len(clean_line) <= 100:  # Разумное ограничение для заголовка
                            titles.append(clean_line)
                            break

        # Если рекомендуемый заголовок не был явно указан, выбираем первый
        if recommended_index == -1 and titles:
            recommended_index = 0

        # Убедимся, что индекс рекомендуемого заголовка в допустимом диапазоне
        if recommended_index >= len(titles):
            recommended_index = 0 if titles else -1

        # Возвращаем заголовки и информацию о рекомендуемом
        return {
            "titles": titles,
            "recommended_index": recommended_index
        }

    async def process_video_transcript(self, video_id: str, subtitle_language: str = "ru") -> str:
        """Process video transcript for language learning"""
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
        from datetime import datetime

        logger.info(f"Обработка транскрипта для видео {video_id}")

        # Extract YouTube ID from URL if a full URL was provided
        video_id = self._extract_video_id(video_id)
        if not video_id:
            logger.error("Invalid YouTube video ID")
            raise ValueError("Invalid YouTube video ID format")

        # Check cache first without starting a new transaction
        stmt = select(VideoTranscript).where(
            VideoTranscript.video_id == video_id,
            VideoTranscript.language == subtitle_language
        )

        result = await self.session.execute(stmt)
        cached_transcript = result.scalar_one_or_none()

        if cached_transcript:
            logger.info(f"Found cached transcript for video {video_id} in {subtitle_language}")
            return cached_transcript.content

        # If not cached, fetch from YouTube
        try:
            logger.info(f"Fetching transcript for video {video_id} in {subtitle_language}")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[subtitle_language])
            
            # Combine transcript entries into a single text
            transcript_text = ' '.join([entry['text'] for entry in transcript_list])
            
            # Save to database
            video_transcript = VideoTranscript(
                video_id=video_id,
                language=subtitle_language,
                content=transcript_text,
                created_at=datetime.utcnow()
            )
            self.session.add(video_transcript)
            await self.session.flush()
            
            logger.info(f"Successfully fetched and cached transcript for video {video_id}")
            return transcript_text
            
        except Exception as e:
            logger.error(f"Error fetching YouTube transcript: {str(e)}")
            raise ValidationError(f"Could not fetch transcript for video {video_id}: {str(e)}")

    @memory_optimized()
    async def generate_questions(
        self,
        text: str,
        question_count: int = 5,
        question_type: str = "mixed",
        difficulty: str = "medium",
        **kwargs
    ) -> QuestionsAnalysis:
        """
        Генерирует вопросы по тексту

        Args:
            text (str): Исходный текст
            question_count (int): Количество вопросов
            question_type (str): Тип вопросов (multiple_choice, open_ended, mixed)
            difficulty (str): Уровень сложности
            **kwargs: Дополнительные параметры

        Returns:
            QuestionsAnalysis: Объект с сгенерированными вопросами
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Generating {question_count} {question_type} questions with {difficulty} difficulty")

            # Создаем промпт для генерации вопросов
            prompt = self._create_questions_prompt(text, question_count, question_type, difficulty)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={
                    "question_count": question_count,
                    "question_type": question_type,
                    "difficulty": difficulty
                }
            )

            return QuestionsAnalysis(
                original_text=text[:200] + "..." if len(text) > 200 else text,
                questions=content,
                question_type=question_type,
                difficulty=difficulty,
                count=question_count
            )

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise

    def _validate_question_params(self, params: Dict[str, Any]) -> None:
        """
        Проверяет параметры для генерации вопросов.

        Args:
            params: Параметры для генерации вопросов
        """
        if not params.get("language"):
            raise ValueError("Missing required parameter: language")

        if not params.get("text"):
            raise ValueError("Missing required parameter: text")

        if not params.get("num_questions"):
            raise ValueError("Missing required parameter: num_questions")

        if not 1 <= params.get('num_questions', 0) <= 20:
            raise ValueError("Number of questions must be between 1 and 20")

    def _structure_questions(self, content: str) -> List[Dict[str, Any]]:
        """
        Разбирает сгенерированный контент с вопросами и преобразует его в структурированный список.

        Args:
            content: Сгенерированный текст с вопросами

        Returns:
            List[Dict[str, Any]]: Список словарей с вопросами и ответами
        """
        import json
        questions = []

        try:
            # Пытаемся найти и распарсить JSON в тексте
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)

            # Пытаемся найти JSON-массив в тексте
            json_match = re.search(r'\[\s*{\s*"number".*?}\s*\]', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)

            # Если не нашли JSON в тексте, пробуем распарсить весь текст как JSON
            try:
                json_data = json.loads(content)
                if isinstance(json_data, list) and len(json_data) > 0:
                    return json_data
            except:
                pass

            # Если не удалось распарсить как JSON, используем регулярные выражения

            # Попробуем разные шаблоны для нахождения вопросов
            patterns = [
                # Формат "Question 1:" only
                r'(?:Question)\s+(\d+)[:\.]',
                # Формат "## Question 1" only
                r'#{2,3}\s*(?:Question)\s+(\d+)[:\.]?',
                # Формат "1. Question" only
                r'(\d+)[\.:\)]\s+[A-Z]',
                # Формат "Exercise 1:" only
                r'(?:Exercise)\s+(\d+)[:\.]'
            ]

            # Пробуем каждый шаблон по очереди
            question_blocks = []
            for pattern in patterns:
                question_blocks = re.split(pattern, content)
                # Если нашли хотя бы один вопрос, прерываем поиск
                if len(question_blocks) > 2:
                    break

            if len(question_blocks) <= 1:
                # Если не нашли вопросы по шаблонам, попробуем просто разбить по строкам
                # и искать строки, начинающиеся с цифр
                lines = content.split('\n')
                current_question = None
                current_options = []
                current_block = ""

                for line in lines:
                    if re.match(r'^\d+\.?\s+', line):
                        # Если нашли новый вопрос, сохраняем предыдущий
                        if current_question:
                            questions.append({
                                "number": len(questions) + 1,
                                "question": current_question,
                                "options": current_options,
                                "answer": None  # Ответ определим позже
                            })
                        # Начинаем новый вопрос
                        current_question = re.sub(r'^\d+\.?\s+', '', line).strip()
                        current_options = []
                        current_block = line + "\n"
                    elif re.match(r'^[A-D]\.?\s+', line) and current_question:
                        # Нашли вариант ответа
                        option_text = re.sub(r'^[A-D]\.?\s+', '', line).strip()
                        current_options.append(option_text)
                        current_block += line + "\n"
                    elif current_question:
                        # Продолжение текущего вопроса или блока
                        current_block += line + "\n"

                        # Проверяем, не ответ ли это
                        if re.search(r'(?:Answer)[:\s]+([^\n\r]+)', line):
                            answer_match = re.search(r'(?:Answer)[:\s]+([^\n\r]+)', line)
                            if answer_match:
                                questions[-1]["answer"] = answer_match.group(1).strip()

                # Добавляем последний вопрос, если он есть
                if current_question:
                    questions.append({
                        "number": len(questions) + 1,
                        "question": current_question,
                        "options": current_options,
                        "answer": None
                    })

                # Проверяем на наличие ответов
                for i, q in enumerate(questions):
                    if not q["answer"]:
                        # Пытаемся найти ответ в блоке текста
                        answer_pattern = re.search(r'(?:Answer)[:\s]+([^\n\r]+)', current_block)
                        if answer_pattern:
                            questions[i]["answer"] = answer_pattern.group(1).strip()

                return questions
            else:
                # Обрабатываем найденные блоки вопросов
                question_number = 1
                for i in range(1, len(question_blocks), 2):
                    if i + 1 >= len(question_blocks):
                        break

                    number = int(question_blocks[i])
                    block = question_blocks[i + 1].strip()

                    # Извлекаем текст вопроса
                    question_lines = block.split('\n')
                    question_text = ""

                    # Находим текст вопроса до вариантов ответов
                    for line in question_lines:
                        if re.match(r'^[A-D]\.', line.strip()) or "Options" in line:
                            break
                        question_text += line + " "

                    question_text = question_text.strip()
                    question_text = re.sub(r'^[:\s]+', '', question_text)

                    # Извлекаем варианты ответов
                    options = []
                    options_pattern = r'(?:[A-D])[\.\:\)\s]+([^\n]+)'
                    option_matches = re.findall(options_pattern, block)

                    if option_matches:
                        options = [opt.strip() for opt in option_matches]
                    else:
                        # Альтернативный поиск вариантов ответов
                        options_section = re.search(r'(?:Options)[:\s]+(.*?)(?:(?:Correct )?Answer|$)', block, re.DOTALL)
                        if options_section:
                            options_text = options_section.group(1).strip()
                            option_lines = re.findall(r'([A-D])[\.:\)\s]+([^\n\r]+)', options_text)
                            options = [opt[1].strip() for opt in option_lines]

                    # Извлекаем правильный ответ
                    answer = None
                    answer_match = re.search(r'(?:Answer)[:\s]+([^\n\r]+)', block, re.DOTALL)

                    if answer_match:
                        answer = answer_match.group(1).strip()

                    if question_text:
                        questions.append({
                            "number": number,
                            "question": question_text,
                            "options": options,
                            "answer": answer
                        })
                        question_number += 1

                # Если ничего не нашли, возвращаем пустой список
                return questions if questions else []

        except Exception as e:
            logger.error(f"Error structuring questions: {str(e)}")
            return []

    def _extract_video_id(self, video_id_or_url: str) -> str:
        """Extract YouTube video ID from URL or return as is if already an ID"""
        if not video_id_or_url:
            return None

        # If it's already a video ID (11 characters, alphanumeric + _ -)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id_or_url):
            return video_id_or_url

        # Extract from various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, video_id_or_url)
            if match:
                return match.group(1)

        return None

    def _create_questions_prompt(self, text: str, question_count: int, question_type: str, difficulty: str) -> str:
        """Создает промпт для генерации вопросов"""
        
        type_instructions = {
            "multiple_choice": "Create multiple choice questions with 4 options each (A, B, C, D). Mark the correct answer.",
            "open_ended": "Create open-ended questions that require detailed answers.",
            "mixed": "Create a mix of multiple choice and open-ended questions."
        }
        
        difficulty_instructions = {
            "easy": "Questions should test basic understanding and recall.",
            "medium": "Questions should require good comprehension and some analysis.",
            "hard": "Questions should require deep analysis, inference, and critical thinking."
        }
        
        type_instruction = type_instructions.get(question_type, type_instructions["mixed"])
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["medium"])
        
        prompt = f"""
Based on the following text, create {question_count} questions.

Instructions:
- {type_instruction}
- {difficulty_instruction}
- Questions should be based solely on the provided text
- Number each question clearly
- For multiple choice questions, provide the correct answer

Text:
{text}

Generate {question_count} questions now:
"""
        
        return prompt

    @memory_optimized()
    async def summarize_text(
        self,
        text: str,
        max_length: int = None,
        level: str = None,
        **kwargs
    ) -> str:
        """
        Генерирует саммари текста

        Args:
            text (str): Текст, для которого генерируется саммари
            max_length (int, optional): Максимальная длина саммари в словах
            level (str, optional): Уровень владения языком (a1, a2, b1, b2, c1, c2, etc.)
            **kwargs: Дополнительные параметры

        Returns:
            str: Сгенерированное саммари
        """
        try:
            user_id = kwargs.get('user_id', 1)
            language = kwargs.get('language', 'english')

            # Карта соответствия уровней и длины саммари
            level_to_length = {
                # CEFR для европейских языков
                'a1': 50,    # Начальный - очень короткое, простое саммари
                'a2': 75,    # Элементарный - короткое, простое саммари
                'b1': 150,   # Средний - среднее по длине, базовые конструкции
                'b2': 200,   # Средне-продвинутый - умеренно длинное
                'c1': 300,   # Продвинутый - длинное, детализированное
                'c2': 400,   # Свободное владение - очень детальное и длинное

                # HSK для китайского
                'hsk1': 50,
                'hsk2': 75,
                'hsk3': 125,
                'hsk4': 200,
                'hsk5': 300,
                'hsk6': 400,
                'hsk7-9': 450,

                # JLPT для японского
                'n5': 50,
                'n4': 100,
                'n3': 200,
                'n2': 300,
                'n1': 450,

                # TOPIK для корейского
                'topik1': 50,
                'topik2': 100,
                'topik3': 150,
                'topik4': 250,
                'topik5': 350,
                'topik6': 450,

                # Для русского (ТРКИ)
                'tea': 50,
                'tba': 100,
                't1': 200,
                't2': 300,
                't3': 400,
                't4': 450,

                # Для арабского (общие уровни)
                'beginner': 50,
                'elementary': 100,
                'intermediate': 200,
                'advanced': 300,
                'superior': 400,
                'native': 450
            }

            # Если указан уровень, определяем длину на его основе
            if level and level.lower() in level_to_length:
                actual_max_length = level_to_length[level.lower()]
                logger.info(f"Using level '{level}' to determine max_length: {actual_max_length}")
            elif max_length is not None:
                # Если указана точная длина, используем её
                actual_max_length = max_length
                # Проверяем параметры
                if not 50 <= actual_max_length <= 500:
                    logger.warning(f"Invalid max_length: {actual_max_length}, using default of 200")
                    actual_max_length = 200
            else:
                # По умолчанию используем средний уровень
                logger.warning("Neither level nor max_length specified, using default max_length of 200")
                actual_max_length = 200

            logger.info(f"Generating summary with max length {actual_max_length} for text of length {len(text)}")

            # Создаем промпт для генерации саммари
            prompt = self._create_summary_prompt(text, language, actual_max_length, level)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={"max_length": actual_max_length, "level": level}
            )

            return content

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    def _create_summary_prompt(self, text: str, language: str, max_length: int, level: str = None) -> str:
        """Создает промпт для генерации саммари"""

        # Определяем языковые параметры на основе указанного языка
        language_codes = {
            "english": {"code": "en", "native": "English"},
            "spanish": {"code": "es", "native": "Español"},
            "french": {"code": "fr", "native": "Français"},
            "german": {"code": "de", "native": "Deutsch"},
            "italian": {"code": "it", "native": "Italiano"},
            "chinese": {"code": "zh", "native": "中文"},
            "japanese": {"code": "ja", "native": "日本語"},
            "korean": {"code": "ko", "native": "한국어"},
            "turkish": {"code": "tr", "native": "Türkçe"},
            "russian": {"code": "ru", "native": "Русский"},
            "arabic": {"code": "ar", "native": "العربية"}
        }

        language_info = language_codes.get(language.lower(), {"code": "en", "native": "English"})
        language_code = language_info["code"]
        language_native = language_info["native"]

        # Добавляем инструкции в соответствии с уровнем
        level_instructions = ""
        if level:
            if level.lower().startswith('a'):
                level_instructions = f"""
# LANGUAGE LEVEL INSTRUCTIONS (Level {level.upper()}):
- Use very simple vocabulary appropriate for beginner level
- Use short, simple sentences with basic grammar structures
- Avoid complex sentences, idioms, and advanced expressions
- Focus on the most basic and essential information only
- Use common words and phrases that beginners would understand
- Use present tense predominantly, minimizing complex verb forms
"""
            elif level.lower().startswith('b'):
                level_instructions = f"""
# LANGUAGE LEVEL INSTRUCTIONS (Level {level.upper()}):
- Use vocabulary appropriate for intermediate level
- Use a mix of simple and some compound sentences
- Include some common expressions and idioms, but avoid very advanced ones
- Provide a more detailed overview with moderate complexity
- Use a variety of tenses, but limit very complex grammatical structures
"""
            elif level.lower().startswith('c') or level.lower() in ['native', 'superior', 't3', 't4', 'hsk6', 'hsk7-9', 'n1']:
                level_instructions = f"""
# LANGUAGE LEVEL INSTRUCTIONS (Level {level.upper()}):
- Use rich, varied vocabulary appropriate for advanced level
- Use complex sentence structures, including compound and complex sentences
- Include idiomatic expressions, specialized terminology, and nuanced language
- Provide detailed information with significant depth and complexity
- Use a full range of grammatical structures, including advanced ones
- Demonstrate sophisticated language comparable to educated native usage
"""
            else:
                # Промежуточные уровни или уровни для других языковых систем
                level_instructions = f"""
# LANGUAGE LEVEL INSTRUCTIONS (Level {level.upper()}):
- Adapt vocabulary and grammar to the specified level ({level})
- Balance simplicity and complexity appropriate for this level
- Use language structures commonly taught at this level
- Ensure the summary is challenging but comprehensible for learners at this level
"""

        # Формируем промпт для генерации саммари
        prompt = f"""
# RESPOND ONLY IN {language_native.upper()} ({language_code})

# CONTEXT:
I have a text in {language_native} that contains approximately {len(text.split())} words.
I need a summary with EXACTLY AND PRECISELY {max_length} words - NOT LESS, NOT MORE.
This is a STRICT REQUIREMENT - the summary MUST contain {max_length} words.

{level_instructions}

# ASK:
Create a detailed summary of the provided text using EXACTLY {max_length} words.
DO NOT create a summary shorter than {max_length} words under any circumstances.
IF your summary is shorter than {max_length} words, add more details from the original text to reach EXACTLY {max_length} words.

# IMPORTANT LANGUAGE INSTRUCTION:
- The summary MUST be created in {language_native} language ({language_code})
- DO NOT translate the summary into any other language
- Use ONLY {language_native} for ALL content
- The summary must be in plain text format

# RULES:
- Your summary MUST contain EXACTLY {max_length} words (±1 word maximum deviation)
- Count each word carefully during writing
- Capture the main ideas, key points, AND sufficient details from the original text
- Include enough details to REACH the {max_length} word count - this is MANDATORY
- DO NOT make the summary shorter than {max_length} words
- Maintain the original meaning and intent of the text
- Organize the summary in a logical flow
- Do not include your own opinions or interpretations
- Do not add information that is not present in the original text
- If the summary is approaching {max_length} words, adjust detail level to meet exact count

# WORD COUNTING METHODOLOGY:
1. Split the text by spaces to count words
2. Before submitting, count the total words in your summary
3. If the count is less than {max_length}, add more details until you reach EXACTLY {max_length} words
4. If the count is more than {max_length}, remove minor details until you reach EXACTLY {max_length} words

# FINAL REMINDER:
You MUST create the summary in {language_native} language ONLY.
The summary MUST contain EXACTLY {max_length} words - not fewer, not more.
Double-check your word count before submitting.

# THE TEXT:
{text}

Now generate a summary of this text with EXACTLY {max_length} words. Before submitting your answer, count the words to verify it is EXACTLY {max_length} words.
"""

        return prompt

    @memory_optimized()
    async def generate_summaries(
        self,
        text: str,
        language: str = "english",
        **kwargs
    ) -> str:
        """
        Генерирует три варианта саммари разной длины для текста

        Args:
            text (str): Текст, для которого генерируются саммари
            language (str): Язык текста
            **kwargs: Дополнительные параметры

        Returns:
            str: Сгенерированные саммари в формате Markdown
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Generating three summaries of different lengths for text in {language}")

            # Создаем промпт для генерации саммари разной длины
            prompt = self._create_multiple_summaries_prompt(text, language)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id
            )

            return content

        except Exception as e:
            logger.error(f"Error generating multiple summaries: {str(e)}")
            raise

    def _create_multiple_summaries_prompt(self, text: str, language: str) -> str:
        """Создает промпт для генерации нескольких саммари разной длины"""

        # Определяем языковые параметры на основе указанного языка
        language_codes = {
            "english": {"code": "en", "native": "English"},
            "spanish": {"code": "es", "native": "Español"},
            "french": {"code": "fr", "native": "Français"},
            "german": {"code": "de", "native": "Deutsch"},
            "italian": {"code": "it", "native": "Italiano"},
            "chinese": {"code": "zh", "native": "中文"},
            "japanese": {"code": "ja", "native": "日本語"},
            "korean": {"code": "ko", "native": "한국어"},
            "turkish": {"code": "tr", "native": "Türkçe"},
            "russian": {"code": "ru", "native": "Русский"},
            "arabic": {"code": "ar", "native": "العربية"}
        }

        language_info = language_codes.get(language.lower(), {"code": "en", "native": "English"})
        language_code = language_info["code"]
        language_native = language_info["native"]

        # Формируем промпт для генерации нескольких саммари
        prompt = f"""
# RESPOND ONLY IN {language_native.upper()} ({language_code})

# CONTEXT:
I am working with a text in {language_native} that contains approximately {len(text.split())} words and {len(text.split('.')) + len(text.split('!')) + len(text.split('?')) - 2} sentences.
The text begins with: {text[:100]}...

# ASK:
Create three different summaries of the text at different levels of detail:
1. Brief summary (1-2 sentences)
2. Medium summary (3-5 sentences)
3. Detailed summary (6-10 sentences)

# IMPORTANT LANGUAGE INSTRUCTION:
- The summaries MUST be created in {language_native} language ({language_code})
- DO NOT translate into any other language
- Use ONLY {language_native} for ALL content including titles and summaries
- Format the response in Markdown with clear headings for each summary type

# RULES:
- Each summary must accurately reflect the main content of the text
- The brief summary should capture only the most essential information
- The medium summary should include main ideas and key supporting details
- The detailed summary should cover all major aspects of the text, including important details
- Maintain the logical structure and flow of the original text
- Use your own wording rather than copying sentences directly from the original
- Do not add information that is not present in the original text
- Format the response in Markdown with clear headings for each summary type
- Ensure that each summary is coherent and stands on its own

# FINAL REMINDER:
You MUST create ALL summaries in {language_native} language ONLY.
Format the response with proper Markdown headings and sections.

# THE TEXT:
{text}

Now create three well-structured summaries at different levels of detail for this text.
"""

        return prompt

    @memory_optimized()
    async def change_text_level(
        self,
        text: str,
        target_level: str,
        source_level: str = None,
        **kwargs
    ) -> str:
        """
        Изменяет уровень сложности текста

        Args:
            text (str): Исходный текст
            target_level (str): Целевой уровень (a1, a2, b1, b2, c1, c2)
            source_level (str, optional): Исходный уровень текста
            **kwargs: Дополнительные параметры

        Returns:
            str: Текст, адаптированный под целевой уровень
        """
        try:
            user_id = kwargs.get('user_id', 1)
            language = kwargs.get('language', 'english')

            logger.info(f"Changing text level from {source_level or 'auto-detected'} to {target_level}")

            # Создаем промпт для изменения уровня
            prompt = self._create_text_level_prompt(text, language, target_level, source_level)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={"target_level": target_level, "source_level": source_level}
            )

            return content

        except Exception as e:
            logger.error(f"Error changing text level: {str(e)}")
            raise

    def _create_text_level_prompt(self, text: str, language: str, target_level: str, source_level: str = None) -> str:
        """Create prompt for text level adaptation"""

        level_descriptions = {
            'a1': 'Beginner level - very simple vocabulary, basic grammar, short sentences',
            'a2': 'Elementary level - simple vocabulary, basic grammar structures, clear sentences',
            'b1': 'Intermediate level - common vocabulary, standard grammar, moderate complexity',
            'b2': 'Upper-intermediate level - varied vocabulary, complex grammar, sophisticated sentences',
            'c1': 'Advanced level - rich vocabulary, complex structures, nuanced language',
            'c2': 'Proficiency level - sophisticated vocabulary, complex grammar, native-like fluency'
        }

        target_desc = level_descriptions.get(target_level.lower(), 'intermediate level')
        source_desc = level_descriptions.get(source_level.lower(), 'current level') if source_level else 'current level'

        prompt = f"""
Adapt the following text from {source_desc} to {target_desc} in {language}.

Target Level: {target_level.upper()}
Requirements for {target_level.upper()}:
- {target_desc}

Instructions:
- Maintain the core meaning and information of the original text
- Adjust vocabulary complexity to match {target_level.upper()} level
- Modify sentence structure appropriately
- Ensure grammar is suitable for {target_level.upper()} learners
- Keep the same general length and structure

Original text:
{text}

Adapted text for {target_level.upper()} level:
"""

        return prompt

    def _create_text_level_prompt(self, text: str, language: str, level_system: str) -> str:
        """Создает промпт для определения уровня текста"""

        # Определяем языковые параметры на основе указанного языка
        language_codes = {
            "english": {"code": "en", "native": "English"},
            "spanish": {"code": "es", "native": "Español"},
            "french": {"code": "fr", "native": "Français"},
            "german": {"code": "de", "native": "Deutsch"},
            "italian": {"code": "it", "native": "Italiano"},
            "chinese": {"code": "zh", "native": "中文"},
            "japanese": {"code": "ja", "native": "日本語"},
            "korean": {"code": "ko", "native": "한국어"},
            "turkish": {"code": "tr", "native": "Türkçe"},
            "russian": {"code": "ru", "native": "Русский"},
            "arabic": {"code": "ar", "native": "العربية"}
        }

        language_info = language_codes.get(language.lower(), {"code": "en", "native": "English"})
        language_code = language_info["code"]
        language_native = language_info["native"]

        # Определяем критерии оценки уровня для разных систем
        if "CEFR" in level_system:
            level_criteria = """
- A1 (Beginner): Can understand and use familiar everyday expressions and very basic phrases. Can introduce him/herself and others.
- A2 (Elementary): Can understand sentences and frequently used expressions related to areas of most immediate relevance.
- B1 (Intermediate): Can deal with most situations likely to arise while traveling in an area where the language is spoken.
- B2 (Upper Intermediate): Can interact with a degree of fluency and spontaneity that makes regular interaction with native speakers quite possible.
- C1 (Advanced): Can express ideas fluently and spontaneously without much obvious searching for expressions.
- C2 (Proficiency): Can understand with ease virtually everything heard or read. Can express him/herself spontaneously, very fluently and precisely.
"""
            valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        elif "HSK" in level_system:
            level_criteria = """
- HSK 1: Can understand and use very simple Chinese phrases.
- HSK 2: Can communicate in simple and routine tasks requiring a simple and direct exchange of information.
- HSK 3: Can handle most situations likely to arise whilst traveling in Chinese-speaking regions.
- HSK 4: Can interact with a degree of fluency and spontaneity with Chinese speakers.
- HSK 5: Can express ideas fluently without much difficulty with native Chinese speakers.
- HSK 6: Can express themselves fluently and precisely in complex situations in Chinese.
"""
            valid_levels = ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"]
        elif "JLPT" in level_system:
            level_criteria = """
- N5: Can understand basic Japanese.
- N4: Can understand basic Japanese used in daily situations to a certain degree.
- N3: Can understand Japanese used in everyday situations to a certain degree.
- N2: Can understand Japanese used in everyday situations and in a variety of circumstances.
- N1: Can understand Japanese used in a wide range of circumstances.
"""
            valid_levels = ["N5", "N4", "N3", "N2", "N1"]
        elif "TOPIK" in level_system:
            level_criteria = """
- TOPIK 1: Can understand and use familiar everyday expressions in Korean.
- TOPIK 2: Can communicate in simple and routine tasks in Korean.
- TOPIK 3: Can handle most situations in Korean.
- TOPIK 4: Can express ideas with fluency in Korean.
- TOPIK 5: Can express ideas with high fluency in Korean.
- TOPIK 6: Can express ideas with native-like fluency in Korean.
"""
            valid_levels = ["TOPIK1", "TOPIK2", "TOPIK3", "TOPIK4", "TOPIK5", "TOPIK6"]
        elif "ТРКИ" in level_system:
            level_criteria = """
- ТЭУ (A1): Базовое владение русским языком для минимального общения.
- ТБУ (A2): Базовый уровень владения для ограниченного повседневного общения.
- ТРКИ-1 (B1): Средний уровень для достаточного общения в бытовой и социально-культурной сферах.
- ТРКИ-2 (B2): Уровень, необходимый для обучения и работы по нелингвистическим специальностям.
- ТРКИ-3 (C1): Уровень, достаточный для профессиональной деятельности на русском языке.
- ТРКИ-4 (C2): Свободное владение русским языком близкое к уровню носителя языка.
"""
            valid_levels = ["ТЭУ", "ТБУ", "ТРКИ-1", "ТРКИ-2", "ТРКИ-3", "ТРКИ-4"]
        else:
            level_criteria = """
- Beginner: Can understand and use very basic phrases.
- Elementary: Can communicate in simple and routine tasks.
- Intermediate: Can handle most situations in everyday life.
- Upper Intermediate: Can interact with a degree of fluency.
- Advanced: Can express ideas fluently and spontaneously.
- Proficient: Can understand virtually everything heard or read.
"""
            valid_levels = ["Beginner", "Elementary", "Intermediate", "Upper Intermediate", "Advanced", "Proficient"]

        # Формируем промпт для определения уровня текста
        prompt = f"""
# TASK: ANALYZE TEXT LEVEL

# CONTEXT:
I need a detailed analysis of the level of a text in {language_native}.
The text contains approximately {len(text.split())} words.
Please use the {level_system} scale for your analysis.

# LEVEL CRITERIA:
{level_criteria}

# OUTPUT REQUIREMENTS:
1. You MUST return your analysis as a JSON object with the following fields:
   - "level": The exact level from {valid_levels}
   - "explanation": Detailed explanation in {language_native} why you determined this level
   - "vocabulary_analysis": Assessment of vocabulary level
   - "grammar_analysis": Assessment of grammar complexity
   - "sentence_structure": Assessment of sentence complexity
   - "recommendations": Suggestions for readers at different levels

2. The "level" field MUST be exactly one of these values: {valid_levels}
3. Do not include any text before or after the JSON object
4. Make sure the JSON is properly formatted and can be parsed

# IMPORTANT LANGUAGE INSTRUCTION:
- The explanation and all analysis fields MUST be written in {language_native} language ({language_code})
- Only the JSON field names should be in English
- DO NOT translate your analysis into any other language
- Use ONLY {language_native} for all content values

# THE TEXT TO ANALYZE:
{text}

Now analyze this text and determine its language level according to the {level_system} scale.
Return ONLY a well-formatted JSON object as specified.
"""

        return prompt

    @memory_optimized()
    async def regenerate_text(
        self,
        text: str,
        language: str,
        vocabulary_type: str = "neutral",
        preserve_style: bool = True,
        **kwargs
    ) -> str:
        """
        Перегенерация текста с изменением типа лексики

        Args:
            text (str): Исходный текст
            language (str): Язык текста
            vocabulary_type (str): Тип лексики (formal, informal, neutral, academic, slang)
            preserve_style (bool): Сохранять ли оригинальный стиль текста
            **kwargs: Дополнительные параметры

        Returns:
            str: Перегенерированный текст
        """
        try:
            user_id = kwargs.get('user_id', 1)

            logger.info(f"Regenerating text with vocabulary type '{vocabulary_type}' for {language} text (preserve_style={preserve_style})")

            # Инструкции для сохранения стиля
            preserve_style_instructions = ""
            if preserve_style:
                preserve_style_instructions = """
                IMPORTANT: Preserve the original style, tone, and structure of the text as much as possible.
                Keep the same paragraph structure, sentence patterns, and organization.
                Only change words and expressions to match the target vocabulary type.
                """
            else:
                preserve_style_instructions = """
                You may restructure the text as needed to match the target vocabulary type.
                Feel free to change sentence structures, organization, and word choice.
                """

            # Инструкции для типов лексики
            vocabulary_instructions = {
                "formal": """
                Use formal, professional vocabulary and expressions.
                Employ sophisticated language structures and avoid contractions.
                Use precise, academic terminology where appropriate.
                Maintain a respectful, professional tone throughout.
                """,
                "informal": """
                Use casual, conversational vocabulary and expressions.
                Include contractions, colloquialisms, and everyday language.
                Use simple, direct language that feels natural and relaxed.
                Maintain a friendly, approachable tone throughout.
                """,
                "academic": """
                Use scholarly, academic vocabulary and specialized terminology.
                Employ complex sentence structures and formal expressions.
                Include precise, technical language appropriate for academic contexts.
                Maintain an objective, analytical tone throughout.
                """,
                "business": """
                Use professional business vocabulary and industry terminology.
                Employ clear, direct language with action-oriented expressions.
                Include business-specific phrases and formal communication style.
                Maintain a confident, professional tone throughout.
                """,
                "neutral": """
                Use balanced vocabulary that is neither too formal nor too informal.
                Employ clear, standard language appropriate for general audiences.
                Avoid extreme formality or casualness.
                Maintain a balanced, accessible tone throughout.
                """
            }

            vocab_instruction = vocabulary_instructions.get(vocabulary_type, vocabulary_instructions["neutral"])

            prompt = f"""
Please regenerate the following text in {language} with {vocabulary_type} vocabulary type.

{preserve_style_instructions}

Vocabulary Type Instructions:
{vocab_instruction}

Requirements:
1. Maintain the original meaning and key information
2. Adjust vocabulary and expressions to match the {vocabulary_type} style
3. Keep approximately the same length as the original
4. Ensure the text remains coherent and natural
5. Do not add or remove important information

Original text:
{text}

Regenerated text with {vocabulary_type} vocabulary:
"""

            # Генерируем перегенерированный текст
            regenerated_text = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={"action": "regenerate_text", "vocabulary_type": vocabulary_type}
            )

            logger.info(f"Generated regenerated text (length: {len(regenerated_text)})")
            return regenerated_text

        except Exception as e:
            logger.error(f"Error regenerating text: {str(e)}")
            raise

    @memory_optimized()
    async def detect_text_level(
        self,
        text: str,
        language: str = "en",
        **kwargs
    ) -> TextLevelAnalysis:
        """
        Определяет уровень сложности текста

        Args:
            text (str): Текст для анализа
            language (str): Язык текста
            **kwargs: Дополнительные параметры

        Returns:
            TextLevelAnalysis: Анализ уровня текста
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Detecting text level for text in {language}")

            # Создаем промпт для определения уровня
            prompt = self._create_level_detection_prompt(text, language)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={"language": language}
            )

            # Парсим результат
            level_info = self._parse_level_analysis(content)

            return TextLevelAnalysis(
                original_text=text[:200] + "..." if len(text) > 200 else text,
                detected_level=level_info.get("level", "intermediate"),
                confidence=level_info.get("confidence", 0.8),
                analysis=content,
                language=language
            )

        except Exception as e:
            logger.error(f"Error detecting text level: {str(e)}")
            raise

    def _create_level_detection_prompt(self, text: str, language: str) -> str:
        """Создает промпт для определения уровня текста"""

        prompt = f"""
Analyze the following text in {language} and determine its difficulty level.

Consider:
- Vocabulary complexity
- Sentence structure
- Grammar complexity
- Topic sophistication

Provide:
1. Level (beginner/elementary/intermediate/upper-intermediate/advanced/proficiency)
2. Confidence score (0.0-1.0)
3. Brief explanation

Text to analyze:
{text}

Analysis:
"""

        return prompt

    def _parse_level_analysis(self, content: str) -> Dict[str, Any]:
        """Парсит результат анализа уровня"""
        try:
            # Простой парсинг - в реальности здесь была бы более сложная логика
            level = "intermediate"  # по умолчанию
            confidence = 0.8

            content_lower = content.lower()

            if "beginner" in content_lower or "elementary" in content_lower:
                level = "beginner"
            elif "advanced" in content_lower or "proficiency" in content_lower:
                level = "advanced"
            elif "upper-intermediate" in content_lower:
                level = "upper-intermediate"
            elif "intermediate" in content_lower:
                level = "intermediate"

            return {
                "level": level,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error parsing level analysis: {str(e)}")
            return {"level": "intermediate", "confidence": 0.5}
