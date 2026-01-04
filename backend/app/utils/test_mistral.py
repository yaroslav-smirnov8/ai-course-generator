"""
Тестовый скрипт для проверки работы модуля mistral_api.py
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

logger.info("Пытаемся импортировать модуль mistral_api...")
try:
    from mistral_api import MistralHandler, MistralAPIException, MistralConnectionException
    logger.info("Модуль mistral_api успешно импортирован")
except ImportError as e:
    logger.error(f"Ошибка импорта модуля mistral_api: {e}")
    logger.error("Проверьте установку библиотеки mistralai")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

async def test_mistral_api():
    """Тестирование API Mistral"""
    # Получаем API ключ из переменной окружения
    api_key = os.environ.get("MISTRAL_API_KEY")
    
    if not api_key:
        logger.error("API ключ Mistral не найден в переменных окружения")
        logger.info("Установите переменную MISTRAL_API_KEY или передайте ключ через параметр")
        return
    
    logger.info(f"API ключ получен (начинается с {api_key[:4]}...)")
    
    try:
        logger.info("Инициализация MistralHandler...")
        # Инициализируем обработчик Mistral
        mistral = MistralHandler(api_key=api_key)
        logger.info("MistralHandler успешно инициализирован")
        
        # Проверяем доступность API
        if not mistral.is_available():
            logger.error("API Mistral недоступен")
            return
        
        logger.info("API Mistral доступен, получаем список моделей...")
        
        # Получаем и выводим список доступных моделей
        models = mistral.get_available_models()
        logger.info(f"Найдено {len(models)} моделей:")
        for i, model in enumerate(models, 1):
            logger.info(f"  {i}. {model['id']} - {model['name']}")
            logger.info(f"     Макс. токенов: {model['max_tokens']}")
            logger.info(f"     Поддержка чата: {model['capabilities']['chat']}")
            logger.info(f"     Поддержка функций: {model['capabilities']['function_calling']}")
            logger.info(f"     Поддержка изображений: {model['capabilities']['vision']}")
        
        # Тестируем генерацию содержимого
        test_prompt = "Напиши короткое стихотворение о программировании на Python"
        
        # Выбираем модель для теста (используем open-mistral-nemo)
        test_model = "open-mistral-nemo"
        
        # Асинхронная генерация
        logger.info(f"Тестирование асинхронной генерации с моделью {test_model}...")
        try:
            async_result = await mistral.generate_content(
                prompt=test_prompt,
                model=test_model,
                temperature=0.7,
                max_tokens=200
            )
            logger.info(f"Результат асинхронной генерации:\n{async_result}")
        except Exception as e:
            logger.error(f"Ошибка при асинхронной генерации: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Синхронная генерация
        logger.info(f"Тестирование синхронной генерации с моделью {test_model}...")
        try:
            sync_result = mistral.generate_content_sync(
                prompt=test_prompt,
                model=test_model,
                temperature=0.7,
                max_tokens=200
            )
            logger.info(f"Результат синхронной генерации:\n{sync_result}")
        except Exception as e:
            logger.error(f"Ошибка при синхронной генерации: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("Тестирование завершено успешно")
        
    except MistralConnectionException as e:
        logger.error(f"Ошибка подключения к Mistral API: {e}")
        import traceback
        logger.error(traceback.format_exc())
    except MistralAPIException as e:
        logger.error(f"Ошибка Mistral API: {e}")
        import traceback
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Непредвиденная ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Запуск тестирования Mistral API...")
    # Запускаем асинхронное тестирование
    asyncio.run(test_mistral_api())
    logger.info("Тестирование завершено") 