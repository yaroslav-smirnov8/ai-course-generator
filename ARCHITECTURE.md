# Architecture Overview

## System Design Philosophy

This platform demonstrates a **multi-layered architecture** with clear separation of concerns, designed for scalability, maintainability, and extensibility.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Presentation Layer                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Vue 3 SPA (TypeScript + Composition API)             │  │
│  │  - Reactive UI components                              │  │
│  │  - Pinia state management                              │  │
│  │  - Vue Router for navigation                           │  │
│  │  - Tailwind CSS for styling                            │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP/REST
┌───────────────────────────▼──────────────────────────────────┐
│                     Application Layer                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Python 3.9+)                         │  │
│  │  - RESTful API endpoints                               │  │
│  │  - Request validation (Pydantic)                       │  │
│  │  - Business logic orchestration                        │  │
│  │  - Error handling & logging                            │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     Service Layer                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Content Generation Services                           │  │
│  │  - Lesson plan generator                               │  │
│  │  - Exercise generator                                  │  │
│  │  - Game generator                                      │  │
│  │  - Course structure builder                            │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     Adapter Layer (ABSTRACTION)               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  BaseAIAdapter (Abstract Interface)                    │  │
│  │  ├── generate_text()                                   │  │
│  │  ├── generate_structured()                             │  │
│  │  ├── generate_lesson_plan()                            │  │
│  │  └── generate_exercises()                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MockAdapter  │  │CustomAdapter │  │ YourAdapter  │      │
│  │ (Built-in)   │  │  (Template)  │  │ (Implement)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                     External Services                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Your AI Provider / Neural Network / API               │  │
│  │  - OpenAI, Anthropic, Cohere, etc.                     │  │
│  │  - Self-hosted models (Ollama, vLLM)                   │  │
│  │  - Custom ML endpoints                                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend (Vue 3 + TypeScript)

**Location**: `vue-project/`

**Responsibilities**:
- User interface rendering
- Form validation and user input
- State management (Pinia)
- API communication
- Routing and navigation

**Key Technologies**:
- Vue 3 Composition API
- TypeScript for type safety
- Pinia for state management
- Vue Router for SPA routing
- Tailwind CSS for styling
- Axios for HTTP requests

**Component Structure**:
```
src/
├── components/       # Reusable UI components
│   ├── common/      # Shared components
│   └── LessonPlan.vue
├── views/           # Page-level components
├── services/        # API service layer
├── store/           # Pinia stores
├── router/          # Route definitions
└── utils/           # Helper functions
```

### 2. Backend (FastAPI)

**Location**: `backend/app/`

**Responsibilities**:
- API endpoint handling
- Request/response validation
- Business logic orchestration
- Adapter management
- Error handling and logging

**Key Technologies**:
- FastAPI for async REST API
- Pydantic for data validation
- Python asyncio for concurrency
- Uvicorn ASGI server

**Module Structure**:
```
app/
├── api/             # API route handlers
│   └── routes/      # Endpoint definitions
├── adapters/        # AI provider adapters
│   ├── base.py      # Abstract base class
│   ├── mock.py      # Mock implementation
│   └── custom.py    # Custom adapter template
├── core/            # Core business logic
├── models/          # Data models
├── schemas/         # Pydantic schemas
├── services/        # Business services
└── main.py          # Application entry point
```

### 3. Adapter Layer

**Location**: `backend/app/adapters/`

**Purpose**: Provides a **generic interface** for AI providers, allowing easy swapping without changing business logic.

**Base Interface**:
```python
class BaseAIAdapter(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate plain text response"""
        
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        """Generate structured JSON response"""
        
    @abstractmethod
    async def generate_lesson_plan(self, topic: str, level: str, **kwargs) -> dict:
        """Generate educational lesson plan"""
```

**Built-in Adapters**:

1. **MockAdapter** (`mock.py`):
   - Returns realistic sample data
   - No API keys required
   - Perfect for demos and testing

2. **CustomAdapter** (`custom.py`):
   - Template for implementing your own
   - Configurable via environment variables
   - Supports any REST API

**Creating Your Own Adapter**:
```python
from .base import BaseAIAdapter
import httpx

class MyAdapter(BaseAIAdapter):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        response = await self.client.post(
            f"{self.base_url}/generate",
            json={"prompt": prompt, **kwargs},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()["text"]
```

## Data Flow

### Example: Generating a Lesson Plan

```
1. User Input (Frontend)
   └─> User fills form: topic="Present Simple", level="A1"

2. API Request (Frontend → Backend)
   └─> POST /api/lesson-plan
       Body: { topic: "Present Simple", level: "A1", language: "en" }

3. Request Validation (Backend)
   └─> Pydantic schema validates input
       └─> LessonPlanRequest model

4. Service Layer (Backend)
   └─> LessonPlanService.generate()
       ├─> Loads prompt template
       ├─> Formats prompt with user data
       └─> Calls adapter

5. Adapter Layer (Backend)
   └─> adapter.generate_lesson_plan(topic, level)
       └─> Calls external AI API (or mock)

6. Response Processing (Backend)
   └─> Validates response structure
       └─> Returns LessonPlanResponse

7. UI Update (Frontend)
   └─> Displays generated lesson plan
       └─> User can download/edit/save
```

