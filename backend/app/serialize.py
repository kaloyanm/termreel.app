from app.models import RenderJob, Scenario
from app.schemas import RenderJobRead, ScenarioRead


def job_to_read(job: RenderJob) -> RenderJobRead:
    def url(p):
        return f"/media/{p}" if p else None

    return RenderJobRead(
        id=job.id, scenario_id=job.scenario_id, status=job.status.value, theme=job.theme,
        error=job.error, cast_url=url(job.cast_path), gif_url=url(job.gif_path),
        mp4_url=url(job.mp4_path), created_at=job.created_at, started_at=job.started_at,
        finished_at=job.finished_at,
    )


def scenario_to_read(scenario: Scenario) -> ScenarioRead:
    latest = max(scenario.jobs, key=lambda j: j.created_at, default=None)
    return ScenarioRead(
        id=scenario.id, playlist_id=scenario.playlist_id, title=scenario.title,
        docker=scenario.docker, typing=scenario.typing, steps=scenario.steps,
        created_at=scenario.created_at, updated_at=scenario.updated_at,
        latest_job=job_to_read(latest) if latest else None,
    )
