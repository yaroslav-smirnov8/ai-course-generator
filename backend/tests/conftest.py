"""
Pytest configuration and fixtures for testing
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import Base
from app.main import app
from app.models import User
from app.core.constants import TariffType
from datetime import datetime, timezone, timedelta

# Test database URL
# По умолчанию используем SQLite для тестов (не требует PostgreSQL)
# Можно переопределить через переменную окружения для использования PostgreSQL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test.db"  # SQLite для быстрых тестов
    # "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"  # PostgreSQL если нужно
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create test session maker
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        telegram_id=12345,
        first_name="Test",
        last_name="User",
        username="testuser",
        tariff=TariffType.FREE,
        tariff_valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        has_access=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def premium_user(db_session: AsyncSession) -> User:
    """Create a premium test user"""
    user = User(
        telegram_id=67890,
        first_name="Premium",
        last_name="User",
        username="premiumuser",
        tariff=TariffType.PREMIUM,
        tariff_valid_until=datetime.now(timezone.utc) + timedelta(days=365),
        has_access=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def sample_course_json() -> str:
    """Sample course JSON for testing"""
    return '''
    {
        "name": "English Grammar Basics",
        "description": "Introduction to English grammar",
        "lessons": [
            {
                "title": "Present Simple",
                "description": "Learn present simple tense",
                "activities": [
                    {
                        "type": "explanation",
                        "title": "What is Present Simple?",
                        "content": "Present simple is used for habits and facts."
                    },
                    {
                        "type": "quiz",
                        "title": "Practice Quiz",
                        "questions": [
                            {
                                "text": "She ___ to school every day.",
                                "options": ["go", "goes", "going", "gone"],
                                "correct": 1
                            }
                        ]
                    }
                ]
            }
        ]
    }
    '''


@pytest.fixture
def malformed_json() -> str:
    """Malformed JSON for testing error handling"""
    return '''
    {
        "name": "Test Course",
        "description": "Test description",
        "lessons": [
            {
                "title": "Lesson 1",
                "activities": [
                    {"type": "quiz", "title": "Quiz 1"
    '''


@pytest.fixture
def truncated_json() -> str:
    """Truncated JSON for testing recovery"""
    return '''
    {
        "name": "Incomplete Course",
        "description": "This JSON is cut off",
        "lessons": [
            {
                "title": "Lesson 1",
                "activities": [
                    {
                        "type": "explanation",
                        "content": "Some content here
    '''
