"""
Base adapter interface for AI providers.

This module defines the abstract interface that all AI provider adapters must implement.
It provides a consistent API for generating educational content regardless of the underlying AI service.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseAIAdapter(ABC):
    """
    Abstract base class for AI provider adapters.
    
    All concrete adapters must implement these methods to ensure
    consistent behavior across different AI providers.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the adapter with configuration.
        
        Args:
            config: Dictionary containing adapter-specific configuration
                   (API keys, endpoints, model names, etc.)
        """
        self.config = config or {}
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate plain text response from a prompt.
        
        Args:
            prompt: The input prompt for text generation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text as a string
            
        Raises:
            AdapterError: If generation fails
        """
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response matching a schema.
        
        Args:
            prompt: The input prompt for generation
            schema: JSON schema that the response should match
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary matching the provided schema
            
        Raises:
            AdapterError: If generation fails or response doesn't match schema
        """
        pass
    
    @abstractmethod
    async def generate_lesson_plan(
        self,
        topic: str,
        level: str,
        duration: int = 45,
        language: str = "en",
        methodology: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a structured lesson plan.
        
        Args:
            topic: The subject/topic of the lesson
            level: Student level (e.g., "A1", "B2", "beginner", "advanced")
            duration: Lesson duration in minutes
            language: Language for the lesson plan
            methodology: Teaching methodology (e.g., "CELTA", "Montessori")
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing:
                - title: Lesson title
                - objectives: Learning objectives
                - materials: Required materials
                - activities: List of activities with timing
                - assessment: Assessment methods
                - notes: Additional notes
                
        Raises:
            AdapterError: If generation fails
        """
        pass
    
    @abstractmethod
    async def generate_exercises(
        self,
        topic: str,
        level: str,
        count: int = 5,
        exercise_type: Optional[str] = None,
        language: str = "en",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate practice exercises.
        
        Args:
            topic: The subject/topic for exercises
            level: Difficulty level
            count: Number of exercises to generate
            exercise_type: Type of exercise (e.g., "multiple_choice", "fill_blank")
            language: Language for exercises
            **kwargs: Additional parameters
            
        Returns:
            List of exercise dictionaries, each containing:
                - question: The exercise question
                - options: Answer options (if applicable)
                - correct_answer: The correct answer
                - explanation: Explanation of the answer
                - difficulty: Exercise difficulty
                
        Raises:
            AdapterError: If generation fails
        """
        pass
    
    @abstractmethod
    async def generate_game(
        self,
        topic: str,
        level: str,
        game_type: str,
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an educational game.
        
        Args:
            topic: The subject/topic for the game
            level: Difficulty level
            game_type: Type of game (e.g., "quiz", "matching", "word_search")
            language: Language for the game
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing game data:
                - title: Game title
                - instructions: How to play
                - content: Game-specific content
                - scoring: Scoring rules
                
        Raises:
            AdapterError: If generation fails
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the adapter is healthy and can connect to its service.
        
        Returns:
            Dictionary with health status:
                - status: "healthy" or "unhealthy"
                - adapter: Adapter name
                - details: Additional information
        """
        return {
            "status": "healthy",
            "adapter": self.__class__.__name__,
            "details": "Base health check - override in subclass"
        }


class AdapterError(Exception):
    """Base exception for adapter-related errors."""
    pass


class AdapterConnectionError(AdapterError):
    """Raised when adapter cannot connect to the AI service."""
    pass


class AdapterValidationError(AdapterError):
    """Raised when response validation fails."""
    pass


class AdapterTimeoutError(AdapterError):
    """Raised when request times out."""
    pass
