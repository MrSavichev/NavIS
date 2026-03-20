"""
Минимальные SQLAlchemy модели для worker (дублируют backend/models).
Используются только для записи в БД из worker.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    system_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Interface(Base):
    __tablename__ = "interfaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    service_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50))
    spec_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Method(Base):
    __tablename__ = "methods"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    interface_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    http_method: Mapped[str | None] = mapped_column(String(10))
    path: Mapped[str | None] = mapped_column(String(1024))
    description: Mapped[str | None] = mapped_column(Text)
    request_schema: Mapped[dict | None] = mapped_column(JSON)
    response_schema: Mapped[dict | None] = mapped_column(JSON)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    method_id: Mapped[str] = mapped_column(String(36), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    ref: Mapped[str] = mapped_column(Text, nullable=False)
    hash: Mapped[str | None] = mapped_column(String(64))
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IngestSource(Base):
    __tablename__ = "ingest_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    system_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    repo_url: Mapped[str | None] = mapped_column(Text)
    branch: Mapped[str | None] = mapped_column(String(255))
    path_filter: Mapped[str | None] = mapped_column(String(500))
    token: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(50))
    confluence_url: Mapped[str | None] = mapped_column(Text)
    space_key: Mapped[str | None] = mapped_column(String(100))
    db_host: Mapped[str | None] = mapped_column(String(255))
    db_port: Mapped[int | None] = mapped_column()
    db_name: Mapped[str | None] = mapped_column(String(255))
    db_schema: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Edge(Base):
    __tablename__ = "edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_id: Mapped[str] = mapped_column(String(36), nullable=False)
    from_type: Mapped[str] = mapped_column(String(50), nullable=False)
    to_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_type: Mapped[str] = mapped_column(String(50), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IngestJob(Base):
    __tablename__ = "ingest_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    files_found: Mapped[int] = mapped_column(default=0)
    methods_created: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(Text)
    log: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
