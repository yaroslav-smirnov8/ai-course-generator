# app/services/content/generator.py
"""
Основной файл ContentGenerator - обеспечивает обратную совместимость
Импортирует модульную версию ContentGenerator для полной совместимости с существующим кодом
"""

# Импортируем модульный ContentGenerator
from .content_generator_core import ContentGenerator

# Экспортируем для обратной совместимости
__all__ = ['ContentGenerator']

# Для совместимости с существующими импортами
# Теперь все импорты типа:
# from app.services.content.generator import ContentGenerator
# или
# from .generator import ContentGenerator
# будут работать корректно и получат полнофункциональный модульный класс
