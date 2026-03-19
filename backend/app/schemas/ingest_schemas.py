from datetime import datetime
from pydantic import BaseModel


class IngestSourceCreate(BaseModel):
    name: str
    type: str                       # git, confluence
    # Git
    repo_url: str | None = None
    branch: str = "main"
    path_filter: str | None = None
    token: str | None = None
    provider: str = "github"        # github, gitlab
    # Confluence
    confluence_url: str | None = None
    space_key: str | None = None


class IngestSourceOut(BaseModel):
    id: str
    system_id: str
    name: str
    type: str
    repo_url: str | None
    branch: str | None
    path_filter: str | None
    provider: str | None
    confluence_url: str | None
    space_key: str | None
    last_run_at: datetime | None
    last_run_status: str | None
    last_run_error: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class IngestJobOut(BaseModel):
    id: str
    source_id: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    files_found: int
    methods_created: int
    error: str | None
    log: str | None
    created_at: datetime

    class Config:
        from_attributes = True
