from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Interface, Service
from app.schemas.schemas import InterfaceCreate, InterfaceOut, InterfaceUpdate

router = APIRouter(prefix="/services/{service_id}/interfaces", tags=["interfaces"])


@router.get("/", response_model=list[InterfaceOut])
async def list_interfaces(service_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interface).where(Interface.service_id == service_id).order_by(Interface.name)
    )
    return result.scalars().all()


@router.get("/{interface_id}", response_model=InterfaceOut)
async def get_interface(service_id: str, interface_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interface).where(Interface.id == interface_id, Interface.service_id == service_id)
    )
    iface = result.scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="Interface not found")
    return iface


@router.post("/", response_model=InterfaceOut, status_code=201)
async def create_interface(service_id: str, data: InterfaceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).where(Service.id == service_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Service not found")
    iface = Interface(service_id=service_id, **data.model_dump())
    db.add(iface)
    await db.commit()
    await db.refresh(iface)
    return iface


@router.patch("/{interface_id}", response_model=InterfaceOut)
async def update_interface(service_id: str, interface_id: str, data: InterfaceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interface).where(Interface.id == interface_id, Interface.service_id == service_id)
    )
    iface = result.scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="Interface not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(iface, field, value)
    await db.commit()
    await db.refresh(iface)
    return iface


@router.delete("/{interface_id}", status_code=204)
async def delete_interface(service_id: str, interface_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Interface).where(Interface.id == interface_id, Interface.service_id == service_id)
    )
    iface = result.scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="Interface not found")
    await db.delete(iface)
    await db.commit()
