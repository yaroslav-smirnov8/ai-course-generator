"""
Тестовый скрипт для проверки интеграции G4FHandler с новым модулем MistralHandler
"""

import os
import asyncio
import logging
import sys
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()

logger.info("Пытаемся импортировать необходимые модули...")
try:
    from g4f_handler import G4FHandler
    from mistral_api import MistralHandler
    logger.info("Модули успешно импортированы")
except ImportError as e:
    logger.error(f"Ошибка импорта модулей: {e}")
    logger.error("Проверьте установку необходимых библиотек")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

async def test_integration():
    """Тестирование интеграции G4FHandler с MistralHandler"""
    # Получаем API ключ из переменной окружения
    api_key = os.environ.get("MISTRAL_API_KEY")
    
    if not api_key:
        logger.error("API ключ Mistral не найден в переменных окружения")
        logger.info("Установите переменную MISTRAL_API_KEY или передайте ключ через параметр")
        return
    
    logger.info(f"API ключ получен (начинается с {api_key[:4]}...)")
    
    try:
        logger.info("Инициализация G4FHandler...")
        # Инициализируем G4FHandler с API ключом
        g4f_handler = G4FHandler(api_key=api_key)
        logger.info("G4FHandler успешно инициализирован")
        
        # Проверяем, что MistralHandler был успешно инициализирован внутри G4FHandler
        if not hasattr(g4f_handler, 'mistral_handler') or not g4f_handler.mistral_handler:
            logger.error("Атрибут mistral_handler не найден в G4FHandler")
            return
            
        if not g4f_handler.mistral_handler.is_available():
            logger.error("MistralHandler доступен, но API недоступен")
            return
        
        logger.info("G4FHandler успешно инициализирован с MistralHandler")
        
        # Тестовые промпты
        test_prompts = [
            "Напиши короткое стихотворение о программировании на Python",
            "Объясни, что такое рекурсия в программировании",
            "Расскажи о преимуществах и недостатках микросервисной архитектуры"
        ]
        
        # Тестируем генерацию через generate_content (асинхронный метод)
        logger.info("Тестирование асинхронной генерации через generate_content...")
        for i, prompt in enumerate(test_prompts, 1):
            logger.info(f"Тест {i}: Генерация ответа на промпт: '{prompt[:50]}...'")
            try:
                result = await g4f_handler.generate_content(prompt=prompt)
                logger.info(f"Результат {i} (длина: {len(result)}): '{result[:100]}...'")
            except Exception as e:
                logger.error(f"Ошибка при асинхронной генерации (тест {i}): {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Тестируем генерацию через generate_chat_completion (синхронный метод)
        logger.info("Тестирование синхронной генерации через generate_chat_completion...")
        for i, prompt in enumerate(test_prompts, 1):
            logger.info(f"Тест {i}: Генерация ответа на промпт: '{prompt[:50]}...'")
            try:
                messages = [{"role": "user", "content": prompt}]
                result = g4f_handler.generate_chat_completion(messages=messages)
                
                if isinstance(result, dict) and "content" in result:
                    logger.info(f"Результат {i} (длина: {len(result['content'])}): '{result['content'][:100]}...'")
                    logger.info(f"Модель: {result.get('model')}, Провайдер: {result.get('provider')}")
                else:
                    logger.warning(f"Неожиданный формат результата: {result}")
            except Exception as e:
                logger.error(f"Ошибка при синхронной генерации (тест {i}): {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info("Тестирование интеграции завершено успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании интеграции: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Запуск тестирования интеграции G4FHandler и MistralHandler...")
    # Запускаем асинхронное тестирование
    asyncio.run(test_integration())
    logger.info("Тестирование завершено") 