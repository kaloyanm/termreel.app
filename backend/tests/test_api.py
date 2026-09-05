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
            "flavour": "rust",
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
        "docker": {"flavour": "rust", "container_name": "x"},
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
            "docker": {"flavour": "rust", "container_name": "x"},
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
            "docker": {"flavour": "rust", "container_name": "x"},
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
            "docker": {"flavour": "rust", "container_name": "x"},
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
            "docker": {"flavour": "rust", "container_name": "x"},
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


def test_presenterm_step_round_trip(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "slides demo",
            "docker": {"flavour": "rust", "container_name": "x"},
            "typing": {"base_cps": 14},
            "steps": [
                {
                    "type": "presenterm",
                    "path": "talk.md",
                    "content": "# Slide 1\n<!-- end_slide -->\n# Slide 2\n<!-- end_slide -->\n# Slide 3\n",
                    "slide_pause": 2.5,
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    scenario = r.json()
    step = scenario["steps"][0]
    assert step["type"] == "presenterm"
    assert step["slide_pause"] == 2.5


def test_presenterm_requires_path_or_content(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "bad presenterm step",
            "docker": {"flavour": "rust", "container_name": "x"},
            "steps": [{"type": "presenterm", "path": "talk.md"}],  # missing content
        },
    )
    assert r.status_code == 422


def test_presenterm_slide_pause_must_be_positive(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    for bad_pause in (0, -1):
        r = client.post(
            f"/api/playlists/{playlist['id']}/scenarios",
            json={
                "title": "bad slide_pause",
                "docker": {"flavour": "rust", "container_name": "x"},
                "steps": [
                    {"type": "presenterm", "path": "talk.md", "content": "# Slide 1\n", "slide_pause": bad_pause}
                ],
            },
        )
        assert r.status_code == 422


def test_presenterm_step_not_subject_to_write_vim_typing_guardrail(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    # This much content at 1 cps would trip the write_vim typing-time
    # guardrail if it were mistakenly applied to presenterm steps too -
    # presenterm content is written silently, never human-typed on screen.
    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "long slides",
            "docker": {"flavour": "rust", "container_name": "x"},
            "typing": {"base_cps": 1},
            "steps": [{"type": "presenterm", "path": "talk.md", "content": "x" * 5000}],
        },
    )
    assert r.status_code == 201, r.text


def test_list_flavours(client):
    r = client.get("/api/flavours")
    assert r.status_code == 200
    flavours = r.json()
    assert any(f["id"] == "rust" and f["display_name"] == "Rust" for f in flavours)


def test_scenario_rejects_unknown_flavour(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()

    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "bad flavour",
            "docker": {"flavour": "does-not-exist", "container_name": "x"},
            "steps": [{"type": "command", "text": "echo hi"}],
        },
    )
    assert r.status_code == 422

    # Also rejected on update.
    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={
            "title": "good flavour",
            "docker": {"flavour": "rust", "container_name": "x"},
            "steps": [{"type": "command", "text": "echo hi"}],
        },
    )
    scenario = r.json()
    r = client.put(
        f"/api/scenarios/{scenario['id']}",
        json={"docker": {"flavour": "does-not-exist", "container_name": "x"}},
    )
    assert r.status_code == 422


def test_render_requires_steps(client):
    r = client.post("/api/projects", json={"name": "P"})
    project = r.json()
    r = client.post(f"/api/projects/{project['id']}/playlists", json={"name": "PL"})
    playlist = r.json()
    r = client.post(
        f"/api/playlists/{playlist['id']}/scenarios",
        json={"title": "empty", "docker": {"flavour": "rust", "container_name": "x"}, "steps": []},
    )
    scenario = r.json()
    r = client.post(f"/api/scenarios/{scenario['id']}/render", json={"theme": "dracula"})
    assert r.status_code == 400
