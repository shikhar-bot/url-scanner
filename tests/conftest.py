import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db

# Using SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread" : False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Override DB dependency ──────────────────────────────────────

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ── Override Redis dependency ──────────────────────────────────────

class MockRedis:
    """Fake Redis that stores data in memory for tests."""
    def __init__(self):
        self.store = {}
    
    async def get(self, key):
        return self.store.get(key)
    
    async def setex(self, key, ttl, value):
        self.store[key] = value

    async def delete(self, key):
        self.store.pop(key, None)
    
    async def aclose(self):
        pass

# mock_redis_instance = MockRedis()

# async def override_get_redis():
#     return mock_redis_instance

# ── Fixtures ──────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Test HTTP client with DB override and Redis patched."""
    app.dependency_overrides[get_db] = override_get_db

    # app.dependency_overrides[get_redis] = override_get_redis

    # Patch get_redis at the source in cache.py
    mock_redis = MockRedis()
    with patch(
        "app.cache.get_redis",
        new_callable=AsyncMock,
        return_value=mock_redis
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac
    
    app.dependency_overrides.clear()