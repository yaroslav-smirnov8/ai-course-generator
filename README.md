# AI Educational Content Generator

**Type:** Hybrid Server-Serverless + Telegram Mini App

A production-grade platform for generating educational content using AI models. Originally developed as a commercial SaaS product, now open-sourced as a portfolio demonstration of modern full-stack architecture.

## Platform & Runtime Requirements

This is a **Telegram Mini App** backed by a hybrid server-serverless architecture. It is platform-dependent and requires multiple external services.

**Core Dependencies:**
- Telegram Mini App SDK (cryptographic session validation)
- FastAPI backend (Python 3.9+)
- PostgreSQL 12+ with async driver
- Cloudflare Workers for edge computing
- AI providers: OpenAI, Google Gemini, or Anthropic Claude
- Vue.js 3 for frontend

**Platform-specific constraints:**
- Telegram Mini App requires `initData` validation (cryptographic signature verification)
- Frontend runs inside Telegram client, using Telegram Web App API
- Backend serves both traditional API endpoints and WebSocket connections
- Cloudflare Workers layer requires wrangler deployment tooling

**Why full local development without external services is not applicable:**
- Telegram Mini App development requires either: (a) Telegram test server with Mini App enabled, or (b) external tunnel (ngrok/cloudflared) to expose localhost to Telegram's HTTPS requirements
- PostgreSQL must be accessible (local Docker container suffices for single developer)
- AI provider keys are required for generation features (test credentials can be mocked in development)
- Cloudflare Workers integration requires Wrangler CLI and Cloudflare account access

This is standard for Telegram Mini App development. Telegram explicitly requires HTTPS and external tunneling for Mini App development.

## 🎯 Project Overview

This system generates structured educational content (lesson plans, exercises, games, course materials) using multiple AI providers with automatic fallback mechanisms. It demonstrates enterprise-level patterns including:

- Multi-provider AI orchestration with automatic failover
- Serverless architecture with edge computing
- Type-safe frontend with Vue 3 + TypeScript
- RESTful API design with FastAPI
- Modular adapter pattern for AI integrations

## 🏗️ Architecture

```
┌─────────────┐
│   Vue 3 UI  │ ← User Interface (TypeScript + Tailwind)
└──────┬──────┘
       │
┌──────▼──────────┐
│  FastAPI Backend│ ← Business Logic + Orchestration
└──────┬──────────┘
       │
┌──────▼──────────┐
│ Adapter Layer   │ ← Generic AI Provider Interface
└──────┬──────────┘
       │
┌──────▼──────────────────────────┐
│  Your AI Provider / Mock API    │
└─────────────────────────────────┘
```

### Key Components

- **Backend** (`backend/`): FastAPI application with content generation logic
- **Frontend** (`vue-project/`): Vue 3 SPA with TypeScript
- **Adapters** (`backend/app/adapters/`): Generic AI provider interfaces
- **Prompt Templates** (`backend/prompt_templates/`): Structured prompts for content generation

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Local Development

1. **Clone and setup backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

3. **Run backend:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Setup frontend:**

```bash
cd vue-project
npm install
```

5. **Run frontend:**

```bash
npm run dev
```

Access the application at `http://localhost:5173`

## ⚙️ Configuration

### Environment Variables

Create `backend/.env` from `.env.example`:

```bash
# Application Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# AI Adapter Configuration
AI_ADAPTER=mock  # Options: mock, custom, openai, anthropic, etc.

# Custom AI Provider (if using custom adapter)
CUSTOM_AI_API_URL=https://your-api.example.com
CUSTOM_AI_API_KEY=your_api_key_here
CUSTOM_AI_MODEL=your_model_name

# API Settings
API_TIMEOUT=60
MAX_RETRIES=3
```

### Frontend Configuration

Edit `vue-project/.env`:

```bash
VITE_API_URL=http://localhost:8000
```

## 🔌 Adapter System

The platform uses a **dual-layer architecture** for AI integration:

