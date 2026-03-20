from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Edge, System, Service, Interface, Method
from app.schemas.schemas import EdgeCreate, EdgeOut

router = APIRouter(tags=["edges"])


async def _resolve_label(db: AsyncSession, node_id: str, node_type: str) -> str | None:
    """Возвращает человеко-читаемое название для узла."""
    if node_type == "external":
        return node_id.removeprefix("ext:")
    if node_type == "system":
        r = await db.get(System, node_id)
        return r.name if r else None
    if node_type == "service":
        r = await db.get(Service, node_id)
        return r.name if r else None
    if node_type == "interface":
        r = await db.get(Interface, node_id)
        return r.name if r else None
    if node_type == "method":
        r = await db.get(Method, node_id)
        return r.name if r else None
    return None


async def _edge_to_out(edge: Edge, db: AsyncSession) -> EdgeOut:
    from_label = await _resolve_label(db, edge.from_id, edge.from_type)
    to_label = await _resolve_label(db, edge.to_id, edge.to_type)
    return EdgeOut(
        id=edge.id,
        from_id=edge.from_id,
        from_type=edge.from_type,
        from_label=from_label,
        to_id=edge.to_id,
        to_type=edge.to_type,
        to_label=to_label,
        kind=edge.kind,
        confidence=edge.confidence,
        source=edge.source,
        created_at=edge.created_at,
    )


# ─── GET /systems/{system_id}/edges/ — рёбра, связанные с сервисами системы ──

@router.get("/systems/{system_id}/edges/", response_model=list[EdgeOut])
async def list_system_edges(
    system_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Собираем ID сервисов системы
    svc_result = await db.execute(select(Service).where(Service.system_id == system_id))
    svc_ids = {s.id for s in svc_result.scalars().all()}

    # Также сам system_id
    all_ids = svc_ids | {system_id}

    # Рёбра, где from_id или to_id входит в набор
    result = await db.execute(select(Edge))
    edges = [
        e for e in result.scalars().all()
        if e.from_id in all_ids or e.to_id in all_ids
    ]

    return [await _edge_to_out(e, db) for e in edges]


# ─── POST /edges/ — создать ручное ребро ─────────────────────────────────────

@router.post("/edges/", response_model=EdgeOut, status_code=201)
async def create_edge(
    payload: EdgeCreate,
    db: AsyncSession = Depends(get_db),
):
    edge = Edge(
        from_id=payload.from_id,
        from_type=payload.from_type,
        to_id=payload.to_id,
        to_type=payload.to_type,
        kind=payload.kind,
        confidence=payload.confidence,
        source="manual",
    )
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    return await _edge_to_out(edge, db)


# ─── DELETE /edges/{edge_id} ──────────────────────────────────────────────────

@router.delete("/edges/{edge_id}", status_code=204)
async def delete_edge(edge_id: str, db: AsyncSession = Depends(get_db)):
    edge = await db.get(Edge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    await db.delete(edge)
    await db.commit()
