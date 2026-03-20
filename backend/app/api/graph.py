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
    show_methods: bool = Query(True, description="Показывать методы"),
    show_interfaces: bool = Query(True, description="Показывать интерфейсы"),
    show_deps: bool = Query(True, description="Показывать зависимости из draw.io"),
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
                source=sys.id, target=svc.id, kind="contains",
            ))

            if depth < 2 or not show_interfaces:
                continue

            # Интерфейсы
            interfaces = (await db.execute(
                select(Interface).where(Interface.service_id == svc.id)
            )).scalars().all()

            for iface in interfaces:
                if iface.id not in node_ids:
                    nodes.append(GraphNode(
                        id=iface.id, type="interface",
                        label=f"{iface.name} ({iface.type})",
                    ))
                    node_ids.add(iface.id)
                edges.append(GraphEdge(
                    id=f"{svc.id}->{iface.id}",
                    source=svc.id, target=iface.id, kind="exposes",
                ))

                if depth < 3 or not show_methods:
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
                        source=iface.id, target=method.id, kind="defines",
                    ))

    # Зависимости из таблицы Edge (draw.io)
    if show_deps:
        edge_result = await db.execute(select(Edge))
        for edge in edge_result.scalars().all():
            # Добавляем внешние узлы (ext:ServiceName), которых нет в каталоге
            for node_id, node_type in [(edge.from_id, edge.from_type), (edge.to_id, edge.to_type)]:
                if node_id not in node_ids:
                    label = node_id.removeprefix("ext:")
                    nodes.append(GraphNode(id=node_id, type=node_type, label=label))
                    node_ids.add(node_id)

            edges.append(GraphEdge(
                id=edge.id,
                source=edge.from_id,
                target=edge.to_id,
                kind=edge.kind,
            ))

    return GraphOut(nodes=nodes, edges=edges)
