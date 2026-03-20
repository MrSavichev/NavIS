# NavIS — Навигатор Информационных Систем

> Service Catalog & API Explorer для SRE-инженеров и разработчиков

---

## Что это

NavIS — внутренний веб-сервис для навигации по архитектуре корпоративных информационных систем. Позволяет в одном месте видеть сервисы, их API, зависимости и связи с базами данных.

**Основные возможности:**
- Каталог ИС → Сервисы → Интерфейсы → Методы с карточками request/response
- Граф зависимостей между сервисами (включая внешние) с фильтрами по типам узлов
- Автоматический импорт из **Confluence** (draw.io архитектурные диаграммы) и **Git** (OpenAPI/Swagger)
- Ручное добавление и редактирование сущностей
- Полнотекстовый поиск по всему каталогу
- Тёмная / светлая тема

---

## Стек

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI (Python 3.11+) |
| Frontend | React + Cytoscape.js |
| База данных | PostgreSQL |
| Кэш / очередь | Redis |
| Прокси | Nginx |
| Deploy | Docker + docker-compose |
| Тесты | pytest + pytest-asyncio (SQLite in-memory) |

---

## Структура репозитория

```
NavIS/
├── backend/          — FastAPI приложение
│   ├── app/
│   │   ├── api/      — роутеры (systems, services, interfaces, methods, graph, search, ingest)
│   │   ├── models.py — SQLAlchemy модели
│   │   └── schemas/  — Pydantic схемы
│   └── tests/        — pytest тесты
├── frontend/         — React SPA
│   └── src/
│       ├── pages/    — SystemList, SystemDetail, SourcesPage, GraphPage, MethodDetail
│       └── api/      — axios клиент
├── worker/           — Ingest worker
│   └── worker/
│       ├── fetchers/ — git.py, confluence.py
│       └── parsers/  — openapi.py, drawio.py
├── infra/            — docker-compose.yml, nginx.conf
└── docs/
    ├── API.md        — справочник API
    └── ТЗ_v1.0.md   — техническое задание
```

---

## Быстрый старт

Приложение разворачивается из WSL2 (Debian) через Docker Compose.

```bash
cd ~/navis/infra
docker compose up -d
```

После запуска:
- UI: `http://localhost`
- Swagger UI: `http://localhost/api/docs`
- ReDoc: `http://localhost/api/redoc`

---

## Коннекторы

### Git (GitHub / GitLab / Bitbucket Server)

Парсит OpenAPI/Swagger YAML и JSON файлы из репозиториев. Создаёт сервисы, интерфейсы и методы.

```
Тип источника: git
Провайдеры: github, gitlab, bitbucket
Аутентификация: PAT / токен (опционально)
```

Формат URL Bitbucket Server: `https://bitbucket.company.com/projects/KEY/repos/my-repo`

### Confluence Server

Находит draw.io архитектурные диаграммы на страницах space и строит граф зависимостей между сервисами.

```
Тип источника: confluence
Сервер: Confluence Server / Data Center (on-premise)
Аутентификация: Basic auth — поле token в формате "username:password"
Формат диаграмм: application/vnd.jgraph.mxfile (plain XML или base64+deflate)
```

Сущности из диаграмм сопоставляются с сервисами каталога. Несопоставленные отображаются в графе как узлы типа **external**.

---

## Граф зависимостей

Интерактивный граф на Cytoscape.js с фильтрами по типам узлов:

| Тип | Цвет | Описание |
|-----|------|----------|
| `system` | тёмно-синий | Информационная система |
| `service` | синий | Сервис внутри ИС |
| `interface` | фиолетовый | API интерфейс |
| `method` | зелёный | Эндпоинт / операция |
| `external` | янтарный | Внешний сервис из диаграммы |

---

## DB-коннекторы

Инвентаризация схем, таблиц, VIEW и процедур. Результат попадает в каталог: `DB: name [driver]` → схема → таблица/процедура.

| СУБД | Статус | Порт по умолчанию |
|------|--------|-------------------|
| MS SQL Server | ✅ Готово | 1433 |
| PostgreSQL | ✅ Готово | 5432 |
| ClickHouse | В разработке | 9000 |

Аутентификация для всех: поле `token` в формате `username:password`.

---

## Тесты

```bash
cd ~/navis/backend
source .venv/bin/activate
pytest -v
```

44 теста покрывают CRUD всех сущностей и поиск (SQLite in-memory, без Docker).

---

## Документация

- [API Reference](docs/API.md) — все эндпоинты с примерами запросов/ответов
- [Техническое задание v1.0](docs/ТЗ_v1.0.md) — требования, архитектура, статус этапов
