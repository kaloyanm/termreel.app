from datetime import datetime, timezone

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select

from app.db import get_session
from app.models import Playlist, Scenario
from app.schemas import ScenarioCreate, ScenarioRead, ScenarioUpdate
from app.serialize import scenario_to_read

router = APIRouter(tags=["scenarios"])

# FR-EDIT-007: a write_vim step whose content would take longer than this to
# type (at the scenario's typing.base_cps) is rejected at save time rather
# than silently queuing a very long render. `content` length is a valid
# upper bound for both write_vim modes (diff mode's deletions are instant
# vim commands, not human-typed; its insertions are always a subset of
# `content`), so this never needs the container's live "before" state.
WRITE_VIM_TYPING_TIME_LIMIT_S = 60


def _check_write_vim_typing_time(steps: list[dict], typing_cfg: dict):
    base_cps = typing_cfg.get("base_cps") or 14
    for i, step in enumerate(steps):
        content = step.get("content")
        if step.get("type") != "write_vim" or not content:
            continue
        estimated_s = len(content) / base_cps
        if estimated_s > WRITE_VIM_TYPING_TIME_LIMIT_S:
            raise HTTPException(
                422,
                f"step {i} (write_vim): content is ~{len(content)} chars, would take "
                f"~{estimated_s:.0f}s to type at {base_cps} cps "
                f"(limit: {WRITE_VIM_TYPING_TIME_LIMIT_S}s). Shorten the content, split "
                "it into multiple steps, or raise typing.base_cps.",
            )


@router.get("/api/playlists/{playlist_id}/scenarios", response_model=list[ScenarioRead])
def list_scenarios(playlist_id: str, session: Session = Depends(get_session)):
    if not session.get(Playlist, playlist_id):
        raise HTTPException(404, "playlist not found")
    scenarios = session.exec(select(Scenario).where(Scenario.playlist_id == playlist_id)).all()
    return [scenario_to_read(s) for s in scenarios]


@router.post("/api/playlists/{playlist_id}/scenarios", response_model=ScenarioRead, status_code=201)
def create_scenario(playlist_id: str, body: ScenarioCreate, session: Session = Depends(get_session)):
    if not session.get(Playlist, playlist_id):
        raise HTTPException(404, "playlist not found")
    typing_cfg = body.typing.model_dump(exclude_none=True)
    steps = [s.model_dump(exclude_none=True) for s in body.steps]
    _check_write_vim_typing_time(steps, typing_cfg)
    scenario = Scenario(
        playlist_id=playlist_id,
        title=body.title,
        docker=body.docker.model_dump(exclude_none=True),
        typing=typing_cfg,
        steps=steps,
    )
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario_to_read(scenario)


@router.get("/api/scenarios/{scenario_id}", response_model=ScenarioRead)
def get_scenario(scenario_id: str, session: Session = Depends(get_session)):
    scenario = session.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    return scenario_to_read(scenario)


@router.put("/api/scenarios/{scenario_id}", response_model=ScenarioRead)
def update_scenario(scenario_id: str, body: ScenarioUpdate, session: Session = Depends(get_session)):
    scenario = session.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    effective_typing = body.typing.model_dump(exclude_none=True) if body.typing is not None else scenario.typing
    effective_steps = (
        [s.model_dump(exclude_none=True) for s in body.steps] if body.steps is not None else scenario.steps
    )
    _check_write_vim_typing_time(effective_steps, effective_typing)
    if body.title is not None:
        scenario.title = body.title
    if body.docker is not None:
        scenario.docker = body.docker.model_dump(exclude_none=True)
    if body.typing is not None:
        scenario.typing = effective_typing
    if body.steps is not None:
        scenario.steps = effective_steps
    scenario.updated_at = datetime.now(timezone.utc)
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario_to_read(scenario)


@router.delete("/api/scenarios/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: str, session: Session = Depends(get_session)):
    scenario = session.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    session.delete(scenario)
    session.commit()


@router.get("/api/scenarios/{scenario_id}/yaml", response_class=PlainTextResponse)
def get_scenario_yaml(scenario_id: str, session: Session = Depends(get_session)):
    """Dumps the scenario in the exact custom YAML format used by driver.py."""
    scenario = session.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    doc = {
        "title": scenario.title,
        "docker": scenario.docker,
        "typing": scenario.typing,
        "steps": scenario.steps,
    }
    return yaml.safe_dump(doc, sort_keys=False)