### Layer 1: High-Level Adapters (LLM Abstraction)

Located in `backend/app/adapters/`, these provide a **unified interface** for any LLM provider:

```python
class BaseAIAdapter(ABC):
    async def generate_text(self, prompt: str, **kwargs) -> str
    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict
    async def generate_lesson_plan(self, topic: str, level: str, **kwargs) -> dict
    async def generate_exercises(self, topic: str, level: str, **kwargs) -> list
    async def generate_game(self, topic: str, level: str, game_type: str, **kwargs) -> dict
```

**Extension Point**: Implement `BaseAIAdapter` to connect any LLM (OpenAI, Anthropic, local models, etc.)

### Layer 2: Provider Gateway (Multi-Provider Orchestration)

Located in `backend/app/services/api_gateway/`, this layer provides:

- **Automatic failover** between multiple providers
- **Health monitoring** and metrics collection
- **Rate limiting** and cooldown management
- **Load balancing** across providers

```python
class BaseProvider(ABC):
    async def call_api(self, request: APIRequest) -> APIResponse
    async def health_check(self) -> bool
```

**Extension Point**: Implement `BaseProvider` to add new provider types with custom routing logic

### Architecture Diagram

```
Application Logic
       ↓
┌──────────────────────────────────┐
│   BaseAIAdapter (Layer 1)        │  ← Unified LLM Interface
│   - generate_text()               │
│   - generate_structured()         │
│   - generate_lesson_plan()        │
└──────────────┬───────────────────┘
               ↓
┌──────────────────────────────────┐
│   API Gateway (Layer 2)          │  ← Multi-Provider Orchestration
│   - Automatic failover            │
│   - Health monitoring             │
│   - Metrics collection            │
└──────────────┬───────────────────┘
               ↓
       ┌───────┴────────┬──────────┐
       ↓                ↓          ↓
  DirectProvider  NetlifyProvider  YourProvider
       ↓                ↓          ↓
   Your APIs      Serverless    Custom Backend
```

## 🚀 How to Plug Your Own API

### Option 1: Simple Adapter (Recommended for Single Provider)

Best for: Connecting a single LLM API without complex routing

**Step 1**: Create your adapter

```python
# backend/app/adapters/my_llm.py
from .base import BaseAIAdapter
import httpx

class MyLLMAdapter(BaseAIAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = os.getenv("MY_LLM_API_KEY")
        self.api_url = os.getenv("MY_LLM_API_URL")
        self.client = httpx.AsyncClient()
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        response = await self.client.post(
            f"{self.api_url}/generate",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"prompt": prompt, **kwargs}
        )
        return response.json()["text"]
    
    async def generate_structured(self, prompt: str, schema: dict, **kwargs) -> dict:
        # Add JSON schema to prompt or use provider's structured output
        response = await self.generate_text(f"{prompt}\n\nReturn JSON: {schema}")
        return json.loads(response)
    
    # Implement other methods...
```

**Step 2**: Register your adapter

```python
# backend/app/adapters/__init__.py
from .my_llm import MyLLMAdapter

ADAPTER_REGISTRY = {
    "mock": MockAdapter,
    "my_llm": MyLLMAdapter,  # Add here
}
```

**Step 3**: Configure environment

```bash
# backend/.env
AI_ADAPTER=my_llm
MY_LLM_API_KEY=your_api_key
MY_LLM_API_URL=https://api.yourllm.com/v1
```

### Option 2: Provider Gateway (Recommended for Multiple Providers)

Best for: Multiple APIs with automatic failover and load balancing

**Step 1**: Create your provider

