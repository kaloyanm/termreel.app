from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---- Projects ----

class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    playlist_count: int = 0


# ---- Playlists ----

class PlaylistCreate(BaseModel):
    name: str
    description: str = ""


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PlaylistRead(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    created_at: datetime
    scenario_count: int = 0


# ---- Flavours ----

class FlavourRead(BaseModel):
    id: str
    display_name: str
    dockerfile: str
    description: str = ""


# ---- Scenario steps (mirrors scenario.example.yaml) ----

class DockerConfig(BaseModel):
    flavour: str
    container_name: str
    mount_host_path: str = "./demo-repo"
    mount_container_path: str = "/repo"
    workdir: Optional[str] = None


class TypingConfig(BaseModel):
    base_cps: float = 14
    jitter_pct: float = 0.35
    default_pause_after: float = 1.5


class ScenarioStep(BaseModel):
    type: Literal["command", "comment", "write_file", "write_vim", "presenterm"]
    text: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    content_file: Optional[str] = None
    pause_after: Optional[float] = None
    # write_vim only (see FR-EDIT-005): simulate occasional typos while
    # typing, and always start from a blank buffer instead of auto-diffing
    # against whatever's already at `path` in the container. Optional/None
    # (not a plain bool default) so they're omitted, like pause_after, from
    # steps that don't set them rather than cluttering every step's YAML.
    simulate_typos: Optional[bool] = None
    force_blank: Optional[bool] = None
    # presenterm only (see FR-EDIT-009): seconds to pause before each slide
    # advance. Optional so it's omitted, like pause_after, from steps that
    # don't set it; driver.py falls back to a fixed default when unset.
    slide_pause: Optional[float] = None

    @model_validator(mode="after")
    def check_fields_for_type(self):
        if self.type in ("command", "comment") and not self.text:
            raise ValueError(f"step of type '{self.type}' requires 'text'")
        if self.type in ("write_file", "write_vim", "presenterm"):
            if not self.path:
                raise ValueError(f"step of type '{self.type}' requires 'path'")
            if not self.content and not self.content_file:
                raise ValueError(
                    f"step of type '{self.type}' requires 'content' or 'content_file'"
                )
        if self.slide_pause is not None and self.slide_pause <= 0:
            raise ValueError("slide_pause must be positive")
        return self


class ScenarioCreate(BaseModel):
    title: str
    docker: DockerConfig
    typing: TypingConfig = TypingConfig()
    steps: list[ScenarioStep] = Field(default_factory=list)


class ScenarioUpdate(BaseModel):
    title: Optional[str] = None
    docker: Optional[DockerConfig] = None
    typing: Optional[TypingConfig] = None
    steps: Optional[list[ScenarioStep]] = None


class ScenarioRead(BaseModel):
    id: str
    playlist_id: str
    title: str
    docker: dict[str, Any]
    typing: dict[str, Any]
    steps: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    latest_job: Optional["RenderJobRead"] = None


# ---- Render jobs ----

class RenderJobCreate(BaseModel):
    theme: str = "dracula"


class RenderJobRead(BaseModel):
    id: str
    scenario_id: str
    status: str
    theme: str
    error: Optional[str] = None
    cast_url: Optional[str] = None
    gif_url: Optional[str] = None
    mp4_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


ScenarioRead.model_rebuild()
