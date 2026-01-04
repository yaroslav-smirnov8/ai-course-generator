"""
Конфигурация провайдеров и моделей для API Gateway
"""

import os
from typing import Dict, List
from .models import ProviderConfig, ModelConfig, ProviderType, ContentType


def create_gemini_models() -> List[ModelConfig]:
    """Создать конфигурации для Gemini моделей"""
    return [
        ModelConfig(
            name="gemini-2.0-flash",
            provider_type="gemini",
            api_url="https://generativelanguage.googleapis.com/v1beta/models",
            max_tokens=15000,  # Как в боте для планов уроков
            temperature=0.8,   # Увеличено для большей креативности
            timeout=60,
            retry_count=2,
            priority=0,  # Высший приоритет
            request_format={
                "generationConfig": {
                    "maxOutputTokens": 15000,  # Как в боте для планов уроков
                    "temperature": 0.8,        # Увеличено для большей креативности
                    "topP": 0.95,
                    "topK": 64,
                }
            }
        ),
        ModelConfig(
            name="gemini-1.5-pro",
            provider_type="gemini",
            api_url="https://generativelanguage.googleapis.com/v1beta/models",
            max_tokens=3500,  # Синхронизировано с ботом
            temperature=0.8,  # Увеличено для большей креативности
            timeout=90,
            retry_count=2,
            priority=1,
            request_format={
                "generationConfig": {
                    "maxOutputTokens": 3500,  # Синхронизировано с ботом
                    "temperature": 0.8,       # Увеличено для большей креативности
                    "topP": 0.95,
                    "topK": 64,
                }
            }
        )
    ]


