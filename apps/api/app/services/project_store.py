from __future__ import annotations

from pathlib import Path
from uuid import uuid4
import json
from datetime import datetime, UTC

from app.models.manifest import BuildablesPhysicsManifest
from app.paths import projects_root, sim_data_root


def project_dir(project_id: str) -> Path:
    return projects_root() / project_id


def create_project(project_name: str, project_id: str | None = None) -> dict:
    pid = project_id or f"project-{uuid4().hex[:8]}"
    pdir = project_dir(pid)
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "assets").mkdir(exist_ok=True)
    (pdir / "generated" / "collision").mkdir(parents=True, exist_ok=True)
    (pdir / "generated" / "robot_description").mkdir(parents=True, exist_ok=True)
    (pdir / "manifest_versions").mkdir(parents=True, exist_ok=True)
    (pdir / "runs").mkdir(exist_ok=True)
    manifest = BuildablesPhysicsManifest(project_id=pid, project_name=project_name)
    save_manifest(pid, manifest)
    return {"project_id": pid, "project_name": project_name}


def list_projects() -> list[dict]:
    out: list[dict] = []
    root = projects_root()
    if not root.exists():
        return out
    for child in root.iterdir():
        if child.is_dir():
            manifest_path = child / "manifest.buildables.physics.json"
            if manifest_path.exists():
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                out.append({"project_id": data.get("project_id", child.name), "project_name": data.get("project_name", child.name)})
            else:
                out.append({"project_id": child.name, "project_name": child.name})
    return out


def delete_project(project_id: str) -> None:
    pdir = project_dir(project_id)
    if not pdir.exists():
        return
    for path in sorted(pdir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
        else:
            path.rmdir()
    pdir.rmdir()


def manifest_path(project_id: str) -> Path:
    return project_dir(project_id) / "manifest.buildables.physics.json"


def load_manifest(project_id: str) -> BuildablesPhysicsManifest:
    path = manifest_path(project_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    return BuildablesPhysicsManifest.model_validate(data)


def save_manifest(project_id: str, manifest: BuildablesPhysicsManifest) -> None:
    pdir = project_dir(project_id)
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "manifest_versions").mkdir(parents=True, exist_ok=True)
    current_path = manifest_path(project_id)
    previous_version = 0
    if current_path.exists():
        old_data = json.loads(current_path.read_text(encoding="utf-8"))
        previous_version = int(old_data.get("version", 0))
    requested_version = int(getattr(manifest, "version", 0) or 0)
    manifest.version = max(previous_version + 1, requested_version if requested_version > previous_version else previous_version + 1)
    manifest.updated_at = datetime.now(UTC).isoformat()
    payload = manifest.model_dump_json(indent=2)
    current_path.write_text(payload, encoding="utf-8")
    (pdir / "manifest_versions" / f"{manifest.version}.json").write_text(payload, encoding="utf-8")


def load_or_copy_default_project(default_project_id: str = "default-robot-dog") -> dict:
    target = project_dir(default_project_id)
    if not target.exists():
        raise FileNotFoundError(f"Default project folder missing: {target}")
    (target / "runs").mkdir(parents=True, exist_ok=True)
    (target / "manifest_versions").mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(default_project_id)
    return {"project_id": manifest.project_id, "project_name": manifest.project_name, "loaded": True}


def _active_project_path() -> Path:
    return sim_data_root() / "active_project.json"


def set_active_project(project_id: str | None) -> None:
    path = _active_project_path()
    if project_id is None:
        if path.exists():
            path.unlink()
        return
    payload = {"project_id": project_id}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_active_project_id() -> str | None:
    path = _active_project_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("project_id")
    except Exception:
        return None
