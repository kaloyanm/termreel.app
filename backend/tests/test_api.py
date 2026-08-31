import os

os.environ.setdefault("PYTEST_RUNNING", "1")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app import db as db_module
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    db_module.engine = engine

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_module.get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_project_playlist_scenario_flow(client):
    r = client.post("/api/projects", json={"name": "My Project", "description": "d"})
    assert r.status_code == 201
    project = r.json()
    assert project["playlist_count"] == 0

    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "Playlist 1"})
    assert r.status_code == 201
    playlist = r.json()

    r = client.get(f"/api/projects/{project['id']}/playlists")
    assert len(r.json()) == 1

    scenario_payload = {
        "title": "Demo episode",
        "docker": {
            "image": "golang:1.22",
            "container_name": "demo",
            "mount_host_path": "./demo-repo",
            "mount_container_path": "/repo",
            "workdir": "/repo",
        },
        "typing": {"base_cps": 14, "jitter_pct": 0.35, "default_pause_after": 1.5},
        "steps": [
            {"type": "command", "text": "cat worker.go", "pause_after": 3},
            {"type": "comment", "text": "notice the race", "pause_after": 2},
            {
                "type": "write_file",
                "path": "worker.go",
                "content": "package main\n",
                "pause_after": 2,
            },
        ],
    }
    r = client.post(f"/api/playlists/{playlist['id']}/scenarios", json=scenario_payload)
    assert r.status_code == 201, r.text
    scenario = r.json()
    assert scenario["steps"][2]["type"] == "write_file"

    r = client.get(f"/api/playlists/{playlist['id']}")
    assert r.json()["scenario_count"] == 1

    r = client.get(f"/api/scenarios/{scenario['id']}/yaml")
    assert "docker:" in r.text and "steps:" in r.text

    # unlimited playlists per project
    for i in range(5):
        r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": f"Playlist {i}"})
        assert r.status_code == 201
    r = client.get(f"/api/projects/{project['id']}/playlists")
    assert len(r.json()) == 6


def test_scenario_validation_rejects_bad_step(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    bad_payload = {
        "title": "bad",
        "docker": {"image": "x", "container_name": "x"},
        "steps": [{"type": "command"}],  # missing required 'text'
    }
    r = client.post(f"/api/playlists/{playlist['id']}/scenarios", json=bad_payload)
    assert r.status_code == 422


def test_write_vim_step_round_trip(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "vim demo",
            "docker": {"image": "x", "container_name": "x"},
            "typing": {"base_cps": 14},
            "steps": [
                {
                    "type": "write_vim",
                    "path": "worker.go",
                    "content": "package main\n",
                    "simulate_typos": True,
                    "force_blank": True,
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    scenario = r.json()
    step = scenario["steps"][0]
    assert step["type"] == "write_vim"
    assert step["simulate_typos"] is True
    assert step["force_blank"] is True


def test_write_vim_requires_path_or_content(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "bad vim step",
            "docker": {"image": "x", "container_name": "x"},
            "steps": [{"type": "write_vim", "path": "worker.go"}],  # missing content
        },
    )
    assert r.status_code == 422


def test_write_vim_typing_time_guardrail_rejects_oversized_content(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    # 100 chars at 1 cps would take 100s, well past the 60s limit.
    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "too slow",
            "docker": {"image": "x", "container_name": "x"},
            "typing": {"base_cps": 1},
            "steps": [{"type": "write_vim", "path": "f.txt", "content": "x" * 100}],
        },
    )
    assert r.status_code == 422
    assert "write_vim" in r.text


def test_write_vim_typing_time_guardrail_allows_small_content(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "fine",
            "docker": {"image": "x", "container_name": "x"},
            "typing": {"base_cps": 14},
            "steps": [{"type": "write_vim", "path": "f.txt", "content": "short"}],
        },
    )
    assert r.status_code == 201, r.text
    scenario = r.json()

    # Updating steps alone (no typing in the payload) must still use the
    # scenario's existing typing.base_cps to evaluate the guardrail.
    r = client.put(
        f"/api/scenarios/{scenario['id']}",
        json={"steps": [{"type": "write_vim", "path": "f.txt", "content": "x" * 5000}]},
    )
    assert r.status_code == 422


def test_render_requires_steps(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()
    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={"title": "empty", "docker": {"image": "x", "container_name": "x"}, "steps": []},
    )
    scenario = r.json()
    r = client.post(f"/api/scenarios/{scenario['id']}/render", json={"theme": "dracula"})
    assert r.status_code == 400