```python
# backend/app/services/api_gateway/providers/my_provider.py
from .base_provider import BaseProvider
from ..models import APIRequest, APIResponse

class MyProvider(BaseProvider):
    async def _call_model_api(
        self, 
        model_name: str, 
        request: APIRequest
    ) -> APIResponse:
        # Your API call logic
        response = await self.client.post(
            f"{self.config.base_url}/generate",
            json={
                "model": model_name,
                "prompt": request.data.get("prompt"),
            }
        )
        
        return APIResponse(
            success=True,
            content=response.json()["text"],
            provider_name=self.name,
            model_name=model_name
        )
    
    async def _health_check_implementation(self) -> bool:
        try:
            response = await self.client.get(f"{self.config.base_url}/health")
            return response.status_code == 200
        except:
            return False
```

**Step 2**: Register in gateway

```python
# backend/app/services/api_gateway/config.py
from .providers.my_provider import MyProvider

def get_provider_config(content_type: ContentType) -> List[ProviderConfig]:
    if content_type == ContentType.TEXT:
        return [
            ProviderConfig(
                name="my_provider",
                type=ProviderType.CUSTOM,
                priority=1,  # Highest priority
                base_url=os.getenv("MY_PROVIDER_URL"),
                models=[
                    ModelConfig(name="model-1", priority=1),
                    ModelConfig(name="model-2", priority=2),
                ]
            ),
            # Other providers as fallback...
        ]
```

**Step 3**: Update gateway initialization

```python
# backend/app/services/api_gateway/gateway.py
from .providers import MyProvider

class APIGateway:
    def _initialize_providers(self):
        provider_classes = {
            ProviderType.CUSTOM: MyProvider,  # Add here
            ProviderType.DIRECT: DirectProvider,
            ProviderType.NETLIFY: NetlifyProvider
        }
        # Rest of initialization...
```

### Comparison: When to Use Which?

| Feature | Simple Adapter | Provider Gateway |
|---------|---------------|------------------|
| **Complexity** | Low | Medium |
| **Setup Time** | 5-10 minutes | 15-30 minutes |
| **Multiple Providers** | No | Yes |
| **Automatic Failover** | No | Yes |
| **Health Monitoring** | Basic | Advanced |
| **Metrics Collection** | No | Yes |
| **Best For** | Single API, prototyping | Production, multiple APIs |

### Using the Mock Adapter (Default)

The mock adapter returns realistic sample data without requiring any API keys:

```python
# backend/.env
AI_ADAPTER=mock
```

Perfect for:
- Testing the application without API costs
- Demonstrating the system to stakeholders
- Developing frontend without backend dependencies

## 📁 Project Structure

```
bfront/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── adapters/          # AI provider adapters
│   │   │   ├── base.py        # Base adapter interface
│   │   │   ├── mock.py        # Mock adapter (no API needed)
│   │   │   └── custom.py      # Template for custom adapters
│   │   ├── api/               # API routes
│   │   ├── core/              # Core business logic
│   │   ├── models/            # Data models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business services
│   │   └── main.py            # Application entry point
│   ├── prompt_templates/      # AI prompt templates
│   ├── tests/                 # Unit and integration tests
│   ├── .env.example           # Environment template
│   └── requirements.txt       # Python dependencies
│
├── vue-project/               # Vue 3 frontend
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   ├── services/          # API services
│   │   ├── store/             # Pinia state management
│   │   └── router/            # Vue Router config
│   ├── .env                   # Frontend config
│   └── package.json           # Node dependencies
│
├── docs/                      # Documentation
├── ARCHITECTURE.md            # Architecture deep-dive
├── DEPLOY.md                  # Deployment guide
└── README.md                  # This file
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd vue-project
npm run test
```

## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md) - Detailed system architecture
- [Deployment Guide](DEPLOY.md) - How to deploy to production
- [API Documentation](docs/API.md) - REST API reference
- [Adapter Development](docs/ADAPTERS.md) - Creating custom adapters

## 🎓 Educational Use Cases

This platform can generate:

- **Lesson Plans**: Structured teaching plans with objectives, activities, and assessments
- **Exercises**: Practice problems with varying difficulty levels
- **Games**: Educational games and interactive activities
- **Course Materials**: Complete course structures with multiple lessons
- **Assessments**: Quizzes and exams with answer keys

