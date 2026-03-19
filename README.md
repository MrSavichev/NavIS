# NavIS — Навигатор Информационных Систем

> Service Catalog & API Explorer для SRE-инженеров и разработчиков

## Что это

NavIS — внутренний веб-сервис для навигации по архитектуре корпоративных информационных систем.

- Каталог ИС → Сервисы → Методы с карточками request/response
- Граф зависимостей между сервисами, БД и хранимыми процедурами
- Автоматический импорт из Confluence, Git (OpenAPI, .proto), БД
- Поиск по всей документации в одном месте

## Стек

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI (Python) |
| Frontend | React + Cytoscape.js |
| БД | PostgreSQL |
| Кэш/очередь | Redis |
| Proxy | Nginx |
| Deploy | Docker + docker-compose |

## Структура

```
NavIS/
├── backend/      — FastAPI приложение
├── frontend/     — React SPA
├── worker/       — Ingest worker (парсеры коннекторов)
├── infra/        — docker-compose, nginx конфиги
└── docs/         — ТЗ и документация
```

## Документация

- [ТЗ v0.1](docs/ТЗ_v0.1.md) — техническое задание (черновик)
