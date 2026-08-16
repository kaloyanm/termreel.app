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
    scenario = Scenario(
        playlist_id=playlist_id,
        title=body.title,
        docker=body.docker.model_dump(exclude_none=True),
        typing=body.typing.model_dump(exclude_none=True),
        steps=[s.model_dump(exclude_none=True) for s in body.steps],
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
    if body.title is not None:
        scenario.title = body.title
    if body.docker is not None:
        scenario.docker = body.docker.model_dump(exclude_none=True)
    if body.typing is not None:
        scenario.typing = body.typing.model_dump(exclude_none=True)
    if body.steps is not None:
        scenario.steps = [s.model_dump(exclude_none=True) for s in body.steps]
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
