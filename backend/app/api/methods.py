from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Method, Interface, Source
from app.schemas.schemas import MethodCreate, MethodOut, InterfaceOut, SourceOut

router = APIRouter(prefix="/interfaces/{interface_id}/methods", tags=["methods"])
direct_router = APIRouter(tags=["methods"])


@router.get("/", response_model=list[MethodOut])
async def list_methods(interface_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Method).where(Method.interface_id == interface_id).order_by(Method.path, Method.name)
    )
    return result.scalars().all()


@router.get("/{method_id}", response_model=MethodOut)
async def get_method(interface_id: str, method_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Method).where(Method.id == method_id, Method.interface_id == interface_id)
    )
    method = result.scalar_one_or_none()
    if not method:
        raise HTTPException(status_code=404, detail="Method not found")
    return method


@router.post("/", response_model=MethodOut, status_code=201)
async def create_method(interface_id: str, data: MethodCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Interface).where(Interface.id == interface_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Interface not found")
    method = Method(interface_id=interface_id, **data.model_dump())
    db.add(method)
    await db.commit()
    await db.refresh(method)
    return method


@router.delete("/{method_id}", status_code=204)
async def delete_method(interface_id: str, method_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Method).where(Method.id == method_id, Method.interface_id == interface_id)
    )
    method = result.scalar_one_or_none()
    if not method:
        raise HTTPException(status_code=404, detail="Method not found")
    await db.delete(method)
    await db.commit()


# ─── Прямой доступ без parent-id ──────────────────────────────────────────────

@direct_router.get("/interfaces/{interface_id}", response_model=InterfaceOut)
async def get_interface_direct(interface_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Interface).where(Interface.id == interface_id))
    iface = result.scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="Interface not found")
    return iface


@direct_router.get("/methods/{method_id}/sources", response_model=list[SourceOut])
async def get_method_sources(method_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).where(Source.method_id == method_id).order_by(Source.collected_at.desc())
    )
    return result.scalars().all()
