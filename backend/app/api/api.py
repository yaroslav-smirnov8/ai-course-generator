"""
Основной файл API, который объединяет все маршруты.
"""

from fastapi import APIRouter

# Импортируем объединенный роутер из v1
from app.api.v1 import router as v1_router

# Создаем основной маршрутизатор API
api_router = APIRouter()

# Включаем все маршруты из v1 с префиксом /v1
api_router.include_router(v1_router, prefix="/v1")

# Дополнительные маршруты (например, для v2 или корневые) могут быть добавлены здесь
