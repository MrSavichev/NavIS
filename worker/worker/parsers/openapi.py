"""
Парсер OpenAPI / Swagger спецификаций.
Принимает задачу с URL или содержимым спецификации,
создаёт Interface + Method записи в БД.
"""
import logging
import httpx
import yaml
import json

log = logging.getLogger(__name__)


async def parse_openapi(task: dict):
    """
    task: {
        "type": "ingest:openapi",
        "interface_id": "<uuid>",
        "spec_url": "<url>",   # или
        "spec_content": "<yaml/json string>"
    }
    """
    spec = None

    if "spec_url" in task:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(task["spec_url"])
            resp.raise_for_status()
            content = resp.text
    elif "spec_content" in task:
        content = task["spec_content"]
    else:
        log.error("parse_openapi: no spec_url or spec_content in task")
        return

    # Парсим YAML или JSON
    try:
        spec = yaml.safe_load(content)
    except Exception:
        try:
            spec = json.loads(content)
        except Exception as e:
            log.error(f"Failed to parse spec: {e}")
            return

    interface_id = task.get("interface_id")
    paths = spec.get("paths", {})
    log.info(f"Parsed OpenAPI spec: {len(paths)} paths for interface {interface_id}")

    # TODO: сохранить методы в БД через SQLAlchemy
    # Будет реализовано в следующей итерации
    for path, path_item in paths.items():
        for http_method, operation in path_item.items():
            if http_method in ("get", "post", "put", "patch", "delete", "head", "options"):
                log.info(f"  {http_method.upper()} {path} — {operation.get('summary', '')}")
