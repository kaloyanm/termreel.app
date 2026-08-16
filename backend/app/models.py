import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


def now() -> datetime:
    return datetime.now(timezone.utc)


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class Project(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=now)

    playlists: list["Playlist"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Playlist(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=now)

    project: Optional[Project] = Relationship(back_populates="playlists")
    scenarios: list["Scenario"] = Relationship(
        back_populates="playlist",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Scenario(SQLModel, table=True):
    """An artefact created by the scenario editor.

    Field layout mirrors scenario.example.yaml 1:1 so it can be dumped
    straight to YAML and handed to the existing driver.py unchanged.
    """

    id: str = Field(default_factory=gen_id, primary_key=True)
    playlist_id: str = Field(foreign_key="playlist.id", index=True)
    title: str
    docker: dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    typing: dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    steps: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)

    playlist: Optional[Playlist] = Relationship(back_populates="scenarios")
    jobs: list["RenderJob"] = Relationship(
        back_populates="scenario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class RenderJob(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    scenario_id: str = Field(foreign_key="scenario.id", index=True)
    status: JobStatus = Field(default=JobStatus.queued)
    theme: str = "dracula"
    log: str = ""
    error: Optional[str] = None
    cast_path: Optional[str] = None
    gif_path: Optional[str] = None
    mp4_path: Optional[str] = None
    created_at: datetime = Field(default_factory=now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    scenario: Optional[Scenario] = Relationship(back_populates="jobs")
