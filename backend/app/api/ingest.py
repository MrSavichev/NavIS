import json
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.models.models import IngestSource, IngestJob, System
from app.schemas.ingest_schemas import IngestSourceCreate, IngestSourceOut, IngestJobOut

router = APIRouter(prefix="/systems/{system_id}/sources", tags=["ingest"])
jobs_router = APIRouter(prefix="/ingest", tags=["ingest"])


# ─── Sources CRUD ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[IngestSourceOut])
async def list_sources(system_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IngestSource).where(IngestSource.system_id == system_id).order_by(IngestSource.name)
    )
    return result.scalars().all()


@router.post("/", response_model=IngestSourceOut, status_code=201)
async def create_source(system_id: str, data: IngestSourceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.id == system_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="System not found")
    source = IngestSource(system_id=system_id, **data.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(system_id: str, source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IngestSource).where(IngestSource.id == source_id, IngestSource.system_id == system_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()


# ─── Run ingest ────────────────────────────────────────────────────────────────

@router.post("/{source_id}/run", response_model=IngestJobOut, status_code=202)
async def run_ingest(system_id: str, source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IngestSource).where(IngestSource.id == source_id, IngestSource.system_id == system_id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Создаём job
    job = IngestJob(source_id=source_id, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Кладём задачу в Redis
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    task = {
        "type": f"ingest:{source.type}",
        "job_id": job.id,
        "source_id": source.id,
        "system_id": system_id,
        # Git fields
        "repo_url": source.repo_url,
        "branch": source.branch,
        "path_filter": source.path_filter,
        "token": source.token,
        "provider": source.provider,
        # Confluence fields
        "confluence_url": source.confluence_url,
        "space_key": source.space_key,
        "page_filter": source.path_filter,
        # DB fields
        "db_host": source.db_host,
        "db_port": source.db_port,
        "db_name": source.db_name,
        "db_schema": source.db_schema,
    }
    await redis.rpush("navis:ingest:queue", json.dumps(task))
    await redis.aclose()

    return job


# ─── Job status ────────────────────────────────────────────────────────────────

@jobs_router.get("/jobs/{job_id}", response_model=IngestJobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IngestJob).where(IngestJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@jobs_router.get("/jobs", response_model=list[IngestJobOut])
async def list_jobs(source_id: str | None = None, limit: int = 20, db: AsyncSession = Depends(get_db)):
    q = select(IngestJob).order_by(IngestJob.created_at.desc()).limit(limit)
    if source_id:
        q = q.where(IngestJob.source_id == source_id)
    result = await db.execute(q)
    return result.scalars().all()
