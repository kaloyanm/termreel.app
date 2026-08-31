"""Reads the flavour catalog (flavours/flavours.yaml at repo root) — the
same manifest driver.py resolves flavours against, see FR-CLI-012."""
import yaml

from app.config import FLAVOURS_MANIFEST


def load_flavours() -> list[dict]:
    return yaml.safe_load(FLAVOURS_MANIFEST.read_text())


def flavour_ids() -> set[str]:
    return {f["id"] for f in load_flavours()}
