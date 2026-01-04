"""
Mock adapter for testing and demonstration.

This adapter returns realistic sample data without making any external API calls.
Perfect for demos, testing, and development without API keys.
"""

from typing import Dict, List, Optional, Any
from .base import BaseAIAdapter


class MockAdapter(BaseAIAdapter):
    """
    Mock implementation of the AI adapter.
    
    Returns pre-defined realistic responses for all methods.
    No external API calls are made.
    """
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Generate mock text response."""
        return f"""This is a mock response to your prompt: "{prompt[:50]}..."

The mock adapter is working correctly. In a production environment, 
this would be replaced with actual AI-generated content from your 
chosen provider (OpenAI, Anthropic, Cohere, self-hosted model, etc.).

To use a real AI provider:
1. Implement a custom adapter in backend/app/adapters/
2. Set AI_ADAPTER=your_adapter in .env
3. Configure your API credentials

Temperature: {temperature}
Max tokens: {max_tokens}
"""
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock structured response."""
        return {
            "mock": True,
            "message": "This is a mock structured response",
            "prompt_preview": prompt[:100],
            "schema_received": list(schema.keys()) if schema else [],
            "note": "Replace with real AI provider for production use"
        }
    
    async def generate_lesson_plan(
        self,
        topic: str,
        level: str,
        duration: int = 45,
        language: str = "en",
        methodology: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock lesson plan."""
        return {
            "title": f"{topic} - {level} Level",
            "duration": duration,
            "level": level,
            "language": language,
            "methodology": methodology or "Communicative Approach",
            "objectives": [
                f"Students will be able to understand the basics of {topic}",
                f"Students will practice {topic} in context",
                f"Students will demonstrate comprehension through exercises"
            ],
            "materials": [
                "Whiteboard and markers",
                "Handouts with examples",
                "Audio/visual materials (optional)",
                "Practice worksheets"
            ],
            "activities": [
                {
                    "name": "Warm-up",
                    "duration": 5,
                    "description": f"Quick review of previous lesson and introduction to {topic}",
                    "interaction": "Teacher-led discussion"
                },
                {
                    "name": "Presentation",
                    "duration": 15,
                    "description": f"Introduce {topic} with clear examples and explanations",
                    "interaction": "Teacher presents, students observe and ask questions"
                },
                {
                    "name": "Practice",
                    "duration": 15,
                    "description": f"Guided practice exercises focusing on {topic}",
                    "interaction": "Pair work and group activities"
                },
                {
                    "name": "Production",
                    "duration": 8,
                    "description": f"Students create their own examples using {topic}",
                    "interaction": "Individual and pair work"
                },
                {
                    "name": "Wrap-up",
                    "duration": 2,
                    "description": "Review key points and assign homework",
                    "interaction": "Class discussion"
                }
            ],
            "assessment": {
                "formative": "Monitor student participation and correct errors during practice",
                "summative": "Written exercise at end of lesson",
                "homework": f"Complete 10 practice exercises on {topic}"
            },
            "notes": [
                "Adjust timing based on student needs",
                "Prepare extra activities for fast finishers",
                "Consider student learning styles"
            ],
            "mock_notice": "This is sample data from MockAdapter. Connect a real AI provider for dynamic content."
        }
    
    async def generate_exercises(
        self,
        topic: str,
        level: str,
        count: int = 5,
        exercise_type: Optional[str] = None,
        language: str = "en",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate mock exercises."""
        exercises = []
        
        for i in range(min(count, 10)):  # Limit to 10 for mock
            exercises.append({
                "id": i + 1,
                "type": exercise_type or "multiple_choice",
                "question": f"Sample question {i + 1} about {topic} ({level} level)",
                "options": [
                    f"Option A for question {i + 1}",
                    f"Option B for question {i + 1}",
                    f"Option C for question {i + 1}",
                    f"Option D for question {i + 1}"
                ] if exercise_type != "fill_blank" else None,
                "correct_answer": "Option A" if exercise_type != "fill_blank" else f"answer_{i + 1}",
                "explanation": f"This is the explanation for question {i + 1}. In a real implementation, this would contain detailed reasoning.",
                "difficulty": level,
                "points": 1
            })
        
        return exercises
    
    async def generate_game(
        self,
        topic: str,
        level: str,
        game_type: str,
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock game."""
        games = {
            "quiz": {
                "title": f"{topic} Quiz Challenge",
                "type": "quiz",
                "instructions": "Answer all questions correctly to win!",
                "questions": [
                    {
                        "question": f"Sample quiz question 1 about {topic}",
                        "options": ["Answer A", "Answer B", "Answer C", "Answer D"],
                        "correct": 0,
                        "points": 10
                    },
                    {
                        "question": f"Sample quiz question 2 about {topic}",
                        "options": ["Answer A", "Answer B", "Answer C", "Answer D"],
                        "correct": 1,
                        "points": 10
                    }
                ],
                "scoring": {
                    "total_points": 20,
                    "passing_score": 15,
                    "time_limit": 300
                }
            },
            "matching": {
                "title": f"{topic} Matching Game",
                "type": "matching",
                "instructions": "Match the items in column A with column B",
                "pairs": [
                    {"left": f"Term 1 ({topic})", "right": "Definition 1"},
                    {"left": f"Term 2 ({topic})", "right": "Definition 2"},
                    {"left": f"Term 3 ({topic})", "right": "Definition 3"},
                    {"left": f"Term 4 ({topic})", "right": "Definition 4"}
                ],
                "scoring": {
                    "points_per_match": 5,
                    "total_points": 20
                }
            },
            "word_search": {
                "title": f"{topic} Word Search",
                "type": "word_search",
                "instructions": "Find all the hidden words related to the topic",
                "words": [
                    f"word1_{topic[:5]}",
                    f"word2_{topic[:5]}",
                    f"word3_{topic[:5]}",
                    f"word4_{topic[:5]}"
                ],
                "grid_size": 10,
                "scoring": {
                    "points_per_word": 5,
                    "time_bonus": True
                }
            }
        }
        
        game_data = games.get(game_type, games["quiz"])
        game_data["level"] = level
        game_data["language"] = language
        game_data["mock_notice"] = "This is sample data from MockAdapter"
        
        return game_data
    
    async def health_check(self) -> Dict[str, Any]:
        """Check mock adapter health."""
        return {
            "status": "healthy",
            "adapter": "MockAdapter",
            "details": "Mock adapter is always available (no external dependencies)",
            "features": [
                "generate_text",
                "generate_structured",
                "generate_lesson_plan",
                "generate_exercises",
                "generate_game"
            ]
        }
