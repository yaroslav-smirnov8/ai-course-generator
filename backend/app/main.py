"""
AI Educational Content Generator - Main Application

This is the entry point for the FastAPI backend application.
It provides RESTful endpoints for generating educational content using AI.
"""

import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.adapters import create_adapter
from app.adapters.base import AdapterError

# Initialize FastAPI application
app = FastAPI(
    title="AI Educational Content Generator",
    description="Generate educational content (lesson plans, exercises, games) using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI adapter
try:
    adapter = create_adapter()
    print(f"✅ Initialized adapter: {adapter.__class__.__name__}")
except Exception as e:
    print(f"⚠️ Failed to initialize adapter: {e}")
    print("⚠️ Using MockAdapter as fallback")
    from app.adapters.mock import MockAdapter
    adapter = MockAdapter()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class LessonPlanRequest(BaseModel):
    """Request model for lesson plan generation."""
    topic: str = Field(..., description="The subject/topic of the lesson")
    level: str = Field(..., description="Student level (e.g., A1, B2, beginner)")
    duration: int = Field(45, description="Lesson duration in minutes")
    language: str = Field("en", description="Language for the lesson plan")
    methodology: Optional[str] = Field(None, description="Teaching methodology")


class ExerciseRequest(BaseModel):
    """Request model for exercise generation."""
    topic: str = Field(..., description="The subject/topic for exercises")
    level: str = Field(..., description="Difficulty level")
    count: int = Field(5, description="Number of exercises to generate")
    exercise_type: Optional[str] = Field(None, description="Type of exercise")
    language: str = Field("en", description="Language for exercises")


class GameRequest(BaseModel):
    """Request model for game generation."""
    topic: str = Field(..., description="The subject/topic for the game")
    level: str = Field(..., description="Difficulty level")
    game_type: str = Field(..., description="Type of game (quiz, matching, word_search)")
    language: str = Field("en", description="Language for the game")


class TextGenerationRequest(BaseModel):
    """Request model for generic text generation."""
    prompt: str = Field(..., description="The prompt for text generation")
    temperature: float = Field(0.7, description="Sampling temperature (0.0 to 1.0)")
    max_tokens: int = Field(2000, description="Maximum tokens to generate")


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Educational Content Generator",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "adapter": adapter.__class__.__name__
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the application and adapter.
    """
    try:
        health = await adapter.health_check()
        return {
            "status": "healthy",
            "application": "AI Educational Content Generator",
            "adapter": health
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/api/lesson-plan")
async def generate_lesson_plan(request: LessonPlanRequest):
    """
    Generate a structured lesson plan.
    
    Creates a detailed lesson plan including objectives, materials,
    activities, and assessment methods.
    """
    try:
        result = await adapter.generate_lesson_plan(
            topic=request.topic,
            level=request.level,
            duration=request.duration,
            language=request.language,
            methodology=request.methodology
        )
        return {
            "success": True,
            "data": result,
            "adapter": adapter.__class__.__name__
        }
    except AdapterError as e:
        raise HTTPException(status_code=500, detail=f"Adapter error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/exercises")
async def generate_exercises(request: ExerciseRequest):
    """
    Generate practice exercises.
    
    Creates a set of exercises with questions, answers, and explanations.
    """
    try:
        result = await adapter.generate_exercises(
            topic=request.topic,
            level=request.level,
            count=request.count,
            exercise_type=request.exercise_type,
            language=request.language
        )
        return {
            "success": True,
            "data": result,
            "count": len(result),
            "adapter": adapter.__class__.__name__
        }
    except AdapterError as e:
        raise HTTPException(status_code=500, detail=f"Adapter error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/game")
async def generate_game(request: GameRequest):
    """
    Generate an educational game.
    
    Creates an interactive game for learning (quiz, matching, word search, etc.).
    """
    try:
        result = await adapter.generate_game(
            topic=request.topic,
            level=request.level,
            game_type=request.game_type,
            language=request.language
        )
        return {
            "success": True,
            "data": result,
            "adapter": adapter.__class__.__name__
        }
    except AdapterError as e:
        raise HTTPException(status_code=500, detail=f"Adapter error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/generate-text")
async def generate_text(request: TextGenerationRequest):
    """
    Generate plain text from a prompt.
    
    Generic text generation endpoint for custom prompts.
    """
    try:
        result = await adapter.generate_text(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return {
            "success": True,
            "text": result,
            "adapter": adapter.__class__.__name__
        }
    except AdapterError as e:
        raise HTTPException(status_code=500, detail=f"Adapter error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/api/adapters")
async def list_adapters():
    """
    List available adapters.
    
    Returns information about available AI provider adapters.
    """
    from app.adapters import list_adapters
    
    return {
        "current": adapter.__class__.__name__,
        "available": list_adapters(),
        "note": "Change adapter by setting AI_ADAPTER environment variable"
    }


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
        }
    )


# ============================================
# STARTUP/SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("=" * 60)
    print("🚀 AI Educational Content Generator")
    print("=" * 60)
    print(f"📦 Adapter: {adapter.__class__.__name__}")
    print(f"🌐 CORS Origins: {cors_origins}")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 Shutting down AI Educational Content Generator")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
