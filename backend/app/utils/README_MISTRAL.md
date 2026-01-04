# Модуль для работы с Mistral AI API

Этот модуль предоставляет простой интерфейс для взаимодействия с Mistral AI API, используя официальную клиентскую библиотеку.

## Установка

Для работы с модулем необходимо установить зависимости:

```bash
pip install mistralai python-dotenv httpx
```

## Настройка

1. Создайте файл `.env` в корневой директории проекта и добавьте в него ваш API ключ Mistral:

```
MISTRAL_API_KEY=your-api-key-here
MISTRAL_API_BASE=https://api.mistral.ai  # опционально, если нужно изменить базовый URL
```

2. Импортируйте и используйте модуль в своем коде.

## Использование

### Самостоятельное использование MistralHandler

```python
from mistral_api import MistralHandler

# Инициализация
mistral = MistralHandler(api_key="your-api-key-here")  # или не указывайте, если он задан в .env

# Проверка доступности
if mistral.is_available():
    # Получение списка доступных моделей
    models = mistral.get_available_models()
    print(f"Доступно {len(models)} моделей")
    
    # Асинхронная генерация текста
    async def generate():
        result = await mistral.generate_content(
            prompt="Напиши стихотворение о программировании",
            model="open-mistral-nemo",  # можно указать конкретную модель
            temperature=0.7,
            max_tokens=2048
        )
        print(result)
    
    # Синхронная генерация текста
    result = mistral.generate_content_sync(
        prompt="Напиши стихотворение о программировании",
        model="open-mistral-nemo",
        temperature=0.7,
        max_tokens=2048
    )
    print(result)
```

### Использование в G4FHandler

Модуль `mistral_api.py` интегрирован с `G4FHandler` и используется как основной метод для генерации контента:

```python
from g4f_handler import G4FHandler

# Инициализация
handler = G4FHandler(api_key="your-api-key-here")  # или не указывайте, если он задан в .env

# Асинхронная генерация через G4FHandler (использует MistralHandler)
async def generate():
    result = await handler.generate_content(
        prompt="Напиши стихотворение о программировании"
    )
    print(result)

# Синхронная генерация через G4FHandler (использует MistralHandler)
messages = [{"role": "user", "content": "Напиши стихотворение о программировании"}]
result = handler.generate_chat_completion(messages=messages)
print(result["content"])
```

## Тестирование

1. Для тестирования автономной работы модуля Mistral API:

```bash
python test_mistral.py
```

2. Для тестирования интеграции с G4FHandler:

```bash
python test_integration.py
```

## Обработка ошибок

Модуль включает специальные исключения для обработки различных ошибок:

- `MistralAPIException` - базовое исключение для всех ошибок API
- `MistralConnectionException` - ошибки подключения к API
- `MistralRateLimitException` - превышение лимита запросов
- `MistralAuthException` - ошибки авторизации

Пример обработки ошибок:

```python
from mistral_api import MistralHandler, MistralAPIException, MistralConnectionException

try:
    mistral = MistralHandler(api_key="your-api-key-here")
    result = mistral.generate_content_sync(prompt="Ваш запрос")
except MistralConnectionException as e:
    print(f"Ошибка подключения: {e}")
except MistralAPIException as e:
    print(f"Ошибка API: {e}")
```

## Примечания

- При инициализации G4FHandler с корректным API ключом Mistral AI, автоматически будет использоваться Mistral API вместо G4F
- Если Mistral API недоступен или вернул ошибку, G4FHandler попытается использовать другие провайдеры
- Для работы с большими контекстами рекомендуется использовать модели с большим значением `max_tokens` 