## Design Patterns

### 1. Adapter Pattern
**Purpose**: Decouple AI provider implementation from business logic

**Benefits**:
- Easy to swap providers
- Testable with mock implementations
- Consistent interface across different APIs

### 2. Repository Pattern
**Purpose**: Abstract data access (if database is added)

**Benefits**:
- Separation of data access logic
- Easy to switch databases
- Testable with in-memory implementations

### 3. Service Layer Pattern
**Purpose**: Encapsulate business logic

**Benefits**:
- Reusable business logic
- Easier to test
- Clear separation from API layer

### 4. Dependency Injection
**Purpose**: Inject dependencies (adapters, configs) at runtime

**Benefits**:
- Loose coupling
- Easy to test with mocks
- Configurable behavior

## Prompt Engineering

**Location**: `backend/prompt_templates/`

Prompts are centralized and version-controlled:

```python
# prompt_templates/lesson_plan.py
LESSON_PLAN_PROMPT = """
Create a detailed lesson plan for teaching {topic} at {level} level.

Requirements:
- Duration: {duration} minutes
- Language: {language}
- Include: objectives, activities, materials, assessment

Format the response as JSON with this structure:
{schema}
"""
```

**Benefits**:
- Version control for prompts
- Easy A/B testing
- Reusable across adapters
- Centralized prompt optimization

## Error Handling Strategy

### 1. Validation Errors (400)
- Invalid input format
- Missing required fields
- Type mismatches

### 2. Authentication Errors (401)
- Missing API keys
- Invalid credentials

### 3. Rate Limiting (429)
- Too many requests
- Quota exceeded

### 4. Server Errors (500)
- AI provider failures
- Unexpected exceptions
- Timeout errors

### Fallback Mechanism
```python
async def generate_with_fallback(prompt: str):
    try:
        return await primary_adapter.generate(prompt)
    except Exception as e:
        logger.warning(f"Primary failed: {e}")
        try:
            return await fallback_adapter.generate(prompt)
        except Exception as e2:
            logger.error(f"Fallback failed: {e2}")
            return mock_adapter.generate(prompt)  # Always works
```

## Scalability Considerations

### Horizontal Scaling
- Stateless backend (can run multiple instances)
- Load balancer distributes requests
- Shared configuration via environment variables

### Caching Strategy (Future)
- Cache common prompts/responses
- Redis for distributed caching
- TTL-based invalidation

### Rate Limiting (Future)
- Per-user rate limits
- Per-endpoint limits
- Token bucket algorithm

### Monitoring (Future)
- Request/response logging
- Performance metrics
- Error tracking
- Usage analytics

## Security Architecture

### Input Validation
- Pydantic schemas validate all inputs
- SQL injection prevention (if DB added)
- XSS prevention in frontend

### API Security
- CORS configuration
- Rate limiting (implement per deployment)
- API key rotation support

### Secrets Management
- Environment variables for secrets
- Never commit credentials
- Use secret managers in production (AWS Secrets Manager, etc.)

## Testing Strategy

### Unit Tests
- Test individual functions
- Mock external dependencies
- Fast execution

### Integration Tests
- Test API endpoints
- Use mock adapter
- Validate request/response flow

### E2E Tests (Future)
- Test complete user flows
- Browser automation
- Real UI interactions

## Deployment Architecture

### Development
```
Local Machine
├── Backend: localhost:8000
├── Frontend: localhost:5173
└── Mock Adapter (no external calls)
```

### Production (Example)
```
Cloud Provider
├── Backend: Docker container / VM
│   └── Uvicorn + Gunicorn
├── Frontend: Static hosting (Netlify, Vercel, S3)
│   └── Built Vue app
└── AI Provider: Your choice
    └── OpenAI, Anthropic, self-hosted, etc.
```

## Technology Choices Rationale

| Technology | Why Chosen |
|------------|-----------|
| **FastAPI** | Async support, automatic OpenAPI docs, type hints |
| **Vue 3** | Composition API, TypeScript support, lightweight |
| **Pydantic** | Runtime validation, type safety, auto-documentation |
| **TypeScript** | Compile-time type checking, better IDE support |
| **Tailwind CSS** | Utility-first, fast development, consistent design |
| **Pinia** | Vue 3 native, TypeScript support, devtools |

## Future Enhancements

### Potential Additions
1. **Database Layer**: PostgreSQL for persistence
2. **Authentication**: OAuth2 / JWT tokens
3. **Caching**: Redis for response caching
4. **Queue System**: Celery for background jobs
5. **WebSockets**: Real-time generation updates
6. **Multi-tenancy**: Support multiple organizations
7. **Analytics**: Usage tracking and insights
8. **A/B Testing**: Prompt optimization framework

### Architectural Evolution
```
Current: Monolithic backend + SPA frontend
Future: Microservices architecture
  ├── Content Generation Service
  ├── User Management Service
  ├── Analytics Service
  └── API Gateway
```

## Conclusion

This architecture demonstrates:
- **Clean separation of concerns**
- **Extensibility through adapters**
- **Type safety across the stack**
- **Production-ready patterns**
- **Easy to understand and modify**

The adapter pattern is the key innovation, allowing you to plug in any AI provider without touching business logic.
