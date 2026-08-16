from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Playlist, Project
from app.schemas import PlaylistCreate, PlaylistRead, PlaylistUpdate

router = APIRouter(tags=["playlists"])


def _to_read(pl: Playlist) -> PlaylistRead:
    return PlaylistRead(
        id=pl.id, project_id=pl.project_id, name=pl.name, description=pl.description,
        created_at=pl.created_at, scenario_count=len(pl.scenarios),
    )


@router.get("/api/projects/{project_id}/playlists", response_model=list[PlaylistRead])
def list_playlists(project_id: str, session: Session = Depends(get_session)):
    if not session.get(Project, project_id):
        raise HTTPException(404, "project not found")
    playlists = session.exec(select(Playlist).where(Playlist.project_id == project_id)).all()
    return [_to_read(p) for p in playlists]


@router.post("/api/projects/{project_id}/playlists", response_model=PlaylistRead, status_code=201)
def create_playlist(project_id: str, body: PlaylistCreate, session: Session = Depends(get_session)):
    if not session.get(Project, project_id):
        raise HTTPException(404, "project not found")
    playlist = Playlist(project_id=project_id, name=body.name, description=body.description)
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    return _to_read(playlist)


@router.get("/api/playlists/{playlist_id}", response_model=PlaylistRead)
def get_playlist(playlist_id: str, session: Session = Depends(get_session)):
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(404, "playlist not found")
    return _to_read(playlist)


@router.patch("/api/playlists/{playlist_id}", response_model=PlaylistRead)
def update_playlist(playlist_id: str, body: PlaylistUpdate, session: Session = Depends(get_session)):
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(404, "playlist not found")
    if body.name is not None:
        playlist.name = body.name
    if body.description is not None:
        playlist.description = body.description
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    return _to_read(playlist)


@router.delete("/api/playlists/{playlist_id}", status_code=204)
def delete_playlist(playlist_id: str, session: Session = Depends(get_session)):
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(404, "playlist not found")
    session.delete(playlist)
    session.commit()
