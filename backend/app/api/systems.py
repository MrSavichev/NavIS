from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.models import System, Service
from app.schemas.schemas import SystemCreate, SystemUpdate, SystemOut, SystemListOut

router = APIRouter(prefix="/systems", tags=["systems"])


@router.get("/", response_model=list[SystemListOut])
async def list_systems(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(System, func.count(Service.id).label("service_count"))
        .outerjoin(Service, Service.system_id == System.id)
        .group_by(System.id)
        .order_by(System.name)
    )
    rows = result.all()
    out = []
    for system, count in rows:
        item = SystemListOut.model_validate(system)
        item.service_count = count
        out.append(item)
    return out


@router.get("/{system_id}", response_model=SystemOut)
async def get_system(system_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.id == system_id))
    system = result.scalar_one_or_none()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    return system


@router.post("/", response_model=SystemOut, status_code=201)
async def create_system(data: SystemCreate, db: AsyncSession = Depends(get_db)):
    system = System(**data.model_dump())
    db.add(system)
    await db.commit()
    await db.refresh(system)
    return system


@router.patch("/{system_id}", response_model=SystemOut)
async def update_system(system_id: str, data: SystemUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.id == system_id))
    system = result.scalar_one_or_none()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(system, field, value)
    await db.commit()
    await db.refresh(system)
    return system


@router.delete("/{system_id}", status_code=204)
async def delete_system(system_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.id == system_id))
    system = result.scalar_one_or_none()
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    await db.delete(system)
    await db.commit()
