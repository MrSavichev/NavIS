import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class System(Base):
    """Информационная система (верхнеуровневая сущность)."""
    __tablename__ = "systems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    environments: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    services: Mapped[list["Service"]] = relationship("Service", back_populates="system", cascade="all, delete-orphan")


class Service(Base):
    """Микросервис внутри ИС."""
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    system_id: Mapped[str] = mapped_column(String(36), ForeignKey("systems.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    system: Mapped["System"] = relationship("System", back_populates="services")
    interfaces: Mapped[list["Interface"]] = relationship("Interface", back_populates="service", cascade="all, delete-orphan")


class Interface(Base):
    """API интерфейс сервиса (HTTP/gRPC и т.д.)."""
    __tablename__ = "interfaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    service_id: Mapped[str] = mapped_column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # http, grpc, asyncapi
    version: Mapped[str | None] = mapped_column(String(50))
    spec_ref: Mapped[str | None] = mapped_column(Text)  # ссылка на спецификацию
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service: Mapped["Service"] = relationship("Service", back_populates="interfaces")
    methods: Mapped[list["Method"]] = relationship("Method", back_populates="interface", cascade="all, delete-orphan")


class Method(Base):
    """Метод/эндпоинт API."""
    __tablename__ = "methods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    interface_id: Mapped[str] = mapped_column(String(36), ForeignKey("interfaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    http_method: Mapped[str | None] = mapped_column(String(10))  # GET, POST, PUT, DELETE, ...
    path: Mapped[str | None] = mapped_column(String(1024), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    request_schema: Mapped[dict | None] = mapped_column(JSON)
    response_schema: Mapped[dict | None] = mapped_column(JSON)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interface: Mapped["Interface"] = relationship("Interface", back_populates="methods")
    sources: Mapped[list["Source"]] = relationship("Source", back_populates="method", cascade="all, delete-orphan")


class Source(Base):
    """Evidence — первоисточник данных о методе."""
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    method_id: Mapped[str] = mapped_column(String(36), ForeignKey("methods.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # git, confluence, db
    ref: Mapped[str] = mapped_column(Text, nullable=False)          # URL/commit/pageId
    hash: Mapped[str | None] = mapped_column(String(64))
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    method: Mapped["Method"] = relationship("Method", back_populates="sources")


class Edge(Base):
    """Ребро графа зависимостей."""
    __tablename__ = "edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    from_type: Mapped[str] = mapped_column(String(50), nullable=False)  # system, service, method, db, table, procedure
    to_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    to_type: Mapped[str] = mapped_column(String(50), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # calls, reads-from, writes-to, depends-on, defined-in
    confidence: Mapped[float | None] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
