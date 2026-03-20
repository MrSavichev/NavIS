from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import Service, System
from app.schemas.schemas import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter(prefix="/systems/{system_id}/services", tags=["services"])


@router.get("/", response_model=list[ServiceOut])
async def list_services(system_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Service).where(Service.system_id == system_id).order_by(Service.name)
    )
    return result.scalars().all()


@router.get("/{service_id}", response_model=ServiceOut)
async def get_service(system_id: str, service_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.system_id == system_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/", response_model=ServiceOut, status_code=201)
async def create_service(system_id: str, data: ServiceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.id == system_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="System not found")
    service = Service(system_id=system_id, **data.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.patch("/{service_id}", response_model=ServiceOut)
async def update_service(system_id: str, service_id: str, data: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.system_id == system_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(service, field, value)
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
async def delete_service(system_id: str, service_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.system_id == system_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.delete(service)
    await db.commit()
