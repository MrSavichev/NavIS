"""
MS SQL Server fetcher.
Инвентаризирует схемы, таблицы, представления и хранимые процедуры.
Аутентификация: token = "username:password"
Запускается синхронно через asyncio.run_in_executor (pymssql не поддерживает async).
"""
import logging

log = logging.getLogger(__name__)

PROC_SNIPPET_LEN = 1000  # символов из тела процедуры


def _parse_auth(token: str) -> tuple[str, str]:
    if ":" not in token:
        raise ValueError("MSSQL token must be 'username:password'")
    username, password = token.split(":", 1)
    return username, password


def fetch_mssql_sync(
    host: str,
    port: int,
    token: str,
    db_name: str,
    schema_filter: str | None = None,
) -> list[dict]:
    """
    Синхронная функция — вызывать через run_in_executor.
    Возвращает список схем, каждая содержит:
    {
        schema: str,
        tables: [{name, type, columns: [{name, data_type, nullable}]}],
        procs:  [{name, definition_snippet}]
    }
    """
    import pymssql  # импорт здесь — не падаем если не установлен

    username, password = _parse_auth(token)

    log.info(f"Connecting to MSSQL {host}:{port}/{db_name} as {username}")
    conn = pymssql.connect(
        server=host,
        port=port,
        user=username,
        password=password,
        database=db_name,
        login_timeout=10,
        charset="UTF-8",
    )

    results = []

    try:
        cursor = conn.cursor(as_dict=True)

        # Получаем схемы
        if schema_filter:
            cursor.execute(
                "SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = %s ORDER BY TABLE_SCHEMA",
                (schema_filter,),
            )
        else:
            cursor.execute(
                "SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES "
                "ORDER BY TABLE_SCHEMA"
            )
        schemas = [row["TABLE_SCHEMA"] for row in cursor.fetchall()]
        log.info(f"Found schemas: {schemas}")

        for schema in schemas:
            # Таблицы и представления
            cursor.execute(
                "SELECT TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = %s ORDER BY TABLE_TYPE, TABLE_NAME",
                (schema,),
            )
            raw_tables = cursor.fetchall()

            tables = []
            for t in raw_tables:
                tname = t["TABLE_NAME"]
                ttype = t["TABLE_TYPE"]  # 'BASE TABLE' или 'VIEW'

                # Колонки
                cursor.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                    "ORDER BY ORDINAL_POSITION",
                    (schema, tname),
                )
                columns = [
                    {
                        "name": c["COLUMN_NAME"],
                        "data_type": c["DATA_TYPE"],
                        "nullable": c["IS_NULLABLE"] == "YES",
                    }
                    for c in cursor.fetchall()
                ]

                tables.append({
                    "name": tname,
                    "type": "VIEW" if ttype == "VIEW" else "TABLE",
                    "columns": columns,
                })

            # Хранимые процедуры
            cursor.execute(
                "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES "
                "WHERE ROUTINE_TYPE = 'PROCEDURE' AND ROUTINE_SCHEMA = %s "
                "ORDER BY ROUTINE_NAME",
                (schema,),
            )
            raw_procs = cursor.fetchall()

            procs = []
            for p in raw_procs:
                pname = p["ROUTINE_NAME"]
                snippet = None
                try:
                    cursor.execute(
                        "SELECT SUBSTRING(OBJECT_DEFINITION(OBJECT_ID(%s)), 1, %s) AS def",
                        (f"{schema}.{pname}", PROC_SNIPPET_LEN),
                    )
                    row = cursor.fetchone()
                    if row:
                        snippet = row["def"]
                except Exception:
                    pass  # процедура может быть зашифрована (WITH ENCRYPTION)
                procs.append({"name": pname, "definition_snippet": snippet})

            results.append({
                "schema": schema,
                "tables": tables,
                "procs": procs,
            })

        log.info(
            f"MSSQL {db_name}: {len(schemas)} schemas, "
            f"{sum(len(s['tables']) for s in results)} tables/views, "
            f"{sum(len(s['procs']) for s in results)} procs"
        )

    finally:
        conn.close()

    return results
