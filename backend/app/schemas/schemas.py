from datetime import datetime
from pydantic import BaseModel


# ─── System ───────────────────────────────────────────────────────────────────

class SystemCreate(BaseModel):
    name: str
    description: str | None = None
    owner: str | None = None
    tags: list[str] = []
    environments: list[str] = []


class SystemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    owner: str | None = None
    tags: list[str] | None = None
    environments: list[str] | None = None


class SystemOut(BaseModel):
    id: str
    name: str
    description: str | None
    owner: str | None
    tags: list
    environments: list
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemListOut(BaseModel):
    id: str
    name: str
    owner: str | None
    tags: list
    environments: list
    service_count: int = 0

    class Config:
        from_attributes = True


# ─── Service ──────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name: str
    description: str | None = None


class ServiceOut(BaseModel):
    id: str
    system_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Interface ────────────────────────────────────────────────────────────────

class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class InterfaceCreate(BaseModel):
    name: str
    type: str  # http, grpc
    version: str | None = None
    spec_ref: str | None = None


class InterfaceOut(BaseModel):
    id: str
    service_id: str
    name: str
    type: str
    version: str | None
    spec_ref: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Method ───────────────────────────────────────────────────────────────────

class InterfaceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    version: str | None = None
    spec_ref: str | None = None


class MethodCreate(BaseModel):
    name: str
    http_method: str | None = None
    path: str | None = None
    description: str | None = None
    request_schema: dict | None = None
    response_schema: dict | None = None
    examples: list = []


class MethodOut(BaseModel):
    id: str
    interface_id: str
    name: str
    http_method: str | None
    path: str | None
    description: str | None
    request_schema: dict | None
    response_schema: dict | None
    examples: list
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MethodUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    http_method: str | None = None
    path: str | None = None
    request_schema: dict | None = None
    response_schema: dict | None = None


# ─── Source ───────────────────────────────────────────────────────────────────

class SourceOut(BaseModel):
    id: str
    method_id: str
    type: str
    ref: str
    hash: str | None
    collected_at: datetime

    class Config:
        from_attributes = True


# ─── Graph ────────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    type: str   # system, service, interface, method
    label: str


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    kind: str


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ─── Edge (manual mapping) ────────────────────────────────────────────────────

class EdgeCreate(BaseModel):
    from_id: str
    from_type: str  # system, service, interface, method, external
    to_id: str
    to_type: str
    kind: str       # calls, depends, uses, consumes, publishes, ...
    confidence: float = 1.0


class EdgeOut(BaseModel):
    id: str
    from_id: str
    from_type: str
    from_label: str | None = None
    to_id: str
    to_type: str
    to_label: str | None = None
    kind: str
    confidence: float | None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Search ───────────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    id: str
    type: str   # system, service, method
    label: str
    description: str | None
    path: str | None = None
    url: str | None = None
