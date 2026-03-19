from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import System, Service, Interface, Method, Edge
from app.schemas.schemas import GraphOut, GraphNode, GraphEdge

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/", response_model=GraphOut)
async def get_graph(
    system_id: str | None = Query(None, description="Фильтр по ИС"),
    depth: int = Query(2, ge=1, le=5, description="Глубина графа"),
    db: AsyncSession = Depends(get_db),
):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_ids: set[str] = set()

    # Загружаем системы
    q = select(System)
    if system_id:
        q = q.where(System.id == system_id)
    systems = (await db.execute(q)).scalars().all()

    for sys in systems:
        if sys.id not in node_ids:
            nodes.append(GraphNode(id=sys.id, type="system", label=sys.name))
            node_ids.add(sys.id)

        # Сервисы
        services = (await db.execute(
            select(Service).where(Service.system_id == sys.id)
        )).scalars().all()

        for svc in services:
            if svc.id not in node_ids:
                nodes.append(GraphNode(id=svc.id, type="service", label=svc.name))
                node_ids.add(svc.id)
            edges.append(GraphEdge(
                id=f"{sys.id}->{svc.id}",
                source=sys.id, target=svc.id, kind="contains"
            ))

            if depth < 2:
                continue

            # Интерфейсы
            interfaces = (await db.execute(
                select(Interface).where(Interface.service_id == svc.id)
            )).scalars().all()

            for iface in interfaces:
                if iface.id not in node_ids:
                    nodes.append(GraphNode(
                        id=iface.id, type="interface",
                        label=f"{iface.name} ({iface.type})"
                    ))
                    node_ids.add(iface.id)
                edges.append(GraphEdge(
                    id=f"{svc.id}->{iface.id}",
                    source=svc.id, target=iface.id, kind="exposes"
                ))

                if depth < 3:
                    continue

                # Методы
                methods = (await db.execute(
                    select(Method).where(Method.interface_id == iface.id)
                )).scalars().all()

                for method in methods:
                    if method.id not in node_ids:
                        label = f"{method.http_method or ''} {method.path or method.name}".strip()
                        nodes.append(GraphNode(id=method.id, type="method", label=label))
                        node_ids.add(method.id)
                    edges.append(GraphEdge(
                        id=f"{iface.id}->{method.id}",
                        source=iface.id, target=method.id, kind="defines"
                    ))

    # Добавляем зависимости из таблицы Edge
    edge_result = await db.execute(select(Edge))
    for edge in edge_result.scalars().all():
        edges.append(GraphEdge(
            id=edge.id,
            source=edge.from_id,
            target=edge.to_id,
            kind=edge.kind,
        ))

    return GraphOut(nodes=nodes, edges=edges)
