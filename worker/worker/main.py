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
from worker.models import IngestJob, IngestSource, Service, Edge

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


async def handle_ingest_confluence(task: dict, db: AsyncSession):
    """Обрабатывает ingest:confluence — скачивает draw.io из Confluence и сохраняет рёбра."""
    job_id = task.get("job_id")
    source_id = task.get("source_id")
    system_id = task.get("system_id")

    result = await db.execute(select(IngestJob).where(IngestJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        log.error(f"IngestJob {job_id} not found")
        return

    job.status = "running"
    job.started_at = utcnow()
    await db.commit()

    log.info(f"[job={job_id}] Starting Confluence ingest: {task.get('confluence_url')} space={task.get('space_key')}")

    try:
        from worker.fetchers.confluence import fetch_drawio_attachments
        from worker.parsers.drawio import parse_drawio_xml, match_entity_to_service

        diagrams = await fetch_drawio_attachments(
            base_url=task["confluence_url"],
            space_key=task["space_key"],
            token=task["token"],
            page_filter=task.get("page_filter"),
        )

        # Загружаем все сервисы системы для сопоставления
        svc_result = await db.execute(select(Service).where(Service.system_id == system_id))
        services = svc_result.scalars().all()

        edges_created = 0
        log_lines = []

        for diagram in diagrams:
            parsed = parse_drawio_xml(diagram["content"])
            page_label = f"{diagram['page_title']} / {diagram['filename']}"

            if not parsed.edges:
                log_lines.append(f"SKIP {page_label} (no edges)")
                continue

            for edge in parsed.edges:
                src_id = match_entity_to_service(edge.source_name, services)
                tgt_id = match_entity_to_service(edge.target_name, services)

                # Если сервис не найден — используем синтетический ID
                src_node_id = src_id or f"ext:{edge.source_name}"
                tgt_node_id = tgt_id or f"ext:{edge.target_name}"
                src_type = "service" if src_id else "external"
                tgt_type = "service" if tgt_id else "external"

                # Проверяем дубликат
                existing = await db.execute(
                    select(Edge).where(
                        Edge.from_id == src_node_id,
                        Edge.to_id == tgt_node_id,
                        Edge.kind == edge.label,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                db.add(Edge(
                    from_id=src_node_id,
                    from_type=src_type,
                    to_id=tgt_node_id,
                    to_type=tgt_type,
                    kind=edge.label,
                    confidence=1.0,
                ))
                edges_created += 1
                log_lines.append(
                    f"EDGE {edge.source_name} → {edge.target_name} [{edge.label}]"
                    + ("" if src_id else " (src unmatched)")
                    + ("" if tgt_id else " (tgt unmatched)")
                )

        await db.commit()

        job.files_found = len(diagrams)
        job.methods_created = edges_created
        job.status = "done"
        job.finished_at = utcnow()
        job.log = "\n".join(log_lines)
        await db.commit()

        log.info(f"[job={job_id}] Done. diagrams={len(diagrams)} edges={edges_created}")

    except Exception as e:
        log.exception(f"[job={job_id}] Confluence ingest failed: {e}")
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
        elif task_type == "ingest:confluence":
            await handle_ingest_confluence(task, db)
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
