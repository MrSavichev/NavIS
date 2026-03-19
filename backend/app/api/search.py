from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import System, Service, Method
from app.schemas.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/", response_model=list[SearchResult])
async def search(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    db: AsyncSession = Depends(get_db),
):
    results: list[SearchResult] = []
    pattern = f"%{q}%"

    # Системы
    systems = (await db.execute(
        select(System).where(
            or_(System.name.ilike(pattern), System.description.ilike(pattern))
        ).limit(10)
    )).scalars().all()
    for s in systems:
        results.append(SearchResult(id=s.id, type="system", label=s.name, description=s.description))

    # Сервисы
    services = (await db.execute(
        select(Service).where(
            or_(Service.name.ilike(pattern), Service.description.ilike(pattern))
        ).limit(10)
    )).scalars().all()
    for s in services:
        results.append(SearchResult(id=s.id, type="service", label=s.name, description=s.description))

    # Методы
    methods = (await db.execute(
        select(Method).where(
            or_(Method.name.ilike(pattern), Method.path.ilike(pattern), Method.description.ilike(pattern))
        ).limit(10)
    )).scalars().all()
    for m in methods:
        results.append(SearchResult(id=m.id, type="method", label=m.name, description=m.description, path=m.path))

    return results
