"""
PostgreSQL fetcher.
Инвентаризирует схемы, таблицы, представления и функции/процедуры.
Аутентификация: token = "username:password"
Использует asyncpg (уже в зависимостях воркера).
"""
import logging

import asyncpg

log = logging.getLogger(__name__)

PROC_SNIPPET_LEN = 1000

# Системные схемы PostgreSQL — пропускаем
SYSTEM_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast", "pg_temp_1", "pg_toast_temp_1"}


def _parse_auth(token: str) -> tuple[str, str]:
    if ":" not in token:
        raise ValueError("PostgreSQL token must be 'username:password'")
    username, password = token.split(":", 1)
    return username, password


async def fetch_postgresql(
    host: str,
    port: int,
    token: str,
    db_name: str,
    schema_filter: str | None = None,
) -> list[dict]:
    """
    Асинхронная инвентаризация PostgreSQL.
    Возвращает список схем:
    [{schema, tables: [{name, type, columns}], procs: [{name, definition_snippet}]}]
    """
    username, password = _parse_auth(token)

    log.info(f"Connecting to PostgreSQL {host}:{port}/{db_name} as {username}")
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=db_name,
        timeout=10,
    )

    results = []

    try:
        # Получаем схемы
        if schema_filter:
            schemas = [schema_filter]
        else:
            rows = await conn.fetch(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT LIKE 'pg_%' AND schema_name != 'information_schema' "
                "ORDER BY schema_name"
            )
            schemas = [r["schema_name"] for r in rows]

        log.info(f"Found schemas: {schemas}")

        for schema in schemas:
            if schema in SYSTEM_SCHEMAS:
                continue

            # Таблицы и представления
            raw_tables = await conn.fetch(
                "SELECT table_name, table_type FROM information_schema.tables "
                "WHERE table_schema = $1 ORDER BY table_type, table_name",
                schema,
            )

            tables = []
            for t in raw_tables:
                tname = t["table_name"]
                ttype = "VIEW" if t["table_type"] == "VIEW" else "TABLE"

                cols = await conn.fetch(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = $1 AND table_name = $2 "
                    "ORDER BY ordinal_position",
                    schema, tname,
                )
                columns = [
                    {
                        "name": c["column_name"],
                        "data_type": c["data_type"],
                        "nullable": c["is_nullable"] == "YES",
                    }
                    for c in cols
                ]
                tables.append({"name": tname, "type": ttype, "columns": columns})

            # Функции и процедуры
            raw_procs = await conn.fetch(
                "SELECT routine_name, routine_type "
                "FROM information_schema.routines "
                "WHERE routine_schema = $1 AND routine_type IN ('FUNCTION', 'PROCEDURE') "
                "ORDER BY routine_name",
                schema,
            )

            procs = []
            seen_procs: set[str] = set()
            for p in raw_procs:
                pname = p["routine_name"]
                if pname in seen_procs:
                    continue  # перегруженные функции — берём одну
                seen_procs.add(pname)

                snippet = None
                try:
                    row = await conn.fetchrow(
                        "SELECT LEFT(pg_get_functiondef(p.oid), $1) AS def "
                        "FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid "
                        "WHERE n.nspname = $2 AND p.proname = $3 LIMIT 1",
                        PROC_SNIPPET_LEN, schema, pname,
                    )
                    if row:
                        snippet = row["def"]
                except Exception:
                    pass

                procs.append({"name": pname, "definition_snippet": snippet})

            results.append({"schema": schema, "tables": tables, "procs": procs})

        log.info(
            f"PostgreSQL {db_name}: {len(results)} schemas, "
            f"{sum(len(s['tables']) for s in results)} tables/views, "
            f"{sum(len(s['procs']) for s in results)} procs"
        )

    finally:
        await conn.close()

    return results
