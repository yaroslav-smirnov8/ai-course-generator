"""
API-эндпоинты для работы с курсами, включая генерацию и обработку курсов.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body, Query, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.services.content.generator import ContentGenerator
from app.api.adapters.course_response_adapter import process_course_content
from app.config import get_settings

# Инициализация логирования
logger = logging.getLogger(__name__)

# Инициализация маршрутизатора
router = APIRouter(prefix="/api/courses", tags=["courses"])


class CourseGenerationRequest(BaseModel):
    """Модель для запроса на генерацию курса"""
    language: str = Field(..., description="Язык курса (например, 'french', 'spanish')")
    level: str = Field(..., description="Уровень курса (например, 'beginner', 'intermediate')")
    topic: Optional[str] = Field(None, description="Тема курса (необязательно)")
    lessons_count: int = Field(3, description="Количество уроков в курсе")
    model: str = Field("gemini-1.5-pro", description="Модель для генерации (по умолчанию 'gemini-1.5-pro')")
    debug: bool = Field(False, description="Режим отладки (только для логирования)")


class CourseValidationRequest(BaseModel):
    """Модель для запроса на валидацию курса"""
    content: str = Field(..., description="Сырое содержимое ответа API")
    debug: bool = Field(False, description="Режим отладки (только для логирования)")


@router.post("/generate")
async def generate_course(request: CourseGenerationRequest):
    """
    Генерирует новый курс с использованием языковой модели.
    Возвращает готовую структуру курса.
    """
    try:
        logger.info(f"Запрос на генерацию курса: {request.language}, {request.level}, {request.topic}")
        
        # Инициализируем генератор контента
        generator = ContentGenerator()
        
        # Генерируем запрос для языковой модели
        prompt = generator.create_course_prompt(
            language=request.language,
            level=request.level,
            topic=request.topic,
            lessons_count=request.lessons_count
        )
        
        # Отправляем запрос к API и получаем ответ
        raw_response = await generator.generate_course_content(
            prompt=prompt,
            model=request.model
        )
        
        # Обрабатываем ответ и получаем готовую структуру курса
        course_data = process_course_content(raw_response, debug=request.debug)
        
        # Возвращаем готовую структуру без метаданных
        return course_data
        
    except Exception as e:
        logger.error(f"Ошибка при генерации курса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации курса: {str(e)}")


@router.post("/process")
async def process_course_content_endpoint(request: CourseValidationRequest):
    """
    Обрабатывает сырое содержимое ответа API и возвращает готовую структуру курса.
    Используется для тестирования обработки различных форматов данных.
    """
    try:
        logger.info(f"Запрос на обработку контента курса длиной {len(request.content)} символов")
        
        # Обрабатываем контент и получаем готовую структуру курса
        course_data = process_course_content(request.content, debug=request.debug)
        
        # Возвращаем только данные курса
        return course_data
        
    except Exception as e:
        logger.error(f"Ошибка при обработке курса: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке курса: {str(e)}")


@router.get("/examples")
async def get_course_examples():
    """
    Возвращает примеры структур курсов для тестирования.
    """
    examples = {
        "french_beginner": {
            "name": "Французский для начинающих",
            "description": "Базовый курс французского языка",
            "lessons": [
                {
                    "title": "Знакомство и приветствия",
                    "objectives": ["Научиться представляться", "Освоить базовые приветствия"],
                    "grammar": ["Личные местоимения", "Глагол être (быть)"],
                    "vocabulary": ["Bonjour - Здравствуйте", "Au revoir - До свидания"]
                },
                {
                    "title": "Еда и напитки",
                    "objectives": ["Научиться заказывать еду и напитки", "Выучить названия блюд и напитков"],
                    "grammar": ["Определенные и неопределенные артикли", "Глагол avoir (иметь)"],
                    "vocabulary": ["Le café - кофе", "Le thé - чай", "L'eau - вода"]
                }
            ]
        },
        "spanish_travel": {
            "name": "Испанский для путешествий",
            "description": "Практический курс испанского языка для туристов",
            "lessons": [
                {
                    "title": "В аэропорту",
                    "objectives": ["Понимать объявления в аэропорту", "Задавать вопросы о рейсах"],
                    "grammar": ["Вопросительные слова", "Настоящее время глаголов"],
                    "vocabulary": ["El vuelo - рейс", "La salida - выход", "El pasaporte - паспорт"]
                }
            ]
        }
    }
    
    return examples 