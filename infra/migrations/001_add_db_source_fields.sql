-- Migration 001: добавление полей для DB-источников (mssql, postgresql, clickhouse)
-- Применять на существующих инсталляциях (create_all не добавляет колонки в existing таблицы)
-- Новые инсталляции получают эти поля автоматически через create_all

ALTER TABLE ingest_sources ADD COLUMN IF NOT EXISTS db_host VARCHAR(255);
ALTER TABLE ingest_sources ADD COLUMN IF NOT EXISTS db_port INTEGER;
ALTER TABLE ingest_sources ADD COLUMN IF NOT EXISTS db_name VARCHAR(255);
ALTER TABLE ingest_sources ADD COLUMN IF NOT EXISTS db_schema VARCHAR(255);

-- Также добавляем confluence_url и space_key если их нет (на случай старых инсталляций)
ALTER TABLE ingest_sources ADD COLUMN IF NOT EXISTS confluence_url TEXT;
ALTER TABLE ingest_sources ADD COLUMN IF NOT EXISTS space_key VARCHAR(100);
