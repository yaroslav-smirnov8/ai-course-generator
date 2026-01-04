"""
API эндпоинты для мониторинга и управления API Gateway
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.security import get_current_user
from ....models import User

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def get_api_gateway_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить статус здоровья всех провайдеров API Gateway
    """
    try:
        # Импортируем здесь, чтобы избежать проблем с инициализацией
        from ....services.api_gateway import APIGateway

        gateway = APIGateway()
        health_status = await gateway.get_provider_health_status()
        return {
            "status": "success",
            "data": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса здоровья: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_api_gateway_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить статистику API Gateway
    """
    try:
        from ....services.api_gateway import APIGateway

        gateway = APIGateway()
        stats = gateway.get_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@router.get("/providers", response_model=Dict[str, Any])
async def get_providers_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить информацию о всех провайдерах
    """
    try:
        from ....services.api_gateway import APIGateway

        gateway = APIGateway()
        health_status = await gateway.get_provider_health_status()
        stats = gateway.get_stats()

        # Объединяем информацию о провайдерах
        providers_info = {}

        # Текстовые провайдеры
        for provider_name, health_info in health_status.get('text_providers', {}).items():
            provider_stats = stats.get('provider_stats', {}).get(provider_name, {})
            providers_info[provider_name] = {
                "type": "text",
                "healthy": health_info.get('healthy', False),
                "available_models": health_info.get('available_models', 0),
                "total_models": health_info.get('total_models', 0),
                "error": health_info.get('error'),
                "stats": provider_stats
            }

        # Провайдеры изображений
        for provider_name, health_info in health_status.get('image_providers', {}).items():
            provider_stats = stats.get('provider_stats', {}).get(provider_name, {})
            providers_info[provider_name] = {
                "type": "image",
                "healthy": health_info.get('healthy', False),
                "available_models": health_info.get('available_models', 0),
                "total_models": health_info.get('total_models', 0),
                "error": health_info.get('error'),
                "stats": provider_stats
            }

        return {
            "status": "success",
            "data": {
                "providers": providers_info,
                "overall_health": health_status.get('overall_health', False),
                "text_providers_count": stats.get('text_providers_count', 0),
                "image_providers_count": stats.get('image_providers_count', 0)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о провайдерах: {str(e)}")


@router.post("/test", response_model=Dict[str, Any])
async def test_api_gateway(
    prompt: str = Query(..., description="Промпт для тестирования"),
    content_type: str = Query("text", description="Тип контента (text/image)"),
    preferred_provider: Optional[str] = Query(None, description="Предпочтительный провайдер"),
    preferred_model: Optional[str] = Query(None, description="Предпочтительная модель"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Тестирование генерации контента через API Gateway
    """
    try:
        # Маппинг типов контента
        from ....core.constants import ContentType
        
        content_type_mapping = {
            "text": ContentType.TEXT,
            "image": ContentType.IMAGE,
            "lesson": ContentType.LESSON_PLAN,
            "exercise": ContentType.EXERCISE,
            "game": ContentType.GAME
        }
        
        mapped_content_type = content_type_mapping.get(content_type.lower(), ContentType.TEXT)
        
        # Импортируем здесь для избежания проблем с инициализацией
        from ....services.api_gateway import APIGateway
        from ....services.api_gateway.models import ContentType as GatewayContentType

        # Маппинг типов контента для API Gateway
        gateway_content_mapping = {
            "text": GatewayContentType.TEXT,
            "image": GatewayContentType.IMAGE,
            "lesson": GatewayContentType.TEXT,
            "exercise": GatewayContentType.TEXT,
            "game": GatewayContentType.TEXT
        }

        gateway_content_type = gateway_content_mapping.get(content_type.lower(), GatewayContentType.TEXT)

        # Получаем эндпоинт
        endpoint_mapping = {
            "lesson": "lesson-plan",
            "exercise": "exercises",
            "game": "games",
            "image": "flux-images",
            "text": "assistant"
        }
        endpoint = endpoint_mapping.get(content_type.lower(), "assistant")

        # Подготавливаем данные
        request_data = {
            "prompt": prompt,
            "temperature": 0.7,
            "maxTokens": 1000
        }

        # Получаем API ключи из переменных окружения
        import os
        api_keys = {
            'gemini': os.getenv('GEMINI_API_KEY', ''),
            'groq': os.getenv('GROQ_API_KEY', ''),
            'openrouter': os.getenv('OPENROUTER_API_KEY', ''),
            'together': os.getenv('TOGETHER_API_KEY', '')
        }
        api_keys = {k: v for k, v in api_keys.items() if v}

        if not api_keys:
            raise HTTPException(status_code=500, detail="API ключи не настроены")

        # Тестируем генерацию
        gateway = APIGateway()
        response = await gateway.generate_content(
            endpoint=endpoint,
            data=request_data,
            api_keys=api_keys,
            content_type=gateway_content_type,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model
        )

        if response.success:
            result = response.image_url if gateway_content_type == GatewayContentType.IMAGE else response.content
        else:
            result = f"Ошибка: {response.error}"
            
            return {
                "status": "success",
                "data": {
                    "prompt": prompt,
                    "content_type": content_type,
                    "preferred_provider": preferred_provider,
                    "preferred_model": preferred_model,
                    "result": result,
                    "result_length": len(result) if isinstance(result, str) else 0
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка тестирования: {str(e)}")


@router.get("/metrics", response_model=Dict[str, Any])
async def get_detailed_metrics(
    provider_name: Optional[str] = Query(None, description="Имя провайдера для детальной статистики"),
    hours: int = Query(24, description="Количество часов для анализа трендов"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить детальные метрики API Gateway
    """
    try:
        from ....services.api_gateway import APIGateway

        # Создаем прямое подключение к API Gateway для получения метрик
        api_gateway = APIGateway()

        # Получаем базовую статистику
        stats = api_gateway.get_stats()

        # Получаем статус здоровья
        health_status = await api_gateway.get_provider_health_status()
        
        result = {
            "general_stats": stats,
            "health_status": health_status,
            "timestamp": "2024-01-01T00:00:00Z"  # Заглушка, в реальности используйте datetime.utcnow()
        }
        
        # Если запрошена статистика конкретного провайдера
        if provider_name:
            # Здесь можно добавить детальную статистику конкретного провайдера
            # Пока возвращаем базовую информацию
            provider_stats = stats.get('provider_stats', {}).get(provider_name)
            if provider_stats:
                result['provider_details'] = {
                    "name": provider_name,
                    "stats": provider_stats
                }
            else:
                result['provider_details'] = {
                    "error": f"Провайдер {provider_name} не найден"
                }
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_api_gateway(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up API Gateway resources
    """
    try:
        from ....services.api_gateway import APIGateway

        gateway = APIGateway()
        await gateway.cleanup()

        return {
            "status": "success",
            "message": "API Gateway resources cleaned up successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки ресурсов: {str(e)}")


@router.get("/config", response_model=Dict[str, Any])
async def get_api_gateway_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить конфигурацию API Gateway
    """
    try:
        # Возвращаем общую информацию о конфигурации
        # (без чувствительных данных типа API ключей)
        
        config_info = {
            "text_providers": [
                {
                    "name": "direct",
                    "type": "direct",
                    "priority": 1,
                    "description": "Direct calls to AI services"
                }
            ],
            "image_providers": [
                {
                    "name": "netlify",
                    "type": "netlify",
                    "priority": 1,
                    "description": "Image generation via Netlify Functions"
                }
            ],
            "supported_content_types": ["text", "image"],
            "fallback_enabled": True,
            "model_cooldown_enabled": True
        }
        
        return {
            "status": "success",
            "data": config_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения конфигурации: {str(e)}")
