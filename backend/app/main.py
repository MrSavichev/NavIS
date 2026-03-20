import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import JSONResponse, HTMLResponse

from app.db.database import engine, Base
from app.api import systems, services, interfaces, methods, graph, search, ingest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("NavIS backend starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables verified.")
    yield
    log.info("NavIS backend shutting down.")


app = FastAPI(
    title="NavIS API",
    description="Навигатор Информационных Систем — Service Catalog & API Explorer",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.get("/api/redoc", include_in_schema=False, response_class=HTMLResponse)
async def redoc():
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="NavIS API — ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(
        "Unhandled exception on %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )

# Роутеры
app.include_router(systems.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(interfaces.router, prefix="/api/v1")
app.include_router(methods.router, prefix="/api/v1")
app.include_router(methods.direct_router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(ingest.jobs_router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "navis-backend"}
