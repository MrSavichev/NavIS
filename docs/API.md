# NavIS — API Reference

**Версия:** 0.3.0
**Base URL:** `http://<host>/api/v1`
**Интерактивная документация:** `http://<host>/api/docs` (Swagger UI) · `http://<host>/api/redoc`

---

## Оглавление

1. [Иерархия данных](#иерархия-данных)
2. [Health](#health)
3. [Systems — Информационные системы](#systems)
4. [Services — Сервисы](#services)
5. [Interfaces — Интерфейсы](#interfaces)
6. [Methods — Методы API](#methods)
7. [Sources — Источники (evidence)](#sources)
8. [Graph — Граф зависимостей](#graph)
9. [Search — Поиск](#search)
10. [Ingest — Импорт из источников](#ingest)

---

## Иерархия данных

```
System (Информационная система)
└── Service (Микросервис)
    └── Interface (API интерфейс: HTTP / gRPC)
        └── Method (Эндпоинт / операция)
            └── Source (Evidence — откуда взяты данные)
```

Каждый `Source` хранит ссылку на файл в Git или страницу Confluence, из которых метод был импортирован.

---

## Health

### `GET /api/health`

Проверка работоспособности бэкенда.

**Response `200`**
```json
{ "status": "ok", "service": "navis-backend" }
```

---

## Systems

### `GET /api/v1/systems/`

Список всех информационных систем с количеством сервисов.

**Response `200`** — массив `SystemListOut`
```json
[
  {
    "id": "uuid",
    "name": "Billing",
    "owner": "team-billing",
    "tags": ["payments", "core"],
    "environments": ["prod", "staging"],
    "service_count": 3
  }
]
```

---

### `GET /api/v1/systems/{system_id}`

Полная информация о системе.

**Response `200`** — `SystemOut`
```json
{
  "id": "uuid",
  "name": "Billing",
  "description": "Сервис биллинга",
  "owner": "team-billing",
  "tags": ["payments"],
  "environments": ["prod"],
  "created_at": "2026-03-20T10:00:00",
  "updated_at": "2026-03-20T10:00:00"
}
```

---

### `POST /api/v1/systems/`

Создание новой системы.

**Request body** — `SystemCreate`
```json
{
  "name": "Billing",
  "description": "Сервис биллинга",
  "owner": "team-billing",
  "tags": ["payments", "core"],
  "environments": ["prod", "staging"]
}
```
Обязательные поля: `name`.

**Response `201`** — `SystemOut`

---

### `PATCH /api/v1/systems/{system_id}`

Обновление системы (частичное — передаются только изменяемые поля).

**Request body** — `SystemUpdate` (все поля опциональны)
```json
{
  "name": "Billing v2",
  "owner": "team-payments"
}
```

**Response `200`** — `SystemOut`

---

### `DELETE /api/v1/systems/{system_id}`

Удаление системы вместе со всеми сервисами, интерфейсами и методами (cascade).

**Response `204`** — No Content

---

## Services

### `GET /api/v1/systems/{system_id}/services/`

Список сервисов системы, отсортированных по имени.

**Response `200`** — массив `ServiceOut`
```json
[
  {
    "id": "uuid",
    "system_id": "uuid",
    "name": "payment-service",
    "description": "Приём платежей",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### `POST /api/v1/systems/{system_id}/services/`

Создание сервиса.

**Request body** — `ServiceCreate`
```json
{ "name": "payment-service", "description": "Приём платежей" }
```

**Response `201`** — `ServiceOut`

---

### `PATCH /api/v1/systems/{system_id}/services/{service_id}`

Обновление сервиса.

**Request body** — `ServiceUpdate`
```json
{ "name": "payment-service-v2", "description": "Обновлённое описание" }
```

**Response `200`** — `ServiceOut`

---

### `DELETE /api/v1/systems/{system_id}/services/{service_id}`

Удаление сервиса (cascade — удаляет интерфейсы и методы).

**Response `204`**

---

## Interfaces

Интерфейс — это конкретный API сервиса (HTTP REST, gRPC, AsyncAPI и т.д.) с версией.

### `GET /api/v1/services/{service_id}/interfaces/`

Список интерфейсов сервиса.

**Response `200`** — массив `InterfaceOut`
```json
[
  {
    "id": "uuid",
    "service_id": "uuid",
    "name": "payment-service HTTP API",
    "type": "http",
    "version": "2.1.0",
    "spec_ref": "https://github.com/org/repo/blob/main/api/openapi.yaml",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### `POST /api/v1/services/{service_id}/interfaces/`

Создание интерфейса.

**Request body** — `InterfaceCreate`
```json
{
  "name": "payment-service HTTP API",
  "type": "http",
  "version": "2.1.0",
  "spec_ref": "https://github.com/org/repo/blob/main/api/openapi.yaml"
}
```
`type` — одно из: `http`, `grpc`, `asyncapi`.

**Response `201`** — `InterfaceOut`

---

### `PATCH /api/v1/services/{service_id}/interfaces/{interface_id}`

Обновление интерфейса.

**Request body** — `InterfaceUpdate` (все поля опциональны)
```json
{ "version": "2.2.0", "spec_ref": "https://..." }
```

**Response `200`** — `InterfaceOut`

---

### `DELETE /api/v1/services/{service_id}/interfaces/{interface_id}`

Удаление интерфейса (cascade — удаляет методы).

**Response `204`**

---

### `GET /api/v1/interfaces/{interface_id}` *(прямой доступ)*

Получить интерфейс без знания `service_id`. Используется фронтендом на странице метода.

**Response `200`** — `InterfaceOut`

---

## Methods

Метод — конкретный эндпоинт или RPC-операция интерфейса.

### `GET /api/v1/interfaces/{interface_id}/methods/`

Список методов интерфейса, отсортированных по пути.

**Response `200`** — массив `MethodOut`
```json
[
  {
    "id": "uuid",
    "interface_id": "uuid",
    "name": "createPayment",
    "http_method": "POST",
    "path": "/api/v1/payments",
    "description": "Создать платёж",
    "request_schema": { "type": "object", "properties": { "amount": { "type": "number" } } },
    "response_schema": { "type": "object", "properties": { "id": { "type": "string" } } },
    "examples": [],
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### `GET /api/v1/interfaces/{interface_id}/methods/{method_id}`

Получить метод.

**Response `200`** — `MethodOut`

---

### `POST /api/v1/interfaces/{interface_id}/methods/`

Создать метод вручную.

**Request body** — `MethodCreate`
```json
{
  "name": "createPayment",
  "http_method": "POST",
  "path": "/api/v1/payments",
  "description": "Создать платёж",
  "request_schema": { "type": "object" },
  "response_schema": { "type": "object" },
  "examples": []
}
```

**Response `201`** — `MethodOut`

---

### `PATCH /api/v1/interfaces/{interface_id}/methods/{method_id}`

Обновить метод.

**Request body** — `MethodUpdate` (все поля опциональны)
```json
{ "description": "Обновлённое описание", "path": "/api/v2/payments" }
```

**Response `200`** — `MethodOut`

---

### `DELETE /api/v1/interfaces/{interface_id}/methods/{method_id}`

Удалить метод.

**Response `204`**

---

## Sources

Evidence — ссылки на первоисточники данных о методе (Git-файл, Confluence-страница).

### `GET /api/v1/methods/{method_id}/sources`

Список источников метода, отсортированных по дате сбора (новые первые).

**Response `200`** — массив `SourceOut`
```json
[
  {
    "id": "uuid",
    "method_id": "uuid",
    "type": "git",
    "ref": "https://github.com/org/repo/blob/main/api/openapi.yaml",
    "hash": null,
    "collected_at": "2026-03-20T10:00:00"
  }
]
```

`type` — одно из: `git`, `confluence`, `db`.

---

## Graph

### `GET /api/v1/graph/`

Граф зависимостей для визуализации в Cytoscape.js.

**Query params:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `depth` | int | 2 | Глубина графа: 1 = только системы, 2 = +сервисы, 3 = +интерфейсы |
| `system_id` | string | — | Фильтр по конкретной системе |

**Response `200`** — `GraphOut`
```json
{
  "nodes": [
    { "id": "uuid", "type": "system", "label": "Billing" },
    { "id": "uuid", "type": "service", "label": "payment-service" },
    { "id": "ext:SomeExternalSystem", "type": "external", "label": "SomeExternalSystem" }
  ],
  "edges": [
    { "id": "uuid", "source": "system-id", "target": "service-id", "kind": "contains" },
    { "id": "uuid", "source": "service-id", "target": "ext:SomeExternalSystem", "kind": "REST/POST" }
  ]
}
```

**Типы узлов (`node.type`):**

| Тип | Описание |
|---|---|
| `system` | Информационная система |
| `service` | Сервис внутри ИС |
| `interface` | API интерфейс |
| `method` | Эндпоинт / операция |
| `external` | Внешний сервис, не зарегистрированный в каталоге (из draw.io диаграмм Confluence) |

**Типы рёбер (`edge.kind`):** `contains`, `calls`, `depends-on`, а также значения из label draw.io диаграмм (например, `REST/POST →`, `gRPC`).

---

## Search

### `GET /api/v1/search/`

Полнотекстовый поиск по системам, сервисам и методам.

**Query params:**

| Параметр | Тип | Описание |
|---|---|---|
| `q` | string | Поисковый запрос (минимум 2 символа) |

**Response `200`** — массив `SearchResult`
```json
[
  {
    "id": "uuid",
    "type": "method",
    "label": "POST /api/v1/payments",
    "description": "Создать платёж",
    "path": "Billing / payment-service / HTTP API",
    "url": "/systems/uuid/..."
  }
]
```

`type` — одно из: `system`, `service`, `method`.

---

## Ingest

Управление источниками данных и заданиями импорта.

Поддерживаются два типа источников:
- **`git`** — репозитории GitHub / GitLab / Bitbucket Server; парсит OpenAPI/Swagger YAML/JSON
- **`confluence`** — Confluence Server; извлекает draw.io диаграммы (архитектурные схемы) и строит граф зависимостей

### `GET /api/v1/systems/{system_id}/sources/`

Список источников системы.

**Response `200`** — массив `IngestSourceOut`
```json
[
  {
    "id": "uuid",
    "system_id": "uuid",
    "name": "Main API repo",
    "type": "git",
    "provider": "github",
    "repo_url": "https://github.com/org/repo",
    "branch": "main",
    "path_filter": "api/**/*.yaml",
    "confluence_url": null,
    "space_key": null,
    "last_run_at": "2026-03-20T10:00:00",
    "last_run_status": "done",
    "last_run_error": null,
    "created_at": "..."
  }
]
```

---

### `POST /api/v1/systems/{system_id}/sources/`

Создать источник.

#### Git-источник

**Request body**
```json
{
  "name": "Main API repo",
  "type": "git",
  "provider": "github",
  "repo_url": "https://github.com/org/repo",
  "branch": "main",
  "path_filter": "api/**/*.yaml",
  "token": "ghp_..."
}
```

Поддерживаемые провайдеры (`provider`): `github`, `gitlab`, `bitbucket`.
Для Bitbucket Server формат URL: `https://bitbucket.company.com/projects/KEY/repos/my-repo`.

#### DB-источник (MS SQL Server / PostgreSQL)

**Request body**
```json
{
  "name": "BackOffice DB",
  "type": "mssql",
  "db_host": "msa-db01.company.com",
  "db_port": 1433,
  "db_name": "BackOffice",
  "db_schema": "dbo",
  "token": "svc_navis:password"
}
```

Для PostgreSQL: `"type": "postgresql"`, `"db_port": 5432`, `"db_schema": "public"` (или null — все схемы).

Для ClickHouse: `"type": "clickhouse"`, `"db_port": 9000`. Поле `db_name` — конкретная база данных (null = все пользовательские). Поле `db_schema` не используется — в ClickHouse нет sub-schemas.

Поля DB-источника:
| Поле | Обязательно | Описание |
|---|---|---|
| `db_host` | ✓ | Хост сервера БД |
| `db_port` | — | Порт (по умолчанию: 1433 для mssql, 5432 для postgresql) |
| `db_name` | ✓ | Имя базы данных |
| `db_schema` | — | Конкретная схема (null = все пользовательские схемы) |
| `token` | ✓ | Аутентификация в формате `username:password` |

DB-коннектор создаёт в каталоге:
- **Service**: `DB: {db_name} [{driver}]`
- **Interface**: имя схемы, `type` = `mssql` / `postgresql`
- **Method**: таблица / VIEW / процедура; `http_method` = `TABLE` / `VIEW` / `PROC`; `description` = список колонок или фрагмент кода

#### Confluence-источник

**Request body**
```json
{
  "name": "Architecture diagrams",
  "type": "confluence",
  "confluence_url": "https://wiki.company.com",
  "space_key": "MYSPACE",
  "token": "username:password",
  "path_filter": "Схема сервисов"
}
```

Поля Confluence:
| Поле | Обязательно | Описание |
|---|---|---|
| `confluence_url` | ✓ | Базовый URL Confluence Server (без слеша в конце) |
| `space_key` | ✓ | Ключ пространства (Space Key) |
| `token` | ✓ | Basic auth в формате `username:password` |
| `path_filter` | — | Фильтр по заголовку страницы (частичное совпадение) |

Confluence-коннектор находит на страницах вложения с `mediaType: application/vnd.jgraph.mxfile` (draw.io диаграммы), парсит сущности и связи, сохраняет рёбра в граф. Сущности сопоставляются с сервисами каталога по имени; несопоставленные создаются как узлы типа `external`.

**Response `201`** — `IngestSourceOut`

---

### `DELETE /api/v1/systems/{system_id}/sources/{source_id}`

Удалить источник.

**Response `204`**

---

### `POST /api/v1/systems/{system_id}/sources/{source_id}/run`

Запустить импорт. Создаёт `IngestJob` и отправляет задачу в Redis-очередь (`navis:ingest:queue`). Worker подхватывает задачу асинхронно.

**Response `202`** — `IngestJobOut`
```json
{
  "id": "uuid",
  "source_id": "uuid",
  "status": "pending",
  "started_at": null,
  "finished_at": null,
  "files_found": 0,
  "methods_created": 0,
  "error": null,
  "log": null,
  "created_at": "..."
}
```

Статусы: `pending` → `running` → `done` | `error`.

Для Confluence-источника поле `files_found` = количество найденных draw.io диаграмм, `methods_created` = количество созданных рёбер в графе.

---

### `GET /api/v1/ingest/jobs`

Список заданий импорта.

**Query params:**

| Параметр | Тип | Описание |
|---|---|---|
| `source_id` | string | Фильтр по источнику |
| `limit` | int | Максимум записей (по умолчанию 20) |

**Response `200`** — массив `IngestJobOut`

---

### `GET /api/v1/ingest/jobs/{job_id}`

Статус конкретного задания.

**Response `200`** — `IngestJobOut`

---

## Прямой доступ *(без parent-id)*

Эндпоинты для случаев когда известен только ID сущности, без знания родительского ID.

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/v1/interfaces/{interface_id}` | Получить интерфейс |
| GET | `/api/v1/services/{service_id}` | Получить сервис |
| GET | `/api/v1/methods/{method_id}/sources` | Источники метода |

---

## Схемы данных

### System
| Поле | Тип | Описание |
|---|---|---|
| id | string (UUID) | Идентификатор |
| name | string | Название ИС |
| description | string? | Описание |
| owner | string? | Владелец / команда |
| tags | string[] | Теги для категоризации |
| environments | string[] | Окружения (prod, staging, dev) |
| created_at / updated_at | datetime | Временны́е метки |

### Method
| Поле | Тип | Описание |
|---|---|---|
| id | string (UUID) | Идентификатор |
| interface_id | string (UUID) | Родительский интерфейс |
| name | string | Название операции (или operationId из OpenAPI) |
| http_method | string? | GET / POST / PUT / PATCH / DELETE |
| path | string? | URL путь (/api/v1/resource/{id}) |
| description | string? | Описание из спецификации |
| request_schema | object? | JSON Schema тела запроса |
| response_schema | object? | JSON Schema первого 2xx ответа |
| examples | array | Примеры (зарезервировано) |

### IngestJob — статусы
| Статус | Описание |
|---|---|
| `pending` | Задача создана, ожидает Worker |
| `running` | Worker активно обрабатывает |
| `done` | Успешно завершено |
| `error` | Завершено с ошибкой (текст в поле `error`) |

---

## Архитектура

```
Browser
  │
  ▼
Nginx :80
  ├── /api/*     → FastAPI Backend :8000  ──→ PostgreSQL
  ├── /api/docs  → Swagger UI
  └── /*         → React Frontend :3000

FastAPI Backend ──→ Redis (push задач)
                         │
                         ▼
                    Worker (blpop)
                         │
              ┌──────────┴──────────┐
              │                     │
         Git коннектор      Confluence коннектор
         (GitHub/GitLab/    (Confluence Server,
          Bitbucket)         Basic auth)
              │                     │
         OpenAPI/Swagger     draw.io attachments
         YAML/JSON парсер    (vnd.jgraph.mxfile)
              │                     │
              └──────────┬──────────┘
                         ▼
                    PostgreSQL
                    (Services, Edges, Jobs)
```
