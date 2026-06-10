"""Asset path resolution for generated scripts."""
from __future__ import annotations

import json
from pathlib import Path


def load_context(context_path: str | Path) -> dict:
    path = Path(context_path)
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_asset_path(project_root: str | Path, relative: str) -> Path:
    root = Path(project_root)
    cleaned = relative.replace("\\", "/").lstrip("/")
    candidate = root / cleaned
    if candidate.is_file():
        return candidate.resolve()
    imported = root / "assets" / "imported" / cleaned
    if imported.is_file():
        return imported.resolve()
    return candidate.resolve()


def validate_asset_exists(path: str | Path) -> bool:
    return Path(path).is_file()


def normalize_windows_path(path: str | Path) -> str:
    return str(Path(path)).replace("\\", "/")


def get_robot_description_type(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext in {".urdf", ".xacro"}:
        return "urdf"
    if ext in {".xml", ".mjcf"}:
        return "mjcf"
    return "urdf"
