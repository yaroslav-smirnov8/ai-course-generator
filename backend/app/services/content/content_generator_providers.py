# app/services/content/content_generator_providers.py
"""
Управление AI провайдерами для ContentGenerator
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class ContentGeneratorProviders:
    """
    Базовый класс для управления AI провайдерами
    """
    
    def __init__(self):
        """Инициализация всех доступных AI провайдеров"""
        # Получаем API ключи из переменных окружения (используем более новый подход)
        mistral_api_key = os.environ.get("MISTRAL_API_KEY")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        groq_api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY_TEST")
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        llm7_api_key = os.environ.get("LLM7_API_KEY")
        together_api_key = os.environ.get("TOGETHER_API_KEY_1")  # Используем первый ключ
        cerebras_api_key = os.environ.get("CEREBRAS_API_KEY_1")  # Используем первый ключ
        chutes_api_key = os.environ.get("CHUTES_API_KEY_1")     # Используем первый ключ

        # Инициализируем обработчики API для разных провайдеров
        self.mistral_handler = None
        self.gemini_handler = None
        self.groq_handler = None
        self.openrouter_handler = None
        self.llm7_handler = None
        self.together_handler = None
        self.cerebras_handler = None
        self.chutes_handler = None
        self.g4f_handler = None

        # Флаги доступности провайдеров
        self._mistral_available = False
        self._gemini_available = False
        self._groq_available = False
        self._openrouter_available = False
        self._llm7_available = False
        self._together_available = False
        self._cerebras_available = False
        self._chutes_available = False
        self._g4f_available = False

        # Инициализируем Gemini API если доступен ключ
        if gemini_api_key:
            try:
                from ...utils.gemini_api import GeminiHandler, GEMINI_AVAILABLE
                if GEMINI_AVAILABLE:
                    # Определяем component_id на основе типа контента
                    from ...utils.component_mapping import get_gemini_component_id
                    component_id = getattr(self, '_component_id', None)
                    # Если component_id не установлен, используем lesson-plan по умолчанию
                    # В реальном использовании component_id должен устанавливаться через content_type
                    if not component_id:
                        component_id = 'lesson-plan'
                    self.gemini_handler = GeminiHandler(
                        api_key=gemini_api_key, 
                        component_id=component_id,
                        use_proxy=True  # Включаем прокси по умолчанию
                    )
                    self._gemini_available = self.gemini_handler.is_available()
                    logger.info(f"GeminiHandler инициализирован для компонента '{component_id}' и доступен: {self._gemini_available}")
                else:
                    logger.warning("Библиотека Google Generative AI не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации GeminiHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ Google Gemini не найден в переменных окружения")

        # Инициализируем Mistral API если доступен ключ
        if mistral_api_key:
            try:
                from ...utils.mistral_api import MistralHandler, MISTRAL_AVAILABLE
                if MISTRAL_AVAILABLE:
                    self.mistral_handler = MistralHandler(api_key=mistral_api_key)
                    self._mistral_available = self.mistral_handler.is_available()
                    logger.info(f"MistralHandler инициализирован и доступен: {self._mistral_available}")
                else:
                    logger.warning("Библиотека Mistral не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации MistralHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ Mistral не найден в переменных окружения")

        # Инициализируем Groq API если доступен ключ
        if groq_api_key:
            try:
                from ...utils.groq_api import GroqHandler, GROQ_AVAILABLE
                if GROQ_AVAILABLE:
                    self.groq_handler = GroqHandler(api_key=groq_api_key)
                    self._groq_available = self.groq_handler.is_available()
                    logger.info(f"GroqHandler инициализирован и доступен: {self._groq_available}")
                else:
                    logger.warning("Библиотека Groq не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации GroqHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ Groq не найден в переменных окружения")

        # Инициализируем OpenRouter API если доступен ключ
        if openrouter_api_key:
            try:
                from ...utils.openrouter_api import OpenRouterHandler, OPENROUTER_AVAILABLE
                if OPENROUTER_AVAILABLE:
                    self.openrouter_handler = OpenRouterHandler(api_key=openrouter_api_key)
                    self._openrouter_available = self.openrouter_handler.is_available()
                    logger.info(f"OpenRouterHandler инициализирован и доступен: {self._openrouter_available}")
                else:
                    logger.warning("Библиотека OpenRouter не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации OpenRouterHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ OpenRouter не найден в переменных окружения")

        # Инициализируем Together AI API если доступен ключ
        if together_api_key:
            try:
                from ...utils.together_api import TogetherHandler, TOGETHER_AVAILABLE
                if TOGETHER_AVAILABLE:
                    self.together_handler = TogetherHandler(api_key=together_api_key)
                    self._together_available = self.together_handler.is_available()
                    logger.info(f"TogetherHandler инициализирован и доступен: {self._together_available}")
                else:
                    logger.warning("Библиотека Together AI не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации TogetherHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ Together AI не найден в переменных окружения")

        # Инициализируем Cerebras API если доступен ключ
        if cerebras_api_key:
            try:
                from ...utils.cerebras_api import CerebrasHandler, CEREBRAS_AVAILABLE
                if CEREBRAS_AVAILABLE:
                    self.cerebras_handler = CerebrasHandler(api_key=cerebras_api_key)
                    self._cerebras_available = self.cerebras_handler.is_available()
                    logger.info(f"CerebrasHandler инициализирован и доступен: {self._cerebras_available}")
                else:
                    logger.warning("Библиотека Cerebras не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации CerebrasHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ Cerebras не найден в переменных окружения")

        # Инициализируем Chutes AI API если доступен ключ
        if chutes_api_key:
            try:
                from ...utils.chutes_api import ChutesHandler, CHUTES_AVAILABLE
                if CHUTES_AVAILABLE:
                    self.chutes_handler = ChutesHandler(api_key=chutes_api_key)
                    self._chutes_available = self.chutes_handler.is_available()
                    logger.info(f"ChutesHandler инициализирован и доступен: {self._chutes_available}")
                else:
                    logger.warning("Библиотека Chutes AI не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации ChutesHandler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ Chutes AI не найден в переменных окружения")

        # Инициализируем LLM7 API если доступен ключ
        if llm7_api_key:
            try:
                from ...utils.llm7_api import LLM7Handler, LLM7_AVAILABLE
                if LLM7_AVAILABLE:
                    self.llm7_handler = LLM7Handler(api_key=llm7_api_key)
                    self._llm7_available = self.llm7_handler.is_available()
                    logger.info(f"LLM7Handler инициализирован и доступен: {self._llm7_available}")
                else:
                    logger.warning("Библиотека LLM7 не установлена")
            except Exception as e:
                logger.error(f"Ошибка при инициализации LLM7Handler: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("API ключ LLM7 не найден в переменных окружения")

        # Инициализируем G4F как запасной вариант
        try:
            from ...utils.g4f_handler import G4FHandler, G4F_AVAILABLE
            if G4F_AVAILABLE:
                self.g4f_handler = G4FHandler(
                    api_key=mistral_api_key,
                    openrouter_api_key=openrouter_api_key,
                    llm7_api_key=llm7_api_key,
                    gemini_handler=self.gemini_handler if self._gemini_available else None,
                    groq_handler=self.groq_handler if self._groq_available else None,
                    together_handler=self.together_handler if self._together_available else None,
                    cerebras_handler=self.cerebras_handler if self._cerebras_available else None,
                    chutes_handler=self.chutes_handler if self._chutes_available else None
                )
                self._g4f_available = True
                logger.info("G4FHandler инициализирован")
            else:
                logger.warning("G4F не установлен, этот провайдер будет недоступен")
        except Exception as e:
            logger.error(f"Ошибка при инициализации G4FHandler: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Логируем информацию о доступных провайдерах (используем более современный подход)
        available_providers = []
        if self._gemini_available:
            available_providers.append("Gemini")
        if self._openrouter_available:
            available_providers.append("OpenRouter")
        if self._groq_available:
            available_providers.append("Groq")
        if self._llm7_available:
            available_providers.append("LLM7")
        if self._together_available:
            available_providers.append("Together AI")
        if self._cerebras_available:
            available_providers.append("Cerebras")
        if self._chutes_available:
            available_providers.append("Chutes AI")
        if self._mistral_available:
            available_providers.append("Mistral")
        if self._g4f_available:
            available_providers.append("G4F")

        logger.info(f"ContentGenerator инициализирован с {len(available_providers)} провайдерами: {', '.join(available_providers)}")

    async def ensure_g4f_handler(self) -> bool:
        """Проверяем и обеспечиваем доступность провайдеров генерации"""
        # Если ни один провайдер не доступен, пробуем переинициализировать
        if not any([
            self._gemini_available, self._openrouter_available, self._groq_available,
            self._llm7_available, self._together_available, self._cerebras_available,
            self._chutes_available, self._mistral_available, self._g4f_available
        ]):
            logger.info("Ни один провайдер генерации не доступен, пробуем переинициализировать")
            return await self.refresh_g4f_handler()

        # Если хотя бы один провайдер доступен, возвращаем True
        return any([
            self._gemini_available, self._openrouter_available, self._groq_available,
            self._llm7_available, self._together_available, self._cerebras_available,
            self._chutes_available, self._mistral_available, self._g4f_available
        ])

    async def refresh_g4f_handler(self) -> bool:
        """Обновляем провайдеры генерации и проверяем их доступность"""
        try:
            logger.info("Обновление провайдеров генерации...")
            
            # Переинициализируем провайдеры
            self.__init__()
            
            # Проверяем доступность хотя бы одного провайдера
            available = any([
                self._gemini_available, self._openrouter_available, self._groq_available,
                self._llm7_available, self._together_available, self._cerebras_available,
                self._chutes_available, self._mistral_available, self._g4f_available
            ])
            
            if available:
                logger.info("Провайдеры генерации успешно обновлены")
            else:
                logger.warning("После обновления ни один провайдер не доступен")
                
            return available
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении провайдеров: {str(e)}")
            return False
