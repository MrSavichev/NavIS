"""
Парсер OpenAPI / Swagger (JSON/YAML).
Создаёт Service → Interface → Method в БД.
"""
import json
import logging

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


def _load_spec(content: str) -> dict | None:
    try:
        return yaml.safe_load(content)
    except Exception:
        pass
    try:
        return json.loads(content)
    except Exception:
        return None


def _is_openapi(spec: dict) -> bool:
    return isinstance(spec, dict) and (
        "openapi" in spec or "swagger" in spec
    )


async def parse_and_save(
    content: str,
    file_path: str,
    file_url: str,
    system_id: str,
    db: AsyncSession,
) -> dict:
    """
    Парсит спецификацию и сохраняет в БД.
    Возвращает {"service_name": ..., "methods_created": N, "skipped": N}
    """
    # Импорты здесь чтобы не тянуть зависимости бэкенда напрямую
    from sqlalchemy import select
    from worker.models import Service, Interface, Method, Source

    spec = _load_spec(content)
    if not spec or not _is_openapi(spec):
        log.info(f"  Skipping {file_path}: not an OpenAPI spec")
        return {"skipped": True}

    # Название сервиса из info.title или имени файла
    info = spec.get("info", {})
    service_name = info.get("title") or file_path.split("/")[-1].replace(".yaml", "").replace(".yml", "").replace(".json", "")
    version = info.get("version", "1.0")

    log.info(f"  Parsing: {service_name} v{version} ({file_path})")

    # Найти или создать Service
    result = await db.execute(
        select(Service).where(Service.system_id == system_id, Service.name == service_name)
    )
    service = result.scalar_one_or_none()
    if not service:
        service = Service(
            system_id=system_id,
            name=service_name,
            description=info.get("description"),
        )
        db.add(service)
        await db.flush()

    # Найти или создать Interface
    result = await db.execute(
        select(Interface).where(Interface.service_id == service.id, Interface.version == version)
    )
    interface = result.scalar_one_or_none()
    if not interface:
        interface = Interface(
            service_id=service.id,
            name=f"{service_name} API",
            type="http",
            version=version,
            spec_ref=file_url,
        )
        db.add(interface)
        await db.flush()

    # Создать/обновить методы
    paths = spec.get("paths", {})
    methods_created = 0

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for http_method, operation in path_item.items():
            if http_method not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue
            if not isinstance(operation, dict):
                continue

            name = operation.get("operationId") or f"{http_method.upper()} {path}"
            description = operation.get("summary") or operation.get("description")

            # Request schema
            request_schema = None
            rb = operation.get("requestBody", {})
            if rb:
                content_types = rb.get("content", {})
                for ct, ct_data in content_types.items():
                    request_schema = ct_data.get("schema")
                    break

            # Response schema (берём первый 2xx)
            response_schema = None
            responses = operation.get("responses", {})
            for code, resp_data in responses.items():
                if str(code).startswith("2") and isinstance(resp_data, dict):
                    content_types = resp_data.get("content", {})
                    for ct, ct_data in content_types.items():
                        response_schema = ct_data.get("schema")
                        break
                    break

            # Дедупликация: ищем существующий метод
            result = await db.execute(
                select(Method).where(
                    Method.interface_id == interface.id,
                    Method.path == path,
                    Method.http_method == http_method.upper(),
                )
            )
            method = result.scalar_one_or_none()
            if not method:
                method = Method(
                    interface_id=interface.id,
                    name=name,
                    http_method=http_method.upper(),
                    path=path,
                    description=description,
                    request_schema=request_schema,
                    response_schema=response_schema,
                )
                db.add(method)
                await db.flush()
                methods_created += 1

                # Evidence
                source = Source(
                    method_id=method.id,
                    type="git",
                    ref=file_url,
                )
                db.add(source)

    log.info(f"  Created {methods_created} methods for {service_name}")
    return {
        "skipped": False,
        "service_name": service_name,
        "methods_created": methods_created,
    }
