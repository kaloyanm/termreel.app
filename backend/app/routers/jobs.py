from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select

from app.db import get_session
from app.models import RenderJob, Scenario
from app.queue import render_queue
from app.schemas import RenderJobCreate, RenderJobRead
from app.serialize import job_to_read

router = APIRouter(tags=["jobs"])


@router.post("/api/scenarios/{scenario_id}/render", response_model=RenderJobRead, status_code=201)
def start_render(scenario_id: str, body: RenderJobCreate, session: Session = Depends(get_session)):
    scenario = session.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    if not scenario.steps:
        raise HTTPException(400, "scenario has no steps to render")

    job = RenderJob(scenario_id=scenario_id, theme=body.theme)
    session.add(job)
    session.commit()
    session.refresh(job)

    render_queue.enqueue("app.tasks.render_scenario_job", job.id, job_id=job.id, job_timeout=1800)

    return job_to_read(job)


@router.get("/api/scenarios/{scenario_id}/jobs", response_model=list[RenderJobRead])
def list_jobs(scenario_id: str, session: Session = Depends(get_session)):
    jobs = session.exec(
        select(RenderJob).where(RenderJob.scenario_id == scenario_id).order_by(RenderJob.created_at.desc())
    ).all()
    return [job_to_read(j) for j in jobs]


@router.get("/api/jobs/{job_id}", response_model=RenderJobRead)
def get_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(RenderJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job_to_read(job)


@router.get("/api/jobs/{job_id}/log", response_class=PlainTextResponse)
def get_job_log(job_id: str, session: Session = Depends(get_session)):
    job = session.get(RenderJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job.log
