# app/services/content/content_generator_game.py
"""
Модуль для генерации игр и интерактивных упражнений
"""
import logging
from typing import Optional, Dict, Any, List

from ...core.memory import memory_optimized
from ...core.constants import ContentType
from ...core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ContentGeneratorGame:
    """
    Миксин для генерации игр и интерактивных упражнений
    """
    
    @memory_optimized()
    async def generate_game(
            self,
            user_id: int,
            game_type: str = "vocabulary",
            game_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate educational game with optimization"""
        try:
            # Prepare context for generation
            context = game_data or {}
            context['game_type'] = game_type

            # Create prompt
            prompt = self._create_game_prompt(context)

            # Generate content
            content = await self.generate_content(
                content_type=ContentType.GAME,
                prompt=prompt,
                user_id=user_id,
                extra_params=context
            )

            # Structure result
            game = self._structure_game(content)

            return game

        except Exception as e:
            logger.error(f"Error generating game: {str(e)}")
            raise

    def _validate_game_params(self, params: Dict[str, Any]) -> None:
        """Validate parameters for game generation"""
        required_params = ['language', 'topic', 'game_type', 'duration']
        for param in required_params:
            if param not in params:
                raise ValidationError(f"Missing required parameter: {param}")

        if not 5 <= params.get('duration', 0) <= 60:
            raise ValidationError("Duration must be between 5 and 60 minutes")

        # Проверяем формат игры, если он указан
        if 'format' in params and params['format'] not in ['individual', 'group']:
            raise ValidationError("Format must be either 'individual' or 'group'")

        # Проверяем тип контента, если он отсутствует, добавляем его
        if 'type' not in params:
            params['type'] = ContentType.GAME

    def _create_game_prompt(self, context: Dict[str, Any]) -> str:
        """Create prompt for game generation with multilingual approach"""

        # Получаем язык обучения
        target_language = context.get('language', 'English')

        # Определяем формат игры (индивидуальный или групповой)
        format_instruction = ""
        if context.get('format') == 'individual':
            format_instruction = "This game should be designed for individual play (one student with teacher)."
        elif context.get('format') == 'group':
            format_instruction = "This game should be designed for group play (multiple students)."

        prompt_template = f"""
        IMPORTANT: Create a game for teaching {target_language} language to students.

        CRITICAL LANGUAGE REQUIREMENTS:
        - ALL TEACHER INSTRUCTIONS should be written in ENGLISH
        - ALL GAME MATERIALS AND STUDENT ACTIVITIES should be in {target_language.upper()} language
        - Game rules and explanations - in English for the teacher
        - Cards, questions, tasks - in {target_language.upper()} for students

        Game parameters:
        - Game type: {{game_type}}
        - Topic: {{topic}}
        - Duration: {{duration}} minutes
        - Age group: {{age_group}}
        {{format_instruction}}

        Include the following sections:
        1. Game title (in English)
        2. Required materials (description in English)
        3. Setup instructions (in English for teacher)
        4. Game rules (in English for teacher)
        5. Scoring system (in English)
        6. Game variations (optional, in English)

        Game materials (cards, questions, tasks) should be in {target_language.upper()} language.
        Make the game engaging, interactive, and suitable for language learning.
        """

        return prompt_template.format(
            game_type=context.get('game_type', 'языковая'),
            topic=context.get('topic', 'Общая тема'),
            duration=context.get('duration', 15),
            age_group=context.get('age_group', 'взрослые'),
            format_instruction=format_instruction
        )

    def _structure_game(self, content: str, game_type: str = None) -> Dict[str, Any]:
        """Structure the raw generated content into a game format"""
        game = {
            "title": "",
            "materials": [],
            "setup": "",
            "rules": "",
            "scoring": "",
            "variations": []
        }

        # Basic parsing
        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()
            if game["title"] == "" and current_section is None:
                game["title"] = line
                continue
            elif "materials" in lower_line or "requirements" in lower_line:
                current_section = "materials"
                continue
            elif "setup" in lower_line or "preparation" in lower_line:
                current_section = "setup"
                continue
            elif "rules" in lower_line or "how to play" in lower_line:
                current_section = "rules"
                continue
            elif "scoring" in lower_line or "points" in lower_line:
                current_section = "scoring"
                continue
            elif "variations" in lower_line or "alternatives" in lower_line:
                current_section = "variations"
                continue

            if current_section == "materials" and line.startswith("- "):
                game["materials"].append(line[2:])
            elif current_section == "setup":
                game["setup"] += line + "\n"
            elif current_section == "rules":
                game["rules"] += line + "\n"
            elif current_section == "scoring":
                game["scoring"] += line + "\n"
            elif current_section == "variations" and line.startswith("- "):
                game["variations"].append(line[2:])

        return game

    def _add_game_section(self, game: Dict[str, Any], section: str, content: str):
        """Add section content to game structure"""
        if 'title' in section or 'название' in section:
            game['title'] = content
        elif 'description' in section or 'описание' in section:
            game['description'] = content
        elif 'instruction' in section or 'инструкц' in section:
            game['instructions'] = content
        elif 'scoring' in section or 'очки' in section or 'баллы' in section:
            game['scoring'] = content
        elif 'feature' in section or 'особенност' in section:
            game['features'] = [item.strip() for item in content.split('\n') if item.strip()]
        elif 'content' in section or 'содержание' in section:
            # Дополнительный контент игры
            if 'game_content' not in game:
                game['game_content'] = []
            game['game_content'].append({
                'section': section,
                'content': content
            })

    @memory_optimized()
    async def regenerate_text(
        self,
        original_text: str,
        regeneration_type: str = "paraphrase",
        language: str = "en",
        **kwargs
    ) -> str:
        """
        Перегенерирует текст с различными модификациями

        Args:
            original_text (str): Исходный текст
            regeneration_type (str): Тип регенерации (paraphrase, expand, simplify, formalize)
            language (str): Язык текста
            **kwargs: Дополнительные параметры

        Returns:
            str: Перегенерированный текст
        """
        try:
            user_id = kwargs.get('user_id', 1)
            logger.info(f"Regenerating text with type: {regeneration_type}, language: {language}")

            # Создаем промпт для регенерации
            prompt = self._create_regeneration_prompt(original_text, regeneration_type, language)

            # Генерируем контент
            content = await self.generate_content(
                content_type=ContentType.TEXT_ANALYSIS,
                prompt=prompt,
                user_id=user_id,
                extra_params={
                    "regeneration_type": regeneration_type,
                    "language": language,
                    "original_length": len(original_text)
                }
            )

            return content

        except Exception as e:
            logger.error(f"Error regenerating text: {str(e)}")
            raise

    def _create_regeneration_prompt(self, text: str, regeneration_type: str, language: str) -> str:
        """Создает промпт для регенерации текста"""
        
        type_instructions = {
            "paraphrase": "Rewrite the text using different words and sentence structures while maintaining the same meaning",
            "expand": "Expand the text by adding more details, examples, and explanations",
            "simplify": "Simplify the text using easier vocabulary and shorter sentences",
            "formalize": "Make the text more formal and academic in tone",
            "informalize": "Make the text more casual and conversational",
            "summarize": "Create a shorter version that captures the main points"
        }
        
        instruction = type_instructions.get(regeneration_type, type_instructions["paraphrase"])
        
        prompt = f"""
{instruction} in {language} language.

Original text:
{text}

Regenerated text ({regeneration_type}):
"""
        
        return prompt
