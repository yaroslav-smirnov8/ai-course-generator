"""
Custom adapter template for connecting your own AI provider.

This is a template you can customize to connect to any AI API or neural network.
Replace the placeholder implementations with your actual API calls.
"""

import os
import json
import httpx
from typing import Dict, List, Optional, Any
from .base import BaseAIAdapter, AdapterError, AdapterConnectionError, AdapterTimeoutError


class CustomAdapter(BaseAIAdapter):
    """
    Custom adapter for connecting to your AI provider.
    
    Configure via environment variables:
    - CUSTOM_AI_API_URL: Your API endpoint
    - CUSTOM_AI_API_KEY: Your API key
    - CUSTOM_AI_MODEL: Model name to use
    - CUSTOM_AI_TIMEOUT: Request timeout in seconds
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Load configuration from environment or config dict
        self.api_url = config.get("api_url") or os.getenv("CUSTOM_AI_API_URL", "")
        self.api_key = config.get("api_key") or os.getenv("CUSTOM_AI_API_KEY", "")
        self.model = config.get("model") or os.getenv("CUSTOM_AI_MODEL", "default-model")
        self.timeout = int(config.get("timeout") or os.getenv("CUSTOM_AI_TIMEOUT", "60"))
        
        if not self.api_url:
            raise AdapterError("CUSTOM_AI_API_URL is required")
        if not self.api_key:
            raise AdapterError("CUSTOM_AI_API_KEY is required")
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate text using your AI provider.
        
        Customize this method to match your API's request/response format.
        """
        try:
            # Example request format - adjust to match your API
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.api_url}/generate",  # Adjust endpoint
                json=request_data
            )
            
            if response.status_code != 200:
                raise AdapterConnectionError(
                    f"API returned status {response.status_code}: {response.text}"
                )
            
            result = response.json()
            
            # Extract text from response - adjust based on your API's format
            # Example formats:
            # - OpenAI-style: result["choices"][0]["text"]
            # - Anthropic-style: result["completion"]
            # - Custom: result["generated_text"]
            
            text = result.get("text") or result.get("generated_text") or ""
            
            if not text:
                raise AdapterError("No text in API response")
            
            return text
            
        except httpx.TimeoutException:
            raise AdapterTimeoutError(f"Request timed out after {self.timeout}s")
        except httpx.RequestError as e:
            raise AdapterConnectionError(f"Connection error: {str(e)}")
        except Exception as e:
            raise AdapterError(f"Generation failed: {str(e)}")
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.
        
        Customize this to use your API's structured output feature,
        or parse JSON from text response.
        """
        try:
            # Option 1: If your API supports JSON mode
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},  # Adjust for your API
                "schema": schema,
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.api_url}/generate",
                json=request_data
            )
            
            if response.status_code != 200:
                raise AdapterConnectionError(
                    f"API returned status {response.status_code}: {response.text}"
                )
            
            result = response.json()
            
            # Extract structured data
            structured_data = result.get("data") or result.get("json") or {}
            
            # Option 2: If your API returns text, parse JSON
            # text = result.get("text", "")
            # structured_data = json.loads(text)
            
            return structured_data
            
        except json.JSONDecodeError as e:
            raise AdapterError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise AdapterError(f"Structured generation failed: {str(e)}")
    
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
        Generate lesson plan using your AI provider.
        
        This uses generate_structured with a lesson plan prompt.
        """
        prompt = f"""Create a detailed lesson plan for teaching "{topic}" at {level} level.

Duration: {duration} minutes
Language: {language}
Methodology: {methodology or 'Communicative Approach'}

Include:
1. Clear learning objectives
2. Required materials
3. Step-by-step activities with timing
4. Assessment methods
5. Additional notes for the teacher

Format the response as JSON matching this structure:
{{
    "title": "lesson title",
    "objectives": ["objective 1", "objective 2"],
    "materials": ["material 1", "material 2"],
    "activities": [
        {{"name": "activity name", "duration": minutes, "description": "...", "interaction": "..."}}
    ],
    "assessment": {{"formative": "...", "summative": "...", "homework": "..."}},
    "notes": ["note 1", "note 2"]
}}
"""
        
        schema = {
            "title": "string",
            "objectives": ["string"],
            "materials": ["string"],
            "activities": [{"name": "string", "duration": "number", "description": "string"}],
            "assessment": {"formative": "string", "summative": "string"},
            "notes": ["string"]
        }
        
        return await self.generate_structured(prompt, schema, **kwargs)
    
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
        Generate practice exercises using your AI provider.
        """
        prompt = f"""Create {count} practice exercises about "{topic}" at {level} level.

Exercise type: {exercise_type or 'multiple choice'}
Language: {language}

For each exercise, include:
- Clear question
- Answer options (if applicable)
- Correct answer
- Explanation

Format as JSON array:
[
    {{
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "explanation": "..."
    }}
]
"""
        
        schema = {
            "exercises": [
                {
                    "question": "string",
                    "options": ["string"],
                    "correct_answer": "string",
                    "explanation": "string"
                }
            ]
        }
        
        result = await self.generate_structured(prompt, schema, **kwargs)
        return result.get("exercises", [])
    
    async def generate_game(
        self,
        topic: str,
        level: str,
        game_type: str,
        language: str = "en",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate educational game using your AI provider.
        """
        prompt = f"""Create a {game_type} game about "{topic}" at {level} level.

Language: {language}

Include:
- Game title
- Clear instructions
- Game content (questions, pairs, words, etc.)
- Scoring rules

Format as JSON matching the game type.
"""
        
        schema = {
            "title": "string",
            "type": "string",
            "instructions": "string",
            "content": "object",
            "scoring": "object"
        }
        
        return await self.generate_structured(prompt, schema, **kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the custom adapter can connect to your API.
        """
        try:
            # Try a simple request to verify connectivity
            response = await self.client.get(f"{self.api_url}/health")
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "adapter": "CustomAdapter",
                    "api_url": self.api_url,
                    "model": self.model
                }
            else:
                return {
                    "status": "unhealthy",
                    "adapter": "CustomAdapter",
                    "error": f"API returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "adapter": "CustomAdapter",
                "error": str(e)
            }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup."""
        await self.client.aclose()
