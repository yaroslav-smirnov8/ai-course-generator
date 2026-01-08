# Module for Working with Mistral AI API

This module provides a simple interface for interacting with the Mistral AI API using the official client library.

## Installation

To work with the module, you need to install the dependencies:

```bash
pip install mistralai python-dotenv httpx
```

## Configuration

1. Create a `.env` file in the project root directory and add your Mistral API key to it:

```
MISTRAL_API_KEY=your-api-key-here
MISTRAL_API_BASE=https://api.mistral.ai  # optional, if you need to change the base URL
```

2. Import and use the module in your code.

## Usage

### Standalone Usage of MistralHandler

```python
from mistral_api import MistralHandler

# Initialization
mistral = MistralHandler(api_key="your-api-key-here")  # or don't specify if it's set in .env

# Availability check
if mistral.is_available():
    # Getting the list of available models
    models = mistral.get_available_models()
    print(f"Available {len(models)} models")

    # Asynchronous text generation
    async def generate():
        result = await mistral.generate_content(
            prompt="Write a poem about programming",
            model="open-mistral-nemo",  # can specify a specific model
            temperature=0.7,
            max_tokens=2048
        )
        print(result)

    # Synchronous text generation
    result = mistral.generate_content_sync(
        prompt="Write a poem about programming",
        model="open-mistral-nemo",
        temperature=0.7,
        max_tokens=2048
    )
    print(result)
```

### Usage in G4FHandler

The `mistral_api.py` module is integrated with `G4FHandler` and is used as the main method for content generation:

```python
from g4f_handler import G4FHandler

# Initialization
handler = G4FHandler(api_key="your-api-key-here")  # or don't specify if it's set in .env

# Asynchronous generation via G4FHandler (uses MistralHandler)
async def generate():
    result = await handler.generate_content(
        prompt="Write a poem about programming"
    )
    print(result)

# Synchronous generation via G4FHandler (uses MistralHandler)
messages = [{"role": "user", "content": "Write a poem about programming"}]
result = handler.generate_chat_completion(messages=messages)
print(result["content"])
```

## Testing

1. For testing standalone operation of the Mistral API module:

```bash
python test_mistral.py
```

2. For testing integration with G4FHandler:

```bash
python test_integration.py
```

## Error Handling

The module includes special exceptions for handling various errors:

- `MistralAPIException` - base exception for all API errors
- `MistralConnectionException` - API connection errors
- `MistralRateLimitException` - exceeding request limit
- `MistralAuthException` - authorization errors

Example of error handling:

```python
from mistral_api import MistralHandler, MistralAPIException, MistralConnectionException

try:
    mistral = MistralHandler(api_key="your-api-key-here")
    result = mistral.generate_content_sync(prompt="Your request")
except MistralConnectionException as e:
    print(f"Connection error: {e}")
except MistralAPIException as e:
    print(f"API error: {e}")
```

## Notes

- When initializing G4FHandler with a correct Mistral AI API key, Mistral API will automatically be used instead of G4F
- If Mistral API is unavailable or returns an error, G4FHandler will try to use other providers
- For working with large contexts, it's recommended to use models with a larger `max_tokens` value