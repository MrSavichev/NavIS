"""
NavIS Ingest Worker
Слушает очередь Redis и запускает парсеры источников.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from worker.config import settings
from worker.models import IngestJob, IngestSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

QUEUE_KEY = "navis:ingest:queue"

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def handle_ingest_git(task: dict, db: AsyncSession):
    """
    Обрабатывает задачу типа ingest:git.
    task = {"type": "ingest:git", "job_id": "...", "source_id": "..."}
    """
    job_id = task.get("job_id")
    source_id = task.get("source_id")

    # Загружаем job и source из БД
    result = await db.execute(select(IngestJob).where(IngestJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        log.error(f"IngestJob {job_id} not found")
        return

    result = await db.execute(select(IngestSource).where(IngestSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        log.error(f"IngestSource {source_id} not found")
        job.status = "error"
        job.error = "Source not found"
        job.finished_at = utcnow()
        await db.commit()
        return

    # Помечаем job как running
    job.status = "running"
    job.started_at = utcnow()
    await db.commit()

    log.info(f"[job={job_id}] Starting git ingest: {source.repo_url} branch={source.branch}")

    try:
        from worker.fetchers.git import fetch_files
        from worker.parsers.openapi import parse_and_save

        files = await fetch_files(
            repo_url=source.repo_url,
            branch=source.branch or "main",
            token=source.token,
            path_filter=source.path_filter,
            provider=source.provider or "github",
        )

        log.info(f"[job={job_id}] Fetched {len(files)} files")
        job.files_found = len(files)

        total_methods = 0
        log_lines = []

        for f in files:
            result = await parse_and_save(
                content=f["content"],
                file_path=f["path"],
                file_url=f["url"],
                system_id=source.system_id,
                db=db,
            )
            if result.get("skipped"):
                log_lines.append(f"SKIP {f['path']}")
            else:
                n = result.get("methods_created", 0)
                total_methods += n
                log_lines.append(f"OK   {f['path']} → {result['service_name']} ({n} methods)")

        await db.commit()

        job.methods_created = total_methods
        job.status = "done"
        job.finished_at = utcnow()
        job.log = "\n".join(log_lines)
        await db.commit()

        log.info(f"[job={job_id}] Done. files={len(files)} methods={total_methods}")

    except Exception as e:
        log.exception(f"[job={job_id}] Ingest failed: {e}")
        job.status = "error"
        job.error = str(e)
        job.finished_at = utcnow()
        await db.commit()


async def process_task(task: dict):
    task_type = task.get("type")
    log.info(f"Processing task: {task_type}")

    async with AsyncSessionLocal() as db:
        if task_type == "ingest:git":
            await handle_ingest_git(task, db)
        else:
            log.warning(f"Unknown task type: {task_type}")


async def main():
    log.info("NavIS Worker started, listening on queue...")
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    while True:
        try:
            item = await redis.blpop(QUEUE_KEY, timeout=5)
            if item:
                _, raw = item
                task = json.loads(raw)
                await process_task(task)
        except Exception as e:
            log.error(f"Worker error: {e}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
