from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_read(p: Project) -> ProjectRead:
    return ProjectRead(
        id=p.id, name=p.name, description=p.description, created_at=p.created_at,
        playlist_count=len(p.playlists),
    )


@router.get("", response_model=list[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project)).all()
    return [_to_read(p) for p in projects]


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(body: ProjectCreate, session: Session = Depends(get_session)):
    project = Project(name=body.name, description=body.description)
    session.add(project)
    session.commit()
    session.refresh(project)
    return _to_read(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "project not found")
    return _to_read(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, body: ProjectUpdate, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "project not found")
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    session.add(project)
    session.commit()
    session.refresh(project)
    return _to_read(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "project not found")
    session.delete(project)
    session.commit()
