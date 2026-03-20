"""
ClickHouse fetcher.
Инвентаризирует базы данных, таблицы, представления и материализованные представления.
В ClickHouse нет хранимых процедур. "Схема" = база данных.
Аутентификация: token = "username:password"
Запускается через asyncio.run_in_executor (clickhouse-driver синхронный).
"""
import logging

log = logging.getLogger(__name__)

SYSTEM_DATABASES = {
    "system", "information_schema", "INFORMATION_SCHEMA",
    "_temporary_and_external_tables",
}

# Движки ClickHouse → тип объекта
def _engine_to_type(engine: str) -> str:
    if engine == "View":
        return "VIEW"
    if engine == "MaterializedView":
        return "MATVIEW"
    return "TABLE"


def _parse_auth(token: str) -> tuple[str, str]:
    if ":" not in token:
        raise ValueError("ClickHouse token must be 'username:password'")
    username, password = token.split(":", 1)
    return username, password


def fetch_clickhouse_sync(
    host: str,
    port: int,
    token: str,
    db_filter: str | None = None,
) -> list[dict]:
    """
    Синхронная функция — вызывать через run_in_executor.
    db_filter: конкретная БД для сканирования; None = все пользовательские БД.
    Возвращает список в формате [{schema, tables, procs}] — procs всегда пусто.
    """
    from clickhouse_driver import Client

    username, password = _parse_auth(token)

    log.info(f"Connecting to ClickHouse {host}:{port} as {username}")
    client = Client(
        host=host,
        port=port,
        user=username,
        password=password,
        database="default",
        connect_timeout=10,
        settings={"max_execution_time": 30},
    )

    # Получаем список баз данных
    if db_filter:
        databases = [db_filter]
    else:
        rows = client.execute(
            "SELECT name FROM system.databases "
            "WHERE name NOT IN %(excluded)s ORDER BY name",
            {"excluded": list(SYSTEM_DATABASES)},
        )
        databases = [r[0] for r in rows]

    log.info(f"ClickHouse databases to scan: {databases}")

    results = []

    for db in databases:
        # Таблицы и представления
        raw_tables = client.execute(
            "SELECT name, engine FROM system.tables "
            "WHERE database = %(db)s AND engine != 'Dictionary' "
            "ORDER BY engine, name",
            {"db": db},
        )

        tables = []
        for tname, engine in raw_tables:
            ttype = _engine_to_type(engine)

            cols = client.execute(
                "SELECT name, type FROM system.columns "
                "WHERE database = %(db)s AND table = %(tbl)s "
                "ORDER BY position",
                {"db": db, "tbl": tname},
            )
            columns = [
                {"name": c[0], "data_type": c[1], "nullable": "Nullable" in c[1]}
                for c in cols
            ]
            tables.append({"name": tname, "type": ttype, "columns": columns, "engine": engine})

        results.append({
            "schema": db,
            "tables": tables,
            "procs": [],  # ClickHouse не поддерживает хранимые процедуры
        })

        log.info(f"  DB {db}: {len(tables)} tables/views")

    return results
