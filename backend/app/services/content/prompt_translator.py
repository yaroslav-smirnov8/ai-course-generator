"""
Сервис для перевода промптов генерации изображений на английский язык
Использует LLM7 ChatGPT 4.1 для качественного перевода
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ...utils.llm7_api import LLM7Handler, LLM7_AVAILABLE, LLM7ConnectionException, LLM7RateLimitException

logger = logging.getLogger(__name__)

class PromptTranslationService:
    """
    Сервис для перевода промптов генерации изображений на английский язык
    """
    
    def __init__(self):
        """Инициализация сервиса перевода"""
        self.llm7_handler = None
        self._last_request_time = None
        self._request_delay = 1.0  # Минимальная задержка между запросами в секундах
        self._max_retries = 3
        self._retry_delay = 2.0  # Задержка между повторными попытками
        
        # Инициализируем LLM7 handler
        self._initialize_llm7()
        
        # Кэш переводов для избежания повторных запросов
        self._translation_cache = {}
        self._cache_ttl = timedelta(hours=24)  # TTL кэша - 24 часа
        
    def _initialize_llm7(self):
        """Инициализация LLM7 handler"""
        try:
            if LLM7_AVAILABLE:
                self.llm7_handler = LLM7Handler()
                if self.llm7_handler.is_available():
                    logger.info("✅ PromptTranslationService: LLM7 handler initialized successfully")
                else:
                    logger.warning("⚠️ PromptTranslationService: LLM7 handler not available (no API key)")
                    self.llm7_handler = None
            else:
                logger.warning("⚠️ PromptTranslationService: LLM7 library not available")
        except Exception as e:
            logger.error(f"❌ PromptTranslationService: Failed to initialize LLM7 handler: {e}")
            self.llm7_handler = None
    
    def is_available(self) -> bool:
        """Проверяет доступность сервиса перевода"""
        return self.llm7_handler is not None and self.llm7_handler.is_available()
    
    def _is_english(self, text: str) -> bool:
        """
        Простая проверка, является ли текст уже на английском языке
        
        Args:
            text: Текст для проверки
            
        Returns:
            True если текст уже на английском, False если нужен перевод
        """
        # Удаляем знаки препинания и цифры для анализа
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        
        if not words:
            return True  # Пустой текст считаем английским
        
        # Проверяем наличие кириллических символов
        cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
        if cyrillic_pattern.search(text):
            return False
        
        # Если нет кириллицы и есть латинские буквы, считаем английским
        latin_pattern = re.compile(r'[a-z]', re.IGNORECASE)
        if latin_pattern.search(text):
            return True
        
        # Если только цифры и знаки, считаем английским
        return True
    
    def _get_cache_key(self, text: str) -> str:
        """Генерирует ключ кэша для текста"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_cached_translation(self, text: str) -> Optional[str]:
        """Получает перевод из кэша если он актуален"""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self._translation_cache:
            cached_data = self._translation_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self._cache_ttl:
                logger.debug(f"Using cached translation for: {text[:50]}...")
                return cached_data['translation']
            else:
                # Удаляем устаревший кэш
                del self._translation_cache[cache_key]
        
        return None
    
    def _cache_translation(self, original: str, translation: str):
        """Сохраняет перевод в кэш"""
        cache_key = self._get_cache_key(original)
        self._translation_cache[cache_key] = {
            'translation': translation,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cached translation: {original[:50]}... -> {translation[:50]}...")
    
    async def _wait_for_rate_limit(self):
        """Ожидание для соблюдения rate limit"""
        if self._last_request_time:
            elapsed = datetime.now() - self._last_request_time
            if elapsed.total_seconds() < self._request_delay:
                wait_time = self._request_delay - elapsed.total_seconds()
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        self._last_request_time = datetime.now()
    
    def _create_translation_prompt(self, text: str) -> str:
        """
        Создает промпт для перевода текста на английский
        
        Args:
            text: Исходный текст для перевода
            
        Returns:
            Промпт для LLM7
        """
        return f"""You are a professional translator specializing in image generation prompts. 

Your task is to translate the following text to English while preserving the artistic and descriptive intent for image generation.

IMPORTANT RULES:
1. Translate ONLY the user input, preserve any existing English parts
2. Keep artistic terms, style descriptions, and technical parameters intact
3. Maintain the creative intent and visual description quality
4. If the text is already in English, return it unchanged
5. For mixed language text, translate only non-English parts
6. Preserve formatting, commas, and structure
7. Focus on accuracy for visual/artistic descriptions

Text to translate:
{text}

Provide ONLY the translated text, no explanations or additional text."""

    async def translate_prompt(self, prompt: str) -> str:
        """
        Переводит промпт на английский язык
        
        Args:
            prompt: Исходный промпт для перевода
            
        Returns:
            Переведенный промпт на английском языке
            
        Raises:
            Exception: При ошибке перевода
        """
        if not prompt or not prompt.strip():
            return prompt
        
        # Проверяем, нужен ли перевод
        if self._is_english(prompt):
            logger.debug(f"Prompt already in English: {prompt[:50]}...")
            return prompt
        
        # Проверяем кэш
        cached_translation = self._get_cached_translation(prompt)
        if cached_translation:
            return cached_translation
        
        # Проверяем доступность сервиса
        if not self.is_available():
            logger.warning("Translation service not available, returning original prompt")
            return prompt
        
        logger.info(f"🔄 Translating prompt: {prompt[:100]}...")
        
        # Выполняем перевод с повторными попытками
        for attempt in range(self._max_retries):
            try:
                # Соблюдаем rate limit
                await self._wait_for_rate_limit()
                
                # Создаем промпт для перевода
                translation_prompt = self._create_translation_prompt(prompt)
                
                # Выполняем перевод с использованием ChatGPT 4.1
                translated = await self.llm7_handler.generate_content(
                    prompt=translation_prompt,
                    model="gpt-4.1-2025-04-14",  # Используем ChatGPT 4.1
                    temperature=0.3,  # Низкая температура для точного перевода
                    max_tokens=500
                )
                
                if not translated or not translated.strip():
                    raise Exception("Empty translation received")
                
                # Очищаем результат от лишних символов
                translated = translated.strip()

                # Проверяем, не вернулся ли полный JSON ответ вместо содержимого
                if translated.startswith('{"id":') and '"content":"' in translated:
                    try:
                        import json
                        json_response = json.loads(translated)
                        if 'choices' in json_response and len(json_response['choices']) > 0:
                            choice = json_response['choices'][0]
                            if 'message' in choice and 'content' in choice['message']:
                                translated = choice['message']['content'].strip()
                                logger.info(f"✅ Extracted content from JSON response: {translated[:50]}...")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse JSON response, using as-is: {e}")

                # Кэшируем результат
                self._cache_translation(prompt, translated)
                
                logger.info(f"✅ Successfully translated prompt: {prompt[:50]}... -> {translated[:50]}...")
                return translated
                
            except LLM7RateLimitException as e:
                logger.warning(f"⚠️ Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries reached for rate limit, returning original prompt")
                    return prompt
                    
            except LLM7ConnectionException as e:
                logger.error(f"❌ Connection error on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries reached for connection error, returning original prompt")
                    return prompt
                    
            except Exception as e:
                logger.error(f"❌ Translation error on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries reached, returning original prompt")
                    return prompt
        
        # Если все попытки неудачны, возвращаем оригинальный промпт
        return prompt

    def clear_cache(self):
        """Очищает кэш переводов"""
        self._translation_cache.clear()
        logger.info("Translation cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        active_entries = 0
        expired_entries = 0

        now = datetime.now()
        for cached_data in self._translation_cache.values():
            if now - cached_data['timestamp'] < self._cache_ttl:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            'total_entries': len(self._translation_cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'cache_ttl_hours': self._cache_ttl.total_seconds() / 3600
        }

# Глобальный экземпляр сервиса
try:
    prompt_translation_service = PromptTranslationService()
    logger.info("✅ PromptTranslationService successfully initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize PromptTranslationService: {e}")
    prompt_translation_service = None