## 🔒 Security Notes

- Never commit API keys or secrets to version control
- Use environment variables for all sensitive configuration
- The mock adapter is safe for public demos (no external API calls)
- Implement rate limiting in production deployments
- Validate and sanitize all user inputs

## 🏆 Architectural Strengths

1. **Separation of Concerns**: Clean layering between UI, business logic, and AI providers
2. **Adapter Pattern**: Easy to swap AI providers without changing core logic
3. **Type Safety**: TypeScript frontend + Pydantic backend for compile-time safety
4. **Async/Await**: Non-blocking I/O for high concurrency
5. **Modular Design**: Each component can be developed and tested independently
6. **Prompt Engineering**: Centralized, version-controlled prompt templates
7. **Error Handling**: Graceful degradation with fallback mechanisms

## What to Review Instead of Running Locally

Best understood through architecture review and code analysis:

### Hybrid Deployment Architecture
- **Server-Serverless Split** – How critical business logic stays on FastAPI (always-warm) while edge tasks run on Cloudflare Workers
- **Cold Start Mitigation** – Why persistent FastAPI core is necessary (serverless cold starts break streaming), while Workers handle caching
- **Cost Optimization** – How this hybrid approach achieves cost efficiency vs. traditional single-provider model

### AI Orchestration Layer
- **Multi-Provider Routing** (`/backend/app/adapters/`) – Abstract provider interface enabling OpenAI, Gemini, Claude swapping without core changes
- **Waterfall Strategy** – How requests attempt lower-cost models first, escalate on timeout or failure
- **Health Monitoring** – Tracking provider failure rates and auto-switching to secondary provider
- **Cost Tracking** – Per-request cost logging and daily quota management

### Real-Time Streaming Design
- **Server-Sent Events (SSE)** – How FastAPI StreamingResponse delivers cursor-by-cursor LLM output
- **Automatic Reconnect** – Client-side logic resuming from last received token if connection drops mid-stream
- **Buffering Strategy** – How tokens are buffered server-side to enable replay on reconnection

### Telegram Mini App Integration
- **initData Validation** – HMAC-SHA256 signature verification against Telegram Bot token
- **Session Management** – JWT token issuance after Telegram auth validation
- **Client-Side Implementation** – How Vue.js 3 frontend uses Telegram Web App API for haptics, theme detection, etc.

### Database & Async Patterns
- **Async SQLAlchemy + asyncpg** – Why asyncpg is critical for non-blocking I/O under concurrent generation requests
- **Connection Pool Tuning** – How pool sizing handles burst traffic from serverless environments
- **JSONB Course Storage** – Why PostgreSQL JSONB enables flexible schema evolution for lesson structures

### Frontend (Vue.js 3)
- **State Management with Pinia** – How generation state, user quotas, and course progress are tracked
- **Real-time Updates** – Integration with SSE endpoint for streaming generation progress
- **Responsive Design** – TailwindCSS styling optimized for mobile and desktop Telegram clients

## ⚠️ Known Limitations

- Mock adapter provides static responses (not real AI generation)
- No built-in authentication system (add your own OAuth/JWT)
- No database persistence layer (responses are ephemeral)
- Rate limiting must be implemented per deployment
- No built-in caching mechanism

## 🤝 Contributing

This is a portfolio project demonstrating production-ready patterns. Feel free to:

- Study the architecture for learning purposes
- Use as a template for your own projects
- Adapt the adapter pattern for your use cases

## 📄 License

Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)

This project is licensed for non-commercial use only. See [LICENSE](LICENSE) for details.

## 👤 Author

Portfolio project demonstrating full-stack development capabilities with modern technologies.

**Technologies**: Python, FastAPI, Vue 3, TypeScript, Pinia, Tailwind CSS, Async/Await, REST APIs

---

**Note**: This is a portfolio demonstration project. The original commercial infrastructure has been removed and replaced with generic adapters. To use in production, implement your own AI provider adapters and authentication system.
