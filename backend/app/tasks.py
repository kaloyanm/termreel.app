"""RQ job entrypoint. Runs in the worker process (see worker.py)."""
import time
import traceback
from datetime import datetime, timezone

from sqlmodel import Session

from app.db import engine
from app.models import JobStatus, RenderJob, Scenario
from app.render_pipeline import RenderError, run_render

LOG_COMMIT_INTERVAL = 0.5  # seconds between DB commits while streaming log output


def render_scenario_job(job_id: str) -> None:
    with Session(engine) as session:
        job = session.get(RenderJob, job_id)
        if job is None:
            return
        scenario = session.get(Scenario, job.scenario_id)
        if scenario is None:
            job.status = JobStatus.failed
            job.error = "scenario no longer exists"
            session.add(job)
            session.commit()
            return

        job.status = JobStatus.running
        job.started_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()

        last_commit = time.monotonic()

        def on_log(chunk: str) -> None:
            nonlocal last_commit
            job.log += chunk
            now = time.monotonic()
            if now - last_commit >= LOG_COMMIT_INTERVAL:
                session.add(job)
                session.commit()
                last_commit = now

        try:
            result = run_render(
                job_id=job.id,
                scenario_title=scenario.title,
                docker_cfg=scenario.docker,
                typing_cfg=scenario.typing,
                steps=scenario.steps,
                on_log=on_log,
                theme=job.theme,
            )
        except RenderError as exc:
            job.status = JobStatus.failed
            job.error = str(exc)
            job.finished_at = datetime.now(timezone.utc)
            session.add(job)
            session.commit()
            return
        except Exception as exc:  # noqa: BLE001 - surface any unexpected failure to the UI
            job.status = JobStatus.failed
            job.error = f"unexpected error: {exc}"
            job.log += traceback.format_exc()
            job.finished_at = datetime.now(timezone.utc)
            session.add(job)
            session.commit()
            return

        job.status = JobStatus.done
        job.cast_path = result["cast_path"]
        job.gif_path = result["gif_path"]
        job.mp4_path = result["mp4_path"]
        job.finished_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()
