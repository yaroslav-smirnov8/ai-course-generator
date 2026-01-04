import os
from typing import Dict, Any
from log import logger

class CourseGenerator:
    async def generate_course_structure(self, title: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Генерирует структуру курса на основе заголовка и опций
        """
        options = options or {}
        
        try:
            # Получаем промпт для генерации структуры курса
            prompt = self._get_course_structure_prompt(title, options)
            
            # Логируем длину и первые/последние части промпта для анализа
            logger.info(f"Длина промпта для структуры курса: {len(prompt)} символов")
            logger.info(f"Начало промпта: {prompt[:200]}...")
            logger.info(f"Конец промпта: ...{prompt[-200:]}")
            
            # Если включен режим отладки, выводим полный промпт
            if os.getenv("DEBUG", "false").lower() == "true":
                logger.debug(f"Полный промпт для структуры курса:\n{prompt}")
            
            # Генерируем структуру курса с помощью генеративной модели
            response = await self.generator.generate_content(
                prompt=prompt, 
                content_type="course_structure",
                max_tokens=2048
            )
            
            # ... existing code ...
        except Exception as e:
            logger.error(f"Ошибка при генерации структуры курса: {e}")
            raise

        return response 