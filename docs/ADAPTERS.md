# Adapter Development Guide

This guide explains how to create custom adapters to connect the platform to any AI provider or neural network.

## Table of Contents

1. [Understanding Adapters](#understanding-adapters)
2. [Adapter Interface](#adapter-interface)
3. [Creating a Custom Adapter](#creating-a-custom-adapter)
4. [Testing Your Adapter](#testing-your-adapter)
5. [Examples](#examples)

## Understanding Adapters

Adapters provide a **consistent interface** between the application's business logic and external AI providers. This pattern allows you to:

- Swap AI providers without changing application code
- Test with mock data before connecting real APIs
- Support multiple providers simultaneously
- Implement fallback mechanisms

### Architecture

```
Application Code
       ↓
BaseAIAdapter (Interface)
       ↓
┌──────┴──────┬──────────┬──────────┐
│             │          │          │
MockAdapter  CustomAdapter  YourAdapter
```

## Adapter Interface

All adapters must implement the `BaseAIAdapter` abstract class:

```python
from backend.app.adapters.base import BaseAIAdapter

class YourAdapter(BaseAIAdapter):
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate plain text"""
        
    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """Generate structured JSON"""
        
    async def generate_lesson_plan(self, topic: str, level: str, **kwargs) -> dict:
        """Generate lesson plan"""
        
    async def generate_exercises(self, topic: str, level: str, **kwargs) -> list:
        """Generate exercises"""
        
    async def generate_game(self, topic: str, level: str, game_type: str, **kwargs) -> dict:
        """Generate educational game"""
```

## Creating a Custom Adapter

### Step 1: Create Adapter File

Create a new file in `backend/app/adapters/`:

```python
# backend/app/adapters/my_provider.py

import os
import httpx
from typing import Dict, List, Optional, Any
from .base import BaseAIAdapter, AdapterError

class MyProviderAdapter(BaseAIAdapter):
    """Adapter for MyProvider AI service."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Load configuration
        self.api_key = config.get("api_key") or os.getenv("MYPROVIDER_API_KEY")
        self.api_url = config.get("api_url") or os.getenv("MYPROVIDER_API_URL")
        self.model = config.get("model") or os.getenv("MYPROVIDER_MODEL", "default")
        
        if not self.api_key:
            raise AdapterError("MYPROVIDER_API_KEY is required")
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Implement text generation for your provider."""
        response = await self.client.post(
            f"{self.api_url}/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000)
            }
        )
        
        if response.status_code != 200:
            raise AdapterError(f"API error: {response.status_code}")
        
        result = response.json()
        return result["text"]  # Adjust based on your API's response format
```

### Step 2: Register Your Adapter

Add your adapter to `backend/app/adapters/__init__.py`:

```python
from .my_provider import MyProviderAdapter

ADAPTER_REGISTRY = {
    "mock": MockAdapter,
    "custom": CustomAdapter,
    "my_provider": MyProviderAdapter,  # Add your adapter
}
```

### Step 3: Configure Environment

Add configuration to `.env`:

```bash
AI_ADAPTER=my_provider
MYPROVIDER_API_KEY=your_api_key
MYPROVIDER_API_URL=https://api.myprovider.com/v1
MYPROVIDER_MODEL=your_model_name
```

### Step 4: Use Your Adapter

```python
from backend.app.adapters import create_adapter

# Adapter is automatically created based on AI_ADAPTER env var
adapter = create_adapter()

# Or create explicitly
adapter = create_adapter("my_provider")

# Use the adapter
result = await adapter.generate_text("Hello, world!")
```

## Testing Your Adapter

### Unit Tests

Create `backend/tests/test_my_provider_adapter.py`:

```python
import pytest
from backend.app.adapters.my_provider import MyProviderAdapter

@pytest.mark.asyncio
async def test_generate_text():
    adapter = MyProviderAdapter({
        "api_key": "test_key",
        "api_url": "https://test.api.com"
    })
    
    result = await adapter.generate_text("Test prompt")
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_health_check():
    adapter = MyProviderAdapter({"api_key": "test_key"})
    health = await adapter.health_check()
    assert health["status"] in ["healthy", "unhealthy"]
```

### Integration Tests

Test with real API (use test credentials):

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_call():
    adapter = create_adapter("my_provider")
    
    result = await adapter.generate_lesson_plan(
        topic="Present Simple",
        level="A1"
    )
    
    assert "title" in result
    assert "objectives" in result
    assert len(result["activities"]) > 0
```

## Examples

### Example 1: OpenAI Adapter

```python
import openai
from .base import BaseAIAdapter

class OpenAIAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000)
        )
        return response.choices[0].message.content
```

### Example 2: Anthropic Adapter

```python
import anthropic
from .base import BaseAIAdapter

class AnthropicAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
```

### Example 3: Self-Hosted Ollama

```python
import httpx
from .base import BaseAIAdapter

class OllamaAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama2")
        self.client = httpx.AsyncClient()
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        result = response.json()
        return result["response"]
```

### Example 4: Hugging Face Inference API

```python
import httpx
from .base import BaseAIAdapter

class HuggingFaceAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = os.getenv("HF_API_KEY")
        self.model = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        response = await self.client.post(
            f"https://api-inference.huggingface.co/models/{self.model}",
            json={
                "inputs": prompt,
                "parameters": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_new_tokens": kwargs.get("max_tokens", 2000)
                }
            }
        )
        result = response.json()
        return result[0]["generated_text"]
```

## Advanced Features

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientAdapter(BaseAIAdapter):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_text(self, prompt: str, **kwargs) -> str:
        # Your implementation with automatic retries
        pass
```

### Caching

```python
from functools import lru_cache
import hashlib

class CachedAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.cache = {}
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        # Create cache key
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Generate and cache
        result = await self._generate_uncached(prompt, **kwargs)
        self.cache[cache_key] = result
        return result
```

### Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta

class RateLimitedAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.requests = []
        self.max_per_minute = 60
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        await self._wait_for_rate_limit()
        return await self._generate(prompt, **kwargs)
    
    async def _wait_for_rate_limit(self):
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove old requests
        self.requests = [r for r in self.requests if r > minute_ago]
        
        if len(self.requests) >= self.max_per_minute:
            wait_time = (self.requests[0] - minute_ago).total_seconds()
            await asyncio.sleep(wait_time)
        
        self.requests.append(now)
```

## Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Timeouts**: Set reasonable timeouts for API requests
3. **Logging**: Log important events and errors
4. **Validation**: Validate responses before returning
5. **Configuration**: Use environment variables for secrets
6. **Testing**: Write both unit and integration tests
7. **Documentation**: Document your adapter's requirements

## Troubleshooting

### Common Issues

**Problem**: Import errors

```python
# Solution: Ensure __init__.py imports your adapter
from .my_provider import MyProviderAdapter
```

**Problem**: Configuration not loading

```python
# Solution: Check environment variable names
print(os.getenv("MYPROVIDER_API_KEY"))  # Debug
```

**Problem**: Async/await errors

```python
# Solution: Ensure all methods are async
async def generate_text(self, ...):  # Must be async
    result = await self.client.post(...)  # Must await
```

## Resources

- [BaseAIAdapter source](../backend/app/adapters/base.py)
- [MockAdapter example](../backend/app/adapters/mock.py)
- [CustomAdapter template](../backend/app/adapters/custom.py)

---

**Need help?** Check the existing adapters for reference implementations.
