"""
Файл конфигурации приложения.
Содержит классы и функции для доступа к настройкам из переменных окружения.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Настройки приложения, загружаемые из переменных окружения.
    
    Attributes:
        APP_ENV: Окружение приложения (development, testing, production)
        API_KEY_GEMINI: Ключ API для Gemini
        API_KEY_OPENAI: Ключ API для OpenAI
        API_TIMEOUT: Таймаут для API-запросов (в секундах)
        DEBUG: Флаг отладки
        LOG_LEVEL: Уровень логирования
    """
    APP_ENV: str = "development"
    API_KEY_GEMINI: str = ""
    API_KEY_OPENAI: str = ""
    API_TIMEOUT: int = 60
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Игнорировать дополнительные поля из .env


@lru_cache()
def get_settings() -> Settings:
    """
    Получает настройки приложения с кэшированием результата.
    
    Returns:
        Settings: Объект настроек приложения
    """
    return Settings()


def get_env_variable(name: str, default: str = "") -> str:
    """
    Получает переменную окружения по имени с возможностью указания значения по умолчанию.
    
    Args:
        name: Имя переменной окружения
        default: Значение по умолчанию, если переменная не найдена
        
    Returns:
        str: Значение переменной окружения или значение по умолчанию
    """
    return os.environ.get(name, default) 