def create_groq_models() -> List[ModelConfig]:
    """Создать конфигурации для Groq моделей"""
    return [
        ModelConfig(
            name="llama-3.3-70b-versatile",
            provider_type="groq",
            api_url="https://api.groq.com/openai/v1/chat/completions",
            max_tokens=15000,  # Как в боте для планов уроков
            temperature=0.8,   # Увеличено для большей креативности
            timeout=45,
            retry_count=2,
            priority=0,
            request_format={
                "temperature": 0.8,     # Увеличено для большей креативности
                "max_tokens": 15000,    # Как в боте для планов уроков
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="llama-3.1-70b-versatile",
            provider_type="groq",
            api_url="https://api.groq.com/openai/v1/chat/completions",
            max_tokens=3500,  # Синхронизировано с ботом
            temperature=0.8,  # Увеличено для большей креативности
            timeout=45,
            retry_count=2,
            priority=1,
            request_format={
                "temperature": 0.8,    # Увеличено для большей креативности
                "max_tokens": 3500,    # Синхронизировано с ботом
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="mixtral-8x7b-32768",
            provider_type="groq",
            api_url="https://api.groq.com/openai/v1/chat/completions",
            max_tokens=32768,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=2,
            request_format={
                "temperature": 0.7,
                "max_tokens": 32768,
                "top_p": 0.95,
            }
        )
    ]


def create_openrouter_models() -> List[ModelConfig]:
    """Создать конфигурации для OpenRouter моделей"""
    return [
        ModelConfig(
            name="google/gemini-2.0-flash-exp",
            provider_type="openrouter",
            api_url="https://openrouter.ai/api/v1/chat/completions",
            max_tokens=8192,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=0,
            request_format={
                "temperature": 0.7,
                "max_tokens": 8192,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="anthropic/claude-3.5-sonnet",
            provider_type="openrouter",
            api_url="https://openrouter.ai/api/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=1,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="openai/gpt-4o",
            provider_type="openrouter",
            api_url="https://openrouter.ai/api/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=2,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="meta-llama/llama-3.3-70b-instruct",
            provider_type="openrouter",
            api_url="https://openrouter.ai/api/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=3,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        )
    ]


def create_llm7_models() -> List[ModelConfig]:
    """Создать конфигурации для LLM7 моделей"""
    return [
        ModelConfig(
            name="gpt-4.1-2025-04-14",
            provider_type="llm7",
            api_url="https://api.llm7.io/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=0,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="gpt-4.1-mini-2025-04-14",
            provider_type="llm7",
            api_url="https://api.llm7.io/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=45,
            retry_count=2,
            priority=1,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="llama-4-scout-17b-16e-instruct",
            provider_type="llm7",
            api_url="https://api.llm7.io/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=45,
            retry_count=2,
            priority=2,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="phi-4-multilmodal-instruct",
            provider_type="llm7",
            api_url="https://api.llm7.io/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=45,
            retry_count=2,
            priority=3,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        )
    ]


def create_together_models() -> List[ModelConfig]:
    """Создать конфигурации для Together AI моделей"""
    return [
        ModelConfig(
            name="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            provider_type="together",
            api_url="https://api.together.xyz/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=0,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="meta-llama/Llama-3.1-70B-Instruct-Turbo",
            provider_type="together",
            api_url="https://api.together.xyz/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=1,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="Qwen/Qwen2.5-72B-Instruct-Turbo",
            provider_type="together",
            api_url="https://api.together.xyz/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=60,
            retry_count=2,
            priority=2,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        )
    ]


def create_cerebras_models() -> List[ModelConfig]:
    """Создать конфигурации для Cerebras моделей"""
    return [
        ModelConfig(
            name="llama3.1-70b",
            provider_type="cerebras",
            api_url="https://api.cerebras.ai/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=45,
            retry_count=2,
            priority=0,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        ),
        ModelConfig(
            name="llama3.1-8b",
            provider_type="cerebras",
            api_url="https://api.cerebras.ai/v1/chat/completions",
            max_tokens=4096,
            temperature=0.7,
            timeout=30,
            retry_count=2,
            priority=1,
            request_format={
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            }
        )
    ]


# Provider configurations for text generation
TEXT_GENERATION_PROVIDERS = [
    # Priority 1: Direct Workers calls
    ProviderConfig(
        name="direct",
        type=ProviderType.DIRECT,
        priority=0,
        timeout=120,
        retry_count=1,
        models=create_gemini_models() + create_groq_models() + create_openrouter_models() + create_llm7_models(),
        endpoints={
            "lesson-plan": "https://lesson-plan.syysyy33.workers.dev/generateContent",
            "course-lesson-plan": "https://course-lesson-plan.syysyy33.workers.dev/generateContent",
            "course-exercises": "https://course-exercises.syysyy33.workers.dev/generateContent",
            "course-games": "https://course-games.syysyy33.workers.dev/generateContent",
            "exercises": "https://exercises.syysyy33.workers.dev/generateContent",
            "games": "https://games.syysyy33.workers.dev/generateContent",
            "assistant": "https://assistant.syysyy33.workers.dev/generateContent",
            "text-analyzer": "https://text-analyzer.syysyy33.workers.dev/generateContent",
            "concept-explainer": "https://concept-explainer.syysyy33.workers.dev/generateContent",
            "course-generator": "https://course-generator.syysyy33.workers.dev/generateContent"
        }
    )
]

# Конфигурации провайдеров для генерации изображений (ТОЛЬКО Netlify)
IMAGE_GENERATION_PROVIDERS = [
    ProviderConfig(
        name="netlify",
        type=ProviderType.NETLIFY,
        priority=0,
        base_url=os.getenv("NETLIFY_FLUX_IMAGES_URL", "https://aiteachers.netlify.app").replace("/.netlify/functions/flux-images", ""),
        timeout=150,
        retry_count=2,
        models=[
            ModelConfig(
                name="flux-schnell",
                provider_type="together",
                api_url="https://api.together.xyz/v1/images/generations",
                max_tokens=0,  # Не применимо для изображений
                timeout=150,
                retry_count=2,
                priority=0,
                request_format={
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "width": 1024,
                    "height": 1024,
                    "steps": 4,
                    "n": 1
                }
            )
        ],
        endpoints={
            "flux-images": ".netlify/functions/flux-images"
        },
        extra_config={
            "translation_required": True,
            "translation_provider": "llm7"
        }
    )
]

# Приоритеты провайдеров AI внутри воркеров (как в существующих воркерах)
WORKER_AI_PROVIDER_PRIORITY = [
    "gemini",      # Основной провайдер
    "groq",        # Первый fallback
    "openrouter",  # Второй fallback с ротацией моделей
    "llm7",        # Третий fallback с ротацией моделей
    "together",    # Четвертый fallback
    "cerebras"     # Пятый fallback
]

# Общие приоритеты провайдеров
PROVIDER_PRIORITIES = {
    ContentType.TEXT: TEXT_GENERATION_PROVIDERS,
    ContentType.IMAGE: IMAGE_GENERATION_PROVIDERS
}


def get_provider_config(content_type: ContentType) -> List[ProviderConfig]:
    """Получить конфигурацию провайдеров для типа контента"""
    return PROVIDER_PRIORITIES.get(content_type, [])


def get_provider_by_name(name: str, content_type: ContentType) -> ProviderConfig:
    """Получить провайдер по имени"""
    providers = get_provider_config(content_type)
    for provider in providers:
        if provider.name == name:
            return provider
    raise ValueError(f"Провайдер {name} не найден для типа контента {content_type}")


def get_model_by_name(provider_name: str, model_name: str, content_type: ContentType) -> ModelConfig:
    """Получить модель по имени провайдера и модели"""
    provider = get_provider_by_name(provider_name, content_type)
    for model in provider.models:
        if model.name == model_name:
            return model
    raise ValueError(f"Модель {model_name} не найдена в провайдере {provider_name}")


def update_model_cooldown(provider_name: str, model_name: str, content_type: ContentType, minutes: int = 5):
    """Установить cooldown для модели"""
    from datetime import datetime, timedelta
    from .models import ModelStatus

    try:
        model = get_model_by_name(provider_name, model_name, content_type)
        model.status = ModelStatus.COOLDOWN
        model.cooldown_until = datetime.utcnow() + timedelta(minutes=minutes)
        model.error_count += 1
    except ValueError:
        pass  # Модель не найдена, игнорируем


def mark_model_success(provider_name: str, model_name: str, content_type: ContentType):
    """Отметить успешное использование модели"""
    from datetime import datetime
    from .models import ModelStatus

    try:
        model = get_model_by_name(provider_name, model_name, content_type)
        model.status = ModelStatus.AVAILABLE
        model.cooldown_until = None
        model.last_success = datetime.utcnow()
        model.error_count = 0
    except ValueError:
        pass  # Модель не найдена, игнорируем
