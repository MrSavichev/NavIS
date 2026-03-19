"""
NavIS Ingest Worker
Слушает очередь Redis и запускает парсеры источников.
"""
import asyncio
import json
import logging

import redis.asyncio as aioredis

from worker.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

QUEUE_KEY = "navis:ingest:queue"


async def process_task(task: dict):
    task_type = task.get("type")
    log.info(f"Processing task: {task_type} — {task}")

    if task_type == "ingest:openapi":
        from worker.parsers.openapi import parse_openapi
        await parse_openapi(task)
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
