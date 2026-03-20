import os

# Подменяем DATABASE_URL ДО импорта app — иначе SQLAlchemy попытается загрузить asyncpg
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from contextlib import asynccontextmanager

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.database import Base, get_db
from app.main import app

# Отключаем lifespan — он пытается подключиться к PostgreSQL
@asynccontextmanager
async def noop_lifespan(_app):
    yield

app.router.lifespan_context = noop_lifespan

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await engine.dispose()
