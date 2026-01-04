# app/services/content/generator.py

from g4f.client import AsyncClient
from g4f.Provider import RetryProvider, Pizzagpt, Pi, FreeChatgpt, You, GeminiPro, HuggingChat, DeepInfra, DeepInfraChat, ChatGpt, AiChatOnline, AmigoChat, Airforce
from g4f.Provider.nexra import NexraFluxPro
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
import asyncio
import re
import time
import uuid
import os
from youtube_transcript_api import YouTubeTranscriptApi
from ...models import VideoTranscript
from datetime import datetime, timedelta
from ...utils.log_config import get_g4f_logger

# Получаем настроенный логгер для g4f
g4f_logger = get_g4f_logger('g4f.gen')

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.g4f_client = AsyncClient(
            provider=RetryProvider([
                Pizzagpt, Pi, FreeChatgpt, You,
                GeminiPro, HuggingChat, DeepInfra, 
                DeepInfraChat, ChatGpt, AiChatOnline,
                NexraFluxPro, AmigoChat, Airforce
            ], shuffle=True)
        )
        g4f_logger.info("ContentGenerator initialized with g4f client")
        logger.info("ContentGenerator initialized")

    async def get_best_model(self) -> str:
        """Выбор лучшей доступной модели"""
        preferred_models = [
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "palm", "llama-2", "gemini-pro"
        ]

        request_id = str(uuid.uuid4())
        g4f_logger.info(f"[{request_id}] Starting model selection test")

        for model in preferred_models:
            try:
                g4f_logger.info(f"[{request_id}] Testing model: {model}")
                start_time = time.time()
                
                response = await self.g4f_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Test"}]
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                logger.info(f"Successfully connected to model: {model}")
                g4f_logger.info(f"[{request_id}] Successfully connected to model: {model}. Response time: {duration:.2f}s")
                return model
                
            except Exception as e:
                logger.warning(f"Model {model} is not available: {str(e)}")
                g4f_logger.warning(f"[{request_id}] Model {model} is not available: {str(e)}")
                continue

        error_msg = "No available models found"
        logger.error(error_msg)
        g4f_logger.error(f"[{request_id}] {error_msg}")
        raise Exception(error_msg)

    async def generate_content(self, prompt: str) -> str:
        """Генерация контента с использованием лучшей доступной модели"""
        max_retries = 3
        last_error = None
        request_id = str(uuid.uuid4())
        
        prompt_summary = prompt[:100] + "..." if len(prompt) > 100 else prompt
        g4f_logger.info(f"[{request_id}] Starting content generation")
        g4f_logger.info(f"[{request_id}] Prompt summary: {prompt_summary}")
        g4f_logger.info(f"[{request_id}] Prompt length: {len(prompt)}")

        for attempt in range(max_retries):
            try:
                logger.info(f"Generation attempt {attempt + 1}/{max_retries}")
                g4f_logger.info(f"[{request_id}] Generation attempt {attempt + 1}/{max_retries}")
                
                model = await self.get_best_model()
                logger.info(f"Using model: {model}")
                g4f_logger.info(f"[{request_id}] Using model: {model}")

                messages = [
                    {
                        "role": "system",
                        "content": "You are a professional teacher creating detailed lesson plans. Provide complete, untruncated responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                g4f_logger.info(f"[{request_id}] Sending request to provider...")
                start_time = time.time()

                response = await self.g4f_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    presence_penalty=0.6,
                    frequency_penalty=0.3
                )
                
                end_time = time.time()
                duration = end_time - start_time
                g4f_logger.info(f"[{request_id}] Received response from provider. Time: {duration:.2f}s")

                if not response or not response.choices:
                    error_msg = "Empty response from model"
                    g4f_logger.error(f"[{request_id}] {error_msg}")
                    raise ValueError(error_msg)

                content = response.choices[0].message.content
                logger.info(f"Generated content length: {len(content)}")
                g4f_logger.info(f"[{request_id}] Generated content length: {len(content)}")
                g4f_logger.info(f"[{request_id}] Response beginning: {content[:100]}...")

                if "Generated by" in content:
                    content = content.split("Generated by")[0].strip()
                    g4f_logger.info(f"[{request_id}] Cleaned promotional content from response")

                g4f_logger.info(f"[{request_id}] Content generation successful")
                return content

            except Exception as e:
                last_error = e
                error_msg = f"Error in attempt {attempt + 1}: {str(e)}"
                logger.error(error_msg)
                g4f_logger.error(f"[{request_id}] {error_msg}")
                continue

        final_error = f"Failed to generate content after {max_retries} attempts. Last error: {str(last_error)}"
        logger.error(final_error)
        g4f_logger.error(f"[{request_id}] {final_error}")
        raise Exception(final_error)

    async def generate_image(self, request) -> str:
        """Генерация изображения"""
        try:
            logger.info(f"Attempting to generate image with prompt: {request.prompt}")

            response = await self.g4f_client.images.generate(
                model="sdxl",
                prompt=request.prompt,
                response_format="url"
            )

            if not response or not response.data:
                logger.warning("Empty response received from image model")
                raise ValueError("Empty response from image model")

            image_url = response.data[0].url
            logger.info(f"Image generated successfully. URL: {image_url}")
            return image_url

        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}", exc_info=True)
            raise

    async def process_video_transcript(self, video_id: str, subtitle_language: str = 'en') -> str:
        """Обработка транскрипта видео с кэшированием"""
        try:
            video_id = self._extract_video_id(video_id)

            async with self.db.begin():
                cached_transcript = await self.db.execute(
                    select(VideoTranscript).filter(
                        VideoTranscript.video_id == video_id,
                        VideoTranscript.language == subtitle_language,
                        VideoTranscript.expires_at > datetime.utcnow()
                    )
                )
                cached_transcript = cached_transcript.scalar_one_or_none()

            if cached_transcript:
                logger.info(f"Found cached transcript for video {video_id}")
                return cached_transcript.transcript

            transcript = await asyncio.to_thread(
                YouTubeTranscriptApi.get_transcript,
                video_id,
                languages=[subtitle_language, 'en']
            )

            formatted_transcript = self._format_transcript(transcript)

            async with self.db.begin():
                new_transcript = VideoTranscript(
                    video_id=video_id,
                    language=subtitle_language,
                    transcript=formatted_transcript,
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                self.db.add(new_transcript)

            return formatted_transcript

        except Exception as e:
            logger.error(f"Error processing video transcript: {str(e)}", exc_info=True)
            raise

    def _extract_video_id(self, video_id_or_url: str) -> str:
        """Extract video ID from URL if necessary"""
        # Check if it's a full URL
        if video_id_or_url.startswith(('http://', 'https://', 'www.')):
            # Extract video ID from URL
            pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
            match = re.search(pattern, video_id_or_url)
            if match:
                return match.group(1)
            else:
                raise ValueError("Invalid YouTube URL")
        return video_id_or_url  # If it's not a URL, assume it's already a video ID

    def _format_transcript(self, transcript: list) -> str:
        """Форматирование транскрипта"""
        return ' '.join(entry['text'] for entry in transcript)

    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Суммаризация длинного текста"""
        try:
            model = await self.get_best_model()
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Summarize the following text in no more than {max_length} words:"
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            raise

    async def generate_questions(self, text: str, num_questions: int = 5, vocabulary: str = None, grammar: str = None) -> list:
        """Генерация вопросов на основе текста"""
        try:
            model = await self.get_best_model()
            
            # Добавляем информацию о целевой лексике и грамматике
            vocabulary_instruction = ""
            if vocabulary:
                vocabulary_instruction = f"- Focus on {vocabulary} vocabulary in the questions\n"
            else:
                vocabulary_instruction = "- Identify and use key vocabulary from the text in the questions\n"
                
            grammar_instruction = ""
            if grammar:
                grammar_instruction = f"- Include questions that practice {grammar} grammar structures\n"
            else:
                grammar_instruction = "- Identify and use important grammar structures from the text in the questions\n"
            
            # Создаем промпт по структуре CARE (Context, Ask, Rules, Examples)
            care_prompt = f"""
# CONTEXT:
I am working with a text that contains approximately {len(text.split())} words.
The text is about: {text[:100]}...

# ASK:
Generate {num_questions} diverse and meaningful questions based on the provided text.

# RULES:
- Create questions that check different aspects of the text (main ideas, details, inferences, etc.)
- Questions should be clear, concise, and directly related to the text
- Include a mix of question types (factual, analytical, inferential, evaluative)
- Avoid yes/no questions unless they lead to deeper discussion
- Ensure questions are grammatically correct and well-formulated
- Questions should be numbered from 1 to {num_questions}
- Do not include answers to the questions
{vocabulary_instruction}{grammar_instruction}

# EXAMPLES:
For the text: "Learning foreign languages develops cognitive abilities. Studies show that bilinguals are better at multitasking. They also have improved memory and attention."

Example questions:
1. How does learning foreign languages affect cognitive abilities according to the text?
2. What specific advantage do bilinguals have when it comes to task management?
3. What cognitive improvements besides multitasking are mentioned for people who speak multiple languages?
4. What connection can be made between bilingualism and memory based on the text?
5. How might the cognitive benefits mentioned in the text apply to other areas of life?
"""
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": care_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.8
            )
            
            # Обработка ответа
            raw_questions = response.choices[0].message.content.split('\n')
            
            # Фильтруем и очищаем вопросы
            questions = []
            for line in raw_questions:
                line = line.strip()
                # Ищем строки, которые начинаются с цифры и точки (вопросы)
                if re.match(r'^\d+\.', line):
                    # Удаляем номер в начале
                    question = re.sub(r'^\d+\.\s*', '', line)
                    questions.append(question)
            
            # Если не удалось извлечь вопросы по формату, берем все непустые строки
            if not questions:
                questions = [q.strip() for q in raw_questions if q.strip()]
                
            # Ограничиваем количество вопросов
            return questions[:num_questions]
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            raise

    async def translate_text(self, text: str, target_language: str) -> str:
        """Перевод текста на целевой язык"""
        try:
            model = await self.get_best_model()
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following text to {target_language}:"
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            raise

    async def detect_text_level(self, text: str, language: str) -> dict:
        """Определение уровня текста"""
        try:
            model = await self.get_best_model()
            
            # Определяем систему уровней в зависимости от языка
            level_system = "CEFR (A1, A2, B1, B2, C1, C2)" if language.lower() in ["english", "french", "german", "spanish", "italian"] else "Basic/Intermediate/Advanced"
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Analyze the following text in {language} and determine its language level according to {level_system}. 
                        Provide a detailed analysis including:
                        1. The determined level
                        2. Average sentence length
                        3. Vocabulary diversity
                        4. Grammar complexity
                        5. Recommendations for language learners
                        
                        Format your response as a structured JSON with the following keys:
                        - level: the determined level
                        - sentence_length: average sentence length
                        - vocabulary: description of vocabulary diversity
                        - grammar: description of grammar complexity
                        - recommendations: list of recommendations
                        """
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            
            # Попытка извлечь JSON из ответа
            import json
            import re
            
            # Ищем JSON в ответе
            json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result
            
            try:
                # Пытаемся распарсить JSON
                analysis = json.loads(json_str)
                return analysis
            except json.JSONDecodeError:
                # Если не удалось распарсить, возвращаем текстовый ответ
                return {
                    "level": "Unknown",
                    "analysis": result
                }
                
        except Exception as e:
            logger.error(f"Error detecting text level: {str(e)}")
            raise

    async def regenerate_text(self, text: str, language: str, vocabulary_type: str = "neutral") -> str:
        """Перегенерация текста с заданным типом лексики"""
        try:
            model = await self.get_best_model()
            
            vocabulary_descriptions = {
                "simple": "simple, basic vocabulary suitable for beginners",
                "neutral": "neutral, standard vocabulary",
                "advanced": "advanced, diverse vocabulary",
                "academic": "academic, formal vocabulary suitable for research papers",
                "professional": "professional vocabulary specific to the text's domain"
            }
            
            vocab_description = vocabulary_descriptions.get(vocabulary_type, "neutral, standard vocabulary")
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Rewrite the following text in {language} using {vocab_description}.
                        Maintain the same meaning, length, and structure, but adapt the vocabulary according to the specified type.
                        Do not add explanations or comments - just provide the rewritten text.
                        """
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error regenerating text: {str(e)}")
            raise

    async def change_text_level(self, text: str, language: str, target_level: str) -> str:
        """Изменение уровня сложности текста"""
        try:
            model = await self.get_best_model()
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Adapt the following text in {language} to {target_level} level.
                        Maintain the same meaning and content, but adjust:
                        1. Vocabulary complexity
                        2. Sentence structure
                        3. Grammar complexity
                        4. Overall readability
                        
                        Do not add explanations or comments - just provide the adapted text.
                        """
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error changing text level: {str(e)}")
            raise

    async def generate_titles(self, text: str, language: str, count: int = 4) -> list:
        """Генерация вариантов названий для текста"""
        try:
            model = await self.get_best_model()
            
            # Создаем промпт по структуре CARE (Context, Ask, Rules, Examples)
            care_prompt = f"""
# CONTEXT:
I am working with a text in {language} that contains approximately {len(text.split())} words.
The text begins with: {text[:100]}...

# ASK:
Generate {count} different title options for this text.

# RULES:
- Create titles that accurately reflect the main topic of the text
- Each title should be unique and different in style
- Titles should be concise (no more than 10 words each)
- Titles should be attention-grabbing and engaging
- Include the following types of titles:
  1. Informative title (clearly stating the main topic)
  2. Creative title (using metaphor or wordplay)
  3. Question title (framed as a question)
  4. Title with a number (e.g., "5 Ways to...")
  5. Title with a colon (e.g., "Main Topic: Subtopic")
- Format your response as a numbered list (1. Title One, 2. Title Two, etc.)
- Do not use generic or vague titles

# EXAMPLES:
For the text: "Learning foreign languages develops cognitive abilities. Studies show that bilinguals are better at multitasking. They also have improved memory and attention."

Example titles:
1. The Cognitive Benefits of Learning Foreign Languages
2. Brain Power Unleashed: How Language Learning Transforms Your Mind
3. Can Speaking Multiple Languages Make You Smarter?
4. 3 Ways Bilingualism Enhances Your Cognitive Abilities
5. Language Mastery: The Secret to Better Memory and Attention
"""
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": care_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.8
            )
            
            result = response.choices[0].message.content
            
            # Обработка ответа для извлечения заголовков
            # Сначала пробуем найти нумерованный список
            titles = []
            lines = result.split('\n')
            
            for line in lines:
                line = line.strip()
                # Ищем строки, которые начинаются с цифры и точки (заголовки)
                if re.match(r'^\d+\.', line):
                    # Удаляем номер в начале
                    title = re.sub(r'^\d+\.\s*', '', line)
                    titles.append(title)
            
            # Если не удалось извлечь заголовки по формату, пробуем другие методы
            if not titles:
                # Пытаемся извлечь JSON из ответа
                import json
                import re
                
                # Ищем JSON в ответе
                json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    try:
                        # Пытаемся распарсить JSON
                        titles_data = json.loads(json_str)
                        if isinstance(titles_data, list):
                            titles = titles_data
                        elif isinstance(titles_data, dict) and 'titles' in titles_data:
                            titles = titles_data['titles']
                    except:
                        # Если не удалось распарсить JSON, берем все непустые строки
                        titles = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                else:
                    # Если нет JSON, берем все непустые строки, которые не являются заголовками разделов
                    titles = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            
            # Очищаем заголовки от кавычек и других символов
            titles = [title.strip('"\'').strip() for title in titles]
            
            # Удаляем дубликаты и пустые строки
            titles = [title for title in titles if title]
            titles = list(dict.fromkeys(titles))  # Удаление дубликатов с сохранением порядка
            
            # Ограничиваем количество заголовков
            return titles[:count]
                
        except Exception as e:
            logger.error(f"Error generating titles: {str(e)}")
            raise

    async def generate_comprehension_test(self, text: str, language: str, question_count: int = 5, difficulty: str = "medium") -> str:
        """Генерация теста на понимание текста"""
        try:
            model = await self.get_best_model()
            
            difficulty_descriptions = {
                "easy": "basic comprehension questions suitable for beginners",
                "medium": "moderate difficulty questions requiring good understanding",
                "hard": "challenging questions requiring deep analysis and inference"
            }
            
            diff_description = difficulty_descriptions.get(difficulty, "moderate difficulty questions")
            
            # Создаем промпт по структуре CARE (Context, Ask, Rules, Examples)
            care_prompt = f"""
# CONTEXT:
I am working with a text in {language} that contains approximately {len(text.split())} words.
The text begins with: {text[:100]}...
The difficulty level requested is: {difficulty} ({diff_description})

# ASK:
Create a comprehensive reading comprehension test with {question_count} questions in various formats based on the provided text.

# RULES:
- Each question must test a different aspect of text comprehension
- Questions should be at {difficulty} difficulty level ({diff_description})
- Include a variety of question formats (distribute evenly across the test):
  1. True/False/Not Stated questions (statements that are true, false, or not mentioned in the text)
  2. Multiple-choice questions with 4 options (a, b, c, d)
  3. Complete the sentence questions (where students choose the correct ending)
  4. Meaning questions (asking what the author meant by a specific phrase)
  5. Short answer questions (requiring a brief response based on the text)
- For multiple-choice questions:
  * Mark the correct answer with a ✓ symbol
  * Incorrect options should be plausible but clearly wrong based on the text
- For True/False/Not Stated questions:
  * Clearly indicate the correct answer (True, False, or Not Stated)
  * Include a mix of all three types
- For sentence completion:
  * Provide 3-4 possible endings, with only one being correct
  * Mark the correct ending with a ✓ symbol
- Format the test in Markdown with clear sections and numbering
- Questions should be challenging but fair
- All questions and answers must be based solely on the text content
- Number each question and clearly indicate its type

# EXAMPLES:
For the text: "Learning foreign languages develops cognitive abilities. Studies show that bilinguals are better at multitasking. They also have improved memory and attention. Additionally, knowing multiple languages opens up new career opportunities and helps in understanding other cultures better."

Example comprehension test:

## Reading Comprehension Test

### 1. Multiple Choice
What is the main benefit of learning foreign languages according to the text?
a) Improved social skills
b) Enhanced cognitive abilities ✓
c) Better career prospects
d) Cultural appreciation

### 2. True/False/Not Stated
Bilingual people have better mathematical abilities.
Answer: Not Stated

### 3. True/False/Not Stated
Learning multiple languages improves memory.
Answer: True

### 4. Complete the Sentence
According to the text, knowing multiple languages helps in...
a) getting higher grades in school
b) understanding other cultures better ✓
c) learning musical instruments faster
d) improving physical coordination

### 5. Meaning Question
What does the author mean by saying bilinguals are "better at multitasking"?
a) They can speak two languages simultaneously
b) They can perform multiple tasks at the same time more effectively ✓
c) They can learn multiple languages at once
d) They can teach others while learning themselves
"""
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": care_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating comprehension test: {str(e)}")
            raise

    async def generate_summaries(self, text: str, language: str) -> str:
        """Генерация резюме текста разной длины"""
        try:
            model = await self.get_best_model()
            
            # Создаем промпт по структуре CARE (Context, Ask, Rules, Examples)
            care_prompt = f"""
# CONTEXT:
I am working with a text in {language} that contains approximately {len(text.split())} words and {len(text.split('.')) + len(text.split('!')) + len(text.split('?')) - 2} sentences.
The text begins with: {text[:100]}...

# ASK:
Create three different summaries of the text at different levels of detail:
1. Brief summary (1-2 sentences)
2. Medium summary (3-5 sentences)
3. Detailed summary (6-10 sentences)

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

# EXAMPLES:
For the text: "Learning foreign languages develops cognitive abilities. Studies show that bilinguals are better at multitasking. They also have improved memory and attention. Additionally, knowing multiple languages opens up new career opportunities and helps in understanding other cultures better. Research indicates that children who learn multiple languages from an early age develop more flexible thinking patterns. Some studies even suggest that bilingualism may delay the onset of dementia in older adults."

Example summaries:

## Brief Summary (1-2 sentences):
Learning foreign languages enhances cognitive abilities like multitasking, memory, and attention, while also providing career advantages and cultural understanding benefits.

## Medium Summary (3-5 sentences):
Learning foreign languages develops various cognitive abilities, with studies showing that bilinguals excel at multitasking and have better memory and attention. Knowledge of multiple languages also creates new career opportunities and improves cross-cultural understanding. Children who learn languages early develop more flexible thinking, and bilingualism may even delay dementia in older adults.

## Detailed Summary (6-10 sentences):
Learning foreign languages has been shown to significantly enhance cognitive abilities in several ways. Research demonstrates that bilingual individuals perform better at multitasking compared to those who speak only one language. Studies also indicate that people who know multiple languages exhibit improved memory capacity and attention skills. Beyond these cognitive benefits, language proficiency opens up additional career opportunities in our increasingly globalized world. Multilingual individuals can better understand and appreciate cultural differences, facilitating cross-cultural communication. Children exposed to multiple languages from an early age develop more flexible thinking patterns and problem-solving approaches. Interestingly, scientific research suggests that bilingualism might delay the onset of dementia and other cognitive decline in elderly populations. These findings highlight the lifelong advantages of language learning beyond just communication skills.
"""
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": care_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating summaries: {str(e)}")
            raise

    async def _format_prompt(self, prompt_type: str, data: dict) -> str:
        """Вспомогательный метод для форматирования промптов"""
        if prompt_type == "lesson_plan":
            prompt = f"""Create a lesson plan for {data['language']} language learning.
Topic: {data['topic']}
Age group: {data['age']}
Previous lesson: {data.get('previous_lesson', 'N/A')}
Grammar focus: {data.get('grammar', 'N/A')}
Vocabulary focus: {data.get('vocabulary', 'N/A')}
Lesson type: {data['individual_group']}
Format: {data['online_offline']}
Exam preparation: {data.get('exam', 'N/A')}"""

            # Добавляем специфические инструкции в зависимости от формата урока
            if data['individual_group'] == 'individual':
                prompt += """

!!! CRITICAL INSTRUCTION !!!
This is an INDIVIDUAL lesson (one-on-one teaching). You MUST follow these rules:
- DO NOT include ANY pair work or group activities
- DO NOT use phrases like "break into pairs", "work in groups", "discuss with your partner", or similar
- All activities MUST be designed for one-on-one interaction between teacher and student only
- Focus on personalized feedback and individual practice
- Adapt all activities to be suitable for a single student working with the teacher

The entire lesson plan MUST be appropriate for individual teaching. Review your final plan to ensure no group activities are included.
"""
            else:  # group
                prompt += """

This is a GROUP lesson. You should:
- Include collaborative activities and pair/group work
- Incorporate peer feedback and group discussions
- Design activities that promote interaction among students
- Include opportunities for students to practice with different partners
"""

            return prompt

        elif prompt_type == "exercise":
            return f"""Create {data['quantity']} {data['difficulty']} {data['exercise_type']} exercises.
    Language: {data['language']}
    Topic: {data['topic']}"""

        elif prompt_type == "game":
            return f"""Create a {data['game_type']} game for {data['language']} learning.
    Topic: {data['topic']}
    Duration: {data['duration']} minutes"""

        return str(data)

    async def generate_lesson_plan(self, text: str, language: str, age: str = "teens") -> str:
        """Генерация плана урока на основе текста"""
        try:
            model = await self.get_best_model()
            
            # Определяем возрастную группу
            age_map = {
                "children": "children (7-12 years old)",
                "teens": "teenagers (13-17 years old)",
                "adults": "adults (18+ years old)"
            }
            
            age_description = age_map.get(age, "teenagers (13-17 years old)")
            
            # Создаем промпт по структуре CARE (Context, Ask, Rules, Examples)
            care_prompt = f"""
# CONTEXT:
Я работаю с текстом на {language}, который содержит примерно {len(text.split())} слов.
Текст начинается с: {text[:100]}...
Целевая аудитория: {age_description}

# ASK:
Создай детальный план урока для обучения {language} языку на основе предоставленного текста.

# RULES:
КРИТИЧЕСКИ ВАЖНО - ЯЗЫКОВОЕ РАЗДЕЛЕНИЕ:
- ВСЕ ИНСТРУКЦИИ ДЛЯ УЧИТЕЛЯ должны быть написаны на РУССКОМ языке
- ВСЕ УПРАЖНЕНИЯ И ЗАДАНИЯ ДЛЯ УЧЕНИКОВ должны быть написаны на {language.upper()} языке
- План урока должен быть структурированным и логичным
- Включи четкие цели обучения (образовательные, развивающие и воспитательные)
- Раздели урок на этапы с указанием времени
- Добавь разнообразные активности для разных стилей обучения
- Учти возрастные особенности целевой аудитории ({age_description})
- Включи интерактивные и увлекательные элементы
- План урока должен включать:
  * Организационный момент (3-5 минут)
  * Разминка (5-7 минут)
  * Основная часть (20-25 минут)
  * Практика (15-20 минут)
  * Заключение (5-10 минут)
  * Домашнее задание
- Форматируй ответ в Markdown с четкими заголовками и списками
- Не включай никаких примечаний или оговорок в конце

# EXAMPLES:
Для текста: "Learning foreign languages develops cognitive abilities. Studies show that bilinguals are better at multitasking. They also have improved memory and attention."

## План урока для подростков

### Тема: Преимущества изучения иностранных языков

### Цели обучения:
#### Образовательные:
- Познакомить учащихся с понятием когнитивных способностей и влиянием изучения языков на них
- Развить навыки критического мышления и анализа
- Изучить новую лексику, связанную с познанием и изучением языков

#### Развивающие:
- Развить навыки публичных выступлений
- Улучшить способность работать в группах
- Усилить аналитическое мышление

#### Воспитательные:
- Способствовать мотивации к самостоятельному изучению языков
- Развить уважение к культурным различиям
- Воспитать ответственность за собственное обучение

### Материалы и оборудование:
- Раздаточные материалы с текстом
- Карточки с лексикой
- Презентация о когнитивных способностях
- Интерактивная доска/проектор

### План урока:

#### 1. Организационный момент (3-5 минут)
- Приветствие
- Проверка присутствующих
- Объявление темы и целей

#### 2. Разминка (5-7 минут)
- Мозговой штурм: "What do you already know about the benefits of learning languages?"
- Короткий видеоролик с последующим обсуждением
- Игра "True or False" с фактами об изучении языков

#### 3. Основная часть (20-25 минут)
- Чтение текста о изучении языков и когнитивных способностях
- Обсуждение новых терминов и понятий
- Групповая работа: анализ исследований о билингвах
- Презентация результатов групповой работы

#### 4. Практика (15-20 минут)
- Create a mind map of the text
- Discussion of problematic questions from the text
- Role-play based on situations from the text
- Vocabulary work with key terms

#### 5. Заключение (5-10 минут)
- Подведение итогов урока
- Рефлексия: что нового узнали, что было интересно
- Объяснение домашнего задания

### Домашнее задание:
- Write a short essay on the topic
- Prepare a presentation about one aspect of the topic
- Find additional information on the topic
"""
            
            response = await self.g4f_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": care_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating lesson plan: {str(e)}")
            raise