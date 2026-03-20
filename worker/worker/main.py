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
from worker.models import IngestJob, IngestSource, Service, Interface, Method, Edge

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


async def handle_ingest_db(task: dict, db: AsyncSession, driver: str):
    """
    Общий handler для DB-коннекторов (mssql, postgresql).
    Логика одинакова — отличается только fetcher.
    """
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

    host = task.get("db_host")
    port = int(task.get("db_port") or (1433 if driver == "mssql" else 5432))
    db_name = task.get("db_name")
    schema_filter = task.get("db_schema") or None
    token = task.get("token")

    log.info(f"[job={job_id}] {driver.upper()} ingest: {host}:{port}/{db_name} schema={schema_filter}")

    try:
        if driver == "mssql":
            from worker.fetchers.mssql import fetch_mssql_sync
            loop = asyncio.get_event_loop()
            schemas_data = await loop.run_in_executor(
                None, fetch_mssql_sync, host, port, token, db_name, schema_filter
            )
        elif driver == "postgresql":
            from worker.fetchers.postgresql import fetch_postgresql
            schemas_data = await fetch_postgresql(host, port, token, db_name, schema_filter)
        elif driver == "clickhouse":
            from worker.fetchers.clickhouse import fetch_clickhouse_sync
            loop = asyncio.get_event_loop()
            # db_name используется как фильтр базы данных; schema не применима
            schemas_data = await loop.run_in_executor(
                None, fetch_clickhouse_sync, host, port, token, db_name or None
            )
        else:
            raise ValueError(f"Unknown DB driver: {driver}")

        log_lines = []
        total_objects = 0

        for schema_info in schemas_data:
            schema = schema_info["schema"]

            # Service: "DB: db_name [driver]"
            svc_name = f"DB: {db_name} [{driver}]"
            svc_result = await db.execute(
                select(Service).where(Service.system_id == system_id, Service.name == svc_name)
            )
            svc = svc_result.scalar_one_or_none()
            if not svc:
                svc = Service(
                    system_id=system_id,
                    name=svc_name,
                    description=f"{driver.upper()} база данных: {db_name} на {host}:{port}",
                )
                db.add(svc)
                await db.flush()

            # Interface: схема
            iface_result = await db.execute(
                select(Interface).where(Interface.service_id == svc.id, Interface.name == schema)
            )
            iface = iface_result.scalar_one_or_none()
            if not iface:
                iface = Interface(
                    service_id=svc.id,
                    name=schema,
                    type=driver,
                    spec_ref=f"{driver}://{host}:{port}/{db_name}/{schema}",
                )
                db.add(iface)
                await db.flush()

            for table in schema_info["tables"]:
                tname = table["name"]
                ttype = table["type"]
                col_summary = ", ".join(
                    f"{c['name']} {c['data_type']}" + ("?" if c["nullable"] else "")
                    for c in table["columns"][:20]
                )
                if len(table["columns"]) > 20:
                    col_summary += f", ... (+{len(table['columns']) - 20})"

                exists = await db.execute(
                    select(Method).where(Method.interface_id == iface.id, Method.name == tname)
                )
                if not exists.scalar_one_or_none():
                    db.add(Method(
                        interface_id=iface.id,
                        name=tname,
                        http_method=ttype,
                        path=f"{schema}.{tname}",
                        description=col_summary or None,
                    ))
                    total_objects += 1
                    log_lines.append(f"OK   {ttype} {schema}.{tname} ({len(table['columns'])} cols)")

            for proc in schema_info["procs"]:
                pname = proc["name"]
                exists = await db.execute(
                    select(Method).where(Method.interface_id == iface.id, Method.name == pname)
                )
                if not exists.scalar_one_or_none():
                    db.add(Method(
                        interface_id=iface.id,
                        name=pname,
                        http_method="PROC",
                        path=f"{schema}.{pname}",
                        description=proc.get("definition_snippet"),
                    ))
                    total_objects += 1
                    log_lines.append(f"OK   PROC {schema}.{pname}")

        await db.commit()

        job.files_found = len(schemas_data)
        job.methods_created = total_objects
        job.status = "done"
        job.finished_at = utcnow()
        job.log = "\n".join(log_lines)
        await db.commit()

        log.info(f"[job={job_id}] Done. schemas={len(schemas_data)} objects={total_objects}")

    except Exception as e:
        log.exception(f"[job={job_id}] {driver.upper()} ingest failed: {e}")
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
        elif task_type == "ingest:mssql":
            await handle_ingest_db(task, db, driver="mssql")
        elif task_type == "ingest:postgresql":
            await handle_ingest_db(task, db, driver="postgresql")
        elif task_type == "ingest:clickhouse":
            await handle_ingest_db(task, db, driver="clickhouse")
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
