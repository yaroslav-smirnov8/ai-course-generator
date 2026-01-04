# Quick Start Guide

Get the AI Educational Content Generator running in 5 minutes.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- Git

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd bfront
```

### 2. Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# The default configuration uses MockAdapter (no API keys needed)
# Edit .env if you want to use a real AI provider
```

### 3. Frontend Setup (2 minutes)

```bash
# Navigate to frontend (from project root)
cd vue-project

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env
```

### 4. Run Application (1 minute)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd vue-project
npm run dev
```

### 5. Access Application

Open your browser and navigate to:
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## First Steps

### Using the Mock Adapter (Default)

The application comes with a **MockAdapter** that works without any API keys:

1. Open http://localhost:5173
2. Navigate to "Lesson Plan Generator"
3. Fill in the form:
   - Topic: "Present Simple"
   - Level: "A1"
   - Duration: 45 minutes
4. Click "Generate"
5. See sample lesson plan (from MockAdapter)

### Connecting a Real AI Provider

To use a real AI provider (OpenAI, Anthropic, etc.):

1. **Edit `backend/.env`:**

```bash
# Change adapter type
AI_ADAPTER=custom

# Add your API credentials
CUSTOM_AI_API_URL=https://api.openai.com/v1
CUSTOM_AI_API_KEY=sk-your-api-key-here
CUSTOM_AI_MODEL=gpt-4
```

2. **Restart backend:**

```bash
# Stop the backend (Ctrl+C)
# Start again
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Test with real AI:**
   - Generate content again
   - Now it uses your AI provider

## Testing the API

### Using Swagger UI

1. Open http://localhost:8000/docs
2. Try the `/health` endpoint:
   - Click "Try it out"
   - Click "Execute"
   - See response with adapter status

3. Try `/api/lesson-plan`:
   - Click "Try it out"
   - Fill in the request body:
   ```json
   {
     "topic": "Present Simple",
     "level": "A1",
     "duration": 45,
     "language": "en"
   }
   ```
   - Click "Execute"
   - See generated lesson plan

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Generate lesson plan
curl -X POST http://localhost:8000/api/lesson-plan \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Present Simple",
    "level": "A1",
    "duration": 45,
    "language": "en"
  }'
```

## Available Features

### 1. Lesson Plan Generator
- Create structured lesson plans
- Specify topic, level, duration
- Get objectives, activities, materials, assessment

### 2. Exercise Generator
- Generate practice exercises
- Multiple choice, fill-in-blank, etc.
- Adjustable difficulty

### 3. Game Generator
- Create educational games
- Quiz, matching, word search
- Interactive learning activities

### 4. Course Generator
- Build complete courses
- Multiple lessons
- Structured curriculum

## Troubleshooting

### Backend won't start

**Problem**: `ModuleNotFoundError`

```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Problem**: Port 8000 already in use

```bash
# Solution: Use different port
uvicorn app.main:app --reload --port 8001

# Update frontend .env:
echo "VITE_API_URL=http://localhost:8001" > vue-project/.env
```

### Frontend won't start

**Problem**: `Cannot find module`

```bash
# Solution: Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Problem**: API connection refused

```bash
# Solution: Check backend is running
curl http://localhost:8000/health

# If not running, start backend first
```

### Mock adapter not working

**Problem**: Getting errors with mock adapter

```bash
# Solution: Verify .env configuration
cat backend/.env | grep AI_ADAPTER
# Should show: AI_ADAPTER=mock

# If not, fix it:
echo "AI_ADAPTER=mock" >> backend/.env
```

## Next Steps

1. **Read Documentation**:
   - [Architecture Overview](ARCHITECTURE.md)
   - [Adapter Development Guide](docs/ADAPTERS.md)
   - [Deployment Guide](DEPLOY.md)

2. **Create Custom Adapter**:
   - Copy `backend/app/adapters/custom.py`
   - Implement for your AI provider
   - Register in `__init__.py`

3. **Customize Frontend**:
   - Modify components in `vue-project/src/components/`
   - Add new views in `vue-project/src/views/`
   - Update styling with Tailwind CSS

4. **Deploy to Production**:
   - Follow [DEPLOY.md](DEPLOY.md)
   - Choose your hosting platform
   - Configure production environment

## Common Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload          # Development
uvicorn app.main:app --host 0.0.0.0    # Production
pytest tests/                           # Run tests

# Frontend
cd vue-project
npm run dev                             # Development
npm run build                           # Production build
npm run preview                         # Preview build

# Both
# Run in separate terminals
```

## Getting Help

- Check [README.md](README.md) for overview
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- See [docs/ADAPTERS.md](docs/ADAPTERS.md) for adapter guide
- Review example code in `backend/app/adapters/`

## Success Indicators

✅ Backend running at http://localhost:8000
✅ Frontend running at http://localhost:5173
✅ API docs accessible at http://localhost:8000/docs
✅ Health check returns `{"status": "healthy"}`
✅ Can generate lesson plan with mock adapter

---

**Congratulations!** You now have a working AI content generation platform.

**Next**: Try connecting your own AI provider by following the [Adapter Development Guide](docs/ADAPTERS.md).
