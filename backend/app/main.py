from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.api import systems, services, interfaces, methods, graph, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы при старте (в продакшне использовать Alembic миграции)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="NavIS API",
    description="Навигатор Информационных Систем — Service Catalog & API Explorer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(systems.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(interfaces.router, prefix="/api/v1")
app.include_router(methods.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "navis-backend"}
